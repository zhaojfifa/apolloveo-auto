# Digital Anchor `/tasks/digital-anchor/new` Route Contract v1

Date: 2026-05-02
Status: Plan B contract freeze (Operator-Visible Surface Validation Wave / Operations Upgrade Alignment). Contract-only; **no route implementation in this wave**.
Authority:
- `docs/reviews/operations_upgrade_gap_review_and_ops_plan_v1.md` §13 Plan B
- `docs/architecture/ApolloVeo_2.0_Operator_Visible_Surface_Validation_Wave_指挥单_v1.md`
- `docs/contracts/digital_anchor/task_entry_contract_v1.md`
- `docs/contracts/digital_anchor/create_entry_payload_builder_contract_v1.md` (sibling Plan B contract)
- Mirror reference: `docs/execution/evidence/matrix_script_formal_create_entry_alignment_v1.md` (Matrix Script analogue)

## Purpose

Pin the formal `/tasks/digital-anchor/new` operator-entry route as the **single canonical create surface** for Digital Anchor tasks, mirroring the Matrix Script alignment that landed in commit `4896f7c`. This contract freezes:

1. the canonical route paths (GET render, POST create);
2. the closed request shape (delegated to the Plan B builder contract);
3. the closed response shape (read-only confirmation of the seeded packet);
4. the deprecation of the generic temp `/tasks/connect/digital_anchor/new` path once the formal route lands;
5. the surface fences that protect Phases B/C/D from leaking into entry.

This contract does **not** authorize implementation. Implementation is gated behind Plan E acceptance per the gap review §13.

## Ownership

- Owner: contract layer (Plan B).
- Future runtime consumer: `gateway/app/routers/tasks.py` (Plan E gate).
- Non-owners: workbench presenters, delivery surfaces, frontend platform, donor modules.

## Route map

| Surface                                  | Route                                |
| ---------------------------------------- | ------------------------------------ |
| New Tasks Digital Anchor card link       | `/tasks/digital-anchor/new`          |
| Digital Anchor create-entry GET          | `/tasks/digital-anchor/new`          |
| Digital Anchor create-entry POST         | `/tasks/digital-anchor/new`          |
| Workbench after create                   | `/tasks/{task_id}`                   |
| Delivery after task exists               | `/tasks/{task_id}/publish`           |
| Generic temp create path (to be removed) | `/tasks/connect/digital_anchor/new`  |

The generic temp path is **discovery-only** today (gap review §6 classification). Once this route lands and the Plan B builder is in place, the temp path MUST be removed from `_TEMP_CONNECTED_LINES` (mirroring Matrix Script removal in commit `4896f7c`). The contract-level removal is declared here; the code change is gated behind Plan E.

## GET request / response

GET `/tasks/digital-anchor/new` renders the create-entry surface. The rendered surface MUST collect **exactly** the closed entry field set defined in [docs/contracts/digital_anchor/task_entry_contract_v1.md](task_entry_contract_v1.md) §"Entry field set" — required: `topic`, `source_script_ref`, `language_scope`, `role_profile_ref`, `role_framing_hint`, `output_intent`, `speaker_segment_count_hint`; optional: `dub_kind_hint`, `lip_sync_kind_hint`, `scene_binding_hint`, `operator_notes`.

The rendered surface MUST NOT expose:

- any `vendor_id`, `model_id`, `provider_id`, `engine_id`, avatar-engine / TTS-provider / lip-sync-engine identifier;
- any state-shape field (`status`, `ready`, `done`, `phase`, `current_attempt`, `delivery_ready`, `final_ready`, `publishable`);
- any donor (SwiftCraft) module identifier;
- Phase B authoring fields (`roles[]` enumeration, `segments[]` enumeration, `binds_role_id`);
- Phase C delivery binding fields;
- Phase D publish-feedback fields;
- Matrix Script or Hot Follow concerns.

## POST request / response

POST `/tasks/digital-anchor/new` accepts the closed entry field set above as a form/JSON payload and delegates payload construction to the Plan B builder contract [docs/contracts/digital_anchor/create_entry_payload_builder_contract_v1.md](create_entry_payload_builder_contract_v1.md).

### Request shape

Closed; identical to the builder's input shape. Unknown fields MUST be rejected with HTTP 400.

### Response shape

On accept (HTTP 303 See Other to `/tasks/{task_id}`):

- response carries no body beyond standard redirect headers;
- the new task row carries the builder's payload verbatim (see builder contract §"Outputs (closed)").

On reject (HTTP 400):

- response carries `{ "detail": "<field> is required" | "<field> is not supported" }` for missing required fields, unknown fields, or values outside closed enums (e.g. `target_language` outside the language_scope contract; `framing_kind_hint` outside `framing_kind_set`).
- response MUST NOT carry vendor / model / provider information in any error message.

## Forbidden in route surface

- Any provider/model/vendor/engine selector exposed via querystring, form field, or header.
- Any workbench mutation field — workbench surfaces remain read-only behind the workbench panel dispatch contract (Plan D).
- Any state field on the response payload.
- Any second source of task truth (writing to L3/L4 from this route is forbidden).
- Any cross-line side effect (no Matrix Script, Hot Follow, W2.2/W2.3 mutation).
- Any donor namespace import.

## Acceptance

This contract is green when:

1. Both GET and POST surfaces accept exactly the closed entry field set.
2. POST delegates payload construction to the Plan B builder contract verbatim.
3. The generic temp path `/tasks/connect/digital_anchor/new` is declared deprecated (code removal gated to Plan E).
4. No forbidden field appears anywhere on the surface.
5. The route never mutates packet or task state outside the builder's seed payload.

## What this contract does NOT do

- Does not implement the route in this wave (Plan E only).
- Does not redefine the entry field set.
- Does not author Phase B / C / D surfaces.
- Does not touch Matrix Script, Hot Follow, W2.2 / W2.3.
- Does not unblock Platform Runtime Assembly, Capability Expansion, or frontend patching.

## References

- `docs/contracts/digital_anchor/task_entry_contract_v1.md`
- `docs/contracts/digital_anchor/create_entry_payload_builder_contract_v1.md`
- `docs/execution/evidence/matrix_script_formal_create_entry_alignment_v1.md`
- `docs/reviews/operations_upgrade_gap_review_and_ops_plan_v1.md`
