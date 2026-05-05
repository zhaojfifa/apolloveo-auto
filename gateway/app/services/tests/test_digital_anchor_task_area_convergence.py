"""Tests for OWC-DA PR-1 — Digital Anchor Task Area Workflow Convergence.

Covers DA-W1 (8-field card) + DA-W2 (eight-stage projection) per
``docs/reviews/owc_da_gate_spec_v1.md`` §3 and the binding line-specific
authority at ``docs/product/digital_anchor_product_flow_v1.md``
§§5.1 / 5.2.

Test floor per gate spec §5.2: ≥25 cases. This module ships ≥30.

Hard discipline mirrored in the assertions below:

- Reminder #1 — 当前版本状态 consumes ``board_bucket`` truth only.
- Reminder #2 — 交付包状态 stays tracked-gap with the closed
  ``DELIVERY_PACK_STATE_GATED_BY_DA_W8`` sentinel until DA-W8 lands.
- Reminder #3 — eight-stage projection degrades gracefully when
  ``closure`` is ``None`` and invents no late-stage truth.
"""
from __future__ import annotations

import pytest

from gateway.app.services.digital_anchor.closure_binding import reset_for_tests
from gateway.app.services.digital_anchor.task_area_convergence import (
    CURRENT_VERSION_STATE_LABELS,
    DELIVERY_PACK_STATE_GATED_BY_DA_W8,
    DELIVERY_PACK_STATE_TOOLTIP,
    DIGITAL_ANCHOR_LINE_ID,
    EIGHT_STAGES,
    EIGHT_STAGE_LABELS,
    ROLE_PACK_REF_ID,
    SPEAKER_PLAN_REF_ID,
    STAGE_ARCHIVED,
    STAGE_COMPOSED,
    STAGE_DELIVERABLE,
    STAGE_INPUT_SUBMITTED,
    STAGE_MULTI_LANGUAGE_GENERATING,
    STAGE_ROLE_VOICE_BOUND,
    STAGE_SCENE_PLAN_GENERATED,
    STAGE_STRUCTURE_GENERATED,
    derive_digital_anchor_card_summary,
    derive_digital_anchor_card_summary_for_task,
    derive_digital_anchor_eight_stage_state,
)


@pytest.fixture(autouse=True)
def _isolate_closure_store() -> None:
    """Each test starts with a clean Digital Anchor closure store."""
    reset_for_tests()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _digital_anchor_row(
    *,
    task_id: str = "task_owc_da_001",
    title: str = "Spring digital anchor demo",
    bucket: str = "ready",
    head_reason: str | None = None,
    role_profile_ref: str | None = "asset://role/da_demo_v1",
    scene_binding_hint: str | None = "asset://scene/keynote_v1",
    target_languages: list[str] | None = None,
    roles_authored: bool = False,
    segments_authored: bool = False,
    compose_status: str | None = None,
    final_exists: bool = False,
    archived: bool = False,
    updated_at: str | None = "2026-05-05T05:00:00Z",
    next_surfaces: dict | None = None,
) -> dict:
    target_languages = target_languages if target_languages is not None else ["en", "vi"]
    refs: list[dict] = []
    role_delta: dict = {}
    if roles_authored:
        role_delta = {
            "roles": [
                {
                    "role_id": "role_alpha",
                    "display_name": "Alpha",
                    "framing_kind": "head",
                    "appearance_ref": "asset://appearance/alpha_v1",
                }
            ]
        }
    refs.append({"ref_id": ROLE_PACK_REF_ID, "delta": role_delta})

    speaker_delta: dict = {}
    if segments_authored:
        speaker_delta = {
            "segments": [
                {
                    "segment_id": "seg_1",
                    "binds_role_id": "role_alpha",
                    "script_ref": "content://script/seg_1",
                    "dub_kind": "tts_neutral",
                    "lip_sync_kind": "loose",
                    "language_pick": "en",
                }
            ]
        }
    refs.append({"ref_id": SPEAKER_PLAN_REF_ID, "delta": speaker_delta})

    config_entry: dict = {
        "topic": title,
        "language_scope": {"source_language": "zh", "target_language": list(target_languages)},
        "role_framing_hint": "head",
        "output_intent": "broadcast",
        "speaker_segment_count_hint": 4,
    }
    if role_profile_ref is not None:
        config_entry["role_profile_ref"] = role_profile_ref
    if scene_binding_hint is not None:
        config_entry["scene_binding_hint"] = scene_binding_hint

    config: dict = {
        "line_id": DIGITAL_ANCHOR_LINE_ID,
        "entry_contract": "digital_anchor_task_entry_v1",
        "entry": config_entry,
        "next_surfaces": next_surfaces
        if next_surfaces is not None
        else {
            "workbench": f"/tasks/{task_id}",
            "delivery": f"/tasks/{task_id}/publish",
        },
    }

    return {
        "task_id": task_id,
        "kind": DIGITAL_ANCHOR_LINE_ID,
        "title": title,
        "board_bucket": bucket,
        "head_reason": head_reason,
        "line_specific_refs": refs,
        "config": config,
        "ready_gate": {"compose_ready": False, "publish_ready": False},
        "compose_status": compose_status,
        "final": {"exists": final_exists},
        "archived": archived,
        "updated_at": updated_at,
        "created_at": "2026-05-05T04:55:00Z",
    }


