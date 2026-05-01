from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

import gateway.app.services.task_router_presenters as presenters
from gateway.app.services.task_router_presenters import (
    build_task_publish_hub,
    build_task_summaries_page,
    build_task_workbench_page_context,
    build_tasks_page_rows,
    build_task_status_payload,
    build_v1_task_status_payload,
    build_task_workbench_task_json,
    build_task_workbench_view,
    filter_tasks_for_kind,
)
from gateway.app.services.task_semantics import derive_task_semantics
from gateway.app.services.task_view_helpers import derive_status


@pytest.fixture(autouse=True)
def _stub_hot_follow_projection(monkeypatch):
    monkeypatch.setattr(
        presenters,
        "compute_hot_follow_state",
        lambda _task, base_state: dict(base_state or {}),
    )


class _Detail:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def dict(self):
        return dict(self.__dict__)


class _Repo:
    def __init__(self, rows=None):
        self._rows = dict(rows or {})

    def get(self, task_id):
        row = self._rows.get(task_id)
        return dict(row) if isinstance(row, dict) else row


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
        {
            "mm_txt_path": "/v1/tasks/hf-1/mm_txt",
            "raw_download_url": "/op/dl/hf-1?kind=raw",
            "pack_download_url": "/op/dl/hf-1?kind=pack",
        },
        workbench_kind="hot_follow",
        settings=object(),
        hot_follow_operational_defaults=lambda: {"compose_status": "never"},
        hot_follow_ui_collector=lambda _task, _settings: {"subtitle_ready": True},
    )

    assert task_json["task_id"] == "hf-1"
    assert task_json["mm_txt_path"] == "/v1/tasks/hf-1/mm_txt"
    assert task_json["raw_download_url"] == "/op/dl/hf-1?kind=raw"
    assert task_json["pack_download_url"] == "/op/dl/hf-1?kind=pack"
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


def test_build_task_publish_hub_dispatches_hot_follow_to_service_builder():
    repo = _Repo(
        {
            "hf-1": {
                "task_id": "hf-1",
                "kind": "hot_follow",
            }
        }
    )

    payload = build_task_publish_hub(
        "hf-1",
        repo,
        hot_follow_publish_hub_builder=lambda task_id, repo=None: {"task_id": task_id, "surface": "service"},
        fallback_publish_payload_builder=lambda _task: {"surface": "fallback"},
    )

    assert payload == {"task_id": "hf-1", "surface": "service"}


def test_build_task_publish_hub_keeps_fallback_builder_for_non_hot_follow():
    repo = _Repo(
        {
            "task-1": {
                "task_id": "task-1",
                "kind": "generic",
                "status": "processing",
            }
        }
    )

    payload = build_task_publish_hub(
        "task-1",
        repo,
        hot_follow_publish_hub_builder=lambda *_args, **_kwargs: {"surface": "service"},
        fallback_publish_payload_builder=lambda task: {"task_id": task["task_id"], "surface": "fallback"},
    )

    assert payload == {"task_id": "task-1", "surface": "fallback"}


def test_build_v1_task_status_payload_keeps_storage_existence_shape():
    repo = _Repo(
        {
            "hf-1": {
                "task_id": "hf-1",
                "status": "processing",
                "last_step": "subtitles",
                "subtitles_status": "done",
                "dub_status": "pending",
                "pack_status": "pending",
                "scenes_status": "pending",
                "raw_path": "deliver/tasks/hf-1/raw.mp4",
                "origin_srt_path": "deliver/tasks/hf-1/origin.srt",
                "mm_srt_path": "deliver/tasks/hf-1/mm.srt",
                "mm_audio_key": "deliver/tasks/hf-1/audio.mp3",
                "pack_key": "deliver/tasks/hf-1/pack.zip",
            }
        }
    )

    existing = {
        "deliver/tasks/hf-1/raw.mp4",
        "deliver/tasks/hf-1/origin.srt",
        "deliver/tasks/hf-1/mm.srt",
        "deliver/tasks/hf-1/mm.txt",
        "deliver/tasks/hf-1/audio.mp3",
        "deliver/tasks/hf-1/pack.zip",
    }
    payload = build_v1_task_status_payload(
        "hf-1",
        repo,
        task_key=lambda task, field: task.get(field),
        object_exists=lambda key: key in existing,
    )

    assert payload["task_id"] == "hf-1"
    assert payload["raw_exists"] is True
    assert payload["origin_srt_exists"] is True
    assert payload["mm_srt_exists"] is True
    assert payload["mm_txt_exists"] is True
    assert payload["mm_audio_exists"] is True
    assert payload["pack_exists"] is True
    assert payload["scenes_exists"] is False


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


