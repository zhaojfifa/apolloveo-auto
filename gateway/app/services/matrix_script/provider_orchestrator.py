"""Matrix Script — Provider Orchestrator (Provider Orchestrator + Multi-Shot wave, Part A + C).

The multi-shot provider orchestration layer the Owner authorized: for a bounded set of
storyboard shots it builds a script-derived prompt (deterministic Prompt Builder), OPTIONALLY
strengthens it with Gemini (:mod:`gemini_prompt_refiner`), hosts the material + calls the
image_to_video provider (reusing the proven
:func:`akool_image_to_video_capability.generate_shot_clip_akool`), and — on a non-fatal
failure — asks Gemini to REWRITE the prompt and retries ONCE within a bounded attempt budget.
It never silently falls back: every attempt produces an honest per-shot :class:`ShotTrace`,
and :func:`build_provider_request_panel` projects those traces into the operator-safe
"AI 生成请求过程" panel (Part C).

This module owns multi-shot strategy + tracing ONLY. It does not host/poll/download itself
(that stays in the capability) and it surfaces NO provider/secret/url/task-id — operator
fields are fixed Chinese strings + status enums, and :func:`assert_no_provider_trace_leak`
guards the panel.

Hard boundaries: ``official_publish_ready`` unaffected; no provider/vendor brand, no api key,
no signed/raw provider URL, no raw task id, no local path in any operator-facing field;
bounded video-attempt budget (Owner cap ≤ 5); a fallback-only batch is honest, never faked.
"""
from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from gateway.app.services.matrix_script import akool_image_to_video_capability as akool_i2v
from gateway.app.services.matrix_script import gemini_prompt_refiner as refiner_mod

logger = logging.getLogger(__name__)

# Bounded provider video-attempt budget for one batch run (Owner cap: ≤ 5).
DEFAULT_MAX_VIDEO_ATTEMPTS = 5
# At most one Gemini-refined retry per shot (initial + 1 retry).
_MAX_ATTEMPTS_PER_SHOT = 2

# Operator-safe Chinese fallback reasons (honest; provider-agnostic; never a vendor msg).
_FALLBACK_REASON_ZH = {
    akool_i2v.STATUS_PROVIDER_FAILED: "实时生成未成功，已回退本地兜底镜头。",
    akool_i2v.STATUS_TIMEOUT: "实时生成超时，已回退本地兜底镜头。",
    akool_i2v.STATUS_POLICY_BLOCKED: "实时生成被服务限制，已回退本地兜底镜头。",
    akool_i2v.STATUS_CREDENTIAL_MISSING: "实时生成未启用（缺少凭据），使用本地兜底镜头。",
}
_FALLBACK_REASON_DEFAULT_ZH = "实时生成未完成，已回退本地兜底镜头。"
_FALLBACK_REASON_BUDGET_ZH = "已达本次实时生成次数上限，使用本地兜底镜头。"

# Operator-safe panel status (closed set).
PANEL_STATUS_NOT_REQUESTED = "not_requested"   # 未请求
PANEL_STATUS_GENERATED = "generated"           # 已生成（进入成片）
PANEL_STATUS_FALLBACK = "fallback"             # 失败回退
_PANEL_STATUS_LABEL_ZH = {
    PANEL_STATUS_NOT_REQUESTED: "未请求",
    PANEL_STATUS_GENERATED: "已生成",
    PANEL_STATUS_FALLBACK: "失败回退",
}
_PROMPT_SOURCE_LABEL_ZH = {
    refiner_mod.SOURCE_DETERMINISTIC: "系统生成",
    refiner_mod.SOURCE_GEMINI: "AI 强化",
    refiner_mod.SOURCE_RETRY: "AI 重写重试",
}
_POLL_LABEL_ZH = {"queued": "排队", "processing": "处理中", "success": "成功", "failed": "失败"}

# Tokens that must NEVER appear in an operator-facing panel value.
_PANEL_FORBIDDEN_TOKENS = (
    "akool", "vendor", "model_id", "credit", "provider_url", "temporary_url",
    "download_url", "provider_task_id", "msmaterial://", "asset://", "://",
    "http", "api_key", "apikey", "bearer", ".mp4", "/users/", "local_path",
)


@dataclass(frozen=True)
class ShotTarget:
    """One shot to attempt. Prompts are script-derived (Prompt Builder); the still is a
    resolved local path (the capability hosts it — the path is never operator-surfaced)."""

    shot_id: str
    shot_title_zh: str
    still_path: str
    base_prompt: str
    base_negative: str = ""
    visual_goal: str = ""
    narration_line: str = ""
    script_segment: str = ""
    motion_instruction: str = ""
    material_role: str = ""
    material_role_label_zh: str = ""
    product_constraints: str = ""


