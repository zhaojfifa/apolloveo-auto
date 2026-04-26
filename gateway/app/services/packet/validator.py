"""Factory packet validator skeleton.

Implements R1..R5 (factory_packet_validator_rules_v1.md) and E1..E5
(factory_packet_envelope_contract_v1.md). Read-only: no packet mutation,
no truth writes, no orchestration.

This is a P1 skeleton — sufficient to validate Hot Follow reference packets
and future Matrix Script / Digital Anchor packets once their schemas land.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable, List, Mapping, Optional, Sequence, Tuple

from .envelope import (
    CAPABILITY_KINDS,
    FORBIDDEN_STATE_FIELDS,
    KNOWN_VENDOR_TOKENS,
    PERMITTED_READY_STATES,
    Advisory,
    FieldRef,
    PacketEnvelope,
    PacketValidationReport,
    Violation,
)

RULE_SET_VERSION = "v1"
ENVELOPE_RULE_SET_VERSION = "v1"

GENERIC_PATH_PREFIX = "docs/contracts/factory_"
GENERIC_PATH_SUFFIX = "_contract_v1.md"

GENERIC_SHAPE_SUFFIXES = (
    "_input",
    "_content_structure",
    "_scene_plan",
    "_audio_plan",
    "_language_plan",
    "_delivery",
    "_delivery_pack",
)


def _fr(path: str) -> FieldRef:
    return FieldRef(path=path)


def _is_vendor_leak(value: Any) -> Optional[str]:
    if not isinstance(value, str):
        return None
    lowered = value.lower()
    for token in KNOWN_VENDOR_TOKENS:
        if token in lowered:
            return token
    return None


def _check_r1_generic_refs(
    envelope: PacketEnvelope, repo_root: Path
) -> Tuple[List[Violation], List[FieldRef]]:
    violations: List[Violation] = []
    missing: List[FieldRef] = []
    for idx, ref in enumerate(envelope.generic_refs):
        base = f"generic_refs[{idx}]"
        if not ref.path.startswith(GENERIC_PATH_PREFIX) or not ref.path.endswith(
            GENERIC_PATH_SUFFIX
        ):
            violations.append(
                Violation(
                    rule_id="R1.path-shape",
                    field=_fr(f"{base}.path"),
                    reason=(
                        f"generic_refs path must start with '{GENERIC_PATH_PREFIX}' "
                        f"and end with '{GENERIC_PATH_SUFFIX}'; got '{ref.path}'"
                    ),
                )
            )
            continue
        full = repo_root / ref.path
        if not full.is_file():
            missing.append(_fr(f"{base}.path"))
            violations.append(
                Violation(
                    rule_id="R1.path-not-found",
                    field=_fr(f"{base}.path"),
                    reason=f"contract file does not exist: {ref.path}",
                )
            )
    return violations, missing


def _walk(obj: Any, prefix: str) -> Iterable[Tuple[str, Any]]:
    if isinstance(obj, Mapping):
        for k, v in obj.items():
            sub = f"{prefix}.{k}" if prefix else k
            yield sub, v
            yield from _walk(v, sub)
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            sub = f"{prefix}[{i}]"
            yield sub, v
            yield from _walk(v, sub)


def _check_r2_no_duplication(envelope: PacketEnvelope) -> List[Violation]:
    violations: List[Violation] = []
    generic_ids = {ref.ref_id for ref in envelope.generic_refs}

    line_ref_index = {ref.ref_id: ref for ref in envelope.line_specific_refs}

    for ref_id, line_ref in line_ref_index.items():
        # Suffix heuristic: if the line-specific contract path looks like a generic-shape
        # extension (e.g. *_scene_plan_v1.md), it MUST declare binds_to into a generic ref.
        path_lower = line_ref.path.lower()
        looks_like_generic = any(suf in path_lower for suf in GENERIC_SHAPE_SUFFIXES)
        if looks_like_generic and not line_ref.binds_to:
            violations.append(
                Violation(
                    rule_id="R2.missing-binds_to",
                    field=_fr(f"line_specific_refs[{ref_id}].binds_to"),
                    reason=(
                        "line-specific contract appears to extend a generic shape but "
                        "declares no binds_to; bind to a generic_ref or rename"
                    ),
                )
            )

    # line_specific_objects payload check: if a payload object names itself with a
    # generic-shape suffix, require a `binds_to` declaration in the corresponding ref.
    for obj_name, obj_payload in envelope.line_specific_objects.items():
        looks_like_generic = any(obj_name.endswith(suf) for suf in GENERIC_SHAPE_SUFFIXES)
        if not looks_like_generic:
            continue
        ref = line_ref_index.get(obj_name)
        if ref is None or not ref.binds_to:
            violations.append(
                Violation(
                    rule_id="R2.duplicate-shape",
                    field=_fr(f"line_specific_objects.{obj_name}"),
                    reason=(
                        f"object '{obj_name}' uses a generic-shape suffix but is not "
                        f"bound to a generic_ref via binds_to"
                    ),
                )
            )
            continue
        # binds_to ids must resolve into generic_refs (E3 also covers this; we re-check here for R2 context)
        for bid in ref.binds_to:
            if bid not in generic_ids:
                violations.append(
                    Violation(
                        rule_id="R2.non-delta-fields-in-binding",
                        field=_fr(f"line_specific_refs[{ref.ref_id}].binds_to"),
                        reason=f"binds_to id '{bid}' does not resolve to a generic_ref",
                    )
                )
    return violations


def _check_r3_capability_kinds(envelope: PacketEnvelope) -> List[Violation]:
    violations: List[Violation] = []
    for idx, item in enumerate(envelope.binding.capability_plan):
        base = f"binding.capability_plan[{idx}]"
        if item.kind not in CAPABILITY_KINDS:
            violations.append(
                Violation(
                    rule_id="R3.unknown-kind",
                    field=_fr(f"{base}.kind"),
                    reason=f"kind '{item.kind}' not in closed set {sorted(CAPABILITY_KINDS)}",
                )
            )
        # Forbid vendor / model / engine fields in extras + any string value matching a vendor token.
        forbidden_keys = {"vendor_id", "model_id", "provider", "provider_id", "engine_id"}
        for k in forbidden_keys:
            if k in item.extras:
                violations.append(
                    Violation(
                        rule_id="R3.provider-pin",
                        field=_fr(f"{base}.{k}"),
                        reason=f"forbidden vendor-pin field '{k}' on capability plan entry",
                    )
                )
        for sub_path, value in _walk(item.extras, base):
            leak = _is_vendor_leak(value)
            if leak is not None:
                violations.append(
                    Violation(
                        rule_id="R3.vendor-leak",
                        field=_fr(sub_path),
                        reason=f"value contains vendor token '{leak}'",
                    )
                )
    return violations


_DRAFT_2020_12_URI = "https://json-schema.org/draft/2020-12/schema"


def _check_r4_schema_loadable(schema_path: Optional[Path]) -> List[Violation]:
    if schema_path is None:
        return []
    violations: List[Violation] = []
    base = f"schema:{schema_path}"
    if not schema_path.is_file():
        violations.append(
            Violation(
                rule_id="R4.parse-error",
                field=_fr(base),
                reason=f"schema file does not exist: {schema_path}",
            )
        )
        return violations
    try:
        data = json.loads(schema_path.read_text())
    except json.JSONDecodeError as exc:
        violations.append(
            Violation(
                rule_id="R4.parse-error",
                field=_fr(base),
                reason=f"JSON parse error: {exc}",
            )
        )
        return violations
    if not isinstance(data, dict):
        violations.append(
            Violation(
                rule_id="R4.parse-error",
                field=_fr(base),
                reason="schema root must be a JSON object",
            )
        )
        return violations
    if data.get("$schema") != _DRAFT_2020_12_URI:
        violations.append(
            Violation(
                rule_id="R4.draft-mismatch",
                field=_fr(f"{base}.$schema"),
                reason=f"$schema must be '{_DRAFT_2020_12_URI}'; got {data.get('$schema')!r}",
            )
        )
    sid = data.get("$id")
    if not isinstance(sid, str) or not sid.startswith("apolloveo://packets/"):
        violations.append(
            Violation(
                rule_id="R4.missing-id",
                field=_fr(f"{base}.$id"),
                reason="$id must be set and start with 'apolloveo://packets/<line_id>/<version>'",
            )
        )
    return violations


def _check_r5_no_state_fields(envelope: PacketEnvelope) -> List[Violation]:
    violations: List[Violation] = []
    # Walk binding, line_specific_objects, and metadata for forbidden field names.
    candidates: List[Tuple[str, Any]] = [
        ("binding", asdict(envelope.binding)),
        ("metadata", dict(envelope.metadata)),
        ("line_specific_objects", dict(envelope.line_specific_objects)),
    ]
    for top, payload in candidates:
        for path, value in _walk(payload, top):
            # Last segment of path is the field name (strip array indices).
            tail = re.sub(r"\[\d+\]", "", path).split(".")[-1]
            if tail in FORBIDDEN_STATE_FIELDS:
                violations.append(
                    Violation(
                        rule_id="R5.forbidden-field-name",
                        field=_fr(path),
                        reason=f"field name '{tail}' is in forbidden state-field set",
                    )
                )
    return violations


# ---- Envelope structural rules E1..E5 ----


def _check_e1_line_id(envelope: PacketEnvelope) -> List[Violation]:
    if not envelope.line_id or not isinstance(envelope.line_id, str):
        return [
            Violation(
                rule_id="E1",
                field=_fr("line_id"),
                reason="line_id must be a non-empty string",
            )
        ]
    return []


def _check_e2_generic_refs_paths(envelope: PacketEnvelope) -> List[Violation]:
    violations: List[Violation] = []
    for idx, ref in enumerate(envelope.generic_refs):
        if not (
            ref.path.startswith(GENERIC_PATH_PREFIX) and ref.path.endswith(GENERIC_PATH_SUFFIX)
        ):
            violations.append(
                Violation(
                    rule_id="E2",
                    field=_fr(f"generic_refs[{idx}].path"),
                    reason="generic_refs paths must point at factory-generic contracts only",
                )
            )
    return violations


def _check_e3_binds_to_resolves(envelope: PacketEnvelope) -> List[Violation]:
    generic_ids = {ref.ref_id for ref in envelope.generic_refs}
    violations: List[Violation] = []
    for idx, ref in enumerate(envelope.line_specific_refs):
        for bid in ref.binds_to:
            if bid not in generic_ids:
                violations.append(
                    Violation(
                        rule_id="E3",
                        field=_fr(f"line_specific_refs[{idx}].binds_to"),
                        reason=f"binds_to id '{bid}' does not resolve to a generic_ref",
                    )
                )
    return violations


def _check_e4_ready_state(envelope: PacketEnvelope) -> List[Violation]:
    rs = envelope.evidence.ready_state
    if rs not in PERMITTED_READY_STATES:
        return [
            Violation(
                rule_id="E4",
                field=_fr("evidence.ready_state"),
                reason=(
                    f"ready_state must be one of {sorted(PERMITTED_READY_STATES)}; got '{rs}'"
                ),
            )
        ]
    return []


def _check_e5_capability_kind_closure(envelope: PacketEnvelope) -> List[Violation]:
    violations: List[Violation] = []
    for idx, item in enumerate(envelope.binding.capability_plan):
        if item.kind not in CAPABILITY_KINDS:
            violations.append(
                Violation(
                    rule_id="E5",
                    field=_fr(f"binding.capability_plan[{idx}].kind"),
                    reason=f"capability kind '{item.kind}' outside closed set",
                )
            )
    return violations


# ---- Public entry point ----


def validate_packet(
    envelope: PacketEnvelope,
    repo_root: Optional[os.PathLike] = None,
    schema_path: Optional[os.PathLike] = None,
) -> PacketValidationReport:
    """Run R1..R5 + E1..E5 against `envelope`.

    `repo_root` defaults to the repo containing this module (four parents up
    from validator.py: gateway/app/services/packet/validator.py → repo root).
    `schema_path` is optional; when provided, R4 is run against that JSON file.
    """
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[4]
    schema = Path(schema_path) if schema_path is not None else None

    violations: List[Violation] = []
    missing: List[FieldRef] = []
    advisories: List[Advisory] = []

    # Envelope structural checks first.
    violations.extend(_check_e1_line_id(envelope))
    violations.extend(_check_e2_generic_refs_paths(envelope))
    violations.extend(_check_e3_binds_to_resolves(envelope))
    violations.extend(_check_e4_ready_state(envelope))
    violations.extend(_check_e5_capability_kind_closure(envelope))

    # Content rules.
    r1_viol, r1_missing = _check_r1_generic_refs(envelope, root)
    violations.extend(r1_viol)
    missing.extend(r1_missing)
    violations.extend(_check_r2_no_duplication(envelope))
    violations.extend(_check_r3_capability_kinds(envelope))
    violations.extend(_check_r4_schema_loadable(schema))
    violations.extend(_check_r5_no_state_fields(envelope))

    # Advisories: unused generic refs.
    referenced = {bid for ref in envelope.line_specific_refs for bid in ref.binds_to}
    for ref in envelope.generic_refs:
        if ref.ref_id not in referenced:
            advisories.append(
                Advisory(
                    code="A.unused-generic-ref",
                    field=_fr(f"generic_refs[{ref.ref_id}]"),
                    note="generic_ref is not bound by any line_specific_ref",
                )
            )

    return PacketValidationReport(
        ok=not violations and not missing,
        missing=missing,
        violations=violations,
        advisories=advisories,
        rule_versions={
            "content_rules": RULE_SET_VERSION,
            "envelope_rules": ENVELOPE_RULE_SET_VERSION,
        },
    )


__all__ = ["validate_packet", "RULE_SET_VERSION", "ENVELOPE_RULE_SET_VERSION"]
