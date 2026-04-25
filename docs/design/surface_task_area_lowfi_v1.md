# Surface 1 — Task Area (Low-fi v1)

**Purpose**: The operator's entry surface. Pick or intake a packet, see whether it has cleared the gate, and route to the Workbench. The Task Area is **read-mostly** with respect to gate truth — it never authors a `ready_state`, it only renders one.

## Layout (low-fi)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  TASK AREA                                              [+ New Packet]  │
├─────────────────────────────────────────────────────────────────────────┤
│  Filter: [ Line ▾ ] [ Gate State ▾ ] [ Search ____________ ]            │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌── Packet Card ──────────────────────────────────────────────────┐    │
│  │  Line: matrix_script         packet_version: v1                 │    │
│  │  Gate: ● ready               Reference: hot_follow ✓            │    │
│  │  Capabilities: understanding · variation · subtitles · …        │    │
│  │  Generic refs: 6/6   Line-specific refs: 2/2                    │    │
│  │  [ Open in Workbench ]   [ View validator report ]              │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│  ┌── Packet Card ──────────────────────────────────────────────────┐    │
│  │  Line: digital_anchor        packet_version: v1                 │    │
│  │  Gate: ◐ validating          Reference: hot_follow ✓            │    │
│  │  Capabilities: avatar · speaker · subtitles · dub · …           │    │
│  │  [ Open (read-only) ]   [ View validator report ]               │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

## Regions

| Region | Role | Notes |
|---|---|---|
| Header | New-packet intake | Launches a contract-shaped intake form scoped to envelope-required fields only. |
| Filters | Index narrowing | `Line` filter values are the literal `line_id` constants from the packet schemas. `Gate State` filter values are the five `ready_state` enum values. No invented buckets. |
| Packet Card list | Per-packet projection | One card per packet. Card content is a strict projection of envelope fields. |

## Packet Card — fields and bindings

| Field rendered | Source (contract path) | Notes |
|---|---|---|
| Line label | `line_id` | Display literal value; no relabeling. |
| `packet_version` | `packet_version` | Show as text. |
| Gate badge | `evidence.ready_state` | Five-state badge: `draft`, `validating`, `ready`, `gated`, `frozen`. No "in progress", "running", "done". |
| Reference badge | `evidence.reference_line` + `evidence.reference_evidence_path` | Always shows `hot_follow`. Green check iff `reference_evidence_path` resolves to a present file (truth from validator, not surface). |
| Capability chips | `binding.capability_plan[].kind` | Render each `kind` as a chip. `mode` shown on hover. `required: false` chips render with a dotted border. |
| Generic refs counter | `generic_refs.length` | Format `n/6` (envelope `minItems: 6`). |
| Line-specific refs counter | `line_specific_refs.length` | Format `n/2` (envelope `minItems: 2`). |

## Open routing

- `[ Open in Workbench ]` only enabled when `evidence.ready_state ∈ {ready, frozen}`.
- All other `ready_state` values render `[ Open (read-only) ]`, which routes to Workbench in inspect mode (no execution affordance).
- `[ View validator report ]` opens `evidence.validator_report_path` in a side drawer.

## State the Task Area must NOT invent

- No "draft saved", "submitted", "in queue", "running", "completed".
- No vendor / model / provider / engine selectors at intake.
- No donor or supply UI. The intake form has no concept of capability sourcing.
- No "publishable" / "delivery_ready" / "final_ready" — these are explicitly forbidden by the envelope's metadata `not` clause.

## Contract Mapping Notes

| UI element | Contract object | Contract path |
|---|---|---|
| Line filter | `line_id` const | packet.schema.json `properties.line_id.const` |
| Gate badge | `ready_state` enum | packet.schema.json `$defs.evidence.properties.ready_state.enum` |
| Reference badge | `reference_line` const | packet.schema.json `$defs.evidence.properties.reference_line.const` |
| Capability chips | `capability_plan[].kind` | packet.schema.json `$defs.capabilityEntry.properties.kind.enum` |
| Generic refs counter | `generic_refs` array | packet.schema.json `properties.generic_refs.minItems` |
| Line-specific refs counter | `line_specific_refs` array | packet.schema.json `properties.line_specific_refs.minItems` |
| Validator report link | `validator_report_path` | packet.schema.json `$defs.evidence.properties.validator_report_path` |

**Gate Truth Rule**: The Task Area never writes `ready_state`. The badge is a one-way projection of validator output.
