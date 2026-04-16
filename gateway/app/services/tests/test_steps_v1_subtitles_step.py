from __future__ import annotations

import asyncio
import json
from pathlib import Path

from gateway.app.schemas import SubtitlesRequest
from gateway.app.services import steps_v1


class _FakeWorkspace:
    def __init__(self, base: Path, task_id: str, target_lang: str | None = None):
        self.base_dir = base / task_id
        self.subtitles_dir = self.base_dir / "subs"
        self.subtitles_dir.mkdir(parents=True, exist_ok=True)
        self.origin_srt_path = self.subtitles_dir / "origin.srt"
        suffix = "vi.srt" if str(target_lang or "").strip().lower() == "vi" else "mm.srt"
        self.mm_srt_path = self.subtitles_dir / suffix
        self.segments_json = self.subtitles_dir / "subtitles.json"


def test_run_subtitles_step_consumes_result_contract_for_myanmar(monkeypatch, tmp_path):
    updates: list[dict] = []
    pipeline_updates: list[dict] = []

    async def _generate_subtitles(**kwargs):
        return _fake_generate_subtitles(tmp_path, kwargs["task_id"], kwargs["target_lang"], complete=True)

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

    req = SubtitlesRequest(task_id="hf-mm-sub2", target_lang="my", force=True, translate=True)
    result = asyncio.run(steps_v1.run_subtitles_step(req))

    assert result["mm_srt"]
    final_update = updates[-1]
    assert final_update["subtitles_status"] == "ready"
    assert final_update["subtitles_error"] is None
    assert final_update["target_subtitle_current"] is True
    assert final_update["target_subtitle_current_reason"] == "ready"
    assert pipeline_updates[-1]["translation_incomplete"] == "false"


def test_run_subtitles_step_marks_vi_translation_incomplete_without_step_error(monkeypatch, tmp_path):
    updates: list[dict] = []
    pipeline_updates: list[dict] = []

    async def _generate_subtitles(**kwargs):
        return _fake_generate_subtitles(tmp_path, kwargs["task_id"], kwargs["target_lang"], complete=False)

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
        return _fake_generate_subtitles(tmp_path, kwargs["task_id"], kwargs["target_lang"], complete=False)

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

    req = SubtitlesRequest(task_id="hf-mm-sub-incomplete", target_lang="my", force=True, translate=True)
    result = asyncio.run(steps_v1.run_subtitles_step(req))

    assert result["translation_incomplete"] is True
    final_update = updates[-1]
    assert final_update["subtitles_status"] == "ready"
    assert final_update["subtitles_error"] is None
    assert final_update["target_subtitle_current"] is False
    assert final_update["target_subtitle_current_reason"] == "target_subtitle_translation_incomplete"
    assert pipeline_updates[-1]["translation_incomplete"] == "true"


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


def _fake_generate_subtitles(base: Path, task_id: str, target_lang: str, *, complete: bool) -> dict:
    workspace = _FakeWorkspace(base, task_id, target_lang)
    origin_text = "1\n00:00:00,000 --> 00:00:02,000\n你好\n"
    target_text = (
        "1\n00:00:00,000 --> 00:00:02,000\nXin chao\n"
        if str(target_lang).strip().lower() == "vi"
        else "1\n00:00:00,000 --> 00:00:02,000\nမင်္ဂလာပါ\n"
    )
    if not complete:
        target_text = ""
    workspace.origin_srt_path.write_text(origin_text, encoding="utf-8")
    workspace.mm_srt_path.write_text(target_text, encoding="utf-8")
    workspace.segments_json.write_text(json.dumps({"scenes": []}), encoding="utf-8")
    qa_payload = {
        "source_count": 1,
        "translated_count": 1 if complete else 0,
        "missing_indexes": [] if complete else [1],
        "retry_count": 0,
        "complete": complete,
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
    }


def steps_v1_hot_follow_pipeline_state(task: dict) -> tuple[str, str]:
    from gateway.app.routers import hot_follow_api as hf_router

    status, summary = hf_router._hf_pipeline_state(task, "subtitles")
    return status, summary
