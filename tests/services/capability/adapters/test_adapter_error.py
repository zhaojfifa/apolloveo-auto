"""B3 — base-only AdapterError envelope tests.

Covers construction, closed category set, stable serialisation shape,
immutability of details, raise/catch behaviour, and the discipline rule
that the base error type carries no provider/business semantics.
"""
from __future__ import annotations

import inspect

import pytest

from gateway.app.services.capability.adapters import (
    AdapterError,
    AdapterErrorCategory,
)
from gateway.app.services.capability.adapters import base as base_module


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_construct_minimum_fields():
    err = AdapterError(AdapterErrorCategory.UPSTREAM, "boom")
    assert err.category is AdapterErrorCategory.UPSTREAM
    assert err.message == "boom"
    assert err.source is None
    assert err.retryable is None
    assert dict(err.details) == {}


def test_construct_full_fields():
    err = AdapterError(
        "timeout",
        "deadline exceeded",
        source="understanding",
        retryable=True,
        details={"elapsed_ms": 1234},
    )
    assert err.category is AdapterErrorCategory.TIMEOUT
    assert err.source == "understanding"
    assert err.retryable is True
    assert err.details["elapsed_ms"] == 1234


def test_category_string_accepted_via_closed_set():
    err = AdapterError("auth", "missing credential")
    assert err.category is AdapterErrorCategory.AUTH


def test_category_outside_closed_set_rejected():
    with pytest.raises(ValueError, match="closed set"):
        AdapterError("not_a_category", "nope")


def test_message_must_be_non_empty_string():
    with pytest.raises(ValueError):
        AdapterError(AdapterErrorCategory.INTERNAL, "")
    with pytest.raises(ValueError):
        AdapterError(AdapterErrorCategory.INTERNAL, None)  # type: ignore[arg-type]


def test_retryable_must_be_bool_when_set():
    with pytest.raises(TypeError):
        AdapterError(
            AdapterErrorCategory.UPSTREAM,
            "x",
            retryable="yes",  # type: ignore[arg-type]
        )


def test_source_must_be_string_when_set():
    with pytest.raises(TypeError):
        AdapterError(
            AdapterErrorCategory.UPSTREAM,
            "x",
            source=123,  # type: ignore[arg-type]
        )


# ---------------------------------------------------------------------------
# Behaviour
# ---------------------------------------------------------------------------


def test_is_raisable_and_catchable_as_exception():
    with pytest.raises(AdapterError) as info:
        raise AdapterError(AdapterErrorCategory.CANCELLED, "stop")
    assert info.value.category is AdapterErrorCategory.CANCELLED
    assert str(info.value) == "stop"
    # also catchable as plain Exception — does not invent a parallel hierarchy
    with pytest.raises(Exception):
        raise AdapterError(AdapterErrorCategory.CANCELLED, "stop")


def test_details_are_immutable_view():
    payload = {"key": "value"}
    err = AdapterError(AdapterErrorCategory.UPSTREAM, "x", details=payload)
    # mutating original must not bleed into the envelope
    payload["key"] = "mutated"
    assert err.details["key"] == "value"
    # the exposed mapping itself rejects writes
    with pytest.raises(TypeError):
        err.details["new"] = "x"  # type: ignore[index]


# ---------------------------------------------------------------------------
# Stable serialisation shape
# ---------------------------------------------------------------------------


def test_to_dict_shape_is_frozen():
    err = AdapterError(
        AdapterErrorCategory.RATE_LIMITED,
        "slow down",
        source="subtitles",
        retryable=False,
        details={"retry_after_ms": 500},
    )
    snapshot = err.to_dict()
    assert snapshot == {
        "category": "rate_limited",
        "message": "slow down",
        "source": "subtitles",
        "retryable": False,
        "details": {"retry_after_ms": 500},
    }
    # exact key set — guards against silent shape drift
    assert set(snapshot.keys()) == {
        "category",
        "message",
        "source",
        "retryable",
        "details",
    }


def test_category_values_are_closed_and_stable():
    # Freezes the closed set. Adding a category is a deliberate base change.
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


# ---------------------------------------------------------------------------
# Boundary discipline
# ---------------------------------------------------------------------------


def test_base_module_has_no_provider_or_business_imports():
    """B3 must not silently widen the base's import surface.

    The adapter base may only depend on stdlib + the packet envelope's closed
    capability-kind set. Any provider SDK / business module import here would
    indicate B3 leaked beyond base-only scope.
    """
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
    ]
    lowered = src.lower()
    for needle in forbidden_substrings:
        assert needle not in lowered, (
            f"AdapterError base must not reference '{needle}'"
        )


def test_adapter_error_carries_no_truth_or_presenter_fields():
    """Field set is the contract — no task/packet/state/UI-wording fields."""
    err = AdapterError(AdapterErrorCategory.INTERNAL, "x")
    public = {name for name in vars(err).keys() if not name.startswith("_")}
    # also include __slots__ since AdapterError uses them
    public |= set(getattr(AdapterError, "__slots__", ()))
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
    }
    assert public.isdisjoint(forbidden), (
        f"AdapterError leaked forbidden fields: {public & forbidden}"
    )
