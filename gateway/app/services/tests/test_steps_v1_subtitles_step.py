from __future__ import annotations

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from gateway.app.schemas import DubRequest, SubtitlesRequest
from gateway.app.services import steps_v1
from gateway.app.steps import subtitles as subtitles_step


class _FakeWorkspace:
    def __init__(self, base: Path, task_id: str, target_lang: str | None = None):
        self.base_dir = base / task_id
        self.subtitles_dir = self.base_dir / "subs"
        self.subtitles_dir.mkdir(parents=True, exist_ok=True)
        self.origin_srt_path = self.subtitles_dir / "origin.srt"
        suffix = "vi.srt" if str(target_lang or "").strip().lower() == "vi" else "mm.srt"
        self.mm_srt_path = self.subtitles_dir / suffix
        self.segments_json = self.subtitles_dir / "subtitles.json"


class _FakeRepo:
    def __init__(self, task: dict | None = None):
        self.task = task or {}

    def get(self, _task_id: str) -> dict:
        return dict(self.task)

    def upsert(self, _task_id: str, updates: dict) -> dict:
        self.task.update(updates or {})
        return dict(self.task)


class _MutableFakeRepo(_FakeRepo):
    def update(self, _task_id: str, updates: dict) -> dict:
        self.task.update(updates)
        return dict(self.task)


def test_run_subtitles_step_consumes_result_contract_for_myanmar(monkeypatch, tmp_path):
    pipeline_updates: list[dict] = []
    generate_kwargs: list[dict] = []
    repo = _FakeRepo()

    async def _generate_subtitles(**kwargs):
        generate_kwargs.append(dict(kwargs))
        return _fake_generate_subtitles(
            tmp_path,
            kwargs["task_id"],
            kwargs["target_lang"],
            complete=True,
            parse_source_mode=kwargs["parse_source_mode"],
        )

    monkeypatch.setattr(
        steps_v1,
        "Workspace",
        lambda task_id, target_lang=None: _FakeWorkspace(tmp_path, task_id, target_lang),
    )
    monkeypatch.setattr(steps_v1, "generate_subtitles", _generate_subtitles)
    monkeypatch.setattr(steps_v1, "_update_task", lambda _task_id, **kwargs: repo.upsert(_task_id, kwargs))
    monkeypatch.setattr(steps_v1, "_update_pipeline_config", lambda _task_id, payload: pipeline_updates.append(dict(payload)))
    monkeypatch.setattr(steps_v1, "_upload_artifact", lambda task_id, _path, artifact_name: f"deliver/tasks/{task_id}/{artifact_name}")
    monkeypatch.setattr(steps_v1, "deliver_dir", lambda: tmp_path / "deliver")
    monkeypatch.setattr(steps_v1, "relative_to_workspace", lambda path: str(path))
    monkeypatch.setattr(steps_v1, "get_task_repository", lambda: repo)

    req = SubtitlesRequest(task_id="hf-mm-sub2", target_lang="my", force=True, translate=True)
    result = asyncio.run(steps_v1.run_subtitles_step(req))

    assert result["mm_srt"]
    final_update = repo.get(req.task_id)
    assert final_update["subtitles_status"] == "ready"
    assert final_update["subtitles_error"] is None
    assert final_update["origin_subtitle_artifact_exists"] is True
    assert final_update["target_subtitle_artifact_exists"] is True
    assert final_update["target_subtitle_materialized"] is True
    assert final_update["target_subtitle_authoritative_source"] is True
    assert final_update["target_subtitle_current"] is True
    assert final_update["target_subtitle_current_reason"] == "ready"
    assert generate_kwargs[-1]["parse_source_mode"] == "raw_video_audio"
    assert pipeline_updates[-1]["translation_incomplete"] == "false"
    assert pipeline_updates[-1]["parse_source_authoritative_for_target"] == "true"
    assert pipeline_updates[-1]["target_subtitle_authoritative"] == "true"


