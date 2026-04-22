from __future__ import annotations

from starlette.requests import Request

from gateway.app.services import task_stream_views


def _request_with_range(value: str | None) -> Request:
    headers = []
    if value is not None:
        headers.append((b"range", value.encode("utf-8")))
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": headers,
        }
    )


class _Logger:
    def __init__(self):
        self.info_calls = []
        self.exception_calls = []

    def info(self, event_name, *, extra=None):
        self.info_calls.append((event_name, extra or {}))

    def exception(self, message, *, extra=None):
        self.exception_calls.append((message, extra or {}))


def test_parse_http_range_supports_explicit_and_suffix_ranges():
    assert task_stream_views.parse_http_range("bytes=2-4", 10) == (2, 4)
    assert task_stream_views.parse_http_range("bytes=-3", 10) == (7, 9)


def test_build_stream_head_response_uses_resolved_meta():
    logger = _Logger()
    response = task_stream_views.build_stream_head_response(
        "task-1",
        object(),
        resolve_meta=lambda _task_id, _repo: ("deliver/tasks/task-1/final.mp4", 42, "video/mp4"),
        logger=logger,
        event_name="FINAL_STREAM",
        failure_log="final_head_failed",
        failure_detail="final head failed",
        default_content_type="video/mp4",
    )

    assert response.status_code == 200
    assert response.headers["Content-Length"] == "42"
    assert response.headers["Content-Type"] == "video/mp4"
    assert logger.info_calls[0][0] == "FINAL_STREAM"


def test_build_stream_download_response_returns_partial_content_headers():
    logger = _Logger()
    response = task_stream_views.build_stream_download_response(
        "task-1",
        _request_with_range("bytes=2-4"),
        object(),
        resolve_meta=lambda _task_id, _repo: ("deliver/tasks/task-1/audio.mp3", 10, "audio/mpeg"),
        parse_range=task_stream_views.parse_http_range,
        stream_object_range_loader=lambda _key, start, end: ([b"abc"], end - start + 1),
        logger=logger,
        event_name="AUDIO_STREAM",
        resolve_failure_log="audio_get_failed",
        resolve_failure_detail="audio get failed",
        stream_failure_log="audio_stream_failed",
        stream_failure_detail="audio stream failed",
    )

    assert response.status_code == 206
    assert response.headers["Content-Range"] == "bytes 2-4/10"
    assert response.headers["Content-Length"] == "3"
    assert response.media_type == "audio/mpeg"
