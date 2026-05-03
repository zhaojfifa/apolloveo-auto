# Matrix Script §8.G Phase B Panel Render Correctness — Execution Log v1

Date: 2026-05-03
Wave: ApolloVeo 2.0 Operator-Visible Surface Validation Wave (Plan A trial
correction set, follow-up blocker review v1, item §8.G)
Status: implementation green; ready for signoff
Authority:
- [docs/reviews/matrix_script_followup_blocker_review_v1.md](../reviews/matrix_script_followup_blocker_review_v1.md) §7 (§8.G — Phase B Panel Render Correctness), §9 (Gate Recommendation — §8.G READY, land first)
- [docs/contracts/matrix_script/workbench_variation_surface_contract_v1.md](../contracts/matrix_script/workbench_variation_surface_contract_v1.md) (frozen Phase B projection contract — unchanged by this fix)
- [docs/contracts/matrix_script/variation_matrix_contract_v1.md](../contracts/matrix_script/variation_matrix_contract_v1.md) (axes shape — unchanged)
- [docs/execution/MATRIX_SCRIPT_C_PHASE_B_AUTHORING_EXECUTION_LOG_v1.md](MATRIX_SCRIPT_C_PHASE_B_AUTHORING_EXECUTION_LOG_v1.md) (§8.C — landed; planner output that this template renders)
- [docs/execution/MATRIX_SCRIPT_B_DISPATCH_CONFIRMATION_EXECUTION_LOG_v1.md](MATRIX_SCRIPT_B_DISPATCH_CONFIRMATION_EXECUTION_LOG_v1.md) (§8.B — confirmed; panel mounting unchanged)
- [docs/execution/MATRIX_SCRIPT_A_REF_SHAPE_GUARD_EXECUTION_LOG_v1.md](MATRIX_SCRIPT_A_REF_SHAPE_GUARD_EXECUTION_LOG_v1.md) (§8.A — landed; ref-shape guard unchanged)
- [docs/execution/MATRIX_SCRIPT_D_OPERATOR_BRIEF_CORRECTION_EXECUTION_LOG_v1.md](MATRIX_SCRIPT_D_OPERATOR_BRIEF_CORRECTION_EXECUTION_LOG_v1.md) (§8.D — landed; operator brief unchanged here, §8.H successor will refresh)
- [ENGINEERING_RULES.md](../../ENGINEERING_RULES.md) §6 Contract-First, §10 Validation, §11 Scope Control
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
- the follow-up blocker review v1 (the active authority for §8.E / §8.F /
  §8.G);
- the prior trial blocker review and the §8.A / §8.B / §8.C / §8.D
  execution logs (so §8.G builds on the contract-clean fresh-sample
  pipeline that §8.A / §8.B / §8.C established and that §8.D has
  briefed);
- the matrix_script frozen contracts
  (`workbench_variation_surface_contract_v1`,
  `variation_matrix_contract_v1`, `slot_pack_contract_v1`,
  `task_entry_contract_v1` with §8.A and §8.C addenda) — none changed
  by this PR;
- read-only inspection of
  [gateway/app/templates/task_workbench.html](../../gateway/app/templates/task_workbench.html)
  (the only edited code file),
  [gateway/app/services/matrix_script/phase_b_authoring.py](../../gateway/app/services/matrix_script/phase_b_authoring.py)
  (consumed shape — `axes[].values` is a list for `tone`/`audience`,
  a `{min, max, step}` dict for `length`),
  [gateway/app/services/matrix_script/workbench_variation_surface.py](../../gateway/app/services/matrix_script/workbench_variation_surface.py)
  (projector that carries the planner output to the template
  unchanged).

No top-level `CLAUDE.md` update is needed. The standing instruction lives
in `ENGINEERING_RULES.md` / `CURRENT_ENGINEERING_FOCUS.md`; both have
been updated by this work.

## 2. Scope (binding)

This change implements **only** §8.G from the Matrix Script follow-up
blocker review v1: a narrow template/render correctness fix for the
Matrix Script Phase B variation panel's Axes table. The bug is a Jinja
attribute-vs-item access collision: `{{ axis.values }}` resolves to
the dict's bound `values()` *method* before falling back to the
`"values"` key, so neither `is mapping` nor `is iterable` matches and
the axes table renders `<built-in method values of dict object at
0x…>` instead of human-readable axis values for `tone`, `audience`,
and `length`.

