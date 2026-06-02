"""Matrix Script — PR-A real-result acceptance OVERLAY for the Workbench (PR-B).

NOT a second Workbench flow. The Matrix Script Workbench already renders the
result-oriented flow (① 主视频结果 / ② 故事板 / ③ 素材 / 配音 / 字幕 / 变体 /
⑤ 交付入口), bound to per-task presenters. This helper produces ONLY the thin
overlay that feeds the PR-A real-result acceptance (L2+L3) into the existing
① main-result, ② storyboard, and ⑤ delivery-entry sections — so a generated
operator-usable result is reflected in the existing sections instead of an
isolated/duplicate panel.

Overlay payload:
- ``main_result`` — operator_usable / technical_preview / visual_semantic_match
  / shot_match_count / shot_count / real_visual_count / delivery_candidate /
  preview_url / official_publish_ready=false / blocked_reason + status mapping.
- ``shots`` — per-shot acceptance overlay (asset_name / source / semantic_status
  / included_in_current_video) keyed off the fixed PR-A shot plan.
- ``delivery`` — delivery_candidate / preview_url / official_publish_ready.

Source of the result: the staged PR-A candidate on ``task.config`` (read-only),
or an explicit ``result`` arg (the route payload). When no result exists the
overlay is inert (``has_pr_a_result = False``) and the existing sections render
their normal not-generated state.

Hard boundary: no I/O; no provider/vendor/model/credit; no schema/contract; no
``official_publish_ready=true``; no hardcoded script-understanding / variants
rendered as task truth (removed per the mock-alignment review).
"""
from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional

from gateway.app.services.matrix_script import tomato_real_result_plan as plan_mod

LINE_ID = "matrix_script"

STATUS_OPERATOR_USABLE = "operator_usable"
STATUS_TECHNICAL_PREVIEW = "technical_preview"
STATUS_NOT_GENERATED = "not_generated"
STATUS_PREVIEW_GENERATION_RUNNING = "preview_generation_running"
STATUS_PREVIEW_GENERATION_FAILED = "preview_generation_failed"

# Status mapping onto the existing 主视频结果 vocabulary.
_STATUS_LABEL = {
    STATUS_OPERATOR_USABLE: "运营可用 · 可交付",
    STATUS_TECHNICAL_PREVIEW: "技术预览 · 待审核",
    STATUS_NOT_GENERATED: "未生成",
    STATUS_PREVIEW_GENERATION_RUNNING: "主视频预览生成中",
    STATUS_PREVIEW_GENERATION_FAILED: "首版预览生成失败",
}

_FORBIDDEN_TOKENS = (
    "provider_url", "temporary_url", "download_url", "akool", "vendor",
    "model_id", "credit", "provider_task_id", "publish_url", "publish_status",
)


def _truthy(v: Any) -> bool:
    return bool(v) and v not in ("", "false", "False", 0)


def _resolve_result(task: Mapping[str, Any], result: Optional[Mapping[str, Any]]) -> Optional[Mapping[str, Any]]:
    if isinstance(result, Mapping) and any(
        k in result for k in ("operator_usable", "delivery_candidate", "visual_semantic_match")
    ):
        return result
    config = task.get("config") if isinstance(task, Mapping) else None
    staged = config.get("matrix_script_staged_candidate") if isinstance(config, Mapping) else None
    if isinstance(staged, Mapping) and staged.get("has_result"):
        return staged
    initial = config.get("matrix_script_initial_preview_generation") if isinstance(config, Mapping) else None
    if isinstance(initial, Mapping) and initial.get("status") in {
        STATUS_PREVIEW_GENERATION_RUNNING,
        STATUS_PREVIEW_GENERATION_FAILED,
    }:
        return initial
    return None


