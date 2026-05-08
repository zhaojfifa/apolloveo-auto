"""Matrix Script publish-hub render-data seam (OWC-MS-RO PR-4).

Thin orchestration helper that assembles the matrix_script-specific
template variables for the result-oriented Delivery Center surface
defined in
``docs/design/matrix_script_delivery_center_wireframe_v1.md`` §3-§9
+ ``docs/design/matrix_script_result_oriented_ui_implementation_slicing_v1.md``
§7 (PR-4 scope, RO-4.* acceptance evidence).

This module mirrors the
``gateway/app/services/matrix_script/publish_hub_pr3_attach.py`` precedent:
a pure presentation-layer seam that consumes existing helpers and returns
a closed dict for the template to render. It does NOT introduce any new
helper logic, contract, schema, endpoint, or closed enum. The seam is
extracted (rather than inlined into the page route) so the dedicated
PR-4 test suite can exercise the full assembly path without depending on
``compute_composed_state`` / ``artifact_storage`` / ambient storage
configuration / FastAPI request plumbing.

Hard discipline (binding under
matrix_script_result_oriented_ui_implementation_slicing_v1.md §7.5 +
recovery amendment §7):

- No new helper module beyond this thin orchestration seam — all helper
  logic lives in the existing per-concept modules (``delivery_comprehension``,
  ``preview_compare_view``, ``recommended_action_view``,
  ``delivery_ready_package_view``, ``delivery_copy_bundle_view``,
  ``publish_backfill_readiness_view``, ``task_area_convergence``,
  ``result_status_view``, ``closure_binding``).
- No new endpoint; no contract / schema / packet / validator mutation.
- No closed-enum widening.
- No second authoritative producer for ``publishable`` /
  ``final_provenance`` / advisories — every ``publishable`` consumer
  reads ``compute_publish_readiness`` directly.
- No raw refs / ``content://`` handles / ``slot_id`` / ``cell_id`` /
  ``script_slot_ref`` / ``binds_cell_id`` exposure in
  operator-visible values.
- No fake ``final_video`` / fabricated ``publish_url`` / fake delivery
  artifact — tracked-gap rows render explicit operator-language text
  (RC-R8 invariant carries forward).
- No closure event mutation / deletion (append-only).
- Hot Follow / Digital Anchor / Asset Supply file paths NOT touched —
  this seam returns ``{}`` for non-matrix_script tasks so the page route
  preserves the Hot Follow + Digital Anchor branches bytewise unchanged.
- No ``gateway.app.config`` dependency at module import (so the dedicated
  test loads on Python 3.9 without the PEP-604 baseline issue).
- No ``artifact_storage`` dependency (so the dedicated test does not
  require ambient storage configuration).
"""
from __future__ import annotations

from typing import Any, Mapping, Optional


