import asyncio
import inspect

from gateway.app.services import task_router_actions
from gateway.app.services.task_router_actions import (
    TaskRouterActionPorts,
    create_task_entry,
    register_task_router_action_ports,
    rerun_dub_entry,
    run_task_pipeline_entry,
)


def test_task_router_actions_do_not_lazy_import_router_modules():
    source = inspect.getsource(task_router_actions)

    assert "from gateway.app.routers" + ".tasks import" not in source
    assert "importlib.import_module" not in source


def test_task_router_action_entries_use_registered_ports():
    original_ports = task_router_actions._ports
    calls = []

    async def _rerun_dub(task_id, payload, background_tasks, repo):
        calls.append(("dub", task_id, payload, background_tasks, repo))
        return {"queued": True}

    try:
        register_task_router_action_ports(
            TaskRouterActionPorts(
                create_task=lambda payload, background_tasks, repo: calls.append(
                    ("create", payload, background_tasks, repo)
                )
                or {"task_id": "created"},
                run_task_pipeline=lambda task_id, background_tasks, repo: calls.append(
                    ("run", task_id, background_tasks, repo)
                )
                or {"queued": True},
                rerun_dub=_rerun_dub,
            )
        )

        assert create_task_entry({"kind": "hot_follow"}, "bg", "repo") == {"task_id": "created"}
        assert run_task_pipeline_entry("task-1", "bg", "repo") == {"queued": True}
        assert asyncio.run(rerun_dub_entry("task-1", {"voice": "v"}, "bg", "repo")) == {"queued": True}
        assert calls == [
            ("create", {"kind": "hot_follow"}, "bg", "repo"),
            ("run", "task-1", "bg", "repo"),
            ("dub", "task-1", {"voice": "v"}, "bg", "repo"),
        ]
    finally:
        task_router_actions._ports = original_ports
