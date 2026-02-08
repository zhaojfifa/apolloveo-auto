from __future__ import annotations

from datetime import datetime
from typing import Any

from gateway.app.db import SessionLocal
from gateway.app.models import Task
from gateway.app.services.status_policy.service import policy_upsert


class TaskStateService:
    def __init__(
        self,
        *,
        repo: Any | None = None,
        session: Any | None = None,
        step: str = "services.task_state",
    ) -> None:
        self._repo = repo
        self._session = session
        self._step = step

    def set_pack_key(self, task_id: str, pack_key: str) -> None:
        self.update_fields(
            task_id,
            {
                "pack_key": pack_key,
                "pack_type": "capcut_v18" if pack_key else None,
                "pack_status": "ready" if pack_key else None,
            },
        )

    def set_publish_key(self, task_id: str, publish_key: str) -> None:
        self.update_fields(task_id, {"publish_key": publish_key})

    def set_status(self, task_id: str, status: str) -> None:
        self.update_fields(task_id, {"status": status})

    def mark_step_done(self, task_id: str, step: str) -> None:
        self.update_fields(task_id, {"last_step": step})

    def update_fields(self, task_id: str, fields: dict) -> None:
        if not fields:
            return
        if self._repo is not None:
            policy_upsert(self._repo, task_id, None, fields, step=self._step)
            return

        db = self._session or SessionLocal()
        close_db = self._session is None
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                return
            for key, value in fields.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            if hasattr(task, "updated_at"):
                task.updated_at = datetime.utcnow()
            db.commit()
        finally:
            if close_db:
                db.close()
