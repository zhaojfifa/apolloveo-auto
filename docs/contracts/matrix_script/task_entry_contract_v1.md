# Matrix Script Task Entry Contract v1

Date: 2026-04-27
Status: Phase A landing (Matrix Script First Production Line Wave — `docs/architecture/ApolloVeo_2.0_Matrix_Script_First_Production_Line_Wave_指挥单_v1.md` §6 Phase A)
Authority:
- `docs/architecture/ApolloVeo_2.0_Matrix_Script_First_Production_Line_Wave_指挥单_v1.md` §3, §4, §6 Phase A, §7
- `docs/contracts/matrix_script/packet_v1.md`
- `schemas/packets/matrix_script/packet.schema.json`
- `docs/contracts/factory_input_contract_v1.md`
- `docs/contracts/factory_language_plan_contract_v1.md`
- `docs/product/asset_supply_matrix_v1.md` (matrix_script row)
- `docs/design/surface_task_area_lowfi_v1.md`

## Purpose

Declare the **operator-facing entry surface** by which a Matrix Script task is initiated, and the **mapping rule** by which that entry projects onto the frozen Matrix Script packet truth (`schemas/packets/matrix_script/packet.schema.json` + `docs/contracts/matrix_script/packet_v1.md`).

This contract is the Phase A deliverable of the Matrix Script First Production Line Wave. It does not author packet truth; it declares which operator inputs are accepted at task creation, and which packet fields each input is allowed to seed.

## Ownership

- Owner: product (entry-surface author) + design (surface mapping)
- Runtime consumers: future task-creation path (Phase B+), packet validator (rejects vendor pins / state fields regardless of entry origin)
- Non-owners: routers, workbench presenters, delivery surfaces, donor (SwiftCraft) modules, provider adapters, frontend platform

## Scope discipline (normative)

This contract:
1. defines the **closed set** of fields the Matrix Script task entry MAY accept;
2. classifies each field as **line truth** (projects onto a packet field) or **operator hint** (seeds a packet authoring step but is itself non-truth);
3. classifies each field as **required**, **optional**, or **deferred**;
4. names what entry-time inputs are explicitly **forbidden** (provider/model selection, status-shape fields, donor-side concepts);
5. names what is **deferred** to Phase B (Workbench Variation Surface), Phase C (Delivery Binding), Phase D (Publish Feedback Closure).

This contract does NOT:
- define runtime task creation behavior;
- redeclare packet truth;
- introduce a second source of state or task truth;
- name vendors / models / providers / engines (validator rule R3);
- attach truth-shape state fields (`status`, `ready`, `done`, `phase`, `current_attempt`, `delivery_ready`, `final_ready`, `publishable`) to any entry field (validator rule R5);
- re-version the Matrix Script packet, schema, or sample.

## Entry field set (closed)

The Matrix Script task entry accepts exactly the fields below. The set is closed at v1; additions require a re-version of this contract.

