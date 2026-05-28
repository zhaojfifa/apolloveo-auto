"""Matrix Script Workbench · 主视频结果 read-view (PR-2A · redesign 2026-05-28).

Pure presentation-layer projection. Derives the operator-facing "main video
result" surface that anchors the top of the Workbench page (Mission §B.1).

The derivation is read-only:

- Single source for publishability: ``compute_publish_readiness``
  (unified producer, RC-A7 rule preserved). No second producer.
- Per-variation media status: ``preview_compare_view.variations[]``
  ``preview_status_code`` (closed set ``{current_fresh, historical,
  unresolved, unknown}``).
- Recommended variant: ``recommended_action_view.recommended_variant``
  (RC-R4 single source).
- Operator-confirmed main version: detected by reading the existing
  closure event log for ``operator_note`` records whose
  ``operator_publish_notes`` text contains the structured prefix
  ``[main-version-confirmed]`` (Mission product-decision #1 —
  approved 2026-05-28; "Use structured operator_note. Do not widen
  closed enums."). NO ``RECORD_KINDS`` widening; NO new event_kind;
  NO contract change.

Action enablement rules (operator-language only, no English IDs):

- ``生成主视频`` / ``重新生成`` — always rendered, DISABLED with
  operator-language tooltip "成片生成能力接入后启用" until the
  generation worker lands (Capability Expansion Wave; out of this
  wave's scope).
- ``确认为主版本`` — ENABLED iff there is ``current_fresh`` media on
  at least one variation AND no operator-confirmed main exists yet.
  When clicked, writes an ``operator_note`` event via the existing
  ``POST /api/matrix-script/closures/{task_id}/events`` endpoint with
  ``event_kind=operator_note`` and structured note text. NO new
  endpoint, NO closed-enum widening.
- ``前往交付页面`` — always ENABLED; links to
  ``/tasks/{task_id}/publish``.

State pill (Mission §B.1 closed 4-value set, operator-language only):

  未生成 / 生成中 / 待审核 / 可交付

Mapping:

- ``可交付``       ← ``publish_readiness.publishable == True``
- ``待审核``       ← any variation has ``current_fresh`` AND not yet
                     publishable AND no confirmed main
- ``生成中``       ← (today: never True — no async generation backend)
- ``未生成``       ← default fallback

Empty-state message (no ``current_fresh`` on any variation; the
universal state today):

    "当前尚未生成主视频。已完成脚本结构与生成方案准备，成片生成能力接入后将在这里展示视频结果。"

Verbatim from Mission §B.1. RC-R8 no-fake-output discipline preserved:
NEVER a fake URL, NEVER a fabricated `final_video` reference, NEVER a
placeholder media player widget. Operator sees an honest "not generated
yet" message when the artifact is absent.

Hard discipline (binding under the 2026-05-28 redesign wave):

- No vendor / model / provider / engine identifier in the return value
  (validator R3).
- No raw closed-enum value in the operator-facing output (e.g.
  ``head_reason`` enum literal NEVER appears; only its operator-language
  label).
- No raw ``cell_id`` / ``script_slot_ref`` / ``content://`` handle in
  the operator-facing output.
- Non-Matrix-Script tasks return ``{}`` so the caller can attach
  unconditionally.
- The opaque main video URL (if any) is NEVER echoed back; even
  ``current_fresh`` resolved media stays inside the preview projection
  as an opaque artifact reference for the template to interpret.

Authority:
- User-approved design plan, 2026-05-28 §6.2 (Block ① 主视频结果 detailed spec).
- Mission §B.1 (Workbench layout 主视频结果 binding-and-exhaustive fields).
- Closure schema preserved per
  ``docs/contracts/matrix_script/publish_feedback_closure_contract_v1.md``.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional

# Closed operator-language state values per Mission §B.1.
STATE_NOT_GENERATED = "not_generated"
STATE_GENERATING = "generating"
STATE_AWAITING_REVIEW = "awaiting_review"
STATE_DELIVERABLE = "deliverable"

STATE_LABELS_ZH = {
    STATE_NOT_GENERATED: "未生成",
    STATE_GENERATING: "生成中",
    STATE_AWAITING_REVIEW: "待审核",
    STATE_DELIVERABLE: "可交付",
}

# Closed action identifiers (template uses these as data-action-id markers).
ACTION_GENERATE = "generate_main_video"
ACTION_REGENERATE = "regenerate"
ACTION_CONFIRM_MAIN = "confirm_main_version"
ACTION_GO_TO_DELIVERY = "go_to_delivery"

ACTION_LABELS_ZH = {
    ACTION_GENERATE: "生成主视频",
    ACTION_REGENERATE: "重新生成",
    ACTION_CONFIRM_MAIN: "确认为主版本",
    ACTION_GO_TO_DELIVERY: "前往交付页面",
}

# Disabled-with-tooltip reason for generation actions (no backend yet).
GENERATION_BACKEND_PENDING_REASON_ZH = (
    "成片生成能力接入后启用 · 当前阶段仅做结构与方案准备。"
)
NO_CONFIRMABLE_VARIATION_REASON_ZH = (
    "尚无可作为主版本的成片。生成完成后再操作。"
)
ALREADY_CONFIRMED_REASON_ZH = (
    "本任务已选定主版本。如需更换，请先生成新版本后再操作。"
)

# Structured prefix written into the closure ``operator_publish_notes`` text
# to record the operator's "confirm main version" intent. Pure convention;
# no enum widening, no contract change. Mission product-decision #1
# (approved 2026-05-28).
MAIN_VERSION_CONFIRMED_NOTE_PREFIX = "[main-version-confirmed]"

# Honest empty-state message — verbatim Mission §B.1.
NOT_GENERATED_EMPTY_STATE_ZH = (
    "当前尚未生成主视频。"
    "已完成脚本结构与生成方案准备，"
    "成片生成能力接入后将在这里展示视频结果。"
)

# Operator-language head_reason labels — quarantined here so the engineering
# enum value (``final_missing`` / ``compose_not_ready`` / etc.) NEVER leaks
# into the operator-facing output. Mirrors the pattern in qc_diagnostics_view
# but exposes only the operator label.
_HEAD_REASON_OPERATOR_LABELS_ZH: Mapping[str, str] = {
    "publishable_ok": "无阻塞 · 可发布",
    "ready_gate_blocking": "上游门禁阻塞",
    "compose_not_ready": "成片合成未就绪",
    "final_missing": "主成片缺失",
    "final_stale": "主成片版本过时",
    "final_provenance_historical": "当前版本为历史版本",
    "required_deliverable_missing": "必需交付物缺失",
    "required_deliverable_blocking": "必需交付物未就绪",
    "unresolved": "状态待解析",
}


def _safe_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _safe_list(value: Any) -> list[Any]:
    if isinstance(value, (list, tuple)):
        return list(value)
    return []


def _is_matrix_script(panel: Mapping[str, Any]) -> bool:
    return str(panel.get("panel_kind") or "").strip().lower() == "matrix_script"


def _detect_confirmed_main_variation(
    closure: Optional[Mapping[str, Any]],
) -> Optional[str]:
    """Read closure events for the structured 主版本确认 note.

    Returns the ``variation_id`` of the LAST confirmation event (operators
    can re-confirm a different variation; latest wins). Returns ``None``
    when no confirmation is recorded.

    The note text is expected in either form:
        ``[main-version-confirmed] variation_id=<id>``
        ``[main-version-confirmed]`` (no variation_id — applies to whichever
        variation is currently recommended; the caller resolves).

    No new closed enum, no new event_kind, no contract change.
    """

    if not isinstance(closure, Mapping):
        return None
    records = _safe_list(
        closure.get("feedback_closure_records")
    ) or _safe_list(closure.get("records"))
    confirmed_variation_id: Optional[str] = None
    for record in records:
        if not isinstance(record, Mapping):
            continue
        event_kind = str(record.get("event_kind") or "")
        if event_kind != "operator_note":
            continue
        note = str(record.get("operator_publish_notes") or "")
        if MAIN_VERSION_CONFIRMED_NOTE_PREFIX not in note:
            continue
        # Parse variation_id=<id> from the note if present
        variation_id: Optional[str] = None
        marker = "variation_id="
        idx = note.find(marker)
        if idx != -1:
            tail = note[idx + len(marker):].strip()
            # Take the first whitespace-delimited token
            token = tail.split()[0] if tail else ""
            variation_id = token or None
        if variation_id:
            confirmed_variation_id = variation_id
        else:
            # Confirmation without explicit id — fall back to a sentinel that
            # the caller can resolve against the recommended variant.
            confirmed_variation_id = ""
    return confirmed_variation_id


def _select_preview_variation(
    variations: Iterable[Mapping[str, Any]],
    *,
    confirmed_variation_id: Optional[str],
    recommended_variation_id: Optional[str],
) -> Optional[Mapping[str, Any]]:
    """Pick the variation whose media we render in the preview hero.

    Selection order:
    1. The operator-confirmed main variation if it has ``current_fresh`` media.
    2. The recommended variation if it has ``current_fresh`` media.
    3. The first variation in the list that has ``current_fresh`` media.
    4. ``None`` — render the honest empty-state instead.
    """

    var_list = [v for v in variations if isinstance(v, Mapping)]

    def _is_fresh(v: Mapping[str, Any]) -> bool:
        return str(v.get("preview_status_code") or "") == "current_fresh"

    if confirmed_variation_id:
        for v in var_list:
            if str(v.get("variation_id") or "") == confirmed_variation_id and _is_fresh(v):
                return v
    if recommended_variation_id:
        for v in var_list:
            if str(v.get("variation_id") or "") == recommended_variation_id and _is_fresh(v):
                return v
    for v in var_list:
        if _is_fresh(v):
            return v
    return None


def _state_kind(
    *,
    publishable: bool,
    any_fresh_media: bool,
    is_generating: bool,
) -> str:
    if publishable:
        return STATE_DELIVERABLE
    if is_generating:
        return STATE_GENERATING
    if any_fresh_media:
        return STATE_AWAITING_REVIEW
    return STATE_NOT_GENERATED


def _build_blocker_and_next_action(
    *,
    state_kind: str,
    publish_readiness: Mapping[str, Any],
    confirmed_variation_id: Optional[str],
) -> tuple[str, str]:
    """Build the one-line operator-language blocker + next-action.

    Engineering identifiers (``publish_readiness`` / ``head_reason``)
    NEVER appear in the output; only operator-language labels.
    """

    if state_kind == STATE_DELIVERABLE:
        if confirmed_variation_id:
            return ("无阻塞 · 已确认主版本。", "下一步：前往交付页面发布。")
        return ("无阻塞 · 可发布。", "下一步：在交付页面确认并发布主版本。")
    if state_kind == STATE_AWAITING_REVIEW:
        return (
            "已生成可审核版本 · 等待运营选定主版本。",
            "下一步：在「可选变体」中查看并选定主版本，或重新生成。",
        )
    if state_kind == STATE_GENERATING:
        return ("生成进行中。", "下一步：等待生成完成后进入审核。")
    # not_generated
    head_reason = str(publish_readiness.get("head_reason") or "")
    head_reason_zh = _HEAD_REASON_OPERATOR_LABELS_ZH.get(head_reason)
    if head_reason_zh and head_reason_zh != "无阻塞 · 可发布":
        return (
            f"当前阻塞：{head_reason_zh}。",
            "下一步：完善脚本结构与变体方案后等待生成能力接入。",
        )
    return (
        "当前尚未生成主视频。",
        "下一步：完善脚本结构与变体方案后等待生成能力接入。",
    )


def _build_actions(
    *,
    state_kind: str,
    has_confirmable_variation: bool,
    confirmed_variation_id: Optional[str],
    task_id: str,
) -> list[dict[str, Any]]:
    """Build the closed 4-action bar."""

    actions: list[dict[str, Any]] = [
        {
            "action_id": ACTION_GENERATE,
            "label_zh": ACTION_LABELS_ZH[ACTION_GENERATE],
            "enabled": False,
            "disabled_reason_zh": GENERATION_BACKEND_PENDING_REASON_ZH,
        },
        {
            "action_id": ACTION_REGENERATE,
            "label_zh": ACTION_LABELS_ZH[ACTION_REGENERATE],
            "enabled": False,
            "disabled_reason_zh": GENERATION_BACKEND_PENDING_REASON_ZH,
        },
    ]
    if confirmed_variation_id:
        actions.append(
            {
                "action_id": ACTION_CONFIRM_MAIN,
                "label_zh": ACTION_LABELS_ZH[ACTION_CONFIRM_MAIN],
                "enabled": False,
                "disabled_reason_zh": ALREADY_CONFIRMED_REASON_ZH,
            }
        )
    elif has_confirmable_variation:
        actions.append(
            {
                "action_id": ACTION_CONFIRM_MAIN,
                "label_zh": ACTION_LABELS_ZH[ACTION_CONFIRM_MAIN],
                "enabled": True,
                "disabled_reason_zh": None,
            }
        )
    else:
        actions.append(
            {
                "action_id": ACTION_CONFIRM_MAIN,
                "label_zh": ACTION_LABELS_ZH[ACTION_CONFIRM_MAIN],
                "enabled": False,
                "disabled_reason_zh": NO_CONFIRMABLE_VARIATION_REASON_ZH,
            }
        )
    actions.append(
        {
            "action_id": ACTION_GO_TO_DELIVERY,
            "label_zh": ACTION_LABELS_ZH[ACTION_GO_TO_DELIVERY],
            "enabled": True,
            "href": f"/tasks/{task_id}/publish",
        }
    )
    return actions


def derive_matrix_script_main_video_result(
    task: Optional[Mapping[str, Any]],
    workbench_panel: Optional[Mapping[str, Any]],
    publish_readiness: Optional[Mapping[str, Any]],
    preview_compare: Optional[Mapping[str, Any]] = None,
    recommended_action: Optional[Mapping[str, Any]] = None,
    closure: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    """Project the Matrix Script Workbench 主视频结果 bundle.

    Returns ``{}`` for non-Matrix-Script panels so the caller can attach
    unconditionally.
    """

    panel = _safe_mapping(workbench_panel)
    if not _is_matrix_script(panel):
        return {}

    task_map = _safe_mapping(task)
    task_id = str(task_map.get("task_id") or task_map.get("id") or "")
    pr_map = _safe_mapping(publish_readiness)
    pc_map = _safe_mapping(preview_compare)
    ra_map = _safe_mapping(recommended_action)
    closure_map = _safe_mapping(closure)

    variations = _safe_list(pc_map.get("variations"))
    any_fresh_media = any(
        isinstance(v, Mapping) and str(v.get("preview_status_code") or "") == "current_fresh"
        for v in variations
    )
    recommended_variation_id = str(
        _safe_mapping(ra_map.get("recommended_variant")).get("variation_id") or ""
    ) or None

    confirmed_variation_id = _detect_confirmed_main_variation(closure_map)
    # If the confirmation note had no explicit variation_id, resolve to the
    # recommended variant id at presentation time.
    if confirmed_variation_id == "" and recommended_variation_id:
        confirmed_variation_id = recommended_variation_id

    publishable = bool(pr_map.get("publishable"))
    state_kind = _state_kind(
        publishable=publishable,
        any_fresh_media=any_fresh_media,
        is_generating=False,  # no async generation backend signal today
    )
    state_label_zh = STATE_LABELS_ZH[state_kind]

    preview_variation = _select_preview_variation(
        variations,
        confirmed_variation_id=confirmed_variation_id,
        recommended_variation_id=recommended_variation_id,
    )
    preview = {
        "available": preview_variation is not None,
        "variation_id": str(preview_variation.get("variation_id"))
        if preview_variation is not None
        else None,
        "empty_state_message_zh": None
        if preview_variation is not None
        else NOT_GENERATED_EMPTY_STATE_ZH,
    }

    blocker_zh, next_action_zh = _build_blocker_and_next_action(
        state_kind=state_kind,
        publish_readiness=pr_map,
        confirmed_variation_id=confirmed_variation_id,
    )
    actions = _build_actions(
        state_kind=state_kind,
        has_confirmable_variation=any_fresh_media,
        confirmed_variation_id=confirmed_variation_id,
        task_id=task_id,
    )

    return {
        "is_matrix_script": True,
        "panel_title_zh": "主视频结果",
        "panel_subtitle_zh": (
            "本任务最终交付的主成片。首屏只看这一块即可知道是否生成、是否可交付。"
        ),
        "state_kind": state_kind,
        "state_label_zh": state_label_zh,
        "preview": preview,
        "primary_actions": actions,
        "blocker_one_liner_zh": blocker_zh,
        "next_action_one_liner_zh": next_action_zh,
        "confirmed_main_variation_id": confirmed_variation_id or None,
        "recommended_variation_id": recommended_variation_id,
        # Structured note prefix exposed so the template's JS write-back
        # can construct the correct note text via the existing closure
        # endpoint.
        "confirm_note_prefix": MAIN_VERSION_CONFIRMED_NOTE_PREFIX,
        "closure_event_endpoint_template": (
            "/api/matrix-script/closures/{task_id}/events"
        ),
    }


__all__ = [
    "ACTION_CONFIRM_MAIN",
    "ACTION_GENERATE",
    "ACTION_GO_TO_DELIVERY",
    "ACTION_LABELS_ZH",
    "ACTION_REGENERATE",
    "ALREADY_CONFIRMED_REASON_ZH",
    "GENERATION_BACKEND_PENDING_REASON_ZH",
    "MAIN_VERSION_CONFIRMED_NOTE_PREFIX",
    "NOT_GENERATED_EMPTY_STATE_ZH",
    "NO_CONFIRMABLE_VARIATION_REASON_ZH",
    "STATE_AWAITING_REVIEW",
    "STATE_DELIVERABLE",
    "STATE_GENERATING",
    "STATE_LABELS_ZH",
    "STATE_NOT_GENERATED",
    "derive_matrix_script_main_video_result",
]