def _closure_with_archive_record() -> dict:
    """Minimal Digital Anchor closure carrying one archive_action record."""
    return {
        "surface": "digital_anchor_publish_feedback_closure_v1",
        "closure_id": "closure_test_archive",
        "line_id": "digital_anchor",
        "role_feedback": [],
        "segment_feedback": [],
        "feedback_closure_records": [
            {
                "record_id": "rec_archive_1",
                "recorded_at": "2026-05-05T06:00:00Z",
                "recorded_by": "operator",
                "record_kind": "archive_action",
                "role_ids": [],
                "segment_ids": [],
                "note": None,
            }
        ],
    }


# ---------------------------------------------------------------------------
# Eight-stage state — DA-W2
# ---------------------------------------------------------------------------


def test_eight_stages_constant_matches_product_flow_authority() -> None:
    """EIGHT_STAGES order + labels match digital_anchor_product_flow §5.1 verbatim."""
    assert EIGHT_STAGES == (
        STAGE_INPUT_SUBMITTED,
        STAGE_STRUCTURE_GENERATED,
        STAGE_SCENE_PLAN_GENERATED,
        STAGE_ROLE_VOICE_BOUND,
        STAGE_MULTI_LANGUAGE_GENERATING,
        STAGE_COMPOSED,
        STAGE_DELIVERABLE,
        STAGE_ARCHIVED,
    )
    assert EIGHT_STAGE_LABELS[STAGE_INPUT_SUBMITTED] == "输入已提交"
    assert EIGHT_STAGE_LABELS[STAGE_STRUCTURE_GENERATED] == "内容结构已生成"
    assert EIGHT_STAGE_LABELS[STAGE_SCENE_PLAN_GENERATED] == "场景计划已生成"
    assert EIGHT_STAGE_LABELS[STAGE_ROLE_VOICE_BOUND] == "角色 / 声音已绑定"
    assert EIGHT_STAGE_LABELS[STAGE_MULTI_LANGUAGE_GENERATING] == "多语言版本生成中"
    assert EIGHT_STAGE_LABELS[STAGE_COMPOSED] == "合成完成"
    assert EIGHT_STAGE_LABELS[STAGE_DELIVERABLE] == "可交付"
    assert EIGHT_STAGE_LABELS[STAGE_ARCHIVED] == "已归档"


def test_stage_input_submitted_is_default_for_fresh_row() -> None:
    """Reminder #3 — closure=None and no late-stage signals ⇒ input_submitted."""
    row = _digital_anchor_row()
    state = derive_digital_anchor_eight_stage_state(row)
    assert state["stage"] == STAGE_INPUT_SUBMITTED
    assert state["stage_label"] == "输入已提交"