def test_clear_no_dub_pipeline_flags_removes_stale_skip_marker(monkeypatch, tmp_path):
    repo = _MutableFakeRepo(
        {
            "task_id": "hf-clear-no-dub",
            "kind": "hot_follow",
            "pipeline_config": {
                "no_dub": "true",
                "dub_skip_reason": "target_subtitle_empty",
                "source_audio_policy": "mute",
            },
        }
    )
    note_path = tmp_path / "hf-clear-no-dub" / "dub" / "no_dub.txt"
    note_path.parent.mkdir(parents=True, exist_ok=True)
    note_path.write_text("reason=target_subtitle_empty\n", encoding="utf-8")

    monkeypatch.setattr(steps_v1, "get_task_repository", lambda: repo)
    monkeypatch.setattr(steps_v1, "task_base_dir", lambda task_id: tmp_path / task_id)

    cleared = steps_v1._clear_no_dub_pipeline_flags("hf-clear-no-dub", repo.task)

    assert "no_dub" not in cleared
    assert "dub_skip_reason" not in cleared
    assert cleared["source_audio_policy"] == "mute"
    stored = steps_v1.parse_pipeline_config(repo.task.get("pipeline_config"))
    assert "no_dub" not in stored
    assert "dub_skip_reason" not in stored
    assert stored["source_audio_policy"] == "mute"
    assert repo.task["dub_skip_reason"] is None
    assert note_path.exists() is False


def test_run_subtitles_step_marks_vi_translation_incomplete_without_step_error(monkeypatch, tmp_path):
    pipeline_updates: list[dict] = []
    repo = _FakeRepo()

    async def _generate_subtitles(**kwargs):
        return _fake_generate_subtitles(
            tmp_path,
            kwargs["task_id"],
            kwargs["target_lang"],
            complete=False,
            parse_source_mode=kwargs["parse_source_mode"],
        )

    monkeypatch.setattr(
        steps_v1,
        "Workspace",
        lambda task_id, target_lang=None: _FakeWorkspace(tmp_path, task_id, target_lang),
    )
    monkeypatch.setattr(steps_v1, "generate_subtitles", _generate_subtitles)
    monkeypatch.setattr(steps_v1, "_update_task", lambda _task_id, **kwargs: repo.upsert(_task_id, kwargs))
    monkeypatch.setattr(steps_v1, "_update_pipeline_config", lambda _task_id, payload: pipeline_updates.append(dict(payload)))
    monkeypatch.setattr(steps_v1, "_upload_artifact", lambda task_id, _path, artifact_name: f"deliver/tasks/{task_id}/{artifact_name}")
    monkeypatch.setattr(steps_v1, "deliver_dir", lambda: tmp_path / "deliver")
    monkeypatch.setattr(steps_v1, "relative_to_workspace", lambda path: str(path))
    monkeypatch.setattr(steps_v1, "get_task_repository", lambda: repo)

    req = SubtitlesRequest(task_id="hf-vi-sub2", target_lang="vi", force=True, translate=True)
    result = asyncio.run(steps_v1.run_subtitles_step(req))

    assert result["translation_incomplete"] is True
    final_update = repo.get(req.task_id)
    assert final_update["subtitles_status"] == "pending"
    assert "waiting" in final_update["subtitles_error"]
    assert final_update["origin_subtitle_artifact_exists"] is True
    assert final_update["target_subtitle_artifact_exists"] is False
    assert final_update["target_subtitle_materialized"] is False
    assert final_update["target_subtitle_authoritative_source"] is False
    assert final_update["target_subtitle_current"] is False
    assert final_update["target_subtitle_current_reason"] == "target_subtitle_translation_incomplete"
    assert pipeline_updates[-1]["translation_incomplete"] == "true"


