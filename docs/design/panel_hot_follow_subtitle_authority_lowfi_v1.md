# Panel — Hot Follow Subtitle Authority (Low-fi v1)

**Embedded in**: Workbench right-rail line-specific slot, when the open packet's `line_id` is `hot_follow`.
**Line**: `hot_follow`
**Backed by**: `line_specific_refs[ref_id=hot_follow_subtitle_authority]` and `line_specific_refs[ref_id=hot_follow_dub_compose_legality]`.

> Symmetric with [Matrix Script Variation Panel](panel_matrix_script_variation_lowfi_v1.md) and [Digital Anchor Role/Speaker Panel](panel_digital_anchor_role_speaker_lowfi_v1.md). Hot Follow's per-line panel exists not to add buttons but to *explain* — it surfaces which subtitle artifact is currently authoritative, whether the current dub-compose attempt is legal, and what helper-derived state means.

## Page Goal

Render the Hot Follow line's authority and legality state inside the unified Workbench line-specific slot. The panel is read-mostly: it explains current truth from L2 + L3, never authors it.

## Low-fi layout

```
┌─ HOT FOLLOW · LINE PANEL ────────────────────────────────────────┐
│                                                                   │
│  SUBTITLE AUTHORITY                                                │
│  ──────────────────                                                │
│  Current authoritative source: subtitle_v3_helper_translated       │
│  Origin: helper-translation (source: subtitle_v2_asr)              │
│  Last verified: 2026-04-30T11:14Z                                  │
│  [ open artifact ]                                                 │
│                                                                    │
│  CURRENT SUBTITLE SOURCE (read-only projection)                    │
│  ──────────────────────────                                        │
│   · subtitle_v1_raw          (artifact present)                    │
│   · subtitle_v2_asr          (artifact present)                    │
│   · subtitle_v3_helper       ●  current_subtitle_source            │
│                                                                    │
│  CURRENT DUB / COMPOSE LEGALITY                                    │
│  ──────────────────────────────                                    │
│  dub_current:        ✓                                             │
│  compose_status:     ready                                         │
│  requires_redub:     false                                         │
│  requires_recompose: false                                         │
│  advisory: —                                                       │
│                                                                    │
│  HELPER STATE EXPLANATION                                          │
│  ────────────────────────                                          │
│  Helper-translation produced the current authoritative subtitle.   │
│  This does not change L2 facts — it explains why L3 marks          │
│  dub_current = true after the helper run.                          │
│                                                                    │
│  Historical successful delivery: final_v2 (2026-04-22)             │
│  Current attempt: a07_2026-04-30                                   │
│  These are intentionally separate — the panel never collapses      │
│  history into the current attempt.                                 │
└────────────────────────────────────────────────────────────────────┘
```

## Region semantics

| Region | Source | Authoring? |
|---|---|---|
| Subtitle authority | `line_specific_refs[ref_id=hot_follow_subtitle_authority]` resolved through `hot_follow_projection_rules` | No — projection of which artifact is currently the authoritative subtitle source. |
| Current subtitle source list | L2 artifact facts (subtitle artifacts present) + L3 `current_attempt.current_subtitle_source` | No — L3 marks which one is current; the panel shows the marker. |
| Dub / compose legality | L3 `current_attempt.{dub_current, compose_status, requires_redub, requires_recompose, advisory}` | No — read-only chips. |
| Helper state explanation | static + projection of helper run on L3 attempt | No — explanatory text only, no operator action. |
| Historical vs current | L2 facts (history) + L3 (current attempt) | No — separate rows, never collapsed. |

## Forbidden in this panel

- No vendor / model / provider / engine selectors (no helper-engine, no ASR-vendor, no TTS-vendor controls).
- No "regenerate subtitle" button — re-run affordances belong to the Workbench generic capability spine when L3 marks the attempt stale.
- No editing of subtitle text — Hot Follow front-end's value is *explaining* truth, not authoring it.
- No L4 advisory text overriding L2/L3 facts (red line from `Operator_Visible_Surfaces_v1.md` §7).

## Contract Mapping

| UI element | Contract / source |
|---|---|
| Subtitle authority block | `line_specific_refs[ref_id=hot_follow_subtitle_authority]` resolved via `hot_follow_projection_rules` |
| Current subtitle source marker | L3 `current_attempt.current_subtitle_source` |
| Subtitle artifact rows | L2 artifact facts (subtitle presence list) |
| Dub / compose legality chips | L3 `current_attempt.{dub_current, compose_status, requires_redub, requires_recompose}` |
| Advisory line | L3 `current_attempt.advisory` |
| Historical delivery row | L2 `final` artifact history |
| Current attempt id | L3 `current_attempt.id` |
| Slot mount key | `line_specific_refs[ref_id ∈ {hot_follow_subtitle_authority, hot_follow_dub_compose_legality}]` |

## Notes / Known Deferrals

- **Re-run / regenerate affordances**: deferred. When exposed, they live in the Workbench generic spine, not in this panel.
- **Comparison view** (current attempt vs. historical successful delivery side-by-side): deferred — current design surfaces both as separate rows but does not provide a diff view.
- **Helper provenance graph**: deferred. Current panel notes "subtitle_v2_asr → subtitle_v3_helper" in plain text; a fuller provenance UI is out of scope this round.
- **Subtitle authority override**: not provided. Authority is owned by the line factory's projection rule, not by an operator toggle.
