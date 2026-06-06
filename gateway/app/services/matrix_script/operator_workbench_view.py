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

from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional

from gateway.app.services.matrix_script import tomato_real_result_plan as plan_mod

LINE_ID = "matrix_script"

STATUS_OPERATOR_USABLE = "operator_usable"
STATUS_TECHNICAL_PREVIEW = "technical_preview"
STATUS_NOT_GENERATED = "not_generated"
STATUS_PREVIEW_GENERATION_QUEUED = "preview_generation_queued"
STATUS_PREVIEW_GENERATION_RUNNING = "preview_generation_running"
STATUS_PREVIEW_GENERATION_FAILED = "preview_generation_failed"
STATUS_PREVIEW_GENERATION_RETRY_REQUIRED = "preview_generation_retry_required"

# In-progress (operator should keep polling) vs failure (operator should retry).
_IN_PROGRESS_STATUSES = {
    STATUS_PREVIEW_GENERATION_QUEUED,
    STATUS_PREVIEW_GENERATION_RUNNING,
}
_FAILURE_STATUSES = {
    STATUS_PREVIEW_GENERATION_FAILED,
    STATUS_PREVIEW_GENERATION_RETRY_REQUIRED,
}
_NON_SUCCESS_STATUSES = _IN_PROGRESS_STATUSES | _FAILURE_STATUSES

# Projection owns the stale guard: a queued/running attempt that has not
# finalized within this window is shown as retry_required, never as endless
# "generating". This protects against a background worker that died (process
# restart / OOM) without writing a terminal state.
RUNNING_STALE_SECONDS = 300
_STALE_RETRY_REASON = "首版预览生成超时，请重新生成预览。"

# Status mapping onto the existing 主视频结果 vocabulary.
_STATUS_LABEL = {
    STATUS_OPERATOR_USABLE: "运营可用 · 可交付",
    STATUS_TECHNICAL_PREVIEW: "技术预览 · 待审核",
    STATUS_NOT_GENERATED: "未生成",
    STATUS_PREVIEW_GENERATION_QUEUED: "主视频预览生成中",
    STATUS_PREVIEW_GENERATION_RUNNING: "主视频预览生成中",
    STATUS_PREVIEW_GENERATION_FAILED: "首版预览生成失败",
    STATUS_PREVIEW_GENERATION_RETRY_REQUIRED: "首版预览生成失败",
}

_FORBIDDEN_TOKENS = (
    "provider_url", "temporary_url", "download_url", "akool", "vendor",
    "model_id", "credit", "provider_task_id", "publish_url", "publish_status",
)

# P1 PR-1 — shot-level material replacement INTENT (no upload/storage here).
MATERIAL_INTENT_KEY = "matrix_script_material_replacement_intents"
MATERIAL_INTENT_REPLACE = "replace"
MATERIAL_INTENT_SUPPLEMENT = "supplement"
MATERIAL_INTENT_KEEP = "keep"
MATERIAL_INTENTS = (
    MATERIAL_INTENT_REPLACE,
    MATERIAL_INTENT_SUPPLEMENT,
    MATERIAL_INTENT_KEEP,
)
# A recorded replace/supplement intent makes the current material "dirty" — the
# operator must regenerate the preview. ``keep`` (or no record) is not dirty.
MATERIAL_DIRTY_INTENTS = (MATERIAL_INTENT_REPLACE, MATERIAL_INTENT_SUPPLEMENT)
MATERIAL_INTENT_NOTE_MAX = 280
_MATERIAL_INTENT_LABEL = {
    MATERIAL_INTENT_REPLACE: "已标记替换素材",
    MATERIAL_INTENT_SUPPLEMENT: "已标记补素材",
    MATERIAL_INTENT_KEEP: "使用当前素材",
}
# Operator-authored free text — excluded from the engineering leakage scan
# (the guard polices the projection's own identifiers, not operator prose).
_OPERATOR_NOTE_KEYS = ("intent_note", "operator_note")

