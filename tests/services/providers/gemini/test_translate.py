"""W2.1 first provider absorption — Gemini text-translate provider client tests.

Covers the construction / invocation contract of
``gateway/app/services/providers/gemini/translate.py``:

- I/O-free construction (no env reads, no network, no logger binding)
- network access only inside ``translate_segments``
- closed ``GeminiTextTranslateErrorKind`` mapping for status codes / timeouts
- cooperative cancellation via injected ``cancel_check``
- response parsing (fenced JSON, embedded JSON, `segments` / `items` keys)
- explicit refusal of donor business-layer concerns (no concise rewrite,
  no fallback chain, no env reads)

Provider-typed errors are not mapped to ``AdapterError`` here — that mapping
is the worker-side adapter binding's job (covered separately under
``tests/services/workers/adapters/gemini/``).
"""
from __future__ import annotations

import inspect
import json
from typing import Any

import httpx
import pytest

from gateway.app.services.providers.gemini import (
    GeminiTextTranslateClient,
    GeminiTextTranslateConfig,
    GeminiTextTranslateError,
    GeminiTextTranslateErrorKind,
    GeminiTextTranslateRequest,
    GeminiTextTranslateSegment,
)
from gateway.app.services.providers.gemini import translate as translate_module


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _config(**overrides: Any) -> GeminiTextTranslateConfig:
    base = dict(
        api_key="test-key",
        base_url="https://example.invalid/v1",
        model="gemini-2.0-flash",
        timeout_seconds=5.0,
        connect_timeout_seconds=2.0,
    )
    base.update(overrides)
    return GeminiTextTranslateConfig(**base)


def _request(*texts: str, target_lang: str = "zh") -> GeminiTextTranslateRequest:
    return GeminiTextTranslateRequest(
        segments=tuple(
            GeminiTextTranslateSegment(index=i + 1, text=t)
            for i, t in enumerate(texts)
        ),
        target_lang=target_lang,
    )


def _content_payload(content: str) -> dict[str, Any]:
    return {"choices": [{"message": {"content": content}}]}


class _StubClient:
    """Minimal stand-in for ``httpx.Client`` used as a context manager."""

    def __init__(self, response: httpx.Response | Exception) -> None:
        self._response = response
        self.calls: list[tuple[str, dict[str, Any], dict[str, str]]] = []

    def __enter__(self) -> "_StubClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def post(
        self,
        url: str,
        *,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        self.calls.append((url, json or {}, headers or {}))
        if isinstance(self._response, Exception):
            raise self._response
        return self._response


def _factory_for(stub: _StubClient):
    def _factory(_timeout: httpx.Timeout) -> _StubClient:
        return stub

    return _factory


def _ok_response(content: str) -> httpx.Response:
    return httpx.Response(200, json=_content_payload(content))


# ---------------------------------------------------------------------------
# construction discipline
# ---------------------------------------------------------------------------


def test_module_import_is_side_effect_free() -> None:
    # AST scan: top level of the module must contain no I/O calls and no
    # imports of os.environ-reading or networking modules (network access
    # is allowed only inside ``translate_segments``).
    import ast

    src = inspect.getsource(translate_module)
    tree = ast.parse(src)
    forbidden_top_level_calls = {
        "open", "eval", "exec",
    }
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            func = node.value.func
            name = getattr(func, "id", None) or getattr(func, "attr", None)
            assert name not in forbidden_top_level_calls
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            mod_name = getattr(node, "module", None) or ""
            for alias in getattr(node, "names", []):
                full = mod_name or alias.name
                assert "requests" not in full
    assert "os.environ" not in src
    assert "os.getenv" not in src


def test_config_rejects_invalid_fields() -> None:
    with pytest.raises(ValueError):
        GeminiTextTranslateConfig(api_key="", base_url="https://x", model="m")
    with pytest.raises(ValueError):
        GeminiTextTranslateConfig(api_key="k", base_url="", model="m")
    with pytest.raises(ValueError):
        GeminiTextTranslateConfig(api_key="k", base_url="x", model="")
    with pytest.raises(ValueError):
        GeminiTextTranslateConfig(
            api_key="k", base_url="x", model="m", timeout_seconds=0
        )
    with pytest.raises(ValueError):
        GeminiTextTranslateConfig(
            api_key="k", base_url="x", model="m", connect_timeout_seconds=-1
        )