Items §8.A (entry-form ref-shape guard — landed), §8.B (panel-dispatch
confirmation — confirmed, no narrow fix required), §8.C (Phase B
deterministic authoring — landed), and §8.D (operator brief correction
— landed) are out of scope and remain as already accepted. Items §8.E
(workbench shell line-conditional rendering) and §8.F (opaque-ref
discipline) are out of scope; the review §9 ordering puts §8.G first
because it is independently fixable, narrow, and does not depend on
either §8.E or §8.F.

### 2.1 What this change adds

- A two-step Jinja template fix at
  [gateway/app/templates/task_workbench.html:295-303](../../gateway/app/templates/task_workbench.html:295)
  inside the `{% if ops_workbench_panel.panel_kind == "matrix_script" %}`
  branch's Axes table cell:
  - hoist `{% set axis_values = axis["values"] %}` once per row (item
    access, **not** attribute access);
  - replace every subsequent `axis.values…` reference with
    `axis_values…` (`is mapping`, `is iterable and not string`, the
    `min`/`max`/`step` dict reads, the `join` filter input, and the
    `else`-branch render).
- A new regression test
  `test_axes_table_renders_human_readable_values` in
  [gateway/app/services/tests/test_matrix_script_phase_b_authoring.py](../../gateway/app/services/tests/test_matrix_script_phase_b_authoring.py)
  that scopes its assertion to the axes-table HTML region (between
  `<h3>Axes</h3>` and `<h3>Cells × Slots</h3>`), so cell-level
  `axis_selections` (which surface tone/audience tokens elsewhere on
  the page and previously masked this bug — see follow-up review §4.3)
  cannot mask a broken axes-row render. Asserts that the tone values
  (`formal`/`casual`/`playful`), the audience values
  (`b2b`/`b2c`/`internal`), and the length range mapping
  (`min=30 · max=120 · step=15`) all render inside the axes-table
  region; asserts that the broken bound-method repr
  (`<built-in method values`) is absent both inside the region and
  anywhere in the body.
- A defensive negative assertion (`<built-in method values` absent)
  added to the existing
  `test_get_workbench_renders_real_axes_cells_slots` so any future
  regression of the same shape is caught by both tests.
- This execution log.
- Standing repo guidance writeback to `ENGINEERING_STATUS.md`,
  `CURRENT_ENGINEERING_FOCUS.md`, the Matrix Script first-production-line
  log, and the ApolloVeo 2.0 evidence index.

### 2.2 What this change does NOT add (out of §8.G)

- no `task_entry_contract_v1` change (the closed entry-field set, the
  §8.A source-ref-shape addendum, and the §8.C Phase B authoring
  addendum all stand verbatim);
- no `workbench_variation_surface_contract_v1` change;
- no `workbench_panel_dispatch_contract_v1` change;
- no `variation_matrix_contract_v1` / `slot_pack_contract_v1` /
  `packet_v1` change;
- no Phase B planner change — `phase_b_authoring.py` is consumed
  read-only;
- no projector change — `workbench_variation_surface.py` is consumed
  read-only;
- no router change — `tasks.py` is not touched;
- no schema / sample / packet re-version;
- no §8.E shell-suppression change (Hot Follow stage cards / pipeline
  summary / dub-engine selectors / Burmese deliverable rows are
  intentionally still rendered by the shared shell on
  `kind=matrix_script` tasks; the operator-blocking shell defect
  remains, scoped to §8.E follow-up);
- no §8.F scheme tightening (`https`/`http` remain in the §8.A
  accepted-scheme set; opaque-ref discipline tightening is scoped to
  §8.F follow-up);
- no §8.D operator brief re-correction (§8.H is the natural successor
  once §8.E / §8.F / §8.G all land);
- no Phase D publish-feedback closure write-back;
- no Phase C delivery binding change;
- no `PANEL_REF_DISPATCH` widening;
- no provider / model / vendor / engine controls;
- no Hot Follow / Digital Anchor / Runtime Assembly / Capability
  Expansion entry;
- no second production line onboarding;
- no Asset Library / promote (Plan C C1–C3) work;
- no template gating predicate (`task.kind == "hot_follow"`) — that is
  §8.E's correction, not §8.G's;
- no audit of `task_workbench.html` Hot Follow regions (§8.G's audit is
  scoped to the matrix_script panel's own dict-method-collision
  patterns; the only other `.values` / `.keys` / `.items` / `.update`
  occurrences in the template are explicit method *calls* — `pipeline.get(...)`,
  `ms_slot_index.get(...)`, `ms_slot_index.update(...)`,
  `(cell.axis_selections or {}).items()` — which work correctly because
  Jinja resolves them as callables, not as keys).

