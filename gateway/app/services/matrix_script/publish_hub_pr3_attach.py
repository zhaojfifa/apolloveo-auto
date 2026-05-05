"""Matrix Script publish-hub PR-3 attach seam (OWC-MS PR-3 / MS-W7 + MS-W8).

Pure seam that attaches the two OWC-MS PR-3 Delivery Center bundle keys
(``matrix_script_delivery_copy_bundle`` + ``matrix_script_delivery_backfill``)
to a pre-built publish-hub payload. Extracted from
``gateway/app/services/task_view_helpers.py::publish_hub_payload`` so the
PR-3 wiring test can exercise the actual attach path **without** depending
on ``compute_composed_state`` / ``artifact_storage`` / ambient storage
configuration / the ``gateway.app.config`` import chain (the latter uses
PEP-604 unions and only loads on Python 3.10+).

Behavior in production is byte-equivalent to the prior inline block in
``publish_hub_payload``: the same two helpers are called with the same
inputs, the same defense-in-depth ``try/except`` defaults to ``{}`` on
failure, and the same payload keys are written.

Hard discipline (binding under OWC-MS gate spec §4 + PR-3 reviewer-fail
correction Blocker 2 — 2026-05-05):

- No new behavior. The seam is a refactor of the existing inline attach
  block; the helpers it calls are unchanged.
- No second authoritative producer for publish copy / publishability /
  final_provenance / advisories.
- No new endpoint; no new contract; no schema widening; no packet
  mutation.
- No ``gateway.app.config`` dependency at module import (so the wiring
  test loads on Python 3.9 without the PEP-604 baseline issue).
- No ``artifact_storage`` dependency (so the wiring test does not
  require ambient storage configuration).
- No provider / model / vendor / engine identifier admitted into any
  payload (validator R3 + design-handoff red line 6).
"""
from __future__ import annotations

from typing import Any


def attach_matrix_script_delivery_pr3_extras(
    *, payload: dict[str, Any], task: dict[str, Any]
) -> None:
    """Attach OWC-MS PR-3 Delivery Center extras (MS-W7 + MS-W8) to the
    publish-hub payload in place.

    Reads only:

    - ``payload["copy_bundle"]`` — the existing publish-hub copy_bundle
      projection emitted by ``_build_copy_bundle(task)`` upstream. This
      is the **single authoritative copy producer** for MS-W7. Adjacent
      task-entry hints (``target_platform`` / ``audience_hint`` /
      ``tone_hint`` / ``topic`` / ``length_hint``) are NOT consumed —
      the Blocker 1 correction enforces single-source discipline.
    - ``payload["matrix_script_publish_feedback_closure"]`` — the
      closure view already attached upstream by the Recovery PR-3
      block. This is the single truth path for MS-W8 多渠道回填.

    Defense-in-depth: a projection error never breaks the publish hub;
    both keys default to ``{}`` instead. Mirrors the PR-U3 + Recovery
    PR-3 patterns in ``publish_hub_payload``.

    Authority: ``docs/reviews/owc_ms_gate_spec_v1.md`` §3 MS-W7 / MS-W8;
    ``docs/product/matrix_script_product_flow_v1.md`` §7.1 / §7.3.
    """

    # Defensive cross-line isolation. Production callers already gate by
    # ``kind_value == "matrix_script"`` before invoking this seam; this
    # check guards against future regression and lets the wiring tests
    # drive arbitrary kinds without polluting non-matrix_script payloads.
    if not _is_matrix_script_task(task):
        payload["matrix_script_delivery_copy_bundle"] = {}
        payload["matrix_script_delivery_backfill"] = {}
        return

    try:
        from gateway.app.services.matrix_script.delivery_backfill_view import (
            derive_matrix_script_delivery_backfill,
        )
        from gateway.app.services.matrix_script.delivery_copy_bundle_view import (
            derive_matrix_script_delivery_copy_bundle,
        )

        payload["matrix_script_delivery_copy_bundle"] = (
            derive_matrix_script_delivery_copy_bundle(
                task,
                base_copy_bundle=payload.get("copy_bundle") or {},
            )
        )
        payload["matrix_script_delivery_backfill"] = (
            derive_matrix_script_delivery_backfill(
                payload.get("matrix_script_publish_feedback_closure")
            )
        )
    except Exception:
        payload["matrix_script_delivery_copy_bundle"] = {}
        payload["matrix_script_delivery_backfill"] = {}


def _is_matrix_script_task(task: Any) -> bool:
    if not isinstance(task, dict):
        return False
    for key in ("kind", "category_key", "category", "platform"):
        value = task.get(key)
        if isinstance(value, str) and value.strip().lower() == "matrix_script":
            return True
    return False


__all__ = ["attach_matrix_script_delivery_pr3_extras"]
