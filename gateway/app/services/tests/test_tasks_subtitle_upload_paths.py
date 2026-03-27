from __future__ import annotations

from pathlib import Path

from gateway.app.routers import tasks as tasks_router


class _Repo:
    def __init__(self, task: dict):
        self.task = dict(task)

    def get(self, task_id: str):
        if task_id == self.task.get("task_id"):
            return dict(self.task)
        return None


class _FakeWorkspace:
    def __init__(self, base: Path, task_id: str, target_lang: str | None = None):
        self.base_dir = base / task_id
        self.subtitles_dir = self.base_dir / "subs"
        self.subtitles_dir.mkdir(parents=True, exist_ok=True)
        self.origin_srt_path = self.subtitles_dir / "origin.srt"
        suffix = "vi.srt" if str(target_lang or "").strip().lower() == "vi" else "mm.srt"
        self.mm_srt_path = self.subtitles_dir / suffix


def test_upload_target_subtitle_artifacts_uses_vi_filenames(monkeypatch, tmp_path):
    uploads: list[str] = []
    workspace = _FakeWorkspace(tmp_path, "hf-vi-up", "vi")
    workspace.origin_srt_path.write_text("origin", encoding="utf-8")
    workspace.mm_srt_path.write_text("translated", encoding="utf-8")
    workspace.mm_srt_path.with_suffix(".txt").write_text("translated", encoding="utf-8")

    monkeypatch.setattr(tasks_router, "Workspace", lambda task_id, target_lang=None: _FakeWorkspace(tmp_path, task_id, target_lang))
    monkeypatch.setattr(
        tasks_router,
        "upload_task_artifact",
        lambda _task, _path, artifact_name, task_id=None: uploads.append(artifact_name) or f"deliver/tasks/{task_id}/{artifact_name}",
    )

    origin_key, target_key = tasks_router._upload_target_subtitle_artifacts(
        {"task_id": "hf-vi-up", "content_lang": "vi"},
        "hf-vi-up",
        "vi",
    )

    assert origin_key == "deliver/tasks/hf-vi-up/origin.srt"
    assert target_key == "deliver/tasks/hf-vi-up/vi.srt"
    assert uploads == ["origin.srt", "vi.srt", "vi.txt"]


def test_run_subtitles_job_persists_vi_target_artifact_path(monkeypatch, tmp_path):
    policy_updates: list[dict] = []
    repo = _Repo({"task_id": "hf-vi-job", "content_lang": "vi", "target_lang": "vi"})

    monkeypatch.setattr(tasks_router, "run_subtitles_step_entry", lambda **_kwargs: None)
    monkeypatch.setattr(tasks_router.asyncio, "run", lambda result: result)
    monkeypatch.setattr(tasks_router, "Workspace", lambda task_id, target_lang=None: _FakeWorkspace(tmp_path, task_id, target_lang))
    monkeypatch.setattr(tasks_router, "_task_to_detail", lambda task: task)
    monkeypatch.setattr(
        tasks_router,
        "upload_task_artifact",
        lambda _task, _path, artifact_name, task_id=None: f"deliver/tasks/{task_id}/{artifact_name}",
    )
    monkeypatch.setattr(tasks_router, "_policy_upsert", lambda _repo, _task_id, payload, **_kwargs: policy_updates.append(dict(payload)))

    workspace = _FakeWorkspace(tmp_path, "hf-vi-job", "vi")
    workspace.origin_srt_path.write_text("origin", encoding="utf-8")
    workspace.mm_srt_path.write_text("translated", encoding="utf-8")
    workspace.mm_srt_path.with_suffix(".txt").write_text("translated", encoding="utf-8")

    tasks_router._run_subtitles_job(
        task_id="hf-vi-job",
        target_lang="vi",
        force=False,
        translate=True,
        repo=repo,
    )

    assert policy_updates[-1]["origin_srt_path"] == "deliver/tasks/hf-vi-job/origin.srt"
    assert policy_updates[-1]["mm_srt_path"] == "deliver/tasks/hf-vi-job/vi.srt"