def test_client_construction_is_io_free() -> None:
    # No network call factory provided; constructing the client must not
    # touch the network or read env.
    client = GeminiTextTranslateClient(_config())
    assert client.config.api_key == "test-key"
    assert client.config.model == "gemini-2.0-flash"


def test_client_rejects_non_config() -> None:
    with pytest.raises(TypeError):
        GeminiTextTranslateClient("not-a-config")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# happy path + cancellation
# ---------------------------------------------------------------------------


def test_empty_segments_returns_empty_result_without_io() -> None:
    client = GeminiTextTranslateClient(_config())
    request = GeminiTextTranslateRequest(segments=(), target_lang="zh")

    def _no_factory(_t: httpx.Timeout) -> _StubClient:  # pragma: no cover
        raise AssertionError("network factory must not be called for empty input")

    result = client.translate_segments(request, http_client_factory=_no_factory)
    assert dict(result.translated) == {}
    assert result.missing_indexes == ()
    assert result.json_repair_used is False


def test_translate_segments_happy_path() -> None:
    body = {
        "segments": [
            {"index": 1, "text": "你好"},
            {"index": 2, "text": "世界"},
        ]
    }
    stub = _StubClient(_ok_response(json.dumps(body)))
    client = GeminiTextTranslateClient(_config())

    result = client.translate_segments(
        _request("hello", "world"),
        http_client_factory=_factory_for(stub),
    )

    assert dict(result.translated) == {1: "你好", 2: "世界"}
    assert result.missing_indexes == ()
    assert result.json_repair_used is False
    assert len(stub.calls) == 1
    url, payload, headers = stub.calls[0]
    assert url == "https://example.invalid/v1/chat/completions"
    assert headers["Authorization"] == "Bearer test-key"
    assert payload["model"] == "gemini-2.0-flash"
    assert payload["messages"][0]["role"] == "system"


def test_cancel_check_short_circuits_before_network() -> None:
    def _no_factory(_t: httpx.Timeout) -> _StubClient:  # pragma: no cover
        raise AssertionError("network must not be reached when cancelled")

    client = GeminiTextTranslateClient(_config())
    with pytest.raises(GeminiTextTranslateError) as exc_info:
        client.translate_segments(
            _request("hi"),
            cancel_check=lambda: True,
            http_client_factory=_no_factory,
        )
    assert exc_info.value.kind is GeminiTextTranslateErrorKind.CANCELLED


def test_partial_response_records_missing_indexes() -> None:
    body = {"segments": [{"index": 1, "text": "你好"}]}
    stub = _StubClient(_ok_response(json.dumps(body)))
    client = GeminiTextTranslateClient(_config())

    result = client.translate_segments(
        _request("hello", "world"),
        http_client_factory=_factory_for(stub),
    )
    assert dict(result.translated) == {1: "你好"}
    assert result.missing_indexes == (2,)


def test_fenced_json_triggers_repair_flag() -> None:
    body = "```json\n" + json.dumps({"items": [{"index": 1, "text": "ok"}]}) + "\n```"
    stub = _StubClient(_ok_response(body))
    client = GeminiTextTranslateClient(_config())

    result = client.translate_segments(
        _request("hello"), http_client_factory=_factory_for(stub)
    )
    assert dict(result.translated) == {1: "ok"}
    assert result.json_repair_used is True


# ---------------------------------------------------------------------------
# failure mapping (provider-typed; AdapterError mapping happens in binding)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("status", "kind"),
    [
        (400, GeminiTextTranslateErrorKind.INVALID_REQUEST),
        (401, GeminiTextTranslateErrorKind.AUTH),
        (403, GeminiTextTranslateErrorKind.AUTH),
        (408, GeminiTextTranslateErrorKind.TIMEOUT),
        (429, GeminiTextTranslateErrorKind.RATE_LIMITED),
        (500, GeminiTextTranslateErrorKind.UPSTREAM),
        (502, GeminiTextTranslateErrorKind.UPSTREAM),
    ],
)
def test_status_codes_map_to_provider_kinds(status: int, kind: GeminiTextTranslateErrorKind) -> None:
    stub = _StubClient(httpx.Response(status, text="boom"))
    client = GeminiTextTranslateClient(_config())
    with pytest.raises(GeminiTextTranslateError) as exc_info:
        client.translate_segments(
            _request("hi"), http_client_factory=_factory_for(stub)
        )
    assert exc_info.value.kind is kind
    assert exc_info.value.status == status
    assert exc_info.value.upstream_snippet == "boom"


