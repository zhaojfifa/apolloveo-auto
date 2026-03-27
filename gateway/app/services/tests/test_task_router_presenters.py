from __future__ import annotations

from datetime import datetime, timedelta, timezone

import gateway.app.services.task_router_presenters as presenters
from gateway.app.services.task_router_presenters import (
    build_task_summaries_page,
    build_task_workbench_page_context,
    build_tasks_page_rows,
    build_task_status_payload,
    build_task_workbench_task_json,
    build_task_workbench_view,
    filter_tasks_for_kind,
)
from gateway.app.services.task_semantics import derive_task_semantics
from gateway.app.services.task_view_helpers import derive_status


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


def test_build_task_status_payload_uses_compat_shape_by_default(monkeypatch):
    detail = _make_detail()
    monkeypatch.setattr(
        presenters,
        "compat_hot_follow_task_status_shape",
        lambda _task: {"step": "dub", "phase": "ready", "provider": "azure-speech"},
    )

    payload, log_extra = build_task_status_payload("hf-1", {"kind": "hot_follow"}, detail)

    assert payload["stale"] is False
    assert log_extra["step"] == "dub"
    assert log_extra["phase"] == "ready"
    assert log_extra["provider"] == "azure-speech"


def test_build_task_workbench_view_uses_first_source_url():
    view = build_task_workbench_view(
        {"source_url": "see https://example.com/video and keep"},
        extract_first_http_url=lambda text: "https://example.com/video" if text else None,
    )

    assert view == {"source_url_open": "https://example.com/video"}


def test_filter_tasks_for_kind_keeps_apollo_avatar_compat_rule():
    items = [
        {"task_id": "1", "platform": "apollo_avatar", "category_key": "other"},
        {"task_id": "2", "platform": "other", "category_key": "apollo_avatar"},
        {"task_id": "3", "platform": "hot_follow", "category_key": "hot_follow"},
    ]

    filtered = filter_tasks_for_kind(items, "apollo_avatar")

    assert [item["task_id"] for item in filtered] == ["1", "2"]


def test_build_tasks_page_rows_preserves_board_payload_shape():
    rows = build_tasks_page_rows(
        [
            {
                "task_id": "hf-1",
                "platform": "hot_follow",
                "source_url": "https://example.com/1",
                "title": "task",
                "category_key": "hot_follow",
                "content_lang": "mm",
                "status": "ready",
                "created_at": "2026-03-22T00:00:00+00:00",
                "pack_key": "deliver/tasks/hf-1/pack.zip",
                "cover_url": "https://example.com/cover.jpg",
                "selected_tool_ids": ["a", "b"],
            }
        ],
        kind_norm="hot_follow",
        pack_path_for_list=lambda _task: "deliver/tasks/hf-1/pack.zip",
        normalize_selected_tool_ids=lambda value: list(value or []),
    )

    assert rows == [
        {
            "task_id": "hf-1",
            "platform": "hot_follow",
            "source_url": "https://example.com/1",
            "title": "task",
            "category_key": "hot_follow",
            "content_lang": "mm",
            "status": "ready",
            "parse_status": None,
            "dub_status": None,
            "compose_status": None,
            "compose_last_status": None,
            "final_video_key": None,
            "final_video_path": None,
            "final_url": None,
            "final_video_url": None,
            "ready_gate": None,
            "created_at": "2026-03-22T00:00:00+00:00",
            "pack_path": "deliver/tasks/hf-1/pack.zip",
            "pack_key": "deliver/tasks/hf-1/pack.zip",
            "pack_url": None,
            "deliver_pack_key": None,
            "cover_url": "https://example.com/cover.jpg",
            "thumb_url": None,
            "raw_path": None,
            "raw_key": None,
            "raw_url": None,
            "video_url": None,
            "preview_url": None,
            "ui_lang": "",
            "selected_tool_ids": ["a", "b"],
        }
    ]


def test_build_task_summaries_page_projects_ready_from_final_facts_before_unknown_status():
    summaries, total = build_task_summaries_page(
        [
            {
                "task_id": "hf-vi-done",
                "title": "task",
                "kind": "hot_follow",
                "source_url": "https://example.com/source",
                "platform": "hot_follow",
                "category_key": "hot_follow",
                "content_lang": "vi",
                "ui_lang": "zh",
                "status": "",
                "compose_status": "done",
                "final_video_key": "deliver/tasks/hf-vi-done/final.mp4",
                "created_at": "2026-03-22T00:00:00+00:00",
            }
        ],
        kind_norm="hot_follow",
        page=1,
        page_size=20,
        resolve_download_urls=lambda _task: {"pack_path": None, "scenes_path": None},
        derive_status=derive_status,
        extract_first_http_url=lambda text: "https://example.com/source" if text else None,
        coerce_datetime=lambda value: datetime.fromisoformat(str(value).replace("Z", "+00:00")) if value else None,
        parse_pipeline_config=lambda value: dict(value or {}),
        normalize_selected_tool_ids=lambda value: list(value or []),
        task_summary_cls=_Detail,
    )

    assert total == 1
    assert summaries[0].status == "ready"


