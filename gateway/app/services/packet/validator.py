"""Factory packet validator.

Implements:
  - E1..E5 envelope structural rules from `factory_packet_envelope_contract_v1.md`
  - R1..R5 content rules from `factory_packet_validator_rules_v1.md`

Read-only. Emits `PacketValidationReport`. Does not mutate input or write
any L1/L2/L3/L4 state.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .envelope import Advisory, FieldRef, PacketValidationReport, Violation

RULE_SET_VERSION = "v1"
ENVELOPE_VERSION = "v1"

LINE_IDS: frozenset[str] = frozenset({"hot_follow", "matrix_script", "digital_anchor"})

CAPABILITY_KINDS: frozenset[str] = frozenset(
    {
        "understanding",
        "subtitles",
        "dub",
        "video_gen",
        "avatar",
        "face_swap",
        "post_production",
        "pack",
        "variation",
        "speaker",
        "lip_sync",
    }
)

FORBIDDEN_STATE_FIELDS: frozenset[str] = frozenset(
    {
        "status",
        "state",
        "phase",
        "stage_status",
        "ready",
        "is_ready",
        "ready_state",
        "ready_gate",
        "done",
        "completed",
        "finished",
        "current_attempt",
        "attempt_state",
        "step_status",
        "pipeline_status",
        "publishable",
        "is_publishable",
        "delivery_ready",
        "final_ready",
    }
)

VENDOR_TOKENS: frozenset[str] = frozenset(
    {
        "akool",
        "fal",
        "kling",
        "wan",
        "azure",
        "gemini",
        "openai",
        "whisper",
        "anthropic",
        "elevenlabs",
        "runway",
        "pika",
    }
)

FORBIDDEN_VENDOR_FIELDS: frozenset[str] = frozenset(
    {"vendor_id", "model_id", "provider", "provider_id", "engine_id"}
)

GENERIC_PATH_RE = re.compile(r"^docs/contracts/factory_[a-z_]+_contract_v[0-9]+\.md$")
PACKET_VERSION_RE = re.compile(r"^v[0-9]+(\.[0-9]+)?$")
PERMITTED_READY_STATES: frozenset[str] = frozenset(
    {"draft", "validating", "ready", "gated", "frozen"}
)
DONOR_TOKEN = "swiftcraft"  # Banned per master plan; never appear in packets.


def _heading_for_path(path: str) -> str:
    """Derive expected first-heading text from a `factory_*_contract_v1.md` path."""
    name = Path(path).stem  # factory_input_contract_v1
    parts = name.split("_")
    return "# " + " ".join(p.capitalize() for p in parts)


def _walk(obj: Any, prefix: str = ""):
    """Yield (path, key, value) for every dict key in a nested object."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            here = f"{prefix}.{k}" if prefix else k
            yield here, k, v
            yield from _walk(v, here)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            here = f"{prefix}[{i}]"
            yield from _walk(v, here)


def _string_values(obj: Any, prefix: str = ""):
    if isinstance(obj, str):
        yield prefix, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            here = f"{prefix}.{k}" if prefix else k
            yield from _string_values(v, here)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _string_values(v, f"{prefix}[{i}]")


