"""Factory packet envelope dataclasses.

Mirrors `docs/contracts/factory_packet_envelope_contract_v1.md`.
Read-only — no L1/L2/L3/L4 state writes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class FieldRef:
    path: str


@dataclass(frozen=True)
class Violation:
    rule_id: str
    field_path: str
    reason: str


@dataclass(frozen=True)
class Advisory:
    code: str
    field_path: str
    note: str


@dataclass
class PacketValidationReport:
    ok: bool
    missing: list[FieldRef] = field(default_factory=list)
    violations: list[Violation] = field(default_factory=list)
    advisories: list[Advisory] = field(default_factory=list)
    rule_versions: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "missing": [{"path": m.path} for m in self.missing],
            "violations": [
                {"rule_id": v.rule_id, "field_path": v.field_path, "reason": v.reason}
                for v in self.violations
            ],
            "advisories": [
                {"code": a.code, "field_path": a.field_path, "note": a.note}
                for a in self.advisories
            ],
            "rule_versions": dict(self.rule_versions),
        }
