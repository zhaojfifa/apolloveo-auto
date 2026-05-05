"""Digital Anchor publish-hub PR-3 attach seam (OWC-DA PR-3 / DA-W8 + DA-W9).

Pure seam that attaches the two OWC-DA PR-3 Delivery Center bundle
keys (``digital_anchor_delivery_pack`` + ``digital_anchor_delivery_backfill``)
to a pre-built publish-hub payload. Mirrors the OWC-MS PR-3 pattern at
:mod:`gateway.app.services.matrix_script.publish_hub_pr3_attach`.

Behavior in production is byte-equivalent to an inline block in
``publish_hub_payload``: the same two helpers are called with the same
inputs, the same defense-in-depth ``try/except`` defaults to ``{}`` on
failure, and the same payload keys are written.

Hard discipline (binding under OWC-DA gate spec §4):

- No new behavior beyond projection-side rendering. The helpers it
  calls are pure read-over-existing truth (delivery_binding /
  closure).
- No second authoritative producer for publishability /
  ``final_provenance`` / advisories.
- No new endpoint; no new contract; no schema widening; no packet
  mutation.
- No ``gateway.app.config`` dependency at module import (so the
  wiring tests load on Python 3.9 without the PEP-604 baseline issue).
- No ``artifact_storage`` dependency (so the wiring tests do not
  require ambient storage configuration).
- No provider / model / vendor / engine identifier admitted into any
  payload (validator R3 + design-handoff red line 6).
"""
from __future__ import annotations

from typing import Any


def attach_digital_anchor_delivery_pr3_extras(
    *, payload: dict[str, Any], task: dict[str, Any]
) -> None:
    """Attach OWC-DA PR-3 Delivery Center extras (DA-W8 + DA-W9) to the
    publish-hub payload in place.

    Reads only:

    - ``payload["digital_anchor_delivery_binding"]`` — the
      ``digital_anchor_delivery_binding_v1`` projection emitted by
      ``project_delivery_binding(packet)`` and attached upstream by the
      Recovery PR-4 block in ``publish_hub_payload``. This is the
      single authoritative projection source for DA-W8.
    - ``payload["digital_anchor_publish_feedback_closure"]`` — the
      closure view already attached upstream by the Recovery PR-4
      block. This is the single truth path for DA-W9 多渠道回填.

    Defense-in-depth: a projection error never breaks the publish hub;
    both keys default to ``{}`` instead. Mirrors the OWC-MS PR-3 attach
    seam.

    Authority: ``docs/reviews/owc_da_gate_spec_v1.md`` §3 DA-W8 /
    DA-W9; ``docs/product/digital_anchor_product_flow_v1.md`` §7.1 /
    §7.3.
    """

    # Defensive cross-line isolation. Production callers already gate by
    # ``kind_value == "digital_anchor"`` before invoking this seam; this
    # check guards against future regression and lets the wiring tests
    # drive arbitrary kinds without polluting non-digital_anchor payloads.
    if not _is_digital_anchor_task(task):
        payload["digital_anchor_delivery_pack"] = {}
        payload["digital_anchor_delivery_backfill"] = {}
        return

    try:
        from gateway.app.services.digital_anchor.delivery_pack_view import (
            derive_digital_anchor_delivery_pack,
        )
        from gateway.app.services.digital_anchor.publish_closure_backfill_view import (
            derive_digital_anchor_publish_closure_backfill,
        )

        payload["digital_anchor_delivery_pack"] = (
            derive_digital_anchor_delivery_pack(
                delivery_binding=payload.get("digital_anchor_delivery_binding") or {},
                task=task,
            )
        )
        payload["digital_anchor_delivery_backfill"] = (
            derive_digital_anchor_publish_closure_backfill(
                payload.get("digital_anchor_publish_feedback_closure")
            )
        )
    except Exception:
        payload["digital_anchor_delivery_pack"] = {}
        payload["digital_anchor_delivery_backfill"] = {}


def _is_digital_anchor_task(task: Any) -> bool:
    if not isinstance(task, dict):
        return False
    for key in ("kind", "category_key", "category", "platform"):
        value = task.get(key)
        if isinstance(value, str) and value.strip().lower() == "digital_anchor":
            return True
    return False


__all__ = ["attach_digital_anchor_delivery_pr3_extras"]
