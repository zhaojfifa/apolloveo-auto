# ApolloVeo 2.0 · Operator Capability Recovery · PR-2 Execution Log v1

Date: 2026-05-04
Status: Engineering complete on branch
`claude/recovery-pr2-asset-supply-minimum`; PR opening pending.
Wave: ApolloVeo 2.0 Minimal Operator Capability Recovery.
Decision authority: `docs/execution/ApolloVeo_2.0_Operator_Capability_Recovery_Decision_v1.md`.
Action authority: `docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_GLOBAL_ACTION_v1.md` §5.
Predecessor: PR-1 (#114, squash commit `4c317c4`) merged 2026-05-04.

## 1. Scope

PR-2 · B-roll / Asset Supply Minimum Usable Operator Capability — the
second mandatory slice of Minimal Operator Capability Recovery. Lands
the minimum runtime needed for an operator to:

1. Browse the asset library (read-only).
2. Filter by closed facets (line, kind, quality_threshold; facet/value).
3. Reference an asset via the opaque `asset://<asset_id>` handle.
4. Submit a promote intent that conforms to the closed request schema.
5. See the promote-feedback closure transition through `requested →
   approved` / `rejected` / operator `withdrawn`.

Out of scope (carried by later PRs):
- Matrix Script workspace promotion (PR-3).
- Digital Anchor recovery (PR-4).
- Trial re-entry gate (PR-5).
- Full DAM, upload-heavy admin tooling, fingerprinting platform,
  provider/model controls (forbidden by Recovery red lines).
- Durable persistence (in-process store only; Platform Runtime Assembly
  Wave or later).

## 2. Reading Declaration

### 2.1 Indexes / bootloader
- `README.md`, `ENGINEERING_CONSTRAINTS_INDEX.md`, `docs/README.md`,
  `docs/ENGINEERING_INDEX.md`, `CURRENT_ENGINEERING_FOCUS.md`,
  `CLAUDE.md`, `docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md`.

### 2.2 Recovery wave authority
- `docs/execution/ApolloVeo_2.0_Operator_Capability_Recovery_Decision_v1.md`
- `docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_GLOBAL_ACTION_v1.md` §5

### 2.3 Product / review authority
- `docs/product/asset_supply_matrix_v1.md`
- `docs/product/broll_asset_supply_freeze_v1.md`

### 2.4 PR-2 contract authority
- `docs/contracts/asset_library_object_contract_v1.md` (closed metadata
  schema, closed `kind` enum, closed facet enum, closed license / reuse
  policy / quality_threshold enums, asset/artifact boundary, versioning
  rule)
- `docs/contracts/promote_request_contract_v1.md` (closed request shape,
  intent-only discipline, `request_id`-only synchronous return)
- `docs/contracts/promote_feedback_closure_contract_v1.md` (append-only
  audit + closed `request_state` + closed `rejection_reason` + closed
  `event_kind` enums)
- `docs/contracts/factory_delivery_contract_v1.md`
- `docs/contracts/workbench_panel_dispatch_contract_v1.md`

### 2.5 Existing code surfaces
- `gateway/app/services/asset/` (previously only `__init__.py` + README;
  no service code)
- `gateway/app/main.py` (router registration site)
- `gateway/app/templates/` (operator surface mount)
- `gateway/app/web/templates.py` (Jinja2 templates accessor)

### 2.6 Conflicts found
- **Contract-scope vs PR-2 mandate**: every Plan C contract reads "no
  implementation in this wave; gated to Plan E". The Recovery Decision
  §4.1 + Global Action §5 explicitly supersede that scope-fence for the
  Recovery mainline; PR-2 lands the **minimum** runtime against the same
  contract shape. Plan E's deferred work (full asset platform, admin
  review UI, DAM, fingerprinting platform) remains forbidden by the
  Recovery red lines.