| entry field         | discipline | classification     | line truth? | seeds (packet path)                                                         | authority (generic contract)                                       |
| ------------------- | ---------- | ------------------ | ----------- | --------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| `topic`             | required   | operator hint      | no          | `metadata.notes` (free-form trail) + downstream Phase B authoring seed       | `factory_input_contract_v1` (operator metadata envelope)           |
| `source_script_ref` | required   | line truth (asset) | yes (opaque ref) | downstream `slot_pack.delta.slots[].body_ref` (resolved by Phase B authoring; entry only carries the opaque handle) | `factory_input_contract_v1` (`source_script` per `asset_supply_matrix_v1`) |
| `language_scope`    | required   | line truth         | yes         | `slot_pack.delta.slots[].language_scope` (`source_language`, `target_language[]`) | `factory_language_plan_contract_v1` (`g_lang`)                      |
| `target_platform`   | required   | operator hint      | no          | `metadata.notes` (free-form trail); does NOT bind delivery — delivery binding is Phase C | `factory_input_contract_v1` (operator metadata envelope)           |
| `variation_target_count` | required | operator hint  | no          | seeds Phase B authoring of `variation_matrix.delta.cells[]` cardinality; does NOT itself become a packet field | `factory_input_contract_v1` (operator metadata envelope)           |
| `audience_hint`     | optional   | operator hint      | no          | seeds Phase B selection within `variation_matrix.delta.axes[axis_id="audience"].values[]` (axis values are packet truth; the hint is not) | `factory_input_contract_v1` (operator metadata envelope)           |
| `tone_hint`         | optional   | operator hint      | no          | seeds Phase B selection within `variation_matrix.delta.axes[axis_id="tone"].values[]`     | `factory_input_contract_v1` (operator metadata envelope)           |
| `length_hint`       | optional   | operator hint      | no          | seeds Phase B `slot_pack.delta.slots[].length_hint` and/or `variation_matrix.delta.axes[axis_id="length"]` range pick | `factory_input_contract_v1` (operator metadata envelope)           |
| `product_ref`       | optional   | operator hint      | no          | `metadata.notes` (free-form trail)                                            | `factory_input_contract_v1` (operator metadata envelope)           |
| `operator_notes`    | optional   | operator hint      | no          | `metadata.notes`                                                              | `factory_input_contract_v1` (operator metadata envelope)            |

Required vs optional discipline matches the `matrix_script` column of `docs/product/asset_supply_matrix_v1.md` for the `source_script` and `language_scope_decl` rows. Other entry fields are operator hints and are required only as authoring scaffolding for Phase B; they never become packet line truth.

## Line-truth vs operator-hint rule

- **Line truth** entries are the only entries that appear (after Phase B authoring) inside the packet's `line_specific_refs[].delta` blocks or generic-ref shapes. Line-truth content is owned by the packet, never by the entry surface.
- **Operator hint** entries seed Phase B authoring decisions but are themselves stored only as free-form trail in `metadata.notes` (or carried in an out-of-packet authoring scratch — to be defined in Phase B). They MUST NOT mutate any closed kind-set (`axis_kind_set`, `slot_kind_set`).
- An entry surface that promotes an operator hint into a packet truth field without going through Phase B authoring is a **violation** of this contract.

## Required vs optional (entry-time)

- Required: `topic`, `source_script_ref`, `language_scope`, `target_platform`, `variation_target_count`.
  - `source_script_ref` and `language_scope` are required by the asset supply matrix for the `matrix_script` line; absence MUST block task creation.
  - `topic`, `target_platform`, `variation_target_count` are required by this entry contract as the minimum operator-hint scaffolding so Phase B authoring has enough seed to construct a non-trivial variation matrix; absence MUST block task creation at the entry surface, but their absence is NOT a packet-truth gate (the packet validator does not see them).
- Optional: `audience_hint`, `tone_hint`, `length_hint`, `product_ref`, `operator_notes`.

## Deferred to later phases (entry surface MUST NOT collect)

The following are explicitly out of scope for Phase A entry. Any attempt to collect them at task entry is a violation of this contract.

| concern                          | deferred to                                                       |
| -------------------------------- | ----------------------------------------------------------------- |
| explicit `variation_matrix.delta.cells[]` enumeration | Phase B (Workbench Variation Surface)              |
| explicit `variation_matrix.delta.axes[]` authoring   | Phase B (Workbench Variation Surface)              |
| `slot_pack.delta.slots[]` authoring (slot_id, binds_cell_id) | Phase B (Workbench Variation Surface)      |
| `delivery` binding, manifest, deliverable selection           | Phase C (Delivery Binding)                |
| `result_packet_binding` deliverable wiring                    | Phase C (Delivery Binding)                |
| `publish_feedback` projection / variation_id-level feedback   | Phase D (Publish Feedback Closure)        |
| provider / model / vendor / engine selection                  | **never** at entry surface (validator R3) |
| status / ready / done / delivery_ready / final_ready / publishable | **never** at entry surface (validator R5) |
| donor (SwiftCraft) module identity                            | **never** at entry surface                |
| Digital Anchor, W2.2, W2.3 concerns                           | out of this wave entirely                  |

