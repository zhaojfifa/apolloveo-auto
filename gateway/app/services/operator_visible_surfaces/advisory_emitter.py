"""L4 advisory producer (Operator Capability Recovery, PR-1).

Single producer for L4 advisories per
`docs/contracts/l4_advisory_producer_output_contract_v1.md`. The closed
advisory taxonomy is owned by
`docs/contracts/hot_follow_projection_rules_v1.md` lines 272-335 — this
module reproduces the entries verbatim and never mints new ids, evidence
fields, or hints.

Pure projection. Reads only `l3_current_attempt` + `ready_gate`. No I/O,
no mutation, no vendor/model/provider identifier. Returns an ordered list
where the highest-priority applicable advisory comes first per the
`advisory_resolution_contract.selection` block.
"""
from __future__ import annotations

from typing import Any, Mapping


# Closed advisory taxonomy mirrored verbatim from
# `docs/contracts/hot_follow_projection_rules_v1.md` lines 272-335.
HF_ADVISORY_TRANSLATION_WAITING_RETRYABLE = "hf_advisory_translation_waiting_retryable"
HF_ADVISORY_FINAL_READY = "hf_advisory_final_ready"
HF_ADVISORY_RETRIABLE_DUB_FAILURE = "hf_advisory_retriable_dub_failure"
HF_ADVISORY_NO_DUB_ROUTE_TERMINAL = "hf_advisory_no_dub_route_terminal"

CLOSED_ADVISORY_IDS = frozenset(
    {
        HF_ADVISORY_TRANSLATION_WAITING_RETRYABLE,
        HF_ADVISORY_FINAL_READY,
        HF_ADVISORY_RETRIABLE_DUB_FAILURE,
        HF_ADVISORY_NO_DUB_ROUTE_TERMINAL,
    }
)


_ADVISORY_DEFINITIONS: dict[str, dict[str, Any]] = {
    HF_ADVISORY_TRANSLATION_WAITING_RETRYABLE: {
        "id": HF_ADVISORY_TRANSLATION_WAITING_RETRYABLE,
        "kind": "operator_guidance",
        "level": "info",
        "recommended_next_action": "wait_or_retry_translation",
        "operator_hint": "subtitle translation still pending",
        "explanation": (
            "当前目标字幕翻译尚未就绪，线路处于等待/可重试状态；"
            "请等待翻译返回或重试字幕步骤，再继续配音和合成。"
        ),
        "evidence_fields": [
            "subtitle_ready",
            "subtitle_ready_reason",
            "audio_ready",
            "audio_ready_reason",
        ],
    },
    HF_ADVISORY_FINAL_READY: {
        "id": HF_ADVISORY_FINAL_READY,
        "kind": "operator_guidance",
        "level": "info",
        "recommended_next_action": "continue_qa",
        "operator_hint": "no further action currently required",
        "explanation": "当前成片已可用，可继续做字幕、配音或成片 QA 复核。",
        "evidence_fields": [
            "final_exists",
            "compose_ready",
            "publish_ready",
            "last_successful_output_available",
        ],
    },
    HF_ADVISORY_RETRIABLE_DUB_FAILURE: {
        "id": HF_ADVISORY_RETRIABLE_DUB_FAILURE,
        "kind": "operator_guidance",
        "level": "warning",
        "recommended_next_action": "retry_or_inspect_dub",
        "operator_hint": "retry or inspect TTS/dub path",
        "explanation": (
            "TTS lane is expected but current audio is not ready after a "
            "provider/audio generation failure. Retry or inspect dub before compose."
        ),
        "evidence_fields": [
            "selected_compose_route",
            "tts_lane_expected",
            "retriable_dub_failure",
            "current_attempt_failure_class",
            "audio_ready",
            "audio_ready_reason",
            "compose_status",
        ],
    },
    HF_ADVISORY_NO_DUB_ROUTE_TERMINAL: {
        "id": HF_ADVISORY_NO_DUB_ROUTE_TERMINAL,
        "kind": "operator_guidance",
        "level": "info",
        "recommended_next_action": "compose_no_tts",
        "operator_hint": "no TTS compose route",
        "explanation": (
            "当前素材已进入无 TTS 合成路径：{no_dub_reason}。"
            "可继续合成保留原音或背景音版本。"
        ),
        "evidence_fields": [
            "selected_compose_route",
            "no_dub_route_terminal",
            "no_tts_compose_allowed",
            "no_dub_compose_allowed",
            "no_dub_reason",
        ],
    },
}

_NO_TTS_TERMINAL_ROUTES = frozenset(
    {"preserve_source_route", "bgm_only_route", "no_tts_compose_route"}
)


def _select_advisory_ids(
    l3: Mapping[str, Any],
    gate: Mapping[str, Any],
) -> list[str]:
    """Apply the `advisory_resolution_contract.selection` rules verbatim.

    Source: `docs/contracts/hot_follow_projection_rules_v1.md` lines 272-281.
    Selection rules are mutually exclusive in practice; we enforce a
    deterministic priority order so the producer's output list is stable.
    """
    selected: list[str] = []

    final_ready = (
        bool(l3.get("final_fresh"))
        and bool(gate.get("publish_ready"))
        and bool(gate.get("compose_ready"))
    )
    translation_waiting = bool(l3.get("subtitle_translation_waiting_retryable"))
    retriable_dub = bool(l3.get("retriable_dub_failure"))
    selected_route = str(l3.get("selected_compose_route") or "").strip()
    no_dub_terminal = bool(l3.get("no_dub_route_terminal")) and (
        selected_route in _NO_TTS_TERMINAL_ROUTES
    )

    # Priority: final_ready > translation_waiting > retriable_dub > no_dub_terminal.
    # Final-ready is informational and shown alone; if present, suppress the
    # blocking-style advisories to avoid confusing the operator.
    if final_ready:
        selected.append(HF_ADVISORY_FINAL_READY)
        return selected
    if translation_waiting:
        selected.append(HF_ADVISORY_TRANSLATION_WAITING_RETRYABLE)
    if retriable_dub:
        selected.append(HF_ADVISORY_RETRIABLE_DUB_FAILURE)
    if no_dub_terminal:
        selected.append(HF_ADVISORY_NO_DUB_ROUTE_TERMINAL)
    return selected


def emit_advisories(
    l3_current_attempt: Mapping[str, Any] | None,
    ready_gate: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    """Producer entry point per `l4_advisory_producer_output_contract_v1.md`.

    Returns an ordered list of advisory objects. Each object's shape is
    exactly the closed `Advisory` shape; every emitted `id` is a member of
    the closed taxonomy. The producer never mints new ids, never extends
    the evidence_fields list, and never mutates inputs.
    """
    l3 = dict(l3_current_attempt or {})
    gate = dict(ready_gate or {})
    advisory_ids = _select_advisory_ids(l3, gate)
    return [dict(_ADVISORY_DEFINITIONS[advisory_id]) for advisory_id in advisory_ids]


__all__ = [
    "CLOSED_ADVISORY_IDS",
    "HF_ADVISORY_FINAL_READY",
    "HF_ADVISORY_NO_DUB_ROUTE_TERMINAL",
    "HF_ADVISORY_RETRIABLE_DUB_FAILURE",
    "HF_ADVISORY_TRANSLATION_WAITING_RETRYABLE",
    "emit_advisories",
]