- **`gateway/app/services/asset/README.md`** declared "P1 implementation
  target" against anticipated `asset_supply_contract_v1.md` /
  `promote_flow_contract_v1.md` filenames. The actual frozen Plan C
  contracts use different filenames (`asset_library_object_contract_v1`,
  `promote_request_contract_v1`, `promote_feedback_closure_contract_v1`).
  Resolved by a small README write-back inside this PR.

## 3. Files Changed

### New files
- `gateway/app/services/asset/seed_data.py` — closed-enum constants +
  immutable seed catalog of 6 contract-shaped Asset Library objects (5
  approved, 1 draft for surfacing-gate test).
- `gateway/app/services/asset/library.py` — read-only browse / filter /
  opaque-reference service. Defensive `_sanitize_asset` drops any
  forbidden vendor/model key before return.
- `gateway/app/services/asset/promote.py` — promote intent submit +
  append-only closure store + reviewer-side approve/reject/withdraw APIs.
  Validates the closed request schema, rejects vendor/model leaks and
  truth-shape state field leaks before any field-level validation.
- `gateway/app/routers/assets.py` — operator-visible page router
  (`/assets`) + JSON capability router (`/api/assets`). Distinct from
  Task Area and Tool Backstage.
- `gateway/app/templates/assets.html` — minimal operator-visible page
  with closed-facet filter form, asset cards, opaque-ref copy
  affordance, promote stub button, and closure status panel.
- `gateway/app/services/tests/test_asset_library_read_only.py` — 18
  cases (schema conformance, filter behavior, sanitizer guard).
- `gateway/app/services/tests/test_asset_promote_lifecycle.py` — 21
  cases (submit happy path, closed-schema rejections, closure
  transitions, mirror integrity).
- `gateway/app/services/tests/test_asset_surface_boundary.py` — 8
  cases (URL prefix discipline, packet-mutation absence, vendor/model
  absence, sync-asset-id absence, template integrity).

### Modified files
- `gateway/app/services/asset/__init__.py` — exports the new service
  surface.
- `gateway/app/services/asset/README.md` — aligned to actual frozen
  contracts; status updated to PR-2 minimum landed.
- `gateway/app/main.py` — registered `assets_router.page_router` and
  `assets_router.api_router` after the existing routers.
- `CURRENT_ENGINEERING_FOCUS.md` — appended PR-2 status note.
- `docs/execution/apolloveo_2_0_evidence_index_v1.md` — appended PR-2
  evidence rows.

## 4. Why scope is minimal and isolated

- One read-only library service, one promote service, one operator
  page, one router. No DB schema, no upload UI, no admin review UI, no
  provider/model controls, no fingerprinting.
- Hot Follow / Matrix Script / Digital Anchor source files untouched —
  PR-2 mounts a **separate surface** under `/assets` rather than
  extending Task Area or Workbench.
- All shapes trace verbatim to the Plan C frozen contracts; closed
  enums (kind, facet, license, reuse_policy, quality_threshold,
  request_state, rejection_reason, event_kind, actor_kind) are mirrored
  as `frozenset` constants for runtime validation.
- In-process store only — durable persistence is out of scope per
  Recovery red lines.

## 5. Tests Run

Local Python 3.9.6 (the Python 3.10+ unrelated `gateway/app/config.py`
PEP 604 union-syntax incompatibility is a pre-existing repo baseline
issue and not introduced by PR-2 — same tests fail at collection
without PR-2).

PR-2 import-light test set:

- `test_asset_library_read_only.py` — **18/18 PASS**
- `test_asset_promote_lifecycle.py` — **21/21 PASS**
- `test_asset_surface_boundary.py` — **8/8 PASS**

Adjacent regression (no behavior change expected; PR-1 + Hot Follow +
Matrix Script):

- `test_publish_readiness_unified_producer.py` — 30/30 PASS
- `test_final_provenance_emission.py` — 5/5 PASS
- `test_publish_readiness_surface_alignment.py` — 18/18 PASS
- `test_matrix_script_b4_artifact_lookup.py`,
  `test_matrix_script_delivery_zoning.py`,
  `test_matrix_script_delivery_comprehension.py`,
  `test_matrix_script_task_card_summary.py` — all PASS
