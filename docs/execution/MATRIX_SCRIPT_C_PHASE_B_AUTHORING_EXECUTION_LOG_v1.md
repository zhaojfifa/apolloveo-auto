# Matrix Script §8.C Phase B Authoring — Execution Log v1

Date: 2026-05-03
Wave: ApolloVeo 2.0 Operator-Visible Surface Validation Wave (Plan A trial
correction set, item §8.C)
Status: implementation green; ready for signoff
Authority:
- [docs/reviews/matrix_script_trial_blocker_and_realign_review_v1.md](../reviews/matrix_script_trial_blocker_and_realign_review_v1.md) §8.C
- [docs/contracts/matrix_script/task_entry_contract_v1.md](../contracts/matrix_script/task_entry_contract_v1.md) (with Phase B authoring addendum landed in this change)
- [docs/contracts/matrix_script/variation_matrix_contract_v1.md](../contracts/matrix_script/variation_matrix_contract_v1.md)
- [docs/contracts/matrix_script/slot_pack_contract_v1.md](../contracts/matrix_script/slot_pack_contract_v1.md)
- [docs/contracts/matrix_script/packet_v1.md](../contracts/matrix_script/packet_v1.md)
- [docs/contracts/matrix_script/workbench_variation_surface_contract_v1.md](../contracts/matrix_script/workbench_variation_surface_contract_v1.md)
- [docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md)
- [docs/execution/MATRIX_SCRIPT_A_REF_SHAPE_GUARD_EXECUTION_LOG_v1.md](MATRIX_SCRIPT_A_REF_SHAPE_GUARD_EXECUTION_LOG_v1.md) (§8.A — landed)
- [docs/execution/MATRIX_SCRIPT_B_DISPATCH_CONFIRMATION_EXECUTION_LOG_v1.md](MATRIX_SCRIPT_B_DISPATCH_CONFIRMATION_EXECUTION_LOG_v1.md) (§8.B — confirmed)
- [ENGINEERING_RULES.md](../../ENGINEERING_RULES.md) §6 Contract-First, §10 Validation
- [CURRENT_ENGINEERING_FOCUS.md](../../CURRENT_ENGINEERING_FOCUS.md)

## 1. Reading Declaration

There is **no top-level `CLAUDE.md`** in this repository. Per the standing
execution discipline carried in
[ENGINEERING_RULES.md](../../ENGINEERING_RULES.md),
[CURRENT_ENGINEERING_FOCUS.md](../../CURRENT_ENGINEERING_FOCUS.md),
[ENGINEERING_STATUS.md](../../ENGINEERING_STATUS.md),
[ENGINEERING_CONSTRAINTS_INDEX.md](../../ENGINEERING_CONSTRAINTS_INDEX.md),
[PROJECT_RULES.md](../../PROJECT_RULES.md), and
[docs/ENGINEERING_INDEX.md](../ENGINEERING_INDEX.md), the equivalent
authority chain followed for this work is:

- engineering rules / current focus / status / constraints index;
- docs index;
- the §8.A and §8.B landed logs (so §8.C uses a sample created under the
  §8.A guard and the §8.B-confirmed dispatch, not the prior invalid
  sample);
- the matrix_script frozen contracts (`task_entry_contract_v1`,
  `packet_v1`, `variation_matrix_contract_v1`, `slot_pack_contract_v1`,
  `workbench_variation_surface_contract_v1`) — the four frozen
  authorities §8.C must respect;
- the trial readiness plan (current wave authority);
- the blocker review §8.C decision (Option C1 vs C2) and §9 hard red
  lines;
- read-only inspection of
  [gateway/app/services/matrix_script/create_entry.py](../../gateway/app/services/matrix_script/create_entry.py),
  [gateway/app/services/matrix_script/workbench_variation_surface.py](../../gateway/app/services/matrix_script/workbench_variation_surface.py),
  [gateway/app/services/operator_visible_surfaces/wiring.py](../../gateway/app/services/operator_visible_surfaces/wiring.py),
  [gateway/app/templates/task_workbench.html](../../gateway/app/templates/task_workbench.html),
  [schemas/packets/matrix_script/sample/matrix_script_packet_v1.sample.json](../../schemas/packets/matrix_script/sample/matrix_script_packet_v1.sample.json),
  [tests/contracts/matrix_script/test_workbench_variation_phase_b.py](../../tests/contracts/matrix_script/test_workbench_variation_phase_b.py).

