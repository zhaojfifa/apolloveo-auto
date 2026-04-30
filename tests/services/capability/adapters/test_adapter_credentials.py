"""B1 — base-only auth / credential surface tests.

Covers the construction-time credential surface introduced for the W2.1
Base-Only Adapter Preparation Wave (B1):

- ``SecretRef``  — logical, provider-agnostic secret handle
- ``SecretResolver`` — abstract resolver surface (no implementation in base)
- ``AdapterCredentials`` — frozen envelope injected at adapter construction
- ``AdapterBase.__init__`` accepts and stores credentials without I/O

The tests also enforce the boundary that B1 introduces no provider /
business semantics and no truth fields.
"""
from __future__ import annotations

import dataclasses
import inspect
from typing import Optional

import pytest

from gateway.app.services.capability.adapters import (
    AdapterCredentials,
    AdapterInvocation,
    AdapterResult,
    SecretRef,
    SecretResolver,
    UnderstandingAdapter,
)
from gateway.app.services.capability.adapters import base as base_module


# ---------------------------------------------------------------------------
# Test helpers (live in the test file only — never under base/)
# ---------------------------------------------------------------------------


class _StubResolver(SecretResolver):
    """Test-only resolver. Records calls so we can assert no I/O at ctor."""

    def __init__(self) -> None:
        self.calls: list[SecretRef] = []
        self.responses: dict[str, Optional[str]] = {}

    def resolve(self, ref: SecretRef) -> Optional[str]:
        self.calls.append(ref)
        return self.responses.get(ref.name)


class _ConcreteUnderstanding(UnderstandingAdapter):
    """Minimum concrete subclass for exercising AdapterBase.__init__."""

    def invoke(self, invocation: AdapterInvocation) -> AdapterResult:
        return AdapterResult()


# ---------------------------------------------------------------------------
# SecretRef
# ---------------------------------------------------------------------------


def test_secret_ref_minimum():
    ref = SecretRef(name="translate_api_key")
    assert ref.name == "translate_api_key"
    assert ref.purpose is None


def test_secret_ref_with_purpose():
    ref = SecretRef(name="k", purpose="understanding translate api key")
    assert ref.purpose == "understanding translate api key"


def test_secret_ref_name_must_be_non_empty_string():
    with pytest.raises(ValueError):
        SecretRef(name="")
    with pytest.raises(ValueError):
        SecretRef(name=None)  # type: ignore[arg-type]


def test_secret_ref_purpose_must_be_string_when_set():
    with pytest.raises(TypeError):
        SecretRef(name="k", purpose=123)  # type: ignore[arg-type]


def test_secret_ref_is_frozen():
    ref = SecretRef(name="k")
    with pytest.raises(dataclasses.FrozenInstanceError):
        ref.name = "other"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# SecretResolver
# ---------------------------------------------------------------------------


def test_secret_resolver_is_abstract():
    with pytest.raises(TypeError):
        SecretResolver()  # type: ignore[abstract]


def test_secret_resolver_subclass_must_implement_resolve():
    class _Incomplete(SecretResolver):
        pass

    with pytest.raises(TypeError):
        _Incomplete()  # type: ignore[abstract]


def test_secret_resolver_concrete_implementation_works():
    resolver = _StubResolver()
    resolver.responses["k"] = "val"
    assert resolver.resolve(SecretRef(name="k")) == "val"
    assert resolver.resolve(SecretRef(name="missing")) is None


# ---------------------------------------------------------------------------
# AdapterCredentials
# ---------------------------------------------------------------------------


def test_adapter_credentials_holds_resolver():
    resolver = _StubResolver()
    creds = AdapterCredentials(resolver=resolver)
    assert creds.resolver is resolver


def test_adapter_credentials_rejects_non_resolver():
    with pytest.raises(TypeError):
        AdapterCredentials(resolver="not-a-resolver")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        AdapterCredentials(resolver=object())  # type: ignore[arg-type]


