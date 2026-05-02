# Matrix Script §8.B Workbench Panel Dispatch Confirmation — Execution Log v1

Date: 2026-05-03
Wave: ApolloVeo 2.0 Operator-Visible Surface Validation Wave (Plan A trial
correction set, item §8.B)
Status: confirmation green (no narrow fix required)
Authority:
- [docs/reviews/matrix_script_trial_blocker_and_realign_review_v1.md](../reviews/matrix_script_trial_blocker_and_realign_review_v1.md) §8.B
- [docs/contracts/workbench_panel_dispatch_contract_v1.md](../contracts/workbench_panel_dispatch_contract_v1.md)
- [docs/contracts/matrix_script/workbench_variation_surface_contract_v1.md](../contracts/matrix_script/workbench_variation_surface_contract_v1.md)
- [docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md)
- [docs/execution/MATRIX_SCRIPT_A_REF_SHAPE_GUARD_EXECUTION_LOG_v1.md](MATRIX_SCRIPT_A_REF_SHAPE_GUARD_EXECUTION_LOG_v1.md) (§8.A — landed)
- [ENGINEERING_RULES.md](../../ENGINEERING_RULES.md) §6 Contract-First, §10 Validation
- [CURRENT_ENGINEERING_FOCUS.md](../../CURRENT_ENGINEERING_FOCUS.md)

## 1. Reading Declaration

There is **no top-level `CLAUDE.md`** in this repository. Per the standing
execution discipline carried in
[ENGINEERING_RULES.md](../../ENGINEERING_RULES.md),
[CURRENT_ENGINEERING_FOCUS.md](../../CURRENT_ENGINEERING_FOCUS.md),
[ENGINEERING_STATUS.md](../../ENGINEERING_STATUS.md),
[ENGINEERING_CONSTRAINTS_INDEX.md](../../ENGINEERING_CONSTRAINTS_INDEX.md),
and [docs/ENGINEERING_INDEX.md](../ENGINEERING_INDEX.md), the equivalent
authority chain followed for this work is:

- engineering rules / current focus / status / constraints index;
- docs index;
- the §8.A landed log (so §8.B uses a sample created under the §8.A guard,
  not the prior invalid sample);
- the workbench panel-dispatch contract and the matrix_script workbench
  variation surface contract (the two contracts §8.B confirms);
- the trial readiness plan (current wave authority);
- read-only inspection of
  [gateway/app/routers/tasks.py](../../gateway/app/routers/tasks.py),
  [gateway/app/services/workbench_registry.py](../../gateway/app/services/workbench_registry.py),
  [gateway/app/services/operator_visible_surfaces/projections.py](../../gateway/app/services/operator_visible_surfaces/projections.py),
  [gateway/app/services/operator_visible_surfaces/wiring.py](../../gateway/app/services/operator_visible_surfaces/wiring.py),
  [gateway/app/services/task_router_presenters.py](../../gateway/app/services/task_router_presenters.py),
  [gateway/app/templates/task_workbench.html](../../gateway/app/templates/task_workbench.html),
  [gateway/app/services/matrix_script/workbench_variation_surface.py](../../gateway/app/services/matrix_script/workbench_variation_surface.py).

No top-level `CLAUDE.md` update is needed. The standing instruction lives
in `ENGINEERING_RULES.md` / `CURRENT_ENGINEERING_FOCUS.md`; both have
been updated by this work.

## 2. Scope (binding)

Implements only §8.B from the blocker review: confirm whether a fresh
contract-clean (post-§8.A) Matrix Script task actually lands on the
intended Phase B variation workbench panel for `kind=matrix_script`,
rather than the generic engineering shell. The old invalid sample is
NOT used as evidence.

What this work does:

- Use the `/tasks/matrix-script/new` formal POST to create a fresh
  contract-clean Matrix Script sample (§8.A's `_validate_source_script_ref_shape`
  guard is in force, so `source_script_ref` is an opaque ref handle).