@dataclass(frozen=True)
class ShotTrace:
    """Honest per-shot provider lifecycle record. Operator-facing fields are fixed Chinese
    strings / status enums; ``clip_path`` + ``redacted_detail`` are internal/diagnostic."""

    shot_id: str
    shot_title_zh: str
    material_role: str
    material_role_label_zh: str
    prompt_source: str
    prompt_summary_zh: str
    provider_attempted: bool
    provider_status: str
    hosted_input_created: bool
    task_created: bool
    poll_summary_zh: str
    clip_downloaded: bool
    normalized: bool
    consumed_into_final: bool
    fallback_reason_zh: str
    latency_seconds: float
    attempts: int
    redacted_detail: str = ""
    credit_cost: Optional[float] = None   # provider does not return per-call credit
    clip_path: Optional[str] = None       # internal; never operator-surfaced
    succeeded: bool = False

    def consumed(self) -> "ShotTrace":
        """Return a copy marked consumed_into_final (set by the compose step)."""
        return ShotTrace(**{**self.__dict__, "consumed_into_final": True})


@dataclass(frozen=True)
class ProviderBatchResult:
    traces: Tuple[ShotTrace, ...]
    attempts_used: int

    @property
    def clips_by_shot(self) -> Dict[str, str]:
        return {t.shot_id: t.clip_path for t in self.traces if t.succeeded and t.clip_path}

    @property
    def success_count(self) -> int:
        return sum(1 for t in self.traces if t.succeeded)


def _poll_summary_zh(events: Sequence[str]) -> str:
    """Collapse the captured ``poll_<status>`` events into an operator-safe summary."""
    seq = [e[len("poll_"):] for e in events if e.startswith("poll_")]
    if not seq:
        return "未进入轮询"
    labels: List[str] = []
    last: Optional[str] = None
    for s in seq:
        if s != last:
            labels.append(_POLL_LABEL_ZH.get(s, "处理中"))
            last = s
    return "轮询：" + "→".join(labels)


def _resolve_prompt(
    target: ShotTarget, *, use_gemini: bool, env: Optional[Mapping[str, str]],
    refine_fn: Callable[..., refiner_mod.RefinedPrompt],
    previous_failure_reason: Optional[str] = None,
) -> refiner_mod.RefinedPrompt:
    """Deterministic prompt, optionally strengthened/rewritten by Gemini (honest fallback)."""
    if not use_gemini:
        return refiner_mod.RefinedPrompt(
            refiner_mod.SOURCE_DETERMINISTIC, target.base_prompt, target.base_negative,
            "使用系统生成的生成要求（脚本派生）。", available=False, redacted_detail="gemini_off",
        )
    return refine_fn(
        base_prompt=target.base_prompt, base_negative=target.base_negative,
        visual_goal=target.visual_goal, narration_line=target.narration_line,
        script_segment=target.script_segment, motion_instruction=target.motion_instruction,
        material_role=target.material_role, product_constraints=target.product_constraints,
        previous_failure_reason=previous_failure_reason, env=env,
    )


def _attempt_shot(
    target: ShotTarget, prompt: str, negative: str, attempt_index: int, *,
    task_id: str, work_dir: str, env: Optional[Mapping[str, str]],
    akool_fn: Callable[..., akool_i2v.AkoolShotResult], clock: Callable[[], float],
) -> "tuple[akool_i2v.AkoolShotResult, List[str], float]":
    """One provider attempt. Negatives ride inside the single prompt field (the
    image_to_video call has no separate negative param). Returns (result, events, latency)."""
    events: List[str] = []
    full_prompt = prompt + (f". Avoid: {negative}" if negative else "")
    out_clip = os.path.join(work_dir, f"{target.shot_id}_provider_{attempt_index}.mp4")
    t0 = clock()

    def _collect(name: str) -> None:
        # Redacted phase timing: stage name + shot_id + elapsed only (no url / key / task id).
        events.append(name)
        logger.info("ms_phase phase=akool_%s shot=%s attempt=%d elapsed_ms=%d",
                    name, target.shot_id, attempt_index, int((clock() - t0) * 1000))

    result = akool_fn(
        still_path=target.still_path, out_clip=out_clip,
        task_id=task_id, shot_id=target.shot_id, prompt=full_prompt,
        env=env, on_event=_collect,
    )
    return result, events, max(0.0, clock() - t0)