## Forbidden at entry surface

- Any field named or shaped as `vendor_id`, `model_id`, `provider`, `provider_id`, `engine_id` (validator R3).
- Any field named or shaped as `status`, `state`, `phase`, `ready`, `done`, `current_attempt`, `delivery_ready`, `final_ready`, `publishable` (validator R5; restated by packet schema `metadata.not.anyOf`).
- Any donor-side concept: `donor_*`, `swiftcraft_*`, absorption-module names.
- Any second source of task / state truth (envelope §Forbidden).
- Any cross-line concern (Hot Follow, Digital Anchor, Avatar, VideoGen).
- Any frontend exposure of `vendor_id` / `model_id` / `donor_*` per `docs/product/asset_supply_matrix_v1.md` §Decoupling rules item 7.

## Mapping note (entry → packet)

Notation: `entry.<field>  →  packet.<json-pointer-ish path>`.

```
entry.topic                    →  metadata.notes (appended; non-truth trail)
entry.source_script_ref        →  (Phase B authoring) line_specific_refs[ref_id="matrix_script_slot_pack"].delta.slots[*].body_ref
                                  (entry carries opaque handle only; resolution to slot bodies is Phase B)
entry.language_scope           →  (Phase B authoring) line_specific_refs[ref_id="matrix_script_slot_pack"].delta.slots[*].language_scope
                                  bound by g_lang allowed values
entry.target_platform          →  metadata.notes (appended; non-truth trail)
                                  (delivery target binding is Phase C)
entry.variation_target_count   →  (Phase B authoring scaffold) drives count of
                                  line_specific_refs[ref_id="matrix_script_variation_matrix"].delta.cells[]
                                  (does NOT appear as a packet field)
entry.audience_hint            →  (Phase B authoring scaffold) selection within
                                  line_specific_refs[ref_id="matrix_script_variation_matrix"].delta.axes[axis_id="audience"].values[]
entry.tone_hint                →  (Phase B authoring scaffold) selection within
                                  .delta.axes[axis_id="tone"].values[]
entry.length_hint              →  (Phase B authoring scaffold) either
                                  .delta.axes[axis_id="length"] range pick
                                  and/or slot_pack.delta.slots[*].length_hint
entry.product_ref              →  metadata.notes (appended; non-truth trail)
entry.operator_notes           →  metadata.notes (appended; non-truth trail)
```

Mapping discipline:

- Only `entry.source_script_ref` and `entry.language_scope` cross from entry surface to packet **truth** (line-specific delta). All other entries cross only to `metadata.notes` (non-truth trail) or to Phase B authoring scaffolding (out of packet entirely).
- Closed kind-sets (`axis_kind_set`, `slot_kind_set`) are NOT widened by any entry field. Hints select among existing values; they never add values.
- `binding.capability_plan[]`, `binding.worker_profile_ref`, `binding.deliverable_profile_ref`, `binding.asset_sink_profile_ref` are **NOT** populated from the entry surface. They are static for the Matrix Script line per `docs/contracts/matrix_script/packet_v1.md` §Capability plan and §Binding profiles.
- `evidence.ready_state` is **NOT** writable from the entry surface. `ready_state` is one-way projection from validator output (`docs/design/surface_task_area_lowfi_v1.md` §Gate Truth Rule).

## Source script ref shape (addendum, 2026-05-02; tightened by §8.F on 2026-05-03)

Authority: `docs/reviews/matrix_script_trial_blocker_and_realign_review_v1.md` §8.A; `docs/reviews/matrix_script_followup_blocker_review_v1.md` §6 (§8.F — Opaque Ref Discipline vs Operator Usability) Option F1.

