"""Tests for `mint_source_script_ref_with_body` (2026-05-28 redesign wave).

Authority: 2026-05-28 Matrix Script Operator UI Redesign mission §1 +
`docs/contracts/matrix_script/task_entry_contract_v1.md`
§"Operator-facing minting flow (Option F2 — addendum, 2026-05-04)"
(opaque-handle product-meaning preserved; the body store is separate
from packet truth).

These tests are import-light: they exercise the minting+body-ingest
service directly and never instantiate the FastAPI app.
"""
from __future__ import annotations

from typing import Mapping

import pytest

from gateway.app.services.matrix_script.create_entry import (
    _validate_source_script_ref_shape,
)
from gateway.app.services.matrix_script.source_script_body_store import (
    BODY_MAX_BYTES,
    SOURCE_KIND_PASTE,
    SOURCE_KIND_UPLOAD,
    BodyStoreError,
    _reset_store_for_tests,
    has_body,
    peek_body,
)
from gateway.app.services.matrix_script.source_script_ref_minting import (
    INGESTING_POLICY,
    MATRIX_SCRIPT_INGEST_ROUTE,
    MATRIX_SCRIPT_PEEK_ROUTE,
    MINT_TOKEN_PREFIX,
    mint_source_script_ref_with_body,
)


@pytest.fixture(autouse=True)
def _isolate_store() -> None:
    _reset_store_for_tests()
    yield
    _reset_store_for_tests()


# ---------------------------------------------------------------------------
# Route name pins
# ---------------------------------------------------------------------------


def test_ingest_route_name_is_pinned() -> None:
    assert MATRIX_SCRIPT_INGEST_ROUTE == "/tasks/matrix-script/source-script-refs/ingest"


def test_peek_route_name_is_pinned() -> None:
    assert MATRIX_SCRIPT_PEEK_ROUTE == "/tasks/matrix-script/source-script-refs/{token}/peek"


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_mint_with_body_returns_handle_and_body_metadata() -> None:
    envelope = mint_source_script_ref_with_body(
        body_text="hook\nbody\ncta", source_kind=SOURCE_KIND_PASTE
    )
    assert isinstance(envelope, Mapping)
    assert envelope["source_script_ref"].startswith("content://matrix-script/source/")
    token = envelope["token"]
    assert token.startswith(f"{MINT_TOKEN_PREFIX}-")
    assert envelope["has_body"] is True
    assert envelope["body_source_kind"] == SOURCE_KIND_PASTE
    assert envelope["body_char_count"] == len("hook\nbody\ncta")
    assert envelope["body_byte_size"] > 0
    assert envelope["policy"] == INGESTING_POLICY


def test_mint_with_body_handle_passes_existing_shape_guard() -> None:
    """Ingested handle MUST pass the same validator as bare-mint handles."""

    envelope = mint_source_script_ref_with_body(
        body_text="x", source_kind=SOURCE_KIND_PASTE
    )
    handle = envelope["source_script_ref"]
    accepted = _validate_source_script_ref_shape(handle)
    assert accepted == handle


def test_mint_with_body_stores_body_in_store_under_token() -> None:
    envelope = mint_source_script_ref_with_body(
        body_text="real script text", source_kind=SOURCE_KIND_UPLOAD,
        requested_by="jackie",
    )
    token = envelope["token"]
    assert has_body(token)
    peek = peek_body(token)
    assert peek is not None
    assert peek["body_text"] == "real script text"
    assert peek["source_kind"] == SOURCE_KIND_UPLOAD
    assert peek["requested_by"] == "jackie"


def test_mint_with_body_upload_kind_distinguished_from_paste_kind() -> None:
    envelope_paste = mint_source_script_ref_with_body(
        body_text="from paste", source_kind=SOURCE_KIND_PASTE
    )
    envelope_upload = mint_source_script_ref_with_body(
        body_text="from upload", source_kind=SOURCE_KIND_UPLOAD
    )
    assert envelope_paste["body_source_kind"] == SOURCE_KIND_PASTE
    assert envelope_upload["body_source_kind"] == SOURCE_KIND_UPLOAD


# ---------------------------------------------------------------------------
# Validation failures
# ---------------------------------------------------------------------------


def test_unknown_source_kind_raises_body_store_error() -> None:
    with pytest.raises(BodyStoreError):
        mint_source_script_ref_with_body(
            body_text="hi", source_kind="external_provider"
        )


def test_empty_body_raises_body_store_error() -> None:
    with pytest.raises(BodyStoreError):
        mint_source_script_ref_with_body(
            body_text="", source_kind=SOURCE_KIND_PASTE
        )


def test_oversize_body_raises_body_store_error() -> None:
    big = "a" * (BODY_MAX_BYTES + 1)
    with pytest.raises(BodyStoreError):
        mint_source_script_ref_with_body(
            body_text=big, source_kind=SOURCE_KIND_PASTE
        )


# ---------------------------------------------------------------------------
# Honesty audit — handles are opaque, body never goes anywhere external
# ---------------------------------------------------------------------------


def test_envelope_carries_no_vendor_or_model_or_provider_or_engine_keys() -> None:
    envelope = mint_source_script_ref_with_body(
        body_text="hi", source_kind=SOURCE_KIND_PASTE, requested_by="op"
    )
    forbidden = {"vendor", "model", "provider", "engine", "vendor_id",
                  "model_id", "provider_id", "engine_id"}
    assert not (set(envelope.keys()) & forbidden)


def test_handle_is_opaque_content_scheme_only_no_url_or_bucket_widening() -> None:
    envelope = mint_source_script_ref_with_body(
        body_text="x", source_kind=SOURCE_KIND_PASTE
    )
    handle = envelope["source_script_ref"]
    # The minted handle MUST be in the closed content:// scheme set —
    # §8.F tightening preserved.
    assert handle.startswith("content://matrix-script/source/")
    assert not handle.startswith("https://")
    assert not handle.startswith("http://")
    assert not handle.startswith("s3://")
    assert not handle.startswith("gs://")


def test_two_ingests_produce_distinct_tokens_and_handles() -> None:
    a = mint_source_script_ref_with_body(body_text="one", source_kind=SOURCE_KIND_PASTE)
    b = mint_source_script_ref_with_body(body_text="two", source_kind=SOURCE_KIND_PASTE)
    assert a["token"] != b["token"]
    assert a["source_script_ref"] != b["source_script_ref"]
    assert has_body(a["token"])
    assert has_body(b["token"])


def test_pre_existing_op_token_convention_still_passes_validator() -> None:
    """Backward compatibility — §8.F operator-discipline handles still accepted."""

    legacy = "content://matrix-script/source/op-token-legacy-001"
    accepted = _validate_source_script_ref_shape(legacy)
    assert accepted == legacy
    # The legacy handle does not get auto-stored; the body store only
    # backs ingest-flow handles. has_body returns False — surfaces fall
    # back to STATUS_UNRESOLVED for these handles.
    assert not has_body("op-token-legacy-001")