# P1-2 PR-A — shot-level material ATTACHMENT handle. A replace/supplement intent
# can carry a concrete material reference (an existing asset handle, operator
# language only). This is a BINDING only: regeneration does NOT consume it yet
# (PR-B). Binding keeps the shot dirty ("已绑定，等待再次生成预览") and never
# overwrites the current main (V1), creates V2, changes the delivery candidate,
# or flips official_publish_ready.
MATERIAL_ATTACHMENT_SOURCE = "operator_attachment"
MATERIAL_KIND_VIDEO = "video"
MATERIAL_KIND_IMAGE = "image"
MATERIAL_KINDS = (MATERIAL_KIND_VIDEO, MATERIAL_KIND_IMAGE)
MATERIAL_NAME_MAX = 200
MATERIAL_REF_MAX = 512
_MATERIAL_KIND_LABEL = {
    MATERIAL_KIND_VIDEO: "视频",
    MATERIAL_KIND_IMAGE: "图片",
}
_MATERIAL_SOURCE_LABEL = {
    MATERIAL_ATTACHMENT_SOURCE: "运营补充素材",
}
MATERIAL_ATTACHED_STATUS_ZH = "已绑定，等待再次生成预览"
MATERIAL_UNATTACHED_STATUS_ZH = "待补素材"

# P1 PR-2 — regenerate preview versioning (V1 current main vs V2 candidate).
PREVIEW_VERSIONS_KEY = "matrix_script_preview_versions"
CURRENT_MAIN_VERSION_KEY = "matrix_script_current_main_version"
REGEN_STATUS_KEY = "matrix_script_preview_regeneration"
VERSION_MAIN = "V1"
VERSION_CANDIDATE = "V2"
ROLE_CANDIDATE = "candidate_preview"
ROLE_CURRENT_MAIN = "current_main"
_VERSION_LABEL = {VERSION_MAIN: "当前主视频", VERSION_CANDIDATE: "新预览"}

# P1-2 PR-B — V2 attached-material usage copy. Honest by construction: only claim
# the material was USED (bytes) when the renderer actually consumed it; otherwise
# state plainly that the preview was generated from the material REFERENCE.
MATERIAL_USAGE_CONSUMED_ZH = "已使用运营补充素材"
MATERIAL_USAGE_REFERENCE_ZH = "已绑定运营素材引用，当前预览以素材引用标记生成。"


def _truthy(v: Any) -> bool:
    return bool(v) and v not in ("", "false", "False", 0)


def _now(now: Optional[datetime]) -> datetime:
    return now or datetime.now(timezone.utc)


def _parse_iso(value: Any) -> Optional[datetime]:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _is_stale_attempt(initial: Mapping[str, Any], now: datetime) -> bool:
    """True when a queued/running attempt has outlived the stale window."""
    started = (
        _parse_iso(initial.get("started_at"))
        or _parse_iso(initial.get("queued_at"))
        or _parse_iso(initial.get("updated_at"))
    )
    if started is None:
        return False
    return (now - started).total_seconds() > RUNNING_STALE_SECONDS


def _project_initial_status(initial: Mapping[str, Any], now: datetime) -> str:
    """Apply the stale guard: a stale in-progress attempt projects to retry_required."""
    status = str(initial.get("status") or "")
    if status in _IN_PROGRESS_STATUSES and _is_stale_attempt(initial, now):
        return STATUS_PREVIEW_GENERATION_RETRY_REQUIRED
    return status


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
    if isinstance(initial, Mapping) and str(initial.get("status") or "") in _NON_SUCCESS_STATUSES:
        return initial
    return None


