"""B4 — base-only construction-vs-invocation lifecycle boundary tests.

Freezes the construction-vs-invocation lifecycle for ``AdapterBase``
introduced for the W2.1 Base-Only Adapter Preparation Wave (B4):

- *Construction time* (``__init__``) accepts and stores the injected
  ``AdapterCredentials`` envelope (B1), validates dependency shapes,
  and performs no I/O.
- *Invocation time* (``invoke``) is the only method on which I/O is
  permitted; it carries the ``AdapterInvocation`` plus an optional
  ``AdapterExecutionContext`` (B2) and may raise ``AdapterError`` (B3).
- *Module import* is side-effect-free.

The tests also enforce that B4 introduces no provider-specific
initialisation, no retry / timer / scheduler logic in construction,
and no widening of the B1 / B2 / B3 surfaces.
"""
from __future__ import annotations

import ast
import importlib
import inspect
import sys
from typing import Optional

import pytest

from gateway.app.services.capability.adapters import (
    AdapterBase,
    AdapterCredentials,
    AdapterError,
    AdapterErrorCategory,
    AdapterExecutionContext,
    AdapterInvocation,
    AdapterResult,
    AvatarAdapter,
    CancellationToken,
    DubAdapter,
    FaceSwapAdapter,
    PackAdapter,
    PostProductionAdapter,
    RetryPolicy,
    SecretRef,
    SecretResolver,
    SubtitlesAdapter,
    UnderstandingAdapter,
    VideoGenAdapter,
)
from gateway.app.services.capability.adapters import base as base_module


# ---------------------------------------------------------------------------
# Test helpers (live in the test file only — never under base/)
# ---------------------------------------------------------------------------


class _RecordingResolver(SecretResolver):
    """Resolver that records every ``resolve`` call. Constructor is I/O-free."""

    def __init__(self) -> None:
        self.calls: list[SecretRef] = []

    def resolve(self, ref: SecretRef) -> Optional[str]:
        self.calls.append(ref)
        return None


class _RecordingCancellationToken(CancellationToken):
    """Cancellation token that records every ``is_cancelled`` read."""

    def __init__(self) -> None:
        self.reads = 0

    @property
    def is_cancelled(self) -> bool:
        self.reads += 1
        return False


class _ConcreteUnderstanding(UnderstandingAdapter):
    """Minimum concrete adapter for exercising the lifecycle boundary."""

    def __init__(
        self, *, credentials: Optional[AdapterCredentials] = None
    ) -> None:
        super().__init__(credentials=credentials)
        self.invoke_calls = 0

    def invoke(
        self,
        invocation: AdapterInvocation,
        *,
        context: Optional[AdapterExecutionContext] = None,
    ) -> AdapterResult:
        self.invoke_calls += 1
        return AdapterResult()


# ---------------------------------------------------------------------------
# Construction-time allowed state
# ---------------------------------------------------------------------------


def test_construction_stores_credentials_without_resolving():
    resolver = _RecordingResolver()
    creds = AdapterCredentials(resolver=resolver)
    adapter = _ConcreteUnderstanding(credentials=creds)
    assert adapter.credentials is creds
    assert resolver.calls == [], (
        "AdapterBase.__init__ must not call resolver.resolve(...)"
    )


def test_construction_default_credentials_is_none():
    adapter = _ConcreteUnderstanding()
    assert adapter.credentials is None


def test_construction_credentials_is_keyword_only():
    sig = inspect.signature(AdapterBase.__init__)
    assert "credentials" in sig.parameters
    assert (
        sig.parameters["credentials"].kind is inspect.Parameter.KEYWORD_ONLY
    )
    # Positional construction must fail — the lifecycle entry point is
    # explicit, named, and validated.
    with pytest.raises(TypeError):
        _ConcreteUnderstanding(AdapterCredentials(resolver=_RecordingResolver()))  # type: ignore[misc]


def test_construction_parameter_set_is_stable():
    """Construction-time parameters: only ``self`` and ``credentials``."""
    params = inspect.signature(AdapterBase.__init__).parameters
    assert set(params) == {"self", "credentials"}


def test_construction_persists_only_credentials_state():
    """Base-only construction state lives on a single private slot."""
    adapter = _ConcreteUnderstanding(
        credentials=AdapterCredentials(resolver=_RecordingResolver())
    )
    base_state = {
        k for k in vars(adapter) if not k.startswith(f"_{type(adapter).__name__}__")
    }
    base_state -= {"invoke_calls"}  # subclass-only attribute
    assert base_state == {"_credentials"}, (
        f"AdapterBase added unexpected construction-time state: {base_state}"
    )


