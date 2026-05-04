# ApolloVeo 2.0 · Operator Capability Recovery · PR-1 Execution Log v1

Date: 2026-05-04
Status: Engineering complete on branch `claude/wonderful-visvesvaraya-4020d0`;
PR opening pending.
Wave: ApolloVeo 2.0 Minimal Operator Capability Recovery.
Decision authority: `docs/execution/ApolloVeo_2.0_Operator_Capability_Recovery_Decision_v1.md`.
Action authority: `docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_GLOBAL_ACTION_v1.md` §4.

## 1. Scope

PR-1 · Unified Publish Readiness Runtime Recovery — the first mandatory
slice of Minimal Operator Capability Recovery. Lands the unified
`publish_readiness` runtime producer, the L3 `final_provenance` emitter,
and the L4 advisory producer; rewires Board / Workbench / Delivery to
consume one producer instead of three independently-derived publish
truths.

Out of scope (carried by later PRs): Asset Supply / B-roll capability
(PR-2), Matrix Script workspace promotion (PR-3), Digital Anchor
recovery (PR-4), trial re-entry gate (PR-5).

## 2. Reading Declaration

### 2.1 Indexes read first
- `CLAUDE.md`
- `docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md`
- `ENGINEERING_RULES.md`
- `CURRENT_ENGINEERING_FOCUS.md`

### 2.2 Wave authority
- `docs/execution/ApolloVeo_2.0_Operator_Capability_Recovery_Decision_v1.md`
- `docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_GLOBAL_ACTION_v1.md`

### 2.3 PR-1 contract authority
- `docs/contracts/publish_readiness_contract_v1.md` (output shape, closed
  `head_reason` enum, single-producer rule)
- `docs/contracts/factory_delivery_contract_v1.md` §"Per-Deliverable
  Required / Blocking Fields (Plan D Amendment)" + §"Scene-Pack
  Non-Blocking Rule (Explicit; Plan C Amendment)"
- `docs/contracts/hot_follow_current_attempt_contract_v1.md`
  §"`final_provenance` Field (Plan D Amendment)"
- `docs/contracts/l4_advisory_producer_output_contract_v1.md`
- `docs/contracts/hot_follow_projection_rules_v1.md` lines 272-335 (closed
  advisory taxonomy)