def _build_main_result(result: Optional[Mapping[str, Any]], now: datetime) -> Dict[str, Any]:
    if not result:
        return {
            "status": STATUS_NOT_GENERATED,
            "status_label_zh": _STATUS_LABEL[STATUS_NOT_GENERATED],
            "poll": False,
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
    if str(result.get("status") or "") in _NON_SUCCESS_STATUSES:
        status = _project_initial_status(result, now)
        in_progress = status in _IN_PROGRESS_STATUSES
        if status == STATUS_PREVIEW_GENERATION_RETRY_REQUIRED and _is_stale_attempt(result, now):
            blocked_reason = _STALE_RETRY_REASON
        elif status in _FAILURE_STATUSES:
            blocked_reason = result.get("error_summary") or result.get("error") or _STALE_RETRY_REASON
        else:
            blocked_reason = None
        return {
            "status": status,
            "status_label_zh": _STATUS_LABEL[status],
            "poll": in_progress,
            "operator_usable": False,
            "technical_preview": False,
            "visual_semantic_match": None,
            "shot_match_count": 0,
            "shot_count": plan_mod.shot_count(),
            "real_visual_count": 0,
            "delivery_candidate": False,
            "official_publish_ready": False,
            "blocked_reason": blocked_reason,
            "preview_url": None,
        }
    operator_usable = _truthy(result.get("operator_usable"))
    technical_preview = _truthy(result.get("technical_preview")) or not operator_usable
    status = STATUS_OPERATOR_USABLE if operator_usable else STATUS_TECHNICAL_PREVIEW
    return {
        "status": status,
        "status_label_zh": _STATUS_LABEL[status],
        "poll": False,
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


def _material_intents(task: Mapping[str, Any]) -> Dict[str, Mapping[str, Any]]:
    config = task.get("config") if isinstance(task, Mapping) else None
    raw = config.get(MATERIAL_INTENT_KEY) if isinstance(config, Mapping) else None
    if not isinstance(raw, Mapping):
        return {}
    out: Dict[str, Mapping[str, Any]] = {}
    for shot_id, entry in raw.items():
        if isinstance(entry, Mapping) and entry.get("intent") in MATERIAL_INTENTS:
            out[str(shot_id)] = entry
    return out


def _project_shot_attachment(
    entry: Mapping[str, Any], intent_dirty: bool
) -> Dict[str, Any]:
    """Operator-safe projection of a shot's material ATTACHMENT handle (PR-A).

    A binding requires both a ``material_ref`` and a ``material_name``. The
    regeneration loop does not consume this yet — it is shown so the operator
    can confirm what is bound before the next ``再次生成预览``. When nothing is
    bound but the shot is dirty (replace/supplement), the operator still needs
    material → 待补素材.
    """
    material_ref = entry.get("material_ref")
    material_name = entry.get("material_name")
    attached = bool(material_ref) and bool(material_name)
    if not attached:
        return {
            "material_attached": False,
            "material_ref": None,
            "material_name": None,
            "material_kind": None,
            "material_kind_label_zh": None,
            "thumbnail_url": None,
            "material_source": None,
            "material_source_label_zh": None,
            "material_status_zh": MATERIAL_UNATTACHED_STATUS_ZH if intent_dirty else None,
        }
    kind = str(entry.get("material_kind") or "")
    if kind not in MATERIAL_KINDS:
        kind = MATERIAL_KIND_VIDEO
    source = str(entry.get("material_source") or MATERIAL_ATTACHMENT_SOURCE)
    thumb = entry.get("thumbnail_url")
    return {
        "material_attached": True,
        "material_ref": str(material_ref)[:MATERIAL_REF_MAX],
        "material_name": str(material_name)[:MATERIAL_NAME_MAX],
        "material_kind": kind,
        "material_kind_label_zh": _MATERIAL_KIND_LABEL[kind],
        "thumbnail_url": str(thumb)[:MATERIAL_REF_MAX] if thumb else None,
        "material_source": source,
        "material_source_label_zh": _MATERIAL_SOURCE_LABEL.get(source, "运营补充素材"),
        "material_status_zh": MATERIAL_ATTACHED_STATUS_ZH,
    }


def _build_shots(has_result: bool, intents: Mapping[str, Mapping[str, Any]]) -> List[Dict[str, Any]]:
    cards: List[Dict[str, Any]] = []
    for shot in plan_mod.TOMATO_SHOTS:
        entry = intents.get(shot.shot_id) or {}
        intent = str(entry.get("intent") or MATERIAL_INTENT_KEEP)
        if intent not in MATERIAL_INTENTS:
            intent = MATERIAL_INTENT_KEEP
        note = entry.get("operator_note")
        intent_dirty = intent in MATERIAL_DIRTY_INTENTS
        card = {
            "shot_id": shot.shot_id,
            "order": shot.order,
            "title": shot.title_zh,
            "asset_name": shot.asset_filename,
            "source": shot.source,
            "semantic_status": "pass" if shot.real_visual else "partial",
            "included_in_current_video": bool(has_result),
            "intent": intent,
            "intent_label_zh": _MATERIAL_INTENT_LABEL[intent],
            "intent_dirty": intent_dirty,
            "intent_note": str(note)[:MATERIAL_INTENT_NOTE_MAX] if note else None,
            "intent_updated_at": entry.get("updated_at"),
        }
        card.update(_project_shot_attachment(entry, intent_dirty))
        cards.append(card)
    return cards


def _scrub_operator_notes(value: Any) -> Any:
    """Deep copy with operator-authored note fields blanked, for the leakage scan."""
    if isinstance(value, Mapping):
        return {
            k: ("" if k in _OPERATOR_NOTE_KEYS else _scrub_operator_notes(v))
            for k, v in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_scrub_operator_notes(v) for v in value]
    return value


def _project_regeneration(task: Mapping[str, Any], now: datetime) -> Dict[str, Any]:
    config = task.get("config") if isinstance(task, Mapping) else None
    raw = config.get(REGEN_STATUS_KEY) if isinstance(config, Mapping) else None
    if not isinstance(raw, Mapping) or not raw.get("status"):
        return {"status": None, "poll": False, "blocked_reason": None}
    status = _project_initial_status(raw, now)
    in_progress = status in _IN_PROGRESS_STATUSES
    if status in _FAILURE_STATUSES:
        blocked = raw.get("error_summary") or raw.get("error") or _STALE_RETRY_REASON
    else:
        blocked = None
    return {"status": status, "poll": in_progress, "blocked_reason": blocked}


def _shot_label(shot_id: str) -> str:
    """"shot04" -> "Shot 04" for operator display; fall back to the raw id."""
    sid = str(shot_id)
    if sid.startswith("shot") and sid[4:].isdigit():
        return "Shot %02d" % int(sid[4:])
    return sid


def _project_based_on_assets(raw: Any) -> List[Dict[str, Any]]:
    """Operator-safe projection of a V2 candidate's attached-material list."""
    out: List[Dict[str, Any]] = []
    if not isinstance(raw, (list, tuple)):
        return out
    for asset in raw:
        if not isinstance(asset, Mapping):
            continue
        shot_id = str(asset.get("shot_id") or "")
        kind = str(asset.get("material_kind") or "")
        out.append({
            "shot_id": shot_id,
            "shot_label_zh": _shot_label(shot_id),
            "material_name": str(asset.get("material_name") or ""),
            "material_kind": kind,
            "material_kind_label_zh": _MATERIAL_KIND_LABEL.get(kind, kind),
        })
    return out


def _build_preview_versions(
    task: Mapping[str, Any], main_result: Mapping[str, Any]
) -> Dict[str, Any]:
    """Operator-safe V1/V2 version projection (no payload internals exposed)."""
    config = task.get("config") if isinstance(task, Mapping) else None
    raw_versions = config.get(PREVIEW_VERSIONS_KEY) if isinstance(config, Mapping) else None
    raw_versions = raw_versions if isinstance(raw_versions, Mapping) else {}
    current_main_version = (
        config.get(CURRENT_MAIN_VERSION_KEY) if isinstance(config, Mapping) else None
    )

    versions: List[Dict[str, Any]] = []
    main_preview_url = main_result.get("preview_url")
    if main_preview_url:
        cmv = str(current_main_version or VERSION_MAIN)
        versions.append({
            "version": cmv,
            "role": ROLE_CURRENT_MAIN,
            "label_zh": _VERSION_LABEL.get(cmv, _VERSION_LABEL[VERSION_MAIN]),
            "preview_url": main_preview_url,
        })

    new_preview: Optional[Dict[str, Any]] = None
    candidate = raw_versions.get(VERSION_CANDIDATE)
    if isinstance(candidate, Mapping) and candidate.get("role") == ROLE_CANDIDATE:
        based_on = candidate.get("based_on_intents")
        bytes_consumed = bool(candidate.get("material_bytes_consumed"))
        new_preview = {
            "version": VERSION_CANDIDATE,
            "role": ROLE_CANDIDATE,
            "label_zh": _VERSION_LABEL[VERSION_CANDIDATE],
            "preview_url": candidate.get("preview_url"),
            "based_on_intents": list(based_on) if isinstance(based_on, (list, tuple)) else [],
            "source": candidate.get("source"),
            # P1-2 PR-B: the attached material handles this V2 was regenerated
            # from. Operator-safe labels only — never bytes, never a real
            # pixel-replacement claim unless the renderer actually consumed bytes.
            "based_on_assets": _project_based_on_assets(candidate.get("based_on_assets")),
            "material_bytes_consumed": bytes_consumed,
            "material_usage_note_zh": (
                MATERIAL_USAGE_CONSUMED_ZH if bytes_consumed
                else MATERIAL_USAGE_REFERENCE_ZH
            ),
        }
        versions.append(new_preview)

    return {
        "preview_versions": versions,
        "new_preview": new_preview,
        "has_candidate_preview": new_preview is not None,
        "current_main_version": (
            str(current_main_version) if current_main_version
            else (VERSION_MAIN if main_preview_url else None)
        ),
    }


def _assert_clean(view: Mapping[str, Any]) -> None:
    # Scan the projection's own fields; operator free-text notes are excluded so
    # operator prose can never crash the Workbench render.
    blob = str(_scrub_operator_notes(view)).lower()
    hits = [t for t in _FORBIDDEN_TOKENS if t in blob]
    if hits:
        raise ValueError(f"operator overlay leaks forbidden tokens: {hits}")


def build_matrix_script_operator_workbench_view(
    task: Mapping[str, Any],
    *,
    result: Optional[Mapping[str, Any]] = None,
    env: Optional[Mapping[str, str]] = None,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Build the PR-A acceptance OVERLAY for the existing Workbench sections.

    ``now`` is injectable so the stale-guard projection is deterministically
    testable; it defaults to the current UTC time.
    """
    if not isinstance(task, Mapping):
        task = {}
    clock = _now(now)
    resolved = _resolve_result(task, result)
    has_result = (
        resolved is not None
        and str(resolved.get("status") or "") not in _NON_SUCCESS_STATUSES
    )
    main_result = _build_main_result(resolved, clock)
    intents = _material_intents(task)
    shots = _build_shots(has_result, intents)
    dirty_shots = [s["shot_id"] for s in shots if s["intent_dirty"]]
    material_changed = bool(dirty_shots)
    version_view = _build_preview_versions(task, main_result)
    view: Dict[str, Any] = {
        "is_matrix_script": True,
        "has_pr_a_result": has_result,
        "main_result": main_result,
        "shots": shots,
        # P1 PR-1: material replacement intent is dirty-state only. It must NOT
        # touch the current main video, delivery candidate, or publish readiness.
        "material_changed": material_changed,
        "dirty_shots": dirty_shots,
        "dirty_shot_count": len(dirty_shots),
        "material_intent_endpoint": "/api/matrix-script/{task_id}/material-replacement-intent",
        # P1-2 PR-A: bind a concrete material handle to a shot intent. Binding only —
        # regeneration does not consume it yet (PR-B).
        "material_attachment_endpoint": "/api/matrix-script/{task_id}/shot-material-attachment",
        # P1 PR-2: regenerate preview versioning. The current main (V1) is the
        # staged candidate; a V2 candidate (if any) is shown alongside without
        # replacing V1 until confirmed.
        "regeneration": _project_regeneration(task, clock),
        "regenerate_endpoint": "/api/matrix-script/{task_id}/regenerate-preview",
        "preview_version_confirm_endpoint": "/api/matrix-script/{task_id}/preview-version/confirm",
        "preview_version_discard_endpoint": "/api/matrix-script/{task_id}/preview-version/discard",
        "preview_versions": version_view["preview_versions"],
        "new_preview": version_view["new_preview"],
        "has_candidate_preview": version_view["has_candidate_preview"],
        "current_main_version": version_view["current_main_version"],
        "delivery": {
            "delivery_candidate": main_result["delivery_candidate"],
            "preview_url": main_result["preview_url"],
            "official_publish_ready": False,
        },
        "generate_endpoint": "/api/matrix-script/{task_id}/tomato-real-result",
    }
    _assert_clean(view)
    return view
