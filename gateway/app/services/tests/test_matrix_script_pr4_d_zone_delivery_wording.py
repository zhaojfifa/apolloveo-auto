"""Matrix Script Guided Operator Workflow — PR-4: D区 交付候选与确认保护.

Gate Spec: docs/design/MATRIX_SCRIPT_GUIDED_OPERATOR_WORKFLOW_GATE_SPEC_20260607.md §3.D.
The primary D区 delivery surface shows delivery truth in operator wording only —
R-DELIVERY-WORDING (A-9): `正式交付就绪：否`, never the raw `official_publish_ready=false`.
Delivery follows the confirmed main only; an unconfirmed V2 is never the candidate
(A-7); confirming V2 (existing behavior) switches the candidate to V2 (A-8); V1 is
preserved (A-13); official_publish_ready stays false (A-14). Presentation/copy only
— no delivery-truth source / route / producer change.
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
V1_URL = "/api/matrix-script/ms-pr4/tomato-real-result/preview/final.mp4"
V2_URL = "/api/matrix-script/ms-pr4/preview-version/V2/final.mp4"


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
        "material_ref": f"msmaterial://matrix_script/ms-pr4/{shot_id}/u1",
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
            "material_ref": f"msmaterial://matrix_script/ms-pr4/{consumed_shot_id}/u1",
            "material_source": owv.MATERIAL_UPLOAD_SOURCE,
        }],
    }}}


def _view(config: Dict[str, Any]) -> Dict[str, Any]:
    return owv.build_matrix_script_operator_workbench_view(
        {"task_id": "ms-pr4", "kind": "matrix_script", "config": config}
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
        task={"task_id": "ms-pr4"},
    )


def _d_zone(html: str) -> str:
    """The primary D区 delivery section."""
    start = html.index('data-role="matrix-script-primary-delivery-entry"')
    end = html.index('data-role="matrix-script-primary-video-variants"')
    return html[start:end]


def _visible(fragment: str) -> str:
    return re.sub(r"<[^>]+>", "", fragment)


# --------------------------------------------------------------------------- #
# A-9 — R-DELIVERY-WORDING
# --------------------------------------------------------------------------- #


def test_primary_delivery_shows_operator_wording_only() -> None:
    d = _d_zone(_render(_view(_v1_staged())))
    assert "正式交付就绪：否" in d
    assert "official_publish_ready=false" not in d
    assert "official_publish_ready" not in _visible(d)
    assert "正式交付就绪：false" not in d


# --------------------------------------------------------------------------- #
# A-7 — delivery follows confirmed main; unconfirmed V2 is never the candidate
# --------------------------------------------------------------------------- #


def test_unconfirmed_v2_not_shown_as_delivery_candidate() -> None:
    view = _view({**_v1_staged(), **_candidate(_SHOT_04), K: {_SHOT_04: _uploaded(_SHOT_04)}})
    assert view["current_main_version"] == "V1"
    d = _d_zone(_render(view))
    assert "当前交付候选：主视频 V1。" in d
    assert "主视频 V2" not in d
    assert "V2 新预览在确认为主版本前不会进入交付" in d
    # truth: delivery still tracks the confirmed main, publish-ready false
    assert view["delivery"]["delivery_candidate"] == view["main_result"]["delivery_candidate"]
    assert view["delivery"]["official_publish_ready"] is False


# --------------------------------------------------------------------------- #
# A-8 — confirming V2 switches the candidate to V2 (existing behavior)
# --------------------------------------------------------------------------- #


def test_confirmed_v2_becomes_delivery_candidate() -> None:
    # Simulate the existing post-confirm state: current main is now V2.
    cfg = {**_v1_staged(), owv.CURRENT_MAIN_VERSION_KEY: "V2"}
    cfg["matrix_script_staged_candidate"]["preview_url"] = V2_URL
    view = _view(cfg)
    assert view["current_main_version"] == "V2"
    d = _d_zone(_render(view))
    assert "当前交付候选：主视频 V2。" in d
    assert "正式交付就绪：否" in d  # still operator wording, still not-ready


# --------------------------------------------------------------------------- #
# A-13 V1 preserved · A-11 leakage · A-14 publish-ready
# --------------------------------------------------------------------------- #


def test_v1_preserved_while_candidate_pending() -> None:
    view = _view({**_v1_staged(), **_candidate(_SHOT_04), K: {_SHOT_04: _uploaded(_SHOT_04)}})
    assert view["current_main_version"] == "V1"
    assert view["main_result"]["preview_url"] == V1_URL


def test_primary_delivery_no_raw_leakage() -> None:
    view = _view({**_v1_staged(), **_candidate(_SHOT_04), K: {_SHOT_04: _uploaded(_SHOT_04)}})
    vis = _visible(_d_zone(_render(view)))
    for token in ("local_path", "manifest", "provider", "publish_url",
                  "publish_status", "akool", "msmaterial://", "official_publish_ready"):
        assert token not in vis


def test_official_publish_ready_false_across_states() -> None:
    for cfg in [_v1_staged(),
                {**_v1_staged(), **_candidate(_SHOT_04), K: {_SHOT_04: _uploaded(_SHOT_04)}}]:
        assert _view(cfg)["delivery"]["official_publish_ready"] is False