def test_run_subtitles_step_marks_myanmar_translation_incomplete_without_step_error(monkeypatch, tmp_path):
    pipeline_updates: list[dict] = []
    repo = _FakeRepo()

    async def _generate_subtitles(**kwargs):
        return _fake_generate_subtitles(
            tmp_path,
            kwargs["task_id"],
            kwargs["target_lang"],
            complete=False,
            parse_source_mode=kwargs["parse_source_mode"],
        )

    monkeypatch.setattr(
        steps_v1,
        "Workspace",
        lambda task_id, target_lang=None: _FakeWorkspace(tmp_path, task_id, target_lang),
    )
    monkeypatch.setattr(steps_v1, "generate_subtitles", _generate_subtitles)
    monkeypatch.setattr(steps_v1, "_update_task", lambda _task_id, **kwargs: repo.upsert(_task_id, kwargs))
    monkeypatch.setattr(steps_v1, "_update_pipeline_config", lambda _task_id, payload: pipeline_updates.append(dict(payload)))
    monkeypatch.setattr(steps_v1, "_upload_artifact", lambda task_id, _path, artifact_name: f"deliver/tasks/{task_id}/{artifact_name}")
    monkeypatch.setattr(steps_v1, "deliver_dir", lambda: tmp_path / "deliver")
    monkeypatch.setattr(steps_v1, "relative_to_workspace", lambda path: str(path))
    monkeypatch.setattr(steps_v1, "get_task_repository", lambda: repo)

    req = SubtitlesRequest(task_id="hf-mm-sub-incomplete", target_lang="my", force=True, translate=True)
    result = asyncio.run(steps_v1.run_subtitles_step(req))

    assert result["translation_incomplete"] is True
    final_update = repo.get(req.task_id)
    assert final_update["subtitles_status"] == "pending"
    assert "waiting" in final_update["subtitles_error"]
    assert final_update["target_subtitle_current"] is False
    assert final_update["target_subtitle_current_reason"] == "target_subtitle_translation_incomplete"
    assert pipeline_updates[-1]["translation_incomplete"] == "true"


def test_run_subtitles_step_treats_preserved_source_audio_as_helper_only(monkeypatch, tmp_path):
    pipeline_updates: list[dict] = []
    uploaded_artifacts: list[str] = []
    generate_kwargs: list[dict] = []
    repo = _FakeRepo(
        {
            "config": {"source_audio_policy": "preserve"},
            "pipeline_config": {"source_audio_policy": "preserve"},
        }
    )

    async def _generate_subtitles(**kwargs):
        generate_kwargs.append(dict(kwargs))
        return _fake_generate_subtitles(
            tmp_path,
            kwargs["task_id"],
            kwargs["target_lang"],
            complete=False,
            parse_source_mode=kwargs["parse_source_mode"],
        )

    monkeypatch.setattr(
        steps_v1,
        "Workspace",
        lambda task_id, target_lang=None: _FakeWorkspace(tmp_path, task_id, target_lang),
    )
    monkeypatch.setattr(steps_v1, "generate_subtitles", _generate_subtitles)
    monkeypatch.setattr(steps_v1, "_update_task", lambda _task_id, **kwargs: repo.upsert(_task_id, kwargs))
    monkeypatch.setattr(steps_v1, "_update_pipeline_config", lambda _task_id, payload: pipeline_updates.append(dict(payload)))
    monkeypatch.setattr(
        steps_v1,
        "_upload_artifact",
        lambda task_id, _path, artifact_name: uploaded_artifacts.append(artifact_name)
        or f"deliver/tasks/{task_id}/{artifact_name}",
    )
    monkeypatch.setattr(steps_v1, "deliver_dir", lambda: tmp_path / "deliver")
    monkeypatch.setattr(steps_v1, "relative_to_workspace", lambda path: str(path))
    monkeypatch.setattr(steps_v1, "get_task_repository", lambda: repo)

    req = SubtitlesRequest(task_id="hf-preserve-helper", target_lang="vi", force=True, translate=True)
    result = asyncio.run(steps_v1.run_subtitles_step(req))

    assert generate_kwargs[-1]["parse_source_mode"] == "preserved_source_audio_helper"
    assert result["mm_srt"] == ""
    assert "subs/origin.srt" in uploaded_artifacts
    assert "subs/vi.srt" not in uploaded_artifacts

    final_update = repo.get(req.task_id)
    assert final_update["subtitles_status"] == "ready"
    assert final_update["subtitles_error"] is None
    assert final_update["mm_srt_path"] is None
    assert final_update["target_subtitle_current"] is False
    assert final_update["target_subtitle_current_reason"] == "preserve_source_route_no_target_subtitle_required"

    final_pipeline = pipeline_updates[-1]
    assert final_pipeline["parse_source_mode"] == "preserved_source_audio_helper"
    assert final_pipeline["parse_source_role"] == "preserved_source_audio_helper"
    assert final_pipeline["parse_source_authoritative_for_target"] == "false"
    assert final_pipeline["target_subtitle_authoritative"] == "false"
    assert final_pipeline["translation_incomplete"] == "false"


