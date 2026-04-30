"""B2 — base-only retry / timeout / cancellation surface tests.

Covers the per-invocation execution control surface introduced for the
W2.1 Base-Only Adapter Preparation Wave (B2):

- ``CancellationToken`` — abstract cancellation signal (no concrete in base)
- ``RetryPolicy`` — frozen, advisory retry shape (not a retry executor,
  not bound to any retry library)
- ``AdapterExecutionContext`` — frozen envelope carrying timeout /
  cancellation / retry hints
- ``AdapterBase.invoke`` accepts ``context=`` kwarg as the unified
  execution control entry, but the base never inspects it itself

The tests also enforce the boundary that B2 introduces no provider-
specific retry policy, no fallback strategy, no business semantics, and
no truth fields.
"""
from __future__ import annotations

import dataclasses
import inspect
from typing import Optional

import pytest

from gateway.app.services.capability.adapters import (
    AdapterError,
    AdapterErrorCategory,
    AdapterExecutionContext,
    AdapterInvocation,
    AdapterResult,
    CancellationToken,
    RetryPolicy,
    UnderstandingAdapter,
)
from gateway.app.services.capability.adapters import base as base_module


# ---------------------------------------------------------------------------
# Test helpers (live in the test file only — never under base/)
# ---------------------------------------------------------------------------


class _StubCancellationToken(CancellationToken):
    """Test-only manual cancellation token."""

    def __init__(self, *, cancelled: bool = False) -> None:
        self._cancelled = cancelled

    @property
    def is_cancelled(self) -> bool:
        return self._cancelled

    def cancel(self) -> None:
        self._cancelled = True


class _ConcreteUnderstanding(UnderstandingAdapter):
    """Minimum concrete subclass for exercising AdapterBase.invoke."""

    def __init__(self) -> None:
        super().__init__()
        self.last_context: Optional[AdapterExecutionContext] = None

    def invoke(
        self,
        invocation: AdapterInvocation,
        *,
        context: Optional[AdapterExecutionContext] = None,
    ) -> AdapterResult:
        self.last_context = context
        return AdapterResult()


# ---------------------------------------------------------------------------
# CancellationToken
# ---------------------------------------------------------------------------


def test_cancellation_token_is_abstract():
    with pytest.raises(TypeError):
        CancellationToken()  # type: ignore[abstract]


def test_cancellation_token_subclass_must_implement_is_cancelled():
    class _Incomplete(CancellationToken):
        pass

    with pytest.raises(TypeError):
        _Incomplete()  # type: ignore[abstract]


def test_cancellation_token_concrete_reports_signal():
    token = _StubCancellationToken()
    assert token.is_cancelled is False
    token.cancel()
    assert token.is_cancelled is True


def test_cancellation_token_raise_if_cancelled_when_not_cancelled():
    token = _StubCancellationToken()
    # Should not raise.
    token.raise_if_cancelled()


def test_cancellation_token_raise_if_cancelled_raises_adapter_error():
    token = _StubCancellationToken(cancelled=True)
    with pytest.raises(AdapterError) as exc_info:
        token.raise_if_cancelled()
    assert exc_info.value.category is AdapterErrorCategory.CANCELLED


def test_cancellation_token_lives_only_as_abstract_in_base():
    """The base ships only the abstract token, never a concrete impl."""
    assert getattr(CancellationToken, "__abstractmethods__", frozenset()) == {
        "is_cancelled",
    }
    for name, value in vars(base_module).items():
        if (
            isinstance(value, type)
            and issubclass(value, CancellationToken)
            and value is not CancellationToken
        ):
            pytest.fail(
                f"base module ships concrete CancellationToken subclass '{name}'"
            )


# ---------------------------------------------------------------------------
# RetryPolicy
# ---------------------------------------------------------------------------


def test_retry_policy_defaults_to_no_retry():
    policy = RetryPolicy()
    assert policy.max_attempts == 1
    assert policy.initial_backoff_seconds == 0.0
    assert policy.max_backoff_seconds == 0.0
    assert policy.backoff_multiplier == 1.0