## 3. Code / Docs Changes

| Change | File | Kind |
| ------ | ---- | ---- |
| Jinja item-access fix in the Axes-table values cell. Hoist `{% set axis_values = axis["values"] %}` once per row; replace `axis.values is mapping` / `axis.values.min` / `.max` / `.step` / `axis.values is iterable and axis.values is not string` / `axis.values \| join(" · ")` / `{{ axis.values }}` with `axis_values is mapping` / `axis_values["min"]` / `["max"]` / `["step"]` / `axis_values is iterable and axis_values is not string` / `axis_values \| join(" · ")` / `{{ axis_values }}`. Net change: 8 lines of edits, line count unchanged at 658. | [gateway/app/templates/task_workbench.html](../../gateway/app/templates/task_workbench.html) | EDIT |
| New axes-table-scoped regression test + bound-method-repr negative on the existing render test. Imports `LENGTH_RANGE` from the planner for the range-mapping assertion. | [gateway/app/services/tests/test_matrix_script_phase_b_authoring.py](../../gateway/app/services/tests/test_matrix_script_phase_b_authoring.py) | EDIT |
| This execution log. | [docs/execution/MATRIX_SCRIPT_G_RENDER_CORRECTNESS_EXECUTION_LOG_v1.md](MATRIX_SCRIPT_G_RENDER_CORRECTNESS_EXECUTION_LOG_v1.md) | NEW |
| Standing repo guidance writeback. | [ENGINEERING_STATUS.md](../../ENGINEERING_STATUS.md), [CURRENT_ENGINEERING_FOCUS.md](../../CURRENT_ENGINEERING_FOCUS.md), [docs/execution/MATRIX_SCRIPT_FIRST_PRODUCTION_LINE_LOG.md](MATRIX_SCRIPT_FIRST_PRODUCTION_LINE_LOG.md), [docs/execution/apolloveo_2_0_evidence_index_v1.md](apolloveo_2_0_evidence_index_v1.md) | EDIT |

**File-size budget.** `task_workbench.html` is a Jinja template, not a
Python module, so the ENGINEERING_RULES §1 file-size targets do not
apply. The edit is a localized substitution of 8 lines inside an
existing 9-line `{% if … %}` / `{% elif … %}` / `{% else %}` block. No
router or service file edited; no god-file growth; no new line-specific
logic in `tasks.py`, `task_view.py`, or `hot_follow_api.py`.

## 4. Validation Evidence

Interpreter: `~/.pyenv/versions/3.13.5/bin/python3` (Python 3.13.5),
matching the §8.A / §8.B / §8.C execution logs.
Worktree path:
`/Users/tylerzhao/Code/apolloveo-auto/.claude/worktrees/unruffled-merkle-d9f22e`.
Branch: `claude/unruffled-merkle-d9f22e`. Baseline commit: `bfa723d`
(post-§8.A / §8.B / §8.C / §8.D and post the follow-up blocker review
v1 landing). The old invalid pre-§8.A sample referenced in the prior
blocker review is **not** used in any of the assertions below.

### 4.1 Targeted suite — §8.G axes-table render plus §8.C end-to-end render

```
~/.pyenv/versions/3.13.5/bin/python3 -m pytest \
  gateway/app/services/tests/test_matrix_script_phase_b_authoring.py -v
```

Result: **12 passed, 0 failed.** The 11 prior §8.C end-to-end cases
(`test_post_persists_packet_with_populated_ls_deltas`,
`test_persisted_round_trip_cells_to_slots_resolves`,
`test_projector_consumes_authored_delta`,
`test_get_workbench_renders_real_axes_cells_slots` — now also asserts
`<built-in method values` is absent —
`test_persisted_cells_cardinality_matches_variation_target_count[1]`,
`[12]`, `test_slot_language_scope_uses_entry_target_language[mm]`,
`[vi]`, `test_source_script_ref_remains_opaque_on_phase_b_sample`,
`test_panel_kind_dispatch_unchanged_under_phase_b_authoring`,
`test_workbench_render_context_attaches_variation_surface`) all stay
green, plus the new
`test_axes_table_renders_human_readable_values` passes (asserts each
of `formal`/`casual`/`playful` is inside the axes table region; each
of `b2b`/`b2c`/`internal` is inside the axes table region;
`min=30`/`max=120`/`step=15` are inside the axes table region; the
broken bound-method repr is absent in the region and absent in the
body).

