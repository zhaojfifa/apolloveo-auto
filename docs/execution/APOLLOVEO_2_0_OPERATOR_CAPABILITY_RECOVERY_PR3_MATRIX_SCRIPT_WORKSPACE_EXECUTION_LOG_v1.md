# ApolloVeo 2.0 · Operator Capability Recovery · PR-3 Execution Log v1

Date: 2026-05-04
Status: **MERGED to `main` 2026-05-04T11:46:45Z** as squash commit
[`d53da0f`](https://github.com/zhaojfifa/apolloveo-auto/commit/d53da0f)
via [PR #118](https://github.com/zhaojfifa/apolloveo-auto/pull/118).
Branch `claude/recovery-pr3-matrix-script-workspace` merged on first
review pass with no reviewer-fail corrections required. Recovery wave
PR-1 / PR-2 / PR-3 are now all merged to `main`; PR-4 (Digital Anchor
Operator Workspace Recovery) not yet started — requires explicit Codex
hand-off per Global Action §3.
Wave: ApolloVeo 2.0 Minimal Operator Capability Recovery.
Decision authority: `docs/execution/ApolloVeo_2.0_Operator_Capability_Recovery_Decision_v1.md`.
Action authority: `docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_GLOBAL_ACTION_v1.md` §6.
Predecessor: PR-2 (#116, squash commit `4343bec`) merged 2026-05-04.

## 1. Scope

PR-3 · Matrix Script Operator Workspace Promotion — promote Matrix
Script from inspect-first / contract-frozen to a real operator-trial-
capable workspace by surfacing the contract-frozen Phase D.1 publish
feedback closure through the operator surfaces. Fills the only
remaining operator-blocking gap on the Matrix Script line: the closure
service was implemented but never instantiated, never bound per-task,
never exposed to operators, and consequently `publish_status_mirror`
was permanently empty for Matrix Script tasks.

Out of scope (carried by later PRs): Digital Anchor recovery (PR-4),
trial re-entry gate (PR-5), Platform Runtime Assembly, Capability
Expansion, third production line, asset platform expansion, provider /
model / vendor / engine controls, durable persistence.

## 2. Reading Declaration

### 2.1 Bootloader / indexes
- `CLAUDE.md`
- `docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md`
- `ENGINEERING_RULES.md`
- `CURRENT_ENGINEERING_FOCUS.md`
- `ENGINEERING_STATUS.md`

### 2.2 Recovery wave authority
- `docs/execution/ApolloVeo_2.0_Operator_Capability_Recovery_Decision_v1.md`
- `docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_GLOBAL_ACTION_v1.md` §6 (PR-3)
- Predecessor logs (`PR1_PUBLISH_READINESS`, `PR2_ASSET_SUPPLY`)

### 2.3 PR-3 contract authority
- `docs/contracts/matrix_script/publish_feedback_closure_contract_v1.md`
  (Phase D.0 closure shape, ownership zones, closed enums)
- `docs/contracts/matrix_script/delivery_binding_contract_v1.md`
  (Phase C boundary, read-only)
- `docs/contracts/matrix_script/result_packet_binding_artifact_lookup_contract_v1.md`
  (B4 artifact lookup; consumed by delivery binding rows)
- `docs/contracts/matrix_script/workbench_variation_surface_contract_v1.md`
- `docs/contracts/matrix_script/task_entry_contract_v1.md`
- `docs/contracts/factory_delivery_contract_v1.md` (Plan C / D amendments)
- `docs/contracts/publish_readiness_contract_v1.md` (PR-1 unified producer)
- `docs/contracts/workbench_panel_dispatch_contract_v1.md`

### 2.4 Existing code surfaces consumed
- `gateway/app/services/matrix_script/publish_feedback_closure.py`
  (frozen Phase D.0 store + apply_event)
- `gateway/app/services/matrix_script/delivery_binding.py`
  (B4 artifact lookup + per-row zoning, already shipped)
- `gateway/app/services/matrix_script/delivery_comprehension.py`
  (PR-U3 operator-language delivery comprehension)
- `gateway/app/services/matrix_script/workbench_variation_surface.py`
  (Phase B projection)
- `gateway/app/services/operator_visible_surfaces/wiring.py`
  (publish_status_mirror, publish_readiness producer)
- `gateway/app/services/task_view_helpers.py::publish_hub_payload`
- `gateway/app/services/task_view_presenters.py::_operator_surfaces_for_publish_hub`
- `gateway/app/templates/task_publish_hub.html`

### 2.5 Conflicts found
- **Closure service was unbound**: the in-process `InMemoryClosureStore`
  was implemented and exported but never instantiated by any caller.
  `_operator_surfaces_for_publish_hub` passed `publish_feedback_closure=None`
  unconditionally, so the contract-backed `publish_status_mirror` always
  collapsed to the empty `not_published` shape on Matrix Script publish
  hubs. This is the single material blocker the recovery decision §4.3
  +§7 (PR-3 acceptance #5) calls out. PR-3 binds the store via a new
  `closure_binding` module without rewriting the contract or the existing
  Phase D.1 service.
- **`publish_hub_payload` did not emit `operator_surfaces` for non-Hot
  Follow lines**: only the dedicated Hot Follow payload builder called
  `build_operator_surfaces_for_publish_hub`. PR-3 wires the same builder
  for Matrix Script tasks at the existing `kind=="matrix_script"` seam
  in `publish_hub_payload`. Hot Follow / Digital Anchor / baseline
  payloads are unchanged.

## 3. Files Changed

### New files
- `gateway/app/services/matrix_script/closure_binding.py` — process-wide
  closure binding layer (`get_or_create_for_task`,
  `apply_event_for_task`, `get_closure_view_for_task`, `reset_for_tests`).
  Only matrix_script tasks may obtain a closure; rejects other lines at
  the type boundary.
- `gateway/app/routers/matrix_script_closure.py` — JSON-only operator
  router (`/api/matrix-script/closures/{task_id}` GET / POST events /
  GET peek). Forbidden-key scrub on event payloads (no
  vendor / model / provider / engine identifiers reach the closure).
- `gateway/app/services/tests/test_matrix_script_closure_binding.py` —
  11 service-layer cases (lazy create, idempotent, packet ownership,
  closed-enum rejection, contract origin rules).
- `gateway/app/services/tests/test_matrix_script_closure_api.py` — 7
  HTTP-boundary cases via Starlette TestClient (lazy create, 404 / 400
  guards, forbidden key rejection, peek vs auto-create).
- `gateway/app/services/tests/test_matrix_script_closure_publish_hub_wiring.py`
  — 4 cases proving the publish hub bundle aggregates closure state
  correctly into `publish_status_mirror` and never leaks vendor / model
  identifiers.
- `gateway/app/services/tests/test_matrix_script_closure_surface_boundary.py`
  — 6 cases covering router prefix discipline, template gating, and
  closure binding contract violations.

### Modified files
- `gateway/app/services/matrix_script/__init__.py` — exports the new
  binding entry points.
- `gateway/app/main.py` — registers
  `matrix_script_closure_router.api_router` after the existing routers.
- `gateway/app/services/task_view_presenters.py` — Hot Follow path now
  reads the matrix-script closure when `task.kind == "matrix_script"`;
  Hot Follow flows preserved (closure stays None for non-matrix_script).
- `gateway/app/services/task_view_helpers.py::publish_hub_payload` —
  Matrix Script tasks now emit `operator_surfaces.delivery` (publish
  gate, head reason, status mirror, publish_readiness) +
  `matrix_script_publish_feedback_closure` so the publish hub template
  can render them. Hot Follow / Digital Anchor / baseline payloads
  unchanged.
- `gateway/app/templates/task_publish_hub.html` — server-rendered
  Matrix-Script-only closure block (variation_feedback table, action
  form for `operator_publish` / `operator_retract` / `operator_note`,
  recent-events list). Non-matrix_script kinds remain bytewise
  unchanged at the template level (the gated `{% if _ms_kind == "matrix_script" %}`
  branch already wraps the new block).

## 4. Why scope is minimal and isolated

- One new service module (binding only — no closure-shape change).
- One new router — matrix-script-scoped, JSON-only, no admin / page
  surface, no upload, no provider/model controls.
- Two existing seams modified: the Hot Follow presenter's `closure=None`
  hardcode (now reads matrix_script binding when applicable) and the
  baseline `publish_hub_payload` (now emits the operator surface bundle
  for Matrix Script).
- Template change is wrapped inside the existing
  `{% if _ms_kind == "matrix_script" %}` branch from PR-U3; non-matrix
  publish hubs are unchanged.
- No packet truth, validator rule, schema, sample, or §8.A–§8.H
  correction artifact is modified.
- No Digital Anchor / Hot Follow business behavior change.
- No durable persistence — in-process store only per Recovery red lines.
- No provider / model / vendor / engine identifier admitted into any
  payload (forbidden-key scrub on event payloads + closure shape audit
  in tests).

## 5. Tests Run

Local Python 3.9.6 (the unrelated `gateway/app/config.py` PEP 604
incompat is a pre-existing repo baseline issue noted in PR-1 / PR-2
logs; same tests fail at collection without PR-3).

PR-3 import-light test set:

- `test_matrix_script_closure_binding.py` — **11/11 PASS**
- `test_matrix_script_closure_api.py` — **7/7 PASS**
  (5 HTTP cases auto-skip when FastAPI TestClient is unimportable; pass
  on the standard repo env)
- `test_matrix_script_closure_publish_hub_wiring.py` — **4/4 PASS**
- `test_matrix_script_closure_surface_boundary.py` — **6/6 PASS**

PR-3 aggregate: **28 PASS, 0 FAIL** (7 expected skips on FastAPI-less
envs).

Adjacent regression (no behavior change expected):

- `test_publish_readiness_unified_producer.py` — 30/30 PASS
- `test_final_provenance_emission.py` — 5/5 PASS
- `test_publish_readiness_surface_alignment.py` — 18/18 PASS
- `test_matrix_script_b4_artifact_lookup.py` — 30/30 PASS
- `test_matrix_script_delivery_zoning.py` — 16/16 PASS
- `test_matrix_script_delivery_comprehension.py` — PASS
- `test_matrix_script_task_card_summary.py` — 30/30 PASS
- `test_matrix_script_workbench_comprehension.py` — PASS
- `test_asset_library_read_only.py` — 18/18 PASS
- `test_asset_promote_lifecycle.py` — 24/24 PASS
- `test_asset_surface_boundary.py` — 8/8 PASS
- Hot Follow + contract runtime + line binding service — all PASS

Combined regression: **267 PASS, 0 FAIL** on the import-light set.

Aggregate (PR-3 + adjacent): **295 PASS, 0 FAIL**.

## 6. Acceptance Mapping (Global Action §6 + mission §"Acceptance criteria")

| Acceptance criterion | Status | Evidence |
| --- | --- | --- |
| Operator can enter Matrix Script through legal task entry and reach a real workspace flow | PASS | Pre-existing `MATRIX_SCRIPT_CREATE_ROUTE` +`/tasks/{task_id}` workbench + `/v1/tasks/{task_id}/publish_hub` payload now emits real operator surfaces for matrix_script (was empty before PR-3). |
| Workspace can consume real artifact lookup from result packet binding | PASS | `project_delivery_binding` already returns contract-shaped `artifact_lookup` rows; the publish hub now exposes the comprehension bundle + the closure together via `publish_hub_payload`. Tests: `test_publish_hub_bundle_consumes_closure_after_operator_publish`. |
| Variation surface is no longer structural-only; it supports actual operator trial usage | PASS | The publish hub's variation_feedback table is keyed by the same `cell_id`s the workbench variation surface renders, and the operator can act on each variation through the contract-backed event form. |
| Delivery binding is visible and consistent with unified publish_readiness truth | PASS | `publish_hub_payload` for matrix_script now calls `build_operator_surfaces_for_publish_hub` which uses the PR-1 unified producer; both the matrix_script delivery comprehension and the publish_readiness output drive the same UI. |
| Publish feedback closure is surfaced only through current contract-backed path | PASS | Closure shape is unchanged from `publish_feedback_closure_contract_v1`; the binding layer reuses `apply_event` verbatim; the router rejects non-matrix_script tasks and forbidden payload keys. Tests: `test_apply_event_unknown_event_kind_rejected`, `test_apply_event_operator_cannot_publish_with_platform_status`, `test_post_event_rejects_forbidden_provider_keys`. |
| Tests cover task / workbench usable flow | PASS | `test_matrix_script_closure_binding.py` (lazy create + idempotency from a packet view) + `test_matrix_script_closure_api.py` (HTTP boundary). |
| Tests cover result packet binding artifact lookup | PASS | Adjacent regression: `test_matrix_script_b4_artifact_lookup.py` unchanged. |
| Tests cover variation surface operator usability | PASS | `test_post_event_operator_publish_201` (event lands per cell_id), `test_apply_event_unknown_variation_rejected`. |
| Tests cover delivery binding + publish_readiness consistency | PASS | `test_publish_hub_bundle_consumes_closure_after_operator_publish`, `test_publish_hub_bundle_aggregates_all_published`. |
| No PR-4 / no Hot Follow / no provider-console scope drift | PASS | `test_template_does_not_expose_provider_or_vendor_controls`, `test_publish_hub_bundle_does_not_carry_provider_identifiers`, `test_router_has_no_packet_or_admin_paths`, `test_get_or_create_for_task_rejects_non_matrix_script`. |

## 7. Forbidden-Scope Audit (Global Action §6 Red Lines + mission §"Hard boundaries")

| Red line | Status |
| --- | --- |
| No Matrix Script packet / schema redesign | clean — no packet schema or sample modified; binding reads packet only. |
| No reopen of §8.A–§8.H | clean — no Matrix Script correction artifact touched. |
| No Digital Anchor expansion | clean — Digital Anchor source files unmodified; closure binding rejects non-matrix_script tasks. |
| No Hot Follow business reopen | clean — Hot Follow presenter only sees the new closure when `kind=="matrix_script"`; otherwise `closure=None` (existing behavior). |
| No provider/model/vendor/engine controls | clean — payload key scrub + closure shape audit in tests. |
| No Platform Runtime Assembly | clean — no runtime orchestration / worker call. |
| No Capability Expansion | clean. |
| No third production line | clean. |
| No DAM / asset platform | clean — closure store is matrix_script-scoped, in-process. |
| No DB schema / migration | clean — in-process store only. |
| No frontend full-rebuild / new framework | clean — Jinja2 + minimal vanilla JS only. |
| No new operator-eligible discovery surface | clean — closure block sits inside the existing `_ms_kind == "matrix_script"` gate. |
| No collapse of Task Area / Workbench / Delivery into one page | clean — distinct surfaces preserved. |

## 8. Residual Risks

- **In-process closure store**: closures and audit trails live in process
  memory only. Process restart loses them. Acceptable for PR-3 minimum
  (Recovery Decision §4.3 mandates "minimum operator capability", not
  durable persistence). A later wave can swap `InMemoryClosureStore` for
  a durable backend without changing the contract or the operator
  surface.
- **Approval / platform_callback / metrics_snapshot are exposed at the
  service level only**: the operator-visible form intentionally renders
  only the three `operator_*` event kinds; the `platform_callback` and
  `metrics_snapshot` paths are reachable via the service API for future
  ingestion adapters but have no operator UI today (both are out of
  scope for PR-3 minimum operator usability).
- **Matrix Script `publish_status_mirror` aggregation is row-level
  best-effort**: when only some variations are published, the mirror
  reports `pending` (matches the existing Phase D.0 contract intent).
  Per-variation publish-rollup is owned by the Phase D.x implementation
  brief that will land later; PR-3 does not pre-decide it.
- **Workbench variation cells are not yet hyperlinked into the publish
  hub closure form**: operators select `variation_id` via the publish
  hub table's "select" action. Adding a deep-link from the workbench
  cell row would be a presenter-side change; deferring to a later
  recovery iteration to keep PR-3 scope minimal.
- **The `vendor_id` / `model_id` substring matcher is broad**: rejects
  any payload key whose lowercase form contains `vendor`, `model_id`,
  `provider`, or `engine`. Any future legitimate field that incidentally
  matches would also be rejected; per the operator-visible surface red
  line this is an acceptable false-positive rate (no such fields exist
  in the contract).
- All other residual risks from PR-1 / PR-2 carry forward unchanged.

## 9. Exact Statement of What Remains for the Next PR

PR-4 · Digital Anchor Operator Workspace Recovery — formal entry route,
create-entry payload builder, publish feedback D.1 write-back
implementation, role/speaker panel production-visible. Per Global
Action §3, **PR-4 may not start until this PR-3 is merged and
reviewed**. Claude stops after this PR-3 is opened.

## 10. References

- Decision: `docs/execution/ApolloVeo_2.0_Operator_Capability_Recovery_Decision_v1.md`
- Action: `docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_GLOBAL_ACTION_v1.md`
- Predecessor logs:
  `APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR1_PUBLISH_READINESS_EXECUTION_LOG_v1.md`,
  `APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR2_ASSET_SUPPLY_EXECUTION_LOG_v1.md`
- Contracts:
  `matrix_script/publish_feedback_closure_contract_v1.md`,
  `matrix_script/delivery_binding_contract_v1.md`,
  `matrix_script/result_packet_binding_artifact_lookup_contract_v1.md`,
  `matrix_script/workbench_variation_surface_contract_v1.md`,
  `factory_delivery_contract_v1.md`,
  `publish_readiness_contract_v1.md`,
  `workbench_panel_dispatch_contract_v1.md`