def _build_trace(
    target: ShotTarget, refined: refiner_mod.RefinedPrompt,
    result: Optional[akool_i2v.AkoolShotResult], events: List[str], *,
    attempts: int, latency: float, fallback_reason_zh: str,
) -> ShotTrace:
    succeeded = bool(result and result.succeeded)
    status = result.status if result else akool_i2v.STATUS_FALLBACK_USED
    return ShotTrace(
        shot_id=target.shot_id, shot_title_zh=target.shot_title_zh,
        material_role=target.material_role, material_role_label_zh=target.material_role_label_zh,
        prompt_source=refined.source, prompt_summary_zh=refined.operator_summary_zh,
        provider_attempted=bool(result and result.provider_attempted),
        provider_status=status,
        hosted_input_created="hosted_input_created" in events,
        task_created="task_created" in events,
        poll_summary_zh=_poll_summary_zh(events),
        clip_downloaded="clip_downloaded" in events,
        normalized="normalized" in events,
        consumed_into_final=False,
        fallback_reason_zh="" if succeeded else fallback_reason_zh,
        latency_seconds=round(latency, 2), attempts=attempts,
        redacted_detail=(result.redacted_detail if result else "not_attempted"),
        clip_path=(result.clip_path if succeeded else None), succeeded=succeeded,
    )


def _run_one_shot(
    target: ShotTarget, *, task_id: str, work_dir: str, env: Optional[Mapping[str, str]],
    use_gemini: bool, akool_fn: Callable[..., akool_i2v.AkoolShotResult],
    refine_fn: Callable[..., refiner_mod.RefinedPrompt], clock: Callable[[], float],
    budget_remaining: int, enable_retry: bool = True,
) -> "tuple[ShotTrace, int]":
    """Attempt one shot within the remaining budget; return (trace, attempts_used)."""
    max_attempts = min(_MAX_ATTEMPTS_PER_SHOT, max(0, budget_remaining))
    _t_ref = clock()
    refined = _resolve_prompt(target, use_gemini=use_gemini, env=env, refine_fn=refine_fn)
    logger.info("ms_phase phase=gemini_refine_done shot=%s source=%s elapsed_ms=%d",
                target.shot_id, refined.source, int((clock() - _t_ref) * 1000))
    if max_attempts == 0:
        return _build_trace(target, refined, None, [], attempts=0, latency=0.0,
                            fallback_reason_zh=_FALLBACK_REASON_BUDGET_ZH), 0

    all_events: List[str] = []
    latency_total = 0.0
    attempts = 0
    result: Optional[akool_i2v.AkoolShotResult] = None
    for i in range(max_attempts):
        result, events, lat = _attempt_shot(
            target, refined.provider_prompt, refined.negative_prompt, i,
            task_id=task_id, work_dir=work_dir, env=env, akool_fn=akool_fn, clock=clock,
        )
        attempts += 1
        latency_total += lat
        all_events.extend(events)
        if result.succeeded:
            break
        if result.status == akool_i2v.STATUS_CREDENTIAL_MISSING:
            break  # no point retrying without credentials / flag
        # Retry ONLY when Gemini actually rewrites the prompt (Owner: retry == Gemini
        # rewrite, not a blind re-send). No rewrite available → honest fallback now.
        if i + 1 < max_attempts and use_gemini and enable_retry:
            retry_refined = _resolve_prompt(
                target, use_gemini=True, env=env, refine_fn=refine_fn,
                previous_failure_reason=(result.redacted_detail or result.status),
            )
            if retry_refined.available:
                refined = retry_refined
                continue
        break
    fallback_reason = _FALLBACK_REASON_ZH.get(
        result.status if result else "", _FALLBACK_REASON_DEFAULT_ZH
    )
    trace = _build_trace(target, refined, result, all_events,
                         attempts=attempts, latency=latency_total,
                         fallback_reason_zh=fallback_reason)
    logger.info("ms_phase phase=shot_done shot=%s status=%s attempts=%d succeeded=%s elapsed_ms=%d",
                target.shot_id, trace.provider_status, attempts, trace.succeeded,
                int(latency_total * 1000))
    return trace, attempts