`source_script_ref` is an opaque reference handle. The entry surface MUST reject any value that carries script body text, document prose, any publisher article URL, or any other non-reference payload. The server-side guard at `gateway/app/services/matrix_script/create_entry.py` enforces the closed shape declared here; the operator-facing input at `gateway/app/templates/matrix_script_new.html` mirrors the same shape via `pattern` / `maxlength`.

A submitted value is accepted only when it matches one of the two closed shapes below.

1. **URI with closed opaque-by-construction scheme.** Scheme prefix from the closed set followed by `://` and at least one non-whitespace character.
   - Closed scheme set: `content`, `task`, `asset`, `ref`. (No external web schemes.)
   - Example: `content://matrix-script/source/001`.
2. **Bare token id.** `^[A-Za-z0-9][A-Za-z0-9._\-:/]{3,}$`. No whitespace, no embedded scheme separator (`://`). Used for short opaque content storage handles or external system ids.
   - Example: `MS-SRC-2026-04-001`.

Independent of the shape match, the value MUST also satisfy:

- single line (no `\n` or `\r`);
- no whitespace anywhere;
- length ≤ 512 characters.

On any rejection the entry surface raises the existing entry-validation error type (HTTP 400) with a localised message that names the field and the constraint. The rejection MUST happen before `build_matrix_script_task_payload` runs, so the payload-builder never sees body text.

The closed scheme set is exhaustive at v1; widening it requires a re-version of this contract. Narrowing it is permitted only if no live trial sample relies on the removed scheme.

### Opaque-by-construction discipline (§8.F tightening, 2026-05-03)

Authority: `docs/reviews/matrix_script_followup_blocker_review_v1.md` §6 Option F1; `docs/execution/MATRIX_SCRIPT_F_OPAQUE_REF_DISCIPLINE_EXECUTION_LOG_v1.md`.

Original §8.A accepted scheme set was `{content, task, asset, ref, s3, gs, https, http}`. §8.F tightens it to `{content, task, asset, ref}` — the four schemes the product owns the dereferencing path for. The dropped schemes were:

- **`https` / `http`**: external web content. The product cannot dereference an arbitrary publisher URL to authored script content (web scraping is out of scope for this wave). The follow-up review §3 documented the live operator submitting `https://news.qq.com/rain/a/...` as a trigger case.
- **`s3` / `gs`**: object-storage buckets. While "opaque by convention" (the product would own its own bucket), the entry surface has no enforceable mechanism to distinguish a product-owned bucket from a public / arbitrary one, and the §8.C `body_ref` template never emits `s3://` / `gs://`. Removing them aligns the closed set with the only schemes the product actually mints under Plan A.

The four retained schemes are **opaque-by-construction inside the product**: the product (or a trial-wave operator-token convention, see below) is the sole authority that mints / interprets each scheme.

### Operator transitional convention (Plan A trial wave only)

Until Plan E lands an operator-facing minting / lookup service (Plan C C1, contract-frozen, gated), operators have no in-product way to obtain a `content://` / `task://` / `asset://` / `ref://` handle. For the Plan A trial wave the only supported operator-facing form is:

```
content://matrix-script/source/<token>
```

where `<token>` is operator-chosen, opaque to the product, and uniquely identifies the operator's script source within the operator's own bookkeeping. The product treats the entire ref as an opaque label: it never dereferences `<token>` to body content, never validates uniqueness across operators, and never reads back content by this handle. Operators are responsible for keeping their own mapping of `<token>` to wherever the source lives (private doc, internal page, working notes, etc.).

This convention is **transitional**:

- the convention is operator-discipline only — it is not a product feature;
- it does not back-fit a content-mint endpoint, asset-library service, or any new operator-facing service into this wave (Plan C C1 / Plan E);
- it produces refs that pass the §8.A guard's `content` scheme path and the §8.F tightened scheme set with no further changes;
- the refs are interchangeable with §8.C's deterministically-authored `body_ref` template (`content://matrix-script/{task_id}/slot/{slot_id}`) at the contract level; both forms are opaque-by-construction `content://...` URIs;
- removal path: when Plan E adds the in-product minting flow (Option F2 path), the convention is replaced by the minted handle. Operators are not asked to migrate existing handles; the convention is forward-compatible with whatever Plan E mints because the product never bound any meaning to `<token>` beyond opaqueness.

