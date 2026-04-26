# Hot Follow Reference Packet — Validator + Onboarding Gate Evidence v1

Date: 2026-04-25
Status: Green reference baseline (P2 pre-unlock wave)
Authority:
- `docs/contracts/factory_packet_envelope_contract_v1.md`
- `docs/contracts/factory_packet_validator_rules_v1.md`
- `docs/execution/apolloveo_2_0_p2_gate_checklist_v1.md` (Packet gate)

## Purpose

Establish Hot Follow as the green reference baseline for the factory packet
validator and onboarding gate. Future packets (Matrix Script, Digital Anchor)
must produce a comparable green report before they can move from `gated` /
`validating` toward `ready`.

This evidence does NOT promote any line into runtime onboarding; the runtime
gate remains Blocked per `docs/execution/apolloveo_2_0_p2_gate_checklist_v1.md`.

## Inputs

- Packet instance: `schemas/packets/hot_follow/sample/reference_packet_v1.json`
- Validator: `gateway/app/services/packet/validator.py` (R1..R5, E1..E5)
- Onboarding gate: `gateway/app/services/packet/onboarding_gate.py`
- Reference evidence anchor: `docs/contracts/hot_follow_line_contract.md`

## Validator Report (in-process)

| Field | Value |
| --- | --- |
| `ok` | `True` |
| `violations` | `[]` |
| `missing` | `[]` |
| `advisories` | 4 × `A.unused-generic-ref` (factory_input, factory_audio_plan, factory_language_plan, factory_delivery — informational) |
| `rule_versions.content_rules` | `v1` |
| `rule_versions.envelope_rules` | `v1` |

The advisories are non-blocking by design (R1..R5 do not require every
generic_ref to be bound; the reference packet binds only the scene plan
delta as a minimal example).

## Onboarding Gate Result

| Field | Value |
| --- | --- |
| `gate_status` | `passed` |
| `blocked_reasons` | `[]` |
| `evidence_links` | `reference_evidence:docs/contracts/hot_follow_line_contract.md`, `validator_report:docs/execution/evidence/hot_follow_reference_packet_validation_v1.md`, `rule_versions:content_rules=v1,envelope_rules=v1` |
| `rule_versions.onboarding_gate` | `v1` |
| `rule_versions.content_rules` | `v1` |
| `rule_versions.envelope_rules` | `v1` |

## Reproduction

```python
from gateway.app.services.packet.entry import validate_packet_path, envelope_from_dict
from gateway.app.services.packet.onboarding_gate import evaluate_onboarding
import json
from pathlib import Path

p = Path("schemas/packets/hot_follow/sample/reference_packet_v1.json")
report = validate_packet_path(p)
envelope = envelope_from_dict(json.loads(p.read_text()))
gate = evaluate_onboarding(envelope, report)
assert report.ok is True
assert gate.gate_status == "passed"
```

A regression test pinning this baseline lives at
`tests/contracts/packet_validator/test_hot_follow_reference_baseline.py`.

## Use as Reference

Future line packets (Matrix Script, Digital Anchor) MUST cite this evidence
when claiming a green validator pass. The reviewer/donor signoff closure
gate uses this row as the `reference_line` benchmark.

## What this evidence is NOT

- not a P3 runtime onboarding signal (runtime gate remains Blocked)
- not a Hot Follow business-logic change (Hot Follow remains frozen)
- not a packet schema (`packet.schema.json` for Hot Follow is intentionally
  not shipped because Hot Follow is not onboarded as a runtime packet line;
  the reference instance is enough to anchor R1..R5 / E1..E5 truth)
