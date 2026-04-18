from __future__ import annotations

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

from gateway.app.schemas import SubtitlesRequest
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


def test_run_subtitles_step_consumes_result_contract_for_myanmar(monkeypatch, tmp_path):
    updates: list[dict] = []
    pipeline_updates: list[dict] = []
    generate_kwargs: list[dict] = []

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
    monkeypatch.setattr(steps_v1, "_update_task", lambda _task_id, **kwargs: updates.append(dict(kwargs)))
    monkeypatch.setattr(steps_v1, "_update_pipeline_config", lambda _task_id, payload: pipeline_updates.append(dict(payload)))
    monkeypatch.setattr(steps_v1, "_upload_artifact", lambda task_id, _path, artifact_name: f"deliver/tasks/{task_id}/{artifact_name}")
    monkeypatch.setattr(steps_v1, "deliver_dir", lambda: tmp_path / "deliver")
    monkeypatch.setattr(steps_v1, "relative_to_workspace", lambda path: str(path))
    monkeypatch.setattr(steps_v1, "get_task_repository", lambda: _FakeRepo())

    req = SubtitlesRequest(task_id="hf-mm-sub2", target_lang="my", force=True, translate=True)
    result = asyncio.run(steps_v1.run_subtitles_step(req))

    assert result["mm_srt"]
    final_update = updates[-1]
    assert final_update["subtitles_status"] == "ready"
    assert final_update["subtitles_error"] is None
    assert final_update["target_subtitle_current"] is True
    assert final_update["target_subtitle_current_reason"] == "ready"
    assert generate_kwargs[-1]["parse_source_mode"] == "raw_video_audio"
    assert pipeline_updates[-1]["translation_incomplete"] == "false"
    assert pipeline_updates[-1]["parse_source_authoritative_for_target"] == "true"
    assert pipeline_updates[-1]["target_subtitle_authoritative"] == "true"


def test_run_subtitles_step_marks_vi_translation_incomplete_without_step_error(monkeypatch, tmp_path):
    updates: list[dict] = []
    pipeline_updates: list[dict] = []

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
    monkeypatch.setattr(steps_v1, "_update_task", lambda _task_id, **kwargs: updates.append(dict(kwargs)))
    monkeypatch.setattr(steps_v1, "_update_pipeline_config", lambda _task_id, payload: pipeline_updates.append(dict(payload)))
    monkeypatch.setattr(steps_v1, "_upload_artifact", lambda task_id, _path, artifact_name: f"deliver/tasks/{task_id}/{artifact_name}")
    monkeypatch.setattr(steps_v1, "deliver_dir", lambda: tmp_path / "deliver")
    monkeypatch.setattr(steps_v1, "relative_to_workspace", lambda path: str(path))
    monkeypatch.setattr(steps_v1, "get_task_repository", lambda: _FakeRepo())

    req = SubtitlesRequest(task_id="hf-vi-sub2", target_lang="vi", force=True, translate=True)
    result = asyncio.run(steps_v1.run_subtitles_step(req))

    assert result["translation_incomplete"] is True
    final_update = updates[-1]
    assert final_update["subtitles_status"] == "ready"
    assert final_update["subtitles_error"] is None
    assert final_update["target_subtitle_current"] is False
    assert final_update["target_subtitle_current_reason"] == "target_subtitle_translation_incomplete"
    assert pipeline_updates[-1]["translation_incomplete"] == "true"