def test_stage_deliverable_when_board_bucket_publishable() -> None:
    """Reminder #1 — 可交付 derives from the unified producer's board_bucket."""
    row = _digital_anchor_row(bucket="publishable")
    state = derive_digital_anchor_eight_stage_state(row)
    assert state["stage"] == STAGE_DELIVERABLE
    assert state["stage_label"] == "可交付"


def test_stage_composed_when_final_exists_but_not_publishable() -> None:
    row = _digital_anchor_row(final_exists=True, bucket="ready")
    state = derive_digital_anchor_eight_stage_state(row)
    assert state["stage"] == STAGE_COMPOSED


def test_stage_multi_language_generating_when_compose_status_running() -> None:
    row = _digital_anchor_row(compose_status="running")
    state = derive_digital_anchor_eight_stage_state(row)
    assert state["stage"] == STAGE_MULTI_LANGUAGE_GENERATING


def test_stage_multi_language_generating_for_in_progress_and_queued() -> None:
    for status in ("in_progress", "queued"):
        row = _digital_anchor_row(compose_status=status)
        state = derive_digital_anchor_eight_stage_state(row)
        assert state["stage"] == STAGE_MULTI_LANGUAGE_GENERATING, status


def test_stage_role_voice_bound_when_both_roles_and_segments_authored() -> None:
    row = _digital_anchor_row(roles_authored=True, segments_authored=True)
    state = derive_digital_anchor_eight_stage_state(row)
    assert state["stage"] == STAGE_ROLE_VOICE_BOUND


def test_stage_scene_plan_generated_when_roles_authored_and_scene_present() -> None:
    row = _digital_anchor_row(
        roles_authored=True,
        segments_authored=False,
        scene_binding_hint="asset://scene/keynote_v1",
    )
    state = derive_digital_anchor_eight_stage_state(row)
    assert state["stage"] == STAGE_SCENE_PLAN_GENERATED


def test_stage_structure_generated_when_only_roles_authored() -> None:
    row = _digital_anchor_row(
        roles_authored=True,
        segments_authored=False,
        scene_binding_hint=None,
    )
    state = derive_digital_anchor_eight_stage_state(row)
    assert state["stage"] == STAGE_STRUCTURE_GENERATED


def test_stage_archived_takes_precedence_over_other_signals() -> None:
    row = _digital_anchor_row(
        archived=True,
        bucket="publishable",
        final_exists=True,
        compose_status="running",
    )
    state = derive_digital_anchor_eight_stage_state(row)
    assert state["stage"] == STAGE_ARCHIVED


def test_stage_archived_via_closure_archive_action_record() -> None:
    """Reminder #3 — late-stage truth derives from observable closure
    events, not invented signals. archive_action is the closed record_kind
    that drives ``已归档`` from the closure side."""
    row = _digital_anchor_row(bucket="publishable")
    closure = _closure_with_archive_record()
    state = derive_digital_anchor_eight_stage_state(row, closure=closure)
    assert state["stage"] == STAGE_ARCHIVED


def test_stage_unaffected_by_closure_records_with_other_record_kinds() -> None:
    row = _digital_anchor_row()
    closure = {
        "feedback_closure_records": [
            {"record_kind": "operator_review"},
            {"record_kind": "publish_callback"},
            {"record_kind": "correction_note"},
        ],
    }
    state = derive_digital_anchor_eight_stage_state(row, closure=closure)
    assert state["stage"] == STAGE_INPUT_SUBMITTED


def test_stage_index_is_position_in_eight_stages_tuple() -> None:
    row = _digital_anchor_row(bucket="publishable")
    state = derive_digital_anchor_eight_stage_state(row)
    assert state["stage_index"] == EIGHT_STAGES.index(STAGE_DELIVERABLE)


