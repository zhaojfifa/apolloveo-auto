from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import gateway.app.lines.hot_follow as _line_reg_hot_follow  # noqa: F401
from gateway.app.lines.base import LineRegistry, ProductionLine


@dataclass(frozen=True)
class LineRuntimeBinding:
    kind: str
    line: ProductionLine | None

    def to_payload(self) -> dict[str, Any]:
        if self.line is None:
            return {
                "bound": False,
                "task_kind": self.kind,
                "line_id": None,
                "hook_refs": {},
                "confirmation_policy": {},
            }
        payload = self.line.contract_metadata()
        payload["bound"] = True
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
