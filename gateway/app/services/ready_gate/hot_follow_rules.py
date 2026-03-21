"""Hot Follow ready-gate rules (TASK-2.3).

Declares the complete ``ReadyGateSpec`` for the Hot Follow production line,
translating the hardcoded if/else logic from ``compute_hot_follow_state()``
into declarative Signal / Gate / Blocking / Override rules.

Every extract callable maps 1:1 to the original code lines in
``hot_follow_state.py`` (pre-refactor).
"""

from __future__ import annotations

from typing import Any, Dict

from .engine import (
    BlockingRule,
    GateRule,
    OverrideRule,
    ReadyGateSpec,
    Signal,
)


# ---------------------------------------------------------------------------
# Helper: safe dict access (mirrors _as_dict in hot_follow_state.py)
# ---------------------------------------------------------------------------

def _d(v: Any) -> Dict[str, Any]:
    return v if isinstance(v, dict) else {}


# ---------------------------------------------------------------------------
# Signal extract functions
# ---------------------------------------------------------------------------
# Each function signature: (task: dict, state: dict) -> bool
# These are standalone functions (not lambdas) for debuggability and testability.


def _extract_final_exists(task: dict, state: dict) -> bool:
    """Check if a final video file physically exists (any version, fresh or stale)."""
    final = _d(state.get("final"))
    historical_final = _d(state.get("historical_final"))
    artifact_facts = _d(state.get("artifact_facts"))
    if bool(final.get("exists")):
        return True
    if bool(historical_final.get("exists")):
        return True
    if bool(artifact_facts.get("final_exists")):
        return True
    # Also check evidence from URL resolution
    if state.get("final_url") or state.get("final_video_url"):
        return True
    return False


def _extract_final_fresh(task: dict, state: dict) -> bool:
    """Final video is fresh — it incorporates the current subtitle and audio revision.

    A stale final (composed before the latest subtitle save or re-dub) is NOT
    fresh and must not be counted as a valid compose output for the gate.
    """
    final = _d(state.get("final"))
    # Explicit stale_reason on the state or on final_info → not fresh.
    if state.get("final_stale_reason") or final.get("stale_reason"):
        return False
    # fresh flag set by compute_composed_state().
    fresh_hint = final.get("fresh")
    if fresh_hint is not None:
        return bool(fresh_hint)
    # No freshness metadata available — treat as not fresh so compose runs.
    return False


def _extract_audio_done(task: dict, state: dict) -> bool:
    """audio_status in {"done","ready","success","completed"}."""
    audio = _d(state.get("audio"))
    status = str(audio.get("status") or task.get("dub_status") or "").strip().lower()
    return status in {"done", "ready", "success", "completed"}


def _extract_voiceover_exists(task: dict, state: dict) -> bool:
    """Voiceover artifact exists in any known location."""
    audio = _d(state.get("audio"))
    media = _d(state.get("media"))
    return bool(
        audio.get("voiceover_url")
        or media.get("voiceover_url")
        or task.get("mm_audio_key")
        or task.get("mm_audio_path")
    )


def _extract_tts_voice_valid(task: dict, state: dict) -> bool:
    """TTS voice is set and not a sentinel value."""
    audio = _d(state.get("audio"))
    tts_voice = str(audio.get("tts_voice") or task.get("voice_id") or "").strip()
    return bool(tts_voice and tts_voice not in {"-", "none", "null"})


def _extract_audio_ready(task: dict, state: dict) -> bool:
    """Audio readiness: hint override OR (audio_done AND voiceover_exists AND tts_voice_valid).

    Preserves the hint-priority pattern from original L167-171.
    """
    audio = _d(state.get("audio"))
    hint = audio.get("audio_ready")
    if hint is not None:
        return bool(hint)
    # Fall through to composite check
    return (
        _extract_audio_done(task, state)
        and _extract_voiceover_exists(task, state)
        and _extract_tts_voice_valid(task, state)
    )


def _extract_subtitle_artifact_exists(task: dict, state: dict) -> bool:
    """Subtitle artifact exists in any known location."""
    subs = _d(state.get("subtitles"))
    return bool(
        subs.get("subtitle_artifact_exists")
        or subs.get("actual_burn_subtitle_source")
        or subs.get("edited_text")
        or subs.get("srt_text")
        or task.get("mm_srt_path")
        or task.get("origin_srt_path")
    )


