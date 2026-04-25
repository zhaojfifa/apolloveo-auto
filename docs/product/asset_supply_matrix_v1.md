# Asset Supply Matrix v1

Date: 2026-04-26
Status: Frozen for P2 entry review (product handoff; consumed by surface design + packet validator)
Authority: ApolloVeo 2.0 Overall Master Plan v1.1 Part I Q5 / Part III P2; Multi-role Execution Command v1 §4.A
Owner: Product
Non-owners: routers, workbench presenters, delivery surfaces, donor (SwiftCraft) modules, frontend

## Purpose

Declare, per production line, **what assets the operator must supply** and **what assets the line itself produces** — at the level of *kinds*, never at the level of vendor, model, engine, or runtime.

This document binds the two new line packets (Matrix Script, Digital Anchor) to their input expectations and deliverable expectations, so:

- the design surface can render asset-collection slots without inventing fields
- the packet validator can cross-check `factory_input` and `factory_delivery` references
- the onboarding gate can confirm that operator-supply assumptions match line capability declarations

This document is **not** a runtime spec, **not** a vendor catalog, and **not** a state-truth source.

## Scope

Three lines are in scope:

- `hot_follow` — reference line (frozen baseline; included for parity)
- `matrix_script` — new line being onboarded
- `digital_anchor` — new line being onboarded

For each line, the matrix declares:

1. operator-supplied input asset kinds (what the user must provide)
2. line-produced deliverable kinds (what the line emits)
3. authority binding (which generic contract owns the kind)
4. supply discipline (required / optional / non-blocking)

## Closed kind sets

The matrix uses two closed kind sets. Adding a kind requires a document re-version.

### Input asset kinds (operator-supplied)

- `source_video` — primary source video reference
- `source_audio` — primary source audio reference (when separated from video)
- `source_script` — text source for variation / anchor speaker
- `source_subtitle` — pre-existing subtitle file (when authoritative source of truth)
- `language_scope_decl` — declared source/target language scope
- `role_appearance_ref` — operator-chosen anchor role catalog reference
- `variation_axes_decl` — operator-chosen variation axes + values
- `business_metadata` — operator-supplied tagging / campaign metadata

### Deliverable kinds (line-produced)

- `final_video` — primary delivery video
- `subtitle_pack` — authoritative subtitle bundle (per `factory_language_plan`)
- `dub_pack` — voice realization bundle
- `script_variation_pack` — derivative scripts produced by Matrix Script
- `anchor_render_pack` — anchor role renders produced by Digital Anchor
- `scene_pack` — optional scene-pack derivatives (non-blocking; per `factory_scene_plan`)

## Matrix · operator-supplied input assets

| input kind             | hot_follow         | matrix_script      | digital_anchor     | authority (generic contract)               |
| ---------------------- | ------------------ | ------------------ | ------------------ | ------------------------------------------ |
| `source_video`         | required           | optional           | optional           | `factory_input_contract_v1`                |
| `source_audio`         | optional           | optional           | optional           | `factory_input_contract_v1`                |
| `source_script`        | optional           | required           | required           | `factory_input_contract_v1`                |
| `source_subtitle`      | optional           | optional           | optional           | `factory_input_contract_v1` + `factory_language_plan_contract_v1` |
| `language_scope_decl`  | required           | required           | required           | `factory_language_plan_contract_v1`        |
| `role_appearance_ref`  | not applicable     | not applicable     | required           | `factory_input_contract_v1` (line delta in `digital_anchor_role_pack`) |
| `variation_axes_decl`  | not applicable     | required           | not applicable     | `factory_input_contract_v1` (line delta in `matrix_script_variation_matrix`) |
| `business_metadata`    | optional           | optional           | optional           | `factory_input_contract_v1`                |

Discipline notes:

- `required` — onboarding gate blocks if absent at packet-supply time
- `optional` — line can run without it; downstream behavior may be reduced
- `not applicable` — the kind is structurally meaningless for this line; surface MUST NOT collect it
- Operator-supplied assets are referenced by opaque ids only; the matrix does not embed file payloads

## Matrix · line-produced deliverables

| deliverable kind         | hot_follow         | matrix_script      | digital_anchor     | authority (generic contract)               |
| ------------------------ | ------------------ | ------------------ | ------------------ | ------------------------------------------ |
| `final_video`            | required           | required           | required           | `factory_delivery_contract_v1`             |
| `subtitle_pack`          | required           | required           | required           | `factory_language_plan_contract_v1` + `factory_delivery_contract_v1` |
| `dub_pack`               | optional           | optional           | required           | `factory_audio_plan_contract_v1` + `factory_delivery_contract_v1` |
| `script_variation_pack`  | not applicable     | required           | not applicable     | `factory_content_structure_contract_v1` (line delta in `matrix_script_slot_pack`) |
| `anchor_render_pack`     | not applicable     | not applicable     | required           | `factory_scene_plan_contract_v1` (line delta in `digital_anchor_speaker_plan`) |
| `scene_pack`             | optional (non-blocking) | optional (non-blocking) | optional (non-blocking) | `factory_scene_plan_contract_v1`           |

Discipline notes:

- `required` — line cannot reach `ready` packet state if the deliverable kind is not declared in `factory_delivery` references
- `optional` — line MAY emit it; absence does not block readiness
- `not applicable` — surface MUST NOT render the deliverable slot for this line
- `scene_pack` is non-blocking by `factory_scene_plan_contract_v1` rule (absence MUST NOT demote a line whose final delivery does not require scene packs)

## Cross-checks

The packet validator MUST be able to confirm, for each line's packet:

1. Every `required` input kind in the operator-supplied matrix is reachable through `generic_refs` (typically `factory_input` + line-specific extensions via `binds_to`)
2. Every `required` deliverable kind in the line-produced matrix is reachable through `generic_refs` (typically `factory_delivery` + relevant generic contracts)
3. No `not applicable` kind appears in the packet's line-specific objects (validator R2 catches structural duplication; this matrix catches surface-level inclusion)
4. No vendor / model / provider name appears anywhere (validator R3)
5. No truth-shape state field is attached to any kind (validator R5)

## Forbidden in this matrix

- Any vendor / model / provider / engine name (R3)
- Any `status` / `ready` / `done` / `delivery_ready` field attached to any kind (R5)
- Any donor (SwiftCraft) module path or module-level reference
- Any frontend exposure of `vendor_id`, `model_id`, or `donor_*` concept (consumed by surface design as guardrail)
- Any second source of task / state truth

## Surface implications (handoff to design)

For Phase B (Surface Freeze), design MUST:

- render asset-collection slots only for kinds marked `required` or `optional` for the active line
- hide kinds marked `not applicable` for the active line (no greyed-out vendor selectors)
- never expose `donor`, `supply`, `vendor`, `model`, or `provider` to the operator
- treat `scene_pack` as non-blocking — its absence MUST NOT block forward progression in the workbench

## References

- `docs/contracts/factory_packet_envelope_contract_v1.md`
- `docs/contracts/factory_packet_validator_rules_v1.md`
- `docs/contracts/factory_input_contract_v1.md`
- `docs/contracts/factory_content_structure_contract_v1.md`
- `docs/contracts/factory_scene_plan_contract_v1.md`
- `docs/contracts/factory_audio_plan_contract_v1.md`
- `docs/contracts/factory_language_plan_contract_v1.md`
- `docs/contracts/factory_delivery_contract_v1.md`
- `docs/contracts/matrix_script/packet_v1.md`
- `docs/contracts/digital_anchor/packet_v1.md`
- `docs/execution/ApolloVeo_2.0_多角色实施指挥单_v1.md` §4.A