### Why this is contract-tightening AND a usability adjustment

The original §8.A addendum included `https` / `http` as a pragmatic allowance for operators who already had URLs on hand. The follow-up review §6 observed that this allowance defeats the contract intent ("opaque ref handle") because a publisher article URL is not opaque-by-construction in the product, and there is no documented dereference path for URL-shaped refs anywhere downstream. §8.F removes that pragmatic allowance and pins the operator transitional convention so the operator workflow remains usable in the Plan A trial without the contract intent slippage. Plan E (Option F2) is the proper resolution: a real operator-facing minting flow that owns the `content://` namespace.

### Out of scope for §8.F

- no in-product minting / lookup service (Plan C C1, gated to Plan E);
- no `POST /assets/mint?kind=script_source` endpoint (Plan E Option F2);
- no asset-library service expansion;
- no operator brief refresh (the §8.D operator brief still reflects the pre-§8.F scheme set; the §8.H operator brief re-correction follow-up is the natural successor that re-aligns §3.2 / §6.2 / §7.1 with the §8.F tightened scheme set);
- no `body_ref` template change (`content://matrix-script/{task_id}/slot/{slot_id}` from §8.C is unchanged and remains opaque-by-construction);
- no `g_lang` token alphabet pinning (separate review);
- no widening of the closed scheme set; future widening requires a contract re-version, not an addendum;
- no Plan E gated items (B4 `result_packet_binding` URL-shaped-ref handling, D1 / D2 / D3 / D4) implementation;
- no second production line onboarding.

### Operator-facing minting flow (Option F2 — addendum, 2026-05-04)

Authority: `docs/reviews/plan_e_matrix_script_operator_facing_gate_spec_v1.md` §3.2 / §5.2 (Plan E PR-2 / Item E.MS.2). This sub-section is **additive**; it documents the in-product minting service that lands as part of the same PR. It does **not** replace, weaken, remove, or widen any prior rule on this contract — the `_validate_source_script_ref_shape` guard, the §8.F-tightened `SOURCE_SCRIPT_REF_ACCEPTED_SCHEMES = ("content", "task", "asset", "ref")` closed scheme set, the §0.2 product-meaning of `source_script_ref` (asset identity handle, not body input, not URL ingestion, not currently dereferenced), the §8.A body-text rejection, and the operator-discipline `<token>` transitional convention all remain in force unchanged.

#### Endpoint

```
POST /tasks/matrix-script/source-script-refs/mint
```

Matrix-script-scoped JSON endpoint. No Hot Follow, no Digital Anchor, no cross-line surface is touched by this endpoint or by the service that backs it.

#### Request envelope

Empty body, OR a JSON object with one optional field:

```
{
  "requested_by": "<operator-handle-string, optional>"
}
```

- `requested_by` (optional, string): an operator-side record-keeping label only. The product does not dereference it, never returns it as packet truth, and never attaches it to the minted handle. Empty / non-string / oversize / non-printable values collapse to the empty string.

#### Response envelope

```
{
  "source_script_ref": "content://matrix-script/source/<token>",
  "token":             "<token>",
  "minted_at":         "2026-05-04T12:34:56+00:00",
  "policy":            "operator_request_v1",
  "requested_by":      "<sanitized requested_by, possibly empty>"
}
```

