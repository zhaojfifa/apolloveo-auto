"""Factory packet envelope dataclasses.

Mirrors `docs/contracts/factory_packet_envelope_contract_v1.md`.

Read-only data shapes. No L1/L2/L3/L4 truth writes. No runtime orchestration.
Consumed by `validator.py` and (later) `onboarding_gate.py`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence

# Closed sets owned by factory_packet_validator_rules_v1 (R3, R5).
CAPABILITY_KINDS: frozenset = frozenset({
    "understanding",
    "subtitles",
    "dub",
    "video_gen",
    "avatar",
    "face_swap",
    "post_production",
    "pack",
    "variation",
    "speaker",
    "lip_sync",
})

FORBIDDEN_STATE_FIELDS: frozenset = frozenset({
    "status",
    "state",
    "phase",
    "stage_status",
    "ready",
    "is_ready",
    "ready_gate",
    "done",
    "completed",
    "finished",
    "current_attempt",
    "attempt_state",
    "step_status",
    "pipeline_status",
    "publishable",
    "is_publishable",
    "delivery_ready",
    "final_ready",
    # NOTE: `ready_state` is permitted ONLY at envelope.evidence.ready_state per E4 / R5 exception.
})

KNOWN_VENDOR_TOKENS: frozenset = frozenset({
    "akool",
    "fal",
    "kling",
    "wan",
    "azure",
    "gemini",
    "openai",
    "whisper",
    "fastwhisper",
    "faster-whisper",
    "elevenlabs",
    "runway",
})

PERMITTED_READY_STATES: frozenset = frozenset({"draft", "validating", "ready", "gated", "frozen"})


@dataclass(frozen=True)
class GenericRef:
    ref_id: str
    path: str
    version: str


@dataclass(frozen=True)
class LineSpecificRef:
    ref_id: str
    path: str
    version: str
    binds_to: Sequence[str] = ()


@dataclass(frozen=True)
class CapabilityPlanItem:
    kind: str
    mode: Optional[str] = None
    inputs: Optional[Mapping[str, Any]] = None
    outputs: Optional[Mapping[str, Any]] = None
    quality_hint: Optional[str] = None
    language_hint: Optional[str] = None
    extras: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Binding:
    worker_profile_ref: str
    deliverable_profile_ref: str
    asset_sink_profile_ref: str
    capability_plan: Sequence[CapabilityPlanItem] = ()


@dataclass(frozen=True)
class Evidence:
    reference_line: str
    reference_evidence_path: str
    validator_report_path: Optional[str]
    ready_state: str  # one of PERMITTED_READY_STATES


@dataclass(frozen=True)
class PacketEnvelope:
    line_id: str
    packet_version: str
    generic_refs: Sequence[GenericRef]
    line_specific_refs: Sequence[LineSpecificRef]
    binding: Binding
    evidence: Evidence
    metadata: Mapping[str, Any] = field(default_factory=dict)
    # Line-specific objects (the increments that ride alongside the envelope) live
    # outside the envelope as a payload dict; the validator inspects them through
    # `line_specific_objects` for R2 duplication detection.
    line_specific_objects: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)


# ---- Validator output shapes ----


@dataclass(frozen=True)
class FieldRef:
    path: str  # JSON-pointer-ish dotted path (e.g. "binding.capability_plan[0].kind")


@dataclass(frozen=True)
class Violation:
    rule_id: str  # e.g. "R3.vendor-leak", "E2"
    field: FieldRef
    reason: str


@dataclass(frozen=True)
class Advisory:
    code: str
    field: FieldRef
    note: str


@dataclass(frozen=True)
class PacketValidationReport:
    ok: bool
    missing: List[FieldRef]
    violations: List[Violation]
    advisories: List[Advisory]
    rule_versions: Dict[str, str]


__all__ = [
    "CAPABILITY_KINDS",
    "FORBIDDEN_STATE_FIELDS",
    "KNOWN_VENDOR_TOKENS",
    "PERMITTED_READY_STATES",
    "GenericRef",
    "LineSpecificRef",
    "CapabilityPlanItem",
    "Binding",
    "Evidence",
    "PacketEnvelope",
    "FieldRef",
    "Violation",
    "Advisory",
    "PacketValidationReport",
]
