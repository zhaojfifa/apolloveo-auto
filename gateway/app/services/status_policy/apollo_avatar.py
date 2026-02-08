from __future__ import annotations

from typing import Dict, Any

from .base import StatusPolicy


_FAILED_STATUSES = {"failed", "error"}


class ApolloAvatarStatusPolicy(StatusPolicy):
    """
    Apollo avatar status policy:
    - Any failure signal => status=failed
    - Publish deliverables ready => status=ready (and mark skipped steps)
    - Otherwise => status=running
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

        merged = dict(task or {})
        merged.update(updates or {})

        def _failed() -> bool:
            if merged.get("error_reason"):
                return True
            for key in ("subtitles_status", "dub_status", "scenes_status", "pack_status", "publish_status"):
                if str(merged.get(key) or "").lower() in _FAILED_STATUSES:
                    return True
            return False

        publish_ready = (
            str(merged.get("publish_status") or "").lower() == "ready"
            and bool(merged.get("publish_key") or merged.get("publish_url"))
        )

        u = dict(updates or {})
        if _failed():
            u["status"] = "failed"
            return u

        if publish_ready:
            u["status"] = "ready"
            u.setdefault("last_step", "publish")
            u["scenes_status"] = "skipped"
            u["subtitles_status"] = "skipped"
            u["dub_status"] = "skipped"
            u["pack_status"] = "skipped"
            u["publish_status"] = "ready"
            return u

        u["status"] = "running"
        return u