No top-level `CLAUDE.md` update is needed. The standing instruction lives
in `ENGINEERING_RULES.md` / `CURRENT_ENGINEERING_FOCUS.md`; both have
been updated by this work.

## 2. Scope (binding)

This change implements **only** §8.C from the Matrix Script trial blocker
review: a synchronous, deterministic Phase B authoring step that
populates `variation_matrix.delta.axes[]/cells[]` and
`slot_pack.delta.slots[]` on every fresh contract-clean Matrix Script
sample, so the §8.B-confirmed Phase B variation panel renders real
resolvable axes / cells / slots truth instead of empty fallbacks. Items
§8.A (entry-form ref-shape guard — landed) and §8.B (panel-dispatch
confirmation — confirmed, no narrow fix required) are out of scope and
remain as already accepted. §8.D (operator brief correction) is out of
scope and remains required before fresh sample evidence is fully
briefed.

### 2.1 Path decision

The blocker review §8.C offered two paths:

- **Option C1** — minimal real Phase B authoring;
- **Option C2** — explicit fixture-LS-delta policy.

This change lands **Option C1**. Rationale, with citations:

1. The entry contract has already pre-specified the mapping. The
   `Mapping note (entry → packet)` at
   [task_entry_contract_v1.md:101-125](../contracts/matrix_script/task_entry_contract_v1.md)
   explicitly maps `entry.variation_target_count` → `cells[]` cardinality,
   `entry.audience_hint`/`tone_hint`/`length_hint` → axis-value selection,
   `entry.source_script_ref` → `slots[*].body_ref`, and
   `entry.language_scope` → `slots[*].language_scope`. C1 is the
   implementation of a mapping the contract has already declared.
2. Wave authority explicitly authorizes §8.C as in-wave correction work.
   [CURRENT_ENGINEERING_FOCUS.md:10](../../CURRENT_ENGINEERING_FOCUS.md)
   names "Plan A trial correction set ... §8.C and §8.D still required
   before a fresh Matrix Script trial sample is authorized." This is
   current-wave-aware authorization, not a Plan E gated item.
3. C2 is strictly worse for the same runtime outcome: a fixture-LS-delta
   policy ships the same delta values via a static fixture **plus** a
   new fixture file **plus** a contract addendum declaring
   fixture-vs-authoring. C1 is smaller and more honest because the
   entry inputs (`variation_target_count`, `language_scope`) actually
   drive the deltas.

The mission's "tiny stub alongside the minimal real path … only if repo
authority forces" branch is not exercised; repo authority does not
force a stub.

### 2.2 What this change adds

- A new pure module
  [gateway/app/services/matrix_script/phase_b_authoring.py](../../gateway/app/services/matrix_script/phase_b_authoring.py)
  exporting `derive_phase_b_deltas(entry, task_id) -> tuple[dict, dict]`
  that returns `(variation_matrix_delta, slot_pack_delta)` from the
  closed entry field set.
- A wire-up edit in
  [gateway/app/services/matrix_script/create_entry.py](../../gateway/app/services/matrix_script/create_entry.py)
  that calls `derive_phase_b_deltas` once inside
  `build_matrix_script_task_payload` and attaches the resulting deltas
  to both LS1 (`matrix_script_variation_matrix`) and LS2
  (`matrix_script_slot_pack`) entries on **both** the packet mirror
  and the duplicate top-level mirror.
- A contract addendum
  ([docs/contracts/matrix_script/task_entry_contract_v1.md](../contracts/matrix_script/task_entry_contract_v1.md)
  §"Phase B deterministic authoring (addendum, 2026-05-03)") that
  pins the canonical axes, the cell↔slot pairing rule, the opaque
  `body_ref` template, the determinism statement, and the Plan E
  removal path.