def orchestrate_shots(
    targets: Sequence[ShotTarget], *,
    task_id: str, work_dir: str, env: Optional[Mapping[str, str]] = None,
    use_gemini: bool = True, max_video_attempts: int = DEFAULT_MAX_VIDEO_ATTEMPTS,
    enable_retry: bool = True,
    akool_fn: Optional[Callable[..., akool_i2v.AkoolShotResult]] = None,
    refine_fn: Optional[Callable[..., refiner_mod.RefinedPrompt]] = None,
    clock: Callable[[], float] = time.monotonic,
) -> ProviderBatchResult:
    """Run the bounded multi-shot provider batch. Continues past non-fatal failures; never
    stops at the first success; respects the global ``max_video_attempts`` budget.

    ``enable_retry`` toggles the Gemini-rewrite retry (diagnostic load knob).
    ``akool_fn`` / ``refine_fn`` resolve at CALL time (so a monkeypatch on the capability /
    refiner module is honored) and stay injectable for offline unit tests."""
    akool_fn = akool_fn or akool_i2v.generate_shot_clip_akool
    refine_fn = refine_fn or refiner_mod.refine_prompt
    os.makedirs(work_dir, exist_ok=True)
    logger.info("ms_phase phase=provider_batch_start targets=%d max_attempts=%d use_gemini=%s retry=%s",
                len(targets), int(max_video_attempts), use_gemini, enable_retry)
    traces: List[ShotTrace] = []
    attempts_used = 0
    for target in targets:
        remaining = max_video_attempts - attempts_used
        trace, used = _run_one_shot(
            target, task_id=task_id, work_dir=work_dir, env=env, use_gemini=use_gemini,
            akool_fn=akool_fn, refine_fn=refine_fn, clock=clock, budget_remaining=remaining,
            enable_retry=enable_retry,
        )
        attempts_used += used
        traces.append(trace)
    return ProviderBatchResult(tuple(traces), attempts_used)


# ---------------------------------------------------------------------------
# Part C — operator-safe "AI 生成请求过程" panel projection.
# ---------------------------------------------------------------------------

def _panel_status(trace: ShotTrace) -> str:
    if not trace.provider_attempted:
        return PANEL_STATUS_NOT_REQUESTED
    if trace.succeeded and trace.consumed_into_final:
        return PANEL_STATUS_GENERATED
    return PANEL_STATUS_FALLBACK


def _panel_summary_zh(traces: Sequence[ShotTrace]) -> str:
    requested = sum(1 for t in traces if t.provider_attempted)
    generated = sum(1 for t in traces if t.succeeded and t.consumed_into_final)
    fell_back = sum(1 for t in traces if t.provider_attempted and not (t.succeeded and t.consumed_into_final))
    return (
        f"本次共请求 {requested} 个镜头：{generated} 个由 AI 实时生成并进入成片，"
        f"{fell_back} 个回退本地兜底。"
    )


def build_provider_request_panel(traces: Sequence[ShotTrace]) -> Dict[str, object]:
    """Project per-shot traces into the operator-safe "AI 生成请求过程" panel. No secrets."""
    rows: List[Dict[str, object]] = []
    for t in traces:
        status = _panel_status(t)
        rows.append({
            "shot_id": t.shot_id,
            "shot_title_zh": t.shot_title_zh,
            "material_role_label_zh": t.material_role_label_zh,
            "prompt_source_label_zh": _PROMPT_SOURCE_LABEL_ZH.get(t.prompt_source, "系统生成"),
            "prompt_summary_zh": t.prompt_summary_zh,
            "status_code": status,
            "status_label_zh": _PANEL_STATUS_LABEL_ZH[status],
            "entered_final_zh": "是" if status == PANEL_STATUS_GENERATED else "否",
            "generation_time_zh": (f"{t.latency_seconds:.1f}s" if t.provider_attempted else "—"),
            "poll_summary_zh": t.poll_summary_zh,
            "fallback_reason_zh": t.fallback_reason_zh,
        })
    panel = {
        "panel_title_zh": "AI 生成请求过程",
        "panel_key": "ai_generation_request_process",
        "summary_zh": _panel_summary_zh(traces),
        "rows": rows,
    }
    assert_no_provider_trace_leak(panel)
    return panel


def trace_to_diagnostic_dict(trace: ShotTrace) -> Dict[str, object]:
    """Engineering-facing (§J) diagnostic dict — keeps redacted_detail OUT of operator copy."""
    return {
        "shot_id": trace.shot_id, "provider_status": trace.provider_status,
        "provider_attempted": trace.provider_attempted, "attempts": trace.attempts,
        "hosted_input_created": trace.hosted_input_created, "task_created": trace.task_created,
        "clip_downloaded": trace.clip_downloaded, "normalized": trace.normalized,
        "succeeded": trace.succeeded, "consumed_into_final": trace.consumed_into_final,
        "latency_seconds": trace.latency_seconds, "redacted_detail": trace.redacted_detail,
    }


def assert_no_provider_trace_leak(payload: object) -> None:
    """Raise if any operator-facing panel value leaks a forbidden token (vendor/url/key/path)."""
    if isinstance(payload, Mapping):
        for value in payload.values():
            assert_no_provider_trace_leak(value)
    elif isinstance(payload, (list, tuple)):
        for item in payload:
            assert_no_provider_trace_leak(item)
    else:
        text = str(payload).lower()
        hits = [t for t in _PANEL_FORBIDDEN_TOKENS if t in text]
        if hits:
            raise ValueError(f"provider trace panel leaks forbidden tokens: {hits}")
