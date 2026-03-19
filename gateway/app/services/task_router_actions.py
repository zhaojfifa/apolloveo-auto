"""Task router action bridge.

PR-2 routes Hot Follow task actions through this service entry so
``hot_follow_api.py`` no longer imports ``tasks.py`` directly.
"""

from __future__ import annotations


def create_task_entry(payload, background_tasks, repo):
    from gateway.app.routers.tasks import create_task

    return create_task(payload, background_tasks=background_tasks, repo=repo)


def run_task_pipeline_entry(task_id: str, background_tasks, repo):
    from gateway.app.routers.tasks import run_task_pipeline

    return run_task_pipeline(task_id, background_tasks=background_tasks, repo=repo)


async def rerun_dub_entry(task_id: str, payload, background_tasks, repo):
    from gateway.app.routers.tasks import rerun_dub

    return await rerun_dub(task_id, payload=payload, background_tasks=background_tasks, repo=repo)