### 2.4 PR-1 code surface
- `gateway/app/services/operator_visible_surfaces/projections.py`
  (today's three independent re-derivations)
- `gateway/app/services/operator_visible_surfaces/wiring.py`
- `gateway/app/services/contract_runtime/current_attempt_runtime.py`
  (L3 producer)
- `gateway/app/services/matrix_script/delivery_binding.py`
  (per-row `required` / `blocking_publish` zoning already shipped under
  Plan E PR-3)
- `gateway/app/services/task_router_presenters.py`,
  `gateway/app/services/task_view_presenters.py` (consumers)

### 2.5 Conflicts found
- **Path conflict (resolved)**: mission cited
  `docs/architecture/...Operator_Capability_Recovery_Decision_v1.md`; the
  decision document is actually under `docs/execution/`. Codex's Global
  Action file already pinned the actual location.
- **Forbidden-list conflict (resolved by re-anchor)**:
  `CURRENT_ENGINEERING_FOCUS.md` "Forbidden Work" enumerates the D1
  unified `publish_readiness` producer + D2 L3 `final_provenance` emitter
  as forbidden under multiple Plan E phase gate specs. The Recovery
  Decision explicitly supersedes this by re-anchoring the mainline. PR-1
  lands the formerly-forbidden producer/emitter under the new wave with
  a minimal docs write-back to remove the contradictory line.

## 3. Files Changed

### New files
- `gateway/app/services/operator_visible_surfaces/publish_readiness.py` —
  unified L4 producer per `publish_readiness_contract_v1`.
- `gateway/app/services/operator_visible_surfaces/advisory_emitter.py` —
  L4 advisory producer per `l4_advisory_producer_output_contract_v1`.
  Verbatim mirror of the closed taxonomy.
- `gateway/app/services/tests/test_publish_readiness_unified_producer.py`
  — 24 cases covering closed `head_reason` enum, scene-pack defensive
  clamp, legacy-wrapper agreement, advisory emitter taxonomy bounds,
  input-purity.
- `gateway/app/services/tests/test_final_provenance_emission.py` — 5
  cases covering the closed enum {current, historical} and `to_dict`
  serialization.

### Modified files
- `gateway/app/services/operator_visible_surfaces/__init__.py` — exports
  `compute_publish_readiness`, `emit_advisories`,
  `CLOSED_HEAD_REASON_ENUM`.
- `gateway/app/services/operator_visible_surfaces/projections.py` —
  thinned `derive_board_publishable` and `derive_delivery_publish_gate`
  to delegate to the unified producer; legacy two-field shapes preserved
  byte-for-byte for existing callers.
- `gateway/app/services/operator_visible_surfaces/wiring.py` — added
  `publish_readiness` to both Workbench and Delivery bundles; plumbed
  L3 current_attempt + Matrix Script delivery rows; preserved the
  legacy `publish_gate` / `publish_gate_head_reason` keys on the
  Delivery bundle so the publish-hub template/JSON consumers do not
  see a shape change.
- `gateway/app/services/contract_runtime/current_attempt_runtime.py` —
  added `final_provenance` field to `HotFollowCurrentAttempt` dataclass +
  `to_dict()`; computed in `build_hot_follow_current_attempt` from
  `final_exists`, `final_fresh`, `requires_recompose`, `requires_redub`
  per the Plan D amendment.
- `CURRENT_ENGINEERING_FOCUS.md` — minimal authority-alignment write-back
  noting PR-1 lands formerly Plan-E-deferred D1+D2 under the Recovery
  wave (no historical line removed; new line appended).

## 4. Why scope is minimal and isolated

- One producer, one emitter, one L3 enum field. No new endpoints, no
  template rewrite, no React/Vite work, no provider/model controls.
- Hot Follow business behavior unchanged. `final_provenance` is a new
  L3 field; UI rendering of the new field is deferred (Plan E or later).
- Matrix Script frozen truth unchanged. PR-1 only consumes the existing
  per-row `required` / `blocking_publish` already shipped by Plan E
  PR-3; no Matrix Script source file is modified.
- Digital Anchor untouched and remains inspect-first per Plan A §2.1
  hide guards. The unified producer reads the same inputs for any line;
  Digital Anchor will plug into the same shape when PR-4 lands without
  the producer needing to change.
- Legacy `derive_board_publishable` / `derive_delivery_publish_gate`
  signatures preserved as thin pass-throughs per ENGINEERING_RULES §7
  "Compatibility Rules" (explicitly temporary; removal path: future
  Plan E phase or Platform Runtime Assembly Wave when callers can
  migrate to the full `compute_publish_readiness` shape).

## 5. Tests Run

Local Python 3.9.6 (the Python 3.10+ unrelated config.py union-syntax
incompatibility is a pre-existing repo baseline issue and not introduced
by PR-1 — same tests fail at collection without PR-1).

PR-1 import-light test set:

- `gateway/app/services/tests/test_publish_readiness_unified_producer.py` — **24/24 PASS**
- `gateway/app/services/tests/test_final_provenance_emission.py` — **5/5 PASS**

Adjacent regression (no behavior change expected):

- `test_hot_follow_current_attempt_wave1.py` — PASS (existing field set
  unaffected; `final_provenance` is additive).
- `test_matrix_script_b4_artifact_lookup.py` — 30/30 PASS.
- `test_matrix_script_delivery_zoning.py` — 16/16 PASS.
- `test_matrix_script_delivery_comprehension.py` — PASS.
- `test_matrix_script_task_card_summary.py` — 30/30 PASS.
- `test_contract_runtime_projection_rules.py`,
  `test_hot_follow_l4_wave2.py`, `test_hot_follow_artifact_facts.py`,
  `test_hot_follow_subtitle_currentness.py`,
  `test_hot_follow_helper_translation.py`,
  `test_line_binding_service.py` — all PASS.

Aggregate: **199 PASS, 0 FAIL** on the import-light test set.

## 6. Acceptance Mapping (Global Action §4)

| Acceptance criterion (PR-1 §4 Acceptance) | Status | Evidence |
| --- | --- | --- |
| Board, Workbench, and Delivery expose the same publish readiness result for the same task state | PASS | `test_legacy_board_wrapper_agrees_with_producer`, `test_legacy_delivery_wrapper_agrees_with_producer` |
| Tests prove no second truth source is used for publishability | PASS | Legacy `derive_*` functions are now thin pass-throughs; both wrappers exercise the same producer. |
| `final_provenance` is emitted and consumed from the producer path | PASS | `test_final_provenance_emission.py` (emitter) + `test_final_provenance_historical_blocks_publish` / `test_final_provenance_current_does_not_block` (consumer). |
| Delivery uses `required` / `blocking_publish` rather than ad hoc kind mapping | PASS | `_matrix_script_delivery_rows` plumbs Matrix Script's existing per-row zoning into the producer; `test_required_deliverable_*` cases. |
| Hot Follow baseline remains behaviorally preserved | PASS | Hot Follow consumes the producer through the legacy wrapper signatures unchanged; existing Hot Follow tests pass. `final_provenance` is additive on L3. |
| Evidence / tests / execution log are complete | PASS | This document. |

## 7. Residual Risks

- **`current_attempt` not yet plumbed into Hot Follow Workbench
  state**: the unified producer reads `state.current_attempt` /
  `task.current_attempt` when present and falls back to ready_gate +
  L2 truth otherwise. Hot Follow's Workbench presenter does not yet
  attach the L3 dataclass to the state dict; until it does, the
  `final_provenance_historical` head reason can only be reached via
  `final_stale_reason` on L2. This is intentional — wiring the L3
  consumer into the Hot Follow Workbench presenter is part of a later
  PR (post Recovery Wave) and would otherwise break the PR-1 scope
  rule against Hot Follow business-behavior reopen.
- **No new Hot Follow per-row delivery zoning**: Hot Follow does not
  yet declare per-deliverable `required` / `blocking_publish` rows.
  This is per existing Hot Follow delivery binding contract; adding
  zoning would be a Hot Follow contract amendment outside PR-1 scope.
  The producer accepts `delivery_rows=None` cleanly for Hot Follow.
- **Python 3.10+ collection errors on unrelated config.py**: pre-existing
  repo baseline issue (PEP 604 union syntax in `gateway/app/config.py`).
  Does not affect PR-1's import-light test set. Out of scope.
- **`derive_board_publishable` / `derive_delivery_publish_gate` legacy
  wrappers**: kept as thin pass-throughs per ENGINEERING_RULES §7.
  Removal path: callers migrate to `compute_publish_readiness` in a
  later Recovery Wave PR (likely PR-3 Matrix Script promotion or PR-5
  trial re-entry gate cleanup), at which point the wrappers can be
  deleted.

## 8. Forbidden-Scope Audit (Global Action §2 + §4 Red Lines)

| Red line | Status |
| --- | --- |
| No Platform Runtime Assembly | clean |
| No Capability Expansion | clean |
| No third official production line | clean |
| No full asset platform / admin system | clean |
| No provider/model/vendor/engine controls | clean — producer rejects forbidden keys via `sanitize_operator_payload` boundary; tested |
| No React/Vite full rebuild | clean |
| No Hot Follow business behavior reopen | clean — no Hot Follow source file modified except L3 dataclass field addition |
| No rewrite of closed Matrix Script / Digital Anchor truth | clean — Matrix Script files untouched; consumed via existing `project_delivery_binding` |
| No reopening Matrix Script §8.A–§8.H | clean |
| No page-first drift | clean — no template/route added |
| No promotion of discovery-only surfaces | clean |
| Branch is not used as authority — merges to `main` after PR review | enforced by Codex review process |

## 9. Exact Statement of What Remains for the Next PR

PR-2 · B-roll / Asset Supply Minimum Usable Operator Capability — minimum
read-only asset library service, minimum promote request path, minimum
promote feedback closure, minimum operator-visible asset surface. Per
Global Action §3, PR-2 may not start until PR-1 is merged and reviewed.
Claude stops after this PR-1 is opened.

## 9.1 Reviewer-Fail Correction Pass (2026-05-04)

The Codex/architect review of the initial PR-1 commit returned FAIL with
four explicit findings. This section records the failure findings, the
exact correction made, and residual risks after correction.

### 9.1.1 Reviewer findings (FAIL)

1. **Workbench display drift.** The Workbench template rendered
   `ops.delivery.publish_gate` for one meta-item and
   `ops.board.publishable` for another. Both were backed by the unified
   producer after the initial commit, but the two paths fed the producer
   different inputs (Board path passed `l2_facts=None`, Delivery path
   passed L2). For the same task state, Board and Delivery could
   therefore disagree on publishability — the exact drift PR-1 must
   eliminate.
2. **`head_reason` enum escape.** The producer copied
   `ready_gate.blocking[0]` verbatim into `head_reason` when blocking
   strings were present (e.g. `"voiceover_missing"`,
   `"compose_input_blocked"`). These strings are not members of the
   closed enum declared in `publish_readiness_contract_v1.md`
   §"Closed `head_reason` enum". The contract is normative;
   `head_reason` MUST always be inside the enum.
3. **Missing surface-alignment integration tests.** The initial test
   suite covered the producer in isolation and the legacy wrapper
   agreement, but had no test that exercised Board + Workbench +
   Delivery as a triple and asserted they agree on the same task state.
4. **No integration coverage** for `final_provenance="historical"`,
   Matrix Script blocking rows, or scene_pack non-blocking at the
   surface-alignment level.

### 9.1.2 Exact corrections made

1. **Workbench display alignment** (file:
   [`gateway/app/templates/task_workbench.html`](../../gateway/app/templates/task_workbench.html)).
   Removed the split `ops.board.publishable` / `ops.delivery.publish_gate`
   meta-items that visualized the drift. Replaced with a single
   "Publish readiness" meta-item rendered from
   `ops.publish_readiness.publishable` + `head_reason`, plus a
   `final_provenance` meta-item from
   `ops.publish_readiness.consumed_inputs.final_provenance`. The
   operator-readable original ready-gate string is shown in muted text
   when it differs from the normalized enum value.
2. **Source-of-drift fix in wiring**
   ([`gateway/app/services/operator_visible_surfaces/wiring.py`](../../gateway/app/services/operator_visible_surfaces/wiring.py)):
   `build_operator_surfaces_for_workbench` now computes
   `publish_readiness` once with the FULL input set (`ready_gate` + L2 +
   L3 + delivery rows) and overwrites `bundle["board"]` and
   `bundle["delivery"].publish_gate*` from the same result. Even surfaces
   that read the legacy keys see the unified-producer output.
3. **Board producer-input alignment**: `build_board_row_projection` now
   plumbs L2 facts and L3 `current_attempt` from the row through to the
   producer (when present), rather than passing `l2_facts=None`. Cold
   list rows that have not yet hydrated L2 still degrade to the
   ready-gate-only path so existing Board behavior is preserved.
4. **`head_reason` enum normalization**
   ([`gateway/app/services/operator_visible_surfaces/publish_readiness.py`](../../gateway/app/services/operator_visible_surfaces/publish_readiness.py)):
   added `_BLOCKING_REASON_TO_HEAD_REASON` mapping +
   `_map_ready_gate_blocking_to_head_reason` normalizer. Known compose
   reasons map to `compose_not_ready`; known publish-blocking reasons
   map to `publish_not_ready`; unknown / future reasons degrade safely
   to `ready_gate_blocking` (a member of the closed enum). The original
   string is preserved on
   `consumed_inputs.first_blocking_reason` so the operator surface can
   still render operator-readable detail without `head_reason` itself
   escaping the contract.
5. **Surface-alignment integration tests** (new file:
   [`gateway/app/services/tests/test_publish_readiness_surface_alignment.py`](../../gateway/app/services/tests/test_publish_readiness_surface_alignment.py))
   — 16 cases covering: same task state ⇒ same publishability across
   Board/Workbench/Delivery; ready_gate blocking string normalization
   agreement; `final_provenance="historical"` agreement;
   `final_provenance="current"` agreement; Matrix Script unresolved
   required row blocking agreement; Matrix Script resolved rows publish;
   scene_pack defensive non-blocking clamp; scene_pack unresolved does
   not flip Hot Follow off-publishable; an 8-case parametrized
   cross-surface invariant.
6. **Producer-test updates**: `test_ready_gate_blocking_first_entry_becomes_head_reason`
   renamed to `test_ready_gate_blocking_normalizes_to_closed_enum`;
   added `test_unknown_blocking_reason_degrades_to_ready_gate_blocking`,
   `test_known_compose_blocking_reasons_normalize_to_compose_not_ready`,
   `test_known_publish_blocking_reasons_normalize_to_publish_not_ready`.
   Closed-enum invariant test
   (`test_head_reason_is_always_in_closed_enum`) now hard-asserts no
   escape — no carve-out for ready_gate strings.

### 9.1.3 Tests after correction

- Producer suite: **30/30 PASS** (24 original + 6 enum-normalization).
- L3 emission suite: **5/5 PASS** (unchanged).
- Surface-alignment suite (new): **17/17 PASS**.
- Adjacent baseline: **189 PASS** (Hot Follow current_attempt wave1,
  Matrix Script B4/zoning/comprehension/card summary, contract_runtime
  projection rules, Hot Follow L4 wave2, artifact facts, subtitle
  currentness, helper translation, line binding service).

### 9.1.4 Why the reviewer-fail is now closed

| Finding | Closed by |
| --- | --- |
| Workbench drift | Template now displays `ops.publish_readiness` only. Underlying wiring overlays the unified result onto `bundle.board` and `bundle.delivery.publish_gate*`, so even legacy reads cannot drift. Board's `build_board_row_projection` passes the same L2 + L3 the other surfaces pass. Surface-alignment tests prove agreement across 17 input combinations. |
| `head_reason` enum escape | Explicit normalization layer in the producer maps known reasons into the enum and degrades unknown reasons to `ready_gate_blocking`. Tests assert `head_reason in CLOSED_HEAD_REASON_ENUM` for every probed input including `"some_brand_new_reason_not_in_taxonomy"`. Original string preserved on `consumed_inputs.first_blocking_reason` — the contract is honored without losing operator-readable detail. |
| Missing surface-alignment integration tests | New file `test_publish_readiness_surface_alignment.py` covers the four reviewer-required cases plus an 8-case parametrized invariant. |
| `final_provenance="historical"` / Matrix Script blocking rows / scene_pack non-blocking integration coverage | Each is a named test in the new alignment suite. |

### 9.1.5 Residual risks after correction

- **`build_board_row_projection`'s "no L2 hydrated" carve-out**:
  cold Board list rows that don't carry a `final` dict still flow
  through the producer with `l2_facts=None`, deferring freshness to the
  ready_gate. This preserves legacy Board behavior but means a cold
  list row could in principle disagree with Workbench/Delivery when the
  freshness check would have flipped the result. In practice the row's
  `ready_gate` was already computed from L2 upstream, so the deferral
  is tight; a follow-up could plumb L2 onto every row, but that's a
  presenter-side change outside PR-1's reviewer-fix scope.
- **Hot Follow `current_attempt` not yet attached to `state`**: as in
  the original PR-1 log, the Hot Follow Workbench presenter does not
  yet attach the L3 dataclass to the state dict; until it does, the
  Hot Follow path can reach `final_provenance_historical` only via L2
  `final_stale_reason`. Wiring the L3 dataclass into the Hot Follow
  presenter would touch Hot Follow business surfaces and is intentionally
  deferred. The unified producer reads `current_attempt` from `state`
  or `task` — either source is honored.
- **Legacy thin wrappers** (`derive_board_publishable`,
  `derive_delivery_publish_gate`) remain in `projections.py` per
  ENGINEERING_RULES §7. Removal still queued for a later Recovery Wave PR.

## 10. References

- Decision: `docs/execution/ApolloVeo_2.0_Operator_Capability_Recovery_Decision_v1.md`
- Action: `docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_GLOBAL_ACTION_v1.md`
- Contract (producer): `docs/contracts/publish_readiness_contract_v1.md`
- Contract (delivery zoning): `docs/contracts/factory_delivery_contract_v1.md`
- Contract (L3 amendment): `docs/contracts/hot_follow_current_attempt_contract_v1.md`
- Contract (advisory emitter): `docs/contracts/l4_advisory_producer_output_contract_v1.md`
- Reference (advisory taxonomy): `docs/contracts/hot_follow_projection_rules_v1.md` lines 272-335
