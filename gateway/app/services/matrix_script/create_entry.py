"""Matrix Script formal create-entry payload builder.

This module owns the Matrix-only task creation seed. It validates the closed
entry field set from the Matrix Script task-entry contract and projects it
onto the existing task repository shape without creating packet truth.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from fastapi import HTTPException

from gateway.app.task_repo_utils import normalize_task_payload


MATRIX_SCRIPT_LINE_ID = "matrix_script"
MATRIX_SCRIPT_CREATE_ROUTE = "/tasks/matrix-script/new"
MATRIX_SCRIPT_TEMP_CREATE_ROUTE = "/tasks/connect/matrix_script/new"

MATRIX_SCRIPT_REQUIRED_FIELDS = (
    "topic",
    "source_script_ref",
    "source_language",
    "target_language",
    "target_platform",
    "variation_target_count",
)

MATRIX_SCRIPT_OPTIONAL_FIELDS = (
    "audience_hint",
    "tone_hint",
    "length_hint",
    "product_ref",
    "operator_notes",
)

ALLOWED_TARGET_LANGUAGES = ("mm", "vi")

# Closed scheme set for `source_script_ref` per
# `docs/contracts/matrix_script/task_entry_contract_v1.md` §"Source script ref
# shape (addendum)". The entry surface accepts an opaque reference only —
# never script body text. Two accepted shapes:
#
#   1. URI with one of the closed schemes listed below.
#   2. Bare token id of bounded length, no whitespace, no embedded scheme.
#
# Rejection branches feed the existing entry-validation error type (HTTP 400)
# so the operator brief mirrors the rest of the closed-required-set checks.
SOURCE_SCRIPT_REF_MAX_LENGTH = 512
SOURCE_SCRIPT_REF_ACCEPTED_SCHEMES = (
    "content",
    "task",
    "asset",
    "ref",
    "s3",
    "gs",
    "https",
    "http",
)
_SOURCE_SCRIPT_REF_URI_PATTERN = re.compile(
    r"^(?:" + "|".join(SOURCE_SCRIPT_REF_ACCEPTED_SCHEMES) + r")://\S+$"
)
_SOURCE_SCRIPT_REF_TOKEN_PATTERN = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._\-:/]{3,}$"
)


@dataclass(frozen=True)
class MatrixScriptCreateEntry:
    topic: str
    source_script_ref: str
    source_language: str
    target_language: str
    target_platform: str
    variation_target_count: int
    audience_hint: str = ""
    tone_hint: str = ""
    length_hint: str = ""
    product_ref: str = ""
    operator_notes: str = ""


def _clean(value: str | None) -> str:
    return str(value or "").strip()


def _require(value: str | None, field: str) -> str:
    cleaned = _clean(value)
    if not cleaned:
        raise HTTPException(status_code=400, detail=f"{field} is required")
    return cleaned


def _validate_source_script_ref_shape(value: str) -> str:
    """Enforce the opaque-ref shape on `source_script_ref`.

    Rejects pasted script body text and any value that is not one of the
    closed accepted shapes (URI scheme or bare token id). See the
    `task_entry_contract_v1` source-script-ref addendum for the full
    declared shape.
    """

    if "\n" in value or "\r" in value:
        raise HTTPException(
            status_code=400,
            detail=(
                "source_script_ref must be a single-line opaque reference; "
                "do not paste script body text"
            ),
        )
    if any(ch.isspace() for ch in value):
        raise HTTPException(
            status_code=400,
            detail=(
                "source_script_ref must not contain whitespace; expected an "
                "opaque reference (e.g. content://matrix-script/source/001)"
            ),
        )
    if len(value) > SOURCE_SCRIPT_REF_MAX_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=(
                f"source_script_ref exceeds {SOURCE_SCRIPT_REF_MAX_LENGTH} "
                "characters; expected an opaque reference, not body text"
            ),
        )
    scheme_hint = ", ".join(
        f"{scheme}://" for scheme in SOURCE_SCRIPT_REF_ACCEPTED_SCHEMES
    )
    if "://" in value:
        if not _SOURCE_SCRIPT_REF_URI_PATTERN.match(value):
            raise HTTPException(
                status_code=400,
                detail=(
                    "source_script_ref scheme is not recognised; accepted "
                    f"schemes are [{scheme_hint}]"
                ),
            )
    elif not _SOURCE_SCRIPT_REF_TOKEN_PATTERN.match(value):
        raise HTTPException(
            status_code=400,
            detail=(
                "source_script_ref must be a recognised opaque reference: a "
                f"URI with one of [{scheme_hint}] or a bare token id"
            ),
        )
    return value


def _variation_count(value: str | int | None) -> int:
    raw = _clean(str(value or ""))
    try:
        parsed = int(raw)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="variation_target_count must be an integer") from exc
    if parsed < 1 or parsed > 12:
        raise HTTPException(
            status_code=400,
            detail="variation_target_count must be between 1 and 12",
        )
    return parsed


def build_matrix_script_entry(
    *,
    topic: str | None,
    source_script_ref: str | None,
    source_language: str | None,
    target_language: str | None,
    target_platform: str | None,
    variation_target_count: str | int | None,
    audience_hint: str | None = None,
    tone_hint: str | None = None,
    length_hint: str | None = None,
    product_ref: str | None = None,
    operator_notes: str | None = None,
) -> MatrixScriptCreateEntry:
    target = _require(target_language, "target_language").lower()
    if target not in ALLOWED_TARGET_LANGUAGES:
        raise HTTPException(status_code=400, detail="target_language is not supported")
    validated_source_script_ref = _validate_source_script_ref_shape(
        _require(source_script_ref, "source_script_ref")
    )
    return MatrixScriptCreateEntry(
        topic=_require(topic, "topic"),
        source_script_ref=validated_source_script_ref,
        source_language=_require(source_language, "source_language").lower(),
        target_language=target,
        target_platform=_require(target_platform, "target_platform"),
        variation_target_count=_variation_count(variation_target_count),
        audience_hint=_clean(audience_hint),
        tone_hint=_clean(tone_hint),
        length_hint=_clean(length_hint),
        product_ref=_clean(product_ref),
        operator_notes=_clean(operator_notes),
    )


def build_matrix_script_task_payload(entry: MatrixScriptCreateEntry) -> dict[str, Any]:
    task_id = uuid4().hex[:12]
    language_scope = {
        "source_language": entry.source_language,
        "target_language": [entry.target_language],
    }
    notes_parts = [
        f"topic={entry.topic}",
        f"target_platform={entry.target_platform}",
        f"variation_target_count={entry.variation_target_count}",
    ]
    optional_notes = {
        "audience_hint": entry.audience_hint,
        "tone_hint": entry.tone_hint,
        "length_hint": entry.length_hint,
        "product_ref": entry.product_ref,
        "operator_notes": entry.operator_notes,
    }
    for key, value in optional_notes.items():
        if value:
            notes_parts.append(f"{key}={value}")

    payload = {
        "task_id": task_id,
        "id": task_id,
        "kind": MATRIX_SCRIPT_LINE_ID,
        "category_key": MATRIX_SCRIPT_LINE_ID,
        "category": MATRIX_SCRIPT_LINE_ID,
        "platform": MATRIX_SCRIPT_LINE_ID,
        "title": entry.topic,
        "source_url": entry.source_script_ref,
        "content_lang": entry.target_language,
        "ui_lang": "zh",
        "status": "pending",
        "last_step": None,
        "error_message": None,
        "config": {
            "line_id": MATRIX_SCRIPT_LINE_ID,
            "entry_contract": "matrix_script_task_entry_v1",
            "entry": {
                "topic": entry.topic,
                "source_script_ref": entry.source_script_ref,
                "language_scope": language_scope,
                "target_platform": entry.target_platform,
                "variation_target_count": entry.variation_target_count,
                **optional_notes,
            },
            "next_surfaces": {
                "workbench": f"/tasks/{task_id}",
                "delivery": f"/tasks/{task_id}/publish",
            },
        },
        "packet": {
            "line_id": MATRIX_SCRIPT_LINE_ID,
            "packet_version": "v1",
            "metadata": {
                "notes": "; ".join(notes_parts),
            },
            "line_specific_refs": [
                {
                    "ref_id": "matrix_script_variation_matrix",
                    "path": "docs/contracts/matrix_script/variation_matrix_contract_v1.md",
                    "version": "v1",
                    "binds_to": ["factory_input_contract_v1"],
                },
                {
                    "ref_id": "matrix_script_slot_pack",
                    "path": "docs/contracts/matrix_script/slot_pack_contract_v1.md",
                    "version": "v1",
                    "binds_to": ["factory_language_plan_contract_v1"],
                },
            ],
        },
        "line_specific_refs": [
            {
                "ref_id": "matrix_script_variation_matrix",
                "path": "docs/contracts/matrix_script/variation_matrix_contract_v1.md",
                "version": "v1",
                "binds_to": ["factory_input_contract_v1"],
            },
            {
                "ref_id": "matrix_script_slot_pack",
                "path": "docs/contracts/matrix_script/slot_pack_contract_v1.md",
                "version": "v1",
                "binds_to": ["factory_language_plan_contract_v1"],
            },
        ],
    }
    return normalize_task_payload(payload, is_new=True)


__all__ = [
    "ALLOWED_TARGET_LANGUAGES",
    "MATRIX_SCRIPT_CREATE_ROUTE",
    "MATRIX_SCRIPT_LINE_ID",
    "MATRIX_SCRIPT_OPTIONAL_FIELDS",
    "MATRIX_SCRIPT_REQUIRED_FIELDS",
    "MATRIX_SCRIPT_TEMP_CREATE_ROUTE",
    "MatrixScriptCreateEntry",
    "SOURCE_SCRIPT_REF_ACCEPTED_SCHEMES",
    "SOURCE_SCRIPT_REF_MAX_LENGTH",
    "build_matrix_script_entry",
    "build_matrix_script_task_payload",
]