- Trace the actual route path taken by `GET /tasks/{task_id}`.
- Trace the actual panel-dispatch path for `kind=matrix_script`.
- Confirm the mounted `panel_kind`.
- Confirm the rendered HTML actually mounts the Matrix Script Phase B
  variation panel section.

What this work does NOT do (out of §8.B):

- no Phase B authoring capability (§8.C remains the binding precondition
  for *populated* axes / cells / slots);
- no operator brief correction (§8.D);
- no workbench redesign;
- no per-line workbench template;
- no widening of `PANEL_REF_DISPATCH`;
- no Hot Follow / Digital Anchor / Runtime Assembly / Capability
  Expansion entry;
- no provider / model / vendor / engine controls;
- no packet / schema / sample re-version.

Result: dispatch is confirmed correct; no narrow fix was required.

## 3. Trace — Route, Resolver, Surface, Render

### 3.1 Which route is hit

| Step | Path | Handler / function |
| ---- | ---- | ------------------ |
| 1. Operator submits create form | `POST /tasks/matrix-script/new` | `gateway.app.routers.tasks::create_matrix_script_task` |
| 2. Builder seeds payload | — | `gateway.app.services.matrix_script.create_entry::build_matrix_script_task_payload` (seeds `kind=matrix_script`, `category_key=matrix_script`, `platform=matrix_script`, top-level `line_specific_refs[matrix_script_variation_matrix, matrix_script_slot_pack]`, mirror under `packet.line_specific_refs[]`, redirect target `/tasks/{task_id}?created=matrix_script`) |
| 3. Repo round-trip | — | `repo.create(payload)` → `repo.get(task_id)`; `normalize_task_payload` is permissive and does not strip `packet` or `line_specific_refs` |
| 4. Operator opens the task | `GET /tasks/{task_id}` | `gateway.app.routers.tasks::task_workbench_page` |
| 5. Workbench template choice | — | `gateway.app.services.workbench_registry::resolve_workbench_spec(task)` → `WORKBENCH_REGISTRY["default"]` (because no `matrix_script` row exists; only `default`, `apollo_avatar`, `hot_follow` are registered) → `template="task_workbench.html"` |
| 6. Page context | — | `gateway.app.services.task_router_presenters::build_task_workbench_page_context` → `build_task_workbench_task_json` → `build_operator_surfaces_for_workbench(task=...)` |
| 7. Packet view | — | `_packet_view(task)` reads `task["line_specific_refs"]` (and falls back to `task["packet"]["line_specific_refs"]`) — both are present after the round-trip |
| 8. Resolver | — | `resolve_line_specific_panel(packet)` walks `line_specific_refs[]`, looks each `ref_id` up in `PANEL_REF_DISPATCH`, and returns `panel_kind="matrix_script"` plus the two surfaced refs |
| 9. Variation surface | — | `wiring.py` attaches `bundle["workbench"]["matrix_script_variation_surface"] = project_workbench_variation_surface(packet_view)` because `panel_kind == "matrix_script"` |
| 10. Template render | — | `task_workbench.html` reads `task_json.operator_surfaces.workbench.line_specific_panel.panel_kind`. The `{% if ops_workbench_panel.panel_kind == "matrix_script" %}` branch mounts the Matrix Script Variation Panel section |

### 3.2 Which panel kind is mounted

`PANEL_REF_DISPATCH` (frozen by
[docs/contracts/workbench_panel_dispatch_contract_v1.md](../contracts/workbench_panel_dispatch_contract_v1.md)
and implemented at
[gateway/app/services/operator_visible_surfaces/projections.py:239-246](../../gateway/app/services/operator_visible_surfaces/projections.py:239)):

```
matrix_script_variation_matrix  →  matrix_script
matrix_script_slot_pack         →  matrix_script
```

Both ref_ids are seeded by the formal create-entry payload-builder (one
for variation matrix, one for slot pack). The resolver returns
`panel_kind="matrix_script"`, which is the contract-correct dispatch for
this line.

