# Panel — Digital Anchor Role / Speaker (Low-fi v1)

**Embedded in**: Workbench Active Capability Pane, when the selected `capability_plan[].kind` is `avatar` (Role view) or `speaker` (Speaker view).
**Line**: `digital_anchor`
**Backed by**: `line_specific_refs[ref_id=digital_anchor_role_pack]` and `line_specific_refs[ref_id=digital_anchor_speaker_plan]`.

The panel is one panel with two views. The Workbench spine activates the appropriate view depending on which capability row the operator selects.

## Layout (low-fi)

### View A — Roles (capability `avatar`)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  DIGITAL ANCHOR — Role Pack                                                   │
├──────────────────────────────────────────────────────────────────────────────┤
│  ┌── Role Card ────────────────────────────────────────────────────────────┐ │
│  │  role_anchor_a       Anchor A                                           │ │
│  │  framing_kind: half_body                                                │ │
│  │  language_scope_ref: lang_scope_en_zh                                   │ │
│  │  appearance_ref: catalog://role_card/anchor_a_v1     [preview]          │ │
│  │  notes: primary anchor for product launch line                          │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│  ┌── Role Card ────────────────────────────────────────────────────────────┐ │
│  │  role_anchor_b       Anchor B                                           │ │
│  │  framing_kind: head                                                     │ │
│  │  language_scope_ref: lang_scope_en_only                                 │ │
│  │  appearance_ref: catalog://role_card/anchor_b_v1     [preview]          │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│  Allowed framings: head · half_body · full_body                               │
│  Allowed appearance kinds: role_card · role_pose_set                          │
└──────────────────────────────────────────────────────────────────────────────┘
```

### View B — Speakers (capability `speaker`, optionally with `lip_sync`)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  DIGITAL ANCHOR — Speaker Plan                                                │
├──────────────────────────────────────────────────────────────────────────────┤
│  ┌────────────┬─────────────────┬────────────────┬────────────┬───────────┐ │
│  │ segment_id │ role            │ dub_kind       │ lip_sync   │ language  │ │
│  ├────────────┼─────────────────┼────────────────┼────────────┼───────────┤ │
│  │ seg_001    │ role_anchor_a ↗ │ tts_role_voice │ tight      │ en-US     │ │
│  │ seg_002    │ role_anchor_a ↗ │ tts_role_voice │ tight      │ zh-CN     │ │
│  │ seg_003    │ role_anchor_b ↗ │ tts_neutral    │ loose      │ en-US     │ │
│  └────────────┴─────────────────┴────────────────┴────────────┴───────────┘ │
│                                                                               │
│  Segment detail (expanded):                                                   │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ segment_id: seg_001    binds_role_id: role_anchor_a                    │ │
│  │ script_ref: content://digital_anchor/v1/seg_001     [open]             │ │
│  │ dub_kind: tts_role_voice    lip_sync_kind: tight    language: en-US    │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│  Allowed dub kinds:      tts_neutral · tts_role_voice · source_passthrough    │
│  Allowed lip_sync kinds: tight · loose · none                                 │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Role view binding

| UI element | Source |
|---|---|
| Role card list | `role_pack.delta.roles[]` |
| `role_id` | `role_pack.delta.roles[].role_id` |
| Display name | `role_pack.delta.roles[].display_name` |
| Framing | `role_pack.delta.roles[].framing_kind` (constrained by `role_pack.delta.framing_kind_set`) |
| Language scope link | `role_pack.delta.roles[].language_scope_ref` (resolves through `factory_language_plan` / `g_lang`) |
| Appearance preview | `role_pack.delta.roles[].appearance_ref` (kind constrained by `role_pack.delta.appearance_ref_kind_set`) |
| Notes | `role_pack.delta.roles[].notes` |

## Speaker view binding

| UI element | Source |
|---|---|
| Segment table | `speaker_plan.delta.segments[]` |
| `segment_id` | `speaker_plan.delta.segments[].segment_id` |
| Role link | `speaker_plan.delta.segments[].binds_role_id` (jump to Role view, `role_pack.delta.roles[role_id=...]`) |
| `dub_kind` | `speaker_plan.delta.segments[].dub_kind` (constrained by `speaker_plan.delta.dub_kind_set`) |
| `lip_sync_kind` | `speaker_plan.delta.segments[].lip_sync_kind` (constrained by `speaker_plan.delta.lip_sync_kind_set`) |
| `language_pick` | `speaker_plan.delta.segments[].language_pick` |
| `script_ref` | `speaker_plan.delta.segments[].script_ref` |

## Discipline

- Both views render only `delta` content from the two `lineSpecificRef` entries. They never fabricate roles, segments, or kind values.
- The panel exposes the categorical kind sets (`framing_kind_set`, `appearance_ref_kind_set`, `dub_kind_set`, `lip_sync_kind_set`) as **labels and constraints**, never as vendor or engine selectors. The operator picks a kind; sourcing is invisible.
- Cross-reference rule "every `segments[].binds_role_id` resolves to a `roles[].role_id`" is rendered as a non-blocking inline warning if violated. The panel does not author a new state for this; the gate badge follows `evidence.ready_state`.
- `lip_sync` capability row is `required: false` in the sample packet; the Speaker view must render the column even when `lip_sync` is optional, and must not block segments whose `lip_sync_kind` is `none`.
- No vendor / model / provider / engine fields. The string "TTS engine selection" or "avatar engine selection" must not appear.
- No donor / supply UI.

## Contract Mapping Notes

| UI element | Contract object | Contract path |
|---|---|---|
| Role cards | `role_pack.delta.roles` | digital_anchor `$defs.lineSpecificRef.properties.delta` (line contract: `docs/contracts/digital_anchor/role_pack_contract_v1.md`) |
| Framing constraint | `role_pack.delta.framing_kind_set` | same |
| Appearance kind constraint | `role_pack.delta.appearance_ref_kind_set` | same |
| Segment table | `speaker_plan.delta.segments` | `docs/contracts/digital_anchor/speaker_plan_contract_v1.md` |
| Dub kind constraint | `speaker_plan.delta.dub_kind_set` | same |
| Lip-sync kind constraint | `speaker_plan.delta.lip_sync_kind_set` | same |
| Role↔Segment link | `segments[].binds_role_id` ↔ `roles[].role_id` | digital_anchor role_pack + speaker_plan |
| Language scope | `roles[].language_scope_ref`, `segments[].language_pick` | rooted in `factory_language_plan_contract_v1` (`g_lang`) |
| View A trigger | `binding.capability_plan[kind=avatar]` | packet.schema.json `$defs.capabilityEntry.properties.kind.enum` |
| View B trigger | `binding.capability_plan[kind=speaker]` (with optional `lip_sync`) | same |

**Embedding rule**: This panel is mounted only when the active spine row's `kind ∈ {avatar, speaker}`. It never appears in any other line's Workbench.