def test_build_tasks_page_rows_preserves_board_payload_shape(monkeypatch):
    monkeypatch.setattr(
        presenters,
        "compute_hot_follow_state",
        lambda _task, base_state: dict(base_state or {}),
    )
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
            "target_lang": "mm",
            "status": "ready",
            "parse_status": None,
            "dub_status": None,
            "compose_status": None,
            "compose_last_status": None,
            "final_video_key": None,
            "final_video_path": None,
            "final_url": None,
            "final_video_url": None,
            "publish_status": None,
            "publish_key": None,
            "publish_url": None,
                "ready_gate": {},
            "target_subtitle_current": None,
            "target_subtitle_current_reason": None,
            "subtitles_content_hash": None,
            "subtitles_override_updated_at": None,
            "pipeline_config": None,
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
            # Phase 3B: additive operator-visible Board projection.
            "publishable": False,
            "head_reason": None,
            "board_bucket": "ready",
        }
    ]


def test_build_tasks_page_rows_attaches_operator_visible_board_projection(monkeypatch):
    """Phase 3B: rows expose `publishable` / `head_reason` / `board_bucket`
    derived from `ready_gate`. Authority cited:
    `gateway/app/services/operator_visible_surfaces/projections.py`.
    """
    monkeypatch.setattr(
        presenters,
        "compute_hot_follow_state",
        lambda _task, base_state: dict(base_state or {}),
    )
    rows = build_tasks_page_rows(
        [
            {
                "task_id": "ready-1",
                "platform": "hot_follow",
                "category_key": "hot_follow",
                "ready_gate": {
                    "publish_ready": True,
                    "compose_ready": True,
                    "blocking": [],
                },
            },
            {
                "task_id": "blocked-1",
                "platform": "hot_follow",
                "category_key": "hot_follow",
                "ready_gate": {
                    "publish_ready": False,
                    "compose_ready": True,
                    "blocking": ["final_missing"],
                },
            },
        ],
        kind_norm="hot_follow",
        pack_path_for_list=lambda _task: None,
        normalize_selected_tool_ids=lambda value: list(value or []),
    )
    by_id = {r["task_id"]: r for r in rows}
    assert by_id["ready-1"]["publishable"] is True
    assert by_id["ready-1"]["board_bucket"] == "publishable"
    assert by_id["ready-1"]["head_reason"] is None
    assert by_id["blocked-1"]["publishable"] is False
    assert by_id["blocked-1"]["board_bucket"] == "blocked"
    assert by_id["blocked-1"]["head_reason"] == "final_missing"


def test_build_task_workbench_task_json_attaches_operator_surfaces():
    """Phase 3B: workbench task_json carries `operator_surfaces` shape so the
    template can render the L3 strip + line-specific panel slot.
    """
    detail = _make_detail()
    task = {
        "task_id": "t1",
        "ready_gate": {
            "publish_ready": True,
            "compose_ready": True,
            "blocking": [],
        },
        "final": {"exists": True},
        "final_stale_reason": None,
        "line_specific_refs": [{"ref_id": "hot_follow_subtitle_authority"}],
    }
    out = build_task_workbench_task_json(
        task,
        detail,
        paths={},
        workbench_kind="default",
        settings=object(),
    )
    surfaces = out["operator_surfaces"]
    assert set(surfaces.keys()) == {"board", "workbench", "delivery", "hot_follow_panel"}
    assert surfaces["board"]["publishable"] is True
    assert surfaces["delivery"]["publish_gate"] is True
    assert surfaces["workbench"]["line_specific_panel"]["panel_kind"] == "hot_follow"
    assert surfaces["hot_follow_panel"]["mounted"] is True