# ---------------------------------------------------------------------------
# Construction-time forbidden behaviours
# ---------------------------------------------------------------------------


def test_construction_does_not_invoke_resolver():
    """Repeated construction never triggers resolver I/O."""
    resolver = _RecordingResolver()
    creds = AdapterCredentials(resolver=resolver)
    for _ in range(5):
        _ConcreteUnderstanding(credentials=creds)
    assert resolver.calls == []


def test_construction_does_not_poll_cancellation_token():
    """Construction must not read injected runtime signals.

    Cancellation lives on the per-invocation ``AdapterExecutionContext``;
    even just constructing an adapter (and the context envelope itself)
    must not poll the token.
    """
    token = _RecordingCancellationToken()
    AdapterExecutionContext(cancellation=token)
    _ConcreteUnderstanding(
        credentials=AdapterCredentials(resolver=_RecordingResolver())
    )
    assert token.reads == 0


def test_construction_rejects_non_credentials_dependency():
    with pytest.raises(TypeError):
        _ConcreteUnderstanding(credentials="not-a-credentials")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        _ConcreteUnderstanding(credentials=_RecordingResolver())  # type: ignore[arg-type]


def test_construction_does_not_accept_invocation_time_arguments():
    """Per-invocation envelopes never appear on the construction surface."""
    creds = AdapterCredentials(resolver=_RecordingResolver())
    invocation = AdapterInvocation(capability_kind="understanding")
    ctx = AdapterExecutionContext()
    with pytest.raises(TypeError):
        _ConcreteUnderstanding(  # type: ignore[call-arg]
            credentials=creds, invocation=invocation
        )
    with pytest.raises(TypeError):
        _ConcreteUnderstanding(credentials=creds, context=ctx)  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# Invocation-time boundary
# ---------------------------------------------------------------------------


def test_invocation_is_the_only_abstract_surface():
    """First I/O point is reachable only via ``invoke``."""
    assert AdapterBase.__abstractmethods__ == frozenset({"invoke"})


def test_invoke_signature_carries_invocation_and_keyword_only_context():
    sig = inspect.signature(AdapterBase.invoke)
    params = sig.parameters
    assert list(params) == ["self", "invocation", "context"]
    assert params["invocation"].kind in (
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
        inspect.Parameter.POSITIONAL_ONLY,
    )
    assert params["context"].kind is inspect.Parameter.KEYWORD_ONLY
    assert params["context"].default is None


def test_invocation_does_not_mutate_construction_state():
    creds = AdapterCredentials(resolver=_RecordingResolver())
    adapter = _ConcreteUnderstanding(credentials=creds)
    invocation = AdapterInvocation(capability_kind="understanding")
    adapter.invoke(invocation)
    adapter.invoke(invocation, context=AdapterExecutionContext())
    assert adapter.credentials is creds, (
        "invoke() must not rebind construction-time credentials"
    )


def test_invocation_may_raise_adapter_error_envelope():
    """The frozen B3 envelope is the only error contract on invocation."""

    class _FailingAdapter(UnderstandingAdapter):
        def invoke(
            self,
            invocation: AdapterInvocation,
            *,
            context: Optional[AdapterExecutionContext] = None,
        ) -> AdapterResult:
            raise AdapterError(
                AdapterErrorCategory.UPSTREAM, "upstream failed"
            )

    with pytest.raises(AdapterError) as exc:
        _FailingAdapter().invoke(AdapterInvocation(capability_kind="understanding"))
    assert exc.value.category is AdapterErrorCategory.UPSTREAM


# ---------------------------------------------------------------------------
# Module / import-time boundary
# ---------------------------------------------------------------------------


