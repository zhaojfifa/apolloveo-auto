"""Production Line base contract and registry.

RFC-0001: Production Line Contract
"""
from __future__ import annotations

from dataclasses import dataclass
import importlib
from typing import Any, ClassVar


@dataclass(frozen=True)
class ProductionLine:
    """Immutable contract for a single ApolloVeo production line.

    Each line targets exactly one primary result (``target_result_type``) and
    maps 1:1 to a ``task.kind`` value in the database.  All references are
    relative paths from the repository root so they can be resolved by tooling
    without coupling to the runtime environment.
    """

    # --- Identity ---
    line_id: str
    """Stable identifier, e.g. "hot_follow_line".  Must be unique in the registry."""

    line_name: str
    """Human-readable name."""

    line_version: str
    """Semantic version of this line contract, e.g. "1.9.0"."""

    # --- Business contract ---
    target_result_type: str
    """Primary deliverable type.  Always "final_video" for v1.9/2.0 lines."""

    task_kind: str
    """Value of ``task.kind`` that this line handles, e.g. "hot_follow"."""

    # --- References (relative to repo root) ---
    input_contract_ref: str
    """Path to the runtime/input contract document for this line."""

    deliverable_profile_ref: str
    """Path to the deliverable profile reference for this line."""

    sop_profile_ref: str
    """Path to the SOP profile document for this line."""

    skills_bundle_ref: str
    """Path to the Skills bundle directory for this line."""

    worker_profile_ref: str
    """Path to the worker profile contract for this line."""

    asset_sink_profile_ref: str
    """Path to the asset sink profile reference for this line."""

    ready_gate_ref: str = ""
    """Path to the ready-gate spec source for this line."""

    status_policy_ref: str = ""
    """Path to the status policy entrypoint for this line."""

    # --- Deliverable policy ---
    deliverable_kinds: tuple[str, ...] = (
        "final_video",
        "subtitle",
        "audio",
        "pack",
    )
    """Ordered list of deliverable kinds produced by this line."""

    # --- Sink / confirmation policy ---
    auto_sink_enabled: bool = True
    """Whether results are automatically sunk to the asset store."""

    confirmation_before_execute: bool = False
    """Whether a human confirmation gate is required before execute."""

    confirmation_before_result_accept: bool = False
    """Whether a human confirmation gate is required before result accept."""

    confirmation_before_publish: bool = True
    """Whether a human confirmation gate is required before publish."""

    confirmation_before_retry: bool = False
    """Whether a human confirmation gate is required before retry."""

    def confirmation_policy(self) -> dict[str, bool]:
        return {
            "before_execute": bool(self.confirmation_before_execute),
            "before_result_accept": bool(self.confirmation_before_result_accept),
            "before_publish": bool(self.confirmation_before_publish),
            "before_retry": bool(self.confirmation_before_retry),
        }

    def contract_metadata(self) -> dict[str, Any]:
        return {
            "line_id": self.line_id,
            "line_name": self.line_name,
            "line_version": self.line_version,
            "task_kind": self.task_kind,
            "target_result_type": self.target_result_type,
            "input_contract_ref": self.input_contract_ref or None,
            "deliverable_profile_ref": self.deliverable_profile_ref or None,
            "sop_profile_ref": self.sop_profile_ref or None,
            "skills_bundle_ref": self.skills_bundle_ref or None,
            "worker_profile_ref": self.worker_profile_ref or None,
            "asset_sink_profile_ref": self.asset_sink_profile_ref or None,
            "ready_gate_ref": self.ready_gate_ref or None,
            "status_policy_ref": self.status_policy_ref or None,
            "deliverable_kinds": list(self.deliverable_kinds),
            "auto_sink_enabled": bool(self.auto_sink_enabled),
            "confirmation_policy": self.confirmation_policy(),
            "hook_refs": {
                "skills_bundle_ref": self.skills_bundle_ref or None,
                "worker_profile_ref": self.worker_profile_ref or None,
                "ready_gate_ref": self.ready_gate_ref or None,
                "status_policy_ref": self.status_policy_ref or None,
            },
        }


class LineRegistry:
    """Class-level registry mapping line_id → ProductionLine.

    Lines self-register at module import time by calling
    ``LineRegistry.register(line)``.  The registry is process-global and
    intentionally simple — no persistence, no concurrency concerns.
    """

    _lines: ClassVar[dict[str, ProductionLine]] = {}
    _by_kind: ClassVar[dict[str, ProductionLine]] = {}

    @classmethod
    def _ensure_default_lines_loaded(cls) -> None:
        if cls._lines or cls._by_kind:
            return
        importlib.import_module("gateway.app.lines")

    @classmethod
    def register(cls, line: ProductionLine) -> ProductionLine:
        """Register *line* and return it (supports one-liner module-level assignment)."""
        cls._lines[line.line_id] = line
        cls._by_kind[line.task_kind] = line
        return line

    @classmethod
    def get(cls, line_id: str) -> ProductionLine | None:
        """Look up a line by its stable ``line_id``."""
        cls._ensure_default_lines_loaded()
        return cls._lines.get(line_id)

    @classmethod
    def for_kind(cls, task_kind: str) -> ProductionLine | None:
        """Look up a line by the ``task.kind`` field value."""
        cls._ensure_default_lines_loaded()
        return cls._by_kind.get(task_kind)

    @classmethod
    def all(cls) -> list[ProductionLine]:
        """Return all registered lines in registration order."""
        cls._ensure_default_lines_loaded()
        return list(cls._lines.values())