def test_stage_returns_empty_for_non_digital_anchor() -> None:
    assert derive_digital_anchor_eight_stage_state({"task_id": "x", "kind": "hot_follow"}) == {}
    assert derive_digital_anchor_eight_stage_state({"task_id": "x", "kind": "matrix_script"}) == {}
    assert derive_digital_anchor_eight_stage_state({"task_id": "x"}) == {}


def test_stage_handles_closure_none_gracefully_without_invented_truth() -> None:
    """Reminder #3 verbatim: closure=None must never bump into a late stage."""
    row = _digital_anchor_row()
    state = derive_digital_anchor_eight_stage_state(row, closure=None)
    assert state["stage"] == STAGE_INPUT_SUBMITTED


# ---------------------------------------------------------------------------
# Eight-field card — DA-W1
# ---------------------------------------------------------------------------


def test_card_returns_empty_for_non_digital_anchor() -> None:
    assert derive_digital_anchor_card_summary({"task_id": "x", "kind": "hot_follow"}) == {}
    assert derive_digital_anchor_card_summary({"task_id": "x", "kind": "matrix_script"}) == {}
    assert derive_digital_anchor_card_summary({}) == {}


def test_card_carries_eight_field_labels_in_chinese() -> None:
    summary = derive_digital_anchor_card_summary(_digital_anchor_row())
    # Chinese labels per digital_anchor_product_flow §5.2 — Role Profile /
    # Scene Template / Target Language are deliberately English per the
    # source authority, all other fields are Chinese.
    assert summary["task_title_label"] == "任务标题"
    assert summary["role_profile_label"] == "Role Profile"
    assert summary["scene_template_label"] == "Scene Template"
    assert summary["target_language_label"] == "Target Language"
    assert summary["current_version_state_label"] == "当前版本状态"
    assert summary["current_blocker_label"] == "当前阻塞项"
    assert summary["delivery_pack_state_label"] == "交付包状态"
    assert summary["last_update_label"] == "最近更新"


def test_card_task_title_value_reflects_row_title() -> None:
    row = _digital_anchor_row(title="Brand introduction demo")
    summary = derive_digital_anchor_card_summary(row)
    assert summary["task_title_value"] == "Brand introduction demo"


def test_card_role_profile_value_reads_config_entry_role_profile_ref() -> None:
    row = _digital_anchor_row(role_profile_ref="asset://role/foo_v2")
    summary = derive_digital_anchor_card_summary(row)
    assert summary["role_profile_value"] == "asset://role/foo_v2"


def test_card_role_profile_value_none_when_missing() -> None:
    row = _digital_anchor_row(role_profile_ref=None)
    summary = derive_digital_anchor_card_summary(row)
    assert summary["role_profile_value"] is None


def test_card_scene_template_value_reads_config_entry_scene_binding_hint() -> None:
    row = _digital_anchor_row(scene_binding_hint="asset://scene/foo_v3")
    summary = derive_digital_anchor_card_summary(row)
    assert summary["scene_template_value"] == "asset://scene/foo_v3"


def test_card_target_language_value_is_list_from_language_scope() -> None:
    row = _digital_anchor_row(target_languages=["en", "vi", "ja"])
    summary = derive_digital_anchor_card_summary(row)
    assert summary["target_language_value"] == ["en", "vi", "ja"]


def test_card_target_language_value_empty_when_missing() -> None:
    row = _digital_anchor_row(target_languages=[])
    # _coerce empty list to empty list
    summary = derive_digital_anchor_card_summary(row)
    assert summary["target_language_value"] == []


def test_card_current_version_state_derives_from_board_bucket_only() -> None:
    """Reminder #1 verbatim — board_bucket is the only producer consulted."""
    for bucket, expected_label in CURRENT_VERSION_STATE_LABELS.items():
        row = _digital_anchor_row(bucket=bucket)
        summary = derive_digital_anchor_card_summary(row)
        assert summary["current_version_state_value"] == bucket
        assert summary["current_version_state_label_value"] == expected_label


