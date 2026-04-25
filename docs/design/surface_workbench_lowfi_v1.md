# Surface 2 — Workbench (Low-fi v1)

**Purpose**: The execution shell for an open packet. Renders `binding.capability_plan` as the spine and lets the operator drive each capability without ever choosing a vendor, model, provider, or engine. Line-specific work is delegated to the dedicated panel slot.

## Layout (low-fi)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  WORKBENCH — matrix_script · v1            Gate: ● ready   Ref: hot_follow ✓  │
├──────────────────────┬───────────────────────────────────────────────────────┤
│  CAPABILITY SPINE    │   ACTIVE CAPABILITY PANE                              │
│  ────────────────    │   ─────────────────────────────                       │
│  ▣ understanding  ✓  │                                                        │
│  ▣ variation     ◐   │   [ Line-specific Panel slot ]                         │
│  ▢ subtitles         │                                                        │
│  ▢ dub (optional)    │   (For matrix_script → variation panel here.          │
│  ▢ pack (optional)   │    For digital_anchor → role/speaker panel here.)     │
│                      │                                                        │
│                      │   Generic-capability panes render envelope-shaped      │
│                      │   inputs/outputs only. No vendor selectors.            │
├──────────────────────┴───────────────────────────────────────────────────────┤
│  EVIDENCE STRIP   reference_line: hot_follow   validator_report: [open]      │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Regions

| Region | Role | Notes |
|---|---|---|
| Header | Identity + gate | Shows `line_id`, `packet_version`, `evidence.ready_state`, reference. Read-only. |
| Capability Spine (left rail) | One row per `capability_plan[]` entry | Drives navigation. |
| Active Capability Pane (right) | Renders the selected capability | For line-specific `kind`s, embeds the line panel. |
| Evidence Strip (bottom) | Reference baseline + validator report | Always visible, read-only. |

## Capability Spine — row binding

| Element | Source | Notes |
|---|---|---|
| Row label | `capability_plan[].kind` | Literal enum value: `understanding`, `subtitles`, `dub`, `video_gen`, `avatar`, `face_swap`, `post_production`, `pack`, `variation`, `speaker`, `lip_sync`. |
| Mode hint | `capability_plan[].mode` | Shown as secondary text. |
| Optional indicator | `capability_plan[].required === false` | Renders the row with a dotted leading marker. |
| Inputs / Outputs hover | `capability_plan[].inputs`, `capability_plan[].outputs` | Free-form strings, displayed verbatim. |
| Quality / Language hint | `capability_plan[].quality_hint`, `capability_plan[].language_hint` | Shown inline on hover. |

**Forbidden in spine rows**: any field named `vendor_id`, `model_id`, `provider`, `provider_id`, `engine_id` — explicitly forbidden by the envelope schema's `capabilityEntry.not` clause.

## Active Capability Pane — routing

| `kind` | Pane content |
|---|---|
| `variation` | Embed the **Matrix Script Variation Panel** (line-specific). |
| `speaker` | Embed the **Digital Anchor Speaker segment view** of the role/speaker panel. |
| `avatar` | Embed the **Digital Anchor Role view** of the role/speaker panel. |
| `pack` | Generic Scene-Pack pane. **Non-blocking**: spine never disables downstream rows when `pack` is incomplete. |
| All other generic kinds | Generic pane that reads `inputs`/`outputs` and renders contract-shaped controls only. |

## Gate-state effect on Workbench

| `evidence.ready_state` | Workbench mode |
|---|---|
| `draft` | Read-only, banner: "Gate not yet validated". |
| `validating` | Read-only, banner: "Validator running". |
| `ready` | Full execution affordances enabled. |
| `gated` | Read-only, banner: "Gate held. See validator report." |
| `frozen` | Read-only, banner: "Packet frozen". |

The Workbench **does not author** `ready_state` transitions. It renders the current value and disables write affordances accordingly.

## Non-blocking guarantee for Scene Pack

- The `pack` row never sets a `required: true` blocker for any other row.
- Operator can advance any other capability while `pack` is incomplete.
- The header gate badge does not change because `pack` is incomplete.

## Hot Follow reference

- The Evidence Strip always shows `reference_line: hot_follow` and a link to `reference_evidence_path`.
- This strip is the only place where the reference-line concept surfaces. There is no donor / supply / sourcing UI anywhere.

## Contract Mapping Notes

| UI element | Contract object | Contract path |
|---|---|---|
| Header line + version | `line_id`, `packet_version` | packet.schema.json `properties` |
| Header gate badge | `evidence.ready_state` | `$defs.evidence.properties.ready_state` |
| Spine row | `binding.capability_plan[]` | `$defs.binding.properties.capability_plan` |
| Spine row label | `capability_plan[].kind` | `$defs.capabilityEntry.properties.kind` |
| Spine row mode | `capability_plan[].mode` | `$defs.capabilityEntry.properties.mode` |
| Spine row optional marker | `capability_plan[].required` | `$defs.capabilityEntry.properties.required` |
| Active pane (variation) | `line_specific_refs[ref_id=matrix_script_variation_matrix]` | matrix_script `$defs.lineSpecificRef.properties.ref_id.enum` |
| Active pane (speaker) | `line_specific_refs[ref_id=digital_anchor_speaker_plan]` | digital_anchor `$defs.lineSpecificRef.properties.ref_id.enum` |
| Active pane (avatar / role) | `line_specific_refs[ref_id=digital_anchor_role_pack]` | digital_anchor `$defs.lineSpecificRef.properties.ref_id.enum` |
| Evidence Strip reference | `evidence.reference_line`, `evidence.reference_evidence_path` | `$defs.evidence.properties` |
| Validator open | `evidence.validator_report_path` | `$defs.evidence.properties.validator_report_path` |

**Discipline**: Workbench has zero local state machine. Every visible status is a render of `evidence.ready_state` plus per-capability content read from `capability_plan[]` and `line_specific_refs[]`.