### 3.3 Whether the rendered result is the generic shell or the Matrix Script surface

The operator-visible answer: **the Matrix Script Phase B variation panel
mounts on top of the shared shell**.

Important nuance to record (correcting an implicit reading in the blocker
review §3 row #2): the `task_workbench.html` template is the **shared
workbench shell**, not a "generic engineering shell" in the sense of "no
line-specific surface". Per-line dispatch in this wave is via
`panel_kind` mounting inside the shared shell, not via per-line template
files. The contract
[workbench_panel_dispatch_contract_v1](../contracts/workbench_panel_dispatch_contract_v1.md)
pins the dispatch object as `(ref_id → panel_kind)`; it does not require
`(panel_kind → template)`.

For the fresh contract-clean sample, the shell mounts the Matrix Script
Variation Panel with the labelled heading "Matrix Script — Variation
Panel" and the contract projection name
`matrix_script_workbench_variation_surface_v1`, both visible to the
operator. The line-panel slot is data-tagged `data-panel-kind="matrix_script"`
and the operator-visible "Line panel" strip displays `matrix_script`. The
empty-slot fallback message ("No `line_specific_refs[]` on this packet")
is **absent**.

The blocker review's hypothesis "if dispatch did route, the operator
could not tell, which is itself a defect" is therefore not borne out for
a contract-clean sample: the panel is visually identifiable as Matrix
Script. What the prior invalid sample suffered from was empty axes /
cells / slots inside a correctly-mounted panel — a §8.C concern, not a
§8.B dispatch concern.

### 3.4 Divergence point — none required

The blocker review §4 named three divergence loci, all owned by §8.A or
§8.C. For §8.B specifically, the trace above shows no dispatch
divergence. No narrow fix was applied.

## 4. Code / Docs Changes

| Change | File | Kind |
| ------ | ---- | ---- |
| New end-to-end §8.B confirmation suite. POSTs a fresh contract-clean Matrix Script sample, GETs `/tasks/{task_id}`, and asserts: (a) the redirect lands at `/tasks/{task_id}?created=matrix_script`; (b) the persisted task carries the two seeded `line_specific_refs[]` ref_ids on both the top-level mirror and the packet envelope; (c) `resolve_line_specific_panel` returns `panel_kind="matrix_script"` and both ref_ids; (d) the rendered HTML contains the Matrix Script Phase B variation panel markup with the contract projection name, the `data-panel-kind="matrix_script"` data attribute, and both ref_ids surfaced; (e) the empty-slot fallback message is absent. | [gateway/app/services/tests/test_matrix_script_workbench_dispatch.py](../../gateway/app/services/tests/test_matrix_script_workbench_dispatch.py) | NEW |
| This execution log. | [docs/execution/MATRIX_SCRIPT_B_DISPATCH_CONFIRMATION_EXECUTION_LOG_v1.md](MATRIX_SCRIPT_B_DISPATCH_CONFIRMATION_EXECUTION_LOG_v1.md) | NEW |
| Standing repo guidance writeback. | [ENGINEERING_STATUS.md](../../ENGINEERING_STATUS.md), [CURRENT_ENGINEERING_FOCUS.md](../../CURRENT_ENGINEERING_FOCUS.md), [docs/execution/MATRIX_SCRIPT_FIRST_PRODUCTION_LINE_LOG.md](MATRIX_SCRIPT_FIRST_PRODUCTION_LINE_LOG.md), [docs/execution/apolloveo_2_0_evidence_index_v1.md](apolloveo_2_0_evidence_index_v1.md) | EDIT |

No production code, contract, schema, sample, template, router,
projection module, or workbench surface was modified. No new line was
onboarded; no panel_kind was added; no ref_id was added; no provider /
model / vendor / engine identifier was introduced. The only product
artefact added is a confirmation test against the existing dispatch.

## 5. Validation Evidence

Interpreter: `~/.pyenv/versions/3.13.5/bin/python3` (Python 3.13.5).
Worktree path: `/Users/tylerzhao/Code/apolloveo-auto/.claude/worktrees/zen-chandrasekhar-caa7c9`.
Branch: `claude/zen-chandrasekhar-caa7c9`. Baseline: `f6125aa` (§8.A).
The old invalid sample referenced in the blocker review is **not** used
in any of the assertions below.

### 5.1 New §8.B suite

```
~/.pyenv/versions/3.13.5/bin/python3 -m pytest \
  gateway/app/services/tests/test_matrix_script_workbench_dispatch.py -v
```

Result: **4 passed, 0 failed.** Cases:

- `test_post_redirect_target_is_workbench_route` — POST 303 to
  `/tasks/{task_id}?created=matrix_script`; persisted `kind=matrix_script`;
  `source_url` carries the opaque ref (i.e. §8.A's guard is provably in
  force on the sample under test).
- `test_fresh_sample_packet_seeds_dispatch_inputs` — top-level and
  envelope `line_specific_refs[]` both carry the
  `{matrix_script_variation_matrix, matrix_script_slot_pack}` pair.
- `test_resolver_dispatches_fresh_sample_to_matrix_script_panel_kind` —
  `PANEL_REF_DISPATCH` membership pinned, then
  `resolve_line_specific_panel(packet)` returns
  `panel_kind="matrix_script"` and both surfaced refs.
- `test_get_workbench_renders_matrix_script_phase_b_variation_panel` —
  end-to-end load-bearing assertion. POST a fresh sample, GET
  `/tasks/{task_id}`, capture render context, then assert: template is
  `task_workbench.html`; `panel_kind="matrix_script"`;
  `matrix_script_variation_surface` is attached;
  `data-role="matrix-script-variation-panel"`,
  `data-panel-kind="matrix_script"`,
  `matrix_script_workbench_variation_surface_v1`,
  `matrix_script_variation_matrix`, and `matrix_script_slot_pack` are all
  present in the response body; the empty-slot fallback message is
  absent.

### 5.2 Surrounding suites — no regression

```
~/.pyenv/versions/3.13.5/bin/python3 -m pytest \
  gateway/app/services/tests/test_matrix_script_workbench_dispatch.py \
  gateway/app/services/tests/test_matrix_script_source_script_ref_shape.py \
  gateway/app/services/tests/test_new_tasks_surface.py \
  gateway/app/services/tests/test_task_router_presenters.py \
  tests/contracts/matrix_script/ \
  tests/contracts/operator_visible_surfaces/ \
  tests/guardrails/ -q
```

Result: **155 passed, 0 failed.** §8.A's 23 cases, the existing
matrix-script + operator-visible-surface contract suites, and the
guardrails all stay green.

### 5.3 Captured render markers (fresh sample, end-to-end)

A direct end-to-end run against the live FastAPI app (in-memory repo,
fresh contract-clean sample, `task_id=ade26ae85f0b`):

```
POST status: 303
POST redirect: /tasks/ade26ae85f0b?created=matrix_script
kind= matrix_script category_key= matrix_script platform= matrix_script
source_url(persisted opaque ref)= content://matrix-script/source/8b-evidence-001
packet.line_specific_refs ref_ids: ['matrix_script_variation_matrix', 'matrix_script_slot_pack']
Resolver panel_kind: matrix_script
Resolver surfaced refs: ['matrix_script_variation_matrix', 'matrix_script_slot_pack']
GET status: 200
HTML contains 'data-role="matrix-script-variation-panel"': True
HTML contains 'data-panel-kind="matrix_script"': True
HTML contains 'matrix_script_workbench_variation_surface_v1': True
HTML contains 'matrix_script_variation_matrix': True
HTML contains 'matrix_script_slot_pack': True
HTML contains empty-slot fallback: False
HTML contains 'Line panel' label: True
operator-line-panel-kind text: matrix_script
```

This is the "before/after using the same fresh-sample discipline"
evidence requested by the §8.B brief, with the explicit framing that
**there is no "before" / broken state to fix** — dispatch was already
correct end-to-end; the fresh sample proves it. The "before" state
captured by the blocker review's prior invalid sample was an upstream
contamination (§8.A's pasted body text) compounded with empty LS deltas
(§8.C's authoring gap), neither of which is dispatch-layer.

### 5.4 Pre-existing environment limitation

`gateway/app/services/tests/test_task_repository_file.py::test_op_download_proxy_uses_attachment_redirect_for_final_video`
remains red on the worktree baseline (`f6125aa`) without any of this
change's edits applied. The §8.A log already recorded this as an
environment limitation per `ENGINEERING_RULES.md` §10; it is unrelated
to Matrix Script dispatch and is not introduced or affected by §8.B.

## 6. Contract Alignment Check

- `workbench_panel_dispatch_contract_v1`: PANEL_REF_DISPATCH membership
  pinned and asserted. The closed `(ref_id → panel_kind)` map is
  un-amended; the resolver still returns `panel_kind=null` for unknown
  ref_ids; no new `panel_kind` was added; no vendor / model / provider /
  engine identifier exists in the dispatch boundary or its inputs. The
  closed-by-default rule is observed.
- `matrix_script/workbench_variation_surface_contract_v1`: the
  projection name `matrix_script_workbench_variation_surface_v1` is
  surfaced verbatim in the rendered template; the projection runs only
  when `panel_kind == "matrix_script"`. No mutation of the contract or
  the projection.
- `matrix_script/task_entry_contract_v1` (with the §8.A addendum): the
  fresh sample under test was created through the formal POST and the
  guard rejected nothing; the persisted `source_url` is an opaque ref.
  The contract is respected by the entry boundary.
- `tasks.py` did not receive new line-specific logic. The router still
  dispatches via the registry + the projection bundle.

## 7. Final Gate

- **§8.B: PASS.** The dispatch resolver returns
  `panel_kind="matrix_script"` for a fresh contract-clean Matrix Script
  sample, the workbench surface bundle attaches the formal
  `matrix_script_workbench_variation_surface_v1` projection, and the
  rendered HTML mounts the Matrix Script Phase B variation panel.
- **Matrix Script workbench route confirmed: YES.** GET `/tasks/{task_id}`
  for `kind=matrix_script` lands the operator on the shared shell with
  the line panel mounted on top.
- **Phase B variation surface actually mounted: YES.** Confirmed by both
  the captured render context (panel_kind, surface attached) and the
  rendered HTML markers (`data-role`, `data-panel-kind`, projection
  name, both ref_ids surfaced, empty-slot fallback absent).
- **Old invalid sample reusable: NO.** Per the blocker review §9 and
  §8.A's gate; no §8.B assertion uses the prior sample.
- **Fresh contract-clean sample required: YES.** All §8.B evidence is
  produced from a fresh POST under §8.A's guard.
- **Ready for §8.C: YES.** Dispatch is confirmed; the binding remaining
  precondition for Plan A trial evidence is §8.C (Phase B authoring
  capability or fixture-LS-delta policy) so that axes / cells / slots
  resolve to non-empty values inside the correctly-mounted panel.

## 8. Hard Red Lines (re-stated, observed)

This work observes every red line restated by the blocker review §9 and
the wave authority:

- Hot Follow scope: not reopened.
- Platform Runtime Assembly / Capability Expansion: not entered.
- Provider / model / vendor / engine controls: not introduced.
- Workbench UI: not patched to fake populated axes / cells / slots.
- Workbench redesigned: no.
- Per-line workbench template added: no — dispatch remains via
  `panel_kind` mount in the shared shell, per the existing contracts.
- `source_script_ref` contract: unchanged (§8.A's addendum stands as-is).
- Delivery Center for Matrix Script: still inspect-only; not touched.
- State-shape fields (`delivery_ready`, `publishable`, `final_ready`,
  …): not added to any surface.
- Second production line: not onboarded; Digital Anchor implementation
  remains gated to Plan E.
- Old invalid sample: not used as evidence.

End of v1.
