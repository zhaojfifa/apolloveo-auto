"""Tests for derive_matrix_script_main_video_result (PR-2A · 2026-05-28).

Authority: approved Matrix Script Operator Experience Design Plan §6.2
+ user product decision #1 (structured operator_note prefix; no
closed-enum widening).

These tests are import-light; they call the helper directly and never
instantiate the FastAPI app.
"""
from __future__ import annotations

from typing import Any, Mapping

import pytest

from gateway.app.services.matrix_script.main_video_result_view import (
    ACTION_CONFIRM_MAIN,
    ACTION_GENERATE,
    ACTION_GO_TO_DELIVERY,
    ACTION_REGENERATE,
    ALREADY_CONFIRMED_REASON_ZH,
    GENERATION_BACKEND_PENDING_REASON_ZH,
    MAIN_VERSION_CONFIRMED_NOTE_PREFIX,
    NOT_GENERATED_EMPTY_STATE_ZH,
    NO_CONFIRMABLE_VARIATION_REASON_ZH,
    STATE_AWAITING_REVIEW,
    STATE_DELIVERABLE,
    STATE_LABELS_ZH,
    STATE_NOT_GENERATED,
    derive_matrix_script_main_video_result,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _ms_task(task_id: str = "ms-pr2a-001") -> dict[str, Any]:
    return {
        "task_id": task_id,
        "id": task_id,
        "kind": "matrix_script",
        "config": {"entry": {"topic": "PR-2A 主视频结果测试"}},
    }


def _ms_panel() -> dict[str, Any]:
    return {"panel_kind": "matrix_script"}


def _publish_readiness(
    *, publishable: bool = False, head_reason: str | None = "final_missing"
) -> dict[str, Any]:
    return {
        "publishable": publishable,
        "head_reason": head_reason,
        "consumed_inputs": {"blocking_count": 0 if publishable else 1},
        "blocking_advisories": [],
    }


def _preview_compare(*, variations: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {"is_matrix_script": True, "variations": variations or []}


def _variation(
    *,
    variation_id: str,
    preview_status_code: str = "unresolved",
) -> dict[str, Any]:
    return {
        "variation_id": variation_id,
        "preview_status_code": preview_status_code,
        "preview_status_label_zh": "占位",
        "preview_status_explanation_zh": "",
        "recommended_bucket": "undetermined_pending_review",
    }


def _recommended_action(variation_id: str | None = None) -> dict[str, Any]:
    if variation_id is None:
        return {"is_matrix_script": True, "recommended_variant": {}}
    return {
        "is_matrix_script": True,
        "recommended_variant": {"variation_id": variation_id},
    }


def _closure_with_main_confirmed(
    variation_id: str | None = None,
) -> dict[str, Any]:
    note = MAIN_VERSION_CONFIRMED_NOTE_PREFIX
    if variation_id:
        note = f"{note} variation_id={variation_id}"
    return {
        "feedback_closure_records": [
            {
                "event_kind": "operator_note",
                "operator_publish_notes": note,
            }
        ]
    }


# ---------------------------------------------------------------------------
# Non-matrix-script tasks return empty dict
# ---------------------------------------------------------------------------


def test_non_matrix_script_panel_returns_empty_dict() -> None:
    assert derive_matrix_script_main_video_result(
        task=_ms_task(),
        workbench_panel={"panel_kind": "hot_follow"},
        publish_readiness=_publish_readiness(),
    ) == {}


def test_missing_panel_returns_empty_dict() -> None:
    assert derive_matrix_script_main_video_result(
        task=_ms_task(),
        workbench_panel=None,
        publish_readiness=_publish_readiness(),
    ) == {}


# ---------------------------------------------------------------------------
# State pill derivation — closed 4-value set, operator language only
# ---------------------------------------------------------------------------


def test_state_kind_not_generated_when_no_media_anywhere() -> None:
    result = derive_matrix_script_main_video_result(
        task=_ms_task(),
        workbench_panel=_ms_panel(),
        publish_readiness=_publish_readiness(publishable=False),
        preview_compare=_preview_compare(
            variations=[_variation(variation_id="v1", preview_status_code="unresolved")]
        ),
        recommended_action=_recommended_action(),
    )
    assert result["state_kind"] == STATE_NOT_GENERATED
    assert result["state_label_zh"] == "未生成"


def test_state_kind_awaiting_review_when_fresh_media_but_not_publishable() -> None:
    result = derive_matrix_script_main_video_result(
        task=_ms_task(),
        workbench_panel=_ms_panel(),
        publish_readiness=_publish_readiness(publishable=False),
        preview_compare=_preview_compare(
            variations=[_variation(variation_id="v1", preview_status_code="current_fresh")]
        ),
        recommended_action=_recommended_action("v1"),
    )
    assert result["state_kind"] == STATE_AWAITING_REVIEW
    assert result["state_label_zh"] == "待审核"


def test_state_kind_deliverable_when_publish_readiness_publishable() -> None:
    result = derive_matrix_script_main_video_result(
        task=_ms_task(),
        workbench_panel=_ms_panel(),
        publish_readiness=_publish_readiness(publishable=True, head_reason="publishable_ok"),
        preview_compare=_preview_compare(
            variations=[_variation(variation_id="v1", preview_status_code="current_fresh")]
        ),
        recommended_action=_recommended_action("v1"),
    )
    assert result["state_kind"] == STATE_DELIVERABLE
    assert result["state_label_zh"] == "可交付"


def test_state_pill_label_set_is_exhaustively_chinese() -> None:
    assert STATE_LABELS_ZH == {
        STATE_NOT_GENERATED: "未生成",
        "generating": "生成中",
        STATE_AWAITING_REVIEW: "待审核",
        STATE_DELIVERABLE: "可交付",
    }


# ---------------------------------------------------------------------------
# Preview hero — honest empty state, never fake media
# ---------------------------------------------------------------------------


def test_preview_renders_empty_state_message_when_no_fresh_media() -> None:
    result = derive_matrix_script_main_video_result(
        task=_ms_task(),
        workbench_panel=_ms_panel(),
        publish_readiness=_publish_readiness(),
        preview_compare=_preview_compare(
            variations=[_variation(variation_id="v1", preview_status_code="unresolved")]
        ),
    )
    assert result["preview"]["available"] is False
    assert result["preview"]["variation_id"] is None
    assert result["preview"]["empty_state_message_zh"] == NOT_GENERATED_EMPTY_STATE_ZH
    # Mission §B.1 verbatim wording
    assert "当前尚未生成主视频" in result["preview"]["empty_state_message_zh"]
    assert "成片生成能力接入后将在这里展示视频结果" in result["preview"]["empty_state_message_zh"]


def test_preview_selects_recommended_variation_when_fresh() -> None:
    result = derive_matrix_script_main_video_result(
        task=_ms_task(),
        workbench_panel=_ms_panel(),
        publish_readiness=_publish_readiness(),
        preview_compare=_preview_compare(
            variations=[
                _variation(variation_id="v1", preview_status_code="unresolved"),
                _variation(variation_id="v2", preview_status_code="current_fresh"),
            ]
        ),
        recommended_action=_recommended_action("v2"),
    )
    assert result["preview"]["available"] is True
    assert result["preview"]["variation_id"] == "v2"
    assert result["preview"]["empty_state_message_zh"] is None


def test_preview_prefers_confirmed_main_over_recommended() -> None:
    """When operator confirmed v1 as main but v2 is recommended, preview
    must show v1 (operator intent overrides system recommendation)."""

    result = derive_matrix_script_main_video_result(
        task=_ms_task(),
        workbench_panel=_ms_panel(),
        publish_readiness=_publish_readiness(),
        preview_compare=_preview_compare(
            variations=[
                _variation(variation_id="v1", preview_status_code="current_fresh"),
                _variation(variation_id="v2", preview_status_code="current_fresh"),
            ]
        ),
        recommended_action=_recommended_action("v2"),
        closure=_closure_with_main_confirmed("v1"),
    )
    assert result["preview"]["variation_id"] == "v1"
    assert result["confirmed_main_variation_id"] == "v1"


# ---------------------------------------------------------------------------
# Action bar — closed 4-action set, enablement rules
# ---------------------------------------------------------------------------


def test_generate_and_regenerate_actions_always_disabled_today() -> None:
    """Generation backend not landed yet. Buttons rendered but disabled
    with operator-language tooltip."""

    result = derive_matrix_script_main_video_result(
        task=_ms_task(),
        workbench_panel=_ms_panel(),
        publish_readiness=_publish_readiness(publishable=True, head_reason="publishable_ok"),
        preview_compare=_preview_compare(
            variations=[_variation(variation_id="v1", preview_status_code="current_fresh")]
        ),
    )
    actions = {a["action_id"]: a for a in result["primary_actions"]}
    assert actions[ACTION_GENERATE]["enabled"] is False
    assert actions[ACTION_REGENERATE]["enabled"] is False
    assert actions[ACTION_GENERATE]["disabled_reason_zh"] == GENERATION_BACKEND_PENDING_REASON_ZH
    assert "成片生成能力接入后启用" in actions[ACTION_GENERATE]["disabled_reason_zh"]


def test_confirm_main_enabled_when_fresh_media_and_not_yet_confirmed() -> None:
    result = derive_matrix_script_main_video_result(
        task=_ms_task(),
        workbench_panel=_ms_panel(),
        publish_readiness=_publish_readiness(),
        preview_compare=_preview_compare(
            variations=[_variation(variation_id="v1", preview_status_code="current_fresh")]
        ),
        recommended_action=_recommended_action("v1"),
    )
    actions = {a["action_id"]: a for a in result["primary_actions"]}
    assert actions[ACTION_CONFIRM_MAIN]["enabled"] is True
    assert actions[ACTION_CONFIRM_MAIN]["disabled_reason_zh"] is None


def test_confirm_main_disabled_when_no_fresh_media() -> None:
    result = derive_matrix_script_main_video_result(
        task=_ms_task(),
        workbench_panel=_ms_panel(),
        publish_readiness=_publish_readiness(),
        preview_compare=_preview_compare(
            variations=[_variation(variation_id="v1", preview_status_code="unresolved")]
        ),
    )
    actions = {a["action_id"]: a for a in result["primary_actions"]}
    assert actions[ACTION_CONFIRM_MAIN]["enabled"] is False
    assert actions[ACTION_CONFIRM_MAIN]["disabled_reason_zh"] == NO_CONFIRMABLE_VARIATION_REASON_ZH


def test_confirm_main_disabled_when_already_confirmed() -> None:
    result = derive_matrix_script_main_video_result(
        task=_ms_task(),
        workbench_panel=_ms_panel(),
        publish_readiness=_publish_readiness(),
        preview_compare=_preview_compare(
            variations=[_variation(variation_id="v1", preview_status_code="current_fresh")]
        ),
        recommended_action=_recommended_action("v1"),
        closure=_closure_with_main_confirmed("v1"),
    )
    actions = {a["action_id"]: a for a in result["primary_actions"]}
    assert actions[ACTION_CONFIRM_MAIN]["enabled"] is False
    assert actions[ACTION_CONFIRM_MAIN]["disabled_reason_zh"] == ALREADY_CONFIRMED_REASON_ZH


def test_go_to_delivery_always_enabled_and_links_to_publish_hub() -> None:
    result = derive_matrix_script_main_video_result(
        task=_ms_task(task_id="abc123"),
        workbench_panel=_ms_panel(),
        publish_readiness=_publish_readiness(),
        preview_compare=_preview_compare(),
    )
    actions = {a["action_id"]: a for a in result["primary_actions"]}
    assert actions[ACTION_GO_TO_DELIVERY]["enabled"] is True
    assert actions[ACTION_GO_TO_DELIVERY]["href"] == "/tasks/abc123/publish"


# ---------------------------------------------------------------------------
# Confirm-main intent → structured operator_note, no enum widening
# ---------------------------------------------------------------------------


def test_confirm_note_prefix_is_pinned_structured_string() -> None:
    """The structured prefix is the contract for confirm-main intent
    detection. It MUST NOT change without updating the detection logic
    in _detect_confirmed_main_variation."""

    assert MAIN_VERSION_CONFIRMED_NOTE_PREFIX == "[main-version-confirmed]"


def test_detect_confirmed_main_from_operator_note_with_explicit_variation_id() -> None:
    result = derive_matrix_script_main_video_result(
        task=_ms_task(),
        workbench_panel=_ms_panel(),
        publish_readiness=_publish_readiness(),
        preview_compare=_preview_compare(
            variations=[
                _variation(variation_id="v1", preview_status_code="current_fresh"),
                _variation(variation_id="v2", preview_status_code="current_fresh"),
            ]
        ),
        recommended_action=_recommended_action("v2"),
        closure=_closure_with_main_confirmed("v1"),
    )
    assert result["confirmed_main_variation_id"] == "v1"


def test_detect_confirmed_main_without_explicit_id_falls_back_to_recommended() -> None:
    result = derive_matrix_script_main_video_result(
        task=_ms_task(),
        workbench_panel=_ms_panel(),
        publish_readiness=_publish_readiness(),
        preview_compare=_preview_compare(
            variations=[_variation(variation_id="v2", preview_status_code="current_fresh")]
        ),
        recommended_action=_recommended_action("v2"),
        closure=_closure_with_main_confirmed(None),  # bare prefix, no variation_id
    )
    assert result["confirmed_main_variation_id"] == "v2"


def test_no_closure_means_no_confirmation() -> None:
    result = derive_matrix_script_main_video_result(
        task=_ms_task(),
        workbench_panel=_ms_panel(),
        publish_readiness=_publish_readiness(),
        preview_compare=_preview_compare(),
        recommended_action=_recommended_action(),
        closure=None,
    )
    assert result["confirmed_main_variation_id"] is None


# ---------------------------------------------------------------------------
# Operator-language guarantees — no engineering identifier leakage
# ---------------------------------------------------------------------------


def test_blocker_and_next_action_never_expose_publish_readiness_or_head_reason_enum() -> None:
    """The operator-language blocker / next-action one-liners NEVER carry
    the raw English enum value `head_reason=final_missing` etc. Only the
    operator-language label appears."""

    result = derive_matrix_script_main_video_result(
        task=_ms_task(),
        workbench_panel=_ms_panel(),
        publish_readiness=_publish_readiness(publishable=False, head_reason="final_missing"),
        preview_compare=_preview_compare(),
    )
    blocker = result["blocker_one_liner_zh"]
    next_action = result["next_action_one_liner_zh"]
    for forbidden in ("publish_readiness", "head_reason", "final_missing", "compose_not_ready"):
        assert forbidden not in blocker
        assert forbidden not in next_action


def test_return_value_contains_no_vendor_or_model_or_provider_or_engine_keys() -> None:
    result = derive_matrix_script_main_video_result(
        task=_ms_task(),
        workbench_panel=_ms_panel(),
        publish_readiness=_publish_readiness(publishable=True, head_reason="publishable_ok"),
        preview_compare=_preview_compare(),
    )
    serialized = repr(result).lower()
    for forbidden in ("vendor", "model_id", "provider_id", "engine_id"):
        assert forbidden not in serialized


def test_no_fake_url_in_preview_payload() -> None:
    """RC-R8 audit: even when a variation has current_fresh media, the
    helper does NOT echo back a fake URL — only the opaque variation_id."""

    result = derive_matrix_script_main_video_result(
        task=_ms_task(),
        workbench_panel=_ms_panel(),
        publish_readiness=_publish_readiness(),
        preview_compare=_preview_compare(
            variations=[_variation(variation_id="v1", preview_status_code="current_fresh")]
        ),
        recommended_action=_recommended_action("v1"),
    )
    serialized = repr(result)
    assert "http://" not in serialized
    assert "https://" not in serialized
    assert "://" not in serialized.replace(
        "/api/matrix-script/closures/", ""
    )  # only the closure endpoint template uses a leading slash


# ---------------------------------------------------------------------------
# Closure endpoint template carried in payload (for template JS)
# ---------------------------------------------------------------------------


def test_closure_event_endpoint_template_is_pinned() -> None:
    result = derive_matrix_script_main_video_result(
        task=_ms_task("xyz789"),
        workbench_panel=_ms_panel(),
        publish_readiness=_publish_readiness(),
        preview_compare=_preview_compare(),
    )
    assert result["closure_event_endpoint_template"] == "/api/matrix-script/closures/{task_id}/events"
    assert result["confirm_note_prefix"] == MAIN_VERSION_CONFIRMED_NOTE_PREFIX