def derive_matrix_script_publish_hub_render_data(
    task: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Build the matrix_script-specific render-data dict for the
    Delivery Center page render.

    Returns ``{}`` for non-matrix_script tasks so the page route
    preserves the Hot Follow + Digital Anchor branches bytewise
    unchanged. Defense-in-depth: every helper invocation is wrapped
    in ``try/except``; a projection error never breaks the publish
    hub render — the corresponding key defaults to ``{}``.

    Output dict keys (closed-and-exhaustive for PR-4):

    - ``is_matrix_script`` — ``True`` for matrix_script tasks.
    - ``task_id`` — the operator-visible task id (used for the
      closure-event endpoint URL).
    - ``eight_stage_state`` — header stage badge.
    - ``task_area_result_status`` — header result pill.
    - ``publish_readiness`` — header readiness banner (single-source
      ``compute_publish_readiness`` output; RC-A7 invariant).
    - ``delivery_comprehension`` — Block A primary slot label set +
      Block B / C lane row sets.
    - ``preview_compare`` — Block A variant tabs + Block E
      per-variation publish-status carry-through.
    - ``recommended_action`` — Block A recommended-candidate marker
      (single-source from RC-R4).
    - ``delivery_ready_package`` — Block B per-variation package
      readiness pill (closed PACKAGE_* enum) + Block A primary slot
      tracked-gap explanation when no candidate is publishable.
    - ``delivery_copy_bundle`` — Block D copy bundle (subfields).
    - ``publish_backfill_readiness`` — Block F iteration recommendation
      (per-variation ``next_input_zh`` / ``gap_summary_zh``).
    - ``publish_feedback_closure`` — Block E publish-feedback
      ``variation_feedback[]`` + ``feedback_closure_records[]``
      (read-only).
    - ``closure_endpoint_url`` — ``POST /api/matrix-script/closures/{task_id}/events``
      resolved against the task's task_id (operator-record-publish-event
      form action target).

    For non-matrix_script tasks, returns ``{}``.
    """
    task_dict = task if isinstance(task, Mapping) else {}
    if not _is_matrix_script_task(task_dict):
        return {}

    task_id = _resolve_task_id(task_dict)
    panel = {"panel_kind": "matrix_script"}

    closure_view = _safe_closure_view(task_id)
    delivery_binding = _safe_delivery_binding(task_dict)
    variation_surface = _safe_variation_surface(task_dict)

    delivery_comprehension = _safe_delivery_comprehension(delivery_binding)
    publish_readiness = _safe_publish_readiness(task_dict, delivery_binding)

    preview_compare = _safe_preview_compare(
        variation_surface, delivery_binding, publish_readiness, panel, closure_view
    )

    readable_variants = _safe_readable_variants(
        task_dict, variation_surface, panel, preview_compare
    )

    recommended_action = _safe_recommended_action(
        preview_compare, readable_variants, panel
    )

    base_copy_bundle = _safe_base_copy_bundle(task_dict)
    delivery_copy_bundle = _safe_delivery_copy_bundle(task_dict, base_copy_bundle)

    delivery_ready_package = _safe_delivery_ready_package(
        readable_variants,
        delivery_comprehension,
        delivery_copy_bundle,
        publish_readiness,
        panel,
    )

    publish_backfill_readiness = _safe_publish_backfill_readiness(
        readable_variants,
        delivery_comprehension,
        publish_readiness,
        closure_view,
    )

    eight_stage_state = _safe_eight_stage_state(task_dict, closure_view)
    task_area_result_status = _safe_task_area_result_status(task_dict, closure_view)

    closure_endpoint_url = (
        f"/api/matrix-script/closures/{task_id}/events" if task_id else None
    )

    return {
        "is_matrix_script": True,
        "task_id": task_id,
        "eight_stage_state": eight_stage_state,
        "task_area_result_status": task_area_result_status,
        "publish_readiness": publish_readiness,
        "delivery_comprehension": delivery_comprehension,
        "preview_compare": preview_compare,
        "recommended_action": recommended_action,
        "delivery_ready_package": delivery_ready_package,
        "delivery_copy_bundle": delivery_copy_bundle,
        "publish_backfill_readiness": publish_backfill_readiness,
        "publish_feedback_closure": closure_view or {},
        "closure_endpoint_url": closure_endpoint_url,
    }


# --------------------------------------------------------------------------
# Defensive wrappers — every helper invocation guarded so a projection
# error returns {} instead of breaking the page render.
# --------------------------------------------------------------------------


def _safe_closure_view(task_id: str) -> Optional[Mapping[str, Any]]:
    if not task_id:
        return None
    try:
        from gateway.app.services.matrix_script.closure_binding import (
            get_closure_view_for_task,
        )

        return get_closure_view_for_task(task_id)
    except Exception:
        return None


def _safe_delivery_binding(task: Mapping[str, Any]) -> dict[str, Any]:
    try:
        from gateway.app.services.matrix_script.delivery_binding import (
            project_delivery_binding,
        )

        packet_view = (
            task.get("packet") if isinstance(task.get("packet"), Mapping) else task
        )
        return dict(project_delivery_binding(packet_view) or {})
    except Exception:
        return {}


def _safe_variation_surface(task: Mapping[str, Any]) -> dict[str, Any]:
    try:
        from gateway.app.services.matrix_script.workbench_variation_surface import (
            project_workbench_variation_surface,
        )

        packet_view = (
            task.get("packet") if isinstance(task.get("packet"), Mapping) else task
        )
        return dict(project_workbench_variation_surface(packet_view) or {})
    except Exception:
        return {}


def _safe_delivery_comprehension(
    delivery_binding: Mapping[str, Any],
) -> dict[str, Any]:
    try:
        from gateway.app.services.matrix_script.delivery_comprehension import (
            derive_matrix_script_delivery_comprehension,
        )

        return dict(derive_matrix_script_delivery_comprehension(delivery_binding) or {})
    except Exception:
        return {}


def _safe_publish_readiness(
    task: Mapping[str, Any],
    delivery_binding: Mapping[str, Any],
) -> dict[str, Any]:
    """Re-derive publish_readiness for the publish-hub page render.

    Mirrors the publish-hub-only path inside
    ``publish_hub_payload`` (PR-1 unified producer): single producer,
    no second authoritative truth. Defensive try/except returns ``{}``
    on any failure so the page render degrades gracefully.
    """
    try:
        from gateway.app.services.operator_visible_surfaces.publish_readiness import (
            compute_publish_readiness,
        )

        ready_gate = task.get("ready_gate") if isinstance(task.get("ready_gate"), Mapping) else {}
        l2_facts: dict[str, Any] = {}
        l3_current_attempt: dict[str, Any] = {}
        # Walk the well-known fact roots on the task dict; every key here
        # is already the operator-visible truth surface, never a
        # vendor / model / provider / engine identifier.
        if isinstance(task.get("final"), Mapping):
            l2_facts["final"] = dict(task["final"])
        if isinstance(task.get("historical_final"), Mapping):
            l2_facts["historical_final"] = dict(task["historical_final"])
        if "final_fresh" in task:
            l2_facts["final_fresh"] = bool(task.get("final_fresh"))
        if "final_stale_reason" in task:
            l2_facts["final_stale_reason"] = task.get("final_stale_reason")
        if isinstance(task.get("current_attempt"), Mapping):
            l3_current_attempt = dict(task["current_attempt"])
        delivery_pack = (
            delivery_binding.get("delivery_pack")
            if isinstance(delivery_binding, Mapping)
            else {}
        )
        delivery_rows = None
        if isinstance(delivery_pack, Mapping):
            rows = delivery_pack.get("deliverables")
            if isinstance(rows, list):
                delivery_rows = [r for r in rows if isinstance(r, Mapping)]
        result = compute_publish_readiness(
            ready_gate=ready_gate or {},
            l2_facts=l2_facts,
            l3_current_attempt=l3_current_attempt,
            delivery_rows=delivery_rows,
        )
        return dict(result or {})
    except Exception:
        return {}


def _safe_preview_compare(
    variation_surface: Mapping[str, Any],
    delivery_binding: Mapping[str, Any],
    publish_readiness: Mapping[str, Any],
    panel: Mapping[str, Any],
    closure_view: Optional[Mapping[str, Any]],
) -> dict[str, Any]:
    try:
        from gateway.app.services.matrix_script.preview_compare_view import (
            derive_matrix_script_preview_compare_view,
        )

        return dict(
            derive_matrix_script_preview_compare_view(
                variation_surface,
                delivery_binding,
                publish_readiness,
                panel,
                closure=closure_view,
            )
            or {}
        )
    except Exception:
        return {}


def _safe_readable_variants(
    task: Mapping[str, Any],
    variation_surface: Mapping[str, Any],
    panel: Mapping[str, Any],
    preview_compare: Mapping[str, Any],
) -> dict[str, Any]:
    try:
        from gateway.app.services.matrix_script.readable_variant_view import (
            derive_matrix_script_readable_variants,
        )

        return dict(
            derive_matrix_script_readable_variants(
                task,
                variation_surface,
                panel,
                preview_compare=preview_compare,
            )
            or {}
        )
    except Exception:
        return {}


def _safe_recommended_action(
    preview_compare: Mapping[str, Any],
    readable_variants: Mapping[str, Any],
    panel: Mapping[str, Any],
) -> dict[str, Any]:
    try:
        from gateway.app.services.matrix_script.recommended_action_view import (
            derive_matrix_script_recommended_action,
        )

        return dict(
            derive_matrix_script_recommended_action(
                preview_compare,
                readable_variants,
                panel,
            )
            or {}
        )
    except Exception:
        return {}


def _safe_base_copy_bundle(task: Mapping[str, Any]) -> dict[str, Any]:
    """Read the existing publish-hub copy_bundle producer's output without
    pulling in ``compute_composed_state`` / ``artifact_storage``."""
    try:
        from gateway.app.services.task_view_helpers import _build_copy_bundle  # type: ignore[attr-defined]

        return dict(_build_copy_bundle(dict(task)) or {})
    except Exception:
        return {}


def _safe_delivery_copy_bundle(
    task: Mapping[str, Any], base_copy_bundle: Mapping[str, Any]
) -> dict[str, Any]:
    try:
        from gateway.app.services.matrix_script.delivery_copy_bundle_view import (
            derive_matrix_script_delivery_copy_bundle,
        )

        return dict(
            derive_matrix_script_delivery_copy_bundle(
                dict(task), base_copy_bundle=dict(base_copy_bundle)
            )
            or {}
        )
    except Exception:
        return {}


def _safe_delivery_ready_package(
    readable_variants: Mapping[str, Any],
    delivery_comprehension: Mapping[str, Any],
    copy_bundle_view: Mapping[str, Any],
    publish_readiness: Mapping[str, Any],
    panel: Mapping[str, Any],
) -> dict[str, Any]:
    try:
        from gateway.app.services.matrix_script.delivery_ready_package_view import (
            derive_matrix_script_delivery_ready_package,
        )

        return dict(
            derive_matrix_script_delivery_ready_package(
                readable_variants,
                delivery_comprehension,
                copy_bundle_view,
                publish_readiness,
                panel,
            )
            or {}
        )
    except Exception:
        return {}


def _safe_publish_backfill_readiness(
    readable_variants: Mapping[str, Any],
    delivery_comprehension: Mapping[str, Any],
    publish_readiness: Mapping[str, Any],
    closure_view: Optional[Mapping[str, Any]],
) -> dict[str, Any]:
    try:
        from gateway.app.services.matrix_script.publish_backfill_readiness_view import (
            derive_matrix_script_publish_backfill_readiness,
        )

        return dict(
            derive_matrix_script_publish_backfill_readiness(
                readable_variants,
                delivery_comprehension,
                publish_readiness,
                closure_view,
            )
            or {}
        )
    except Exception:
        return {}


def _safe_eight_stage_state(
    task: Mapping[str, Any],
    closure_view: Optional[Mapping[str, Any]],
) -> dict[str, Any]:
    try:
        from gateway.app.services.matrix_script.task_area_convergence import (
            derive_matrix_script_eight_stage_state,
        )

        return dict(
            derive_matrix_script_eight_stage_state(task, closure=closure_view) or {}
        )
    except Exception:
        return {}


def _safe_task_area_result_status(
    task: Mapping[str, Any],
    closure_view: Optional[Mapping[str, Any]],
) -> dict[str, Any]:
    try:
        from gateway.app.services.matrix_script.result_status_view import (
            derive_matrix_script_task_area_result_status,
        )

        return dict(
            derive_matrix_script_task_area_result_status(task, closure=closure_view)
            or {}
        )
    except Exception:
        return {}


def _is_matrix_script_task(task: Any) -> bool:
    if not isinstance(task, Mapping):
        return False
    for key in ("kind", "category_key", "category", "platform"):
        value = task.get(key)
        if isinstance(value, str) and value.strip().lower() == "matrix_script":
            return True
    return False


def _resolve_task_id(task: Mapping[str, Any]) -> str:
    for key in ("task_id", "id"):
        value = task.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


__all__ = ["derive_matrix_script_publish_hub_render_data"]