- Two focused test suites (planner unit + end-to-end HTTP boundary).

### 2.3 What this change does NOT add (out of §8.C)

- no Phase B authoring surface in the workbench (Phase B render
  remains read-only per `workbench_variation_surface_contract_v1`);
- no operator brief correction (§8.D);
- no Phase D publish-feedback closure write-back (still contract-only);
- no Phase C delivery binding work (Matrix Script Delivery Center
  remains inspect-only with `not_implemented_phase_c` placeholders);
- no schema / sample / packet re-version;
- no template change to `task_workbench.html`;
- no projector change to `workbench_variation_surface.py`;
- no router change to `tasks.py`;
- no widening of `PANEL_REF_DISPATCH`;
- no `g_lang` token alphabet pinning (separate review);
- no Hot Follow / Digital Anchor / Runtime Assembly / Capability
  Expansion entry;
- no provider / model / vendor / engine controls;
- no Plan B B4 (`result_packet_binding` artifact lookup), Plan D D1
  (`publish_readiness`), D2 (`final_provenance`), D3 (workbench panel
  dispatch as contract object), or D4 (advisory producer) — all remain
  Plan E gated;
- no second production line onboarding;
- no Asset Library / promote (Plan C C1–C3) work;
- no consumption of optional entry hints (`audience_hint`, `tone_hint`,
  `length_hint`) — the addendum names this as permitted Plan E future
  work.

## 3. Code / Docs Changes

| Change | File | Kind |
| ------ | ---- | ---- |
| New deterministic Phase B planner module — `derive_phase_b_deltas(entry, task_id)`, canonical axes, 1-to-1 cell↔slot pairing, opaque `body_ref` template. Pure function: no IO, no clock, no randomness, no router import, no `HTTPException`. | [gateway/app/services/matrix_script/phase_b_authoring.py](../../gateway/app/services/matrix_script/phase_b_authoring.py) | NEW |
| Add `from copy import deepcopy`; import `derive_phase_b_deltas`; call once after `task_id = uuid4().hex[:12]`; populate `delta` on both LS1 and LS2 in the packet mirror and the top-level mirror (the top-level mirror gets a `deepcopy` so the two mirrors are independent dict trees). | [gateway/app/services/matrix_script/create_entry.py](../../gateway/app/services/matrix_script/create_entry.py) | EDIT |
| Append §"Phase B deterministic authoring (addendum, 2026-05-03)" after §8.A's source-ref-shape addendum, mirroring its style. ~50 lines: pinned canonical axes table, cell↔slot pairing rule, `body_ref` template, determinism statement, hint-consumption out-of-scope note, Plan E removal path. | [docs/contracts/matrix_script/task_entry_contract_v1.md](../contracts/matrix_script/task_entry_contract_v1.md) | EDIT |
| New planner unit + contract conformance suite (27 cases) — axes pinned, kind sets closed, cardinality matches `variation_target_count`, round-trip `cells[i] ↔ slots[i]`, axis-selection drawn from declared values, `body_ref` opaque + step-aligned, no forbidden state/vendor/donor field, planner deterministic, planner does not mutate entry, output trees independent across calls, projector consumes authored delta. | [tests/contracts/matrix_script/test_phase_b_authoring_phase_c.py](../../tests/contracts/matrix_script/test_phase_b_authoring_phase_c.py) | NEW |
| New end-to-end HTTP-boundary suite (11 cases) — POST persists populated deltas on both mirrors; round-trip resolves through the persisted packet; projector consumes authored delta; rendered HTML carries cell/slot ids, axis ids, value tokens, and the empty-fallback messages are absent; cardinality matches at k=1 and k=12; slot `language_scope` carries entry's `target_language` for `mm`/`vi`; §8.A guard remains in force on the §8.C sample; §8.B dispatch markers remain in force; render context attaches the variation surface with axes=3, cells=4, slots=4. | [gateway/app/services/tests/test_matrix_script_phase_b_authoring.py](../../gateway/app/services/tests/test_matrix_script_phase_b_authoring.py) | NEW |
| This execution log. | [docs/execution/MATRIX_SCRIPT_C_PHASE_B_AUTHORING_EXECUTION_LOG_v1.md](MATRIX_SCRIPT_C_PHASE_B_AUTHORING_EXECUTION_LOG_v1.md) | NEW |
| Standing repo guidance writeback. | [ENGINEERING_STATUS.md](../../ENGINEERING_STATUS.md), [CURRENT_ENGINEERING_FOCUS.md](../../CURRENT_ENGINEERING_FOCUS.md), [docs/execution/MATRIX_SCRIPT_FIRST_PRODUCTION_LINE_LOG.md](MATRIX_SCRIPT_FIRST_PRODUCTION_LINE_LOG.md), [docs/execution/apolloveo_2_0_evidence_index_v1.md](apolloveo_2_0_evidence_index_v1.md) | EDIT |

