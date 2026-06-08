"""Matrix Script — Provider Orchestrator + Gemini Prompt Refiner unit tests.

Provider Orchestrator + Multi-Shot Real Result wave (Owner batch), Parts A / B / C.

Fully OFFLINE + HERMETIC: no network, no ffmpeg, no real key. The Gemini caller and the
image_to_video function are injected, so these tests run anywhere. Covers: multi-shot
target run, continue-after-failure, bounded retry-on-failure (Gemini rewrite), attempt
budget cap, prompt-source provenance, honest fallback, the "AI 生成请求过程" panel, and
the no-secret / no-leak guarantees on the refiner output and the panel.
"""
from __future__ import annotations

import time
from typing import Dict, List

import pytest

from gateway.app.services.matrix_script import akool_image_to_video_capability as akool_i2v
from gateway.app.services.matrix_script import gemini_prompt_refiner as refiner
from gateway.app.services.matrix_script import provider_orchestrator as po


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _target(shot_id: str, role: str = "product_reference") -> po.ShotTarget:
    return po.ShotTarget(
        shot_id=shot_id, shot_title_zh=f"镜头{shot_id}", still_path=f"/tmp/{shot_id}.png",
        base_prompt=f"base prompt for {shot_id}", base_negative="text, watermark",
        visual_goal="sunlit cherry tomatoes by the sea", narration_line="夏天的味道",
        script_segment="海边小番茄", motion_instruction="slow push-in",
        material_role=role, material_role_label_zh="产品素材",
    )


def _akool_ok(*, still_path, out_clip, task_id, shot_id, prompt=akool_i2v.DEFAULT_PROMPT,
              env=None, on_event=None, **kw):
    for ev in ("hosted_input_created", "task_created", "poll_processing", "poll_success",
               "clip_downloaded", "normalized"):
        if on_event:
            on_event(ev)
    return akool_i2v.AkoolShotResult(akool_i2v.STATUS_PROVIDER_SUCCESS, out_clip, True, "")


def _akool_fail(*, still_path, out_clip, task_id, shot_id, prompt=akool_i2v.DEFAULT_PROMPT,
                env=None, on_event=None, **kw):
    for ev in ("hosted_input_created", "task_created", "poll_processing", "poll_failed"):
        if on_event:
            on_event(ev)
    return akool_i2v.AkoolShotResult(akool_i2v.STATUS_PROVIDER_FAILED, None, True, "provider_status_failed")


def _no_gemini(_text: str) -> str:
    raise refiner.RefinerUnavailable("http_404")


# --------------------------------------------------------------------------- #
# Gemini Prompt Refiner (Part B)
# --------------------------------------------------------------------------- #

def test_refiner_falls_back_deterministic_without_key():
    out = refiner.refine_prompt(base_prompt="bp", base_negative="bn", env={})
    assert out.available is False
    assert out.source == refiner.SOURCE_DETERMINISTIC
    assert out.provider_prompt == "bp" and out.negative_prompt == "bn"


def test_refiner_uses_gemini_when_caller_succeeds():
    caller = lambda t: '{"prompt": "cinematic dolly over glistening tomatoes", "negative": "blur, text"}'
    out = refiner.refine_prompt(base_prompt="bp", base_negative="bn", env={"GEMINI_API_KEY": "x"}, caller=caller)
    assert out.available is True
    assert out.source == refiner.SOURCE_GEMINI
    assert out.provider_prompt == "cinematic dolly over glistening tomatoes"
    assert out.negative_prompt == "blur, text"


def test_refiner_retry_source_when_previous_failure():
    caller = lambda t: '{"prompt": "simpler safe shot", "negative": "artifacts"}'
    out = refiner.refine_prompt(base_prompt="bp", base_negative="bn",
                                previous_failure_reason="provider_status_failed",
                                env={"GEMINI_API_KEY": "x"}, caller=caller)
    assert out.available is True
    assert out.source == refiner.SOURCE_RETRY


def test_refiner_parse_failure_degrades_to_deterministic():
    out = refiner.refine_prompt(base_prompt="bp", base_negative="bn",
                                env={"GEMINI_API_KEY": "x"}, caller=lambda t: "not json at all")
    assert out.available is False
    assert out.source == refiner.SOURCE_DETERMINISTIC
    assert out.provider_prompt == "bp"


def test_refiner_strips_code_fences():
    caller = lambda t: '```json\n{"prompt": "p1", "negative": "n1"}\n```'
    out = refiner.refine_prompt(base_prompt="bp", base_negative="bn",
                                env={"GEMINI_API_KEY": "x"}, caller=caller)
    assert out.available is True and out.provider_prompt == "p1"


def test_refiner_unavailable_when_caller_raises():
    out = refiner.refine_prompt(base_prompt="bp", base_negative="bn",
                                env={"GEMINI_API_KEY": "x"}, caller=_no_gemini)
    assert out.available is False and out.source == refiner.SOURCE_DETERMINISTIC
    assert out.redacted_detail == "http_404"


