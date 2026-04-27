"""W2.1 first provider absorption — ``EnvSecretResolver`` shim tests.

Covers the minimal env-backed ``SecretResolver`` introduced under
``gateway/app/services/workers/secrets/env_resolver.py``:

- construction-time mapping validation
- invocation-time-only env reads (no env access at ``__init__``)
- canonical env names only (no alias chain)
- empty / missing values fail closed (return ``None``)
- mapping is exposed read-only
"""
from __future__ import annotations

import inspect
from types import MappingProxyType

import pytest

from gateway.app.services.capability.adapters import (
    SecretRef,
    SecretResolver,
)
from gateway.app.services.workers.secrets import EnvSecretResolver
from gateway.app.services.workers.secrets import env_resolver as env_resolver_module


def _ref(name: str) -> SecretRef:
    return SecretRef(name=name)


# ---------------------------------------------------------------------------
# construction discipline
# ---------------------------------------------------------------------------


def test_resolver_subclasses_secret_resolver_abc() -> None:
    assert issubclass(EnvSecretResolver, SecretResolver)


def test_construction_does_not_read_env(monkeypatch: pytest.MonkeyPatch) -> None:
    sentinel: list[str] = []

    real_get = env_resolver_module.os.environ.get

    def _spy_get(key: str, default: object = None) -> object:
        sentinel.append(key)
        return real_get(key, default)

    monkeypatch.setattr(env_resolver_module.os.environ, "get", _spy_get)
    EnvSecretResolver({"logical": "ENV_NAME"})
    assert sentinel == []


def test_mapping_validation_rejects_non_mapping() -> None:
    with pytest.raises(TypeError):
        EnvSecretResolver(["bad"])  # type: ignore[arg-type]


def test_mapping_validation_rejects_empty_keys_or_values() -> None:
    with pytest.raises(ValueError):
        EnvSecretResolver({"": "ENV"})
    with pytest.raises(ValueError):
        EnvSecretResolver({"logical": ""})
    with pytest.raises(ValueError):
        EnvSecretResolver({"logical": 123})  # type: ignore[dict-item]


def test_mapping_is_read_only() -> None:
    resolver = EnvSecretResolver({"logical": "ENV_NAME"})
    assert isinstance(resolver.mapping, MappingProxyType)
    with pytest.raises(TypeError):
        resolver.mapping["other"] = "X"  # type: ignore[index]


# ---------------------------------------------------------------------------
# resolution behaviour
# ---------------------------------------------------------------------------


def test_resolve_reads_env_at_invoke_time(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MY_ENV", "secret-value")
    resolver = EnvSecretResolver({"logical.key": "MY_ENV"})
    assert resolver.resolve(_ref("logical.key")) == "secret-value"


def test_resolve_unknown_logical_returns_none() -> None:
    resolver = EnvSecretResolver({"logical": "ENV_NAME"})
    assert resolver.resolve(_ref("not.in.mapping")) is None


def test_resolve_missing_env_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ABSENT_ENV", raising=False)
    resolver = EnvSecretResolver({"logical": "ABSENT_ENV"})
    assert resolver.resolve(_ref("logical")) is None


def test_resolve_empty_env_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EMPTY_ENV", "   ")
    resolver = EnvSecretResolver({"logical": "EMPTY_ENV"})
    assert resolver.resolve(_ref("logical")) is None


def test_resolve_strips_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRIM_ENV", "  value  ")
    resolver = EnvSecretResolver({"logical": "TRIM_ENV"})
    assert resolver.resolve(_ref("logical")) == "value"


def test_resolve_rejects_non_secret_ref() -> None:
    resolver = EnvSecretResolver({"logical": "ENV"})
    with pytest.raises(TypeError):
        resolver.resolve("logical")  # type: ignore[arg-type]


def test_resolver_does_not_alias_logical_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    # Per ops/env/secret_loading_baseline_v1.md §3.1: no alias chain — e.g.
    # GOOGLE_API_KEY must NOT be silently consulted when GEMINI_API_KEY is
    # mapped. The resolver only reads the env name it was handed.
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "alias-leak")
    resolver = EnvSecretResolver({"gemini.translate.api_key": "GEMINI_API_KEY"})
    assert resolver.resolve(_ref("gemini.translate.api_key")) is None


# ---------------------------------------------------------------------------
# absorption boundary
# ---------------------------------------------------------------------------


def test_module_does_not_import_provider_or_packet_truth() -> None:
    src = inspect.getsource(env_resolver_module)
    assert "providers.gemini" not in src
    assert "swiftcraft" not in src.lower()
    assert "packet" not in src.lower()