**File-size budget.** `create_entry.py` 305 → 314 lines (well under the
ENGINEERING_RULES §1 service threshold of 900). New
`phase_b_authoring.py` is 160 lines (well under). No router edits. No
god-file growth. No new line-specific logic in `tasks.py`,
`task_view.py`, or `hot_follow_api.py`.

## 4. Validation Evidence

Interpreter: `~/.pyenv/versions/3.13.5/bin/python3` (Python 3.13.5),
matching the §8.A and §8.B execution logs.
Worktree path:
`/Users/tylerzhao/Code/apolloveo-auto/.claude/worktrees/charming-franklin-2546a9`.
Branch: `claude/charming-franklin-2546a9`. Baseline commit: `970b4dc`
(post-§8.B). The old invalid sample referenced in the blocker review is
**not** used in any of the assertions below.

### 4.1 New §8.C planner unit + contract conformance suite

```
~/.pyenv/versions/3.13.5/bin/python3 -m pytest \
  tests/contracts/matrix_script/test_phase_b_authoring_phase_c.py -v
```

Result: **27 passed, 0 failed.** Cases:

- **Axes (3):** `test_axes_emitted_match_contract_canonical_set`,
  `test_axis_kind_set_is_closed_contract_set`,
  `test_slot_kind_set_is_closed_contract_set`.
- **Cardinality + round-trip (3 cardinality + 3 round-trip + 1 ID format
  = 7):** `test_cells_cardinality_matches_variation_target_count` for
  k ∈ {1, 2, 4, 9, 12}; `test_round_trip_cells_to_slots` for
  k ∈ {1, 4, 12}; `test_cell_and_slot_ids_use_zero_padded_three_digit_format`.
- **Axis selection conformance (2):**
  `test_cell_axis_selections_drawn_from_axis_values`,
  `test_axis_selections_distinct_for_max_k` — proves all 12 cells at
  k=12 carry distinct `(tone, audience, length)` tuples.
- **Body ref opacity (2):**
  `test_body_ref_is_opaque_and_carries_no_body_text` — defends
  `slot_pack_contract_v1` §"Forbidden": `body_ref` must not equal the
  operator-supplied `source_script_ref` and must not embed `topic`;
  `test_body_ref_includes_task_id_and_slot_id`.
- **Slot defaults / language scope (3):**
  `test_slot_kind_default_is_primary_member`,
  `test_slot_language_scope_carries_entry_target_language` (parametrised
  for `mm` / `vi`), `test_slot_length_hint_matches_cell_length_pick`.
- **Forbidden tokens (R3 / R5) (2):**
  `test_no_state_or_vendor_field_in_either_delta` walks the delta dict
  trees AND a sorted-JSON serialisation; pins absence of
  `vendor_id`/`model_id`/`provider_id`/`engine_id`/`delivery_ready`/
  `final_ready`/`publishable`/`current_attempt`/`status`/`ready`/`done`/
  `phase`. `test_no_donor_or_cross_line_concept_in_delta` defends
  against `donor_*`, `swiftcraft`, `digital_anchor`, `hot_follow_business`,
  `avatar`.
