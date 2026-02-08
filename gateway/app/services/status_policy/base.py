from __future__ import annotations

from typing import Dict, Any

from .utils import coerce_final_status


class StatusPolicy:
    """
    Default no-op policy. Subclasses can adjust updates to prevent status regression.
    """

    def reconcile_after_step(
        self,
        task: Dict[str, Any],
        *,
        step: str,
        updates: Dict[str, Any],
        force: bool = False,
    ) -> Dict[str, Any]:
        del step
        del force
        kind = getattr(self, "kind", None)
        return coerce_final_status(kind, task, updates or {})