def _extract_subtitle_ready(task: dict, state: dict) -> bool:
    """Subtitle readiness: hint override OR subtitle_artifact_exists.

    Preserves the hint-priority pattern from original L172-181.
    """
    subs = _d(state.get("subtitles"))
    hint = subs.get("subtitle_ready")
    if hint is not None:
        return bool(hint)
    return _extract_subtitle_artifact_exists(task, state)


def _extract_no_dub(task: dict, state: dict) -> bool:
    """Raw no_dub flag (before override application)."""
    audio = _d(state.get("audio"))
    return bool(audio.get("no_dub"))


# ---------------------------------------------------------------------------
# Reason extract functions
# ---------------------------------------------------------------------------


def _reason_subtitle_ready(task: dict, state: dict) -> str:
    subs = _d(state.get("subtitles"))
    explicit = subs.get("subtitle_ready_reason")
    if explicit:
        return str(explicit)
    return "ready" if _extract_subtitle_ready(task, state) else "subtitle_missing"


def _reason_audio_ready(task: dict, state: dict) -> str:
    audio = _d(state.get("audio"))
    explicit = audio.get("audio_ready_reason")
    if explicit:
        return str(explicit)
    return "ready" if _extract_audio_ready(task, state) else "audio_not_ready"


def _reason_no_dub(task: dict, state: dict) -> str:
    audio = _d(state.get("audio"))
    return str(audio.get("no_dub_reason") or "").strip() or ""


# ---------------------------------------------------------------------------
# HOT_FOLLOW_GATE_SPEC
# ---------------------------------------------------------------------------

HOT_FOLLOW_GATE_SPEC = ReadyGateSpec(
    line_id="hot_follow_line",

    # ── Signals ───────────────────────────────────────────────────────────
    signals=(
        Signal("final_exists",             _extract_final_exists),
        Signal("final_fresh",              _extract_final_fresh),
        Signal("audio_done",               _extract_audio_done),
        Signal("voiceover_exists",         _extract_voiceover_exists),
        Signal("tts_voice_valid",          _extract_tts_voice_valid),
        Signal(
            "audio_ready",
            _extract_audio_ready,
            reason_key="audio_ready_reason",
            reason_extract=_reason_audio_ready,
        ),
        Signal("subtitle_artifact_exists", _extract_subtitle_artifact_exists),
        Signal(
            "subtitle_ready",
            _extract_subtitle_ready,
            reason_key="subtitle_ready_reason",
            reason_extract=_reason_subtitle_ready,
        ),
        Signal(
            "no_dub",
            _extract_no_dub,
            reason_key="no_dub_reason",
            reason_extract=_reason_no_dub,
        ),
    ),

    # ── Overrides (artifact wins over flag) ───────────────────────────────
    overrides=(
        OverrideRule(evidence_signal="voiceover_exists", target_signal="no_dub", force_value=False),
        OverrideRule(evidence_signal="audio_ready",      target_signal="no_dub", force_value=False),
    ),

    # ── Gates ─────────────────────────────────────────────────────────────
    # compose_ready = final_exists AND final_fresh AND (audio_ready OR no_dub)
    # final_fresh = False when subtitle or audio changed after the last compose.
    gates=(
        GateRule("compose_ready",  requires=("final_exists", "final_fresh"), unless=("audio_ready", "no_dub")),
        GateRule("publish_ready",  requires=("compose_ready",), unless=()),
    ),

    # ── Blocking rules (all gated by compose_ready=False) ─────────────────
    blocking=(
        # Always emit when gate is false
        BlockingRule("compose_not_done",   when_missing="__always__"),
        # Final is stale (composed before current subtitle/audio)
        BlockingRule("final_stale",        when_missing="final_fresh",        extra_requires=("final_exists",)),
        # Subtitle not ready
        BlockingRule("subtitle_not_ready", when_missing="subtitle_ready"),
        # Audio steps — skipped if no_dub
        BlockingRule("audio_not_done",     when_missing="audio_done",         unless_signal="no_dub"),
        BlockingRule("voiceover_missing",  when_missing="voiceover_exists",   unless_signal="no_dub"),
        BlockingRule("tts_voice_invalid",  when_missing="tts_voice_valid",    unless_signal="no_dub"),
        # audio_not_ready only when final exists (original L232-233)
        BlockingRule("audio_not_ready",    when_missing="audio_ready",        unless_signal="no_dub",
                     extra_requires=("final_exists",)),
        # Dynamic no_dub_reason: only when no_dub=True AND subtitle not ready (original L236-237)
        BlockingRule("",                   when_missing="subtitle_ready",
                     extra_requires=("no_dub",), reason_from="no_dub_reason"),
    ),
)