- `source_script_ref`: the minted opaque handle, ready to submit verbatim to `/tasks/matrix-script/new` POST as the `source_script_ref` form field. The product **guarantees** that this value passes `_validate_source_script_ref_shape` with the §8.F-tightened scheme set; any future refactor of the token shape that would break the guard is rejected by the service's internal acceptance assertion.
- `token`: the bare opaque token slug used inside the `content://matrix-script/source/` wrapper. The product owns its allocation; operators MUST treat it as opaque (no parsing, no dereferencing, no cross-task reuse semantics).
- `minted_at`: an ISO-8601 UTC timestamp recording when the handle was minted. The product does not bind any meaning to this timestamp beyond audit display; downstream consumers MUST NOT use it as packet truth.
- `policy`: a closed enum describing the minting policy in force. The starting set is `{operator_request_v1}`; future minting policies (e.g. batched provisioning, bulk import) require an additive sub-section on this contract.
- `requested_by`: the sanitized operator note from the request, possibly empty.

#### `<token>` allocation policy (`operator_request_v1`)

- The product allocates `<token>` as a hex slug derived from a UUID4 and prefixed with the literal string `mint-`. The full token shape today is `mint-<16-hex-chars>`. The prefix is a coordinator-readability convenience; the product binds **no semantic meaning** to either the prefix or the slug — both remain opaque to every downstream consumer.
- Allocation is per-request and stateless. The minting service does not persist allocations, does not perform uniqueness checks across requests, does not coordinate across operators, and does not back the handle with any catalog object inside the product. Two consecutive requests yield two distinct handles with high probability (UUID4 collision likelihood); operators MUST NOT rely on a stronger guarantee than that.
- Allocation is a pure local function. The minting service does not perform I/O, does not call workers, does not call storage providers, does not resolve provider/vendor/model identifiers, and does not mutate any packet, task, or closure store. The contract surface is identical to the prior operator-discipline `<token>` flow — the only difference is that the product chooses `<token>` instead of the operator.

#### Backward compatibility (binding)

- Handles minted under the operator-discipline `<token>` convention pinned by §8.F / §8.H and §"Operator transitional convention (Plan A trial wave only)" above remain valid. Examples that continue to be accepted by `_validate_source_script_ref_shape`: `content://matrix-script/source/op-token-001`, `content://matrix-script/source/MS-SRC-2026-05-03-001`, `content://matrix-script/source/<your-id>`. The minting flow is **opt-in**; operators may continue to pick `<token>` themselves and submit the handle directly.
- No operator migration of existing samples is required. Previously-submitted handles keep their values verbatim; nothing in this addendum back-fills, rewrites, or deprecates them.
- The other three opaque-by-construction schemes (`task://`, `asset://`, `ref://`) remain accepted; the minting service mints into `content://` only because that is the scheme operators have been using under the transitional convention. Future minting policies for the other three schemes (if needed) require an additive sub-section, not a re-version.

#### What this addendum does NOT do

- Does NOT widen `SOURCE_SCRIPT_REF_ACCEPTED_SCHEMES` (the closed four-scheme set is unchanged).
- Does NOT weaken `_validate_source_script_ref_shape` (the guard runs against the minted handle and against operator-supplied handles identically).
- Does NOT introduce body-text input handling on `source_script_ref` or any other field (§8.A rejection still HTTP 400).
- Does NOT introduce publisher-URL ingestion (§8.F rejection still HTTP 400 with `"scheme is not recognised"`).
- Does NOT introduce bucket-URI ingestion (§8.F rejection still HTTP 400).
- Does NOT introduce a Plan B B4 `result_packet_binding` URL-shaped-ref handling (Plan E PR-1 already landed B4 with sentinel discipline; this addendum does not extend B4).
- Does NOT introduce an asset-library object service, promote intent service, asset-supply page, or any other cross-line operator-surface implementation (gate spec §4.2 forbidden in this Plan E phase).
- Does NOT dereference the minted handle to body content. The product still does not currently dereference any handle (§0.2 product-meaning preserved).
- Does NOT repurpose `source_script_ref` as a body-input field, publisher-URL ingestion field, or currently dereferenced content address (§0.2 preserved).
- Does NOT change the §8.C deterministic Phase B authoring output (`body_ref = "content://matrix-script/{task_id}/slot/{slot_id}"` is unchanged; the minted `source_script_ref` is operator-facing only and is stored verbatim on the persisted task).
- Does NOT touch any Hot Follow surface, any Digital Anchor surface, or any cross-line projection / advisory / publish_readiness / panel-dispatch surface (gate spec §4.1 / §4.2 / §4.4 preserved).
- Does NOT start Platform Runtime Assembly or Capability Expansion (gate spec §7.5 preserved).