def validate_packet(
    packet: dict[str, Any],
    *,
    contracts_root: Path | str = "docs/contracts",
    schema_path: Path | str | None = None,
) -> PacketValidationReport:
    """Validate a packet envelope dict; return read-only report."""
    contracts_root = Path(contracts_root)
    violations: list[Violation] = []
    missing: list[FieldRef] = []
    advisories: list[Advisory] = []

    for key in (
        "line_id",
        "packet_version",
        "generic_refs",
        "line_specific_refs",
        "binding",
        "evidence",
    ):
        if key not in packet:
            missing.append(FieldRef(path=key))

    if missing:
        return PacketValidationReport(
            ok=False,
            missing=missing,
            violations=violations,
            advisories=advisories,
            rule_versions={"rules": RULE_SET_VERSION, "envelope": ENVELOPE_VERSION},
        )

    line_id = packet["line_id"]
    if line_id not in LINE_IDS:
        violations.append(
            Violation("E1.unregistered-line-id", "line_id", f"line_id '{line_id}' is not registered")
        )

    if not PACKET_VERSION_RE.match(str(packet.get("packet_version", ""))):
        violations.append(
            Violation(
                "E1.bad-packet-version",
                "packet_version",
                f"packet_version '{packet.get('packet_version')}' is not vN[.M]",
            )
        )

    generic_ref_ids: set[str] = set()
    for i, ref in enumerate(packet.get("generic_refs", []) or []):
        base = f"generic_refs[{i}]"
        path = ref.get("path", "")
        ref_id = ref.get("ref_id")
        if ref_id:
            generic_ref_ids.add(ref_id)

        if not GENERIC_PATH_RE.match(path):
            violations.append(
                Violation("E2.non-generic-path", f"{base}.path", f"path '{path}' is not factory-generic")
            )
            continue

        repo_path = Path(path)
        if not repo_path.exists():
            violations.append(
                Violation("R1.path-not-found", f"{base}.path", f"contract file '{path}' does not exist")
            )
            continue

        first_line = repo_path.read_text(encoding="utf-8").splitlines()[0].strip()
        expected = _heading_for_path(path)
        if first_line.lower() != expected.lower():
            violations.append(
                Violation(
                    "R1.heading-mismatch",
                    f"{base}.path",
                    f"first heading '{first_line}' does not match expected '{expected}'",
                )
            )

        if not PACKET_VERSION_RE.match(str(ref.get("version", ""))):
            violations.append(
                Violation(
                    "R1.version-skew",
                    f"{base}.version",
                    f"version '{ref.get('version')}' is not vN[.M]",
                )
            )

    for j, lref in enumerate(packet.get("line_specific_refs", []) or []):
        base = f"line_specific_refs[{j}]"
        for k, dep in enumerate(lref.get("binds_to", []) or []):
            if dep not in generic_ref_ids:
                violations.append(
                    Violation(
                        "E3.dangling-binds_to",
                        f"{base}.binds_to[{k}]",
                        f"binds_to '{dep}' is not a known generic ref_id",
                    )
                )
        delta = lref.get("delta")
        if isinstance(delta, dict):
            forbidden_full_shapes = {
                "factory_input",
                "factory_content_structure",
                "factory_scene_plan",
                "factory_audio_plan",
                "factory_language_plan",
                "factory_delivery",
            }
            for fk in delta.keys():
                if fk in forbidden_full_shapes:
                    violations.append(
                        Violation(
                            "R2.duplicate-shape",
                            f"{base}.delta.{fk}",
                            "line-specific delta redeclares a generic-shape full record",
                        )
                    )
            if not lref.get("binds_to"):
                violations.append(
                    Violation(
                        "R2.missing-binds_to",
                        f"{base}.binds_to",
                        "line-specific ref carries delta but declares no binds_to",
                    )
                )

    binding = packet.get("binding", {}) or {}
    plan = binding.get("capability_plan", []) or []
    for n, entry in enumerate(plan):
        base = f"binding.capability_plan[{n}]"
        kind = entry.get("kind")
        if kind not in CAPABILITY_KINDS:
            violations.append(
                Violation("R3.unknown-kind", f"{base}.kind", f"kind '{kind}' is not in closed set")
            )
        for fk in entry.keys():
            if fk in FORBIDDEN_VENDOR_FIELDS:
                violations.append(
                    Violation("R3.provider-pin", f"{base}.{fk}", f"vendor-pin field '{fk}' is forbidden")
                )
        for fpath, sval in _string_values(entry, base):
            tokens = set(re.findall(r"[a-z]+", sval.lower()))
            leaked = tokens & VENDOR_TOKENS
            if leaked:
                violations.append(
                    Violation(
                        "R3.vendor-leak",
                        fpath,
                        f"vendor token(s) {sorted(leaked)} present in value",
                    )
                )

    schema_p = Path(schema_path) if schema_path else None
    if schema_p is not None:
        if not schema_p.exists():
            violations.append(
                Violation("R4.parse-error", str(schema_p), "schema file does not exist")
            )
        else:
            try:
                schema = json.loads(schema_p.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                violations.append(Violation("R4.parse-error", str(schema_p), f"json parse: {e}"))
                schema = None
            if schema is not None:
                if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
                    violations.append(
                        Violation(
                            "R4.draft-mismatch",
                            f"{schema_p}#/$schema",
                            "schema is not Draft 2020-12",
                        )
                    )
                if not schema.get("$id"):
                    violations.append(
                        Violation("R4.missing-id", f"{schema_p}#/$id", "schema is missing $id")
                    )
                try:
                    from jsonschema import Draft202012Validator

                    Draft202012Validator.check_schema(schema)
                    errors = sorted(
                        Draft202012Validator(schema).iter_errors(packet), key=lambda e: e.path
                    )
                    for err in errors:
                        loc = "/".join(str(p) for p in err.absolute_path) or "<root>"
                        violations.append(
                            Violation("R4.sample-fails", loc, err.message.splitlines()[0])
                        )
                except ImportError:
                    advisories.append(
                        Advisory("R4.skipped", str(schema_p), "jsonschema not installed; schema validation skipped")
                    )

    evidence = packet.get("evidence", {}) or {}
    ready_state = evidence.get("ready_state")
    if ready_state not in PERMITTED_READY_STATES:
        violations.append(
            Violation(
                "E4.bad-ready-state",
                "evidence.ready_state",
                f"ready_state '{ready_state}' is not in {{draft,validating,ready,gated,frozen}}",
            )
        )

    for fpath, key, _value in _walk(packet):
        if key in FORBIDDEN_STATE_FIELDS and fpath != "evidence.ready_state":
            violations.append(
                Violation("R5.forbidden-field-name", fpath, f"forbidden state field '{key}'")
            )

    for fpath, sval in _string_values(packet):
        if DONOR_TOKEN in sval.lower():
            violations.append(
                Violation("R3.vendor-leak", fpath, f"donor token '{DONOR_TOKEN}' is forbidden")
            )

    plan_kinds = [e.get("kind") for e in plan]
    for n, entry in enumerate(plan):
        if entry.get("kind") not in CAPABILITY_KINDS:
            violations.append(
                Violation(
                    "E5.kind-not-in-closure",
                    f"binding.capability_plan[{n}].kind",
                    "kind violates envelope-level closure",
                )
            )
    if len(set(plan_kinds)) != len(plan_kinds):
        advisories.append(
            Advisory("E5.duplicate-kinds", "binding.capability_plan", "duplicate capability kinds present")
        )

    return PacketValidationReport(
        ok=not violations and not missing,
        missing=missing,
        violations=violations,
        advisories=advisories,
        rule_versions={"rules": RULE_SET_VERSION, "envelope": ENVELOPE_VERSION},
    )
