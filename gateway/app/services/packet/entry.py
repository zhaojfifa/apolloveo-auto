"""Packet validation entry helpers.

Thin, read-only adapters that turn an incoming dict / JSON file into a
``PacketEnvelope`` and dispatch it through the validator. Designed so
Matrix Script and Digital Anchor packet schemas can be plugged in cleanly
once Product delivers them — no business logic, no truth writes, no
runtime orchestration.

Authority:
- ``docs/contracts/factory_packet_envelope_contract_v1.md`` (envelope shape)
- ``docs/contracts/factory_packet_validator_rules_v1.md`` (R1..R5 rules)

Non-responsibilities:
- Does not derive runtime task readiness (four-layer state owns that).
- Does not mutate the input dict or the produced envelope.
- Does not call out to donor/provider modules.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping, Optional

from .envelope import (
    Binding,
    CapabilityPlanItem,
    Evidence,
    GenericRef,
    LineSpecificRef,
    PacketEnvelope,
    PacketValidationReport,
)
from .validator import validate_packet


def envelope_from_dict(payload: Mapping[str, Any]) -> PacketEnvelope:
    """Build a ``PacketEnvelope`` from a plain dict (e.g. parsed JSON).

    Unknown / extra keys at the top level are ignored deliberately so the
    helper stays forward-compatible while the line packet schemas land.
    Required fields raise ``KeyError`` with the missing path so callers can
    surface a clean error instead of a silent default.
    """
    def _need(d: Mapping[str, Any], key: str, where: str) -> Any:
        if key not in d:
            raise KeyError(f"{where}.{key}")
        return d[key]

    generic_refs = tuple(
        GenericRef(
            ref_id=_need(r, "ref_id", f"generic_refs[{i}]"),
            path=_need(r, "path", f"generic_refs[{i}]"),
            version=_need(r, "version", f"generic_refs[{i}]"),
        )
        for i, r in enumerate(payload.get("generic_refs", ()))
    )
    line_specific_refs = tuple(
        LineSpecificRef(
            ref_id=_need(r, "ref_id", f"line_specific_refs[{i}]"),
            path=_need(r, "path", f"line_specific_refs[{i}]"),
            version=_need(r, "version", f"line_specific_refs[{i}]"),
            binds_to=tuple(r.get("binds_to", ())),
        )
        for i, r in enumerate(payload.get("line_specific_refs", ()))
    )

    binding_raw = _need(payload, "binding", "")
    capability_plan = tuple(
        CapabilityPlanItem(
            kind=_need(c, "kind", f"binding.capability_plan[{i}]"),
            mode=c.get("mode"),
            inputs=c.get("inputs"),
            outputs=c.get("outputs"),
            quality_hint=c.get("quality_hint"),
            language_hint=c.get("language_hint"),
            extras={
                k: v
                for k, v in c.items()
                if k
                not in {
                    "kind",
                    "mode",
                    "inputs",
                    "outputs",
                    "quality_hint",
                    "language_hint",
                }
            },
        )
        for i, c in enumerate(binding_raw.get("capability_plan", ()))
    )
    binding = Binding(
        worker_profile_ref=_need(binding_raw, "worker_profile_ref", "binding"),
        deliverable_profile_ref=_need(
            binding_raw, "deliverable_profile_ref", "binding"
        ),
        asset_sink_profile_ref=_need(
            binding_raw, "asset_sink_profile_ref", "binding"
        ),
        capability_plan=capability_plan,
    )

    evidence_raw = _need(payload, "evidence", "")
    evidence = Evidence(
        reference_line=_need(evidence_raw, "reference_line", "evidence"),
        reference_evidence_path=_need(
            evidence_raw, "reference_evidence_path", "evidence"
        ),
        validator_report_path=evidence_raw.get("validator_report_path"),
        ready_state=_need(evidence_raw, "ready_state", "evidence"),
    )

    return PacketEnvelope(
        line_id=_need(payload, "line_id", ""),
        packet_version=_need(payload, "packet_version", ""),
        generic_refs=generic_refs,
        line_specific_refs=line_specific_refs,
        binding=binding,
        evidence=evidence,
        metadata=dict(payload.get("metadata", {})),
        line_specific_objects=dict(payload.get("line_specific_objects", {})),
    )


def validate_packet_dict(
    payload: Mapping[str, Any],
    *,
    repo_root: Optional[os.PathLike] = None,
    schema_path: Optional[os.PathLike] = None,
) -> PacketValidationReport:
    """Validate a packet given as a dict. Builds the envelope and dispatches."""
    envelope = envelope_from_dict(payload)
    return validate_packet(envelope, repo_root=repo_root, schema_path=schema_path)


def validate_packet_path(
    instance_path: os.PathLike,
    *,
    repo_root: Optional[os.PathLike] = None,
    schema_path: Optional[os.PathLike] = None,
) -> PacketValidationReport:
    """Validate a packet from a JSON instance file on disk."""
    payload = json.loads(Path(instance_path).read_text())
    return validate_packet_dict(
        payload, repo_root=repo_root, schema_path=schema_path
    )


__all__ = [
    "envelope_from_dict",
    "validate_packet_dict",
    "validate_packet_path",
]