def test_adapter_credentials_is_frozen():
    creds = AdapterCredentials(resolver=_StubResolver())
    with pytest.raises(dataclasses.FrozenInstanceError):
        creds.resolver = _StubResolver()  # type: ignore[misc]


def test_adapter_credentials_field_set_is_stable():
    """Freezes the credential envelope shape — guards against silent drift."""
    field_names = {f.name for f in dataclasses.fields(AdapterCredentials)}
    assert field_names == {"resolver"}


# ---------------------------------------------------------------------------
# AdapterBase construction-time injection
# ---------------------------------------------------------------------------


def test_adapter_base_accepts_credentials_kwarg():
    creds = AdapterCredentials(resolver=_StubResolver())
    adapter = _ConcreteUnderstanding(credentials=creds)
    assert adapter.credentials is creds


def test_adapter_base_credentials_default_to_none():
    adapter = _ConcreteUnderstanding()
    assert adapter.credentials is None


def test_adapter_base_rejects_non_credentials_object():
    with pytest.raises(TypeError):
        _ConcreteUnderstanding(credentials="bogus")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        _ConcreteUnderstanding(credentials=_StubResolver())  # type: ignore[arg-type]


def test_adapter_base_construction_does_not_resolve_secrets():
    """Construction must be I/O-free; the base never calls resolve()."""
    resolver = _StubResolver()
    creds = AdapterCredentials(resolver=resolver)
    _ConcreteUnderstanding(credentials=creds)
    assert resolver.calls == []


def test_adapter_base_credentials_property_is_read_only():
    creds = AdapterCredentials(resolver=_StubResolver())
    adapter = _ConcreteUnderstanding(credentials=creds)
    with pytest.raises(AttributeError):
        adapter.credentials = None  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Boundary discipline
# ---------------------------------------------------------------------------


def test_b1_does_not_widen_base_module_import_surface():
    """B1 must not introduce provider / business / vendor imports into base."""
    src = inspect.getsource(base_module)
    forbidden_substrings = [
        "swiftcraft",
        "jellyfish",
        "providers.",
        "workers.adapters",
        "hot_follow",
        "tasks",
        "openai",
        "gemini",
        "anthropic",
        "os.getenv",  # B1 must not read env directly — that is resolver-side
    ]
    lowered = src.lower()
    for needle in forbidden_substrings:
        assert needle not in lowered, (
            f"B1 must not reference '{needle}' in adapter base module"
        )


def test_credential_surface_carries_no_truth_or_vendor_fields():
    """Field set is the contract — no task/packet/state/UI/vendor fields."""
    forbidden = {
        "task_id",
        "packet_id",
        "line_id",
        "state",
        "primary_truth",
        "user_message",
        "presenter_text",
        "vendor_id",
        "model_id",
        "engine_id",
        "api_key",
        "secret",
        "token",
        "env_name",
    }
    for cls in (SecretRef, AdapterCredentials):
        names = {f.name for f in dataclasses.fields(cls)}
        assert names.isdisjoint(forbidden), (
            f"{cls.__name__} leaked forbidden fields: {names & forbidden}"
        )


def test_secret_resolver_lives_only_as_abstract_in_base():
    """The base ships only the abstract resolver surface, never an impl."""
    # SecretResolver is abstract — confirmed by abstractmethod metadata.
    assert getattr(SecretResolver, "__abstractmethods__", frozenset()) == {
        "resolve",
    }
    # No concrete subclass of SecretResolver exists inside base_module.
    for name, value in vars(base_module).items():
        if (
            isinstance(value, type)
            and issubclass(value, SecretResolver)
            and value is not SecretResolver
        ):
            pytest.fail(
                f"base module ships concrete SecretResolver subclass '{name}'"
            )


def test_adapter_credentials_does_not_carry_resolved_secret_value():
    """Resolved secret VALUES must never live on AdapterCredentials itself."""
    fields = {f.name for f in dataclasses.fields(AdapterCredentials)}
    # only the resolver handle — never a cached/resolved value
    assert fields == {"resolver"}