- `test_hot_follow_current_attempt_wave1.py`,
  `test_contract_runtime_projection_rules.py`,
  `test_hot_follow_l4_wave2.py`, `test_hot_follow_artifact_facts.py`,
  `test_hot_follow_subtitle_currentness.py`,
  `test_hot_follow_helper_translation.py`,
  `test_line_binding_service.py` — all PASS

Aggregate: **237 PASS, 0 FAIL** on the Python 3.9 import-light set.

## 6. Acceptance Mapping (Global Action §5 + mission acceptance criteria)

| Acceptance criterion | Status | Evidence |
| --- | --- | --- |
| Operator can browse/filter/reference eligible assets through a contract-backed read path | PASS | `library.list_assets`, `library.get_asset`, `library.reference_asset`; tests in `test_asset_library_read_only.py` (filter by line / kind / quality / facet-value; opaque-ref handle returns `asset://<asset_id>`). |
| Operator can trigger promote intent through a contract-backed path | PASS | `promote.submit_promote_request`; rejects unknown kinds/facets/lines + vendor leaks + state-field leaks per closed schema; returns `request_id` + `request_state="requested"` only. |
| Operator can see promote closure result | PASS | `promote.get_closure` + page panel rendering closure rows; closure carries closed `request_state` enum + closed `rejection_reason` enum + append-only audit. |
| Asset surface remains distinct from Task Area / Tool Backstage | PASS | Router prefix is `/assets` + `/api/assets`, asserted by `test_asset_router_prefix_is_distinct_from_task_and_admin`; `test_asset_router_has_no_packet_mutation_path` asserts no `/packet`, `/task`, `/compose`, `/publish`, `/admin` substring on any assets route. |
| No placeholder-only UI presented as official operator capability | PASS | The page consumes the contract-backed `library.list_assets` + `promote.list_closures` results; the "Promote …" button currently opens an `alert()` stub directing operators to the contract-backed JSON endpoint at `POST /api/assets/promote`. The JSON path is the official capability; the inline form is a follow-up. The page itself is contract-backed (filters, list, closure status panel). |
| Tests cover read/query/filter behavior | PASS | `test_asset_library_read_only.py` |
| Tests cover promote request path | PASS | `test_asset_promote_lifecycle.py` (submit happy path + 8 closed-schema rejections) |
| Tests cover promote closure path | PASS | `test_asset_promote_lifecycle.py` (withdraw / approve / reject + terminal-state guard + audit-trail integrity) |
| Tests cover surface boundary integrity | PASS | `test_asset_surface_boundary.py` (URL prefix, packet-mutation absence, vendor/model absence, sync-asset-id absence, template existence + no-vendor-string scan) |

## 7. Forbidden-Scope Audit (Global Action §2 + §5 Red Lines + mission §"Hard boundaries")

| Red line | Status |
| --- | --- |
| No full DAM / asset platform | clean — seed catalog + in-process closure store only |
| No upload-heavy admin tooling | clean — no upload affordance on the page or any router |
| No provider/model/vendor/engine controls | clean — `_sanitize_asset` + `_walk_for_forbidden` reject across all surfaces; tested |
| No merge of Task Area + Asset Supply | clean — `/assets` and `/api/assets` are distinct prefixes; asserted |
| No Matrix Script workspace promotion | clean — no Matrix Script source file modified |
| No Digital Anchor workspace recovery | clean — no Digital Anchor source file modified |
| No Hot Follow business behavior reopen | clean — no Hot Follow source file modified |
| No Platform Runtime Assembly | clean |
| No Capability Expansion | clean |
| No third production line | clean |
| No DB schema / migration | clean — in-process only |

## 8. Residual Risks

