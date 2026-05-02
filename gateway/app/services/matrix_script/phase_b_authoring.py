"""Matrix Script Phase B deterministic authoring.

Plan A trial correction set §8.C: synchronously derive populated
``variation_matrix.delta`` and ``slot_pack.delta`` payloads from the closed
entry field set so a fresh contract-clean Matrix Script sample renders real
axes / cells / slots in the Phase B workbench panel instead of empty
fallbacks.

Authority:

- ``docs/reviews/matrix_script_trial_blocker_and_realign_review_v1.md`` §8.C
- ``docs/contracts/matrix_script/task_entry_contract_v1.md`` §"Phase B
  deterministic authoring (addendum, 2026-05-03)"
- ``docs/contracts/matrix_script/variation_matrix_contract_v1.md``
- ``docs/contracts/matrix_script/slot_pack_contract_v1.md``
- ``docs/contracts/matrix_script/packet_v1.md``

Discipline:

- Deterministic. Same ``(entry, task_id)`` always produces the same output.
  No clock, no randomness, no env reads, no IO.
- Read-only. ``entry`` is a frozen dataclass; this module does not mutate it.
- Pure. No imports from routers, no ``HTTPException``, no
  ``normalize_task_payload`` — those concerns live in ``create_entry.py``.
- Round-trip integrity by construction:
  ``cells[i].script_slot_ref == slots[i].slot_id`` and
  ``slots[i].binds_cell_id == cells[i].cell_id`` for every
  ``i ∈ [0, entry.variation_target_count)``.
- ``body_ref`` is opaque and derived from ``task_id`` and ``slot_id`` only —
  never embeds body text nor copies the operator-supplied
  ``source_script_ref`` (defends ``slot_pack_contract_v1`` §"Forbidden":
  bodies are referenced by ``body_ref`` only).

Plan E real authoring may replace or extend this seed without re-versioning
the contract.
"""
from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - typing only
    from gateway.app.services.matrix_script.create_entry import (
        MatrixScriptCreateEntry,
    )


AXIS_KIND_SET: tuple[str, ...] = ("categorical", "range", "enum")
SLOT_KIND_SET: tuple[str, ...] = ("primary", "alternate", "fallback")

TONES: tuple[str, ...] = ("formal", "casual", "playful")
AUDIENCES: tuple[str, ...] = ("b2b", "b2c", "internal")
LENGTH_RANGE: dict[str, int] = {"min": 30, "max": 120, "step": 15}
LENGTH_PICKS: tuple[int, ...] = (30, 45, 60, 75, 90, 105, 120)

CELL_NOTES: str = "trial-deterministic"
DEFAULT_SLOT_KIND: str = "primary"


def _canonical_axes() -> list[dict[str, Any]]:
    return [
        {
            "axis_id": "tone",
            "kind": "categorical",
            "values": list(TONES),
            "is_required": True,
        },
        {
            "axis_id": "audience",
            "kind": "enum",
            "values": list(AUDIENCES),
            "is_required": True,
        },
        {
            "axis_id": "length",
            "kind": "range",
            "values": dict(LENGTH_RANGE),
            "is_required": False,
        },
    ]


def _build_body_ref(task_id: str, slot_id: str) -> str:
    return f"content://matrix-script/{task_id}/slot/{slot_id}"


def derive_phase_b_deltas(
    entry: "MatrixScriptCreateEntry",
    task_id: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return ``(variation_matrix_delta, slot_pack_delta)``.

    Cardinality ``k = entry.variation_target_count`` (validated 1..12 by
    ``_variation_count`` upstream). Cells walk a deterministic rotation of
    9 ``(tone, audience)`` combos × 7 ``length`` picks (63 distinct tuples)
    so any k ≤ 12 is covered with distinct ``axis_selections``.
    """

    k = int(entry.variation_target_count)
    language_scope = {
        "source_language": entry.source_language,
        "target_language": [entry.target_language],
    }

    cells: list[dict[str, Any]] = []
    slots: list[dict[str, Any]] = []

    for i in range(k):
        cell_id = f"cell_{i + 1:03d}"
        slot_id = f"slot_{i + 1:03d}"
        tone = TONES[i % len(TONES)]
        audience = AUDIENCES[(i // len(TONES)) % len(AUDIENCES)]
        length_pick = LENGTH_PICKS[i % len(LENGTH_PICKS)]

        cells.append(
            {
                "cell_id": cell_id,
                "axis_selections": {
                    "tone": tone,
                    "audience": audience,
                    "length": length_pick,
                },
                "script_slot_ref": slot_id,
                "notes": CELL_NOTES,
            }
        )
        slots.append(
            {
                "slot_id": slot_id,
                "binds_cell_id": cell_id,
                "language_scope": deepcopy(language_scope),
                "body_ref": _build_body_ref(task_id, slot_id),
                "length_hint": length_pick,
                "slot_kind": DEFAULT_SLOT_KIND,
            }
        )

    variation_delta: dict[str, Any] = {
        "axis_kind_set": list(AXIS_KIND_SET),
        "axes": _canonical_axes(),
        "cells": cells,
    }
    slot_delta: dict[str, Any] = {
        "slot_kind_set": list(SLOT_KIND_SET),
        "slots": slots,
    }
    return variation_delta, slot_delta


__all__ = [
    "AUDIENCES",
    "AXIS_KIND_SET",
    "CELL_NOTES",
    "DEFAULT_SLOT_KIND",
    "LENGTH_PICKS",
    "LENGTH_RANGE",
    "SLOT_KIND_SET",
    "TONES",
    "derive_phase_b_deltas",
]
