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
    MATERIAL_INTENT_SUPPLEMENT: "已标记补充素材",
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
# P1-3 PR-C — uploaded material carries resolvable BYTES (a storage fact); this
# is distinct from material_bytes_consumed (a regeneration fact, still false).
MATERIAL_UPLOAD_SOURCE = "operator_upload"
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
    MATERIAL_UPLOAD_SOURCE: "运营上传素材",
}
MATERIAL_ATTACHED_STATUS_ZH = "已绑定，等待再次生成预览"
MATERIAL_UPLOADED_STATUS_ZH = "已上传，等待再次生成预览"
MATERIAL_UNATTACHED_STATUS_ZH = "待上传素材"

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
# P1-3 PR-D — when the renderer actually consumed UPLOADED material bytes
# (operator_upload source), the copy is explicit that a new preview was made FROM
# the uploaded material. Distinct from the generic consumed copy above.
MATERIAL_USAGE_UPLOAD_CONSUMED_ZH = "已使用运营上传素材生成新预览"

# ---- Operator Process Observability (this PR) ------------------------------ #
# A single derived, operator-safe process state for the whole Matrix Script
# generation flow. It is a PROJECTION over already-existing facts (intents,
# attachments, regeneration lifecycle, candidate version) — it adds no new
# truth, no storage, no route behaviour. Drives A区 copy + the data-process-state
# DOM marker so operations can read "where in the process am I" at a glance.
PROCESS_NOT_GENERATED = "not_generated"
PROCESS_STABLE = "stable"
PROCESS_INTENT_ONLY = "intent_only"
PROCESS_MATERIAL_READY = "material_ready"
PROCESS_GENERATION_RUNNING = "generation_running"
PROCESS_CANDIDATE_READY = "candidate_ready"
PROCESS_FAILED = "failed"
_PROCESS_STATE_LABEL = {
    PROCESS_NOT_GENERATED: "未生成",
    PROCESS_STABLE: "当前主视频可用，无待生成的素材变更",
    PROCESS_INTENT_ONLY: "已记录素材调整意图，待上传/绑定素材",
    PROCESS_MATERIAL_READY: "素材已就绪，待再次生成预览",
    PROCESS_GENERATION_RUNNING: "正在生成新预览",
    PROCESS_CANDIDATE_READY: "V2 新预览待运营确认",
    PROCESS_FAILED: "生成失败，请重试",
}

# Guided Operator Workflow PR-1 (A区 state narration). Per Gate Spec §3.A the A区
# state must read in operator language as 当前主视频 / 当前状态(现状) / 下一步.
# These two maps are the normative 现状 + 下一步 columns of the §3.A table,
# projected over the SAME derived process_state — no new truth, no new producer.
# The short 当前状态 vocabulary matches the operator list in the PR-1 brief
# (稳定 / 已记录调整意图 / 素材已就绪 / 正在生成 V2 / V2 待确认 / 生成失败).
_PROCESS_STATE_STATUS_ZH = {
    PROCESS_NOT_GENERATED: "未生成",
    PROCESS_STABLE: "稳定",
    PROCESS_INTENT_ONLY: "已记录调整意图",
    PROCESS_MATERIAL_READY: "素材已就绪",
    PROCESS_GENERATION_RUNNING: "正在生成 V2",
    PROCESS_CANDIDATE_READY: "V2 待确认",
    PROCESS_FAILED: "生成失败",
}
# 下一步 is phrased as a zone-agnostic operator action so it stays correct in the
# CURRENT layout (regenerate lives in the main-video area, upload in the material
# area); the future C区 re-order (PR-3/PR-4) does not change these action words.
_PROCESS_STATE_NEXT_STEP_ZH = {
    PROCESS_NOT_GENERATED: "确认素材与配乐后，生成主视频预览",
    PROCESS_STABLE: "检查镜头，或进入交付",
    PROCESS_INTENT_ONLY: "先上传这个镜头的素材",
    PROCESS_MATERIAL_READY: "返回主视频区，点击“再次生成预览”",
    PROCESS_GENERATION_RUNNING: "稍候，本页会自动更新；不影响当前主视频",
    PROCESS_CANDIDATE_READY: "对比 V1 / V2，确认主版本或丢弃",
    PROCESS_FAILED: "当前主视频未受影响，可点击“再次生成预览”重试",
}