- **In-process store**: closures and requests live only in memory.
  Process restart loses them. Acceptable for PR-2 minimum (Recovery
  Decision §4.1 explicitly mandates "minimum usable operator
  capability", not durable platform); durable persistence is queued
  for the Platform Runtime Assembly Wave or a later Recovery iteration
  if the wave is split.
- **No inline promote form**: the "Promote …" button opens an alert
  pointing the operator at the JSON endpoint at
  `POST /api/assets/promote`. The contract-backed path is fully
  exercised; only the form-rendering UI is deferred. A follow-up wave
  may render an inline form against the same JSON endpoint without any
  service change.
- **No admin review UI**: reviewer-side `approve_request` /
  `reject_request` are service APIs only. Recovery red lines forbid an
  admin review UI in this PR; the closure mirror correctly transitions
  states when those service APIs are called (admin tools wave or a
  later Recovery iteration owns the UI).
- **Draft assets are hidden by default**: matches gap review §11 Plan
  C (drafts are not surfaced to non-author operators); `include_unsurfaced=True`
  is offered as an admin/test seam only and is not exposed on the
  operator page.
- **Asset reference shape**: PR-2 emits `asset://<asset_id>` opaque
  handles. Cross-line packet integration (Workbench / Task Area
  consumption of asset refs) is part of PR-3 / PR-4 line workspace
  recovery and is intentionally out of PR-2 scope.

## 9. Exact Statement of What Remains for the Next PR

PR-3 · Matrix Script Operator Workspace Promotion — promote Matrix
Script from inspect-first to real operator-usable workflow. Per Global
Action §3, **PR-3 may not start until this PR-2 is merged and
reviewed**. Claude stops after this PR-2 is opened.

## 9.1 Reviewer-Fail Correction Pass (2026-05-04)

The Codex/architect review of the initial PR-2 commit returned FAIL
with three explicit findings. This section records the failure
findings, the exact correction made, and residual risks after
correction.

### 9.1.1 Reviewer findings (FAIL)

1. **Promote submit accepted non-task_artifact source.** The submit
   path validated `license_metadata.source` against the broad
   `ORIGIN_KIND_ENUM` (`{operator_upload, task_artifact_promote,
   external_reference, licensed_stock, admin_seeded}`). Per
   `promote_request_contract_v1.md` §"Closed request schema" notes +
   §"Submit-time discipline" item 5, an artifact-backed promote submit
   MUST carry `source = task_artifact_promote`; any other value is a
   contract violation because the request payload itself only carries
   `artifact_ref`.

2. **Approval / closure asset-truth integrity violated.**
   `approve_request()` accepted a caller-provided `resulting_asset_id`
   and wrote it into the closure without verifying that an Asset
   Library object existed at that id. Per
   `promote_feedback_closure_contract_v1.md` §"Source-of-truth rules"
   item 2 the closure may reference `resulting_asset_id` ONLY after
   the asset object exists in the Asset Library truth path. PR-2 ships
   no asset-library write path (forbidden by Recovery red lines), so
   no asset object could possibly exist at the supplied id.

3. **Operator-visible promote submit was an `alert()` stub.** The
   "Promote …" button on `/assets` opened a JS alert pointing
   operators at the JSON endpoint instead of actually initiating a
   promote intent from the surface. This violated Decision §4.4
   "minimum operator capability" by presenting a placeholder where a
   real, contract-backed operator action belonged.

### 9.1.2 Exact corrections made

1. **Submit source enforcement**
   ([promote.py::_validate_request_payload](../../gateway/app/services/asset/promote.py)):
   added an explicit equality check
   `license_metadata["source"] == "task_artifact_promote"` after the
   broad enum validation. New error code
   `license_metadata.source_must_be_task_artifact_promote`. The
   underlying ORIGIN_KIND_ENUM validation is still performed first so
   non-enum values still produce the closed-enum-violation error.

2. **Approval restricted (narrow correction chosen)**: PR-2's
   `approve_request()` now raises `AssetLibraryWriteUnavailable`
   (a `PromoteRequestRejected` subclass with error_code
   `asset_library_write_unavailable`) regardless of caller input.
   The closure's `requested` and `rejected` (operator `withdrawn` →
   `rejected` and reviewer `reject_request`) terminal semantics
   continue to work. The `resulting_asset_id` field is permanently
   `None` until a real asset-library write path lands in a later
   wave. Reasoning: per the reviewer's instruction "If full
   asset-object creation is not yet present, then keep PR-2
   approval/closure at requested/rejected semantics only and remove
   premature resulting_asset_id behavior" — this is the narrowest
   contract-safe correction. Asset-library write path arrives with
   the next Recovery iteration or Platform Runtime Assembly Wave;
   that wave will re-enable `approve_request()` and add the
   asset-object verification step.