- **Determinism / purity (4):** `test_planner_is_deterministic_same_inputs`,
  `test_planner_does_not_mutate_entry`,
  `test_planner_outputs_are_independent_calls_share_no_aliasing`,
  `test_different_task_ids_produce_different_body_refs`.
- **Projector integration (1):**
  `test_projector_consumes_authored_delta_via_packet_envelope` — builds
  a packet envelope with the planner's deltas, runs
  `project_workbench_variation_surface(packet)`, and asserts
  `variation_plan.axes`, `variation_plan.cells`, `copy_bundle.slots`,
  and `slot_detail_surface.slots` match the authored deltas exactly,
  with cells↔slots round-trip resolving through the projector output.

### 4.2 New §8.C end-to-end HTTP-boundary suite

```
~/.pyenv/versions/3.13.5/bin/python3 -m pytest \
  gateway/app/services/tests/test_matrix_script_phase_b_authoring.py -v
```

Result: **11 passed, 0 failed.** Cases:

- `test_post_persists_packet_with_populated_ls_deltas` — POST a fresh
  contract-clean Matrix Script sample with `variation_target_count=4`;
  read back the persisted task; assert both LS1 and LS2, on the
  packet mirror **and** the top-level mirror, carry populated `delta`
  with the expected axis/slot kind sets, axes of length 3, cells and
  slots of length 4.
- `test_persisted_round_trip_cells_to_slots_resolves` — for the
  persisted sample, every cell's `script_slot_ref` resolves to a
  declared slot, and every slot's `binds_cell_id` resolves to a
  declared cell.
- `test_projector_consumes_authored_delta` — POST → read packet →
  call `project_workbench_variation_surface(packet)` and assert the
  projection's `variation_plan.axes`, `.cells`, `copy_bundle.slots`
  are non-empty with the expected counts.
- `test_get_workbench_renders_real_axes_cells_slots` — POST + GET
  `/tasks/{task_id}?created=matrix_script` and assert the rendered
  HTML body contains: the §8.B mount markers
  (`data-role="matrix-script-variation-panel"`,
  `data-panel-kind="matrix_script"`,
  `matrix_script_workbench_variation_surface_v1`); all four cell ids
  (`cell_001..cell_004`); all four slot ids (`slot_001..slot_004`);
  the canonical axis ids `tone`, `audience`, `length`; at least one
  tone token (formal/casual/playful) and one audience token
  (b2b/b2c/internal); and that the empty-fallback messages
  (`"No axes resolved on this packet"`,
  `"No cells resolved on this packet"`,
  `"No slots resolved on this packet"`,
  `"No `line_specific_refs[]` on this packet"`) are **absent**.
- `test_persisted_cells_cardinality_matches_variation_target_count` —
  parametrised at k=1 and k=12 (the validated `_variation_count`
  bounds). Asserts cardinality, opaque `body_ref` prefix, and
  step-aligned `length_hint` at the boundaries.
- `test_slot_language_scope_uses_entry_target_language` — parametrised
  for `target_language ∈ {"mm", "vi"}`. Confirms the slot scope
  carries the entry's submitted target language, mirroring the
  current `mm` / `vi` allowed set in `create_entry.py:40`.
- `test_source_script_ref_remains_opaque_on_phase_b_sample` — §8.A
  guard regression check. Confirms the persisted `source_url` and
  `config.entry.source_script_ref` are the operator-submitted opaque
  ref, and that synthesised `body_ref` values are not equal to the
  source ref (defends `slot_pack_contract_v1` §"Forbidden": no body
  embedding, no source-ref piggybacking).
- `test_panel_kind_dispatch_unchanged_under_phase_b_authoring` — §8.B
  dispatch regression check. Pins
  `PANEL_REF_DISPATCH["matrix_script_variation_matrix"] == "matrix_script"`
  and `PANEL_REF_DISPATCH["matrix_script_slot_pack"] == "matrix_script"`,
  then runs `resolve_line_specific_panel(packet)` against the
  populated-delta packet and asserts `panel_kind="matrix_script"`
  and both ref_ids surface.