### 4.2 Surrounding suites — no regression

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

Result: **194 passed, 0 failed.** §8.A's 23 cases, §8.B's 4 cases,
§8.C's 27 + 12 cases (the §8.C end-to-end suite is now 12 cases
including §8.G's `test_axes_table_renders_human_readable_values`),
the existing
`tests/contracts/matrix_script/test_workbench_variation_phase_b.py`
(which loads the static sample directly and is unaffected by the
template-level item-access fix), the static Phase A artefact tests,
the operator-visible-surface contract suites, the wiring suite, and
the guardrails all stay green. The 193-case §8.C baseline (recorded
in [MATRIX_SCRIPT_C_PHASE_B_AUTHORING_EXECUTION_LOG_v1.md §4.3](MATRIX_SCRIPT_C_PHASE_B_AUTHORING_EXECUTION_LOG_v1.md))
becomes 194 here as a result of the new §8.G case.

### 4.3 Live render evidence (fresh sample, captured)

A direct end-to-end run against the live FastAPI app (in-memory repo,
fresh contract-clean sample, `task_id=6640deeeb1a6`,
`variation_target_count=4`, `target_language=mm`,
`source_script_ref=content://matrix-script/source/8g-evidence-001`):

```
POST status: 303
GET status: 200
HTML contains '<built-in method values': False

--- AXES TABLE REGION (whitespace collapsed for readability) ---
<h3 …>Axes</h3>
<table …>
  <thead>…axis_id…kind…values…required…</thead>
  <tbody>
    <tr>
      <td><code>tone</code></td>
      <td>categorical</td>
      <td>formal · casual · playful</td>
      <td>yes</td>
    </tr>
    <tr>
      <td><code>audience</code></td>
      <td>enum</td>
      <td>b2b · b2c · internal</td>
      <td>yes</td>
    </tr>
    <tr>
      <td><code>length</code></td>
      <td>range</td>
      <td>min=30 · max=120 · step=15</td>
      <td>no</td>
    </tr>
  </tbody>
</table>
```

This is the load-bearing operator-visible evidence: the Matrix Script
Phase B variation panel's Axes table now renders human-readable axis
values for all three canonical axes. The categorical axis (`tone`)
takes the `is iterable and is not string` branch and renders the list
joined by ` · `; the enum axis (`audience`) takes the same branch;
the range axis (`length`) takes the `is mapping` branch and renders
the `min`/`max`/`step` triple. The previously broken `<built-in
method values of dict object at 0x…>` repr is gone.

### 4.4 Manual proof of the four required §8.G validations

The §8.G "Validation" requirements from the follow-up blocker review
brief, mapped to evidence above:

| Required validation | Evidence |
| ------------------- | -------- |
| Tone values render correctly in the axes table. | §4.1 `test_axes_table_renders_human_readable_values` (asserts `formal`/`casual`/`playful` inside axes table region); §4.3 axes-table region shows `formal · casual · playful` for the `tone` row. |
| Audience values render correctly in the axes table. | §4.1 `test_axes_table_renders_human_readable_values` (asserts `b2b`/`b2c`/`internal` inside axes table region); §4.3 axes-table region shows `b2b · b2c · internal` for the `audience` row. |
| Length values render correctly in the axes table. | §4.1 `test_axes_table_renders_human_readable_values` (asserts `min=30`/`max=120`/`step=15` inside axes table region); §4.3 axes-table region shows `min=30 · max=120 · step=15` for the `length` row. |
| The old `<built-in method values …>` output is gone. | §4.1 `test_axes_table_renders_human_readable_values` and `test_get_workbench_renders_real_axes_cells_slots` both assert `<built-in method values` is not in the body; §4.3 captured render confirms `False`. |
| Smallest relevant regression suites + surrounding matrix_script / operator-visible tests stay green. | §4.2 — 194/194 across §8.A's 23, §8.B's 4, §8.C's planner-unit 27 and end-to-end (now 12), `test_workbench_variation_phase_b`, operator-visible-surface contracts, and guardrails. |

## 5. Contract Alignment Check

- `workbench_variation_surface_contract_v1`: respected, **unchanged**.
  The contract defines `variation_plan.axes[]` shape and the projector
  responsibilities; the projector emits the planner's `axes[]` verbatim
  (one element per declared axis, each carrying `axis_id`, `kind`,
  `values`, `is_required`). The template fix is a presentation-layer
  correction inside the `panel_kind="matrix_script"` mount; it consumes
  the same projection field shape the contract already pins.