def test_build_task_summaries_page_does_not_project_hot_follow_ready_from_final_key_only():
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
    assert summaries[0].status == "processing"


def test_build_tasks_page_rows_bind_hot_follow_board_to_computed_ready_gate(monkeypatch):
    monkeypatch.setattr(
        presenters,
        "compute_hot_follow_state",
        lambda _task, base_state: {
            **dict(base_state or {}),
            "ready_gate": {"publish_ready": True, "compose_ready": True},
            "composed_ready": True,
            "final": {
                "exists": True,
                "key": "deliver/tasks/hf-derived/final.mp4",
                "url": "/v1/tasks/hf-derived/final",
            },
            "final_url": "/v1/tasks/hf-derived/final",
            "final_video_url": "/v1/tasks/hf-derived/final",
        },
    )

    rows = build_tasks_page_rows(
        [
            {
                "task_id": "hf-derived",
                "kind": "hot_follow",
                "platform": "hot_follow",
                "category_key": "hot_follow",
                "content_lang": "vi",
                "status": "processing",
                "pack_status": "pending",
                "scenes_status": "pending",
                "created_at": "2026-03-31T00:00:00+00:00",
            }
        ],
        kind_norm="hot_follow",
        pack_path_for_list=lambda _task: None,
        normalize_selected_tool_ids=lambda value: list(value or []),
    )

    semantics = derive_task_semantics(rows[0])

    assert rows[0]["ready_gate"] == {"publish_ready": True, "compose_ready": True}
    assert rows[0]["final_video_key"] == "deliver/tasks/hf-derived/final.mp4"
    assert rows[0]["compose_status"] == "done"
    assert semantics["db_status"] == "ready"
    assert semantics["filter_status"] == "done"


