from __future__ import annotations

from datetime import datetime, timedelta, timezone

from gateway.app.services.task_router_presenters import (
    build_task_status_payload,
    build_task_workbench_task_json,
    build_task_workbench_view,
)


class _Detail:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def dict(self):
        return dict(self.__dict__)


def _make_detail() -> _Detail:
    return _Detail(
        task_id="hf-1",
        status="processing",
        platform="douyin",
        category_key="hot_follow",
        content_lang="mm",
        ui_lang="zh",
        source_url="https://example.com/source",
        pipeline_config={},
        no_dub=False,
        dub_skip_reason=None,
        raw_path="/v1/tasks/hf-1/raw",
        origin_srt_path="/v1/tasks/hf-1/subs_origin",
        mm_srt_path="/v1/tasks/hf-1/subs_mm",
        mm_audio_path="/v1/tasks/hf-1/audio_mm",
        pack_path="/v1/tasks/hf-1/pack",
        scenes_path="/v1/tasks/hf-1/scenes",
        scenes_status="pending",
        scenes_key=None,
        scenes_error=None,
        subtitles_status="done",
        subtitles_key="deliver/tasks/hf-1/subs/mm.srt",
        subtitles_error=None,
        publish_status="pending",
        publish_provider=None,
        publish_key=None,
        publish_url=None,
        published_at=None,
        updated_at=datetime.now(timezone.utc),
        dub_status="pending",
        pack_status="pending",
        last_step="subtitles",
    )


def test_build_task_workbench_task_json_applies_hot_follow_enrichment():
    detail = _make_detail()
    task_json = build_task_workbench_task_json(
        {"kind": "hot_follow"},
        detail,
        {"mm_txt_path": "/v1/tasks/hf-1/mm_txt"},
        workbench_kind="hot_follow",
        settings=object(),
        hot_follow_operational_defaults=lambda: {"compose_status": "never"},
        hot_follow_ui_collector=lambda _task, _settings: {"subtitle_ready": True},
    )

    assert task_json["task_id"] == "hf-1"
    assert task_json["mm_txt_path"] == "/v1/tasks/hf-1/mm_txt"
    assert task_json["compose_status"] == "never"
    assert task_json["subtitle_ready"] is True


def test_build_task_status_payload_keeps_stale_logic_and_shape_log_fields():
    detail = _make_detail()
    detail.updated_at = datetime.now(timezone.utc) - timedelta(seconds=1905)
    detail.subtitles_status = "running"

    payload, log_extra = build_task_status_payload(
        "hf-1",
        {"kind": "hot_follow"},
        detail,
        task_status_shape=lambda _task: {"step": "subtitles", "phase": "running", "provider": "gemini"},
    )

    assert payload["stale"] is True
    assert payload["stale_reason"] == "running_but_not_updated"
    assert payload["stale_for_seconds"] >= 1800
    assert log_extra["task_id"] == "hf-1"
    assert log_extra["step"] == "subtitles"
    assert log_extra["phase"] == "running"
    assert log_extra["provider"] == "gemini"


def test_build_task_workbench_view_uses_first_source_url():
    view = build_task_workbench_view(
        {"source_url": "see https://example.com/video and keep"},
        extract_first_http_url=lambda text: "https://example.com/video" if text else None,
    )

    assert view == {"source_url_open": "https://example.com/video"}