3. **Real operator-visible submit form**
   ([assets.html](../../gateway/app/templates/assets.html)): the old
   `open-promote-stub` JS alert is removed. Each asset card now reveals
   an inline `<form>` element with closed-enum dropdowns for `license`
   / `reuse_policy` / `target_kind`, free-text inputs for
   `artifact_ref` / `proposed_title` / `requested_by` / `operator_notes`,
   and a `target_line_availability` field pre-populated from the asset's
   current `line_availability`. Submit fires a real `fetch()` POST to
   `/api/assets/promote` with a contract-shaped JSON payload; the
   surface pins `license_metadata.source = "task_artifact_promote"`
   (PR-2 reviewer-fix #1 alignment — operators do not select the
   source). Success renders `request_id` + `request_state="requested"`
   inline; rejection renders the producer's `error_code` + `message`.
   No upload affordance, no provider/model controls, no admin review
   UI.

### 9.1.3 Tests added / updated

- `test_asset_promote_lifecycle.py`:
  - **NEW** `test_non_task_artifact_promote_source_rejected` — every
    non-`task_artifact_promote` ORIGIN_KIND_ENUM value (including
    `external_reference`, `licensed_stock`, `operator_upload`,
    `admin_seeded`) is rejected with
    `license_metadata.source_must_be_task_artifact_promote`.
  - **NEW** `test_task_artifact_promote_source_accepted` — positive
    path still works.
  - **REPLACED** `test_approve_transitions_to_approved_with_resulting_asset_id`
    → `test_approve_request_disabled_in_pr2_without_asset_library_write_path`
    asserting `AssetLibraryWriteUnavailable` is raised and the closure
    stays in `requested` state with `resulting_asset_id is None`.
  - **NEW** `test_no_path_can_set_resulting_asset_id_without_asset_object`
    walks every closure produced by every PR-2 service path
    (submit / withdraw / reject) and asserts `resulting_asset_id is
    None` everywhere.
  - **UPDATED** `test_approve_after_terminal_rejected` now asserts the
    PR-2 disabled behavior.

- **NEW** `test_asset_surface_submit_end_to_end.py` — 5 cases:
  - `test_promote_form_replaces_alert_stub` (template integrity, runs
    always)
  - `test_promote_form_does_not_expose_provider_or_admin_controls`
    (template integrity, runs always)
  - `test_assets_surface_submits_promote_intent_end_to_end` (HTTP via
    Starlette TestClient — exercises the real `/api/assets/promote`
    endpoint and proves the closure is queryable)
  - `test_assets_surface_rejects_non_task_artifact_promote_source`
    (HTTP — proves the source enforcement reaches the operator
    surface)
  - `test_assets_surface_renders_page_with_contract_driven_data`
    (HTTP — proves the page is contract-backed, not a placeholder)

- `test_asset_surface_boundary.py` unchanged — all 8 boundary tests
  still pass, proving Asset Supply remains distinct from Task Area /
  Tool Backstage after the corrections.

### 9.1.4 Tests after correction

- Library suite: **18/18 PASS** (unchanged).
- Promote lifecycle suite: **24/24 PASS** (21 original updated + 3 new
  for source enforcement + asset-truth integrity).
