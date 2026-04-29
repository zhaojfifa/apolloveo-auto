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

    def upsert(self, task_id: str, updates: dict):
        if task_id != self.task.get("task_id"):
            return
        merged = dict(self.task)
        merged.update(dict(updates or {}))
        self.task = merged


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


def test_run_subtitles_job_delegates_subtitle_writeback_to_step_owner(monkeypatch, tmp_path):
    policy_updates: list[dict] = []
    repo = _Repo({"task_id": "hf-vi-job", "content_lang": "vi", "target_lang": "vi"})

    def _run_step(**_kwargs):
        repo.upsert(
            "hf-vi-job",
            {
                "origin_srt_path": "deliver/tasks/hf-vi-job/origin.srt",
                "mm_srt_path": "deliver/tasks/hf-vi-job/vi.srt",
                "subtitles_status": "ready",
            },
        )

    monkeypatch.setattr(tasks_router, "run_subtitles_step_entry", _run_step)
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

    result = tasks_router._run_subtitles_job(
        task_id="hf-vi-job",
        target_lang="vi",
        force=False,
        translate=True,
        repo=repo,
    )

    assert policy_updates == []
    assert result["origin_srt_path"] == "deliver/tasks/hf-vi-job/origin.srt"
    assert result["mm_srt_path"] == "deliver/tasks/hf-vi-job/vi.srt"


def test_run_pipeline_background_skips_link_parse_for_local_ingest_when_raw_ready(monkeypatch, tmp_path):
    task_id = "hf-local-parse"
    repo = _Repo(
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "category_key": "hot_follow",
            "platform": "local",
            "source_type": "local",
            "content_lang": "vi",
            "target_lang": "vi",
            "voice_id": "vi_female_1",
            "pipeline_config": {"ingest_mode": "local"},
            "raw_path": f"deliver/tasks/{task_id}/raw.mp4",
        }
    )
    parse_calls: list[dict] = []
    subtitles_calls: list[dict] = []

    raw_file = tmp_path / task_id / "raw" / "raw.mp4"
    raw_file.parent.mkdir(parents=True, exist_ok=True)
    raw_file.write_bytes(b"video")

    monkeypatch.setattr(tasks_router, "raw_path", lambda _task_id: raw_file)
    monkeypatch.setattr(
        tasks_router,
        "run_parse_step_v1",
        lambda req: parse_calls.append({"task_id": req.task_id, "link": req.link}) or {"duration_sec": 1},
    )
    monkeypatch.setattr(
        tasks_router,
        "run_subtitles_step_v1",
        lambda req: subtitles_calls.append({"task_id": req.task_id, "target_lang": req.target_lang}) or {},
    )
    monkeypatch.setattr(tasks_router.asyncio, "run", lambda result: result)
    monkeypatch.setattr(tasks_router, "upload_task_artifact", lambda _task, _path, artifact_name, task_id=None: f"deliver/tasks/{task_id}/{artifact_name}")
    monkeypatch.setattr(tasks_router, "probe_subtitles", lambda _path: {"subtitle_track_kind": "none"})
    monkeypatch.setattr(tasks_router, "_update_pipeline_probe", lambda _repo, _task_id, _probe: None)
    monkeypatch.setattr(tasks_router, "_upload_target_subtitle_artifacts", lambda _task, _task_id, _target_lang: ("deliver/tasks/hf-local-parse/origin.srt", "deliver/tasks/hf-local-parse/vi.srt"))
    monkeypatch.setattr(tasks_router, "run_dub_step_ssot", lambda _task: None)

    class _FakeWorkspace:
        def __init__(self, _task_id=None, target_lang=None):
            _ = (_task_id, target_lang)
            self.mm_audio_path = tmp_path / task_id / "audio" / "audio_vi.mp3"
            self.mm_audio_mp3_path = self.mm_audio_path
            self.mm_audio_path.parent.mkdir(parents=True, exist_ok=True)
            self.mm_audio_path.write_bytes(b"audio")

        def mm_audio_exists(self):
            return True

    monkeypatch.setattr(tasks_router, "Workspace", _FakeWorkspace)
    monkeypatch.setattr(tasks_router, "_ensure_mp3_audio", lambda audio_path, _mp3_path: audio_path)
    monkeypatch.setattr(tasks_router, "assert_local_audio_ok", lambda _path: (1024, 1.0))

    class _Storage:
        def upload_file(self, _path, key, content_type=None):
            _ = content_type
            return key

    monkeypatch.setattr(tasks_router, "get_storage_service", lambda: _Storage())
    monkeypatch.setattr(tasks_router, "deliver_key", lambda _task_id, filename: f"deliver/tasks/{_task_id}/{filename}")
    monkeypatch.setattr(tasks_router, "TaskStateService", lambda repo, step: type("S", (), {"update_fields": lambda self, task_id, updates: repo.upsert(task_id, updates)})())
    monkeypatch.setattr(tasks_router, "run_pack_step_v1", lambda _req: {"pack_key": f"deliver/tasks/{task_id}/pack.zip"})

    tasks_router._run_pipeline_background(task_id, repo)

    stored = repo.get(task_id)
    assert parse_calls == []
    assert subtitles_calls == [{"task_id": task_id, "target_lang": "vi"}]
    assert stored["parse_status"] == "done"
    assert stored["raw_path"] == f"deliver/tasks/{task_id}/raw.mp4"