def _build_main_result(result: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    if not result:
        return {
            "status": STATUS_NOT_GENERATED,
            "status_label_zh": _STATUS_LABEL[STATUS_NOT_GENERATED],
            "operator_usable": False,
            "technical_preview": False,
            "visual_semantic_match": None,
            "shot_match_count": 0,
            "shot_count": plan_mod.shot_count(),
            "real_visual_count": 0,
            "delivery_candidate": False,
            "official_publish_ready": False,
            "blocked_reason": None,
            "preview_url": None,
        }
    if result.get("status") in {
        STATUS_PREVIEW_GENERATION_RUNNING,
        STATUS_PREVIEW_GENERATION_FAILED,
    }:
        status = str(result.get("status"))
        return {
            "status": status,
            "status_label_zh": _STATUS_LABEL[status],
            "operator_usable": False,
            "technical_preview": False,
            "visual_semantic_match": None,
            "shot_match_count": 0,
            "shot_count": plan_mod.shot_count(),
            "real_visual_count": 0,
            "delivery_candidate": False,
            "official_publish_ready": False,
            "blocked_reason": result.get("error") if status == STATUS_PREVIEW_GENERATION_FAILED else None,
            "preview_url": None,
        }
    operator_usable = _truthy(result.get("operator_usable"))
    technical_preview = _truthy(result.get("technical_preview")) or not operator_usable
    status = STATUS_OPERATOR_USABLE if operator_usable else STATUS_TECHNICAL_PREVIEW
    return {
        "status": status,
        "status_label_zh": _STATUS_LABEL[status],
        "operator_usable": operator_usable,
        "technical_preview": technical_preview,
        "visual_semantic_match": result.get("visual_semantic_match"),
        "shot_match_count": int(result.get("shot_match_count", 0) or 0),
        "shot_count": int(result.get("shot_count", plan_mod.shot_count()) or plan_mod.shot_count()),
        "real_visual_count": int(result.get("real_visual_count", 0) or 0),
        "delivery_candidate": _truthy(result.get("delivery_candidate")),
        "official_publish_ready": False,
        "blocked_reason": result.get("blocked_reason") if not operator_usable else None,
        "preview_url": result.get("preview_url"),
    }


def _build_shots(has_result: bool) -> List[Dict[str, Any]]:
    cards: List[Dict[str, Any]] = []
    for shot in plan_mod.TOMATO_SHOTS:
        cards.append({
            "shot_id": shot.shot_id,
            "order": shot.order,
            "title": shot.title_zh,
            "asset_name": shot.asset_filename,
            "source": shot.source,
            "semantic_status": "pass" if shot.real_visual else "partial",
            "included_in_current_video": bool(has_result),
        })
    return cards


def _assert_clean(view: Mapping[str, Any]) -> None:
    blob = str(view).lower()
    hits = [t for t in _FORBIDDEN_TOKENS if t in blob]
    if hits:
        raise ValueError(f"operator overlay leaks forbidden tokens: {hits}")


def build_matrix_script_operator_workbench_view(
    task: Mapping[str, Any],
    *,
    result: Optional[Mapping[str, Any]] = None,
    env: Optional[Mapping[str, str]] = None,
) -> Dict[str, Any]:
    """Build the PR-A acceptance OVERLAY for the existing Workbench sections."""
    if not isinstance(task, Mapping):
        task = {}
    resolved = _resolve_result(task, result)
    has_result = (
        resolved is not None
        and resolved.get("status") not in {STATUS_PREVIEW_GENERATION_RUNNING, STATUS_PREVIEW_GENERATION_FAILED}
    )
    main_result = _build_main_result(resolved)
    view: Dict[str, Any] = {
        "is_matrix_script": True,
        "has_pr_a_result": has_result,
        "main_result": main_result,
        "shots": _build_shots(has_result),
        "delivery": {
            "delivery_candidate": main_result["delivery_candidate"],
            "preview_url": main_result["preview_url"],
            "official_publish_ready": False,
        },
        "generate_endpoint": "/api/matrix-script/{task_id}/tomato-real-result",
    }
    _assert_clean(view)
    return view
