"""Registered task action ports.

This module is a transitional port surface for actions that still have their
primary implementation in the task router. It must not import router modules.
Routers register explicit callables at import time, and Hot Follow routes call
these service-level entries without hidden lazy router imports.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable


CreateTaskAction = Callable[[Any, Any, Any], Any]
RunTaskPipelineAction = Callable[[str, Any, Any], Any]
RerunDubAction = Callable[[str, Any, Any, Any], Awaitable[Any]]


@dataclass(frozen=True)
class TaskRouterActionPorts:
    create_task: CreateTaskAction
    run_task_pipeline: RunTaskPipelineAction
    rerun_dub: RerunDubAction


_ports: TaskRouterActionPorts | None = None


def register_task_router_action_ports(ports: TaskRouterActionPorts) -> None:
    global _ports
    _ports = ports


def _registered_ports() -> TaskRouterActionPorts:
    if _ports is None:
        raise RuntimeError("task router action ports are not registered")
    return _ports


def create_task_entry(payload, background_tasks, repo):
    return _registered_ports().create_task(payload, background_tasks, repo)


def run_task_pipeline_entry(task_id: str, background_tasks, repo):
    return _registered_ports().run_task_pipeline(task_id, background_tasks, repo)


async def rerun_dub_entry(task_id: str, payload, background_tasks, repo):
    return await _registered_ports().rerun_dub(task_id, payload, background_tasks, repo)