- `test_workbench_render_context_attaches_variation_surface` — captures
  the render context for `task_workbench.html` and asserts the
  template name is `task_workbench.html`, panel_kind is
  `matrix_script`, the variation surface is attached with axes=3,
  cells=4, slots=4.

### 4.3 Surrounding suites — no regression

```
~/.pyenv/versions/3.13.5/bin/python3 -m pytest \
  tests/contracts/matrix_script/test_phase_b_authoring_phase_c.py \
  gateway/app/services/tests/test_matrix_script_phase_b_authoring.py \
  gateway/app/services/tests/test_matrix_script_source_script_ref_shape.py \
  gateway/app/services/tests/test_matrix_script_workbench_dispatch.py \
  gateway/app/services/tests/test_new_tasks_surface.py \
  gateway/app/services/tests/test_task_router_presenters.py \
  tests/contracts/matrix_script/ \
  tests/contracts/operator_visible_surfaces/ \
  tests/guardrails/ -q
```

Result: **193 passed, 0 failed.** §8.A's 23 cases, §8.B's 4 cases, §8.C's
27 + 11 cases, the existing
`tests/contracts/matrix_script/test_workbench_variation_phase_b.py`
(which loads the static sample directly and is unaffected by the runtime
delta shape), the static Phase A artefact tests, the operator-visible-
surface contract suites, the wiring suite, and the guardrails all stay
green.

### 4.4 Pre-existing environment limitation

```
~/.pyenv/versions/3.13.5/bin/python3 -m pytest gateway/app/services/tests/ -q
```

Result: **339 passed, 1 failed** —
`gateway/app/services/tests/test_task_repository_file.py::test_op_download_proxy_uses_attachment_redirect_for_final_video`
fails with HTTP 500 vs expected 302. **Confirmed unrelated to §8.C.** A
`git stash --include-untracked` round-trip reproduces the same failure
on the worktree baseline (`970b4dc`, the §8.C starting commit) without
any of this change's edits applied (verified: stash → run failing test
→ pop). This failure was already recorded as an environment limitation
in the §8.A and §8.B execution logs per `ENGINEERING_RULES.md` §10
("distinguish code regressions from environment limitations"); it is
not introduced or affected by §8.C.

### 4.5 Live end-to-end render evidence (fresh sample, captured)

A direct end-to-end run against the live FastAPI app (in-memory repo,
fresh contract-clean sample, `task_id=b224f07d2c5a`, `variation_target_count=4`,
`target_language=mm`):

```
POST status: 303
POST redirect: /tasks/b224f07d2c5a?created=matrix_script
task_id: b224f07d2c5a
kind=matrix_script category_key=matrix_script platform=matrix_script
source_url(persisted opaque ref)= content://matrix-script/source/8c-evidence-001
LS1 delta keys: ['axis_kind_set', 'axes', 'cells']
LS2 delta keys: ['slot_kind_set', 'slots']
axes count: 3
axis ids: ['tone', 'audience', 'length']
cells count: 4
cell ids: ['cell_001', 'cell_002', 'cell_003', 'cell_004']
slots count: 4
slot ids: ['slot_001', 'slot_002', 'slot_003', 'slot_004']
sample cell axis_selections: {'tone': 'formal', 'audience': 'b2b', 'length': 30}
sample slot body_ref: content://matrix-script/b224f07d2c5a/slot/slot_001
sample slot language_scope: {'source_language': 'zh', 'target_language': ['mm']}
cells->slots round-trip resolves: True
GET status: 200
HTML contains 'data-role="matrix-script-variation-panel"': True
HTML contains 'data-panel-kind="matrix_script"': True
HTML contains 'matrix_script_workbench_variation_surface_v1': True
HTML contains 'cell_001'..'cell_004': True
HTML contains 'slot_001'..'slot_004': True
HTML contains canonical axis ids: True
HTML contains some tone token: True
HTML contains some audience token: True
HTML contains 'No axes resolved': False
HTML contains 'No cells resolved': False
HTML contains 'No slots resolved': False
```

