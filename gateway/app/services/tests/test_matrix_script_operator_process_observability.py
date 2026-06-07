"""Matrix Script — Operator Process Observability.

Makes the Matrix Script generation process explainable to operations: a single
derived process_state, per-shot visual-source / entered-V2 / next-action trace,
and stable action/version DOM markers — all as pure projection over the
already-merged P0/P1/P1-2/P1-3 substrate (#202..#214). No new generation
capability, no Akool, no storage/route behaviour change.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Optional

from gateway.app.services.matrix_script import operator_workbench_view as owv
from gateway.app.services.matrix_script import tomato_real_result_plan as plan_mod

K = owv.MATERIAL_INTENT_KEY
_SHOTS = list(plan_mod.TOMATO_SHOTS)
_SHOT_04 = _SHOTS[3].shot_id
_SHOT_05 = _SHOTS[4].shot_id
V1_URL = "/api/matrix-script/ms-obs/tomato-real-result/preview/final.mp4"
V2_URL = "/api/matrix-script/ms-obs/preview-version/V2/final.mp4"


def _v1_staged() -> Dict[str, Any]:
    return {
        "matrix_script_staged_candidate": {
            "has_result": True, "operator_usable": True, "delivery_candidate": True,
            "official_publish_ready": False, "preview_url": V1_URL,
            "shot_match_count": 3, "real_visual_count": 3, "shot_count": 5,
            "visual_semantic_match": "partial_pass",
        }
    }


def _uploaded(shot_id: str, intent: str = "replace") -> Dict[str, Any]:
    return {
        "intent": intent, "updated_at": "x",
        "material_ref": f"msmaterial://matrix_script/ms-obs/{shot_id}/u1",
        "material_name": "fresh_tomato.png", "material_kind": "image",
        "material_source": owv.MATERIAL_UPLOAD_SOURCE,
        "storage_scope": "local_workspace", "bytes_resolvable": True,
    }


def _candidate(consumed_shot_id: str) -> Dict[str, Any]:
    return {owv.PREVIEW_VERSIONS_KEY: {"V2": {
        "role": owv.ROLE_CANDIDATE, "preview_url": V2_URL,
        "source": "material_regeneration",
        "based_on_intents": ["replace"],
        "based_on_assets": [{"shot_id": consumed_shot_id, "material_name": "fresh_tomato.png", "material_kind": "image"}],
        "material_bytes_consumed": True,
        "consumed_materials": [{
            "shot_id": consumed_shot_id, "material_name": "fresh_tomato.png",
            "material_kind": "image", "material_ref": f"msmaterial://matrix_script/ms-obs/{consumed_shot_id}/u1",
            "material_source": owv.MATERIAL_UPLOAD_SOURCE,
        }],
    }}}


def _view(config: Dict[str, Any]) -> Dict[str, Any]:
    return owv.build_matrix_script_operator_workbench_view(
        {"task_id": "ms-obs", "kind": "matrix_script", "config": config}
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
        task={"task_id": "ms-obs"},
    )


def _a_zone(html: str) -> str:
    start = html.index('data-role="matrix-script-main-video-result"')
    end = html.index('data-role="matrix-script-primary-material-music"')
    return html[start:end]


def _c_zone(html: str) -> str:
    start = html.index('data-role="matrix-script-primary-delivery-entry"')
    end = html.index('data-role="matrix-script-primary-video-variants"')
    return html[start:end]


# --------------------------------------------------------------------------- #
# A区 process-state copy (§8.1–§8.5)
# --------------------------------------------------------------------------- #


def test_a_intent_only_does_not_show_material_updated_and_guides_to_upload() -> None:
    view = _view({**_v1_staged(), K: {_SHOT_05: {"intent": "replace", "updated_at": "x"}}})
    assert view["process_state"] == "intent_only"
    a = _a_zone(_render(view))
    assert "素材已更新，需要再次生成预览" not in a  # §8.1
    assert "已记录素材调整意图" in a
    assert "请先上传/绑定素材" in a  # §8.2


def test_a_material_ready_shows_regenerate_prompt() -> None:
    view = _view({**_v1_staged(), K: {_SHOT_05: _uploaded(_SHOT_05)}})
    assert view["process_state"] == "material_ready"
    a = _a_zone(_render(view))
    assert "素材已就绪，需要再次生成预览" in a  # §8.3


def test_a_regeneration_running_shows_v2_generating() -> None:
    view = _view({**_v1_staged(),
                  owv.REGEN_STATUS_KEY: {"status": "preview_generation_running",
                                         "started_at": "2099-01-01T00:00:00+00:00"}})
    assert view["process_state"] == "generation_running"
    a = _a_zone(_render(view))
    assert "正在生成 V2 新预览" in a  # §8.4


def test_a_v2_candidate_shows_v1_and_v2_separately() -> None:
    view = _view({**_v1_staged(), **_candidate(_SHOT_05), K: {_SHOT_05: _uploaded(_SHOT_05)}})
    assert view["process_state"] == "candidate_ready"
    a = _render(view)
    a_zone = _a_zone(a)
    # V1 main hero + V2 candidate both carry version markers (§8.5).
    assert 'data-preview-version="V1"' in a_zone
    assert 'data-preview-version="V2"' in a_zone
    assert a_zone.count("<video") >= 2


def test_v2_candidate_shows_based_on_assets_and_bytes_consumed_copy() -> None:
    view = _view({**_v1_staged(), **_candidate(_SHOT_05), K: {_SHOT_05: _uploaded(_SHOT_05)}})
    a = _a_zone(_render(view))
    assert "已使用运营上传素材生成新预览" in a  # §8.6 honest consumed copy
    assert 'data-material-bytes-consumed="true"' in a
    assert "fresh_tomato.png" in a


# --------------------------------------------------------------------------- #
# B区 shot trace (§8.7–§8.9)
# --------------------------------------------------------------------------- #


def test_b_each_shot_shows_current_visual_source() -> None:
    view = _view({**_v1_staged(), K: {_SHOT_05: _uploaded(_SHOT_05)}})
    html = _render(view)
    assert html.count("这个镜头现在用了什么？") == 5  # §8.7 one per shot
    assert "运营上传素材" in html      # the uploaded shot
    assert "原始生成素材" in html      # a real-asset shot
    assert "复用素材" in html          # a fallback_semantic_reuse shot


def test_b_uploaded_but_not_consumed_shows_not_in_new_preview() -> None:
    # Candidate consumed shot-04 only; shot-05 uploaded but not in the candidate.
    view = _view({**_v1_staged(), **_candidate(_SHOT_04),
                  K: {_SHOT_04: _uploaded(_SHOT_04), _SHOT_05: _uploaded(_SHOT_05)}})
    by_id = {s["shot_id"]: s for s in view["shots"]}
    assert by_id[_SHOT_05]["entered_v2_candidate"] is False
    assert by_id[_SHOT_05]["shot_observability_status_zh"] == "已上传，但尚未进入新预览。"
    assert "已上传，但尚未进入新预览。" in _render(view)  # §8.8


def test_b_consumed_by_v2_shows_entered_new_preview() -> None:
    view = _view({**_v1_staged(), **_candidate(_SHOT_05), K: {_SHOT_05: _uploaded(_SHOT_05)}})
    by_id = {s["shot_id"]: s for s in view["shots"]}
    assert by_id[_SHOT_05]["entered_v2_candidate"] is True
    assert by_id[_SHOT_05]["bytes_consumed_for_shot"] is True
    assert by_id[_SHOT_05]["shot_observability_status_zh"] == "已进入 V2 新预览。"
    assert "已进入 V2 新预览。" in _render(view)  # §8.9


# --------------------------------------------------------------------------- #
# C区 delivery truth (§8.10)
# --------------------------------------------------------------------------- #


def test_c_delivery_candidate_follows_confirmed_main_only() -> None:
    # Unconfirmed V2 candidate exists; confirmed main is still V1.
    view = _view({**_v1_staged(), **_candidate(_SHOT_05), K: {_SHOT_05: _uploaded(_SHOT_05)}})
    assert view["current_main_version"] == "V1"
    c = _c_zone(_render(view))
    assert "当前交付候选：主视频 V1。" in c  # §8.10 not switched to V2
    assert "主视频 V2" not in c
    assert "V2 新预览在确认为主版本前不会进入交付" in c
    # PR-4 §3.D R-DELIVERY-WORDING: primary D区 shows operator wording only, not the
    # raw official_publish_ready field. Underlying truth still asserted below.
    assert "正式交付就绪：否" in c
    assert "official_publish_ready=false" not in c
    assert view["delivery"]["official_publish_ready"] is False


# --------------------------------------------------------------------------- #
# Action observability + boundary (§8.11–§8.13)
# --------------------------------------------------------------------------- #


def test_action_markers_present_for_network_diagnosis() -> None:
    view = _view({**_v1_staged(), K: {_SHOT_05: _uploaded(_SHOT_05)}})
    html = _render(view)
    assert 'data-action="matrix-script-material-intent"' in html      # §8.11
    assert 'data-action="matrix-script-material-upload"' in html
    assert 'data-action="matrix-script-regenerate-preview"' in html
    assert 'data-action="matrix-script-regeneration-status"' in html
    # Process-state marker on the A区 container.
    assert 'data-process-state="material_ready"' in html


def test_no_engineering_leakage_in_primary_ui() -> None:
    view = _view({**_v1_staged(), **_candidate(_SHOT_05), K: {_SHOT_05: {
        **_uploaded(_SHOT_05), "local_path": "/var/lib/apolloveo/ws/u1.png",
    }}})
    html = _render(view)
    primary = html[: html.find('data-role="op-console-ms-technical-diagnostics-fold"')] or html
    for token in (
        "provider_url", "temporary_url", "download_url", "publish_url", "publish_status",
        "akool", "Akool", "model_id", "credit", "provider_task_id",
        "local_path", "/var/lib/apolloveo", "raw_manifest", "manifest_url",
    ):
        assert token not in primary, f"leaked: {token}"  # §8.12


def test_official_publish_ready_false_across_states() -> None:
    for cfg in (
        _v1_staged(),
        {**_v1_staged(), K: {_SHOT_05: {"intent": "replace", "updated_at": "x"}}},
        {**_v1_staged(), K: {_SHOT_05: _uploaded(_SHOT_05)}},
        {**_v1_staged(), **_candidate(_SHOT_05), K: {_SHOT_05: _uploaded(_SHOT_05)}},
    ):
        view = _view(cfg)
        assert view["main_result"]["official_publish_ready"] is False  # §8.13
        assert view["delivery"]["official_publish_ready"] is False
        assert view["generation_facts"]["current_main"]["official_publish_ready"] is False


# --------------------------------------------------------------------------- #
# §8.14 — #212 byte-consumption behaviour preserved (cross-check)
# --------------------------------------------------------------------------- #


def test_byte_consumption_behaviour_unchanged() -> None:
    view = _view({**_v1_staged(), **_candidate(_SHOT_05), K: {_SHOT_05: _uploaded(_SHOT_05)}})
    np = view["new_preview"]
    assert np["material_bytes_consumed"] is True
    assert np["material_usage_note_zh"] == owv.MATERIAL_USAGE_UPLOAD_CONSUMED_ZH
    assert np["consumed_materials"][0]["shot_id"] == _SHOT_05
    assert np["consumed_materials"][0]["material_name"] == "fresh_tomato.png"


# --------------------------------------------------------------------------- #
# process_state derivation precedence (unit)
# --------------------------------------------------------------------------- #


def test_process_state_precedence() -> None:
    assert _view(_v1_staged())["process_state"] == "stable"
    assert _view({})["process_state"] == "not_generated"
    assert _view({**_v1_staged(), K: {_SHOT_05: {"intent": "replace", "updated_at": "x"}}})["process_state"] == "intent_only"
    assert _view({**_v1_staged(), K: {_SHOT_05: _uploaded(_SHOT_05)}})["process_state"] == "material_ready"
    assert _view({**_v1_staged(), **_candidate(_SHOT_05), K: {_SHOT_05: _uploaded(_SHOT_05)}})["process_state"] == "candidate_ready"
