"""Tests for the in-process source-script body store (2026-05-28 redesign wave).

Authority: 2026-05-28 Matrix Script Operator UI Redesign mission §1
(paste / upload / select primary input affordances backed by a real
in-process body store; mirrors the InMemoryClosureStore pattern).

Discipline checks:
- The store accepts paste / upload kinds and rejects unknown kinds.
- Empty / whitespace-only / oversize bodies are rejected.
- get / peek / has return the stored record.
- The store is volatile (clear() resets state for tests).
- Two writes to the same token overwrite (latest wins).
- A record's body_text round-trips verbatim.
- No vendor/model/provider/engine identifier ever flows through the store.
"""
from __future__ import annotations

import pytest

from gateway.app.services.matrix_script.source_script_body_store import (
    BODY_MAX_BYTES,
    SOURCE_KIND_PASTE,
    SOURCE_KIND_UPLOAD,
    SOURCE_KIND_VALUES,
    BodyRecord,
    BodyStoreError,
    _reset_store_for_tests,
    _store_size,
    get_body,
    has_body,
    peek_body,
    put_body,
)


@pytest.fixture(autouse=True)
def _isolate_store() -> None:
    """Reset the process-wide store before each test."""

    _reset_store_for_tests()
    yield
    _reset_store_for_tests()


# ---------------------------------------------------------------------------
# Closed source_kind enum
# ---------------------------------------------------------------------------


def test_source_kind_values_are_closed_set() -> None:
    assert SOURCE_KIND_VALUES == frozenset({SOURCE_KIND_PASTE, SOURCE_KIND_UPLOAD})
    assert SOURCE_KIND_PASTE == "operator_paste"
    assert SOURCE_KIND_UPLOAD == "operator_upload"


def test_unknown_source_kind_rejected() -> None:
    with pytest.raises(BodyStoreError):
        put_body(token="t1", body_text="hello", source_kind="vendor_paste")


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_put_body_returns_body_record_with_closed_fields() -> None:
    record = put_body(
        token="mint-abc123",
        body_text="hook line\nbody\ncta",
        source_kind=SOURCE_KIND_PASTE,
        requested_by="jackie",
    )
    assert isinstance(record, BodyRecord)
    assert record.token == "mint-abc123"
    assert record.body_text == "hook line\nbody\ncta"
    assert record.source_kind == SOURCE_KIND_PASTE
    assert record.byte_size > 0
    assert record.char_count == len("hook line\nbody\ncta")
    assert record.requested_by == "jackie"
    assert record.stored_at  # ISO timestamp present


def test_get_body_returns_record_after_put() -> None:
    put_body(
        token="mint-xyz", body_text="hello world", source_kind=SOURCE_KIND_PASTE
    )
    record = get_body("mint-xyz")
    assert record is not None
    assert record.body_text == "hello world"


def test_has_body_returns_true_after_put_false_before() -> None:
    assert not has_body("mint-zzz")
    put_body(token="mint-zzz", body_text="x", source_kind=SOURCE_KIND_UPLOAD)
    assert has_body("mint-zzz")


def test_peek_returns_sanitised_payload_with_closed_keys() -> None:
    put_body(
        token="mint-peek",
        body_text="peek body",
        source_kind=SOURCE_KIND_UPLOAD,
        requested_by="alisa",
    )
    payload = peek_body("mint-peek")
    assert payload is not None
    assert set(payload.keys()) == {
        "token",
        "body_text",
        "source_kind",
        "stored_at",
        "byte_size",
        "char_count",
        "requested_by",
    }
    assert payload["body_text"] == "peek body"
    assert payload["source_kind"] == SOURCE_KIND_UPLOAD


def test_overwrite_latest_wins() -> None:
    put_body(token="mint-ov", body_text="first", source_kind=SOURCE_KIND_PASTE)
    put_body(token="mint-ov", body_text="second", source_kind=SOURCE_KIND_PASTE)
    record = get_body("mint-ov")
    assert record is not None
    assert record.body_text == "second"
    assert _store_size() == 1


# ---------------------------------------------------------------------------
# Validation failures
# ---------------------------------------------------------------------------


def test_empty_token_rejected() -> None:
    with pytest.raises(BodyStoreError):
        put_body(token="", body_text="hello", source_kind=SOURCE_KIND_PASTE)
    with pytest.raises(BodyStoreError):
        put_body(token="   ", body_text="hello", source_kind=SOURCE_KIND_PASTE)


def test_empty_body_rejected() -> None:
    with pytest.raises(BodyStoreError):
        put_body(token="t", body_text="", source_kind=SOURCE_KIND_PASTE)
    with pytest.raises(BodyStoreError):
        put_body(token="t", body_text="   \n\t  ", source_kind=SOURCE_KIND_PASTE)


def test_oversize_body_rejected() -> None:
    big = "a" * (BODY_MAX_BYTES + 1)
    with pytest.raises(BodyStoreError):
        put_body(token="t", body_text=big, source_kind=SOURCE_KIND_PASTE)


def test_non_string_body_rejected() -> None:
    with pytest.raises(BodyStoreError):
        put_body(token="t", body_text=123, source_kind=SOURCE_KIND_PASTE)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Volatility / isolation
# ---------------------------------------------------------------------------


def test_clear_resets_store() -> None:
    put_body(token="t1", body_text="a", source_kind=SOURCE_KIND_PASTE)
    put_body(token="t2", body_text="b", source_kind=SOURCE_KIND_PASTE)
    assert _store_size() == 2
    _reset_store_for_tests()
    assert _store_size() == 0
    assert get_body("t1") is None


def test_get_unknown_token_returns_none() -> None:
    assert get_body("never-stored") is None
    assert peek_body("never-stored") is None
    assert not has_body("never-stored")


# ---------------------------------------------------------------------------
# Honesty audit — body text round-trips verbatim and no vendor leak
# ---------------------------------------------------------------------------


def test_body_text_round_trips_verbatim_including_unicode() -> None:
    sample = "你好\n这是一段脚本正文。\nCTA: 点击关注～\n🎬"
    put_body(token="mint-zh", body_text=sample, source_kind=SOURCE_KIND_PASTE)
    record = get_body("mint-zh")
    assert record is not None
    assert record.body_text == sample
    assert record.char_count == len(sample)


def test_peek_does_not_leak_vendor_or_model_or_provider_or_engine_keys() -> None:
    """The peek envelope is closed; vendor/model/provider/engine NEVER appear."""

    put_body(
        token="mint-redline",
        body_text="hello",
        source_kind=SOURCE_KIND_PASTE,
        requested_by="jackie",
    )
    payload = peek_body("mint-redline")
    assert payload is not None
    forbidden_keys = {"vendor", "model", "provider", "engine", "vendor_id",
                       "model_id", "provider_id", "engine_id"}
    assert not (set(payload.keys()) & forbidden_keys)
