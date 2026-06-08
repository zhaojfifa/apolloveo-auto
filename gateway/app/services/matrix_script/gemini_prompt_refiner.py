"""Matrix Script — Gemini Prompt Refiner (Provider Orchestrator + Multi-Shot wave, Part B).

A BACKEND production helper that asks Gemini to STRENGTHEN a script-derived provider
prompt before it is sent to the image_to_video provider, and to REWRITE the prompt on a
failed attempt. It is *not* a UI vendor selector and it is *not* a source of truth — it
is an optional refinement layer in front of the deterministic
:mod:`prompt_builder` / :func:`generation_plan_view.build_provider_prompt_for_shot`.

Audience separation (mirrors prompt_builder §8 of the Storyboard Control gate spec):
  - the **provider prompt / negative** it returns are RUNTIME-TRANSIENT — fed to the
    provider, NEVER surfaced to the operator as raw text.
  - the **operator summary** it returns is a fixed, operator-safe Chinese one-liner
    (no vendor brand, no secret, no raw English payload). This is the only thing the
    "AI 生成请求过程" panel shows for prompt provenance.

Hard boundaries (Owner batch + ``ops/env/secret_loading_baseline_v1.md``):
  - Canonical env names only (``GEMINI_API_KEY`` / ``GEMINI_BASE_URL`` / ``GEMINI_MODEL``);
    no literal secret default; **fail closed** — missing key ⇒ ``available=False`` and the
    caller keeps the deterministic prompt (we NEVER pretend Gemini ran).
  - The API key is passed only on the outgoing request. It is NEVER returned, logged, or
    placed in any exception message. On any HTTP/transport error we raise
    :class:`RefinerUnavailable` carrying ONLY a redacted ``http_<code>`` / ``err_<Class>``
    token (``from None`` drops the chained httpx exception whose text embeds the URL+key).
  - Network is injectable (``caller=``) so unit tests never touch the network or a key.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Optional

# Closed prompt-source codes (operator-safe provenance; no vendor brand).
SOURCE_DETERMINISTIC = "deterministic"
SOURCE_GEMINI = "gemini_refined"
SOURCE_RETRY = "retry_refined"

# Fixed, operator-safe Chinese provenance summaries (no vendor name, no raw payload).
_SUMMARY_ZH = {
    SOURCE_DETERMINISTIC: "使用系统生成的生成要求（脚本派生）。",
    SOURCE_GEMINI: "AI 已强化生成要求：更具体的画面、光线与运镜描述。",
    SOURCE_RETRY: "AI 已根据上次未成功的结果重写生成要求后重试。",
}

_CANON_KEY = "GEMINI_API_KEY"
_CANON_BASE = "GEMINI_BASE_URL"
_CANON_MODEL = "GEMINI_MODEL"


class RefinerUnavailable(RuntimeError):
    """Gemini could not be used. Message is REDACTED (``http_<code>`` / ``err_<Class>`` /
    ``config_missing`` / ``parse_failed``) — never a URL, key, or raw provider message."""


@dataclass(frozen=True)
class RefinedPrompt:
    """Outcome of one refinement. ``provider_prompt`` / ``negative_prompt`` are
    runtime-transient (fed to the provider, never operator-surfaced). ``operator_summary_zh``
    is the only operator-facing provenance string."""

    source: str                     # SOURCE_*
    provider_prompt: str            # runtime-transient
    negative_prompt: str            # runtime-transient
    operator_summary_zh: str        # operator-safe (fixed string)
    available: bool                 # True only when Gemini actually produced the text
    redacted_detail: str = ""       # diagnostic only (§J); class/status token, never raw


def gemini_available(env: Optional[Mapping[str, str]] = None) -> bool:
    """True only when the canonical key + base + model are all configured (no call made)."""
    src = env if env is not None else os.environ
    return bool(
        (src.get(_CANON_KEY) or "").strip()
        and (src.get(_CANON_BASE) or "").strip()
        and (src.get(_CANON_MODEL) or "").strip()
    )


def _build_instruction(
    *, base_prompt: str, visual_goal: str, narration_line: str, script_segment: str,
    motion_instruction: str, material_role: str, product_constraints: str,
    previous_failure_reason: Optional[str],
) -> str:
    """Deterministic instruction text for Gemini. Pure string assembly (no secret)."""
    role = (material_role or "").strip() or "unspecified"
    lines = [
        "You are a senior image-to-video prompt engineer for short vertical (9:16) "
        "commercial product video. Strengthen the shot prompt so the generated clip "
        "shows REAL motion and cinematic life, not a static photo with a pan.",
        f"Shot visual goal: {visual_goal or base_prompt}",
        f"Narration (context, do not render as text): {narration_line}",
        f"Script segment (context): {script_segment}",
        f"Camera / motion intent: {motion_instruction}",
        f"Material role: {role}",
    ]
    if product_constraints.strip():
        lines.append(f"Product fidelity constraints: {product_constraints.strip()}")
    if previous_failure_reason:
        lines.append(
            "The PREVIOUS attempt did not succeed. Rewrite the prompt to be simpler, "
            "safer and more literal to improve generation success; avoid anything that "
            f"could trip a provider safety/quality filter. Prior issue (redacted): "
            f"{previous_failure_reason}"
        )
    lines.append(
        "Return STRICT JSON only, no markdown, with exactly two keys: "
        '"prompt" (a single English image-to-video prompt, <60 words, concrete motion + '
        'lighting + subject fidelity) and "negative" (a comma-separated English negative '
        "list). Do not include any other text."
    )
    return "\n".join(lines)


def _default_gemini_call(
    user_text: str, *, env: Optional[Mapping[str, str]],
    temperature: float = 0.5, max_output_tokens: int = 1024,
) -> str:
    """Real sync Gemini ``generateContent`` call. Returns model text or raises
    :class:`RefinerUnavailable` with a REDACTED token only (never URL/key/body)."""
    src = env if env is not None else os.environ
    key = (src.get(_CANON_KEY) or "").strip()
    base = (src.get(_CANON_BASE) or "").strip().rstrip("/")
    model = (src.get(_CANON_MODEL) or "").strip()
    if not (key and base and model):
        raise RefinerUnavailable("config_missing")
    import httpx

    url = f"{base}/models/{model}:generateContent"
    payload = {
        "contents": [{"role": "user", "parts": [{"text": user_text}]}],
        "generationConfig": {
            "temperature": temperature,
            "topP": 0.9,
            "maxOutputTokens": max_output_tokens,
            # Gemini 2.5 "flash" is a thinking model; reasoning shares the output budget and
            # truncated the JSON. Disable thinking — this is a short deterministic JSON task.
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }
    try:
        with httpx.Client(timeout=httpx.Timeout(60.0, connect=15.0)) as client:
            resp = client.post(url, params={"key": key}, json=payload)
    except Exception as exc:  # noqa: BLE001 — redact: class only, drop chained (URL+key) cause
        raise RefinerUnavailable(f"err_{exc.__class__.__name__}") from None
    if resp.status_code != 200:
        # Do NOT include resp.text / resp.url — both can embed the key/url.
        raise RefinerUnavailable(f"http_{resp.status_code}")
    try:
        data = resp.json()
        return str(data["candidates"][0]["content"]["parts"][0]["text"]).strip()
    except Exception:  # noqa: BLE001
        raise RefinerUnavailable("parse_failed") from None


def _parse_refined(text: str) -> "tuple[str, str]":
    """Parse Gemini's JSON ``{prompt, negative}``; tolerate code fences. Raise on miss."""
    body = text.strip()
    if body.startswith("```"):
        body = body.strip("`")
        # drop a leading language hint like ```json
        nl = body.find("\n")
        if nl != -1 and body[:nl].strip().lower() in ("json", ""):
            body = body[nl + 1:]
    try:
        obj = json.loads(body)
    except json.JSONDecodeError:
        # Tolerant: extract the first {...} object if the model wrapped it in prose.
        i, j = body.find("{"), body.rfind("}")
        if i == -1 or j == -1 or j <= i:
            raise
        obj = json.loads(body[i:j + 1])
    if not isinstance(obj, dict):
        raise ValueError("not an object")
    prompt = str(obj.get("prompt") or "").strip()
    negative = str(obj.get("negative") or "").strip()
    if not prompt:
        raise ValueError("empty prompt")
    return prompt, negative