# Per-shot visual source — where the pixels in the current main video came from.
VISUAL_SOURCE_ORIGINAL = "original_generated"
VISUAL_SOURCE_UPLOAD = "operator_upload"
VISUAL_SOURCE_ATTACHMENT = "operator_attachment_ref"
VISUAL_SOURCE_REUSE = "semantic_reuse"
VISUAL_SOURCE_FALLBACK = "fallback_placeholder"
_VISUAL_SOURCE_LABEL = {
    VISUAL_SOURCE_ORIGINAL: "原始生成素材",
    VISUAL_SOURCE_UPLOAD: "运营上传素材",
    VISUAL_SOURCE_ATTACHMENT: "运营绑定素材引用",
    VISUAL_SOURCE_REUSE: "复用素材",
    VISUAL_SOURCE_FALLBACK: "降级占位素材",
}
# Plan-level source values from the fixed shot plan.
PLAN_SOURCE_REAL = "local_real_asset"
PLAN_SOURCE_REUSE = "fallback_semantic_reuse"

# Per-shot next-available-action (operator language only).
NEXT_ACTION_NONE_ZH = "无需操作"
NEXT_ACTION_UPLOAD_ZH = "上传/绑定素材"
NEXT_ACTION_REGENERATE_ZH = "再次生成预览"
NEXT_ACTION_CONFIRM_V2_ZH = "确认 V2 为主版本"

# Guided Operator Workflow PR-2 (B区, Gate Spec §3.B). Operator-language copy,
# all projection over existing signals — no new producer, no new truth.
# R-SHOT-REASON (§3.B.2): why a shot is suggested for handling. Trigger is the
# existing signal `source == fallback_semantic_reuse` (no real visual yet); the
# per-shot phrase reproduces the established operator copy (was inline in the
# template) so the operator is told WHY, not only WHAT.
SHOT_REASON_PREFIX_ZH = "建议处理原因："
_SHOT_REUSE_REASON_ZH = {
    "shot04": "当前为复用素材，建议补充真实品尝素材。",
    "shot05": "当前为复用素材，建议补充递向镜头素材。",
}
_SHOT_REUSE_REASON_DEFAULT_ZH = "当前为复用素材，建议补充真实素材。"
# R-UPLOAD-HANDOFF (§3.B.2): after a shot's material is attached/uploaded but no
# V2 candidate exists yet, the next step is visible right by the upload area.
UPLOAD_HANDOFF_ZH = "下一步：素材已上传。请点击“再次生成预览”生成 V2。"

# Per-shot observability status copy (§5 of the observability spec).
SHOT_OBS_AWAIT_UPLOAD_ZH = "已选择处理方式，等待上传素材或选择素材来源。"
SHOT_OBS_READY_ZH = "素材已就绪，等待再次生成预览。"
SHOT_OBS_ENTERED_V2_ZH = "已进入 V2 新预览。"
SHOT_OBS_UPLOADED_NOT_CONSUMED_ZH = "已上传，但尚未进入新预览。"
SHOT_ADJUST_OUTCOME_ZH = "上传素材后，再回到主视频区点击“再次生成预览”。"

# A区 process-state copy (§4 of the observability spec).
A_STABLE_TITLE_ZH = "当前没有需要再生成的素材变更"
A_STABLE_BODY_ZH = "可继续检查素材或进入交付。"
A_INTENT_ONLY_TITLE_ZH = "已记录素材调整意图"
A_INTENT_ONLY_BODY_ZH = "请先上传/绑定素材，或选择 AI 生成素材后，再生成预览。"
A_MATERIAL_READY_TITLE_ZH = "素材已就绪，需要再次生成预览"
A_MATERIAL_READY_BODY_ZH = "返回主视频区点击“再次生成预览”，新预览为候选版本，确认后才会成为当前主视频。"