def test_run_pipeline_background_keeps_link_parse_for_non_local_tasks(monkeypatch, tmp_path):
    task_id = "hf-link-parse"
    repo = _Repo(
        {
            "task_id": task_id,
            "kind": "hot_follow",
            "category_key": "hot_follow",
            "platform": "douyin",
            "source_url": "https://example.com/source",
            "content_lang": "vi",
            "target_lang": "vi",
            "voice_id": "vi_female_1",
            "pipeline_config": {},
        }
    )
    parse_calls: list[dict] = []

    raw_file = tmp_path / task_id / "raw" / "raw.mp4"
    raw_file.parent.mkdir(parents=True, exist_ok=True)
    raw_file.write_bytes(b"video")

    monkeypatch.setattr(tasks_router, "raw_path", lambda _task_id: raw_file)
    monkeypatch.setattr(
        tasks_router,
        "run_parse_step_v1",
        lambda req: parse_calls.append({"task_id": req.task_id, "link": req.link, "platform": req.platform}) or {"duration_sec": 1},
    )
    monkeypatch.setattr(tasks_router, "run_subtitles_step_v1", lambda _req: {})
    monkeypatch.setattr(tasks_router.asyncio, "run", lambda result: result)
    monkeypatch.setattr(tasks_router, "upload_task_artifact", lambda _task, _path, artifact_name, task_id=None: f"deliver/tasks/{task_id}/{artifact_name}")
    monkeypatch.setattr(tasks_router, "probe_subtitles", lambda _path: {"subtitle_track_kind": "none"})
    monkeypatch.setattr(tasks_router, "_update_pipeline_probe", lambda _repo, _task_id, _probe: None)
    monkeypatch.setattr(tasks_router, "_upload_target_subtitle_artifacts", lambda _task, _task_id, _target_lang: ("deliver/tasks/hf-link-parse/origin.srt", "deliver/tasks/hf-link-parse/vi.srt"))
    monkeypatch.setattr(tasks_router, "run_dub_step_ssot", lambda _task: None)

    class _FakeWorkspace:
        def __init__(self, _task_id=None, target_lang=None):
            _ = (_task_id, target_lang)
            self.mm_audio_path = tmp_path / task_id / "audio" / "audio_vi.mp3"
            self.mm_audio_mp3_path = self.mm_audio_path
            self.mm_audio_path.parent.mkdir(parents=True, exist_ok=True)
            self.mm_audio_path.write_bytes(b"audio")

        def mm_audio_exists(self):
            return True

    monkeypatch.setattr(tasks_router, "Workspace", _FakeWorkspace)
    monkeypatch.setattr(tasks_router, "_ensure_mp3_audio", lambda audio_path, _mp3_path: audio_path)
    monkeypatch.setattr(tasks_router, "assert_local_audio_ok", lambda _path: (1024, 1.0))

    class _Storage:
        def upload_file(self, _path, key, content_type=None):
            _ = content_type
            return key

    monkeypatch.setattr(tasks_router, "get_storage_service", lambda: _Storage())
    monkeypatch.setattr(tasks_router, "deliver_key", lambda _task_id, filename: f"deliver/tasks/{_task_id}/{filename}")
    monkeypatch.setattr(tasks_router, "TaskStateService", lambda repo, step: type("S", (), {"update_fields": lambda self, task_id, updates: repo.upsert(task_id, updates)})())
    monkeypatch.setattr(tasks_router, "run_pack_step_v1", lambda _req: {"pack_key": f"deliver/tasks/{task_id}/pack.zip"})

    tasks_router._run_pipeline_background(task_id, repo)

    assert parse_calls == [{"task_id": task_id, "link": "https://example.com/source", "platform": "douyin"}]