def test_card_current_version_state_clamps_unknown_bucket_to_ready() -> None:
    row = _digital_anchor_row(bucket="some_invented_bucket_value")
    summary = derive_digital_anchor_card_summary(row)
    assert summary["current_version_state_value"] == "ready"
    assert summary["current_version_state_label_value"] == "进行中"


def test_card_current_blocker_translates_known_head_reason_codes() -> None:
    row = _digital_anchor_row(bucket="blocked", head_reason="compose_ready_pending")
    summary = derive_digital_anchor_card_summary(row)
    assert summary["current_blocker_value"] == "合成未就绪"


def test_card_current_blocker_falls_through_to_raw_string_for_unknown_codes() -> None:
    row = _digital_anchor_row(bucket="blocked", head_reason="future_unknown_code")
    summary = derive_digital_anchor_card_summary(row)
    assert summary["current_blocker_value"] == "future_unknown_code"


def test_card_current_blocker_value_none_when_no_head_reason() -> None:
    row = _digital_anchor_row(bucket="ready", head_reason=None)
    summary = derive_digital_anchor_card_summary(row)
    assert summary["current_blocker_value"] is None


def test_card_delivery_pack_state_is_tracked_gap_with_da_w8_sentinel() -> None:
    """Reminder #2 verbatim — coarse / tracked-gap until DA-W8 lands."""
    summary = derive_digital_anchor_card_summary(_digital_anchor_row())
    assert summary["delivery_pack_state_value"] is None
    assert summary["delivery_pack_state_gated_by"] == DELIVERY_PACK_STATE_GATED_BY_DA_W8
    assert summary["delivery_pack_state_tooltip"] == DELIVERY_PACK_STATE_TOOLTIP
    assert "DA-W8" in summary["delivery_pack_state_tooltip"]


def test_card_last_update_value_prefers_updated_at_over_created_at() -> None:
    row = _digital_anchor_row(updated_at="2026-05-05T07:00:00Z")
    row["created_at"] = "2026-05-05T01:00:00Z"
    summary = derive_digital_anchor_card_summary(row)
    assert summary["last_update_value"] == "2026-05-05T07:00:00Z"


def test_card_last_update_value_falls_back_to_created_at_when_updated_at_missing() -> None:
    row = _digital_anchor_row(updated_at=None)
    summary = derive_digital_anchor_card_summary(row)
    assert summary["last_update_value"] == "2026-05-05T04:55:00Z"


def test_card_workbench_action_href_uses_next_surfaces_when_present() -> None:
    row = _digital_anchor_row(
        next_surfaces={"workbench": "/custom/workbench/x", "delivery": "/custom/delivery/x"}
    )
    summary = derive_digital_anchor_card_summary(row)
    assert summary["workbench_action_href"] == "/custom/workbench/x"
    assert summary["delivery_action_href"] == "/custom/delivery/x"
    assert summary["workbench_action_label"] == "进入工作台"
    assert summary["delivery_action_label"] == "跳交付中心"


def test_card_action_hrefs_fall_back_to_task_id_path_when_next_surfaces_missing() -> None:
    row = _digital_anchor_row(task_id="task_xyz", next_surfaces={})
    summary = derive_digital_anchor_card_summary(row)
    assert summary["workbench_action_href"] == "/tasks/task_xyz"
    assert summary["delivery_action_href"] == "/tasks/task_xyz/publish"


def test_card_includes_eight_stage_badge_block() -> None:
    row = _digital_anchor_row(bucket="publishable")
    summary = derive_digital_anchor_card_summary(row)
    assert summary["eight_stage"]["stage"] == STAGE_DELIVERABLE
    assert summary["eight_stage"]["stage_label"] == "可交付"


# ---------------------------------------------------------------------------
# Cross-line / sanitization isolation
# ---------------------------------------------------------------------------