## Phase B deterministic authoring (addendum, 2026-05-03)

Authority: `docs/reviews/matrix_script_trial_blocker_and_realign_review_v1.md` §8.C (Option C1 — minimal real Phase B authoring).

The Plan A trial wave requires the Phase B workbench variation panel to render real resolvable axes / cells / slots for any fresh contract-clean Matrix Script sample. To meet that requirement without re-versioning `variation_matrix_contract_v1`, `slot_pack_contract_v1`, or `packet_v1` — and without introducing any provider / model / vendor / engine control — Phase B authoring runs **synchronously inside `build_matrix_script_task_payload`** at task-creation time. The authoring step is implemented at `gateway/app/services/matrix_script/phase_b_authoring.py::derive_phase_b_deltas(entry, task_id)`.

### Pinned axes

The authoring step always emits the three canonical axes named by the Mapping note above. Values are pinned for v1 trial reproducibility:

| `axis_id`  | `kind`        | `values`                                | `is_required` |
| ---------- | ------------- | --------------------------------------- | ------------- |
| `tone`     | `categorical` | `["formal", "casual", "playful"]`       | `true`        |
| `audience` | `enum`        | `["b2b", "b2c", "internal"]`            | `true`        |
| `length`   | `range`       | `{"min": 30, "max": 120, "step": 15}`   | `false`       |

`axis_kind_set = ["categorical", "range", "enum"]` exactly. `slot_kind_set = ["primary", "alternate", "fallback"]` exactly. Both kind sets remain the closed sets pinned by `variation_matrix_contract_v1` §"Closed sets" and `slot_pack_contract_v1` §"Closed sets" — Phase B authoring does not widen them.

### Cell ↔ slot pairing

For `i ∈ [0, entry.variation_target_count)`:

- `cell_id = "cell_{i+1:03d}"`, `slot_id = "slot_{i+1:03d}"`.
- `cells[i].script_slot_ref == slots[i].slot_id` (round-trip lower bound).
- `slots[i].binds_cell_id == cells[i].cell_id` (round-trip upper bound).
- `cells[i].axis_selections = {"tone": TONES[i % 3], "audience": AUDIENCES[(i // 3) % 3], "length": LENGTH_PICKS[i % 7]}` where `LENGTH_PICKS = [30, 45, 60, 75, 90, 105, 120]` is the closed step-aligned walk over `length` axis values. The 9 × 7 = 63 distinct tuples cover the validated `variation_target_count` range `[1, 12]` with all `axis_selections` distinct.
- `slots[i].slot_kind = "primary"` (closed-set member; default per `slot_pack_contract_v1` §"Delta fields").

### Body ref shape

`slots[i].body_ref = "content://matrix-script/{task_id}/slot/{slot_id}"` is **opaque** and derived from `task_id` and `slot_id` only. It MUST NOT embed body text, MUST NOT carry the operator-supplied `source_script_ref`, and MUST use the `content` scheme from the §"Source script ref shape (addendum, 2026-05-02)" closed scheme set. The body-text-embedding ban from `slot_pack_contract_v1` §"Forbidden" is upheld by construction.

### Determinism

`derive_phase_b_deltas(entry, task_id)` is a pure function: no clock, no randomness, no env reads, no IO. Same `(entry, task_id)` produces the same deltas. The function does not mutate `entry` (which is a frozen dataclass) and does not write into the task repository.

### Hint consumption (out of scope this addendum)

