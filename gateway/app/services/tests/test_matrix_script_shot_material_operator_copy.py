"""Matrix Script — Shot material operator-copy clarity (B区 decision area).

Follow-up to P1-3 (PR-C #211 upload/storage handle + PR-D #212 byte
consumption, both already merged). This is a COPY/LAYOUT-only correction: the
per-shot material controls now form a clear operator decision area titled
"这个镜头怎么处理？" with operator-language buttons (使用当前素材 / 补充这个镜头
素材 / 替换这个镜头素材), per-choice helper text, and an explicit upload section
("上传这个镜头的新素材") stating that uploading does NOT immediately overwrite
the main video.

It changes ONLY operator-facing copy. No route / storage / resolver /
regeneration / lifecycle behavior changes; intent + upload handle still persist;
bytes_resolvable stays true for uploaded material; V1 preserved; V2 untouched;
delivery protected; official_publish_ready=false.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Optional

from gateway.app.services.matrix_script import operator_workbench_view as owv
from gateway.app.services.matrix_script import tomato_real_result_plan as plan_mod

INTENT_KEY = owv.MATERIAL_INTENT_KEY
_SHOTS = list(plan_mod.TOMATO_SHOTS)
_SHOT_04 = _SHOTS[3].shot_id
_SHOT_05 = _SHOTS[4].shot_id
V1_URL = "/api/matrix-script/ms-copy-1/tomato-real-result/preview/final.mp4"

# Old confusing PRIMARY BUTTON labels that must no longer be button text.
_OLD_PRIMARY_BUTTON_LABELS = {"标记替换素材", "标记补素材", "保持当前素材"}
# New operator-language button labels keyed by data-intent.
_NEW_PRIMARY_BUTTON_LABELS = {
    "keep": "使用当前素材",
    "supplement": "补充这个镜头素材",
    "replace": "替换这个镜头素材",
}


def _v1_staged() -> Dict[str, Any]:
    return {
        "matrix_script_staged_candidate": {
            "has_result": True,
            "operator_usable": True,
            "delivery_candidate": True,
            "official_publish_ready": False,
            "preview_url": V1_URL,
        }
    }


def _ms_task(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {"task_id": "ms-copy-1", "kind": "matrix_script", "config": config or {}}


def _render_ms_primary_branch(overlay: Dict[str, Any]) -> str:
    from jinja2 import ChainableUndefined, Environment

    tpl = Path("gateway/app/templates/task_workbench.html").read_text(encoding="utf-8")
    start = tpl.index("{% if ms_main_video_result.is_matrix_script %}")
    end = tpl.index("{# Phase 2C", start)
    branch = tpl[start:end]
    return Environment(undefined=ChainableUndefined, autoescape=True).from_string(branch).render(
        ms_main_video_result={"is_matrix_script": True, "state_kind": "deliverable",
                              "state_label_zh": "运营可用", "preview": {"available": False}, "primary_actions": []},
        ms_overlay=overlay,
        ms_overlay_mr=overlay["main_result"],
        ms_overlay_has=overlay["main_result"]["operator_usable"],
        ms_preview_compare={"is_matrix_script": True},
        task={"task_id": "ms-copy-1"},
    )


def _primary_only(html: str) -> str:
    """Trim to the operator-facing primary flow (before technical diagnostics)."""
    cut = html.find('data-role="op-console-ms-technical-diagnostics-fold"')
    return html[:cut] if cut != -1 else html


def _button_labels(html: str) -> Dict[str, str]:
    """Map data-intent → rendered button text for the three decision buttons."""
    out: Dict[str, str] = {}
    for intent in ("keep", "supplement", "replace"):
        m = re.search(
            r'data-role="ms-primary-shot-intent-' + intent + r'"[^>]*>([^<]+)</button>',
            html,
        )
        assert m is not None, f"missing intent button: {intent}"
        out[intent] = m.group(1).strip()
    return out


def _overlay(config: Dict[str, Any]) -> Dict[str, Any]:
    return owv.build_matrix_script_operator_workbench_view(_ms_task(config))


# --------------------------------------------------------------------------- #
# 7.1 — primary UI carries the operator-language decision + upload copy.
# --------------------------------------------------------------------------- #


def test_primary_ui_contains_operator_decision_copy() -> None:
    html = _render_ms_primary_branch(_overlay(_v1_staged()))
    primary = _primary_only(html)
    for phrase in (
        "这个镜头怎么处理？",
        "使用当前素材",
        "补充这个镜头素材",
        "替换这个镜头素材",
        "上传这个镜头的新素材",
        "上传后不会立刻覆盖主视频",
        "需要回到主视频区点击“再次生成预览”",
    ):
        assert phrase in primary, f"missing required operator copy: {phrase}"
    # Per-choice helper text is present for each decision.
    assert "当前画面可用，不需要替换。" in primary
    assert "当前画面基本可用，但还需要补一个更合适的细节或补充镜头。" in primary
    assert "当前画面不合适，用上传的新素材替换这个镜头。" in primary
    # One decision area per shot.
    assert primary.count('data-role="ms-primary-shot-decision-title"') == 5


# --------------------------------------------------------------------------- #
# 7.2 — old confusing labels are not used as primary button labels.
# --------------------------------------------------------------------------- #


def test_old_labels_not_used_as_primary_buttons() -> None:
    html = _render_ms_primary_branch(_overlay(_v1_staged()))
    labels = _button_labels(html)
    assert labels == _NEW_PRIMARY_BUTTON_LABELS
    for label in labels.values():
        assert label not in _OLD_PRIMARY_BUTTON_LABELS


# --------------------------------------------------------------------------- #
# 7.3 — no behavior changed (copy-only correction).
# --------------------------------------------------------------------------- #


def test_intent_still_persists_in_projection() -> None:
    overlay = _overlay({**_v1_staged(), INTENT_KEY: {
        _SHOT_04: {"intent": "supplement", "updated_at": "x"},
        _SHOT_05: {"intent": "replace", "updated_at": "x"},
    }})
    by_id = {s["shot_id"]: s for s in overlay["shots"]}
    assert by_id[_SHOT_04]["intent"] == "supplement"
    assert by_id[_SHOT_04]["intent_dirty"] is True
    assert by_id[_SHOT_04]["intent_label_zh"] == "已标记补充素材"
    assert by_id[_SHOT_05]["intent"] == "replace"
    assert by_id[_SHOT_05]["intent_label_zh"] == "已标记替换素材"
    assert overlay["material_changed"] is True


def test_uploaded_handle_persists_and_bytes_resolvable_true() -> None:
    overlay = _overlay({**_v1_staged(), INTENT_KEY: {_SHOT_05: {
        "intent": "replace", "updated_at": "x",
        "material_ref": "msmaterial://matrix_script/ms-copy-1/shot05/u1",
        "material_name": "fresh_tomato.png",
        "material_kind": "image",
        "material_source": owv.MATERIAL_UPLOAD_SOURCE,
        "storage_scope": "local_workspace",
        "bytes_resolvable": True,
    }}})
    by_id = {s["shot_id"]: s for s in overlay["shots"]}
    s5 = by_id[_SHOT_05]
    assert s5["material_attached"] is True
    assert s5["material_source"] == owv.MATERIAL_UPLOAD_SOURCE
    assert s5["bytes_resolvable"] is True
    assert s5["material_status_zh"] == "已上传，等待再次生成预览"
    # Uploaded-material status copy is surfaced verbatim in the rendered B区.
    html = _render_ms_primary_branch(overlay)
    assert "已上传，等待再次生成预览" in html


def test_v1_preserved_and_delivery_and_publish_flag_protected() -> None:
    overlay = _overlay({**_v1_staged(), INTENT_KEY: {_SHOT_05: {"intent": "replace", "updated_at": "x"}}})
    assert overlay["current_main_version"] == "V1"
    assert overlay["main_result"]["preview_url"] == V1_URL
    assert overlay["main_result"]["operator_usable"] is True
    assert overlay["main_result"]["official_publish_ready"] is False
    # Dirty material never auto-promotes; delivery still follows V1.
    assert overlay["delivery"]["delivery_candidate"] is True


# --------------------------------------------------------------------------- #
# 7.4 — no engineering / provider leakage in the primary UI.
# --------------------------------------------------------------------------- #


def test_primary_ui_has_no_engineering_leakage() -> None:
    overlay = _overlay({**_v1_staged(), INTENT_KEY: {_SHOT_05: {
        "intent": "replace", "updated_at": "x",
        "material_ref": "msmaterial://matrix_script/ms-copy-1/shot05/u1",
        "material_name": "fresh_tomato.png",
        "material_kind": "image",
        "material_source": owv.MATERIAL_UPLOAD_SOURCE,
        "storage_scope": "local_workspace",
        "bytes_resolvable": True,
        # A donor-shaped field that must never reach the operator surface.
        "local_path": "/var/lib/apolloveo/workspace/u1.png",
    }}})
    primary = _primary_only(_render_ms_primary_branch(overlay))
    for token in (
        "provider_url", "temporary_url", "download_url",
        "publish_url", "publish_status",
        "akool", "Akool", "model_id", "credit", "provider_task_id",
        "local_path", "/var/lib/apolloveo",
        "raw_manifest", "manifest_url",
    ):
        assert token not in primary, f"leaked engineering token: {token}"
