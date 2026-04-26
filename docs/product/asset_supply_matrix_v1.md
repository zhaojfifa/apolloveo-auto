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

## Supply truth vs donor decoupling boundary

This section is normative for both production lines. It declares the boundary that separates **supply truth** (owned by this matrix and the line packets) from **donor** (SwiftCraft) absorption (owned by runtime). The two sides MUST NOT reach into each other.

### What is supply truth

For each line, supply truth comprises:

- the operator-supplied input asset kinds declared in this matrix (per-line `required` / `optional` / `not applicable` discipline)
- the line-produced deliverable kinds declared in this matrix
- the line-specific contract objects that extend generic refs (`matrix_script_variation_matrix`, `matrix_script_slot_pack`, `digital_anchor_role_pack`, `digital_anchor_speaker_plan`)
- the closed kind-sets declared inside those line-specific contracts (axis kinds, slot kinds, framing kinds, appearance-ref kinds, dub kinds, lip-sync kinds)

Supply truth answers: *what kinds of assets exist, who supplies them, who emits them, and what closed sets describe their shape.*

### What is donor

Donor refers to the SwiftCraft absorption surface — runtime modules that realize capability kinds via concrete vendors, models, providers, or engines. Donor concerns include:

- vendor / model / provider / engine selection for any capability kind
- runtime adapter, client, or absorption-module identity
- runtime-level retry, fallback, or quota logic
- vendor-pinned credentials, endpoints, or rate envelopes

Donor answers: *which concrete realization performs a given capability kind at runtime.*

### Decoupling rules (normative)

For both `matrix_script` and `digital_anchor`:

1. **Supply truth MUST NOT name a donor.** No vendor / model / provider / engine identifier appears in this matrix, in either line packet, or in any line-specific contract object. (Validator rule R3.)
2. **Donor MUST NOT redeclare supply truth.** Runtime donor modules consume supply truth as a read-only input; they MUST NOT add, remove, or reshape kinds from the closed kind-sets declared on the supply side.
3. **Closed kind-sets are owned by supply.** Adding a kind to `axis_kind_set`, `slot_kind_set`, `framing_kind_set`, `appearance_ref_kind_set`, `dub_kind_set`, or `lip_sync_kind_set` requires a packet re-version on the supply side; donor cannot extend a closed set by absorbing a new vendor.
4. **Capability `mode` is descriptive, not selective.** The `mode` value on a capability-plan entry (e.g. `analyze`, `matrix`, `author`, `tts`, `role_render`, `segment_speak`, `sync`, `bundle`) is a supply-side hint about *what kind of work* is required; it MUST NOT be interpreted by donor as a vendor selector. Vendor selection is the sole responsibility of `capability_routing_policy_v1` at runtime.
5. **Asset references are opaque across the boundary.** Supply-side `body_ref`, `script_ref`, `appearance_ref`, and similar fields are opaque content / catalog handles. Donor MAY resolve them through their respective storage / catalog systems but MUST NOT push vendor-shaped state back into the packet.
6. **No truth round-trip from donor to supply.** Donor MUST NOT write `status`, `ready`, `done`, `delivery_ready`, or any state-shape field back onto supply objects. (Validator rule R5.)
7. **Frontend MUST NOT cross the boundary.** Surfaces consume supply truth only; `vendor_id`, `model_id`, `donor_*`, `provider`, and `engine` MUST NOT be exposed to the operator under any circumstance.

### Per-line application

| boundary item                   | matrix_script                                   | digital_anchor                                          |
| ------------------------------- | ----------------------------------------------- | ------------------------------------------------------- |
| supply-owned kind-sets          | `axis_kind_set`, `slot_kind_set`                | `framing_kind_set`, `appearance_ref_kind_set`, `dub_kind_set`, `lip_sync_kind_set` |
| supply-owned references         | `body_ref`, `script_slot_ref`, `binds_cell_id`  | `appearance_ref`, `script_ref`, `binds_role_id`         |
| supply-owned capability kinds   | `understanding`, `variation`, `subtitles`, `dub` (opt.), `pack` (opt.) | `understanding`, `avatar`, `speaker`, `subtitles`, `dub`, `lip_sync` (opt.), `pack` (opt.) |
| donor-owned at runtime          | TTS vendor (when `dub` runs), scene-pack engine (when `pack` runs) | avatar render engine, TTS vendor, lip-sync engine       |
| boundary direction              | supply → donor (read-only)                      | supply → donor (read-only)                              |

This decoupling lets the supply side freeze for P2 entry independent of any donor onboarding, and lets donor evolve (vendor swaps, new absorption modules) without re-versioning supply packets.

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
