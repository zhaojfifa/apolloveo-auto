"""Akool provider client skeleton tests (PR-1).

Covers ``gateway/app/services/providers/akool/client.py``:

- skeleton boundary: no live call possible (no transport → ``NOT_WIRED``);
  module imports no HTTP library and reads no env
- Akool ``code`` → closed provider-kind mapping
- response parsing (create + single result read) via an injected fake
  transport — never a network call
- the temporary-URL-must-not-be-deliverable rule
- secret handling: the api key appears only on the outgoing request header,
  never in parsed results / errors
"""
from __future__ import annotations

import inspect
from typing import Any, Dict, List

import pytest

from gateway.app.services.providers.akool import (
    AKOOL_SUCCESS_CODE,
    AkoolCapability,
    AkoolClient,
    AkoolClientConfig,
    AkoolError,
    AkoolErrorKind,
    AkoolHttpRequest,
    AkoolHttpResponse,
    AkoolTaskStatus,
    ProviderTemporaryOutput,
    classify_akool_code,
)
from gateway.app.services.providers.akool import client as client_module


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _config(**overrides: Any) -> AkoolClientConfig:
    base: Dict[str, Any] = {"api_key": "secret-key-123"}
    base.update(overrides)
    return AkoolClientConfig(**base)


class _RecordingTransport:
    """Fake transport that records requests and returns a queued response."""

    def __init__(self, responses: List[AkoolHttpResponse]) -> None:
        self._responses = list(responses)
        self.requests: List[AkoolHttpRequest] = []

    def __call__(self, request: AkoolHttpRequest) -> AkoolHttpResponse:
        self.requests.append(request)
        return self._responses.pop(0)


# ---------------------------------------------------------------------------
# skeleton boundary — no live call
# ---------------------------------------------------------------------------


def test_construction_is_io_free_and_unwired_by_default() -> None:
    client = AkoolClient(_config())
    assert client.is_wired is False


def test_create_without_transport_raises_not_wired() -> None:
    client = AkoolClient(_config())
    with pytest.raises(AkoolError) as exc:
        client.create_task(AkoolCapability.IMAGE_TO_VIDEO, {"image_url": "x"})
    assert exc.value.kind is AkoolErrorKind.NOT_WIRED


def test_read_without_transport_raises_not_wired() -> None:
    client = AkoolClient(_config())
    with pytest.raises(AkoolError) as exc:
        client.read_task_result(AkoolCapability.IMAGE_TO_VIDEO, "task-1")
    assert exc.value.kind is AkoolErrorKind.NOT_WIRED


def test_client_module_imports_no_http_library_and_no_env() -> None:
    src = inspect.getsource(client_module)
    assert "import httpx" not in src
    assert "import requests" not in src
    assert "os.getenv" not in src
    assert "os.environ" not in src
    # no donor namespace import (the authority-doc path may be cited in prose)
    assert "from swiftcraft" not in src
    assert "import swiftcraft" not in src


# ---------------------------------------------------------------------------
# code → kind mapping
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("code", "kind"),
    [
        (1003, AkoolErrorKind.INVALID_REQUEST),
        (1005, AkoolErrorKind.RATE_LIMITED),
        (1006, AkoolErrorKind.QUOTA),
        (1104, AkoolErrorKind.QUOTA),
        (1103, AkoolErrorKind.QUOTA),
        (1213, AkoolErrorKind.QUOTA),
        (1008, AkoolErrorKind.NOT_FOUND),
        (1014, AkoolErrorKind.NOT_FOUND),
        (1009, AkoolErrorKind.AUTH),
        (1101, AkoolErrorKind.AUTH),
        (1102, AkoolErrorKind.AUTH),
        (1109, AkoolErrorKind.AUTH),
        (1200, AkoolErrorKind.AUTH),
        (9999, AkoolErrorKind.UPSTREAM),  # unknown → upstream
    ],
)
def test_classify_akool_code(code: int, kind: AkoolErrorKind) -> None:
    assert classify_akool_code(code) is kind


def test_classify_rejects_success_code() -> None:
    with pytest.raises(ValueError):
        classify_akool_code(AKOOL_SUCCESS_CODE)


# ---------------------------------------------------------------------------
# create + read parsing via fake transport
# ---------------------------------------------------------------------------


