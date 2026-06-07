"""Matrix Script Guided Operator Workflow — PR-5: E区 进阶/诊断折叠与动作记录.

Gate Spec: docs/design/MATRIX_SCRIPT_GUIDED_OPERATOR_WORKFLOW_GATE_SPEC_20260607.md §3.E.
The advanced / diagnostic surfaces (视频变体 / 脚本理解 / 过程记录) are collapsed by
default, out of the primary operator path. A new operator-safe process/action log
shows operator-language step events only (已记录处理方式 / 上传成功 / 已请求再次生成预览
/ V2 新预览已生成) — projection over existing facts, with no raw backend / state /
debug fields (those stay in J区). Presentation/projection only; preserves all truth.
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
_SHOT_04_TITLE = _SHOTS[3].title_zh
V1_URL = "/api/matrix-script/ms-pr5/tomato-real-result/preview/final.mp4"
V2_URL = "/api/matrix-script/ms-pr5/preview-version/V2/final.mp4"


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
        "material_ref": f"msmaterial://matrix_script/ms-pr5/{shot_id}/u1",
        "material_name": "eat_tomato.png", "material_kind": "image",
        "material_source": owv.MATERIAL_UPLOAD_SOURCE,
        "storage_scope": "local_workspace", "bytes_resolvable": True,
    }


def _candidate(consumed_shot_id: str) -> Dict[str, Any]:
    return {owv.PREVIEW_VERSIONS_KEY: {"V2": {
        "role": owv.ROLE_CANDIDATE, "preview_url": V2_URL,
        "source": "material_regeneration", "based_on_intents": ["supplement"],
        "based_on_assets": [{"shot_id": consumed_shot_id, "material_name": "eat_tomato.png", "material_kind": "image"}],
        "material_bytes_consumed": True,
        "consumed_materials": [{
            "shot_id": consumed_shot_id, "material_name": "eat_tomato.png",
            "material_kind": "image",
            "material_ref": f"msmaterial://matrix_script/ms-pr5/{consumed_shot_id}/u1",
            "material_source": owv.MATERIAL_UPLOAD_SOURCE,
        }],
    }}}


def _view(config: Dict[str, Any]) -> Dict[str, Any]:
    return owv.build_matrix_script_operator_workbench_view(
        {"task_id": "ms-pr5", "kind": "matrix_script", "config": config}
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
        task={"task_id": "ms-pr5"},
    )


def _record(html: str) -> str:
    start = html.index('data-role="matrix-script-primary-process-record"')
    end = html.index("</div>", html.index('data-role="ms-primary-process-record-log"', start))
    return html[start:end]


def _visible(fragment: str) -> str:
    return re.sub(r"<[^>]+>", "", fragment)


def _cfg_uploaded_with_candidate() -> Dict[str, Any]:
    return {**_v1_staged(), **_candidate(_SHOT_04), K: {_SHOT_04: _uploaded(_SHOT_04)}}


# --------------------------------------------------------------------------- #
# advanced / diagnostic surfaces collapsed by default
# --------------------------------------------------------------------------- #


def test_variants_and_script_and_record_are_collapsed_details() -> None:
    html = _render(_view(_cfg_uploaded_with_candidate()))
    # all three E-zone surfaces are <details> (collapsed by default — no `open`)
    for role in ('ms-primary-video-variants-fold',
                 'ms-primary-script-story-fold',
                 'ms-primary-process-record-fold'):
        assert f'<details data-role="{role}"' in html
        # the <details> must not be force-opened
        assert f'<details data-role="{role}" open' not in html


# --------------------------------------------------------------------------- #
# operator-safe process/action log
# --------------------------------------------------------------------------- #


def test_action_log_shows_operator_language_steps() -> None:
    view = _view(_cfg_uploaded_with_candidate())
    log = view["process_action_log"]
    assert any("已记录处理方式" in e and _SHOT_04_TITLE in e and "补充素材" in e for e in log)
    assert any("上传成功" in e and "eat_tomato.png" in e for e in log)
    assert "V2 新预览已生成" in log
    r = _record(_render(view))
    assert 'data-role="ms-primary-process-record-log"' in r
    assert "eat_tomato.png" in r


def test_replace_intent_logs_replace_verb() -> None:
    view = _view({**_v1_staged(), K: {_SHOT_04: _uploaded(_SHOT_04, intent="replace")}})
    assert any("已记录处理方式" in e and "替换素材" in e for e in view["process_action_log"])


def test_action_log_empty_when_no_activity() -> None:
    view = _view(_v1_staged())
    assert view["process_action_log"] == []
    # with no log, the collapsed record section does not render
    assert 'data-role="matrix-script-primary-process-record"' not in _render(view)


# --------------------------------------------------------------------------- #
# no raw leakage in the record / primary path
# --------------------------------------------------------------------------- #


def test_action_log_has_no_raw_backend_fields() -> None:
    view = _view(_cfg_uploaded_with_candidate())
    blob = " ".join(view["process_action_log"])
    for token in ("local_path", "manifest", "provider", "publish_url",
                  "publish_status", "akool", "msmaterial://", "asset://",
                  "official_publish_ready", "fallback_semantic_reuse"):
        assert token not in blob
    r = _visible(_record(_render(view)))
    for token in ("local_path", "manifest", "provider", "publish_url",
                  "publish_status", "akool", "msmaterial://", "official_publish_ready"):
        assert token not in r


# --------------------------------------------------------------------------- #
# truth preserved
# --------------------------------------------------------------------------- #


def test_truth_preserved_by_fold() -> None:
    view = _view(_cfg_uploaded_with_candidate())
    assert view["current_main_version"] == "V1"
    assert view["delivery"]["official_publish_ready"] is False
    assert view["new_preview"]["material_bytes_consumed"] is True
