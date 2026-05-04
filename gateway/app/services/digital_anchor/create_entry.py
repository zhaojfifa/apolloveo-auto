"""Digital Anchor formal create-entry payload builder.

Implements the closed input → output mapping per
``docs/contracts/digital_anchor/create_entry_payload_builder_contract_v1.md``
+ ``docs/contracts/digital_anchor/task_entry_contract_v1.md``. The builder
validates the closed eleven-field entry set and projects it onto the
task-repository payload + Digital Anchor packet seed.

Discipline:
- Builder seeds **only** the two `line_specific_refs[]` skeletons named
  by the contract (`digital_anchor_role_pack`,
  `digital_anchor_speaker_plan`); it does NOT author `roles[]` or
  `segments[]` (Phase B authoring is out of scope).
- Operator hints flow into `metadata.notes` as a free-form trail; they
  never become packet truth.
- No vendor / model / provider / engine / avatar-engine / TTS-provider
  / lip-sync-engine identifier may appear at any layer.
- Closed kind-sets are not widened.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping
from uuid import uuid4

from copy import deepcopy

from fastapi import HTTPException

from gateway.app.task_repo_utils import normalize_task_payload


DIGITAL_ANCHOR_LINE_ID = "digital_anchor"
DIGITAL_ANCHOR_CREATE_ROUTE = "/tasks/digital-anchor/new"

# Closed entry-field set (mirrors task_entry_contract_v1 §"Entry field set").
DIGITAL_ANCHOR_REQUIRED_FIELDS = (
    "topic",
    "source_script_ref",
    "language_scope",
    "role_profile_ref",
    "role_framing_hint",
    "output_intent",
    "speaker_segment_count_hint",
)
DIGITAL_ANCHOR_OPTIONAL_FIELDS = (
    "dub_kind_hint",
    "lip_sync_kind_hint",
    "scene_binding_hint",
    "operator_notes",
)
DIGITAL_ANCHOR_ALLOWED_FIELDS = frozenset(
    DIGITAL_ANCHOR_REQUIRED_FIELDS + DIGITAL_ANCHOR_OPTIONAL_FIELDS
)

# Closed kind-sets per the line-specific contracts. The entry surface may
# select among these values via *_hint fields; it never widens them.
ROLE_FRAMING_KIND_SET = ("head", "half_body", "full_body")
DUB_KIND_SET = ("tts_neutral", "tts_role_voice", "source_passthrough")
LIP_SYNC_KIND_SET = ("tight", "loose", "none")

# Bare opaque-ref scheme set (mirrors Matrix Script §8.F discipline; the
# Digital Anchor entry contract itself does not enumerate schemes, but
# operator-visible reference inputs MUST stay opaque per validator R3 +
# §"Forbidden at entry surface".)
SOURCE_SCRIPT_REF_MAX_LENGTH = 512
ROLE_PROFILE_REF_MAX_LENGTH = 512
_OPAQUE_REF_SCHEMES = ("content", "task", "asset", "ref", "catalog")
_OPAQUE_REF_URI_PATTERN = re.compile(
    r"^(?:" + "|".join(_OPAQUE_REF_SCHEMES) + r")://\S+$"
)
_OPAQUE_REF_TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._\-:/]{3,}$")

# Forbidden substrings in any free-form text or operator-hint field.
_FORBIDDEN_KEY_FRAGMENTS = ("vendor", "model_id", "provider", "engine_id")


@dataclass(frozen=True)
class DigitalAnchorCreateEntry:
    """Closed Digital Anchor task entry shape.

    Mirrors the closed eleven-field set; required fields are surfaced as
    individual attributes, optional fields as defaulted strings or empty
    list.
    """

    topic: str
    source_script_ref: str
    source_language: str
    target_language: tuple[str, ...]
    role_profile_ref: str
    role_framing_hint: str
    output_intent: str
    speaker_segment_count_hint: int
    dub_kind_hint: str = ""
    lip_sync_kind_hint: str = ""
    scene_binding_hint: str = ""
    operator_notes: str = ""


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _require(value: Any, field_name: str) -> str:
    cleaned = _clean(value)
    if not cleaned:
        raise HTTPException(status_code=400, detail=f"{field_name} is required")
    return cleaned


def _validate_opaque_ref(value: str, field_name: str, *, max_length: int) -> str:
    if any(ch.isspace() for ch in value):
        raise HTTPException(
            status_code=400,
            detail=(
                f"{field_name} must not contain whitespace; expected an opaque "
                "reference"
            ),
        )
    if len(value) > max_length:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} exceeds {max_length} characters",
        )
    if "://" in value:
        if not _OPAQUE_REF_URI_PATTERN.match(value):
            schemes = ", ".join(f"{s}://" for s in _OPAQUE_REF_SCHEMES)
            raise HTTPException(
                status_code=400,
                detail=(
                    f"{field_name} scheme is not recognised; accepted schemes are "
                    f"[{schemes}]"
                ),
            )
    elif not _OPAQUE_REF_TOKEN_PATTERN.match(value):
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must be an opaque reference (URI or bare token)",
        )
    return value


def _validate_no_forbidden_substrings(value: str, field_name: str) -> str:
    lowered = value.lower()
    for fragment in _FORBIDDEN_KEY_FRAGMENTS:
        if fragment in lowered:
            raise HTTPException(
                status_code=400,
                detail=f"{field_name} must not name a vendor/model/provider/engine",
            )
    return value


def _coerce_target_languages(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        items = [v.strip() for v in re.split(r"[,;\s]+", value) if v.strip()]
    elif isinstance(value, (list, tuple)):
        items = [str(v).strip() for v in value if str(v).strip()]
    else:
        raise HTTPException(
            status_code=400,
            detail="language_scope.target_language must be a list or comma-separated string",
        )
    if not items:
        raise HTTPException(
            status_code=400,
            detail="language_scope.target_language is required",
        )
    return tuple(items)


def _segment_count(value: Any) -> int:
    raw = _clean(str(value or ""))
    try:
        parsed = int(raw)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="speaker_segment_count_hint must be an integer",
        ) from exc
    if parsed < 1 or parsed > 24:
        raise HTTPException(
            status_code=400,
            detail="speaker_segment_count_hint must be between 1 and 24",
        )
    return parsed


def _validate_closed_set(
    value: str, field_name: str, allowed: Iterable[str]
) -> str:
    if value not in allowed:
        raise HTTPException(
            status_code=400,
            detail=(
                f"{field_name} is not in the closed set; expected one of "
                f"[{', '.join(allowed)}]"
            ),
        )
    return value


def build_digital_anchor_entry(
    *,
    topic: Any,
    source_script_ref: Any,
    language_scope: Any,
    role_profile_ref: Any,
    role_framing_hint: Any,
    output_intent: Any,
    speaker_segment_count_hint: Any,
    dub_kind_hint: Any = None,
    lip_sync_kind_hint: Any = None,
    scene_binding_hint: Any = None,
    operator_notes: Any = None,
    extra_fields: Iterable[str] | None = None,
) -> DigitalAnchorCreateEntry:
    """Validate and assemble a closed Digital Anchor entry.

    The ``language_scope`` argument MUST be a mapping with closed keys
    ``{source_language, target_language}`` per
    ``docs/contracts/digital_anchor/task_entry_contract_v1.md`` §"Entry
    field set" (mirrored verbatim by the create-entry payload builder
    contract). The builder rejects flat ``source_language`` /
    ``target_language`` arguments at the type boundary — those are
    sub-fields of ``language_scope``, not separate top-level inputs.

    Unknown fields supplied by the caller MUST be passed via
    ``extra_fields`` so the closed-set guard rejects them.
    """
    if extra_fields:
        unknown = sorted(set(extra_fields) - DIGITAL_ANCHOR_ALLOWED_FIELDS)
        if unknown:
            raise HTTPException(
                status_code=400,
                detail=f"unknown fields are not supported: {unknown}",
            )

    if not isinstance(language_scope, Mapping):
        raise HTTPException(
            status_code=400,
            detail=(
                "language_scope must be a mapping with closed keys "
                "{source_language, target_language}"
            ),
        )
    unknown_scope = set(language_scope) - {"source_language", "target_language"}
    if unknown_scope:
        raise HTTPException(
            status_code=400,
            detail=(
                "language_scope has unknown sub-keys: "
                f"{sorted(unknown_scope)}; expected exactly "
                "{source_language, target_language}"
            ),
        )

    topic_clean = _validate_no_forbidden_substrings(_require(topic, "topic"), "topic")
    source_script_ref_clean = _validate_opaque_ref(
        _require(source_script_ref, "source_script_ref"),
        "source_script_ref",
        max_length=SOURCE_SCRIPT_REF_MAX_LENGTH,
    )
    source_language_clean = _require(
        language_scope.get("source_language"), "language_scope.source_language"
    ).lower()
    target_languages_clean = _coerce_target_languages(
        language_scope.get("target_language")
    )
    role_profile_ref_clean = _validate_opaque_ref(
        _require(role_profile_ref, "role_profile_ref"),
        "role_profile_ref",
        max_length=ROLE_PROFILE_REF_MAX_LENGTH,
    )
    role_framing_clean = _validate_closed_set(
        _require(role_framing_hint, "role_framing_hint"),
        "role_framing_hint",
        ROLE_FRAMING_KIND_SET,
    )
    output_intent_clean = _validate_no_forbidden_substrings(
        _require(output_intent, "output_intent"), "output_intent"
    )
    segments_count = _segment_count(speaker_segment_count_hint)

    dub_clean = _clean(dub_kind_hint)
    if dub_clean:
        _validate_closed_set(dub_clean, "dub_kind_hint", DUB_KIND_SET)
    lip_clean = _clean(lip_sync_kind_hint)
    if lip_clean:
        _validate_closed_set(lip_clean, "lip_sync_kind_hint", LIP_SYNC_KIND_SET)
    scene_clean = _validate_no_forbidden_substrings(
        _clean(scene_binding_hint), "scene_binding_hint"
    )
    notes_clean = _validate_no_forbidden_substrings(
        _clean(operator_notes), "operator_notes"
    )

    return DigitalAnchorCreateEntry(
        topic=topic_clean,
        source_script_ref=source_script_ref_clean,
        source_language=source_language_clean,
        target_language=target_languages_clean,
        role_profile_ref=role_profile_ref_clean,
        role_framing_hint=role_framing_clean,
        output_intent=output_intent_clean,
        speaker_segment_count_hint=segments_count,
        dub_kind_hint=dub_clean,
        lip_sync_kind_hint=lip_clean,
        scene_binding_hint=scene_clean,
        operator_notes=notes_clean,
    )


def _metadata_notes(entry: DigitalAnchorCreateEntry) -> str:
    """Render the operator-hint trail per the entry contract Mapping note.

    All operator hints flow into ``metadata.notes`` as a free-form trail;
    no field becomes packet truth.
    """
    parts = [
        f"topic={entry.topic}",
        f"output_intent={entry.output_intent}",
        f"role_framing_hint={entry.role_framing_hint}",
        f"speaker_segment_count_hint={entry.speaker_segment_count_hint}",
    ]
    optional = {
        "dub_kind_hint": entry.dub_kind_hint,
        "lip_sync_kind_hint": entry.lip_sync_kind_hint,
        "scene_binding_hint": entry.scene_binding_hint,
        "operator_notes": entry.operator_notes,
    }
    for key, value in optional.items():
        if value:
            parts.append(f"{key}={value}")
    return "; ".join(parts)


def _entry_for_config(entry: DigitalAnchorCreateEntry) -> dict[str, Any]:
    """Project the entry verbatim onto config.entry — the closed eleven-field set."""
    return {
        "topic": entry.topic,
        "source_script_ref": entry.source_script_ref,
        "language_scope": {
            "source_language": entry.source_language,
            "target_language": list(entry.target_language),
        },
        "role_profile_ref": entry.role_profile_ref,
        "role_framing_hint": entry.role_framing_hint,
        "output_intent": entry.output_intent,
        "speaker_segment_count_hint": entry.speaker_segment_count_hint,
        "dub_kind_hint": entry.dub_kind_hint or None,
        "lip_sync_kind_hint": entry.lip_sync_kind_hint or None,
        "scene_binding_hint": entry.scene_binding_hint or None,
        "operator_notes": entry.operator_notes or None,
    }


def build_digital_anchor_task_payload(
    entry: DigitalAnchorCreateEntry,
) -> dict[str, Any]:
    """Project a validated entry onto the closed task-payload shape.

    Output shape verbatim per
    ``create_entry_payload_builder_contract_v1.md`` §"Outputs (closed)".
    Seeds only the two `line_specific_refs[]` skeletons; does NOT author
    `roles[]` or `segments[]`.
    """
    task_id = uuid4().hex[:12]
    target_languages = list(entry.target_language)
    payload: dict[str, Any] = {
        "task_id": task_id,
        "id": task_id,
        "kind": DIGITAL_ANCHOR_LINE_ID,
        "category_key": DIGITAL_ANCHOR_LINE_ID,
        "category": DIGITAL_ANCHOR_LINE_ID,
        "platform": DIGITAL_ANCHOR_LINE_ID,
        "title": entry.topic,
        "source_url": entry.source_script_ref,
        "content_lang": target_languages[0],
        "ui_lang": "zh",
        "status": "pending",
        "last_step": None,
        "error_message": None,
        "config": {
            "line_id": DIGITAL_ANCHOR_LINE_ID,
            "entry_contract": "digital_anchor_task_entry_v1",
            "entry": _entry_for_config(entry),
            "next_surfaces": {
                "workbench": f"/tasks/{task_id}",
                "delivery": f"/tasks/{task_id}/publish",
            },
        },
        "packet": {
            "line_id": DIGITAL_ANCHOR_LINE_ID,
            "packet_version": "v1",
            "metadata": {"notes": _metadata_notes(entry)},
            "line_specific_refs": [
                {
                    "ref_id": "digital_anchor_role_pack",
                    "path": "docs/contracts/digital_anchor/role_pack_contract_v1.md",
                    "version": "v1",
                    "binds_to": ["factory_input_contract_v1"],
                },
                {
                    "ref_id": "digital_anchor_speaker_plan",
                    "path": "docs/contracts/digital_anchor/speaker_plan_contract_v1.md",
                    "version": "v1",
                    "binds_to": [
                        "factory_audio_plan_contract_v1",
                        "factory_language_plan_contract_v1",
                        "factory_scene_plan_contract_v1",
                    ],
                },
            ],
        },
        "line_specific_refs": [
            {
                "ref_id": "digital_anchor_role_pack",
                "path": "docs/contracts/digital_anchor/role_pack_contract_v1.md",
                "version": "v1",
                "binds_to": ["factory_input_contract_v1"],
            },
            {
                "ref_id": "digital_anchor_speaker_plan",
                "path": "docs/contracts/digital_anchor/speaker_plan_contract_v1.md",
                "version": "v1",
                "binds_to": [
                    "factory_audio_plan_contract_v1",
                    "factory_language_plan_contract_v1",
                    "factory_scene_plan_contract_v1",
                ],
            },
        ],
    }
    return normalize_task_payload(deepcopy(payload), is_new=True)


__all__ = [
    "DIGITAL_ANCHOR_CREATE_ROUTE",
    "DIGITAL_ANCHOR_LINE_ID",
    "DIGITAL_ANCHOR_OPTIONAL_FIELDS",
    "DIGITAL_ANCHOR_REQUIRED_FIELDS",
    "DUB_KIND_SET",
    "DigitalAnchorCreateEntry",
    "LIP_SYNC_KIND_SET",
    "ROLE_FRAMING_KIND_SET",
    "build_digital_anchor_entry",
    "build_digital_anchor_task_payload",
]