This is the load-bearing operator-visible evidence: a fresh
contract-clean Matrix Script sample created via the formal POST,
under §8.A's guard, dispatched correctly per §8.B, now renders real
resolvable axes / cells / slots in the Phase B variation panel —
**not** the empty-fallback rendering that blocked Plan A trial
evidence on the previous sample.

### 4.6 Manual proof of the four required validations

The §8.C "Validation" requirements from the blocker review brief,
mapped to evidence above:

| Required validation | Evidence |
| ------------------- | -------- |
| `variation_matrix.axes` resolve. | §4.5 (axis ids `[tone, audience, length]`); §4.1 `test_axes_emitted_match_contract_canonical_set`; §4.2 `test_get_workbench_renders_real_axes_cells_slots`. |
| `variation_matrix.cells` resolve. | §4.5 (4 cells, ids `cell_001..cell_004`); §4.1 `test_cells_cardinality_matches_variation_target_count[1,2,4,9,12]`; §4.2 `test_post_persists_packet_with_populated_ls_deltas`. |
| `slot_pack.slots` resolve. | §4.5 (4 slots, ids `slot_001..slot_004`); §4.1 round-trip + cardinality cases; §4.2 `test_post_persists_packet_with_populated_ls_deltas`. |
| `cells[].script_slot_ref` correctly round-trips into sibling slot truth. | §4.1 `test_round_trip_cells_to_slots[1,4,12]`; §4.2 `test_persisted_round_trip_cells_to_slots_resolves`; §4.5 `cells->slots round-trip resolves: True`. |
| Mounted Matrix Script variation surface renders real inspectable data, not empty fallback. | §4.5 HTML markers (cell/slot ids, axis ids, tone/audience tokens present; empty-fallback messages absent); §4.2 `test_get_workbench_renders_real_axes_cells_slots` and `test_workbench_render_context_attaches_variation_surface`. |
| Packet truth remains aligned to frozen contracts. | §4.1 closed-set kind tests, forbidden-token tests, donor / cross-line absence tests; §4.2 §8.A and §8.B regression cases. No contract or schema or sample re-version. |
| If using fixture/stub policy, the policy is explicit and narrow. | N/A — Option C1 chosen; Option C2 not used. The contract addendum at `task_entry_contract_v1.md` §"Phase B deterministic authoring (addendum, 2026-05-03)" pins the deterministic seed as a Plan A trial wave authoring step with a Plan E removal path. |

## 5. Contract Alignment Check

- `task_entry_contract_v1` Mapping note (entry → packet): now
  implemented. The pre-specified mapping for `variation_target_count`,
  `language_scope`, `source_script_ref`, and the canonical `tone` /
  `audience` / `length` axes is exercised at task-creation time. The
  closed entry-field set is unchanged — the addendum constrains the
  *implementation* of the mapping, not the entry surface.
- `task_entry_contract_v1` §"Source script ref shape (addendum,
  2026-05-02)" (§8.A): respected and asserted as a regression guard
  in the §8.C end-to-end suite (`test_source_script_ref_remains_opaque_on_phase_b_sample`).
  The persisted `source_url` and `config.entry.source_script_ref` carry
  the operator-supplied opaque ref. Synthesised `body_ref` values are
  per-slot, opaque, and never equal to the source ref.
- `variation_matrix_contract_v1`: respected. `axes[]` shape (axis_id /
  kind / values / is_required) matches the contract table; cells[]
  shape matches; `axis_kind_set = ["categorical", "range", "enum"]`
  closed; no state-shape fields, no vendor pins, no embed of
  `factory_input` / `factory_content_structure` record shapes.
- `slot_pack_contract_v1`: respected. `slots[]` shape matches; closed
  `slot_kind_set` honored; `body_ref` is opaque (defends contract
  §"Forbidden" — no body text embedded); `language_scope` drawn from
  what the entry surface accepts (the `g_lang` token alphabet pinning
  is a separate review and out of §8.C scope per the addendum).
- `packet_v1`: respected. `line_id`, `packet_version`,
  `line_specific_refs[]`, `metadata.notes` envelope unchanged. No
  `status` / `ready` / `done` / `phase` / `current_attempt` /
  `delivery_ready` / `final_ready` / `publishable` field added at any
  scope. Validator R3 / R5 token sets unchanged.
