"""Matrix Script Guided Operator Workflow — PR-1: A区 state narration.

Gate Spec: docs/design/MATRIX_SCRIPT_GUIDED_OPERATOR_WORKFLOW_GATE_SPEC_20260607.md §3.A.
A区 presents the derived process_state in operator language as
当前主视频 / 当前状态(现状) / 下一步 — projection only over the already-merged
#211..#215 substrate. No raw process_state enum (and no other raw backend field)
may appear as primary operator copy; the enum stays a diagnosis-only data
attribute. official_publish_ready stays false. Behavior is unchanged.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict

from gateway.app.services.matrix_script import operator_workbench_view as owv
from gateway.app.services.matrix_script import tomato_real_result_plan as plan_mod

K = owv.MATERIAL_INTENT_KEY
_SHOTS = list(plan_mod.TOMATO_SHOTS)
_SHOT_05 = _SHOTS[4].shot_id
V1_URL = "/api/matrix-script/ms-pr1/tomato-real-result/preview/final.mp4"
V2_URL = "/api/matrix-script/ms-pr1/preview-version/V2/final.mp4"


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
        "material_ref": f"msmaterial://matrix_script/ms-pr1/{shot_id}/u1",
        "material_name": "fresh_tomato.png", "material_kind": "image",
        "material_source": owv.MATERIAL_UPLOAD_SOURCE,
        "storage_scope": "local_workspace", "bytes_resolvable": True,
    }


def _candidate(consumed_shot_id: str) -> Dict[str, Any]:
    return {owv.PREVIEW_VERSIONS_KEY: {"V2": {
        "role": owv.ROLE_CANDIDATE, "preview_url": V2_URL,
        "source": "material_regeneration", "based_on_intents": ["replace"],
        "based_on_assets": [{"shot_id": consumed_shot_id, "material_name": "fresh_tomato.png", "material_kind": "image"}],
        "material_bytes_consumed": True,
        "consumed_materials": [{
            "shot_id": consumed_shot_id, "material_name": "fresh_tomato.png",
            "material_kind": "image",
            "material_ref": f"msmaterial://matrix_script/ms-pr1/{consumed_shot_id}/u1",
            "material_source": owv.MATERIAL_UPLOAD_SOURCE,
        }],
    }}}


def _view(config: Dict[str, Any]) -> Dict[str, Any]:
    return owv.build_matrix_script_operator_workbench_view(
        {"task_id": "ms-pr1", "kind": "matrix_script", "config": config}
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
        task={"task_id": "ms-pr1"},
    )


def _banner(html: str) -> str:
    """The A区 narration banner only (from its full opening <div> tag)."""
    marker = html.index('data-role="ms-process-state-banner"')
    start = html.rindex("<div", 0, marker)
    end = html.index("</div>", html.index('data-role="ms-process-next-step"', marker))
    return html[start:end]


def _visible(fragment: str) -> str:
    """Strip all tags (and thus all attributes) → visible primary copy only."""
    return re.sub(r"<[^>]+>", "", fragment)


# --------------------------------------------------------------------------- #
# §3.A — 当前状态(现状) + 下一步 per process_state
# --------------------------------------------------------------------------- #


def test_not_generated_omits_main_version_and_guides_to_generate() -> None:
    view = _view({})
    assert view["process_state"] == "not_generated"
    n = view["process_narration"]
    assert n["current_main_version"] is None        # no main video yet
    assert n["status_zh"] == "未生成"
    assert "生成主视频预览" in n["next_step_zh"]
    banner = _banner(_render(view))
    assert "当前主视频：" not in banner              # version line omitted
    assert "当前状态：" in banner and "下一步：" in banner


def test_stable_shows_v1_and_guides_to_inspect_or_deliver() -> None:
    view = _view(_v1_staged())
    assert view["process_state"] == "stable"
    n = view["process_narration"]
    assert n["current_main_version"] == "V1"
    assert n["status_zh"] == "稳定"
    assert "检查镜头" in n["next_step_zh"]
    banner = _visible(_banner(_render(view)))
    assert "当前主视频：V1" in banner
    assert "当前状态：稳定" in banner
    assert "下一步：" in banner


def test_intent_only_guides_upload_first() -> None:
    view = _view({**_v1_staged(), K: {_SHOT_05: {"intent": "replace", "updated_at": "x"}}})
    assert view["process_state"] == "intent_only"
    n = view["process_narration"]
    assert n["status_zh"] == "已记录调整意图"
    assert "上传" in n["next_step_zh"]


def test_material_ready_guides_regenerate() -> None:
    view = _view({**_v1_staged(), K: {_SHOT_05: _uploaded(_SHOT_05)}})
    assert view["process_state"] == "material_ready"
    n = view["process_narration"]
    assert n["status_zh"] == "素材已就绪"
    assert "再次生成预览" in n["next_step_zh"]


def test_generation_running_guides_waiting() -> None:
    view = _view({**_v1_staged(),
                  owv.REGEN_STATUS_KEY: {"status": "preview_generation_running",
                                         "started_at": "2099-01-01T00:00:00+00:00"}})
    assert view["process_state"] == "generation_running"
    n = view["process_narration"]
    assert n["status_zh"] == "正在生成 V2"
    assert "自动更新" in n["next_step_zh"]
    assert "不影响当前主视频" in n["next_step_zh"]


def test_candidate_ready_guides_compare_confirm() -> None:
    view = _view({**_v1_staged(), **_candidate(_SHOT_05), K: {_SHOT_05: _uploaded(_SHOT_05)}})
    assert view["process_state"] == "candidate_ready"
    n = view["process_narration"]
    assert n["status_zh"] == "V2 待确认"
    assert "对比 V1 / V2" in n["next_step_zh"]
    assert "确认主版本" in n["next_step_zh"]


def test_failed_guides_retry_and_preserves_main() -> None:
    view = _view({**_v1_staged(),
                  owv.REGEN_STATUS_KEY: {"status": "preview_generation_failed"}})
    assert view["process_state"] == "failed"
    n = view["process_narration"]
    assert n["status_zh"] == "生成失败"
    assert "当前主视频未受影响" in n["next_step_zh"]
    assert "重试" in n["next_step_zh"]


# --------------------------------------------------------------------------- #
# §3.A leakage + invariants
# --------------------------------------------------------------------------- #


def test_a_banner_visible_copy_has_no_raw_process_state_enum() -> None:
    # The enum is allowed only as a diagnosis data attribute, never visible copy.
    for cfg, enum in [
        ({}, "not_generated"),
        (_v1_staged(), "stable"),
        ({**_v1_staged(), **_candidate(_SHOT_05), K: {_SHOT_05: _uploaded(_SHOT_05)}},
         "candidate_ready"),
    ]:
        view = _view(cfg)
        banner = _banner(_render(view))
        # data attribute still carries the enum (diagnosis affordance)
        assert f'data-process-state="{enum}"' in banner
        # but visible copy (attributes stripped) must not contain the raw enum
        assert enum not in _visible(banner)


def test_a_banner_has_no_raw_backend_fields() -> None:
    view = _view({**_v1_staged(), **_candidate(_SHOT_05), K: {_SHOT_05: _uploaded(_SHOT_05)}})
    visible = _visible(_banner(_render(view)))
    for token in ("official_publish_ready", "material_bytes_consumed",
                  "preview_generation_succeeded", "local_path", "msmaterial://",
                  "provider", "publish_url", "manifest"):
        assert token not in visible


def test_official_publish_ready_stays_false_across_states() -> None:
    for cfg in [{}, _v1_staged(),
                {**_v1_staged(), K: {_SHOT_05: _uploaded(_SHOT_05)}},
                {**_v1_staged(), **_candidate(_SHOT_05), K: {_SHOT_05: _uploaded(_SHOT_05)}}]:
        view = _view(cfg)
        assert view["delivery"]["official_publish_ready"] is False


def test_narration_markers_present_in_render() -> None:
    view = _view(_v1_staged())
    html = _render(view)
    for marker in ('data-role="ms-process-current-main"',
                   'data-role="ms-process-status"',
                   'data-role="ms-process-next-step"'):
        assert marker in html