def test_refiner_never_leaks_key_in_output():
    # Even if the model echoes nonsense, the operator summary is a fixed safe string and
    # no field carries a key/url. (The key is only ever read, never returned.)
    caller = lambda t: '{"prompt": "p", "negative": "n"}'
    out = refiner.refine_prompt(base_prompt="bp", base_negative="bn",
                                env={"GEMINI_API_KEY": "SECRET-AIza-xyz"}, caller=caller)
    blob = (out.operator_summary_zh + out.redacted_detail + out.source).lower()
    assert "secret-aiza" not in blob and "aiza" not in blob


def test_refiner_gemini_available_predicate():
    assert refiner.gemini_available({"GEMINI_API_KEY": "k", "GEMINI_BASE_URL": "u", "GEMINI_MODEL": "m"})
    assert not refiner.gemini_available({"GEMINI_API_KEY": "k"})  # missing base/model
    assert not refiner.gemini_available({})


# --------------------------------------------------------------------------- #
# Provider Orchestrator (Part A)
# --------------------------------------------------------------------------- #

def test_multi_shot_all_succeed(tmp_path):
    targets = [_target("shot01", "scene_reference"), _target("shot02"), _target("shot03", "character_reference")]
    batch = po.orchestrate_shots(targets, task_id="t", work_dir=str(tmp_path), env={},
                                 use_gemini=False, akool_fn=_akool_ok)
    assert batch.success_count == 3
    assert set(batch.clips_by_shot) == {"shot01", "shot02", "shot03"}
    for tr in batch.traces:
        assert tr.succeeded and tr.provider_attempted
        assert tr.hosted_input_created and tr.task_created and tr.clip_downloaded and tr.normalized
        assert "成功" in tr.poll_summary_zh
        assert tr.fallback_reason_zh == ""


def test_continues_past_failure_does_not_stop_at_first(tmp_path):
    def mixed(*, shot_id, **kw):
        return _akool_ok(shot_id=shot_id, **kw) if shot_id != "shot02" else _akool_fail(shot_id=shot_id, **kw)
    targets = [_target("shot01"), _target("shot02"), _target("shot03")]
    batch = po.orchestrate_shots(targets, task_id="t", work_dir=str(tmp_path), env={},
                                 use_gemini=False, akool_fn=mixed)
    # shot02 failed but shot03 was still attempted (no early stop).
    assert set(batch.clips_by_shot) == {"shot01", "shot03"}
    failed = [t for t in batch.traces if t.shot_id == "shot02"][0]
    assert failed.succeeded is False
    assert failed.fallback_reason_zh and "回退" in failed.fallback_reason_zh


def test_retry_on_failure_then_success_uses_gemini_rewrite(tmp_path):
    calls: Dict[str, int] = {"n": 0}

    def fail_then_ok(*, still_path, out_clip, task_id, shot_id, prompt=akool_i2v.DEFAULT_PROMPT,
                     env=None, on_event=None, **kw):
        calls["n"] += 1
        if calls["n"] == 1:
            return _akool_fail(still_path=still_path, out_clip=out_clip, task_id=task_id,
                               shot_id=shot_id, on_event=on_event)
        return _akool_ok(still_path=still_path, out_clip=out_clip, task_id=task_id,
                         shot_id=shot_id, on_event=on_event)

    refine_calls: List[str] = []

    def refine_fn(*, previous_failure_reason=None, **kw):
        refine_calls.append(previous_failure_reason or "initial")
        src = refiner.SOURCE_RETRY if previous_failure_reason else refiner.SOURCE_GEMINI
        return refiner.RefinedPrompt(src, "refined prompt", "neg", "AI summary", available=True)

    batch = po.orchestrate_shots([_target("shot01")], task_id="t", work_dir=str(tmp_path),
                                 env={"GEMINI_API_KEY": "x"}, use_gemini=True,
                                 akool_fn=fail_then_ok, refine_fn=refine_fn)
    tr = batch.traces[0]
    assert tr.succeeded is True
    assert tr.attempts == 2
    assert tr.prompt_source == refiner.SOURCE_RETRY        # the winning attempt was the rewrite
    assert refine_calls[0] == "initial" and refine_calls[1]  # a retry refinement happened


def test_budget_cap_limits_total_attempts(tmp_path):
    targets = [_target(f"shot0{i}") for i in (1, 2, 3, 4, 5, 6)]
    batch = po.orchestrate_shots(targets, task_id="t", work_dir=str(tmp_path), env={},
                                 use_gemini=False, akool_fn=_akool_fail, max_video_attempts=3)
    # All fail (no retry budget left after 3 attempts); attempts capped at 3.
    assert batch.attempts_used == 3
    attempted = [t for t in batch.traces if t.provider_attempted]
    assert len(attempted) == 3
    not_requested = [t for t in batch.traces if not t.provider_attempted]
    assert len(not_requested) == 3  # the rest never requested (honest)


