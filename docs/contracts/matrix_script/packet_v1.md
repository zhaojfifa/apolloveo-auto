# Matrix Script Line Packet v1

Date: 2026-04-26
Status: Frozen for P2 entry review (product packet freeze, awaiting validator + onboarding gate evidence)
Authority: ApolloVeo 2.0 Overall Master Plan v1.1 Part I Q5 / Part III P2; conforms to `docs/contracts/factory_packet_envelope_contract_v1.md`; bound by `docs/contracts/factory_packet_validator_rules_v1.md`

## Purpose

Declare the **truth interface** of the Matrix Script production line as a packet, so the factory packet validator and onboarding gate can admit it without any runtime, donor, or vendor knowledge.

This packet describes:

- which factory-generic contracts the line consumes
- which line-specific objects the line adds (variation matrix, script slot pack)
- which capability kinds the line declares (closed kinds only; no vendors)
- which reference evidence backs onboarding readiness (Hot Follow green baseline)

This packet does NOT describe runtime behavior, donor absorption, provider clients, or any second source of task / state truth.

## Ownership

- Packet owner: product (line packet author)
- Runtime consumers: packet validator, onboarding gate, line registration
- Non-owners: routers, workbench presenters, delivery surfaces, donor (SwiftCraft) modules, frontend

## Line identity

- `line_id`: `matrix_script`
- `packet_version`: `v1`
- Reference line for evidence: `hot_follow`

## Generic contract references

The Matrix Script line consumes the six factory-generic contracts unmodified. Each ref is reachable via the envelope's `generic_refs[]`:

| ref_id     | path                                                        | version |
| ---------- | ----------------------------------------------------------- | ------- |
| `g_input`  | `docs/contracts/factory_input_contract_v1.md`               | v1      |
| `g_struct` | `docs/contracts/factory_content_structure_contract_v1.md`   | v1      |
| `g_scene`  | `docs/contracts/factory_scene_plan_contract_v1.md`          | v1      |
| `g_audio`  | `docs/contracts/factory_audio_plan_contract_v1.md`          | v1      |
| `g_lang`   | `docs/contracts/factory_language_plan_contract_v1.md`       | v1      |
| `g_deliv`  | `docs/contracts/factory_delivery_contract_v1.md`            | v1      |

The Matrix Script line MUST NOT redeclare any field shape owned by these generic contracts (validator rule R2).

## Line-specific objects

Two line-specific contracts extend the generic refs via `binds_to`. Each declares ONLY delta fields. Neither may carry truth-shape state fields (validator rule R5) nor vendor pins (validator rule R3).

### LS1 · `matrix_script_variation_matrix`

Binds to: `g_input`, `g_struct`

Purpose: declare the variation grid that turns one source script into a matrix of derivative scripts. The matrix is a planning artifact; runtime variation execution is not described here.

Delta fields:

- `axes[]` — ordered list of variation axes; each entry declares:
  - `axis_id` — stable id (e.g. `tone`, `audience`, `length`, `cta_style`)
  - `kind` — `categorical` | `range` | `enum`
  - `values[]` — declared value tokens (categorical/enum) or `min`/`max`/`step` (range)
  - `is_required` — boolean; required axes must have at least one selected value per cell
- `cells[]` — declared variation cells; each entry declares:
  - `cell_id` — stable id within this packet
  - `axis_selections{}` — map from `axis_id` to a value token (or range pick) drawn from the axis declaration
  - `script_slot_ref` — id of a `matrix_script_slot_pack.slots[]` entry that owns the script body for this cell
  - `notes` — non-truth descriptive string (optional)
- `axis_kind_set` — closed set: `{categorical, range, enum}`; additions require packet re-version

Forbidden in LS1:

- any `status` / `ready` / `done` / `phase` field (R5)
- any `vendor_id` / `model_id` / `provider` field (R3)
- any embed of the full `factory_input` or `factory_content_structure` record shape (R2)

### LS2 · `matrix_script_slot_pack`

Binds to: `g_struct`, `g_lang`

Purpose: declare the script slot pack that holds the actual derivative script bodies, language scope per slot, and the binding to the variation matrix cell that consumes the slot.

Delta fields:

