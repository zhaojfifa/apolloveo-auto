"""Hot Follow ready-gate rules (TASK-2.3 / VeoMVP01 PR-4).

Loads the ``ReadyGateSpec`` for the Hot Follow production line from the frozen
YAML contract, while keeping the signal extractor library in Python.

Every extract callable maps 1:1 to the original code lines in
``hot_follow_state.py`` (pre-refactor).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict
import yaml

from .engine import (
    BlockingRule,
    GateRule,
    OverrideRule,
    ReadyGateSpec,
    Signal,
)


REPO_ROOT = Path(__file__).resolve().parents[4]
HOT_FOLLOW_READY_GATE_CONTRACT_REF = "docs/contracts/hot_follow_ready_gate.yaml"
HOT_FOLLOW_READY_GATE_RUNTIME_REF = "gateway/app/services/ready_gate/hot_follow_rules.py"


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
    """Current TTS voiceover URL exists on the audio truth surface."""
    audio = _d(state.get("audio"))
    return bool(
        audio.get("dub_preview_url")
        or audio.get("tts_voiceover_url")
        or audio.get("voiceover_url")
    )


def _extract_tts_voice_valid(task: dict, state: dict) -> bool:
    """TTS voice is set and not a sentinel value."""
    audio = _d(state.get("audio"))
    tts_voice = str(audio.get("tts_voice") or task.get("voice_id") or "").strip()
    return bool(tts_voice and tts_voice not in {"-", "none", "null"})


def _extract_audio_ready(task: dict, state: dict) -> bool:
    """Audio readiness: explicit voice-state hint or current TTS voiceover fact.

    Raw compatibility artifact keys are intentionally ignored here. Source audio,
    uploaded BGM, or stale generic audio references must not satisfy dub truth.
    """
    audio = _d(state.get("audio"))
    hint = audio.get("audio_ready")
    if hint is not None:
        return bool(hint)
    return (
        bool(audio.get("dub_current"))
        and _extract_voiceover_exists(task, state)
        and _extract_tts_voice_valid(task, state)
    )


def _extract_subtitle_artifact_exists(task: dict, state: dict) -> bool:
    """Current target subtitle artifact exists.

    Parse/source subtitles are helper evidence only. They must not satisfy
    target-subtitle readiness when explicit subtitle truth is absent.
    """
    subs = _d(state.get("subtitles"))
    actual_source = str(subs.get("actual_burn_subtitle_source") or "").strip().lower()
    target_source = bool(actual_source and actual_source not in {"origin.srt", "source.srt"})
    return bool(
        (subs.get("subtitle_artifact_exists") and target_source)
        or target_source
        or task.get("mm_srt_path")
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
    return bool(audio.get("no_dub")) or _extract_no_tts_compose_allowed(task, state)


def _extract_compose_blocked(task: dict, state: dict) -> bool:
    artifact_facts = _d(state.get("artifact_facts"))
    compose_input = _d(artifact_facts.get("compose_input"))
    return bool(artifact_facts.get("compose_input_blocked") or compose_input.get("blocked"))


def _extract_no_tts_compose_allowed(task: dict, state: dict) -> bool:
    artifact_facts = _d(state.get("artifact_facts"))
    audio_lane = _d(artifact_facts.get("audio_lane"))
    mode = str(artifact_facts.get("audio_lane_mode") or audio_lane.get("mode") or "").strip().lower()
    no_tts = bool(audio_lane.get("no_tts") or artifact_facts.get("tts_voiceover_exists") is False)
    source_audio_preserved = bool(audio_lane.get("source_audio_preserved"))
    bgm_configured = bool(audio_lane.get("bgm_configured"))
    return bool(no_tts and (source_audio_preserved or bgm_configured or mode == "source_audio_preserved_no_tts"))


def _extract_no_dub_compose_allowed(task: dict, state: dict) -> bool:
    """No-dub mode may bypass subtitle/audio blockers for final compose input checks."""
    audio = _d(state.get("audio"))
    reason = str(audio.get("no_dub_reason") or "").strip().lower()
    return (bool(audio.get("no_dub")) and reason in {"target_subtitle_empty", "dub_input_empty"}) or _extract_no_tts_compose_allowed(task, state)


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
    explicit = str(audio.get("no_dub_reason") or "").strip()
    if explicit:
        return explicit
    artifact_facts = _d(state.get("artifact_facts"))
    audio_lane = _d(artifact_facts.get("audio_lane"))
    mode = str(artifact_facts.get("audio_lane_mode") or audio_lane.get("mode") or "").strip().lower()
    if _extract_no_tts_compose_allowed(task, state):
        return "source_audio_preserved_no_tts" if mode == "source_audio_preserved_no_tts" else "bgm_only_no_tts"
    return ""


def _reason_compose_blocked(task: dict, state: dict) -> str:
    artifact_facts = _d(state.get("artifact_facts"))
    compose_input = _d(artifact_facts.get("compose_input"))
    return str(
        artifact_facts.get("compose_input_reason")
        or compose_input.get("reason")
        or "compose_input_blocked"
    ).strip()


_SIGNAL_EXTRACTORS = {
    "final_exists": _extract_final_exists,
    "final_fresh": _extract_final_fresh,
    "audio_done": _extract_audio_done,
    "voiceover_exists": _extract_voiceover_exists,
    "tts_voice_valid": _extract_tts_voice_valid,
    "audio_ready": _extract_audio_ready,
    "subtitle_artifact_exists": _extract_subtitle_artifact_exists,
    "subtitle_ready": _extract_subtitle_ready,
    "no_dub": _extract_no_dub,
    "no_dub_compose_allowed": _extract_no_dub_compose_allowed,
    "compose_blocked": _extract_compose_blocked,
    "no_tts_compose_allowed": _extract_no_tts_compose_allowed,
}

_REASON_EXTRACTORS = {
    "subtitle_ready_reason": _reason_subtitle_ready,
    "audio_ready_reason": _reason_audio_ready,
    "no_dub_reason": _reason_no_dub,
    "compose_blocked_reason": _reason_compose_blocked,
}


def _resolve_repo_path(ref: str) -> Path:
    path = Path(str(ref or "").strip())
    if not str(path):
        raise RuntimeError("empty ready gate contract ref")
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def _coerce_names(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, (list, tuple)):
        return ()
    names: list[str] = []
    for item in value:
        name = str(item or "").strip()
        if name:
            names.append(name)
    return tuple(names)


@lru_cache(maxsize=8)
def load_hot_follow_gate_spec(contract_ref: str = HOT_FOLLOW_READY_GATE_CONTRACT_REF) -> ReadyGateSpec:
    path = _resolve_repo_path(contract_ref)
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise RuntimeError(f"invalid ready gate contract payload: {path}")
    runtime_rules = payload.get("runtime_rules") or {}
    if not isinstance(runtime_rules, dict):
        raise RuntimeError(f"missing runtime_rules in ready gate contract: {path}")

    signal_defs = runtime_rules.get("signals") or {}
    if not isinstance(signal_defs, dict) or not signal_defs:
        raise RuntimeError(f"missing signals in ready gate contract: {path}")

    signals: list[Signal] = []
    for signal_name, raw_cfg in signal_defs.items():
        cfg = raw_cfg if isinstance(raw_cfg, dict) else {"source": raw_cfg}
        source = str(cfg.get("source") or signal_name).strip()
        extract = _SIGNAL_EXTRACTORS.get(source)
        if extract is None:
            raise RuntimeError(f"unknown ready gate signal source={source!r} in {path}")
        reason_key = str(cfg.get("reason_key") or "").strip() or None
        reason_source_name = str(cfg.get("reason_source") or "").strip() or None
        reason_extract = _REASON_EXTRACTORS.get(reason_source_name) if reason_source_name else None
        signals.append(
            Signal(
                name=str(signal_name).strip(),
                extract=extract,
                reason_key=reason_key,
                reason_extract=reason_extract,
            )
        )

    overrides: list[OverrideRule] = []
    for raw_cfg in runtime_rules.get("overrides") or []:
        if not isinstance(raw_cfg, dict):
            continue
        overrides.append(
            OverrideRule(
                evidence_signal=str(raw_cfg.get("evidence_signal") or "").strip(),
                target_signal=str(raw_cfg.get("target_signal") or "").strip(),
                force_value=bool(raw_cfg.get("force_value", False)),
            )
        )

    gates: list[GateRule] = []
    for raw_cfg in runtime_rules.get("gates") or []:
        if not isinstance(raw_cfg, dict):
            continue
        gates.append(
            GateRule(
                name=str(raw_cfg.get("name") or "").strip(),
                requires=_coerce_names(raw_cfg.get("requires")),
                unless=_coerce_names(raw_cfg.get("unless_any") or raw_cfg.get("unless")),
            )
        )

    blocking: list[BlockingRule] = []
    for raw_cfg in runtime_rules.get("blocking_rules") or []:
        if not isinstance(raw_cfg, dict):
            continue
        blocking.append(
            BlockingRule(
                reason=str(raw_cfg.get("reason") or "").strip(),
                when_missing=str(raw_cfg.get("when_missing") or "").strip() or "__always__",
                unless_signal=str(raw_cfg.get("unless_signal") or "").strip() or None,
                extra_requires=_coerce_names(raw_cfg.get("extra_requires")),
                reason_from=str(raw_cfg.get("reason_from") or "").strip() or None,
                parent_gate=str(raw_cfg.get("parent_gate") or "compose_ready").strip() or "compose_ready",
            )
        )

    return ReadyGateSpec(
        line_id=str(payload.get("line_id") or "hot_follow_line").strip() or "hot_follow_line",
        signals=tuple(signals),
        overrides=tuple(overrides),
        gates=tuple(gates),
        blocking=tuple(blocking),
    )


HOT_FOLLOW_GATE_SPEC = load_hot_follow_gate_spec()