def test_create_task_parses_provider_task_id_and_status() -> None:
    transport = _RecordingTransport(
        [AkoolHttpResponse(200, {"code": 1000, "data": {"_id": "vid-1", "status": 1}})]
    )
    client = AkoolClient(_config(), transport=transport)
    created = client.create_task(AkoolCapability.IMAGE_TO_VIDEO, {"image_url": "x", "prompt": "y"})
    assert created.provider_task_id == "vid-1"
    assert created.status is AkoolTaskStatus.QUEUED
    # create reached the create endpoint via POST
    assert transport.requests[0].method == "POST"
    assert transport.requests[0].url.endswith("/api/open/v4/image2Video/createBySourcePrompt")


def test_read_success_wraps_output_as_non_deliverable() -> None:
    transport = _RecordingTransport(
        [AkoolHttpResponse(200, {"code": 1000, "data": {"video_status": 3, "video": "https://tmp.akool/v.mp4"}})]
    )
    client = AkoolClient(_config(), transport=transport)
    result = client.read_task_result(AkoolCapability.TALKING_AVATAR, "model-1")
    assert result.status is AkoolTaskStatus.SUCCESS
    assert isinstance(result.output, ProviderTemporaryOutput)
    assert result.output.url == "https://tmp.akool/v.mp4"
    # the rule: never a deliverable
    assert result.output.is_deliverable is False
    assert result.output.requires_copy_into_apollo_storage is True


def test_read_processing_has_no_output() -> None:
    transport = _RecordingTransport(
        [AkoolHttpResponse(200, {"code": 1000, "data": {"video_status": 2}})]
    )
    client = AkoolClient(_config(), transport=transport)
    result = client.read_task_result(AkoolCapability.LIP_SYNC, "model-2")
    assert result.status is AkoolTaskStatus.PROCESSING
    assert result.output is None


@pytest.mark.parametrize(
    ("field", "value", "status"),
    [
        ("video_status", 1, AkoolTaskStatus.QUEUED),
        ("faceswap_status", 4, AkoolTaskStatus.FAILED),
        ("status", 2, AkoolTaskStatus.PROCESSING),
    ],
)
def test_status_normalised_across_three_field_families(field, value, status) -> None:
    transport = _RecordingTransport(
        [AkoolHttpResponse(200, {"code": 1000, "data": {field: value, "_id": "j"}})]
    )
    client = AkoolClient(_config(), transport=transport)
    created = client.create_task(AkoolCapability.FACE_SWAP, {"source_url": "s", "target_url": "t"})
    assert created.status is status


def test_non_success_code_raises_mapped_provider_error() -> None:
    transport = _RecordingTransport([AkoolHttpResponse(200, {"code": 1104, "msg": "no credit"})])
    client = AkoolClient(_config(), transport=transport)
    with pytest.raises(AkoolError) as exc:
        client.create_task(AkoolCapability.IMAGE_TO_VIDEO, {"image_url": "x"})
    assert exc.value.kind is AkoolErrorKind.QUOTA
    assert exc.value.code == 1104


def test_protocol_error_on_unrecognised_status() -> None:
    transport = _RecordingTransport(
        [AkoolHttpResponse(200, {"code": 1000, "data": {"video_status": 7, "_id": "j"}})]
    )
    client = AkoolClient(_config(), transport=transport)
    with pytest.raises(AkoolError) as exc:
        client.create_task(AkoolCapability.TALKING_PHOTO, {"talking_photo_url": "p", "audio_url": "a"})
    assert exc.value.kind is AkoolErrorKind.PROTOCOL


# ---------------------------------------------------------------------------
# temporary-URL-must-not-be-deliverable rule
# ---------------------------------------------------------------------------


def test_provider_temporary_output_as_deliverable_raises() -> None:
    out = ProviderTemporaryOutput(url="https://tmp.akool/x.mp4")
    assert out.is_deliverable is False
    with pytest.raises(AkoolError):
        out.as_deliverable()


# ---------------------------------------------------------------------------
# secret handling
# ---------------------------------------------------------------------------


def test_api_key_only_on_request_header_never_in_results() -> None:
    transport = _RecordingTransport(
        [AkoolHttpResponse(200, {"code": 1000, "data": {"_id": "vid-1", "status": 1}})]
    )
    client = AkoolClient(_config(api_key="TOP-SECRET"), transport=transport)
    created = client.create_task(AkoolCapability.IMAGE_TO_VIDEO, {"image_url": "x"})
    # key is on the outgoing header
    assert transport.requests[0].headers["x-api-key"] == "TOP-SECRET"
    # key is NOT in the parsed result
    assert "TOP-SECRET" not in repr(created)