def test_run_subtitles_step_marks_myanmar_translation_incomplete_without_step_error(monkeypatch, tmp_path):
    updates: list[dict] = []
    pipeline_updates: list[dict] = []

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
    monkeypatch.setattr(steps_v1, "_update_task", lambda _task_id, **kwargs: updates.append(dict(kwargs)))
    monkeypatch.setattr(steps_v1, "_update_pipeline_config", lambda _task_id, payload: pipeline_updates.append(dict(payload)))
    monkeypatch.setattr(steps_v1, "_upload_artifact", lambda task_id, _path, artifact_name: f"deliver/tasks/{task_id}/{artifact_name}")
    monkeypatch.setattr(steps_v1, "deliver_dir", lambda: tmp_path / "deliver")
    monkeypatch.setattr(steps_v1, "relative_to_workspace", lambda path: str(path))
    monkeypatch.setattr(steps_v1, "get_task_repository", lambda: _FakeRepo())

    req = SubtitlesRequest(task_id="hf-mm-sub-incomplete", target_lang="my", force=True, translate=True)
    result = asyncio.run(steps_v1.run_subtitles_step(req))

    assert result["translation_incomplete"] is True
    final_update = updates[-1]
    assert final_update["subtitles_status"] == "ready"
    assert final_update["subtitles_error"] is None
    assert final_update["target_subtitle_current"] is False
    assert final_update["target_subtitle_current_reason"] == "target_subtitle_translation_incomplete"
    assert pipeline_updates[-1]["translation_incomplete"] == "true"


def test_run_subtitles_step_treats_preserved_source_audio_as_helper_only(monkeypatch, tmp_path):
    updates: list[dict] = []
    pipeline_updates: list[dict] = []
    uploaded_artifacts: list[str] = []
    generate_kwargs: list[dict] = []

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
    monkeypatch.setattr(steps_v1, "_update_task", lambda _task_id, **kwargs: updates.append(dict(kwargs)))
    monkeypatch.setattr(steps_v1, "_update_pipeline_config", lambda _task_id, payload: pipeline_updates.append(dict(payload)))
    monkeypatch.setattr(
        steps_v1,
        "_upload_artifact",
        lambda task_id, _path, artifact_name: uploaded_artifacts.append(artifact_name)
        or f"deliver/tasks/{task_id}/{artifact_name}",
    )
    monkeypatch.setattr(steps_v1, "deliver_dir", lambda: tmp_path / "deliver")
    monkeypatch.setattr(steps_v1, "relative_to_workspace", lambda path: str(path))
    monkeypatch.setattr(
        steps_v1,
        "get_task_repository",
        lambda: _FakeRepo(
            {
                "config": {"source_audio_policy": "preserve"},
                "pipeline_config": {"source_audio_policy": "preserve"},
            }
        ),
    )

    req = SubtitlesRequest(task_id="hf-preserve-helper", target_lang="vi", force=True, translate=True)
    result = asyncio.run(steps_v1.run_subtitles_step(req))

    assert generate_kwargs[-1]["parse_source_mode"] == "preserved_source_audio_helper"
    assert result["mm_srt"] == ""
    assert "subs/origin.srt" in uploaded_artifacts
    assert "subs/vi.srt" not in uploaded_artifacts

    final_update = updates[-1]
    assert final_update["subtitles_status"] == "ready"
    assert final_update["mm_srt_path"] is None
    assert final_update["target_subtitle_current"] is False
    assert final_update["target_subtitle_current_reason"] == "subtitle_missing"

    final_pipeline = pipeline_updates[-1]
    assert final_pipeline["parse_source_mode"] == "preserved_source_audio_helper"
    assert final_pipeline["parse_source_role"] == "preserved_source_audio_helper"
    assert final_pipeline["parse_source_authoritative_for_target"] == "false"
    assert final_pipeline["target_subtitle_authoritative"] == "false"
    assert final_pipeline["translation_incomplete"] == "true"


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


def test_subtitles_pipeline_state_distinguishes_no_subtitles_and_translation_incomplete():
    no_subtitles_status, no_subtitles_summary = steps_v1_hot_follow_pipeline_state(
        {
            "subtitles_status": "ready",
            "pipeline_config": {"no_subtitles": "true"},
        }
    )
    assert no_subtitles_status == "done"
    assert no_subtitles_summary == "no_subtitles"

    vi_status, vi_summary = steps_v1_hot_follow_pipeline_state(
        {
            "subtitles_status": "ready",
            "pipeline_config": {"translation_incomplete": "true"},
            "target_subtitle_current_reason": "target_subtitle_translation_incomplete",
        }
    )
    assert vi_status == "done"
    assert vi_summary == "translation_incomplete"


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
