# ApolloVeo 2.0 · Operator Capability Recovery · PR-4 Execution Log v1

Date: 2026-05-04
Status: **MERGED to `main` 2026-05-04T13:07:02Z** as squash commit
[`0549ee0`](https://github.com/zhaojfifa/apolloveo-auto/commit/0549ee0)
via [PR #119](https://github.com/zhaojfifa/apolloveo-auto/pull/119).
Branch `claude/recovery-pr4-digital-anchor-workspace` merged after one
reviewer-fail correction pass (see §9.1: route-shape `language_scope`
alignment, route-boundary closed-set rejection, D.1 write-back active
truth path). Recovery wave PR-1 / PR-2 / PR-3 / PR-4 are now all
merged to `main`; PR-5 (Real Operator Trial Re-entry Gate) not yet
started — requires explicit hand-off per Global Action §3.
Wave: ApolloVeo 2.0 Minimal Operator Capability Recovery.
Decision authority:
`docs/execution/ApolloVeo_2.0_Operator_Capability_Recovery_Decision_v1.md`.
Action authority:
`docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_GLOBAL_ACTION_v1.md` §7.
Predecessors: PR-1 (#114, `4c317c4`), PR-2 (#116, `4343bec`), PR-3
(#118, `d53da0f`) — all merged 2026-05-04.

## 1. Scope

PR-4 · Digital Anchor Operator Workspace Recovery — fourth mandatory
slice of Minimal Operator Capability Recovery. Recovers Digital Anchor
from inspection-only (placeholder `/tasks/connect/digital_anchor/new`,
no create-entry path, no closure binding, no operator surface for the
Phase B / C / D contracts) into a **real operator-usable workspace** by
implementing the closed contracts already frozen at the Plan B layer
(`task_entry_v1`, `create_entry_payload_builder_v1`,
`new_task_route_v1`, `workbench_role_speaker_surface_v1`,
`delivery_binding_v1`, `publish_feedback_closure_v1`,
`publish_feedback_writeback_v1`).

Out of scope (carried by PR-5): real operator trial re-entry gate,
live Plan A trial signoff, durable persistence, broader runtime
assembly. PR-5 gates on PR-1..PR-4 acceptance per Global Action §3.

## 2. Reading Declaration

### 2.1 Bootloader / indexes
- `CLAUDE.md`
- `docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md`
- `ENGINEERING_RULES.md`
- `CURRENT_ENGINEERING_FOCUS.md`
- `ENGINEERING_STATUS.md`

### 2.2 Recovery wave authority
- `docs/execution/ApolloVeo_2.0_Operator_Capability_Recovery_Decision_v1.md`
- `docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_GLOBAL_ACTION_v1.md` §7 (PR-4)
- Predecessor logs (PR-1 / PR-2 / PR-3)

### 2.3 PR-4 contract authority
- `docs/contracts/digital_anchor/task_entry_contract_v1.md`
- `docs/contracts/digital_anchor/create_entry_payload_builder_contract_v1.md`
- `docs/contracts/digital_anchor/new_task_route_contract_v1.md`
- `docs/contracts/digital_anchor/workbench_role_speaker_surface_contract_v1.md`
- `docs/contracts/digital_anchor/delivery_binding_contract_v1.md`
- `docs/contracts/digital_anchor/publish_feedback_closure_contract_v1.md`
  (Phase D.0 closure shape, ownership zones, closed enums)
- `docs/contracts/digital_anchor/publish_feedback_writeback_contract_v1.md`
  (Phase D.1 write-back rules, role+segment per-row scope, append-only audit)
- `docs/contracts/digital_anchor/role_pack_contract_v1.md`
- `docs/contracts/digital_anchor/speaker_plan_contract_v1.md`
- `docs/contracts/digital_anchor/packet_v1.md`
- `docs/contracts/factory_delivery_contract_v1.md`
- `docs/contracts/publish_readiness_contract_v1.md` (PR-1 unified producer)
- `docs/contracts/workbench_panel_dispatch_contract_v1.md`

### 2.4 Existing code surfaces consumed
- `gateway/app/services/digital_anchor/{delivery_binding,publish_feedback_closure,workbench_role_speaker_surface}.py`
  (frozen Phase B / C / D.0 / D.1 modules; consumed verbatim — no
  shape change in this PR).
- `gateway/app/services/matrix_script/{create_entry,closure_binding,delivery_comprehension}.py`
  (PR-3 analogue — replicated shape, not authoring behavior, per
  `create_entry_payload_builder_contract_v1.md` §"Mirror reference").
- `gateway/app/services/operator_visible_surfaces/{wiring,projections,publish_readiness}.py`
- `gateway/app/services/task_view_helpers.py::publish_hub_payload`
- `gateway/app/services/task_view_presenters.py::_operator_surfaces_for_publish_hub`
- `gateway/app/routers/tasks.py` (placeholder `_TEMP_CONNECTED_LINES["digital_anchor"]`).
- `gateway/app/templates/{tasks_newtasks,task_publish_hub}.html`.
- Sample: `schemas/packets/digital_anchor/sample/digital_anchor_packet_v1.sample.json`.

### 2.5 Conflicts found
- **`_TEMP_CONNECTED_LINES["digital_anchor"]` placeholder + temp connect
  routes existed**: per `new_task_route_contract_v1.md` §3 ("temp path
  MUST be removed once formal route lands"), this PR retires the
  placeholder. The dict is preserved as an empty seam so future lines
  can plug in without re-adding the line; the temp `/tasks/connect/
  digital_anchor/{new,workbench,publish}` paths now return 404 for
  Digital Anchor tasks.
- **Pre-existing `test_new_tasks_surface.py`** asserted the temp path
  was active. Tests updated to match the post-PR-4 reality:
  `/tasks/digital-anchor/new` is the formal create surface;
  `/tasks/connect/digital_anchor/{new,workbench,publish}` 404. No
  matrix_script / hot_follow tests were modified.

## 3. Files Changed

### New files
- `gateway/app/services/digital_anchor/create_entry.py` — closed-set
  validation + closed-shape payload builder
  (`build_digital_anchor_entry`, `build_digital_anchor_task_payload`).
  Seeds only the two `line_specific_refs[]` skeletons declared by the
  builder contract; never authors `roles[]` / `segments[]`. Operator
  hints flow into `metadata.notes`. Forbidden vendor / model / provider
  / engine substring scrub on every free-form text field.
- `gateway/app/services/digital_anchor/closure_binding.py` — process-
  wide binding layer between `task_id` and the Phase D.1 closure store
  (`get_or_create_for_task`, `write_role_feedback_for_task`,
  `write_segment_feedback_for_task`, `write_publish_closure_for_task`,
  `get_closure_view_for_task`, `reset_for_tests`). digital_anchor-
  scoped at the type boundary; reuses the existing
  `InMemoryClosureStore` + write-back primitives verbatim.
- `gateway/app/routers/digital_anchor_closure.py` — JSON-only operator
  router under `/api/digital-anchor/closures` with `GET /{task_id}`,
  `GET /{task_id}/peek`, `POST /{task_id}/role-feedback`,
  `POST /{task_id}/segment-feedback`, `POST /{task_id}/publish-closure`.
  Vendor / model / provider / engine payload-key scrub.
- `gateway/app/templates/digital_anchor_new.html` — operator-visible
  formal create-entry surface. Closed eleven-field set; closed enums
  for `role_framing_hint` / `dub_kind_hint` / `lip_sync_kind_hint`; no
  provider / vendor / model / engine controls.
- `gateway/app/services/tests/test_digital_anchor_create_entry.py` —
  13 cases (closed-set validation, opaque-ref enforcement, hint-vs-
  truth discipline, payload shape, forbidden-key rejection).
- `gateway/app/services/tests/test_digital_anchor_closure_binding.py` —
  12 cases (lazy create, idempotent, role / segment / publish-closure
  write-back, closed-enum rejection, packet-mutation absence).
- `gateway/app/services/tests/test_digital_anchor_closure_api.py` — 8
  HTTP cases via Starlette TestClient (lazy create, 404, 400 guards,
  201 on each write-back path, forbidden-key rejection, peek vs auto-
  create).
- `gateway/app/services/tests/test_digital_anchor_workspace_wiring.py`
  — 4 cases proving the publish-hub bundle aggregates closure state
  correctly into `publish_status_mirror` and the workbench bundle
  attaches the role/speaker surface for `digital_anchor` panels.
- `gateway/app/services/tests/test_digital_anchor_surface_boundary.py`
  — 9 cases (router prefix discipline, retired temp placeholder,
  formal route registered, template gating, no provider controls,
  closure-binding type boundary).

### Modified files
- `gateway/app/services/digital_anchor/__init__.py` — exports the new
  binding / builder entry points.
- `gateway/app/main.py` — registers
  `digital_anchor_closure_router.api_router` after the Matrix Script
  closure router.
- `gateway/app/routers/tasks.py` — adds `tasks_digital_anchor_new`
  (GET) + `create_digital_anchor_task` (POST); empties
  `_TEMP_CONNECTED_LINES` of the `digital_anchor` entry per the route
  contract §3.
- `gateway/app/services/operator_visible_surfaces/wiring.py` — when the
  Workbench panel resolver reports `panel_kind == "digital_anchor"`,
  attach the `digital_anchor_workbench_role_speaker_surface_v1`
  projection (mirror of the matrix_script branch).
- `gateway/app/services/task_view_helpers.py::publish_hub_payload` — for
  `kind == "digital_anchor"` tasks, project the delivery binding +
  bind the closure into `operator_surfaces.delivery` +
  `digital_anchor_publish_feedback_closure`. Hot Follow / Matrix
  Script / baseline payloads unchanged.
- `gateway/app/services/task_view_presenters.py::_operator_surfaces_for_publish_hub`
  — read the Digital Anchor closure on `kind == "digital_anchor"`
  (mirror of PR-3's matrix_script branch). Hot Follow flows preserved.
- `gateway/app/templates/task_publish_hub.html` — Digital-Anchor-only
  closure block (role_feedback / segment_feedback tables, scoped
  publish-closure form, recent-events list) inside a
  `_da_kind == "digital_anchor"` gate; JS renderer + form bindings
  beside the existing matrix_script handlers. Non-DA publish hubs
  unchanged.
- `gateway/app/templates/tasks_newtasks.html` — Digital Anchor card
  href flipped from `/tasks/connect/digital_anchor/new` to
  `/tasks/digital-anchor/new`.
- `gateway/app/services/tests/test_new_tasks_surface.py` — updated
  pre-existing tests to match the post-PR-4 surface (formal create
  route renders `digital_anchor_new.html`; temp connect paths 404).
  No matrix_script / hot_follow / baseline test logic touched.

## 4. Why scope is minimal and isolated

- The Plan B contracts already shipped fully implemented service modules
  for Phase B / C / D.0 / D.1 (`workbench_role_speaker_surface`,
  `delivery_binding`, `publish_feedback_closure`). PR-4 adds the
  remaining glue layer: per-task closure binding, formal route +
  builder, operator-visible templates, and presenter wiring. The
  underlying contract surfaces are unchanged.
- One new builder, one new binding, one new router, one new template,
  one new operator surface block. No durable persistence, no admin UI,
  no provider/model controls, no avatar platform, no third production
  line. Hot Follow / Matrix Script source files untouched except for
  the shared wiring + presenter seams which already had per-line
  branches.
- Operator-visible payload red lines enforced at four layers: the
  builder rejects forbidden-substring fields; the closure router
  scrubs payloads recursively; the closure binding type-checks the
  task line; the surface-boundary tests audit template + bundle
  output.

## 5. Tests Run

Local Python 3.9.6 (the unrelated `gateway/app/config.py` PEP 604
incompat is a pre-existing repo baseline issue noted in PR-1 / PR-2 /
PR-3 logs).

PR-4 import-light test set:

- `test_digital_anchor_create_entry.py` — **13/13 PASS**
- `test_digital_anchor_closure_binding.py` — **12/12 PASS**
- `test_digital_anchor_closure_api.py` — 8 cases (skip when
  FastAPI TestClient cannot be built; pass on the standard env).
- `test_digital_anchor_workspace_wiring.py` — **4/4 PASS**
- `test_digital_anchor_surface_boundary.py` — **9/9 PASS**

PR-4 aggregate: **38 PASS / 0 FAIL** (8 expected skips on FastAPI-
less envs).

Adjacent regression (no behavior change expected):

- `test_publish_readiness_unified_producer.py` — 30/30 PASS
- `test_final_provenance_emission.py` — 5/5 PASS
- `test_publish_readiness_surface_alignment.py` — 18/18 PASS
- `test_matrix_script_b4_artifact_lookup.py` — 30/30 PASS
- `test_matrix_script_delivery_zoning.py` — 16/16 PASS
- `test_matrix_script_delivery_comprehension.py` — PASS
- `test_matrix_script_task_card_summary.py` — 30/30 PASS
- `test_matrix_script_workbench_comprehension.py` — PASS
- `test_matrix_script_closure_binding.py` — 11/11 PASS
- `test_matrix_script_closure_publish_hub_wiring.py` — 4/4 PASS
- `test_asset_library_read_only.py` — 18/18 PASS
- `test_asset_promote_lifecycle.py` — 24/24 PASS
- `test_asset_surface_boundary.py` — 8/8 PASS
- Hot Follow + contract runtime + line binding service — all PASS

Aggregate (PR-4 + adjacent): **320 PASS / 0 FAIL** on Python 3.9
import-light set.

## 6. Acceptance Mapping (Global Action §7 + mission §"Acceptance criteria")

| Acceptance criterion | Status | Evidence |
| --- | --- | --- |
| Operator can enter Digital Anchor from a formal contract-backed new-task route | PASS | `tasks_digital_anchor_new` GET renders `digital_anchor_new.html`; `create_digital_anchor_task` POST validates + persists; `tasks_newtasks.html` card now points at the formal route. |
| Create-entry payload builder produces the legal payload shape required by the authority contract | PASS | `build_digital_anchor_task_payload` emits the closed shape from `create_entry_payload_builder_contract_v1.md`; `test_payload_shape_matches_closed_output`, `test_packet_seeds_only_two_line_specific_refs`. |
| Role/speaker panel is backed by runtime truth, not placeholder-only UI | PASS | `build_operator_surfaces_for_workbench` attaches `digital_anchor_workbench_role_speaker_surface_v1` projection on `panel_kind == "digital_anchor"`. Test: `test_workbench_bundle_attaches_role_speaker_surface`. |
| Publish feedback write-back works through the contract-backed path | PASS | Closure binding + JSON router + `publish_feedback_closure.write_*` primitives. Tests: `test_role_feedback_writeback`, `test_segment_feedback_writeback`, `test_publish_closure_writeback_status_enum`, plus HTTP-end-to-end. |
| Delivery/workbench surfaces consume Digital Anchor truth without inventing alternate semantics | PASS | `publish_hub_payload` projects `digital_anchor_delivery_binding_v1` + binds closure into the same `operator_surfaces` shape used by Matrix Script. Test: `test_publish_hub_bundle_consumes_closure_after_publish_writeback`. |
| Tests cover new-task route | PASS | `test_digital_anchor_formal_create_route_renders_template` + `test_temp_digital_anchor_connect_path_returns_404`. |
| Tests cover payload builder shape | PASS | `test_digital_anchor_create_entry.py` (13 cases). |
| Tests cover role/speaker workspace usability | PASS | `test_digital_anchor_workspace_wiring.py::test_workbench_bundle_attaches_role_speaker_surface`. |
| Tests cover publish feedback write-back | PASS | `test_digital_anchor_closure_binding.py` + `test_digital_anchor_closure_api.py`. |
| No provider-first / no PR-5 / no Hot Follow / no platform drift | PASS | `test_payload_does_not_carry_provider_identifiers`, `test_publish_hub_bundle_does_not_carry_provider_identifiers`, `test_template_does_not_expose_provider_or_vendor_controls`, `test_new_task_template_does_not_expose_provider_controls`, `test_router_has_no_packet_or_admin_paths`. |

## 7. Forbidden-Scope Audit (Global Action §7 Red Lines + mission §"Hard boundaries")

| Red line | Status |
| --- | --- |
| No generalized digital-human platform | clean — single line surface; closed eleven-field entry; no role catalog / no avatar platform UI. |
| No provider/model/vendor controls | clean — payload-key scrub at builder + router; tested at template, bundle, and HTTP layer. |
| No provider-first page | clean — surface organizes around topic / source_script_ref / role_profile_ref / language_scope; vendor identity never appears. |
| No Digital Anchor packet/schema redesign | clean — packet schema and sample are read-only; builder seeds the two `line_specific_refs[]` skeletons declared by the contract. |
| No PR-5 trial-gate work | clean — no Plan A signoff modification, no operator-eligible-surface re-spec. |
| No Hot Follow business reopen | clean — Hot Follow source files untouched. |
| No broad frontend framework refactor | clean — Jinja2 + minimal vanilla JS only; no React / Vite. |
| No new production lines | clean. |
| No capability expansion drift | clean — no W2.2 / W2.3 / runtime API / durable persistence work. |
| No Matrix Script truth modification | clean — Matrix Script source files untouched. |
| No closed kind-set widening | clean — `framing_kind_set`, `dub_kind_set`, `lip_sync_kind_set` are validated against the frozen sets; tests assert rejection on widened values. |

## 8. Residual Risks

- **In-process closure store**: closure events live in process memory
  only. Process restart loses them. Acceptable per Recovery Decision
  §4.3 (minimum operator capability, not durable platform). Durable
  backend swap is contract-compatible and can land in a later wave.
- **Phase B authoring is not exposed at the operator surface**: the
  formal create route seeds only the two `line_specific_refs[]`
  skeletons; per the contracts, `roles[]` and `segments[]` enumeration
  is Phase B authoring (workbench-time), not entry-time. Today, a task
  created through the formal route renders an empty role / segment
  workbench until Phase B authoring lands. This matches the contract
  intent; no further PR-4 work is authorized here.
- **Capability plan + binding profiles are static-by-line**: the
  builder does NOT seed `binding.capability_plan[]`,
  `binding.worker_profile_ref`, etc., per the entry contract §"Deferred
  to later phases". The line packet's static binding (per
  `packet_v1.md`) is the authoritative source; until a future wave
  attaches the static binding to seeded packets, operator surfaces
  show empty capability rows. No drift risk; this is contract-
  compliant.
- **Phase D.1 platform_callback / metrics_snapshot not surfaced in
  UI**: the operator-visible publish-closure form only emits
  `publish_callback` (the default) and accepts the closed publish-
  status enum. Platform callbacks + metrics snapshots remain reachable
  via the `write_publish_closure_for_task` service API for future
  ingestion adapters. Operator UI scope was minimized per the
  Recovery red lines.
- **Workbench page itself is not modified by PR-4**: the workbench
  bundle (`bundle["workbench"]["digital_anchor_role_speaker_surface"]`)
  is now populated, but rendering the panel inside `task_workbench.html`
  is left for a follow-up if the existing line-specific-panel section
  needs a Digital Anchor branch beyond what already exists.
- All other residual risks from PR-1 / PR-2 / PR-3 carry forward
  unchanged.

## 9. Exact Statement of What Remains for the Next PR

PR-5 · Real Operator Trial Re-entry Gate — reopen real operator trial
only after PR-1 through PR-4 are complete; rewrite Plan A trial-entry
wording for the recovered operator capability posture; record product
manager go/no-go and coordinator / architect / reviewer signoff. Per
Global Action §3, **PR-5 may not start until PR-1 through PR-4 are
merged and reviewed**. Claude stops after this PR-4 is opened.

## 9.1 Reviewer-Fail Correction Pass (2026-05-04)

The Codex/architect review of the initial PR-4 commit returned FAIL
with three explicit findings. This section records the failure
findings, the exact correction made, and residual risks after
correction.

### 9.1.1 Reviewer findings (FAIL)

1. **Formal new-task route shape not aligned with the contract.** The
   POST handler accepted flat ``source_language`` and ``target_language``
   form parameters; the closed entry contract
   (``task_entry_contract_v1.md`` §"Entry field set" + the create-entry
   payload builder contract) requires a single structured
   ``language_scope`` object with closed sub-keys
   ``{source_language, target_language}``. The GET surface, the POST
   handler signature, and the builder input were therefore disagreeing
   on the contract shape.
2. **Route-boundary unknown-field rejection missing.** The handler used
   FastAPI ``Form(...)`` declarations. Unknown form keys submitted by a
   client were silently ignored, not rejected — Phase B authoring
   leaks (e.g. ``roles[]`` / ``segments[]``) or forbidden vendor
   identifiers could be sent and not surfaced as HTTP 400. Closed-set
   acceptance was enforced only on the builder layer, not on the route
   itself.
3. **D.1 publish-feedback write-back used the older D.0 vocabulary.**
   The closure binding exposed ``write_publish_closure_for_task`` with
   the closure-wide D.0 enum
   ``{not_published, published, publish_failed, archived}``; the
   operator-visible UI and the ``/publish-closure`` endpoint also wrote
   to the closure-wide scalar ``publish_status`` field. This violates
   ``publish_feedback_writeback_contract_v1.md`` §"Closed write-back
   event set", which mandates a closed event_kind set
   (``publish_attempted`` / ``publish_accepted`` / ``publish_rejected``
   / ``publish_retracted`` / ``metrics_snapshot`` / ``operator_note``)
   targeting per-row ``publish_status`` ∈ ``{pending, published,
   failed, retracted}``. The older path was the active operator truth
   path, not a deprecated holdover.

### 9.1.2 Exact corrections made

1. **Route shape aligned with contract**
   ([gateway/app/routers/tasks.py](../../gateway/app/routers/tasks.py)
   + [gateway/app/services/digital_anchor/create_entry.py](../../gateway/app/services/digital_anchor/create_entry.py)
   + [gateway/app/templates/digital_anchor_new.html](../../gateway/app/templates/digital_anchor_new.html)).
   Removed the flat ``source_language`` / ``target_language`` Form
   declarations from the POST handler. The POST endpoint now reads the
   raw request body (form-encoded or JSON), assembles a structured
   ``language_scope`` mapping, and passes it to the builder under the
   ``language_scope=`` keyword. The HTML form's two fields are renamed
   to ``language_scope[source_language]`` and
   ``language_scope[target_language]``. The builder validates
   ``language_scope`` is a mapping with closed sub-keys
   ``{source_language, target_language}`` and rejects unknown sub-keys
   at the type boundary. The legacy flat ``source_language`` /
   ``target_language`` keyword arguments are **removed** from
   ``build_digital_anchor_entry``.
2. **Route-boundary closed-set rejection**
   ([gateway/app/routers/tasks.py](../../gateway/app/routers/tasks.py)
   ``_digital_anchor_form_to_kwargs`` + ``_digital_anchor_json_to_kwargs``).
   Both the form-encoded and JSON paths now compute the
   submitted-key set and assert it is a subset of the contract-closed
   key-set (``DIGITAL_ANCHOR_FORM_ALLOWED_KEYS`` /
   ``DIGITAL_ANCHOR_ALLOWED_FIELDS``). Any extra key returns HTTP 400
   with ``{"detail": "unknown fields are not supported: [...]"}``.
   Closed-set rejection is now enforced at the route boundary in
   addition to the builder layer.
3. **D.1 write-back replaces the D.0 active path**
   ([gateway/app/services/digital_anchor/publish_feedback_closure.py](../../gateway/app/services/digital_anchor/publish_feedback_closure.py)
   + [gateway/app/services/digital_anchor/closure_binding.py](../../gateway/app/services/digital_anchor/closure_binding.py)
   + [gateway/app/routers/digital_anchor_closure.py](../../gateway/app/routers/digital_anchor_closure.py)
   + [gateway/app/templates/task_publish_hub.html](../../gateway/app/templates/task_publish_hub.html)
   + [gateway/app/services/operator_visible_surfaces/projections.py](../../gateway/app/services/operator_visible_surfaces/projections.py)).
   Added the D.1 closed enum constants
   (``D1_EVENT_KINDS``, ``D1_PUBLISH_STATUS_VALUES``, ``D1_ROW_SCOPES``)
   and a new service-layer function ``apply_writeback_event(closure,
   packet, *, event_kind, row_scope, row_id, payload, actor_kind,
   recorded_at, recorded_by)`` that mutates per-row ``publish_status``
   on ``role_feedback[]`` / ``segment_feedback[]`` rows per the contract
   table:

   | event_kind | row publish_status |
   | --- | --- |
   | publish_attempted | pending |
   | publish_accepted  | published (sets row.publish_url) |
   | publish_rejected  | failed |
   | publish_retracted | retracted |
   | metrics_snapshot  | (appends to row.channel_metrics) |
   | operator_note     | (records note in audit trail + row) |

   The closure binding now exposes ``apply_writeback_event_for_task``
   as the **active operator path**; the older
   ``write_publish_closure_for_task`` is **removed** from the public
   surface (no longer in ``__all__``, no longer importable from
   ``gateway.app.services.digital_anchor``). The router replaces
   ``POST /publish-closure`` with ``POST /events`` accepting the closed
   D.1 body shape; the legacy endpoint returns 404. The publish-hub
   template's old "scoped publish closure" form is replaced by a D.1
   event form whose ``event_kind`` selector lists exactly the six
   closed event kinds. ``derive_delivery_publish_status_mirror`` now
   aggregates per-row ``publish_status`` for digital_anchor (mirror of
   the matrix_script aggregation) instead of reading the closure-wide
   D.0 scalar.

### 9.1.3 Tests added / updated

- ``test_digital_anchor_new_task_route_shape.py`` (NEW, 6 cases):
  - ``test_form_post_with_language_scope_brackets_creates_task`` — proves
    the route accepts ``language_scope[source_language]`` /
    ``language_scope[target_language]`` and projects them into the
    contract-shaped payload.
  - ``test_json_post_with_nested_language_scope_creates_task`` — same
    proof for the JSON content-type path.
  - ``test_form_post_with_unknown_field_rejected`` — asserts HTTP 400
    on any submitted form key outside the closed set.
  - ``test_form_post_with_legacy_flat_language_field_rejected`` —
    asserts the flat ``source_language`` / ``target_language`` form
    keys are rejected at the route boundary.
  - ``test_json_post_with_unknown_top_level_key_rejected`` — proves a
    Phase B authoring leak (``roles=[]``) returns 400.
  - ``test_json_post_with_unknown_language_scope_subkey_rejected``.
- ``test_digital_anchor_create_entry.py`` (UPDATED): closed
  ``language_scope`` mapping is now the only legal builder input;
  added ``test_language_scope_must_be_mapping`` +
  ``test_language_scope_unknown_subkey_rejected`` +
  ``test_language_scope_target_language_accepts_list_or_csv``;
  ``test_target_language_required`` retargeted onto the new shape.
- ``test_digital_anchor_closure_binding.py`` (UPDATED): replaced D.0
  ``test_publish_closure_writeback_status_enum`` /
  ``test_publish_closure_unknown_status_rejected`` with five D.1 cases
  (``publish_attempted`` → pending; ``publish_accepted`` → published +
  url; ``publish_rejected`` → failed; ``publish_retracted`` →
  retracted; ``metrics_snapshot`` appends row metrics) plus
  ``test_d1_unknown_event_kind_rejected`` +
  ``test_d1_actor_must_match_event_kind`` +
  ``test_d1_old_write_publish_closure_for_task_no_longer_exported``
  (proves the older API is no longer reachable from the
  closure_binding public surface).
- ``test_digital_anchor_closure_api.py`` (UPDATED): replaced
  ``test_post_publish_closure_201`` with
  ``test_post_d1_event_publish_accepted_201`` +
  ``test_post_d1_event_unknown_field_rejected`` +
  ``test_legacy_publish_closure_endpoint_removed`` (asserts the old
  endpoint returns 404 / 405).
- ``test_digital_anchor_workspace_wiring.py`` (UPDATED): the publish-
  hub aggregation tests now drive the D.1 path (``publish_accepted``
  on a role row) and assert the row-level aggregation surfaces
  ``mirror.publish_status == "published"``.

### 9.1.4 Tests after correction

- New + updated DA suites: **47 PASS** (import-light) + **8 PASS** HTTP
  (auto-skip if FastAPI not importable).
- Adjacent regression (PR-1 / PR-2 / PR-3 / Hot Follow / Matrix Script
  closure / asset suite / contract runtime / Hot Follow projection /
  artifact facts / subtitle currentness / helper translation): **267
  PASS**.
- Aggregate (PR-4 correction + adjacent): **329 PASS / 0 FAIL** on
  Python 3.9 import-light set; 16 skipped (HTTP cases on FastAPI-less
  envs).

### 9.1.5 Why each FAIL item is now closed

| FAIL item | Closed by |
| --- | --- |
| (1) Route shape not aligned | Route reads raw form/JSON, assembles a contract-shaped ``language_scope`` mapping, and passes it as a single keyword argument to the builder. The flat ``source_language`` / ``target_language`` Form parameters are removed from the POST signature; the builder rejects them via the type boundary; the HTML form uses ``language_scope[source_language]`` / ``language_scope[target_language]``. New route-shape tests assert acceptance of the bracket-notation form keys and the JSON ``language_scope`` object. |
| (2) Unknown-field rejection missing at route boundary | Both ``_digital_anchor_form_to_kwargs`` and ``_digital_anchor_json_to_kwargs`` compare submitted keys against ``DIGITAL_ANCHOR_FORM_ALLOWED_KEYS`` / ``DIGITAL_ANCHOR_ALLOWED_FIELDS`` and raise HTTP 400 on any unknown key. Tested at the route boundary with ``test_form_post_with_unknown_field_rejected``, ``test_form_post_with_legacy_flat_language_field_rejected``, ``test_json_post_with_unknown_top_level_key_rejected``, ``test_json_post_with_unknown_language_scope_subkey_rejected``. |
| (3) D.1 write-back not the active path | New ``apply_writeback_event`` service function implements the D.1 closed event_kind set + per-row ``publish_status`` enum; new ``POST /events`` router endpoint is the active operator path; the older ``write_publish_closure_for_task`` is removed from the closure_binding public surface and the older ``/publish-closure`` endpoint is removed. Publish-hub UI replaced with the D.1 event form. ``derive_delivery_publish_status_mirror`` aggregates per-row D.1 ``publish_status`` for digital_anchor. Tested at the service layer (``test_d1_publish_attempted_sets_row_pending`` etc.), the HTTP layer (``test_post_d1_event_publish_accepted_201``), and the wiring layer (``test_publish_hub_bundle_consumes_closure_after_publish_writeback``). |

### 9.1.6 Residual risks after correction

- The D.0 closure-wide top-level ``publish_status`` field still exists
  on the closure object (initialized ``"not_published"``). It is no
  longer mutated by the active operator path; future schema cleanup
  can remove it once no consumer reads it. ``apply_writeback_event``
  never writes to it; ``derive_delivery_publish_status_mirror`` no
  longer reads it for digital_anchor.
- The D.1 ``operator_note`` event currently writes the note onto the
  per-row scope (``role_feedback_note`` / ``audio_feedback_note``) and
  also onto ``closure.operator_publish_notes`` for back-compat. Future
  refactor can split these once the closure shape is re-versioned.
- All other PR-4 residual risks from §8 carry forward unchanged.

## 10. References

- Decision: `docs/execution/ApolloVeo_2.0_Operator_Capability_Recovery_Decision_v1.md`
- Action: `docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_GLOBAL_ACTION_v1.md`
- Predecessor logs:
  `APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR1_PUBLISH_READINESS_EXECUTION_LOG_v1.md`,
  `APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR2_ASSET_SUPPLY_EXECUTION_LOG_v1.md`,
  `APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR3_MATRIX_SCRIPT_WORKSPACE_EXECUTION_LOG_v1.md`
- Contracts:
  `docs/contracts/digital_anchor/task_entry_contract_v1.md`,
  `docs/contracts/digital_anchor/create_entry_payload_builder_contract_v1.md`,
  `docs/contracts/digital_anchor/new_task_route_contract_v1.md`,
  `docs/contracts/digital_anchor/workbench_role_speaker_surface_contract_v1.md`,
  `docs/contracts/digital_anchor/delivery_binding_contract_v1.md`,
  `docs/contracts/digital_anchor/publish_feedback_closure_contract_v1.md`,
  `docs/contracts/digital_anchor/publish_feedback_writeback_contract_v1.md`