- `workbench_variation_surface_contract_v1`: respected. The projector
  module is unchanged; it now consumes non-empty deltas and emits
  non-empty `variation_plan` / `copy_bundle` / `slot_detail_surface`,
  which is exactly what the contract permits (the projector's
  fallback-to-empty branch is simply not reached). The integrity-warning
  branch on unresolved `script_slot_ref` is not exercised because
  round-trip resolves by construction.
- `workbench_panel_dispatch_contract_v1` (§8.B authority): respected.
  `PANEL_REF_DISPATCH` membership unchanged; resolver still returns
  `panel_kind="matrix_script"` for the populated-delta sample (asserted
  in the §8.C suite as a §8.B regression guard).
- `tasks.py` did not receive new line-specific logic. The router still
  dispatches via the registry + the projection bundle. The new planning
  logic lives in the matrix_script line service module.
- No new vendor / model / provider / engine identifier was introduced.
- No second source of task or state truth was introduced. The planner
  is a pure derivation; the packet remains the truth boundary.

## 6. Final Gate

- **§8.C: PASS.** Deterministic Phase B authoring lands at
  task-creation time; both LS1 and LS2 ref entries (top-level mirror
  and packet mirror) carry populated `delta` payloads; projector
  consumes them verbatim; rendered HTML carries real axes/cells/slots
  with the empty-fallback messages absent.
- **Fresh corrected Matrix Script sample possible: YES.**
- **Phase B truth populated for axes / cells / slots: YES.**
- **`cells[].script_slot_ref` correctly round-trips into sibling slot
  truth: YES.**
- **Mounted Matrix Script variation surface renders real inspectable
  data, not empty fallback: YES.**
- **Packet truth remains aligned to frozen contracts: YES** (LS1 / LS2
  / packet / workbench surface contracts; `task_entry_contract_v1` with
  the new same-PR addendum).
- **Old invalid sample reusable: NO** (per blocker review §9; reaffirmed
  — no §8.C assertion uses the prior sample).
- **Ready for Matrix Script retry sample creation: YES.** §8.A guard
  + §8.B dispatch + §8.C deterministic authoring together produce a
  fresh contract-clean trial sample whose Phase B variation panel
  renders real inspectable truth. §8.D operator brief correction
  remains required before the sample is fully briefed for the trial.

## 7. Hard Red Lines (re-stated, observed)

This work observes every red line restated by the blocker review §9
and the wave authority:

- Hot Follow scope: not reopened.
- Platform Runtime Assembly / Capability Expansion: not entered.
- Provider / model / vendor / engine controls: not introduced.
- Workbench UI: not patched to fake populated axes/cells/slots — the
  data is real, derived from real entry inputs.
- Workbench redesign: no.
- Per-line workbench template: not added — dispatch remains via
  `panel_kind` mount in the shared shell, per the existing contracts.
- `source_script_ref` contract: unchanged (§8.A's addendum stands
  as-is; §8.C's addendum is additive, narrows the *implementation*
  of the existing mapping note, never widens any field shape).
- Delivery Center for Matrix Script: still inspect-only; not touched.
- Phase D publish-feedback closure: still contract-only; no write-back
  code added.
- State-shape fields (`delivery_ready`, `publishable`, `final_ready`,
  …): not added to any surface.
- Second production line: not onboarded; Digital Anchor implementation
  remains gated to Plan E.
- `tasks.py` / `task_view.py` / `hot_follow_api.py`: untouched.
- Old invalid sample: not used as evidence.
- Asset Library / promote (Plan C C1–C3): not entered.
- Plan E gated items (B4 `result_packet_binding`, D1 `publish_readiness`,
  D2 `final_provenance`, D3 panel-dispatch-as-contract-object,
  D4 advisory producer): not implemented.
- `g_lang` token alphabet: not pinned in this PR (out of scope; left
  to a separate review against `factory_language_plan_contract_v1`).

End of v1.