# Current-main generation source labels (§3A).
GEN_SOURCE_INITIAL_ZH = "首版预览"
GEN_SOURCE_REGENERATED_ZH = "再生成预览"


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
    material → 待上传素材.
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
            "preview_url": None,
            "material_source": None,
            "material_source_label_zh": None,
            "storage_scope": None,
            "bytes_resolvable": False,
            "material_status_zh": MATERIAL_UNATTACHED_STATUS_ZH if intent_dirty else None,
        }
    kind = str(entry.get("material_kind") or "")
    if kind not in MATERIAL_KINDS:
        kind = MATERIAL_KIND_VIDEO
    source = str(entry.get("material_source") or MATERIAL_ATTACHMENT_SOURCE)
    uploaded = source == MATERIAL_UPLOAD_SOURCE
    # An uploaded material has resolvable bytes (storage fact); a bare reference
    # does not. NB: bytes_resolvable != material_bytes_consumed (regen fact).
    bytes_resolvable = bool(entry.get("bytes_resolvable")) if uploaded else False
    thumb = entry.get("thumbnail_url") or (entry.get("preview_url") if uploaded else None)
    preview = entry.get("preview_url") if uploaded else None
    return {
        "material_attached": True,
        "material_ref": str(material_ref)[:MATERIAL_REF_MAX],
        "material_name": str(material_name)[:MATERIAL_NAME_MAX],
        "material_kind": kind,
        "material_kind_label_zh": _MATERIAL_KIND_LABEL[kind],
        "thumbnail_url": str(thumb)[:MATERIAL_REF_MAX] if thumb else None,
        "preview_url": str(preview)[:MATERIAL_REF_MAX] if preview else None,
        "material_source": source,
        "material_source_label_zh": _MATERIAL_SOURCE_LABEL.get(source, "运营补充素材"),
        "storage_scope": str(entry.get("storage_scope")) if uploaded and entry.get("storage_scope") else None,
        "bytes_resolvable": bytes_resolvable,
        "material_status_zh": (
            MATERIAL_UPLOADED_STATUS_ZH if uploaded else MATERIAL_ATTACHED_STATUS_ZH
        ),
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
        # R-SHOT-REASON (PR-2 §3.B.2): reuse-source shots are suggested for
        # handling; show WHY in operator language. Projection over `source`.
        suggested = shot.source == PLAN_SOURCE_REUSE
        card["suggested_for_handling"] = suggested
        card["suggestion_reason_zh"] = (
            SHOT_REASON_PREFIX_ZH
            + _SHOT_REUSE_REASON_ZH.get(shot.shot_id, _SHOT_REUSE_REASON_DEFAULT_ZH)
        ) if suggested else None
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


def _project_consumed_materials(raw: Any) -> List[Dict[str, Any]]:
    """Operator-safe projection of the materials whose bytes V2 actually consumed.

    Records shot_id / label / name / kind + the safe internal ``msmaterial://``
    handle. NEVER a local_path / provider / publish URL.
    """
    out: List[Dict[str, Any]] = []
    if not isinstance(raw, (list, tuple)):
        return out
    for item in raw:
        if not isinstance(item, Mapping):
            continue
        shot_id = str(item.get("shot_id") or "")
        kind = str(item.get("material_kind") or "")
        ref = str(item.get("material_ref") or "")
        out.append({
            "shot_id": shot_id,
            "shot_label_zh": _shot_label(shot_id),
            "material_name": str(item.get("material_name") or ""),
            "material_kind": kind,
            "material_kind_label_zh": _MATERIAL_KIND_LABEL.get(kind, kind),
            "material_ref": ref[:MATERIAL_REF_MAX] if ref else None,
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
        consumed_materials = _project_consumed_materials(candidate.get("consumed_materials"))
        # P1-3 PR-D: an UPLOADED material's bytes were actually consumed → explicit
        # upload copy; a generic (non-upload) consumed flag keeps the PR-B copy;
        # nothing consumed → honest reference-label copy.
        uploaded_consumed = bytes_consumed and any(
            isinstance(m, Mapping)
            and str(m.get("material_source")) == MATERIAL_UPLOAD_SOURCE
            for m in (candidate.get("consumed_materials") or [])
        )
        if uploaded_consumed:
            usage_note = MATERIAL_USAGE_UPLOAD_CONSUMED_ZH
        elif bytes_consumed:
            usage_note = MATERIAL_USAGE_CONSUMED_ZH
        else:
            usage_note = MATERIAL_USAGE_REFERENCE_ZH
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
            # P1-3 PR-D: the materials whose bytes were actually consumed.
            "consumed_materials": consumed_materials,
            "material_usage_note_zh": usage_note,
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


def _derive_visual_source(card: Mapping[str, Any]) -> str:
    """Where the current pixels for this shot come from (operator-safe)."""
    if card.get("material_attached"):
        if card.get("material_source") == MATERIAL_UPLOAD_SOURCE:
            return VISUAL_SOURCE_UPLOAD
        return VISUAL_SOURCE_ATTACHMENT
    src = str(card.get("source") or "")
    if src == PLAN_SOURCE_REAL:
        return VISUAL_SOURCE_ORIGINAL
    if src == PLAN_SOURCE_REUSE:
        return VISUAL_SOURCE_REUSE
    return VISUAL_SOURCE_FALLBACK


def _enrich_shot_observability(
    shots: List[Dict[str, Any]],
    version_view: Mapping[str, Any],
) -> None:
    """Second pass: annotate each shot card with process-observability fields.

    Cross-references the V2 candidate so each shot can state whether its material
    entered the candidate and whether bytes were actually consumed. Pure
    projection — mutates the already-built cards in place, adds no new truth.
    """
    new_preview = version_view.get("new_preview") or {}
    has_candidate = bool(version_view.get("has_candidate_preview"))
    consumed_ids = {
        str(m.get("shot_id"))
        for m in (new_preview.get("consumed_materials") or [])
        if isinstance(m, Mapping) and m.get("shot_id")
    }
    based_on_ids = {
        str(a.get("shot_id"))
        for a in (new_preview.get("based_on_assets") or [])
        if isinstance(a, Mapping) and a.get("shot_id")
    }
    for card in shots:
        shot_id = str(card.get("shot_id"))
        attached = bool(card.get("material_attached"))
        dirty = bool(card.get("intent_dirty"))
        entered_v2 = shot_id in consumed_ids or shot_id in based_on_ids
        bytes_for_shot = shot_id in consumed_ids
        visual_source = _derive_visual_source(card)

        if has_candidate:
            next_action = NEXT_ACTION_CONFIRM_V2_ZH
        elif not dirty:
            next_action = NEXT_ACTION_NONE_ZH
        elif not attached:
            next_action = NEXT_ACTION_UPLOAD_ZH
        else:
            next_action = NEXT_ACTION_REGENERATE_ZH

        if entered_v2:
            obs_status = SHOT_OBS_ENTERED_V2_ZH
        elif attached and has_candidate:
            obs_status = SHOT_OBS_UPLOADED_NOT_CONSUMED_ZH
        elif attached:
            obs_status = SHOT_OBS_READY_ZH
        elif dirty:
            obs_status = SHOT_OBS_AWAIT_UPLOAD_ZH
        else:
            obs_status = None

        card.update({
            "visual_source": visual_source,
            "visual_source_label_zh": _VISUAL_SOURCE_LABEL[visual_source],
            "entered_current_main": bool(card.get("included_in_current_video")),
            "entered_v2_candidate": entered_v2,
            "bytes_consumed_for_shot": bytes_for_shot,
            "next_action_zh": next_action,
            "shot_observability_status_zh": obs_status,
            "shot_adjust_outcome_zh": SHOT_ADJUST_OUTCOME_ZH if dirty else None,
            # R-UPLOAD-HANDOFF (PR-2 §3.B.2): material attached but not yet in a V2
            # candidate → the next step (regenerate) is shown right by the upload.
            "upload_handoff_zh": (
                UPLOAD_HANDOFF_ZH if (attached and not has_candidate) else None
            ),
        })


def _derive_process_state(
    main_result: Mapping[str, Any],
    shots: List[Dict[str, Any]],
    regeneration: Mapping[str, Any],
    version_view: Mapping[str, Any],
) -> str:
    """Single operator-safe process state for the whole generation flow."""
    main_status = str(main_result.get("status") or "")
    regen_status = str(regeneration.get("status") or "")
    if main_result.get("poll") or regeneration.get("poll"):
        return PROCESS_GENERATION_RUNNING
    if main_status in _FAILURE_STATUSES or regen_status in _FAILURE_STATUSES:
        return PROCESS_FAILED
    if version_view.get("has_candidate_preview"):
        return PROCESS_CANDIDATE_READY
    dirty = [s for s in shots if s.get("intent_dirty")]
    if dirty:
        if any(s.get("material_attached") for s in dirty):
            return PROCESS_MATERIAL_READY
        return PROCESS_INTENT_ONLY
    if main_result.get("operator_usable") or main_result.get("preview_url"):
        return PROCESS_STABLE
    return PROCESS_NOT_GENERATED


def _build_process_narration(
    process_state: str,
    version_view: Mapping[str, Any],
    main_result: Mapping[str, Any],
) -> Dict[str, Any]:
    """A区 operator-language state narration (Gate Spec §3.A, PR-1).

    Projects the derived process_state into three operator-safe fields —
    当前主视频 (version) / 当前状态 (现状) / 下一步 — with no raw enum, no backend
    field, no new truth. ``current_main_version`` is None before any preview
    exists so the template omits the 主视频 line rather than asserting a version.
    """
    has_preview = bool(main_result.get("preview_url"))
    current_version = version_view.get("current_main_version") if has_preview else None
    return {
        "current_main_version": current_version,
        "current_main_version_label_zh": (
            _VERSION_LABEL.get(current_version, "") if current_version else ""
        ),
        "status_zh": _PROCESS_STATE_STATUS_ZH[process_state],
        "next_step_zh": _PROCESS_STATE_NEXT_STEP_ZH[process_state],
    }


def _build_generation_facts(
    main_result: Mapping[str, Any],
    shots: List[Dict[str, Any]],
    version_view: Mapping[str, Any],
    missing_material_count: int,
) -> Dict[str, Any]:
    """Operator-safe input/generation facts for the current main (V1/V2)."""
    current_version = version_view.get("current_main_version")
    has_preview = bool(main_result.get("preview_url"))
    current_main: Optional[Dict[str, Any]] = None
    if has_preview:
        source_label = (
            GEN_SOURCE_REGENERATED_ZH
            if current_version == VERSION_CANDIDATE
            else GEN_SOURCE_INITIAL_ZH
        )
        current_main = {
            "version": current_version or VERSION_MAIN,
            "version_label_zh": _VERSION_LABEL.get(
                current_version or VERSION_MAIN, _VERSION_LABEL[VERSION_MAIN]
            ),
            "source_label_zh": source_label,
            "shot_match_count": int(main_result.get("shot_match_count", 0) or 0),
            "real_visual_count": int(main_result.get("real_visual_count", 0) or 0),
            "missing_material_count": int(missing_material_count),
            "official_publish_ready": False,
        }
    return {"current_main": current_main, "candidate": version_view.get("new_preview")}


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
    regeneration = _project_regeneration(task, clock)
    # Process observability (this PR): enrich shots with per-shot trace fields,
    # then derive the single flow-level process state + current-main facts.
    _enrich_shot_observability(shots, version_view)
    missing_material_count = sum(
        1 for s in shots
        if not s.get("material_attached") and s.get("source") == PLAN_SOURCE_REUSE
    )
    process_state = _derive_process_state(
        main_result, shots, regeneration, version_view
    )
    process_narration = _build_process_narration(
        process_state, version_view, main_result
    )
    generation_facts = _build_generation_facts(
        main_result, shots, version_view, missing_material_count
    )
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
        # P1-3 PR-C: upload a material file → resolvable bytes (storage fact).
        # Regeneration still does not consume the bytes (PR-D).
        "material_upload_endpoint": "/api/matrix-script/{task_id}/shot-material-upload",
        # P1 PR-2: regenerate preview versioning. The current main (V1) is the
        # staged candidate; a V2 candidate (if any) is shown alongside without
        # replacing V1 until confirmed.
        "regeneration": regeneration,
        # Process observability (this PR): operator-safe derived process state +
        # current-main generation facts + missing-material count. Projection only.
        "process_state": process_state,
        "process_state_label_zh": _PROCESS_STATE_LABEL[process_state],
        # Guided Operator Workflow PR-1: A区 operator-language state narration
        # (当前主视频 / 当前状态 / 下一步). Projection only; raw process_state stays
        # a diagnosis-only data attribute, never primary operator copy.
        "process_narration": process_narration,
        "generation_facts": generation_facts,
        "missing_material_count": missing_material_count,
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
