from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

import gateway.app.lines.hot_follow as _line_reg_hot_follow  # noqa: F401
from gateway.app.lines.base import LineRegistry, ProductionLine
from gateway.app.services.skills_runtime import load_line_skills_bundle


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _resolve_repo_path(ref: str | None) -> Path | None:
    text = str(ref or "").strip()
    if not text:
        return None
    return (_repo_root() / text).resolve()


@dataclass(frozen=True)
class RuntimeBoundReference:
    ref: str | None
    kind: str
    consumed: bool
    exists: bool
    details: dict[str, Any]

    def to_payload(self) -> dict[str, Any]:
        return {
            "ref": self.ref,
            "kind": self.kind,
            "consumed": bool(self.consumed),
            "exists": bool(self.exists),
            "details": dict(self.details or {}),
        }


@dataclass(frozen=True)
class LineRuntimeReferences:
    line_registry: RuntimeBoundReference
    skills_bundle: RuntimeBoundReference
    worker_profile: RuntimeBoundReference
    deliverable_profile: RuntimeBoundReference
    asset_sink_profile: RuntimeBoundReference

    def to_payload(self) -> dict[str, Any]:
        return {
            "line_registry": self.line_registry.to_payload(),
            "skills_bundle": self.skills_bundle.to_payload(),
            "worker_profile": self.worker_profile.to_payload(),
            "deliverable_profile": self.deliverable_profile.to_payload(),
            "asset_sink_profile": self.asset_sink_profile.to_payload(),
        }


def _missing_reference(kind: str, ref: str | None) -> RuntimeBoundReference:
    return RuntimeBoundReference(
        ref=ref or None,
        kind=kind,
        consumed=False,
        exists=False,
        details={},
    )


def _line_registry_reference(line: ProductionLine | None) -> RuntimeBoundReference:
    return RuntimeBoundReference(
        ref="gateway.app.lines.base.LineRegistry",
        kind="line_registry",
        consumed=line is not None,
        exists=True,
        details={
            "line_id": getattr(line, "line_id", None),
            "task_kind": getattr(line, "task_kind", None),
        },
    )


def _skills_bundle_reference(line: ProductionLine | None) -> RuntimeBoundReference:
    ref = getattr(line, "skills_bundle_ref", None)
    if line is None or not ref:
        return _missing_reference("skills_bundle", ref)
    bundle = load_line_skills_bundle(line)
    return RuntimeBoundReference(
        ref=ref,
        kind="skills_bundle",
        consumed=bundle is not None,
        exists=_resolve_repo_path(ref).is_dir() if _resolve_repo_path(ref) else False,
        details={
            "bundle_id": getattr(bundle, "bundle_id", None),
            "line_id": getattr(bundle, "line_id", None),
            "hook_kind": getattr(bundle, "hook_kind", None),
            "stage_order": list(getattr(bundle, "stage_order", ()) or ()),
        },
    )


def _worker_profile_reference(line: ProductionLine | None) -> RuntimeBoundReference:
    ref = getattr(line, "worker_profile_ref", None)
    path = _resolve_repo_path(ref)
    return RuntimeBoundReference(
        ref=ref or None,
        kind="worker_profile",
        consumed=bool(line and ref and path and path.exists()),
        exists=bool(path and path.exists()),
        details={
            "line_id": getattr(line, "line_id", None),
            "worker_profile_ref": ref,
        },
    )


def _deliverable_profile_reference(line: ProductionLine | None) -> RuntimeBoundReference:
    ref = getattr(line, "deliverable_profile_ref", None)
    path = _resolve_repo_path(ref)
    details: dict[str, Any] = {
        "line_id": getattr(line, "line_id", None),
        "deliverable_kinds": list(getattr(line, "deliverable_kinds", ()) or ()),
    }
    consumed = False
    exists = bool(path and path.exists())
    if path and path.exists():
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        deliverables = data.get("deliverables") if isinstance(data, dict) else {}
        primary = deliverables.get("primary") if isinstance(deliverables, dict) else {}
        secondary = deliverables.get("secondary") if isinstance(deliverables, dict) else []
        details.update(
            {
                "primary_kind": primary.get("kind") if isinstance(primary, dict) else None,
                "secondary_kinds": [
                    item.get("kind")
                    for item in secondary
                    if isinstance(item, dict) and item.get("kind")
                ],
            }
        )
        consumed = True
    return RuntimeBoundReference(
        ref=ref or None,
        kind="deliverable_profile",
        consumed=consumed,
        exists=exists,
        details=details,
    )


def _asset_sink_profile_reference(line: ProductionLine | None) -> RuntimeBoundReference:
    ref = getattr(line, "asset_sink_profile_ref", None)
    path = _resolve_repo_path(ref)
    return RuntimeBoundReference(
        ref=ref or None,
        kind="asset_sink_profile",
        consumed=bool(line and ref and path and path.exists()),
        exists=bool(path and path.exists()),
        details={
            "line_id": getattr(line, "line_id", None),
            "auto_sink_enabled": bool(getattr(line, "auto_sink_enabled", False)),
            "asset_sink_profile_ref": ref,
        },
    )


def resolve_line_runtime_references(line: ProductionLine | None) -> LineRuntimeReferences:
    return LineRuntimeReferences(
        line_registry=_line_registry_reference(line),
        skills_bundle=_skills_bundle_reference(line),
        worker_profile=_worker_profile_reference(line),
        deliverable_profile=_deliverable_profile_reference(line),
        asset_sink_profile=_asset_sink_profile_reference(line),
    )


@dataclass(frozen=True)
class LineRuntimeBinding:
    kind: str
    line: ProductionLine | None

    @property
    def runtime_refs(self) -> LineRuntimeReferences:
        return resolve_line_runtime_references(self.line)

    def to_payload(self) -> dict[str, Any]:
        if self.line is None:
            return {
                "bound": False,
                "task_kind": self.kind,
                "line_id": None,
                "hook_refs": {},
                "runtime_refs": self.runtime_refs.to_payload(),
                "confirmation_policy": {},
            }
        payload = self.line.contract_metadata()
        payload["bound"] = True
        payload["runtime_refs"] = self.runtime_refs.to_payload()
        return payload


def _resolve_task_kind(task_or_kind: dict[str, Any] | str | None) -> str:
    if isinstance(task_or_kind, str):
        return str(task_or_kind or "").strip().lower()
    if not isinstance(task_or_kind, dict):
        return ""
    kind = (
        task_or_kind.get("kind")
        or task_or_kind.get("task_kind")
        or task_or_kind.get("category")
        or task_or_kind.get("category_key")
        or task_or_kind.get("platform")
    )
    return str(kind or "").strip().lower()


def get_line_runtime_binding(task_or_kind: dict[str, Any] | str | None) -> LineRuntimeBinding:
    kind = _resolve_task_kind(task_or_kind)
    return LineRuntimeBinding(kind=kind, line=LineRegistry.for_kind(kind))