def test_card_does_not_emit_keys_containing_vendor_model_provider_engine_substrings() -> None:
    summary = derive_digital_anchor_card_summary(_digital_anchor_row())
    forbidden_substrings = ("vendor", "model_id", "provider", "engine")
    for key in summary.keys():
        lowered = key.lower()
        for fragment in forbidden_substrings:
            assert fragment not in lowered, f"forbidden substring {fragment} in key {key}"


def test_card_emits_no_provider_or_swiftcraft_identifier_in_value_repr() -> None:
    summary = derive_digital_anchor_card_summary(_digital_anchor_row())
    blob = repr(summary).lower()
    for forbidden in ("vendor_id", "model_id", "provider_id", "engine_id", "swiftcraft"):
        assert forbidden not in blob, f"forbidden token {forbidden} leaked into card summary"


def test_card_kind_recognition_is_case_insensitive_and_alias_aware() -> None:
    """The line-id check must pass for ``digital_anchor`` declared via any
    of ``kind`` / ``category_key`` / ``category`` / ``platform``."""
    base = _digital_anchor_row()
    base["kind"] = "DIGITAL_ANCHOR"
    assert derive_digital_anchor_card_summary(base)["is_digital_anchor"] is True

    via_category_key = dict(base)
    via_category_key["kind"] = "other"
    via_category_key["category_key"] = "digital_anchor"
    assert derive_digital_anchor_card_summary(via_category_key)["is_digital_anchor"] is True


# ---------------------------------------------------------------------------
# Wrapper read-only closure binding
# ---------------------------------------------------------------------------


def test_card_for_task_returns_empty_for_non_digital_anchor_row() -> None:
    assert derive_digital_anchor_card_summary_for_task({"task_id": "x", "kind": "hot_follow"}) == {}


def test_card_for_task_does_not_lazy_create_closure_on_in_process_store() -> None:
    """Task Area projection must NEVER lazy-create a closure (mirrors the
    OWC-MS PR-1 discipline). The wrapper reads via
    ``get_closure_view_for_task`` which returns ``None`` if no closure
    exists yet — invoking it for a fresh task must NOT register the task
    in the binding map."""
    from gateway.app.services.digital_anchor.closure_binding import _TASK_TO_CLOSURE

    row = _digital_anchor_row(task_id="task_no_lazy_create")
    summary = derive_digital_anchor_card_summary_for_task(row)
    assert summary["is_digital_anchor"] is True
    assert "task_no_lazy_create" not in _TASK_TO_CLOSURE


def test_card_for_task_picks_up_existing_closure_archive_record() -> None:
    """If a closure already exists for the task (e.g. from a prior
    publish-hub interaction) and carries an archive_action record, the
    Task Area badge bumps to 已归档 without the wrapper re-creating the
    closure."""
    from gateway.app.services.digital_anchor import closure_binding as cb

    row = _digital_anchor_row(task_id="task_archived_via_closure", bucket="publishable")
    cb._STORE._closures["closure_task_archived_via_closure"] = _closure_with_archive_record()  # type: ignore[attr-defined]
    cb._TASK_TO_CLOSURE["task_archived_via_closure"] = "closure_task_archived_via_closure"

    summary = derive_digital_anchor_card_summary_for_task(row)
    assert summary["eight_stage"]["stage"] == STAGE_ARCHIVED


# ---------------------------------------------------------------------------
# Anti-mutation invariants
# ---------------------------------------------------------------------------


def test_card_does_not_mutate_input_row() -> None:
    import copy

    row = _digital_anchor_row(bucket="publishable")
    snapshot = copy.deepcopy(row)
    derive_digital_anchor_card_summary(row)
    assert row == snapshot


def test_eight_stage_does_not_mutate_input_row_or_closure() -> None:
    import copy

    row = _digital_anchor_row(bucket="publishable")
    closure = _closure_with_archive_record()
    row_snapshot = copy.deepcopy(row)
    closure_snapshot = copy.deepcopy(closure)
    derive_digital_anchor_eight_stage_state(row, closure=closure)
    assert row == row_snapshot
    assert closure == closure_snapshot