def test_build_task_summaries_page_bind_hot_follow_status_to_computed_ready_gate(monkeypatch):
    monkeypatch.setattr(
        presenters,
        "compute_hot_follow_state",
        lambda _task, base_state: {
            **dict(base_state or {}),
            "ready_gate": {"publish_ready": True, "compose_ready": True},
            "composed_ready": True,
            "final": {
                "exists": True,
                "key": "deliver/tasks/hf-summary/final.mp4",
                "url": "/v1/tasks/hf-summary/final",
            },
            "final_url": "/v1/tasks/hf-summary/final",
            "final_video_url": "/v1/tasks/hf-summary/final",
        },
    )

    summaries, total = build_task_summaries_page(
        [
            {
                "task_id": "hf-summary",
                "title": "task",
                "kind": "hot_follow",
                "platform": "hot_follow",
                "category_key": "hot_follow",
                "content_lang": "vi",
                "status": "processing",
                "pack_status": "pending",
                "scenes_status": "pending",
                "created_at": "2026-03-31T00:00:00+00:00",
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


def test_build_task_summaries_page_keeps_vi_processing_when_final_exists_but_target_subtitle_is_stale():
    summaries, total = build_task_summaries_page(
        [
            {
                "task_id": "hf-vi-stale",
                "title": "task",
                "kind": "hot_follow",
                "source_url": "https://example.com/source",
                "platform": "hot_follow",
                "category_key": "hot_follow",
                "content_lang": "vi",
                "target_lang": "vi",
                "ui_lang": "zh",
                "status": "",
                "compose_status": "done",
                "final_video_key": "deliver/tasks/hf-vi-stale/final.mp4",
                "target_subtitle_current": False,
                "target_subtitle_current_reason": "target_subtitle_translation_incomplete",
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
    assert summaries[0].status == "processing"


def test_build_tasks_page_rows_keep_hot_follow_processing_without_ready_gate():
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

    assert semantics["db_status"] == "processing"
    assert semantics["filter_status"] == "processing"


def test_build_tasks_page_rows_do_not_require_publish_hub_payload_like_storage_probe(monkeypatch):
    calls = []

    def _fake_compute(_task, base_state):
        calls.append(base_state)
        return {
            **dict(base_state or {}),
            "ready_gate": {"publish_ready": True, "compose_ready": True},
            "composed_ready": True,
            "final": {
                "exists": True,
                "key": "deliver/tasks/hf-board/final.mp4",
                "url": "/v1/tasks/hf-board/final",
            },
            "final_url": "/v1/tasks/hf-board/final",
            "final_video_url": "/v1/tasks/hf-board/final",
        }

    monkeypatch.setattr(presenters, "compute_hot_follow_state", _fake_compute)

    rows = build_tasks_page_rows(
        [
            {
                "task_id": "hf-board",
                "kind": "hot_follow",
                "platform": "hot_follow",
                "category_key": "hot_follow",
                "status": "processing",
                "final_video_key": "deliver/tasks/hf-board/final.mp4",
                "created_at": "2026-04-03T00:00:00+00:00",
            }
        ],
        kind_norm="hot_follow",
        pack_path_for_list=lambda _task: None,
        normalize_selected_tool_ids=lambda value: list(value or []),
    )

    assert calls
    assert calls[0]["final"]["exists"] is True
    assert rows[0]["final_video_key"] == "deliver/tasks/hf-board/final.mp4"


def test_build_tasks_page_rows_do_not_project_hot_follow_done_from_publishable_main_deliverable():
    rows = build_tasks_page_rows(
        [
            {
                "task_id": "hf-publish-ready",
                "platform": "hot_follow",
                "source_url": "https://example.com/hf",
                "title": "publish ready",
                "category_key": "hot_follow",
                "content_lang": "vi",
                "status": "processing",
                "publish_status": "ready",
                "publish_key": "deliver/publish/hf-publish-ready.zip",
                "created_at": "2026-03-31T00:00:00+00:00",
                "pack_status": "pending",
                "scenes_status": "pending",
            }
        ],
        kind_norm="hot_follow",
        pack_path_for_list=lambda _task: None,
        normalize_selected_tool_ids=lambda value: list(value or []),
    )

    semantics = derive_task_semantics(rows[0])

    assert semantics["db_status"] == "processing"
    assert semantics["filter_status"] == "processing"
    assert semantics["show_pack_badge"] is False


def test_derive_task_semantics_enables_download_when_final_exists_without_pack():
    semantics = derive_task_semantics(
        {
            "task_id": "hf-final-only",
            "status": "ready",
            "final_video_key": "deliver/tasks/hf-final-only/final.mp4",
        }
    )

    assert semantics["download_kind"] == "final_mp4"
    assert semantics["downloadable_exists"] is True
    assert semantics["download_class"]


def test_build_tasks_page_rows_keep_vi_processing_when_final_exists_but_target_subtitle_is_stale():
    rows = build_tasks_page_rows(
        [
            {
                "task_id": "hf-vi-board-stale",
                "platform": "hot_follow",
                "source_url": "https://example.com/vi",
                "title": "task",
                "category_key": "hot_follow",
                "content_lang": "vi",
                "target_lang": "vi",
                "status": "",
                "compose_status": "done",
                "final_video_key": "deliver/tasks/hf-vi-board-stale/final.mp4",
                "target_subtitle_current": False,
                "target_subtitle_current_reason": "target_subtitle_translation_incomplete",
                "created_at": "2026-03-22T00:00:00+00:00",
            }
        ],
        kind_norm="hot_follow",
        pack_path_for_list=lambda _task: None,
        normalize_selected_tool_ids=lambda value: list(value or []),
    )

    semantics = derive_task_semantics(rows[0])

    assert semantics["db_status"] == "processing"
    assert semantics["filter_status"] == "processing"


def test_build_tasks_page_rows_keep_vi_processing_when_target_subtitle_is_stale_and_final_is_missing():
    rows = build_tasks_page_rows(
        [
            {
                "task_id": "hf-vi-board-no-final",
                "platform": "hot_follow",
                "source_url": "https://example.com/vi",
                "title": "task",
                "category_key": "hot_follow",
                "content_lang": "vi",
                "target_lang": "vi",
                "status": "processing",
                "target_subtitle_current": False,
                "target_subtitle_current_reason": "target_subtitle_translation_incomplete",
                "created_at": "2026-03-22T00:00:00+00:00",
            }
        ],
        kind_norm="hot_follow",
        pack_path_for_list=lambda _task: None,
        normalize_selected_tool_ids=lambda value: list(value or []),
    )

    semantics = derive_task_semantics(rows[0])

    assert semantics["db_status"] == "processing"
    assert semantics["filter_status"] == "processing"


def test_build_tasks_page_rows_keep_myanmar_processing_when_target_subtitle_is_stale_and_final_is_missing():
    rows = build_tasks_page_rows(
        [
            {
                "task_id": "hf-mm-board-no-final",
                "platform": "hot_follow",
                "source_url": "https://example.com/mm",
                "title": "task",
                "category_key": "hot_follow",
                "content_lang": "mm",
                "target_lang": "mm",
                "status": "processing",
                "target_subtitle_current": False,
                "target_subtitle_current_reason": "target_subtitle_source_copy",
                "created_at": "2026-03-22T00:00:00+00:00",
            }
        ],
        kind_norm="hot_follow",
        pack_path_for_list=lambda _task: None,
        normalize_selected_tool_ids=lambda value: list(value or []),
    )

    semantics = derive_task_semantics(rows[0])

    assert semantics["db_status"] == "processing"
    assert semantics["filter_status"] == "processing"


def test_derive_task_semantics_keeps_hot_follow_processing_when_main_chain_is_still_running():
    semantics = derive_task_semantics(
        {
            "task_id": "hf-running",
            "platform": "hot_follow",
            "category_key": "hot_follow",
            "status": "processing",
            "subtitles_status": "running",
            "pack_status": "pending",
            "scenes_status": "pending",
        }
    )

    assert semantics["db_status"] == "processing"
    assert semantics["filter_status"] == "processing"


def test_derive_task_semantics_keeps_hot_follow_attention_for_main_chain_failure():
    semantics = derive_task_semantics(
        {
            "task_id": "hf-failed",
            "platform": "hot_follow",
            "category_key": "hot_follow",
            "status": "processing",
            "dub_status": "failed",
            "pack_status": "pending",
            "scenes_status": "pending",
        }
    )

    assert semantics["db_status"] == "failed"
    assert semantics["filter_status"] == "attention"


def test_derive_task_semantics_does_not_let_optional_pack_hide_hot_follow_failure():
    semantics = derive_task_semantics(
        {
            "task_id": "hf-failed-with-pack",
            "platform": "hot_follow",
            "category_key": "hot_follow",
            "status": "processing",
            "compose_status": "failed",
            "pack_key": "deliver/tasks/hf-failed-with-pack/pack.zip",
        }
    )

    assert semantics["db_status"] == "failed"
    assert semantics["filter_status"] == "attention"
    assert semantics["yellow_row"] is False
    assert semantics["show_pack_badge"] is True


def test_derive_task_semantics_does_not_use_publish_key_as_hot_follow_ready_truth():
    semantics = derive_task_semantics(
        {
            "task_id": "hf-done-no-pack",
            "platform": "hot_follow",
            "category_key": "hot_follow",
            "status": "processing",
            "publish_status": "ready",
            "publish_key": "deliver/publish/hf-done-no-pack.zip",
        }
    )

    assert semantics["db_status"] == "processing"
    assert semantics["filter_status"] == "processing"
    assert semantics["show_pack_badge"] is False


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
        resolve_download_urls=lambda _task: {
            "mm_txt_path": "/v1/tasks/hf-1/mm_txt",
            "raw_download_url": "/op/dl/hf-1?kind=raw",
            "pack_download_url": "/op/dl/hf-1?kind=pack",
        },
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
    assert ctx["task_json"]["pack_download_url"] == "/op/dl/hf-1?kind=pack"
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
