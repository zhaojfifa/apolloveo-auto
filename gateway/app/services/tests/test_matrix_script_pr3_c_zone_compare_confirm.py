"""Matrix Script Guided Operator Workflow — PR-3: C区 V1/V2 对比与确认区.

Gate Spec: docs/design/MATRIX_SCRIPT_GUIDED_OPERATOR_WORKFLOW_GATE_SPEC_20260607.md §3.C.
Promotes the regenerate → compare → confirm pivot into a named C区 surface that
shows 当前主版本 V1 and 新预览候选 V2 (always 候选), which uploaded materials V2 used,
which shots changed, the existing confirm/discard/continue actions, and the explicit
truth "V2 未确认前不会影响交付". Presentation/projection only over the existing regen
lifecycle (#207/#212/#215) — no new producer, no endpoint/semantics change.
Behavior preserved: V1 kept until confirm (A-13), unconfirmed V2 does not affect
delivery (A-7), confirm uses existing behavior (A-8), no leakage (A-11), #212
byte-consumption unchanged (A-12), official_publish_ready=false (A-14).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict

from gateway.app.services.matrix_script import operator_workbench_view as owv
from gateway.app.services.matrix_script import tomato_real_result_plan as plan_mod

K = owv.MATERIAL_INTENT_KEY
_SHOTS = list(plan_mod.TOMATO_SHOTS)
_SHOT_04 = _SHOTS[3].shot_id
V1_URL = "/api/matrix-script/ms-pr3/tomato-real-result/preview/final.mp4"
V2_URL = "/api/matrix-script/ms-pr3/preview-version/V2/final.mp4"


def _v1_staged() -> Dict[str, Any]:
    return {
        "matrix_script_staged_candidate": {
            "has_result": True, "operator_usable": True, "delivery_candidate": True,
            "official_publish_ready": False, "preview_url": V1_URL,
            "shot_match_count": 3, "real_visual_count": 3, "shot_count": 5,
        }
    }


def _uploaded(shot_id: str) -> Dict[str, Any]:
    return {
        "intent": "supplement", "updated_at": "x",
        "material_ref": f"msmaterial://matrix_script/ms-pr3/{shot_id}/u1",
        "material_name": "fresh_tomato.png", "material_kind": "image",
        "material_source": owv.MATERIAL_UPLOAD_SOURCE,
        "storage_scope": "local_workspace", "bytes_resolvable": True,
    }


def _candidate(consumed_shot_id: str) -> Dict[str, Any]:
    return {owv.PREVIEW_VERSIONS_KEY: {"V2": {
        "role": owv.ROLE_CANDIDATE, "preview_url": V2_URL,
        "source": "material_regeneration", "based_on_intents": ["supplement"],
        "based_on_assets": [{"shot_id": consumed_shot_id, "material_name": "fresh_tomato.png", "material_kind": "image"}],
        "material_bytes_consumed": True,
        "consumed_materials": [{
            "shot_id": consumed_shot_id, "material_name": "fresh_tomato.png",
            "material_kind": "image",
            "material_ref": f"msmaterial://matrix_script/ms-pr3/{consumed_shot_id}/u1",
            "material_source": owv.MATERIAL_UPLOAD_SOURCE,
        }],
    }}}


def _failed() -> Dict[str, Any]:
    return {owv.REGEN_STATUS_KEY: {"status": "preview_generation_failed"}}


def _view(config: Dict[str, Any]) -> Dict[str, Any]:
    return owv.build_matrix_script_operator_workbench_view(
        {"task_id": "ms-pr3", "kind": "matrix_script", "config": config}
    )


def _render(view: Dict[str, Any]) -> str:
    from jinja2 import ChainableUndefined, Environment

    tpl = Path("gateway/app/templates/task_workbench.html").read_text(encoding="utf-8")
    start = tpl.index("{% if ms_main_video_result.is_matrix_script %}")
    end = tpl.index("{# Phase 2C", start)
    branch = tpl[start:end]
    return Environment(undefined=ChainableUndefined, autoescape=True).from_string(branch).render(
        ms_main_video_result={"is_matrix_script": True, "state_kind": "deliverable",
                              "state_label_zh": "运营可用", "preview": {"available": False},
                              "primary_actions": []},
        ms_overlay=view, ms_overlay_mr=view["main_result"],
        ms_overlay_has=view["main_result"]["operator_usable"],
        ms_effective_preview_url=view["main_result"].get("preview_url"),
        ms_effective_preview_source="main_result",
        ms_preview_compare={"is_matrix_script": True},
        ms_script_structure={"is_matrix_script": True, "sections": []},
        task={"task_id": "ms-pr3"},
    )


def _pivot(html: str) -> str:
    start = html.index('data-role="ms-regen-versioning"')
    start = html.rindex("<div", 0, start)
    # end of the versioning block: the <script> right after it
    end = html.index("<script>", start)
    return html[start:end]


def _visible(fragment: str) -> str:
    return re.sub(r"<[^>]+>", "", fragment)


def _candidate_cfg() -> Dict[str, Any]:
    return {**_v1_staged(), **_candidate(_SHOT_04), K: {_SHOT_04: _uploaded(_SHOT_04)}}


# --------------------------------------------------------------------------- #
# A-6 — C区 shows V1 and V2 separately and visually distinct + named pivot
# --------------------------------------------------------------------------- #


def test_named_compare_pivot_present() -> None:
    p = _pivot(_render(_view(_candidate_cfg())))
    assert 'data-role="ms-compare-confirm-pivot-title"' in p
    assert "生成与对比：V1 / V2" in p


def test_v1_and_v2_shown_separately_and_distinct() -> None:
    p = _pivot(_render(_view(_candidate_cfg())))
    # explicit V1 reference + V2 candidate label, each with its own version marker
    assert 'data-role="ms-compare-current-main" data-preview-version="V1"' in p
    assert 'data-role="ms-compare-candidate-label" data-preview-version="V2"' in p
    assert 'data-role="ms-regen-candidate" data-preview-version="V2"' in p
    assert "当前主版本：V1" in p
    assert "新预览候选" in p and "候选" in p


def test_v2_always_labelled_candidate() -> None:
    vis = _visible(_pivot(_render(_view(_candidate_cfg()))))
    assert "候选" in vis  # never asserted as confirmed main before confirm


# --------------------------------------------------------------------------- #
# changed-shots + uploaded-materials (#212) shown
# --------------------------------------------------------------------------- #


def test_changed_shots_listed_from_existing_truth() -> None:
    view = _view(_candidate_cfg())
    changed = view["candidate_changed_shots"]
    assert [c["shot_id"] for c in changed] == [_SHOT_04]
    p = _pivot(_render(view))
    assert 'data-role="ms-compare-changed-shots"' in p
    assert "哪些镜头发生了变化：" in p
    assert f'data-role="ms-compare-changed-shot" data-shot-id="{_SHOT_04}"' in p


def test_changed_shots_empty_without_candidate() -> None:
    assert _view(_v1_staged())["candidate_changed_shots"] == []


def test_uploaded_material_consumed_list_preserved() -> None:
    p = _pivot(_render(_view(_candidate_cfg())))
    # #212 consumed-material surface still rendered (operator-safe)
    assert 'data-role="ms-regen-consumed-materials"' in p
    assert "fresh_tomato.png" in p


# --------------------------------------------------------------------------- #
# A-7 delivery guard + delivery unaffected · A-8 confirm uses existing behavior
# --------------------------------------------------------------------------- #


def test_delivery_guard_truth_shown() -> None:
    p = _pivot(_render(_view(_candidate_cfg())))
    assert 'data-role="ms-compare-delivery-guard"' in p
    assert "V2 未确认前不会影响交付。" in p


def test_unconfirmed_v2_does_not_affect_delivery() -> None:
    view = _view(_candidate_cfg())
    # delivery still tracks the confirmed main (V1), not the candidate
    assert view["current_main_version"] == "V1"
    assert view["delivery"]["delivery_candidate"] == view["main_result"]["delivery_candidate"]
    assert view["delivery"]["official_publish_ready"] is False


def test_confirm_discard_continue_actions_present() -> None:
    p = _pivot(_render(_view(_candidate_cfg())))
    # existing confirm/discard/continue affordances preserved (A-8 existing behavior)
    assert 'data-role="ms-regen-confirm"' in p and "设为主版本" in p
    assert 'data-role="ms-regen-discard"' in p and "丢弃新预览" in p
    assert 'data-role="ms-regen-keep-tuning"' in p and "继续调整" in p


# --------------------------------------------------------------------------- #
# A-13 V1 preserved · A-11 leakage · A-12 #212 · A-14 publish-ready
# --------------------------------------------------------------------------- #


def test_v1_preserved_while_candidate_pending() -> None:
    view = _view(_candidate_cfg())
    assert view["current_main_version"] == "V1"
    assert view["main_result"]["preview_url"] == V1_URL  # V1 not overwritten


def test_failed_regeneration_keeps_v1_no_candidate() -> None:
    view = _view({**_v1_staged(), **_failed()})
    assert view["has_candidate_preview"] is False
    assert view["current_main_version"] == "V1"
    assert view["main_result"]["preview_url"] == V1_URL
    p = _pivot(_render(view))
    assert 'data-role="ms-regen-failed"' in p  # failed state, V1 intact


def test_pivot_no_raw_backend_leakage() -> None:
    vis = _visible(_pivot(_render(_view(_candidate_cfg()))))
    for token in ("local_path", "manifest", "provider", "publish_url",
                  "publish_status", "akool", "msmaterial://", "official_publish_ready"):
        assert token not in vis


def test_212_byte_consumption_unchanged() -> None:
    view = _view(_candidate_cfg())
    assert view["new_preview"]["material_bytes_consumed"] is True
    by_id = {s["shot_id"]: s for s in view["shots"]}
    assert by_id[_SHOT_04]["bytes_consumed_for_shot"] is True


def test_official_publish_ready_false_across_states() -> None:
    for cfg in [_v1_staged(), _candidate_cfg(), {**_v1_staged(), **_failed()}]:
        assert _view(cfg)["delivery"]["official_publish_ready"] is False
