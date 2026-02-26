from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[5]))

from gateway.app.services.status_policy.utils import (
    apply_monotonic_step_policy,
    normalize_task_steps_for_read,
)


def test_status_cannot_downgrade_after_done():
    task = {"compose_status": "done", "final_video_key": "deliver/tasks/t1/final.mp4"}
    updates = {"compose_status": "running"}
    out = apply_monotonic_step_policy(task, updates, force=False)
    assert out["compose_status"] == "done"


def test_normalize_done_when_key_exists_even_if_status_queued():
    payload = {"compose_status": "queued", "final_video_key": "deliver/tasks/t1/final.mp4"}
    out = normalize_task_steps_for_read(payload)
    assert out["compose_status"] == "done"


def test_normalize_failed_when_error_exists():
    payload = {"compose_status": "running", "compose_error": {"reason": "x"}}
    out = normalize_task_steps_for_read(payload)
    assert out["compose_status"] == "failed"