def refine_prompt(
    *,
    base_prompt: str,
    base_negative: str,
    visual_goal: str = "",
    narration_line: str = "",
    script_segment: str = "",
    motion_instruction: str = "",
    material_role: str = "",
    product_constraints: str = "",
    previous_failure_reason: Optional[str] = None,
    env: Optional[Mapping[str, str]] = None,
    caller: Optional[Callable[[str], str]] = None,
) -> RefinedPrompt:
    """Strengthen (or, with ``previous_failure_reason``, rewrite) the provider prompt.

    Falls back to the deterministic ``base_prompt`` / ``base_negative`` (``available=False``,
    ``source=deterministic``) whenever Gemini is not configured or the call/parse fails —
    we NEVER fabricate a Gemini result. ``caller`` is injectable so tests run offline.
    """
    target_source = SOURCE_RETRY if previous_failure_reason else SOURCE_GEMINI

    if caller is None and not gemini_available(env):
        return RefinedPrompt(
            SOURCE_DETERMINISTIC, base_prompt, base_negative,
            _SUMMARY_ZH[SOURCE_DETERMINISTIC], available=False, redacted_detail="config_missing",
        )

    instruction = _build_instruction(
        base_prompt=base_prompt, visual_goal=visual_goal, narration_line=narration_line,
        script_segment=script_segment, motion_instruction=motion_instruction,
        material_role=material_role, product_constraints=product_constraints,
        previous_failure_reason=previous_failure_reason,
    )
    call = caller if caller is not None else (lambda t: _default_gemini_call(t, env=env))
    try:
        raw = call(instruction)
        prompt, negative = _parse_refined(raw)
    except RefinerUnavailable as exc:
        return RefinedPrompt(
            SOURCE_DETERMINISTIC, base_prompt, base_negative,
            _SUMMARY_ZH[SOURCE_DETERMINISTIC], available=False, redacted_detail=str(exc),
        )
    except Exception as exc:  # noqa: BLE001 — parse/other: redact to class only
        return RefinedPrompt(
            SOURCE_DETERMINISTIC, base_prompt, base_negative,
            _SUMMARY_ZH[SOURCE_DETERMINISTIC], available=False,
            redacted_detail=f"refine_{exc.__class__.__name__}",
        )

    return RefinedPrompt(
        target_source, prompt, (negative or base_negative),
        _SUMMARY_ZH[target_source], available=True, redacted_detail="",
    )