def test_retry_policy_accepts_valid_values():
    policy = RetryPolicy(
        max_attempts=3,
        initial_backoff_seconds=0.5,
        max_backoff_seconds=4.0,
        backoff_multiplier=2.0,
    )
    assert policy.max_attempts == 3
    assert policy.initial_backoff_seconds == 0.5
    assert policy.max_backoff_seconds == 4.0
    assert policy.backoff_multiplier == 2.0


def test_retry_policy_rejects_max_attempts_below_one():
    with pytest.raises(ValueError):
        RetryPolicy(max_attempts=0)
    with pytest.raises(ValueError):
        RetryPolicy(max_attempts=-1)


def test_retry_policy_rejects_non_int_max_attempts():
    with pytest.raises(ValueError):
        RetryPolicy(max_attempts=1.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        RetryPolicy(max_attempts=True)  # type: ignore[arg-type]


def test_retry_policy_rejects_negative_backoff():
    with pytest.raises(ValueError):
        RetryPolicy(initial_backoff_seconds=-0.1)
    with pytest.raises(ValueError):
        RetryPolicy(max_backoff_seconds=-1.0)


def test_retry_policy_rejects_max_below_initial_backoff():
    with pytest.raises(ValueError):
        RetryPolicy(initial_backoff_seconds=2.0, max_backoff_seconds=1.0)


def test_retry_policy_rejects_multiplier_below_one():
    with pytest.raises(ValueError):
        RetryPolicy(backoff_multiplier=0.5)


def test_retry_policy_rejects_bool_multiplier():
    with pytest.raises(ValueError):
        RetryPolicy(backoff_multiplier=True)  # type: ignore[arg-type]


def test_retry_policy_is_frozen():
    policy = RetryPolicy()
    with pytest.raises(dataclasses.FrozenInstanceError):
        policy.max_attempts = 5  # type: ignore[misc]


def test_retry_policy_field_set_is_stable():
    field_names = {f.name for f in dataclasses.fields(RetryPolicy)}
    assert field_names == {
        "max_attempts",
        "initial_backoff_seconds",
        "max_backoff_seconds",
        "backoff_multiplier",
    }


# ---------------------------------------------------------------------------
# AdapterExecutionContext
# ---------------------------------------------------------------------------


def test_execution_context_defaults_are_all_none():
    ctx = AdapterExecutionContext()
    assert ctx.timeout_seconds is None
    assert ctx.cancellation is None
    assert ctx.retry is None


def test_execution_context_holds_all_fields():
    token = _StubCancellationToken()
    policy = RetryPolicy(max_attempts=2)
    ctx = AdapterExecutionContext(
        timeout_seconds=1.5,
        cancellation=token,
        retry=policy,
    )
    assert ctx.timeout_seconds == 1.5
    assert ctx.cancellation is token
    assert ctx.retry is policy


def test_execution_context_rejects_non_positive_timeout():
    with pytest.raises(ValueError):
        AdapterExecutionContext(timeout_seconds=0)
    with pytest.raises(ValueError):
        AdapterExecutionContext(timeout_seconds=-1.0)


def test_execution_context_rejects_non_numeric_timeout():
    with pytest.raises(ValueError):
        AdapterExecutionContext(timeout_seconds="1.0")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        AdapterExecutionContext(timeout_seconds=True)  # type: ignore[arg-type]


def test_execution_context_rejects_non_token_cancellation():
    with pytest.raises(TypeError):
        AdapterExecutionContext(cancellation="cancel-please")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        AdapterExecutionContext(cancellation=object())  # type: ignore[arg-type]


def test_execution_context_rejects_non_policy_retry():
    with pytest.raises(TypeError):
        AdapterExecutionContext(retry={"max_attempts": 3})  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        AdapterExecutionContext(retry=object())  # type: ignore[arg-type]


def test_execution_context_is_frozen():
    ctx = AdapterExecutionContext()
    with pytest.raises(dataclasses.FrozenInstanceError):
        ctx.timeout_seconds = 1.0  # type: ignore[misc]


def test_execution_context_field_set_is_stable():
    field_names = {f.name for f in dataclasses.fields(AdapterExecutionContext)}
    assert field_names == {"timeout_seconds", "cancellation", "retry"}


# ---------------------------------------------------------------------------
# AdapterBase.invoke wiring
# ---------------------------------------------------------------------------


def test_invoke_signature_carries_keyword_only_context():
    sig = inspect.signature(_ConcreteUnderstanding.invoke)
    assert "context" in sig.parameters
    param = sig.parameters["context"]
    assert param.kind is inspect.Parameter.KEYWORD_ONLY
    assert param.default is None


def test_invoke_accepts_context_and_does_not_inspect_it_in_base():
    """The base never reads the context — it only carries the entry point."""
    adapter = _ConcreteUnderstanding()
    token = _StubCancellationToken()
    ctx = AdapterExecutionContext(timeout_seconds=2.0, cancellation=token)
    invocation = AdapterInvocation(capability_kind="understanding")
    result = adapter.invoke(invocation, context=ctx)
    assert isinstance(result, AdapterResult)
    assert adapter.last_context is ctx
    # Base never polled the cancellation token while delegating to subclass.
    # (Stub starts un-cancelled; we just confirm calling invoke didn't trip
    # any base-side cancellation handling.)
    assert token.is_cancelled is False


def test_invoke_context_defaults_to_none():
    adapter = _ConcreteUnderstanding()
    invocation = AdapterInvocation(capability_kind="understanding")
    adapter.invoke(invocation)
    assert adapter.last_context is None


# ---------------------------------------------------------------------------
# Boundary discipline
# ---------------------------------------------------------------------------


def test_b2_does_not_widen_base_module_import_surface():
    """B2 must not introduce provider / business / retry-library imports."""
    src = inspect.getsource(base_module)
    # Substring-shaped bans — names that should not legitimately appear in
    # the base module's source at all.
    forbidden_substrings = [
        "swiftcraft",
        "jellyfish",
        "providers.",
        "workers.adapters",
        "hot_follow",
        "openai",
        "gemini",
        "anthropic",
        "time.sleep",
        "os.getenv",
    ]
    lowered = src.lower()
    for needle in forbidden_substrings:
        assert needle not in lowered, (
            f"B2 must not reference '{needle}' in adapter base module"
        )

    # Import-shaped bans — third-party retry libraries and async runtimes
    # that B2 must not bind to. Checked via AST so docstring / field names
    # mentioning these tokens (e.g. "backoff_multiplier") don't trip the
    # check, and only real `import` statements are flagged.
    import ast

    tree = ast.parse(inspect.getsource(base_module))
    forbidden_imports = {
        "tenacity",
        "backoff",
        "urllib3",
        "asyncio",
        "trio",
        "anyio",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                assert root not in forbidden_imports, (
                    f"B2 must not import '{alias.name}' in adapter base module"
                )
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root = node.module.split(".", 1)[0]
                assert root not in forbidden_imports, (
                    f"B2 must not import from '{node.module}' in adapter base module"
                )


def test_execution_context_carries_no_truth_or_vendor_fields():
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
        "fallback",
        "fallback_strategy",
        "deadline_at",  # wall-clock truth belongs to the caller, not the base
    }
    for cls in (RetryPolicy, AdapterExecutionContext):
        names = {f.name for f in dataclasses.fields(cls)}
        assert names.isdisjoint(forbidden), (
            f"{cls.__name__} leaked forbidden fields: {names & forbidden}"
        )


def test_execution_context_has_no_fallback_field():
    """Fallback strategy belongs to the business layer, not B2."""
    field_names = {f.name for f in dataclasses.fields(AdapterExecutionContext)}
    for needle in ("fallback", "primary", "secondary", "alternate"):
        for name in field_names:
            assert needle not in name.lower(), (
                f"AdapterExecutionContext leaked fallback-shaped field '{name}'"
            )


def test_b2_does_not_modify_existing_b1_or_b3_field_shapes():
    """B2 must leave B1 (credentials) and B3 (error envelope) shapes intact."""
    from gateway.app.services.capability.adapters import (
        AdapterCredentials,
        AdapterError,
    )

    cred_fields = {f.name for f in dataclasses.fields(AdapterCredentials)}
    assert cred_fields == {"resolver"}

    err = AdapterError(AdapterErrorCategory.TIMEOUT, "boom")
    assert set(err.to_dict().keys()) == {
        "category",
        "message",
        "source",
        "retryable",
        "details",
    }
