from __future__ import annotations

from datetime import datetime, timedelta, timezone

from gateway.app.services.compose_service import (
    CompositionService,
    HotFollowComposeRequestContract,
)


class _Repo:
    def __init__(self, task: dict):
        self.task = dict(task)

    def get(self, task_id: str):
        if str(self.task.get("task_id")) == str(task_id):
            return dict(self.task)
        return None


def _policy_upsert(repo: _Repo, task_id: str, updates: dict):
    assert repo.task["task_id"] == task_id
    repo.task.update(updates)


def test_service_direct_compose_entry_returns_success_without_router(monkeypatch):
    monkeypatch.setenv("HF_LIPSYNC_ENABLED", "1")
    repo = _Repo(
        {
            "task_id": "hf-compose-1",
            "kind": "hot_follow",
            "content_lang": "mm",
            "target_lang": "mm",
            "config": {},
            "compose_plan": {"overlay_subtitles": True},
            "scene_outputs": [],
        }
    )
    svc = CompositionService(storage=object(), settings=object())

    result = svc.run_hot_follow_compose(
        "hf-compose-1",
        repo.get("hf-compose-1"),
        HotFollowComposeRequestContract(
            bgm_mix=0.5,
            overlay_subtitles=False,
            freeze_tail_enabled=True,
            force=False,
        ),
        repo=repo,
        policy_upsert=_policy_upsert,
        hub_loader=lambda task_id, _repo: {"task_id": task_id, "kind": "hot_follow"},
        subtitle_resolver=lambda *_args, **_kwargs: None,
        subtitle_only_check=lambda *_args, **_kwargs: False,
        revision_snapshot=lambda _task: {},
        lipsync_runner=lambda _task_id, enabled: "lipsync-warning" if enabled else None,
        object_exists_fn=lambda _key: False,
        object_head_fn=lambda _key: None,
        media_meta_from_head_fn=lambda _head: (0, None),
        compose_runner=lambda _task_id, _task: {
            "final_video_key": "deliver/tasks/hf-compose-1/final.mp4",
            "final_video_path": "deliver/tasks/hf-compose-1/final.mp4",
            "compose_status": "done",
            "compose_warning": "inner-warning",
        },
    )

    assert result.status_code == 200
    assert result.body["task_id"] == "hf-compose-1"
    assert result.body["final_key"] == "deliver/tasks/hf-compose-1/final.mp4"
    assert result.body["compose_status"] == "done"
    assert result.body["hub"]["kind"] == "hot_follow"
    assert repo.task["compose_status"] == "done"
    assert repo.task["compose_plan"]["freeze_tail_enabled"] is True
    assert repo.task["config"]["bgm"]["mix_ratio"] == 0.5
    assert repo.task["compose_warning"] == "inner-warning lipsync-warning"


def test_service_direct_compose_entry_returns_in_progress_when_lock_active():
    repo = _Repo(
        {
            "task_id": "hf-compose-locked",
            "compose_lock_until": (datetime.now(timezone.utc) + timedelta(seconds=30)).isoformat(),
        }
    )
    svc = CompositionService(storage=object(), settings=object())

    result = svc.run_hot_follow_compose(
        "hf-compose-locked",
        repo.get("hf-compose-locked"),
        HotFollowComposeRequestContract(),
        repo=repo,
        policy_upsert=_policy_upsert,
        hub_loader=lambda *_args, **_kwargs: {},
        subtitle_resolver=lambda *_args, **_kwargs: None,
        subtitle_only_check=lambda *_args, **_kwargs: False,
    )

    assert result.status_code == 409
    assert result.body["error"] == "compose_in_progress"
    assert result.body["task_id"] == "hf-compose-locked"
