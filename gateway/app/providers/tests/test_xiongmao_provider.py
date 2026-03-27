from __future__ import annotations

import asyncio

import pytest
import httpx

from gateway.app.providers import xiongmao


class _TimeoutClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, _url, params=None):
        _ = params
        request = httpx.Request("GET", "https://xiongmao.example/probe")
        raise httpx.ReadTimeout("", request=request)


class _StatusClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, _url, params=None):
        _ = params
        request = httpx.Request("GET", "https://xiongmao.example/probe")
        return httpx.Response(502, text="bad gateway", request=request)


def test_parse_with_xiongmao_keeps_nonempty_timeout_error(monkeypatch):
    monkeypatch.setattr(
        xiongmao,
        "_resolve_settings",
        lambda: ("https://api.example.com", "test-key", "test-app"),
    )
    monkeypatch.setattr(xiongmao.httpx, "AsyncClient", lambda timeout=20: _TimeoutClient())

    with pytest.raises(xiongmao.XiongmaoError, match=r"provider error: ReadTimeout GET https://xiongmao\.example/probe"):
        asyncio.run(xiongmao.parse_with_xiongmao("https://example.com/video"))


def test_parse_with_xiongmao_includes_http_status_body(monkeypatch):
    monkeypatch.setattr(
        xiongmao,
        "_resolve_settings",
        lambda: ("https://api.example.com", "test-key", "test-app"),
    )
    monkeypatch.setattr(xiongmao.httpx, "AsyncClient", lambda timeout=20: _StatusClient())

    with pytest.raises(xiongmao.XiongmaoError, match=r"provider error: http 502: bad gateway"):
        asyncio.run(xiongmao.parse_with_xiongmao("https://example.com/video"))