def test_run_subtitles_step_delegates_authoritative_truth_to_service(monkeypatch, tmp_path):
    repo = _FakeRepo()
    finalize_calls: list[dict] = []

    async def _generate_subtitles(**kwargs):
        return _fake_generate_subtitles(
            tmp_path,
            kwargs["task_id"],
            kwargs["target_lang"],
            complete=True,
            parse_source_mode=kwargs["parse_source_mode"],
        )

    def _finalize(task_id, task, **kwargs):
        finalize_calls.append({"task_id": task_id, "task": dict(task), **kwargs})
        repo.upsert(
            task_id,
            {
                "subtitles_status": "ready",
                "target_subtitle_current": True,
                "target_subtitle_current_reason": "ready",
            },
        )
        return repo.get(task_id)

    monkeypatch.setattr(
        steps_v1,
        "Workspace",
        lambda task_id, target_lang=None: _FakeWorkspace(tmp_path, task_id, target_lang),
    )
    monkeypatch.setattr(steps_v1, "generate_subtitles", _generate_subtitles)
    monkeypatch.setattr(steps_v1, "_update_task", lambda _task_id, **kwargs: repo.upsert(_task_id, kwargs))
    monkeypatch.setattr(steps_v1, "_update_pipeline_config", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(steps_v1, "_upload_artifact", lambda task_id, _path, artifact_name: f"deliver/tasks/{task_id}/{artifact_name}")
    monkeypatch.setattr(steps_v1, "deliver_dir", lambda: tmp_path / "deliver")
    monkeypatch.setattr(steps_v1, "relative_to_workspace", lambda path: str(path))
    monkeypatch.setattr(steps_v1, "get_task_repository", lambda: repo)
    monkeypatch.setattr(steps_v1, "finalize_hot_follow_subtitles_step", _finalize)

    asyncio.run(steps_v1.run_subtitles_step(SubtitlesRequest(task_id="hf-subtitle-owner", target_lang="vi", force=True, translate=True)))

    assert len(finalize_calls) == 1
    assert finalize_calls[0]["target_subtitle_authoritative"] is True
    assert finalize_calls[0]["target_subtitle_key"] == "deliver/tasks/hf-subtitle-owner/subs/vi.srt"


def test_run_subtitles_step_rejects_timing_only_target_subtitle_before_success(monkeypatch, tmp_path):
    repo = _FakeRepo()
    uploaded_artifacts: list[str] = []

    async def _generate_subtitles(**kwargs):
        workspace = _FakeWorkspace(tmp_path, kwargs["task_id"], kwargs["target_lang"])
        origin_text = "1\n00:00:00,000 --> 00:00:02,000\n你好\n"
        target_text = "1\n00:00:00,000 --> 00:00:02,000\n\n"
        workspace.origin_srt_path.write_text(origin_text, encoding="utf-8")
        workspace.mm_srt_path.write_text(target_text, encoding="utf-8")
        workspace.segments_json.write_text(json.dumps({"scenes": []}), encoding="utf-8")
        return {
            "task_id": kwargs["task_id"],
            "origin_srt": origin_text,
            "origin_normalized_srt": origin_text,
            "mm_srt": target_text,
            "translation_qa": {"complete": True},
            "translation_incomplete": False,
            "stream_probe": {"has_audio": True, "has_subtitle_stream": False},
            "parse_source_mode": kwargs["parse_source_mode"],
            "parse_source_role": "subtitle_source_helper",
            "parse_source_authoritative_for_target": True,
            "target_subtitle_authoritative": True,
        }

    monkeypatch.setattr(
        steps_v1,
        "Workspace",
        lambda task_id, target_lang=None: _FakeWorkspace(tmp_path, task_id, target_lang),
    )
    monkeypatch.setattr(steps_v1, "generate_subtitles", _generate_subtitles)
    monkeypatch.setattr(steps_v1, "_update_task", lambda _task_id, **kwargs: repo.upsert(_task_id, kwargs))
    monkeypatch.setattr(steps_v1, "_update_pipeline_config", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        steps_v1,
        "_upload_artifact",
        lambda task_id, _path, artifact_name: uploaded_artifacts.append(artifact_name)
        or f"deliver/tasks/{task_id}/{artifact_name}",
    )
    monkeypatch.setattr(steps_v1, "deliver_dir", lambda: tmp_path / "deliver")
    monkeypatch.setattr(steps_v1, "relative_to_workspace", lambda path: str(path))
    monkeypatch.setattr(steps_v1, "get_task_repository", lambda: repo)

    asyncio.run(steps_v1.run_subtitles_step(SubtitlesRequest(task_id="hf-empty-body", target_lang="vi", force=True, translate=True)))

    final_update = repo.get("hf-empty-body")
    assert "subs/vi.srt" not in uploaded_artifacts
    assert final_update["subtitles_status"] == "failed"
    assert final_update["target_subtitle_current"] is False
    assert final_update["target_subtitle_current_reason"] == "target_subtitle_empty"


def test_generate_subtitles_keeps_preserved_source_audio_helper_out_of_target_truth(monkeypatch, tmp_path):
    class _GenerateWorkspace:
        def __init__(self, task_id: str, target_lang: str | None = None):
            self.task_id = task_id
            self.target_lang = target_lang
            self.base_dir = tmp_path / task_id
            self.subtitles_dir = self.base_dir / "subs"
            self.subtitles_dir.mkdir(parents=True, exist_ok=True)
            self.raw_video_path = self.base_dir / "raw.mp4"
            self.raw_video_path.parent.mkdir(parents=True, exist_ok=True)
            self.raw_video_path.write_bytes(b"video-with-preserved-source-audio")
            self.origin_srt_path = self.subtitles_dir / "origin.srt"
            self.mm_srt_path = self.subtitles_dir / "vi.srt"
            self.segments_json = self.subtitles_dir / "subtitles.json"

        def raw_video_exists(self) -> bool:
            return True

        def read_origin_srt_text(self) -> str:
            return self.origin_srt_path.read_text(encoding="utf-8") if self.origin_srt_path.exists() else ""

        def write_segments_json(self, payload: dict) -> Path:
            self.segments_json.write_text(json.dumps(payload), encoding="utf-8")
            return self.segments_json

        def write_origin_srt(self, text: str) -> Path:
            self.origin_srt_path.write_text(text, encoding="utf-8")
            return self.origin_srt_path

        def write_mm_srt(self, text: str) -> Path:
            self.mm_srt_path.write_text(text, encoding="utf-8")
            return self.mm_srt_path

    def _unexpected_translate(**_kwargs):
        raise AssertionError("helper-only preserved source audio must not be translated")

    monkeypatch.setattr(
        subtitles_step,
        "get_settings",
        lambda: SimpleNamespace(
            subtitles_backend="gemini",
            asr_backend="faster-whisper",
            openai_api_key=None,
        ),
    )
    monkeypatch.setattr(subtitles_step, "Workspace", _GenerateWorkspace)
    monkeypatch.setattr(subtitles_step, "_probe_streams", lambda _path: {"has_audio": True, "has_subtitle_stream": False})
    monkeypatch.setattr(subtitles_step, "raw_clean_path", lambda task_id: tmp_path / task_id / "clean.mp4")
    monkeypatch.setattr(subtitles_step, "audio_wav_path", lambda task_id: tmp_path / task_id / "asr.wav")
    monkeypatch.setattr(subtitles_step, "_extract_audio", lambda _raw, wav, timeout_sec=None: Path(wav).write_bytes(b"wav"))
    monkeypatch.setattr(subtitles_step, "_wav_duration_seconds", lambda _wav: 2.0)
    monkeypatch.setattr(subtitles_step, "_compute_asr_timeout_sec", lambda _audio_sec: 10)
    monkeypatch.setattr(
        subtitles_step,
        "_transcribe_with_faster_whisper",
        lambda _wav, _hint: ([{"index": 1, "start": 0.0, "end": 2.0, "origin": "lyric source line"}], "zh"),
    )
    monkeypatch.setattr(subtitles_step, "translate_segments_with_gemini", _unexpected_translate)
    monkeypatch.setattr(subtitles_step, "subs_dir", lambda task_id: tmp_path / task_id / "subs")
    monkeypatch.setattr(subtitles_step, "relative_to_workspace", lambda path: str(path))

    result = asyncio.run(
        subtitles_step.generate_subtitles(
            "hf-preserve-generate",
            target_lang="vi",
            force=True,
            translate_enabled=True,
            parse_source_mode="preserved_source_audio_helper",
        )
    )

    assert result["origin_srt"]
    assert result["mm_srt"] == ""
    assert result["translation_incomplete"] is True
    assert result["translation_qa"]["complete"] is False
    assert result["translation_qa"]["missing_indexes"] == [1]
    assert result["parse_source_role"] == "preserved_source_audio_helper"
    assert result["parse_source_authoritative_for_target"] is False
    assert result["target_subtitle_authoritative"] is False


def test_run_dub_step_skips_empty_target_subtitle_instead_of_failing(monkeypatch, tmp_path):
    updates: list[dict] = []

    class _DubWorkspace:
        def __init__(self, task_id: str, target_lang: str | None = None):
            self.base_dir = tmp_path / task_id
            self.subtitles_dir = self.base_dir / "subs"
            self.subtitles_dir.mkdir(parents=True, exist_ok=True)
            suffix = "vi.srt" if str(target_lang or "").strip().lower() == "vi" else "mm.srt"
            self.mm_txt_path = self.subtitles_dir / suffix.replace(".srt", ".txt")
            self.mm_srt_path = self.subtitles_dir / suffix
            self.origin_srt_path = self.subtitles_dir / "origin.srt"

        def mm_srt_exists(self) -> bool:
            return self.mm_srt_path.exists()

        def read_mm_edited_text(self) -> str:
            return ""

    class _DummyDb:
        def query(self, *_args, **_kwargs):
            return self

        def filter(self, *_args, **_kwargs):
            return self

        def first(self):
            return SimpleNamespace(pipeline_config=None)

        def close(self):
            return None

    monkeypatch.setattr(
        steps_v1.config,
        "get_settings",
        lambda: SimpleNamespace(
            edge_tts_voice_map={"mm_female_1": "my-MM-NilarNeural"},
            azure_tts_voice_map={},
        ),
    )
    monkeypatch.setattr(steps_v1, "Workspace", _DubWorkspace)
    monkeypatch.setattr(steps_v1, "SessionLocal", lambda: _DummyDb())
    monkeypatch.setattr(steps_v1, "task_base_dir", lambda task_id: tmp_path / task_id)
    monkeypatch.setattr(
        steps_v1,
        "get_task_repository",
        lambda: _FakeRepo({"config": {"tts_voiceover_key": "deliver/tasks/old/audio_mm.dry.mp3"}}),
    )
    monkeypatch.setattr(steps_v1, "_append_event", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(steps_v1, "_update_task", lambda _task_id, **kwargs: updates.append(dict(kwargs)))
    monkeypatch.setattr(
        steps_v1,
        "synthesize_voice",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("empty dub must not call TTS")),
    )

    result = asyncio.run(
        steps_v1.run_dub_step(
            DubRequest(
                task_id="hf-empty-dub",
                target_lang="my",
                provider="edge-tts",
                force=True,
            )
        )
    )

    assert result["dub_status"] == "skipped"
    assert result["dub_skip_reason"] == "target_subtitle_empty"
    assert updates[-1]["dub_status"] == "skipped"
    assert updates[-1]["dub_error"] is None
    assert updates[-1]["mm_audio_key"] is None
    assert updates[-1]["mm_audio_path"] is None
    assert updates[-1]["config"]["tts_voiceover_key"] is None
    pipeline = json.loads(updates[-1]["pipeline_config"])
    assert pipeline["no_dub"] == "true"
    assert pipeline["dub_skip_reason"] == "target_subtitle_empty"
    assert (tmp_path / "hf-empty-dub" / "dub" / "no_dub.txt").exists()


def test_run_dub_step_does_not_skip_translation_incomplete_first_attempt_as_empty_target(monkeypatch, tmp_path):
    updates: list[dict] = []

    class _DubWorkspace:
        def __init__(self, task_id: str, target_lang: str | None = None):
            self.base_dir = tmp_path / task_id
            self.subtitles_dir = self.base_dir / "subs"
            self.subtitles_dir.mkdir(parents=True, exist_ok=True)
            suffix = "vi.srt" if str(target_lang or "").strip().lower() == "vi" else "mm.srt"
            self.mm_txt_path = self.subtitles_dir / suffix.replace(".srt", ".txt")
            self.mm_srt_path = self.subtitles_dir / suffix
            self.origin_srt_path = self.subtitles_dir / "origin.srt"
            self.origin_srt_path.write_text("1\n00:00:00,000 --> 00:00:02,000\nvoice led transcript\n", encoding="utf-8")

        def mm_srt_exists(self) -> bool:
            return self.mm_srt_path.exists()

        def read_mm_edited_text(self) -> str:
            return ""

    class _DummyDb:
        def query(self, *_args, **_kwargs):
            return self

        def filter(self, *_args, **_kwargs):
            return self

        def first(self):
            return SimpleNamespace(pipeline_config=None)

        def close(self):
            return None

    repo = _FakeRepo(
        {
            "pipeline_config": {"translation_incomplete": "true"},
            "target_subtitle_current_reason": "target_subtitle_translation_incomplete",
            "config": {"tts_voiceover_key": "deliver/tasks/old/audio_mm.dry.mp3"},
        }
    )

    monkeypatch.setattr(
        steps_v1.config,
        "get_settings",
        lambda: SimpleNamespace(
            edge_tts_voice_map={"mm_female_1": "my-MM-NilarNeural"},
            azure_tts_voice_map={},
        ),
    )
    monkeypatch.setattr(steps_v1, "Workspace", _DubWorkspace)
    monkeypatch.setattr(steps_v1, "SessionLocal", lambda: _DummyDb())
    monkeypatch.setattr(steps_v1, "task_base_dir", lambda task_id: tmp_path / task_id)
    monkeypatch.setattr(steps_v1, "get_task_repository", lambda: repo)
    monkeypatch.setattr(steps_v1, "_append_event", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(steps_v1, "_update_task", lambda _task_id, **kwargs: updates.append(dict(kwargs)))
    monkeypatch.setattr(
        steps_v1,
        "synthesize_voice",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("translation incomplete must not call TTS")),
    )

    result = asyncio.run(
        steps_v1.run_dub_step(
            DubRequest(
                task_id="hf-translation-incomplete-first-attempt",
                target_lang="my",
                provider="edge-tts",
                force=True,
            )
        )
    )

    assert result["dub_status"] == "pending"
    assert result["dub_blocked_reason"] == "waiting_for_target_subtitle_translation"
    assert updates[-1]["dub_status"] == "pending"
    assert updates[-1]["dub_error"] is None
    assert "pipeline_config" not in updates[-1]


def test_subtitles_pipeline_state_distinguishes_no_subtitles_and_translation_incomplete():
    no_subtitles_status, no_subtitles_summary = steps_v1_hot_follow_pipeline_state(
        {
            "subtitles_status": "failed",
            "pipeline_config": {"no_subtitles": "true"},
        }
    )
    assert no_subtitles_status == "failed"
    assert no_subtitles_summary == "no_subtitles"

    vi_status, vi_summary = steps_v1_hot_follow_pipeline_state(
        {
            "subtitles_status": "pending",
            "pipeline_config": {"translation_incomplete": "true"},
            "target_subtitle_current_reason": "target_subtitle_translation_incomplete",
        }
    )
    assert vi_status == "pending"
    assert vi_summary == "translation_incomplete"


def test_subtitles_pipeline_state_does_not_promote_done_on_origin_only():
    # URL-lane regression: persisted L1 is pending, source-language parse exists,
    # but target subtitle is not authoritative/current. Projection must not
    # promote pending -> done off origin_srt_path alone.
    status, _summary = steps_v1_hot_follow_pipeline_state(
        {
            "subtitles_status": "pending",
            "origin_srt_path": "tasks/abc/subs/origin.srt",
            "target_subtitle_current": False,
            "target_subtitle_authoritative_source": False,
            "target_subtitle_current_reason": "target_subtitle_source_mismatch",
        }
    )
    assert status == "pending"


def test_subtitles_pipeline_state_does_not_promote_done_on_mm_srt_only():
    # mm.srt may exist as a partial/non-authoritative artifact. Without L3 truth
    # asserting authoritative+current, projection must stay pending.
    status, _summary = steps_v1_hot_follow_pipeline_state(
        {
            "subtitles_status": "pending",
            "mm_srt_path": "tasks/abc/subs/vi.srt",
            "target_subtitle_current": False,
            "target_subtitle_authoritative_source": False,
        }
    )
    assert status == "pending"


def test_subtitles_pipeline_state_promotes_done_when_authoritative_and_current():
    # When L3 truth says target subtitle is authoritative and current,
    # projection may promote pending -> done.
    status, _summary = steps_v1_hot_follow_pipeline_state(
        {
            "subtitles_status": "pending",
            "origin_srt_path": "tasks/abc/subs/origin.srt",
            "mm_srt_path": "tasks/abc/subs/vi.srt",
            "target_subtitle_current": True,
            "target_subtitle_authoritative_source": True,
            "target_subtitle_current_reason": "ready",
        }
    )
    assert status == "done"


def test_subtitles_pipeline_state_translation_incomplete_stays_pending():
    # Defensive: even if L3 currentness flags are accidentally true,
    # translation_waiting derived from pipeline_config keeps the projection pending.
    status, summary = steps_v1_hot_follow_pipeline_state(
        {
            "subtitles_status": "pending",
            "origin_srt_path": "tasks/abc/subs/origin.srt",
            "mm_srt_path": "tasks/abc/subs/vi.srt",
            "target_subtitle_current": True,
            "target_subtitle_authoritative_source": True,
            "pipeline_config": {"translation_incomplete": "true"},
        }
    )
    assert status == "pending"
    assert summary == "translation_incomplete"


def _fake_generate_subtitles(
    base: Path,
    task_id: str,
    target_lang: str,
    *,
    complete: bool,
    parse_source_mode: str = "raw_video_audio",
) -> dict:
    workspace = _FakeWorkspace(base, task_id, target_lang)
    helper_only = parse_source_mode == "preserved_source_audio_helper"
    origin_text = "1\n00:00:00,000 --> 00:00:02,000\n你好\n"
    target_text = (
        "1\n00:00:00,000 --> 00:00:02,000\nXin chao\n"
        if str(target_lang).strip().lower() == "vi"
        else "1\n00:00:00,000 --> 00:00:02,000\nမင်္ဂလာပါ\n"
    )
    if not complete or helper_only:
        target_text = ""
    workspace.origin_srt_path.write_text(origin_text, encoding="utf-8")
    workspace.mm_srt_path.write_text(target_text, encoding="utf-8")
    workspace.segments_json.write_text(json.dumps({"scenes": []}), encoding="utf-8")
    qa_payload = {
        "source_count": 1,
        "translated_count": 1 if complete and not helper_only else 0,
        "missing_indexes": [] if complete and not helper_only else [1],
        "retry_count": 0,
        "complete": complete and not helper_only,
    }
    (workspace.subtitles_dir / "translation_qa.json").write_text(
        json.dumps(qa_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {
        "task_id": task_id,
        "origin_srt": origin_text,
        "origin_normalized_srt": origin_text,
        "mm_srt": target_text,
        "translation_qa": qa_payload,
        "translation_incomplete": not complete,
        "stream_probe": {"has_audio": True, "has_subtitle_stream": False},
        "parse_source_mode": parse_source_mode,
        "parse_source_role": "preserved_source_audio_helper" if helper_only else "subtitle_source_helper",
        "parse_source_authoritative_for_target": not helper_only,
        "target_subtitle_authoritative": not helper_only,
    }


def steps_v1_hot_follow_pipeline_state(task: dict) -> tuple[str, str]:
    from gateway.app.routers import hot_follow_api as hf_router

    status, summary = hf_router._hf_pipeline_state(task, "subtitles")
    return status, summary