def test_prompt_source_deterministic_when_gemini_off(tmp_path):
    batch = po.orchestrate_shots([_target("shot01")], task_id="t", work_dir=str(tmp_path),
                                 env={}, use_gemini=False, akool_fn=_akool_ok)
    assert batch.traces[0].prompt_source == refiner.SOURCE_DETERMINISTIC


def test_prompt_source_gemini_when_refine_available(tmp_path):
    def refine_fn(**kw):
        return refiner.RefinedPrompt(refiner.SOURCE_GEMINI, "rp", "rn", "AI 强化", available=True)
    batch = po.orchestrate_shots([_target("shot01")], task_id="t", work_dir=str(tmp_path),
                                 env={"GEMINI_API_KEY": "x"}, use_gemini=True,
                                 akool_fn=_akool_ok, refine_fn=refine_fn)
    assert batch.traces[0].prompt_source == refiner.SOURCE_GEMINI


# --------------------------------------------------------------------------- #
# Part C — "AI 生成请求过程" panel + no-leak
# --------------------------------------------------------------------------- #

def test_panel_lists_generated_and_fallback(tmp_path):
    def mixed(*, shot_id, **kw):
        return _akool_ok(shot_id=shot_id, **kw) if shot_id != "shot03" else _akool_fail(shot_id=shot_id, **kw)
    targets = [_target("shot01"), _target("shot02"), _target("shot03")]
    batch = po.orchestrate_shots(targets, task_id="t", work_dir=str(tmp_path), env={},
                                 use_gemini=False, akool_fn=mixed)
    # mark consumed for the successes (compose step does this in the orchestrator).
    traces = [t.consumed() if t.succeeded else t for t in batch.traces]
    panel = po.build_provider_request_panel(traces)
    assert panel["panel_title_zh"] == "AI 生成请求过程"
    by = {r["shot_id"]: r for r in panel["rows"]}
    assert by["shot01"]["status_code"] == po.PANEL_STATUS_GENERATED
    assert by["shot01"]["entered_final_zh"] == "是"
    assert by["shot03"]["status_code"] == po.PANEL_STATUS_FALLBACK
    assert by["shot03"]["entered_final_zh"] == "否"
    assert "生成" in panel["summary_zh"]


def test_panel_status_not_requested_when_no_attempt(tmp_path):
    targets = [_target("shot01"), _target("shot02")]
    batch = po.orchestrate_shots(targets, task_id="t", work_dir=str(tmp_path), env={},
                                 use_gemini=False, akool_fn=_akool_fail, max_video_attempts=1)
    panel = po.build_provider_request_panel(batch.traces)
    statuses = {r["shot_id"]: r["status_code"] for r in panel["rows"]}
    assert statuses["shot02"] == po.PANEL_STATUS_NOT_REQUESTED


def test_panel_no_leak_with_dirty_trace():
    # Even a trace whose diagnostic detail carries a URL/path must not leak via the panel
    # (operator-facing fields are fixed strings; redacted_detail is NOT rendered).
    dirty = po.ShotTrace(
        shot_id="shot01", shot_title_zh="镜头1", material_role="product_reference",
        material_role_label_zh="产品素材", prompt_source=refiner.SOURCE_GEMINI,
        prompt_summary_zh="AI 已强化生成要求：更具体的画面、光线与运镜描述。",
        provider_attempted=True, provider_status=akool_i2v.STATUS_PROVIDER_SUCCESS,
        hosted_input_created=True, task_created=True, poll_summary_zh="轮询：处理中→成功",
        clip_downloaded=True, normalized=True, consumed_into_final=True,
        fallback_reason_zh="", latency_seconds=4.2, attempts=1,
        redacted_detail="https://akool.example/raw/abc?key=SECRET",  # must NOT surface
        clip_path="/Users/x/work/shot01.mp4", succeeded=True,
    )
    panel = po.build_provider_request_panel([dirty])   # raises if it leaks
    blob = str(panel).lower()
    for tok in ("http", "://", "akool", "secret", ".mp4", "/users/", "key="):
        assert tok not in blob


def test_assert_no_provider_trace_leak_raises_on_url():
    with pytest.raises(ValueError):
        po.assert_no_provider_trace_leak({"x": "see https://leak.example"})


def test_diagnostic_dict_keeps_redacted_detail_out_of_panel():
    tr = po.ShotTrace(
        shot_id="s", shot_title_zh="t", material_role="r", material_role_label_zh="L",
        prompt_source=refiner.SOURCE_DETERMINISTIC, prompt_summary_zh="s",
        provider_attempted=True, provider_status=akool_i2v.STATUS_PROVIDER_FAILED,
        hosted_input_created=True, task_created=True, poll_summary_zh="轮询：失败",
        clip_downloaded=False, normalized=False, consumed_into_final=False,
        fallback_reason_zh="实时生成未成功，已回退本地兜底镜头。", latency_seconds=1.0,
        attempts=1, redacted_detail="err_TimeoutError",
    )
    diag = po.trace_to_diagnostic_dict(tr)
    assert diag["redacted_detail"] == "err_TimeoutError"
    assert diag["provider_status"] == akool_i2v.STATUS_PROVIDER_FAILED
