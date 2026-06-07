"""Matrix Script Guided Operator Workflow — PR-2: B区 逐镜卡片主流程收敛.

Gate Spec: docs/design/MATRIX_SCRIPT_GUIDED_OPERATOR_WORKFLOW_GATE_SPEC_20260607.md §3.B.
B区 shot cards converge on the operator main flow: each card explains WHY it is
suggested for handling (R-SHOT-REASON, A-2), upload is the primary path (A-4) with
advanced reference-binding folded/secondary (A-3), and an upload→regenerate handoff
nudge sits by the upload area (R-UPLOAD-HANDOFF, A-5). Presentation/projection only
over the merged #211..#215 substrate — no new producer, no second source of truth.
Behavior preserved: #212 byte consumption unchanged (A-12), official_publish_ready
stays false (A-14), no leakage (A-11).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict

from gateway.app.services.matrix_script import operator_workbench_view as owv
from gateway.app.services.matrix_script import tomato_real_result_plan as plan_mod

K = owv.MATERIAL_INTENT_KEY
_SHOTS = list(plan_mod.TOMATO_SHOTS)
_SHOT_04 = _SHOTS[3].shot_id  # reuse source
_SHOT_05 = _SHOTS[4].shot_id  # reuse source
_SHOT_01 = _SHOTS[0].shot_id  # real source
V1_URL = "/api/matrix-script/ms-pr2/tomato-real-result/preview/final.mp4"
V2_URL = "/api/matrix-script/ms-pr2/preview-version/V2/final.mp4"


def _v1_staged() -> Dict[str, Any]:
    return {
        "matrix_script_staged_candidate": {
            "has_result": True, "operator_usable": True, "delivery_candidate": True,
            "official_publish_ready": False, "preview_url": V1_URL,
            "shot_match_count": 3, "real_visual_count": 3, "shot_count": 5,
        }
    }


def _uploaded(shot_id: str, intent: str = "supplement") -> Dict[str, Any]:
    return {
        "intent": intent, "updated_at": "x",
        "material_ref": f"msmaterial://matrix_script/ms-pr2/{shot_id}/u1",
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
            "material_ref": f"msmaterial://matrix_script/ms-pr2/{consumed_shot_id}/u1",
            "material_source": owv.MATERIAL_UPLOAD_SOURCE,
        }],
    }}}


def _view(config: Dict[str, Any]) -> Dict[str, Any]:
    return owv.build_matrix_script_operator_workbench_view(
        {"task_id": "ms-pr2", "kind": "matrix_script", "config": config}
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
        task={"task_id": "ms-pr2"},
    )


def _b_zone(html: str) -> str:
    start = html.index('data-role="matrix-script-primary-material-music"')
    end = html.index('data-role="matrix-script-primary-delivery-entry"')
    return html[start:end]


def _visible(fragment: str) -> str:
    return re.sub(r"<[^>]+>", "", fragment)


# --------------------------------------------------------------------------- #
# A-2 — R-SHOT-REASON: shot cards explain WHY they are suggested for handling
# --------------------------------------------------------------------------- #


def test_reuse_shots_carry_suggestion_reason_real_shots_do_not() -> None:
    view = _view(_v1_staged())
    by_id = {s["shot_id"]: s for s in view["shots"]}
    # reuse shots are suggested with an operator reason
    assert by_id[_SHOT_04]["suggested_for_handling"] is True
    assert by_id[_SHOT_05]["suggested_for_handling"] is True
    assert by_id[_SHOT_04]["suggestion_reason_zh"].startswith("建议处理原因：")
    assert by_id[_SHOT_05]["suggestion_reason_zh"].startswith("建议处理原因：")
    # real-source shots are not flagged and carry no reason
    assert by_id[_SHOT_01]["suggested_for_handling"] is False
    assert by_id[_SHOT_01]["suggestion_reason_zh"] is None


def test_suggestion_reason_renders_with_prefix_and_preserves_copy() -> None:
    b = _b_zone(_render(_view(_v1_staged())))
    assert "建议处理原因：" in b
    # established per-shot copy preserved (substrings)
    assert "当前为复用素材，建议补充真实品尝素材。" in b
    assert "当前为复用素材，建议补充递向镜头素材。" in b


# --------------------------------------------------------------------------- #
# A-4 upload primary · A-3 advanced binding folded/secondary
# --------------------------------------------------------------------------- #


def test_upload_is_primary_and_before_advanced_binding() -> None:
    b = _b_zone(_render(_view(_v1_staged())))
    assert 'data-upload-primary="true"' in b
    assert "上传这个镜头的新素材" in b
    # upload block appears before the advanced binding block (primary path first)
    assert b.index('data-role="ms-primary-shot-material-upload"') < \
        b.index('data-role="ms-primary-shot-material-attach"')


def test_advanced_binding_folded_and_labelled() -> None:
    b = _b_zone(_render(_view(_v1_staged())))
    # advanced binding stays a collapsed <details> with the §3.B.1 label + helper
    assert "高级：绑定已有素材引用" in b
    assert "仅当你已有系统素材引用时使用。普通运营请上传素材。" in b
    assert '<details data-role="ms-primary-shot-material-attach"' in b
    # binding count still one per shot (capability preserved)
    assert b.count('data-role="ms-primary-shot-material-attach"') == len(_SHOTS)


def test_asset_ref_not_a_required_primary_input() -> None:
    # The primary upload path uses a file input; no asset:// / msmaterial:// is
    # presented as a required primary input (only inside the folded advanced block).
    b = _b_zone(_render(_view(_v1_staged())))
    upload = b[b.index('data-role="ms-primary-shot-material-upload"'):
               b.index('data-role="ms-primary-shot-material-attach"')]
    assert "asset://" not in upload
    assert "msmaterial://" not in upload
    assert 'type="file"' in upload


# --------------------------------------------------------------------------- #
# A-5 — R-UPLOAD-HANDOFF nudge near the upload area
# --------------------------------------------------------------------------- #


def test_upload_handoff_nudge_shown_after_upload_no_candidate() -> None:
    view = _view({**_v1_staged(), K: {_SHOT_04: _uploaded(_SHOT_04)}})
    by_id = {s["shot_id"]: s for s in view["shots"]}
    assert by_id[_SHOT_04]["upload_handoff_zh"] is not None
    b = _b_zone(_render(view))
    assert 'data-role="ms-primary-shot-upload-handoff"' in b
    assert "请点击“再次生成预览”生成 V2" in b


def test_upload_handoff_absent_without_upload() -> None:
    view = _view(_v1_staged())
    assert all(s["upload_handoff_zh"] is None for s in view["shots"])
    b = _b_zone(_render(view))
    assert 'data-role="ms-primary-shot-upload-handoff"' not in b


def test_upload_handoff_clears_once_candidate_exists() -> None:
    # Material uploaded AND a V2 candidate already exists → no stale handoff.
    view = _view({**_v1_staged(), **_candidate(_SHOT_04), K: {_SHOT_04: _uploaded(_SHOT_04)}})
    by_id = {s["shot_id"]: s for s in view["shots"]}
    assert by_id[_SHOT_04]["upload_handoff_zh"] is None


# --------------------------------------------------------------------------- #
# A-11 leakage · A-12 #212 byte-consumption · A-14 publish-ready
# --------------------------------------------------------------------------- #


def test_b_zone_no_raw_backend_leakage() -> None:
    view = _view({**_v1_staged(), **_candidate(_SHOT_04), K: {_SHOT_04: _uploaded(_SHOT_04)}})
    visible = _visible(_b_zone(_render(view)))
    for token in ("local_path", "manifest", "provider", "publish_url",
                  "publish_status", "akool", "msmaterial://", "official_publish_ready"):
        assert token not in visible


def test_212_byte_consumption_copy_unchanged() -> None:
    # The #212 honest "uploaded bytes consumed" copy is still produced unchanged.
    view = _view({**_v1_staged(), **_candidate(_SHOT_04), K: {_SHOT_04: _uploaded(_SHOT_04)}})
    assert view["new_preview"]["material_bytes_consumed"] is True
    by_id = {s["shot_id"]: s for s in view["shots"]}
    assert by_id[_SHOT_04]["bytes_consumed_for_shot"] is True
    assert by_id[_SHOT_04]["entered_v2_candidate"] is True


def test_official_publish_ready_false() -> None:
    for cfg in [_v1_staged(),
                {**_v1_staged(), K: {_SHOT_04: _uploaded(_SHOT_04)}},
                {**_v1_staged(), **_candidate(_SHOT_04), K: {_SHOT_04: _uploaded(_SHOT_04)}}]:
        assert _view(cfg)["delivery"]["official_publish_ready"] is False