- `variation_matrix_contract_v1`: respected, **unchanged**. `axes[]`
  field shape is unchanged at the planner, projector, and template
  levels. The `kind ∈ {categorical, enum, range}` closed set still
  drives template branching: list-shaped `values` for categorical /
  enum, dict-shaped `values` for range — exactly what the (now
  correctly-accessed) Jinja branches handle.
- `slot_pack_contract_v1`: respected, **unchanged**. No edit touches
  slot-detail rendering.
- `packet_v1`: respected, **unchanged**. No `status` / `ready` /
  `done` / `phase` / `current_attempt` / `delivery_ready` /
  `final_ready` / `publishable` field added at any scope. Validator
  R3 / R5 token sets unchanged.
- `task_entry_contract_v1`: respected, **unchanged**. The §8.A
  source-ref-shape addendum and the §8.C Phase B deterministic
  authoring addendum are unchanged. The closed entry-field set, the
  `Mapping note (entry → packet)`, and the line-truth/operator-hint
  rule are unchanged.
- `workbench_panel_dispatch_contract_v1` (§8.B authority): respected,
  **unchanged**. `PANEL_REF_DISPATCH` membership unchanged; resolver
  still returns `panel_kind="matrix_script"` (asserted by the
  unchanged §8.C dispatch regression case).
- `tasks.py` did not receive new line-specific logic. The router still
  dispatches via the registry + the projection bundle. No router edit.
- No new vendor / model / provider / engine identifier was introduced.
- No second source of task or state truth was introduced. The template
  is a presentation layer over the projector; the projector is a
  read-only projection of the packet; the packet remains the truth
  boundary.
- No template gating predicate added; the §8.E shell-suppression
  correction (which the follow-up review identifies as a separate
  shell defect with contract-level implications) is intentionally
  scoped out of §8.G.

## 6. Final Gate

- **§8.G: PASS.** Narrow Jinja item-access fix lands at template level
  only; the Matrix Script Phase B variation panel's Axes table now
  renders human-readable axis values for all three canonical axes;
  the bound-method repr is gone; both an axes-table-scoped positive
  regression test and a body-wide negative bound-method-repr
  assertion are in place.
- **Axes table readable: YES.** Tone row renders
  `formal · casual · playful`; audience row renders
  `b2b · b2c · internal`; length row renders
  `min=30 · max=120 · step=15` (per §4.3 captured render evidence).
- **Ready for §8.E: YES.** §8.G is independently fixable and does not
  block §8.E. §8.E is the next item in the follow-up review §9
  ordering — workbench shell line-conditional rendering — and remains
  scoped out of §8.G as required.
- **Old invalid sample reusable: NO** (per follow-up review §1, §4.3,
  and §9; reaffirmed — no §8.G assertion uses the prior sample;
  evidence in §4.3 is on a fresh post-§8.A / §8.B / §8.C sample).
- **§8.A / §8.B / §8.C / §8.D: not retracted.** §8.A guard, §8.B
  dispatch resolver, §8.C deterministic planner / projector / wire-up,
  and §8.D operator brief stand verbatim. §8.G is additive only.

## 7. Hard Red Lines (re-stated, observed)

This work observes every red line restated by the follow-up blocker
review §9 and the prior wave authority:

- Shell suppression: not touched. Hot Follow stage cards / pipeline
  summary / Burmese deliverable rows / dub-engine selectors are
  intentionally still rendered by the shared shell. §8.E is the
  binding correction for that defect; not landed here.
- `source_script_ref` scheme policy: not touched. The §8.A
  accepted-scheme tuple and the §8.A contract addendum stand
  verbatim; `https`/`http` are still accepted. §8.F is the binding
  correction for that defect; not landed here.
- §8.A / §8.B / §8.C / §8.D: not reopened.
- Workbench redesign: no.
- Per-line workbench template: not added — dispatch remains via
  `panel_kind` mount in the shared shell, per
  `workbench_panel_dispatch_contract_v1`.
- Hot Follow scope: not reopened. Hot Follow's
  `hot_follow_workbench.html` template is unaffected by this fix
  (it shares no edited code with the Matrix Script panel block).
- Platform Runtime Assembly / Capability Expansion: not entered.
- Provider / model / vendor / engine controls: not introduced.
- Workbench UI: not patched to fake correct values — the rendered
  values are the actual `axes[].values` payloads from the §8.C
  planner, accessed through the proper Jinja item-access form.
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
- `g_lang` token alphabet: not pinned in this PR (out of scope).

End of v1.