def test_base_module_import_is_side_effect_free():
    """Re-importing the module must not perform I/O.

    A fresh import (after evicting the cached module) must succeed without
    triggering filesystem / network / env reads. We assert the absence of
    side-effect-prone import statements at the AST level so any future
    addition of e.g. ``import socket`` or ``import requests`` at module
    top-level fails this test deliberately.
    """
    module_name = base_module.__name__
    sys.modules.pop(module_name, None)
    reloaded = importlib.import_module(module_name)
    # Sanity — the reload reproduced AdapterBase with the same identity slot.
    assert hasattr(reloaded, "AdapterBase")

    tree = ast.parse(inspect.getsource(reloaded))
    forbidden_roots = {
        "socket",
        "ssl",
        "http",
        "urllib",
        "urllib3",
        "requests",
        "httpx",
        "aiohttp",
        "asyncio",
        "trio",
        "anyio",
        "subprocess",
        "threading",
        "multiprocessing",
        "sqlite3",
        "pathlib",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                assert root not in forbidden_roots, (
                    f"AdapterBase module imports I/O-capable '{alias.name}'"
                )
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root = node.module.split(".", 1)[0]
                assert root not in forbidden_roots, (
                    f"AdapterBase module imports from I/O-capable '{node.module}'"
                )


def test_base_module_has_no_module_level_io_calls():
    """No ``open()`` / ``os.getenv`` / ``socket.*`` calls at module top level.

    Class / function bodies that *define* but never *call* such APIs are
    fine; the AST check inspects only top-level expression statements.
    """
    tree = ast.parse(inspect.getsource(base_module))
    forbidden_callables = {
        "open",
        "input",
        "exec",
        "eval",
    }
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            func = node.value.func
            if isinstance(func, ast.Name) and func.id in forbidden_callables:
                pytest.fail(
                    f"module-level I/O call '{func.id}(...)' in adapter base"
                )
            if isinstance(func, ast.Attribute):
                # Disallow patterns like os.getenv(...), time.sleep(...).
                attr = func.attr
                if attr in {"getenv", "system", "sleep", "popen"}:
                    pytest.fail(
                        f"module-level I/O call '.{attr}(...)' in adapter base"
                    )


# ---------------------------------------------------------------------------
# No provider-specific initialisation
# ---------------------------------------------------------------------------


def test_base_module_has_no_provider_specific_initialisation():
    """Base must not name vendor SDKs / clients in any form."""
    src = inspect.getsource(base_module).lower()
    forbidden_substrings = [
        "swiftcraft",
        "jellyfish",
        "providers.",
        "workers.adapters",
        "hot_follow",
        "openai",
        "gemini",
        "anthropic",
        "google.cloud",
        "boto3",
        "azure.",
        "client(",  # SDK client construction marker
        "api_key",
        "access_token",
        "bearer ",
    ]
    for needle in forbidden_substrings:
        assert needle not in src, (
            f"base module references provider-specific token '{needle}'"
        )


def test_kind_subclasses_do_not_override_construction():
    """Capability-kind subclasses must not extend the construction surface.

    Provider-specific construction logic belongs to vendor adapters under
    ``workers/adapters/<vendor>/``, not to the closed-set kind subclasses
    that live in this base module.
    """
    kind_classes = (
        UnderstandingAdapter,
        SubtitlesAdapter,
        DubAdapter,
        VideoGenAdapter,
        AvatarAdapter,
        FaceSwapAdapter,
        PostProductionAdapter,
        PackAdapter,
    )
    for cls in kind_classes:
        # Each kind subclass inherits ``AdapterBase.__init__`` directly —
        # it must not define its own ``__init__``.
        assert "__init__" not in cls.__dict__, (
            f"{cls.__name__} overrides __init__; "
            "kind subclasses must inherit AdapterBase.__init__"
        )
        assert cls.__init__ is AdapterBase.__init__


# ---------------------------------------------------------------------------
# Compatibility with B1 / B2 / B3 frozen surfaces
# ---------------------------------------------------------------------------


def test_b4_does_not_widen_b1_credentials_surface():
    import dataclasses

    cred_fields = {f.name for f in dataclasses.fields(AdapterCredentials)}
    assert cred_fields == {"resolver"}
    secret_fields = {f.name for f in dataclasses.fields(SecretRef)}
    assert secret_fields == {"name", "purpose"}
    assert getattr(SecretResolver, "__abstractmethods__", frozenset()) == {
        "resolve",
    }


def test_b4_does_not_widen_b2_execution_context_surface():
    import dataclasses

    ctx_fields = {f.name for f in dataclasses.fields(AdapterExecutionContext)}
    assert ctx_fields == {"timeout_seconds", "cancellation", "retry"}
    retry_fields = {f.name for f in dataclasses.fields(RetryPolicy)}
    assert retry_fields == {
        "max_attempts",
        "initial_backoff_seconds",
        "max_backoff_seconds",
        "backoff_multiplier",
    }
    assert getattr(CancellationToken, "__abstractmethods__", frozenset()) == {
        "is_cancelled",
    }


def test_b4_does_not_widen_b3_error_envelope_surface():
    err = AdapterError(AdapterErrorCategory.INTERNAL, "boom")
    assert set(err.to_dict().keys()) == {
        "category",
        "message",
        "source",
        "retryable",
        "details",
    }
    # Closed category set unchanged by B4.
    assert {c.value for c in AdapterErrorCategory} == {
        "invalid_invocation",
        "unavailable",
        "timeout",
        "cancelled",
        "auth",
        "rate_limited",
        "upstream",
        "internal",
    }