Optional entry hints (`audience_hint`, `tone_hint`, `length_hint`) are mapped to Phase B authoring scaffolds by the §"Mapping note" above, but the Plan A trial wave's deterministic seed **does not yet consume them**. Plan E real-authoring may bias the rotation by hints without re-versioning this contract.

### Removal path

This deterministic seed is the Plan A trial wave's narrow Phase B authoring capability. Plan E may replace or extend `derive_phase_b_deltas` with a richer planner; such a replacement does not require re-versioning this contract so long as the pinned axes / kind sets / pairing rule / opaque-`body_ref` invariant remain honoured.

### Out of scope

- `g_lang` token alphabet — this addendum uses whatever ISO-639 short codes the §"Entry field set" already accepts (currently `mm`, `vi`); pinning the alphabet is a separate review against `factory_language_plan_contract_v1`.
- The Phase B render surface (`workbench_variation_surface_contract_v1`) — unchanged.
- Phase C delivery binding and Phase D publish-feedback closure — unchanged.
- Provider / model / vendor / engine selection — forbidden at all phases (validator R3).

## Acceptance (Phase A)

Phase A is green only when:

1. The entry field set above is the exact closed set used by any Matrix Script task-creation surface.
2. Every required entry field is collected; absence blocks task creation at entry.
3. No forbidden field is collected, displayed, or stored at entry.
4. Every line-truth entry maps onto a packet path that is reachable from the existing Matrix Script schema/contract; no new packet field is invented.
5. Every operator-hint entry maps either to `metadata.notes` or to Phase B authoring scaffolding; none is promoted to packet truth at entry time.
6. Implementation, if any, is Matrix-Script-only; no code path under `digital_anchor`, no provider/adapter touch, no Hot Follow business-logic change.

## What Phase A intentionally does NOT add

- No workbench variation authoring surface (Phase B).
- No delivery center binding (Phase C).
- No publish feedback projection (Phase D).
- No provider/model selection control (forbidden at all phases).
- No new packet schema / sample / contract version.
- No Digital Anchor entry (out of this wave).
- No Hot Follow change.
- No frontend platform rebuild.
- No runtime task-creation implementation in this Phase A landing — this contract is the surface-first definition; engineering implementation is sequenced separately and bounded by this contract.

## Remaining blockers before Phase B

1. Phase B requires this Phase A entry contract to be reviewed and accepted as the authority for the operator-supplied seed feeding workbench authoring.
2. Phase B requires the workbench authoring surface to consume the `entry.*` seed without re-authoring it — i.e. the workbench MUST start from this entry's projection into `metadata.notes` and Phase B authoring scaffolding, not from a freshly invented form.
3. Phase B requires `axis_kind_set` and `slot_kind_set` to remain frozen as declared in `docs/contracts/matrix_script/packet_v1.md` §LS1 / §LS2; this Phase A contract relies on that freeze to keep `audience_hint` / `tone_hint` / `length_hint` mapping stable.

## References

- `docs/architecture/ApolloVeo_2.0_Matrix_Script_First_Production_Line_Wave_指挥单_v1.md`
- `docs/contracts/matrix_script/packet_v1.md`
- `docs/contracts/matrix_script/variation_matrix_contract_v1.md`
- `docs/contracts/matrix_script/slot_pack_contract_v1.md`
- `schemas/packets/matrix_script/packet.schema.json`
- `schemas/packets/matrix_script/sample/matrix_script_packet_v1.sample.json`
- `docs/contracts/factory_input_contract_v1.md`
- `docs/contracts/factory_language_plan_contract_v1.md`
- `docs/contracts/factory_packet_envelope_contract_v1.md`
- `docs/contracts/factory_packet_validator_rules_v1.md`
- `docs/product/asset_supply_matrix_v1.md`
- `docs/design/surface_task_area_lowfi_v1.md`
- `docs/design/panel_matrix_script_variation_lowfi_v1.md`