- `slots[]` — ordered list of script slots; each entry declares:
  - `slot_id` — stable id within this packet
  - `binds_cell_id` — id of the `matrix_script_variation_matrix.cells[]` entry that owns this slot
  - `language_scope` — `{source_language, target_language[]}` drawn from `g_lang` allowed values; helper-translation policy follows `g_lang`
  - `body_ref` — opaque content reference (e.g. content storage key); the packet does not embed body text
  - `length_hint` — non-truth integer/range hint for downstream planners
- `slot_kind_set` — closed set: `{primary, alternate, fallback}`; additions require packet re-version

Forbidden in LS2:

- any subtitle `authority` override that contradicts `g_lang`'s single-owner rule
- any `delivery_ready` / `publishable` / `final_ready` field (R5)
- any vendor pin (R3)

## Capability plan (kinds only)

Capability kinds declared by Matrix Script, drawn from the closed kind set in validator rule R3. Vendor selection is performed by `capability_routing_policy_v1` at runtime; the packet MUST NOT pin any vendor, model, provider, or engine.

| kind          | required | mode     | notes                                               |
| ------------- | -------- | -------- | --------------------------------------------------- |
| `understanding` | yes    | analyze  | derive structural understanding of source script    |
| `variation`     | yes    | matrix   | produce derivative scripts per cell selection       |
| `subtitles`     | yes    | author   | authoritative subtitle ownership per `g_lang`       |
| `dub`           | optional | tts     | optional voice realization for delivery preview     |
| `pack`          | optional | bundle  | optional scene-pack derivative (non-blocking)       |

`mode` values are descriptive hints, not provider selectors.

## Binding profiles

Declared at envelope level in `binding`:

- `worker_profile_ref`: `worker_profile_matrix_script_v1` (resolved by worker gateway; not embedded here)
- `deliverable_profile_ref`: `deliverable_profile_matrix_script_v1`
- `asset_sink_profile_ref`: `asset_sink_profile_matrix_script_v1`

These are referenced by id only. Their declarations live outside this packet (worker gateway / delivery contracts).

## Evidence

Onboarding evidence object declared at envelope level in `evidence`:

- `reference_line`: `hot_follow`
- `reference_evidence_path`: `docs/contracts/hot_follow_line_contract.md`
- `validator_report_path`: `docs/execution/logs/packet_validator_matrix_script_v1.json` (written by validator on first run; absent before first validation)
- `ready_state`: `draft` (transitions per envelope E4)

`ready_state` is the only readiness field permitted in this packet (envelope E4 / validator R5).

## Forbidden in this packet

Cross-cutting prohibitions inherited from the envelope and validator rules; restated here for product clarity:

- vendor / model / provider / engine names (R3)
- truth-shape state fields: `status`, `ready`, `done`, `phase`, `current_attempt`, `delivery_ready`, etc. (R5)
- direct embed of any generic contract's full record shape inside line-specific objects (R2)
- references to donor (SwiftCraft) module paths (envelope §Forbidden)
- any second source of task / state truth

## Lifecycle

Per envelope E4:

```
draft  →  validating  →  ready  →  frozen
                    ↘
                      gated  (validator failures or onboarding gate blocked)
```

The packet author submits `draft`; the validator promotes through `validating`; the onboarding gate emits `passed`/`blocked`/`pending`; only `passed` packets at `ready_state = ready` are eligible for runtime onboarding (P3).

## Schema and samples

- Schema: `schemas/packets/matrix_script/packet.schema.json` (Draft 2020-12)
- Samples: `schemas/packets/matrix_script/sample/*.json`
- `$id`: `apolloveo://packets/matrix_script/v1`

## References

- `docs/contracts/factory_packet_envelope_contract_v1.md`
- `docs/contracts/factory_packet_validator_rules_v1.md`
- `docs/contracts/factory_input_contract_v1.md`
- `docs/contracts/factory_content_structure_contract_v1.md`
- `docs/contracts/factory_scene_plan_contract_v1.md`
- `docs/contracts/factory_audio_plan_contract_v1.md`
- `docs/contracts/factory_language_plan_contract_v1.md`
- `docs/contracts/factory_delivery_contract_v1.md`
- `docs/product/asset_supply_matrix_v1.md`