def test_httpx_timeout_maps_to_timeout_kind() -> None:
    stub = _StubClient(httpx.ReadTimeout("read timeout"))
    client = GeminiTextTranslateClient(_config())
    with pytest.raises(GeminiTextTranslateError) as exc_info:
        client.translate_segments(
            _request("hi"), http_client_factory=_factory_for(stub)
        )
    assert exc_info.value.kind is GeminiTextTranslateErrorKind.TIMEOUT


def test_httpx_transport_error_maps_to_upstream() -> None:
    stub = _StubClient(httpx.ConnectError("dns boom"))
    client = GeminiTextTranslateClient(_config())
    with pytest.raises(GeminiTextTranslateError) as exc_info:
        client.translate_segments(
            _request("hi"), http_client_factory=_factory_for(stub)
        )
    assert exc_info.value.kind is GeminiTextTranslateErrorKind.UPSTREAM


def test_non_json_response_maps_to_protocol() -> None:
    stub = _StubClient(httpx.Response(200, text="not json"))
    client = GeminiTextTranslateClient(_config())
    with pytest.raises(GeminiTextTranslateError) as exc_info:
        client.translate_segments(
            _request("hi"), http_client_factory=_factory_for(stub)
        )
    assert exc_info.value.kind is GeminiTextTranslateErrorKind.PROTOCOL


def test_empty_choices_content_maps_to_protocol() -> None:
    stub = _StubClient(httpx.Response(200, json={"choices": [{"message": {"content": ""}}]}))
    client = GeminiTextTranslateClient(_config())
    with pytest.raises(GeminiTextTranslateError) as exc_info:
        client.translate_segments(
            _request("hi"), http_client_factory=_factory_for(stub)
        )
    assert exc_info.value.kind is GeminiTextTranslateErrorKind.PROTOCOL


def test_missing_segments_list_maps_to_protocol() -> None:
    stub = _StubClient(_ok_response(json.dumps({"unexpected": True})))
    client = GeminiTextTranslateClient(_config())
    with pytest.raises(GeminiTextTranslateError) as exc_info:
        client.translate_segments(
            _request("hi"), http_client_factory=_factory_for(stub)
        )
    assert exc_info.value.kind is GeminiTextTranslateErrorKind.PROTOCOL


# ---------------------------------------------------------------------------
# absorption boundary
# ---------------------------------------------------------------------------


def test_module_does_not_read_env_at_any_call() -> None:
    # Sanity: the provider client must never touch os.environ. The whole
    # module's source code carries no `os.getenv` / `os.environ` reads.
    import inspect

    src = inspect.getsource(translate_module)
    assert "os.getenv" not in src
    assert "os.environ" not in src


def test_module_does_not_import_donor_or_capability_adapters() -> None:
    # The provider client must not import donor packages, and must not
    # depend on AdapterError at all (mapping into AdapterError happens at
    # the worker-side binding only). AST-only check; docstrings may name
    # these symbols for traceability.
    import ast

    tree = ast.parse(inspect.getsource(translate_module))
    forbidden_modules = {
        "swiftcraft",
        "backend.app.utils.translate_gemini",
        "gateway.app.services.capability.adapters",
        "gateway.app.services.capability.adapters.base",
    }
    forbidden_names = {"AdapterError", "AdapterErrorCategory"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not any(alias.name.startswith(m) for m in forbidden_modules)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            assert not any(mod.startswith(m) for m in forbidden_modules)
            for alias in node.names:
                assert alias.name not in forbidden_names
        elif isinstance(node, ast.Name):
            assert node.id not in forbidden_names