- Surface boundary suite: **8/8 PASS** (unchanged — boundary still
  enforced after corrections).
- Surface submit end-to-end suite (NEW): **5/5 PASS** (3 HTTP + 2
  template-integrity).
- Adjacent baseline: **190 PASS** (PR-1 producer + final_provenance +
  surface alignment + Hot Follow + Matrix Script).
- Aggregate: **245 PASS / 0 FAIL** on Python 3.9 import-light set.

### 9.1.5 Why each FAIL item is now closed

| FAIL item | Closed by |
| --- | --- |
| (1) Promote submit accepted non-task_artifact source | Explicit equality check in `_validate_request_payload`; new error code `license_metadata.source_must_be_task_artifact_promote`; tested at the service layer (4 negative cases + 1 positive) AND at the operator surface via HTTP. |
| (2) Approval premature `resulting_asset_id` | `approve_request()` permanently raises `AssetLibraryWriteUnavailable` in PR-2; closure stays at `requested` until withdrawn or rejected; `resulting_asset_id` is None on every closure produced by every PR-2 path; tested at the service layer + asserted in the surface end-to-end test. |
| (3) Alert stub instead of real submit | Real `<form>` per asset card POSTs to `/api/assets/promote`; surface pins `source=task_artifact_promote`; tested at template integrity (always) AND at HTTP via Starlette TestClient (proves the endpoint is reachable through the operator surface and the closure is queryable). |

### 9.1.6 Approval-path status (explicit per reviewer ask)

**The PR-2 approval path is intentionally restricted to
`requested → rejected` (via operator `withdraw_request` or reviewer
`reject_request`).** Approval (`requested → approved` with
`resulting_asset_id`) is **disabled** because PR-2 ships no
asset-library write path. The narrow correction was chosen per the
reviewer's instruction: "If full asset-object creation is not yet
present, then keep PR-2 approval/closure at requested/rejected
semantics only and remove premature resulting_asset_id behavior."

Re-enabling approval is a follow-up wave that lands an asset-library
write path AND adds asset-object existence verification before
`approve_request()` writes `resulting_asset_id`.

### 9.1.7 Operator-visible submit path (explicit per reviewer ask)

The corrected operator-visible submit path is a per-asset-card inline
`<form>` revealed by the existing "Promote …" button. The form posts
the contract-shaped JSON to `POST /api/assets/promote` and renders
the returned `request_id` + initial `request_state="requested"`
inline, or the rejection `error_code` on contract violation. No admin
review UI, no upload UI, no provider/model controls.

### 9.1.8 Residual risks after correction

- Approval path remains disabled until a future wave lands the
  asset-library write path (intentional per reviewer instruction).
- HTTP end-to-end tests run only when the FastAPI router + Starlette
  TestClient are importable in the test environment; they
  unconditionally PASS today (Py3.9 + installed FastAPI). Service-level
  tests cover the contract path regardless. Test gracefully skips with
  an explicit reason when the test client cannot be built.
- All other residual risks from §8 carry forward unchanged
  (in-process store, no admin review UI, asset reference plumbing into
  Workbench / Task Area packet refs deferred to PR-3 / PR-4).

## 10. References

- Decision: `docs/execution/ApolloVeo_2.0_Operator_Capability_Recovery_Decision_v1.md`
- Action: `docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_GLOBAL_ACTION_v1.md`
- Contracts: `asset_library_object_contract_v1.md`,
  `promote_request_contract_v1.md`,
  `promote_feedback_closure_contract_v1.md`,
  `factory_delivery_contract_v1.md`,
  `workbench_panel_dispatch_contract_v1.md`
- Product: `asset_supply_matrix_v1.md`, `broll_asset_supply_freeze_v1.md`
- Predecessor PR-1 execution log: `APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR1_PUBLISH_READINESS_EXECUTION_LOG_v1.md`
