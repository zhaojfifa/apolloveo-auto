"""Matrix Script delivery binding projection + B4 artifact lookup + PR-3 zoning.

Phase C: read-only projection from a Matrix Script packet instance to the
delivery-center binding surface. No publish feedback write-back, no provider
routing, no packet mutation.

Plan E phase 1 (Item E.MS.1) added the B4 artifact-lookup function per
``docs/contracts/matrix_script/result_packet_binding_artifact_lookup_contract_v1.md``
and replaced the five ``not_implemented_phase_c`` placeholder rows with calls
to that lookup. The lookup is a pure projection of packet truth — it never
performs I/O, never mutates the packet, never fabricates handles, and never
raises. When the packet does not yet carry the truth required to resolve a
row (notably L3 ``final_provenance`` from Plan D D2, which remains forbidden
in this Plan E phase per the gate spec §4.2), the lookup returns the
contract sentinel ``artifact_lookup_unresolved``.

Plan E phase 1 / PR-3 (Item E.MS.3) extends every Matrix Script delivery row
with the explicit ``required`` + ``blocking_publish`` zoning fields per the
Plan C amendment to ``docs/contracts/factory_delivery_contract_v1.md``
§"Per-Deliverable Required / Blocking Fields (Plan D Amendment)" and pins
``scene_pack`` rows to ``required=false`` + ``blocking_publish=false`` per
§"Scene-Pack Non-Blocking Rule (Explicit; Plan C Amendment)" — independent
of any line capability flag. The validator invariant
``required=false ⇒ blocking_publish=false`` is enforced defensively by
``_clamp_blocking_publish`` so a malformed line policy can never assert a
non-required row as blocking.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Iterable, Mapping, Optional

VARIATION_REF_ID = "matrix_script_variation_matrix"
SLOT_PACK_REF_ID = "matrix_script_slot_pack"
CAPABILITY_SUBTITLES_REF_ID = "capability:subtitles"
CAPABILITY_DUB_REF_ID = "capability:dub"
CAPABILITY_PACK_REF_ID = "capability:pack"

ARTIFACT_LOOKUP_UNRESOLVED = "artifact_lookup_unresolved"

# Per Plan C amendment to docs/contracts/factory_delivery_contract_v1.md
# §"Scene-Pack Non-Blocking Rule": every line MUST emit the scene_pack
# deliverable row as required=false AND blocking_publish=false, independent
# of any capability_plan flag. The packet validator rejects any line that
# asserts blocking_publish=true on a scene_pack row.
SCENE_PACK_BLOCKING_ALLOWED = False

_VALID_PROVENANCE = ("current", "historical")
_CLOSED_REF_IDS = (
    VARIATION_REF_ID,
    SLOT_PACK_REF_ID,
    CAPABILITY_SUBTITLES_REF_ID,
    CAPABILITY_DUB_REF_ID,
    CAPABILITY_PACK_REF_ID,
)
_CAPABILITY_REF_IDS = (
    CAPABILITY_SUBTITLES_REF_ID,
    CAPABILITY_DUB_REF_ID,
    CAPABILITY_PACK_REF_ID,
)


def _line_ref(packet: Mapping[str, Any], ref_id: str) -> Mapping[str, Any]:
    for item in packet.get("line_specific_refs", []):
        if item.get("ref_id") == ref_id:
            return item
    return {}


def _capability_plan(packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    binding = dict(packet.get("binding") or {})
    return [
        {
            "kind": item.get("kind"),
            "mode": item.get("mode"),
            "required": bool(item.get("required", False)),
        }
        for item in binding.get("capability_plan", [])
    ]


def _capability_by_kind(
    capability_plan: Iterable[Mapping[str, Any]], kind: str
) -> Mapping[str, Any]:
    for item in capability_plan:
        if item.get("kind") == kind:
            return item
    return {}


def _ref_ids(packet: Mapping[str, Any], key: str) -> list[str]:
    return [item.get("ref_id") for item in packet.get(key, []) if item.get("ref_id")]


def _cell_slot_bindings(packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    variation_delta = dict(_line_ref(packet, VARIATION_REF_ID).get("delta") or {})
    slot_delta = dict(_line_ref(packet, SLOT_PACK_REF_ID).get("delta") or {})
    slots = {item.get("slot_id"): item for item in slot_delta.get("slots", [])}

    bindings: list[dict[str, Any]] = []
    for cell in variation_delta.get("cells", []):
        slot_id = cell.get("script_slot_ref")
        slot = dict(slots.get(slot_id) or {})
        language_scope = dict(slot.get("language_scope") or {})
        bindings.append(
            {
                "cell_id": cell.get("cell_id"),
                "script_slot_ref": slot_id,
                "slot_id": slot.get("slot_id"),
                "body_ref": slot.get("body_ref"),
                "source_language": language_scope.get("source_language"),
                "target_language": deepcopy(language_scope.get("target_language") or []),
            }
        )
    return bindings


def _is_valid_pair(ref_id: str, locator: Any) -> bool:
    if ref_id == VARIATION_REF_ID or ref_id == SLOT_PACK_REF_ID:
        return isinstance(locator, str) and bool(locator)
    if ref_id in _CAPABILITY_REF_IDS:
        return locator is None
    return False


def _resolve_handle(
    packet: Mapping[str, Any], ref_id: str, locator: Any
) -> Optional[str]:
    if ref_id == VARIATION_REF_ID:
        delta = dict(_line_ref(packet, VARIATION_REF_ID).get("delta") or {})
        for cell in delta.get("cells", []) or []:
            if cell.get("cell_id") == locator:
                handle = cell.get("script_slot_ref")
                return handle if isinstance(handle, str) and handle else None
        return None
    if ref_id == SLOT_PACK_REF_ID:
        delta = dict(_line_ref(packet, SLOT_PACK_REF_ID).get("delta") or {})
        for slot in delta.get("slots", []) or []:
            if slot.get("slot_id") == locator:
                handle = slot.get("body_ref")
                return handle if isinstance(handle, str) and handle else None
        return None
    if ref_id in _CAPABILITY_REF_IDS:
        kind = ref_id.split(":", 1)[1]
        capability = _capability_by_kind(_capability_plan(packet), kind)
        if not capability:
            return None
        deliverable_profile_ref = (
            packet.get("binding", {}).get("deliverable_profile_ref") or ""
        )
        if not isinstance(deliverable_profile_ref, str) or not deliverable_profile_ref:
            return None
        return f"{deliverable_profile_ref}::capability:{kind}"
    return None


def _read_l3_final_provenance(
    packet: Mapping[str, Any], ref_id: str, locator: Any
) -> Optional[str]:
    final_provenance = packet.get("final_provenance")
    if not isinstance(final_provenance, Mapping):
        return None
    row_provenance = final_provenance.get(ref_id)
    if isinstance(row_provenance, str):
        return row_provenance
    if isinstance(row_provenance, Mapping) and locator is not None:
        value = row_provenance.get(locator)
        return value if isinstance(value, str) else None
    return None


def _clamp_blocking_publish(*, required: bool, blocking_publish: bool) -> bool:
    """Enforce the validator invariant from ``factory_delivery_contract_v1.md``
    §"Per-Deliverable Required / Blocking Fields" — a row with ``required=false``
    MUST carry ``blocking_publish=false``. Defensive: clamps to False rather than
    relying on every caller to honour the rule.
    """

    return bool(blocking_publish) if bool(required) else False


def _derive_freshness(
    packet: Mapping[str, Any], ref_id: str, locator: Any
) -> str:
    final_fresh = packet.get("final_fresh")
    if not isinstance(final_fresh, Mapping):
        return "stale"
    row_fresh = final_fresh.get(ref_id)
    if isinstance(row_fresh, bool):
        return "fresh" if row_fresh else "stale"
    if isinstance(row_fresh, Mapping) and locator is not None:
        value = row_fresh.get(locator)
        if isinstance(value, bool):
            return "fresh" if value else "stale"
    return "stale"


def artifact_lookup(
    packet: Mapping[str, Any], ref_id: str, locator: Any = None
) -> Any:
    """Pure projection of packet truth → artifact handle for a deliverable row.

    Returns either an ``ArtifactHandle`` mapping
    ``{"artifact_ref", "freshness", "provenance"}`` or the contract sentinel
    string ``artifact_lookup_unresolved``. Never raises, never fabricates,
    never performs I/O, never mutates the packet.

    Contract: ``docs/contracts/matrix_script/result_packet_binding_artifact_lookup_contract_v1.md``.
    """
    if not isinstance(packet, Mapping):
        return ARTIFACT_LOOKUP_UNRESOLVED
    if ref_id not in _CLOSED_REF_IDS:
        return ARTIFACT_LOOKUP_UNRESOLVED
    if not _is_valid_pair(ref_id, locator):
        return ARTIFACT_LOOKUP_UNRESOLVED

    handle = _resolve_handle(packet, ref_id, locator)
    if not isinstance(handle, str) or not handle:
        return ARTIFACT_LOOKUP_UNRESOLVED

    provenance = _read_l3_final_provenance(packet, ref_id, locator)
    if provenance not in _VALID_PROVENANCE:
        return ARTIFACT_LOOKUP_UNRESOLVED

    return {
        "artifact_ref": handle,
        "freshness": _derive_freshness(packet, ref_id, locator),
        "provenance": provenance,
    }


def project_delivery_binding(packet: Mapping[str, Any]) -> Dict[str, Any]:
    """Project packet truth into the Matrix Script Phase C delivery surface."""
    binding = dict(packet.get("binding") or {})
    evidence = dict(packet.get("evidence") or {})
    metadata = deepcopy(packet.get("metadata") or {})
    capabilities = _capability_plan(packet)
    subtitles = _capability_by_kind(capabilities, "subtitles")
    dub = _capability_by_kind(capabilities, "dub")
    pack = _capability_by_kind(capabilities, "pack")
    generic_refs = _ref_ids(packet, "generic_refs")
    line_specific_refs = _ref_ids(packet, "line_specific_refs")

    deliverable_profile_ref = binding.get("deliverable_profile_ref")
    asset_sink_profile_ref = binding.get("asset_sink_profile_ref")

    # Matrix Script line policy for the Plan C amendment fields per
    # factory_delivery_contract_v1.md §"Per-Deliverable Required / Blocking Fields":
    #
    # - variation_manifest / slot_bundle: structural deliverables; both required
    #   and blocking_publish are True (these are core Matrix Script outputs).
    # - subtitle_bundle / audio_preview: required follows the line capability
    #   plan; blocking_publish mirrors required for Matrix Script (when the
    #   capability is required, its absence blocks publish).
    # - scene_pack: HARDCODED required=False, blocking_publish=False per the
    #   §"Scene-Pack Non-Blocking Rule" (Plan C amendment) — independent of the
    #   pack capability flag. The validator invariant from the same contract
    #   ("required=false ⇒ blocking_publish=false") is enforced defensively by
    #   _clamp_blocking_publish on every row below.
    subtitles_required = bool(subtitles.get("required", False))
    dub_required = bool(dub.get("required", False))

    deliverables = [
        {
            "deliverable_id": "matrix_script_variation_manifest",
            "kind": "variation_manifest",
            "required": True,
            "blocking_publish": _clamp_blocking_publish(required=True, blocking_publish=True),
            "source_ref_id": VARIATION_REF_ID,
            "profile_ref": deliverable_profile_ref,
            "artifact_lookup": artifact_lookup(packet, VARIATION_REF_ID, None),
        },
        {
            "deliverable_id": "matrix_script_slot_bundle",
            "kind": "script_slot_bundle",
            "required": True,
            "blocking_publish": _clamp_blocking_publish(required=True, blocking_publish=True),
            "source_ref_id": SLOT_PACK_REF_ID,
            "profile_ref": deliverable_profile_ref,
            "artifact_lookup": artifact_lookup(packet, SLOT_PACK_REF_ID, None),
        },
        {
            "deliverable_id": "matrix_script_subtitle_bundle",
            "kind": "subtitle_bundle",
            "required": subtitles_required,
            "blocking_publish": _clamp_blocking_publish(
                required=subtitles_required, blocking_publish=subtitles_required
            ),
            "source_ref_id": SLOT_PACK_REF_ID,
            "profile_ref": deliverable_profile_ref,
            "artifact_lookup": artifact_lookup(packet, CAPABILITY_SUBTITLES_REF_ID, None),
        },
        {
            "deliverable_id": "matrix_script_audio_preview",
            "kind": "audio_preview",
            "required": dub_required,
            "blocking_publish": _clamp_blocking_publish(
                required=dub_required, blocking_publish=dub_required
            ),
            "source_ref_id": "capability:dub",
            "profile_ref": deliverable_profile_ref,
            "artifact_lookup": artifact_lookup(packet, CAPABILITY_DUB_REF_ID, None),
        },
        {
            # Scene-Pack Non-Blocking Rule (Plan C amendment): scene_pack is
            # always required=False AND blocking_publish=False, regardless of
            # the line's pack capability. Reading `pack` is intentionally
            # decoupled here — the row's zoning is owned by the contract, not
            # the per-task capability plan.
            "deliverable_id": "matrix_script_scene_pack",
            "kind": "scene_pack",
            "required": False,
            "blocking_publish": _clamp_blocking_publish(
                required=False, blocking_publish=SCENE_PACK_BLOCKING_ALLOWED
            ),
            "source_ref_id": "capability:pack",
            "profile_ref": deliverable_profile_ref,
            "artifact_lookup": artifact_lookup(packet, CAPABILITY_PACK_REF_ID, None),
        },
    ]

    binding_profile_refs = {
        "worker_profile_ref": binding.get("worker_profile_ref"),
        "deliverable_profile_ref": deliverable_profile_ref,
        "asset_sink_profile_ref": asset_sink_profile_ref,
    }

    return {
        "line_id": packet.get("line_id"),
        "packet_version": packet.get("packet_version"),
        "surface": "matrix_script_delivery_binding_v1",
        "delivery_pack": {
            "deliverable_profile_ref": deliverable_profile_ref,
            "asset_sink_profile_ref": asset_sink_profile_ref,
            "deliverables": deliverables,
        },
        "result_packet_binding": {
            "generic_refs": generic_refs,
            "line_specific_refs": line_specific_refs,
            "binding_profile_refs": binding_profile_refs,
            "capability_plan": capabilities,
            "cell_slot_bindings": _cell_slot_bindings(packet),
        },
        "manifest": {
            "manifest_id": "matrix_script_delivery_manifest_v1",
            "line_id": packet.get("line_id"),
            "packet_version": packet.get("packet_version"),
            "deliverable_profile_ref": deliverable_profile_ref,
            "asset_sink_profile_ref": asset_sink_profile_ref,
            "source_refs": {
                "generic": generic_refs,
                "line_specific": line_specific_refs,
            },
            "metadata": metadata,
            "validator_report_path": evidence.get("validator_report_path"),
            "packet_ready_state": evidence.get("ready_state"),
            "write_policy": "read_only_phase_c",
        },
        "metadata_projection": {
            "line_id": packet.get("line_id"),
            "packet_version": packet.get("packet_version"),
            "metadata": metadata,
            "display_only": True,
        },
        "phase_d_deferred": [
            "variation_id_feedback",
            "publish_url",
            "publish_status",
            "channel_metrics",
            "operator_publish_notes",
            "feedback_closure_records",
        ],
    }
