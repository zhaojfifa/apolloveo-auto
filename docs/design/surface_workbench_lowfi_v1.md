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

---

## Extension — four generic panels, L2/L3 strips, line-specific slot

> Tightens the Workbench skeleton to match `ApolloVeo_Operator_Visible_Surfaces_v1.md` §5.3. Names the four generic panels explicitly, adds a top L2 artifact-facts strip and right-rail L3 strip, and confirms the single line-specific mount slot used by all three lines.

### Page Goal

Single execution shell for any open packet. Renders four generic panels driven by the four generic factory contracts, a fact strip from L2, an attempt/gate/advisory strip from L3, and one line-specific side panel chosen from `line_specific_refs[]`.

### Extended low-fi layout

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  WORKBENCH — <line> · <packet_version>     Gate: ●ready  Ref: hot_follow ✓   │
├──────────────────────────────────────────────────────────────────────────────┤
│  L2 ARTIFACT FACTS STRIP  (read-only)                                         │
│  final ✓ · subtitle ✓ · audio ✓ · pack ◐ · manifest ✓                         │
├────────────────────┬────────────────────────────────┬────────────────────────┤
│ CAPABILITY SPINE   │  ACTIVE GENERIC PANEL          │ LINE-SPECIFIC SLOT     │
│ ──────────────     │  ───────────────────────       │ ─────────────────       │
│ ▣ understanding    │  one of:                       │ matrix_script →        │
│ ▣ variation        │   · content_structure          │   variation panel      │
│ ▢ subtitles        │   · scene_plan                 │ digital_anchor →       │
│ ▢ dub (optional)   │   · audio_plan                 │   role/speaker panel   │
│ ▢ pack (optional)  │   · language_plan              │ hot_follow →           │
│                    │  contract-shaped controls only │   subtitle authority   │
│                    │  no provider/model/vendor UI   │   panel                │
│                    │                                │                        │
│                    │                                │ L3 STRIP (right-rail)  │
│                    │                                │ ───────────────        │
│                    │                                │ current_attempt: a07   │
│                    │                                │ gate: ready            │
│                    │                                │ advisory: —            │
├────────────────────┴────────────────────────────────┴────────────────────────┤
│  EVIDENCE STRIP   reference_line: hot_follow   validator_report: [open]      │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Four generic panels

| Panel | Backing contract | Notes |
|---|---|---|
| `content_structure` | `factory_content_structure_contract` | Hook / Body / CTA structure, slot pack pointers. Read-mostly. |
| `scene_plan` | `factory_scene_plan_contract` | Scene template assembly, role/scene binding hints. Pack content non-blocking. |
| `audio_plan` | `factory_audio_plan_contract` | Speaker plan, dub kind, lip-sync constraints. |
| `language_plan` | `factory_language_plan_contract` | Per-language scope, subtitle/dub matrix. |

Each panel is a contract-shaped read/edit view. None of them author truth; edits propagate as proposed packet patches that the gateway validates.

### L2 artifact facts strip (top)

Strict projection of L2 artifact facts: presence chips for `final`, `subtitle`, `audio`, `pack`, `manifest`. Source: gateway L2 facts payload — never recomputed by UI. Optional artifacts (`pack`) render with a subordinate marker and never gate downstream affordances.

### L3 current attempt / gate / advisory strip (right-rail)

The only place where attempt-level state renders. Fields:

| Field | Source |
|---|---|
| `current_attempt` id | L3 `current_attempt.id` |
| `gate` chip | L3 `current_attempt.gate_state` (also surfaced in header for ambient awareness) |
| `advisory` text | L3 `current_attempt.advisory` (read-only) |
| `requires_redub` / `requires_recompose` | L3 boolean flags, surfaced as inline notes only |

The strip never authors any of these values; if a field is absent on the L3 payload, the row renders blank.

### Line-specific side-panel slot

Single mount point on the right column. Content is selected by `line_specific_refs[].ref_id`:

| `line_id` | `ref_id` resolved | Panel mounted |
|---|---|---|
| `matrix_script` | `matrix_script_variation_matrix` / `matrix_script_slot_pack` | [Matrix Script Variation Panel](panel_matrix_script_variation_lowfi_v1.md) |
| `digital_anchor` | `digital_anchor_role_pack` / `digital_anchor_speaker_plan` | [Digital Anchor Role/Speaker Panel](panel_digital_anchor_role_speaker_lowfi_v1.md) |
| `hot_follow` | `hot_follow_subtitle_authority` / `hot_follow_dub_compose_legality` | [Hot Follow Subtitle Authority Panel](panel_hot_follow_subtitle_authority_lowfi_v1.md) |

The slot is always exactly one panel — no tabs, no side-by-side line panels, no second-line bleed-in. Any other `line_id` in the future plugs into this same slot.

### Non-blocking guarantee (re-affirmed)

- `pack` and any other `required: false` capability never gate other capabilities or the publish projection.
- The L2 strip shows `pack` presence but never raises a blocker; the gate badge does not change because `pack` is incomplete.

### Extended Contract Mapping

| UI element | Contract object |
|---|---|
| Generic panel: content_structure | `factory_content_structure_contract` |
| Generic panel: scene_plan | `factory_scene_plan_contract` |
| Generic panel: audio_plan | `factory_audio_plan_contract` |
| Generic panel: language_plan | `factory_language_plan_contract` |
| L2 strip presence chips | L2 artifact facts (`final`, `subtitle`, `audio`, `pack`, `manifest`) |
| L3 strip fields | `current_attempt.{id, gate_state, advisory, requires_redub, requires_recompose}` |
| Line-specific slot mount | `line_specific_refs[]` resolved by `ref_id` |
| Header gate badge | `evidence.ready_state` |
| Reference baseline | `evidence.reference_line` + `evidence.reference_evidence_path` |

### Notes / Known Deferrals
- **Re-run / regenerate affordances**: design exposes them only when L3 marks the attempt as stale (`requires_redub` / `requires_recompose`). Wiring deferred to engineering confirmation.
- **Line switcher**: not provided. A Workbench instance is bound to one `line_id`; switching means navigating back to the Board.
- **Comparison view** (current attempt vs. historical): deferred. The L2 strip shows historical artifact presence, the L3 strip shows current attempt — comparison is design-deferred.
- **Asset library access**: explicitly not provided in Workbench. Operators bounce to the B-roll / Asset page.