def test_build_tasks_page_rows_carry_fact_fields_needed_for_board_ready_projection():
    rows = build_tasks_page_rows(
        [
            {
                "task_id": "hf-vi-board",
                "platform": "hot_follow",
                "source_url": "https://example.com/vi",
                "title": "task",
                "category_key": "hot_follow",
                "content_lang": "vi",
                "status": "",
                "compose_status": "done",
                "final_video_key": "deliver/tasks/hf-vi-board/final.mp4",
                "created_at": "2026-03-22T00:00:00+00:00",
            }
        ],
        kind_norm="hot_follow",
        pack_path_for_list=lambda _task: None,
        normalize_selected_tool_ids=lambda value: list(value or []),
    )

    semantics = derive_task_semantics(rows[0])

    assert semantics["db_status"] == "ready"
    assert semantics["filter_status"] == "done"


def test_build_task_workbench_page_context_keeps_hot_follow_enrichment():
    detail = _make_detail()

    class _Spec:
        kind = "hot_follow"
        js = "/static/js/hf.js"

    class _Settings:
        workspace_root = "/tmp/ws"
        douyin_api_base = "https://douyin.example"
        whisper_model = "whisper-x"
        gpt_model = "gpt-x"
        asr_backend = "whisper"
        subtitles_backend = "gemini"
        gemini_model = "gemini-x"

    ctx = build_task_workbench_page_context(
        {"kind": "hot_follow", "source_url": "https://example.com/source"},
        spec=_Spec(),
        settings=_Settings(),
        task_to_detail=lambda _task: detail,
        resolve_download_urls=lambda _task: {"mm_txt_path": "/v1/tasks/hf-1/mm_txt"},
        build_task_workbench_task_json=build_task_workbench_task_json,
        build_task_workbench_view=build_task_workbench_view,
        extract_first_http_url=lambda text: "https://example.com/source" if text else None,
        hot_follow_operational_defaults=lambda: {"compose_status": "never"},
        hot_follow_ui_collector=lambda _task, _settings: {"subtitle_ready": True},
        features={"ops": True},
    )

    assert ctx["task"].task_id == "hf-1"
    assert ctx["task_json"]["compose_status"] == "never"
    assert ctx["task_json"]["subtitle_ready"] is True
    assert ctx["task_view"]["source_url_open"] == "https://example.com/source"
    assert ctx["env_summary"]["workspace_root"] == "/tmp/ws"
    assert ctx["features"] == {"ops": True}
    assert ctx["workbench_kind"] == "hot_follow"
    assert ctx["workbench_js"] == "/static/js/hf.js"


def test_build_task_workbench_page_context_uses_compat_hooks_by_default(monkeypatch):
    detail = _make_detail()

    class _Spec:
        kind = "hot_follow"
        js = "/static/js/hf.js"

    class _Settings:
        workspace_root = "/tmp/ws"
        douyin_api_base = "https://douyin.example"
        whisper_model = "whisper-x"
        gpt_model = "gpt-x"
        asr_backend = "whisper"
        subtitles_backend = "gemini"
        gemini_model = "gemini-x"

    monkeypatch.setattr(
        presenters,
        "compat_hot_follow_operational_defaults",
        lambda: {"compose_status": "compat-default"},
    )
    monkeypatch.setattr(
        presenters,
        "compat_collect_hot_follow_workbench_ui",
        lambda _task, _settings: {"subtitle_ready": True},
    )

    ctx = build_task_workbench_page_context(
        {"kind": "hot_follow", "source_url": "https://example.com/source"},
        spec=_Spec(),
        settings=_Settings(),
        task_to_detail=lambda _task: detail,
        resolve_download_urls=lambda _task: {"mm_txt_path": "/v1/tasks/hf-1/mm_txt"},
        build_task_workbench_task_json=build_task_workbench_task_json,
        build_task_workbench_view=build_task_workbench_view,
        extract_first_http_url=lambda text: "https://example.com/source" if text else None,
        features={"ops": True},
    )

    assert ctx["task_json"]["compose_status"] == "compat-default"
    assert ctx["task_json"]["subtitle_ready"] is True


def test_build_task_summaries_page_preserves_router_summary_fields():
    summaries, total = build_task_summaries_page(
        [
            {
                "task_id": "hf-1",
                "title": "task",
                "kind": "hot_follow",
                "source_url": "https://example.com/source",
                "platform": "hot_follow",
                "category_key": "hot_follow",
                "content_lang": "mm",
                "ui_lang": "zh",
                "status": "processing",
                "last_step": "subtitles",
                "scenes_status": "pending",
                "subtitles_status": "done",
                "created_at": "2026-03-22T00:00:00+00:00",
                "updated_at": "2026-03-22T01:00:00+00:00",
                "selected_tool_ids": ["tool-a"],
                "pipeline_config": {"mode": "fast"},
            }
        ],
        kind_norm="hot_follow",
        page=1,
        page_size=20,
        resolve_download_urls=lambda _task: {"pack_path": "/pack.zip", "scenes_path": "/scenes.zip"},
        derive_status=lambda task: str(task.get("status") or "pending"),
        extract_first_http_url=lambda text: "https://example.com/source" if text else None,
        coerce_datetime=lambda value: datetime.fromisoformat(str(value).replace("Z", "+00:00")) if value else None,
        parse_pipeline_config=lambda value: dict(value or {}),
        normalize_selected_tool_ids=lambda value: list(value or []),
        task_summary_cls=_Detail,
    )

    assert total == 1
    assert summaries[0].task_id == "hf-1"
    assert summaries[0].pack_path == "/pack.zip"
    assert summaries[0].scenes_path == "/scenes.zip"
    assert summaries[0].source_link_url == "https://example.com/source"
    assert summaries[0].selected_tool_ids == ["tool-a"]
    assert summaries[0].pipeline_config == {"mode": "fast"}
