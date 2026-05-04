# ApolloVeo 2.0 · Operator Capability Recovery · PR-5 Execution Log v1

Date: 2026-05-04 (rewritten from a GO gate to a NOT-READY decision +
Product-Flow Enforcement Order on 2026-05-04)
Status: Engineering complete on branch
`claude/recovery-pr5-trial-reentry-gate`; PR #120 open with the
rewritten posture.
Wave: ApolloVeo 2.0 Minimal Operator Capability Recovery — Re-entry
**evaluation** (the re-entry itself is BLOCKED by the rewrite verdict).
Decision authority:
[`docs/execution/ApolloVeo_2.0_Operator_Capability_Recovery_Decision_v1.md`](ApolloVeo_2.0_Operator_Capability_Recovery_Decision_v1.md).
Action authority:
[`docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_GLOBAL_ACTION_v1.md`](APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_GLOBAL_ACTION_v1.md) §8 (PR-5).
Predecessors (all MERGED to `main` 2026-05-04): PR-1 (#114, `4c317c4`),
PR-2 (#116, `4343bec`), PR-3 (#118, `d53da0f`), PR-4 (#119, `0549ee0`).

## 0. Verdict (top-line)

The PR-5 gate document records **Real operator trial NOT READY**.

What changed since the first revision of this PR-5: the prior revision
declared real-trial **GO subject to coordinator G5..G9**. That
conclusion was wrong — it treated "contract-backed minimum operator
capability is present" as sufficient for real trial, when the binding
condition is "operator workflow as specified by the line-specific
product-flow documents is present on operator-visible surfaces". The
rewrite flips the verdict to **NOT READY** and adds a binding
**Product-Flow Enforcement Order** that elevates the two product-flow
design documents to **line-specific execution authority**.

## 1. Scope

PR-5 · Real Operator Trial Re-Entry Gate — fifth and final mandatory
slice of Minimal Operator Capability Recovery. **Documentation +
narrow validation only.** PR-5 is a gate / re-entry **evaluation**
PR; it is NOT a new runtime feature wave. After rewrite, its role is:

1. Author the binding trial re-entry gate document with PR-1 .. PR-4
   evidence map AND a **NOT-READY verdict** AND a Product-Flow
   Enforcement Order that elevates two product-flow documents to
   line-specific execution authority.
2. Re-anchor Plan A and the Plan A coordinator write-up so neither
   claims real-trial GO.
3. Land the two product-flow design documents into the repo at
   `docs/product/` with the line-specific-execution-authority preamble.
4. Update the bootloader (`CURRENT_ENGINEERING_FOCUS.md`) to record
   the NOT-READY verdict + the Operator Workflow Convergence Wave as
   the next mandatory wave (Matrix Script first, Digital Anchor second).
5. Update the evidence index.
6. Land a narrow validation script + CI test pinning the documentation
   invariants of the rewritten gate so the verdict cannot silently
   regress.

Out of scope (forbidden by the rewrite mission):
- New runtime / product features.
- Asset platform expansion beyond PR-2.
- Matrix Script / Digital Anchor workflow behavior modification.
- Platform Runtime Assembly entry.
- Capability Expansion (W2.2 / W2.3 / durable persistence / runtime
  API).
- Provider / model / vendor controls.
- Packet / schema redesign (unless a documentation conflict is found
  — none was found).
- Hot Follow business behavior reopen.

## 2. Reading Declaration

### 2.1 Bootloader / indexes
- `CLAUDE.md`
- `docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md`
- `ENGINEERING_RULES.md`
- `CURRENT_ENGINEERING_FOCUS.md`
- `ENGINEERING_STATUS.md`

### 2.2 Recovery wave authority
- `docs/execution/ApolloVeo_2.0_Operator_Capability_Recovery_Decision_v1.md`
- `docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_GLOBAL_ACTION_v1.md` §8 (PR-5)
- All four predecessor execution logs (PR-1 / PR-2 / PR-3 / PR-4).

### 2.3 Top-level / readiness authority
- `docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md`
- `docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md` (Plan A; the
  artifact under correction in this PR)
- `docs/execution/PLAN_A_OPS_TRIAL_WRITEUP_v1.md` (coordinator
  runbook + static verification; live-run section corrected to
  NOT-READY in this PR)

### 2.4 Reviews
- `docs/reviews/operations_upgrade_gap_review_and_ops_plan_v1.md`
- `docs/reviews/apolloveo_2_0_unified_cognition_and_document_reanchoring_review_v1.md`

### 2.5 Cross-line contracts (referenced; not modified)
- `docs/contracts/publish_readiness_contract_v1.md`
- `docs/contracts/factory_delivery_contract_v1.md`
- `docs/contracts/workbench_panel_dispatch_contract_v1.md`

### 2.6 Product-flow source documents (elevated to line-specific
execution authority by this PR)
- `docs/product/matrix_script_product_flow_v1.md`
- `docs/product/digital_anchor_product_flow_v1.md`

### 2.7 Conflicts found
- **Plan A §12 readiness conclusion is "CONDITIONAL / authority-only"**;
  it predates the recovery wave. Resolved by §13 (NOT-READY) + §13.4
  (Convergence Wave).
- **Plan A coordinator write-up §8 live-run placeholder** was
  authored as an empty block to be filled by the operations team
  after authority-only trial. Resolved by §13.3 closure of the
  static-only era + redirection of future live-run logs to a v2
  trial gate.
- **No contract/packet conflict** was found. The Product-Flow
  Enforcement Order §3 of the gate document explicitly states that
  where a line-specific document and a frozen contract diverge, the
  contract wins. The product-flow documents do not redefine packet
  truth; they specify operator-surface presentation requirements
  that the existing contracts already permit.

## 3. Files Changed

### New files
- `docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR5_TRIAL_REENTRY_GATE_v1.md`
  — binding trial re-entry gate document. After rewrite carries: §0
  NOT-READY verdict; §1 rewrite rationale; §2 W1..W12 workflow-
  convergence preconditions; §3 Product-Flow Enforcement Order; §4
  Operator Workflow Convergence Wave; §5 post-recovery stage
  definition; §6 recovery wave acceptance evidence map (W1..W4 only);
  §7 operator surface inventory (post-recovery, pre-convergence); §8
  interim allowances during the Convergence Wave; §9 cross-cutting
  forbidden list; §10 stop conditions; §11 signoff block; §12
  references.
- `docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR5_EXECUTION_LOG_v1.md`
  — this document (after rewrite).
- `docs/product/matrix_script_product_flow_v1.md` — line-specific
  execution authority for Matrix Script. Sourced from the user-
  supplied product-flow design with an authority preamble pinning
  its status under PR-5.
- `docs/product/digital_anchor_product_flow_v1.md` — line-specific
  execution authority for Digital Anchor. Same provenance + preamble.
- `scripts/recovery_pr5_trial_reentry_check.py` — narrow validation
  script. After rewrite, asserts: predecessor logs MERGED, gate doc
  records NOT-READY verdict, gate doc carries the W7..W12 unmet
  rows, gate doc carries the Product-Flow Enforcement Order, both
  product-flow documents are present with the authority preamble,
  Plan A §13 records NOT READY, Plan A coordinator write-up §13
  records NOT READY, `CURRENT_ENGINEERING_FOCUS.md` records the
  Convergence Wave as next.
- `gateway/app/services/tests/test_recovery_pr5_trial_reentry_gate.py`
  — pytest module pinning the same invariants. CI catches gate
  regression.

### Modified files (additive only; no deletions)
- `docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md` — §13 rewritten
  from GO conclusion to NOT-READY + §13.4 Convergence Wave block.
  Pre-recovery §1..§12 preserved verbatim.
- `docs/execution/PLAN_A_OPS_TRIAL_WRITEUP_v1.md` — §13 rewritten
  from "real-trial era opened" to "real-trial BLOCKED until
  Convergence Wave closes". §13.5 pointer to product-flow authority
  documents added.
- `CURRENT_ENGINEERING_FOCUS.md` — stage line + main-line block
  rewritten to NOT-READY + Operator Workflow Convergence Wave next.
- `docs/execution/apolloveo_2_0_evidence_index_v1.md` — PR-5 + gate
  doc + product-flow authority rows recorded with the NOT-READY
  framing.
- `docs/execution/APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR1_PUBLISH_READINESS_EXECUTION_LOG_v1.md`,
  `..._PR2_ASSET_SUPPLY_..._v1.md`,
  `..._PR3_MATRIX_SCRIPT_WORKSPACE_..._v1.md`,
  `..._PR4_DIGITAL_ANCHOR_WORKSPACE_..._v1.md` — status headers
  aligned with the recorded merge state (squash commits 4c317c4 /
  4343bec / d53da0f / 0549ee0). Documentation-only — no body
  content changed.

## 4. Why scope remains gate-only after rewrite

- **No runtime change.** No service module, router, packet, schema,
  template, or operator-visible code path is modified. The validation
  script + the pytest module are read-only documentation invariants;
  they import nothing from `gateway.app`.
- **No contract change.** No contract file is modified. The Product-
  Flow Enforcement Order explicitly states that contracts win on
  contract conflicts.
- **No Hot Follow / Matrix Script / Digital Anchor / Asset Supply
  source code touched.** PR-5 source-code diff against `gateway/app/`
  consists of one new test file under `gateway/app/services/tests/`;
  no production source under
  `gateway/app/{services,routers,templates,lines,domain,...}` is
  modified.
- **No re-versioning of the product-flow source documents.** They
  are landed verbatim with an authority preamble; their substantive
  content is untouched.

## 5. Why the two product-flow docs are now formal execution authority

The Recovery Decision §1.1 named the missing capability that demoted
authority-only trial: "缺少真正可用的 operator workspace … 还必须
有任务区、工作台、交付中心、反馈与素材复用的最小工作能力". PR-1 ..
PR-4 restored that minimum **at the contract / runtime layer** — the
unified `publish_readiness` producer, the asset-library service, the
Matrix Script publish-feedback closure, the Digital Anchor formal
create-entry + Phase D.1 write-back. But "minimum work capability" at
the operator level is more than contract-runtime presence: it is the
**workflow** the operator follows on each line.

The two product-flow design documents (originally authored at
`/Users/tylerzhao/apolllo AI/`) define exactly that workflow — task-
area card fields, workbench modules, delivery-center deliverable set
and rules, per-line operational goal — at the level of binding
product specification. Until PR-5, those documents lived outside the
repository and were not citable as execution authority. The recovery
wave's surfaces wired the contracts but did not wire the workflow.
That gap is the proximate cause of the NOT-READY verdict.

The Product-Flow Enforcement Order in the gate document §3 elevates
both documents to **line-specific execution authority**:

1. The top-level
   [`apolloveo_2_0_top_level_business_flow_v1.md`](../architecture/apolloveo_2_0_top_level_business_flow_v1.md)
   remains the factory-wide abstract flow (task → line → workbench
   → delivery → publish → archive). This is unchanged; the cross-line
   abstraction is correct.
2. The two product-flow documents are the **line-specific
   concretization** of that abstract flow. They specify exactly what
   the Task Area card, the Workbench modules, and the Delivery Center
   sections must render on Matrix Script / Digital Anchor surfaces.
3. **Future Task Area / Workbench / Delivery implementations on
   Matrix Script / Digital Anchor MUST map to the product-flow
   modules, not only to the packet / contract / runtime truth.** A
   workbench page that consumes the Phase B variation surface
   projection but does not render §6.1 modules A/B/C/D/E is not
   operator-ready under this rule.
4. **Operator-ready cannot be claimed unless product-flow modules
   are actually present on the surfaces.** The PR-5 NOT-READY
   verdict is the first instance of this rule. Future PRs that claim
   "operator-ready" or "real-trial GO" MUST cite the specific
   product-flow modules they render.
5. Conflict-resolution: line-specific document wins on its line's
   surfaces; frozen contract wins on contract conflicts. Re-versioning
   either document requires a separate authored PR.

This is the binding answer to the rewrite mission's required
conclusion: **the two product-flow documents are formal execution
authority, the top-level flow remains the abstract factory flow, and
ApolloVeo is NOT yet ready for real operator trial from an operator-
workflow perspective.**

## 6. Acceptance Mapping (rewrite mission "Required conclusion" + "Required document updates")

| Required conclusion / update | Status | Evidence |
| --- | --- | --- |
| Top-level business flow remains valid as the factory-wide abstract flow | PASS | Gate doc §3 item 1; the top-level document is referenced unchanged. |
| Matrix Script and Digital Anchor product-flow documents are NOT yet sufficiently enforced as execution authority — fixed by this PR | PASS | Gate doc §3 (Product-Flow Enforcement Order) elevates both documents; both documents now exist at `docs/product/*_product_flow_v1.md` with the authority preamble. |
| ApolloVeo is NOT yet ready for real operator trial from an operator-workflow perspective | PASS | Gate doc §0 verdict NOT READY; §2 W7..W12 unchecked; Plan A §13 records NOT READY; Plan A coordinator write-up §13 records BLOCKED; CURRENT_ENGINEERING_FOCUS records NOT READY. |
| Matrix Script product-flow doc becomes line-specific execution authority | PASS | `docs/product/matrix_script_product_flow_v1.md` carries the authority preamble. |
| Digital Anchor product-flow doc becomes line-specific execution authority | PASS | `docs/product/digital_anchor_product_flow_v1.md` carries the authority preamble. |
| Future Task Area / Workbench / Delivery implementations must map to those product-flow modules, not only to packet/contract/runtime truth | PASS | Gate doc §3 item 3 binding rule. |
| Operator-ready cannot be claimed unless product-flow modules are actually present in the surfaces | PASS | Gate doc §3 item 4 binding rule. |
| Recovery PR-1~PR-4 restored minimum contract-backed operator capability | PASS | Gate doc §6 evidence map. |
| But operator workflow convergence is still missing | PASS | Gate doc §2.3 W7..W12 unchecked; §7 operator surface inventory enumerates the gaps line-by-line. |
| Therefore real operator trial is blocked | PASS | Gate doc §2.4 verdict; §0 verdict; Plan A §13.0; coordinator write-up §13. |
| Next wave is Operator Workflow Convergence Wave — Matrix Script first, Digital Anchor second | PASS | Gate doc §4 wave definition; §4.2 mandatory ordering; Plan A §13.4. |
| PR-5 gate doc updated | PASS | This PR's `APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR5_TRIAL_REENTRY_GATE_v1.md`. |
| `PLAN_A_OPS_TRIAL_WRITEUP_v1.md` updated | PASS | This PR's §13 rewrite. |
| `OPERATIONS_TRIAL_READINESS_PLAN_v1.md` updated | PASS | This PR's §13 rewrite. |
| `CURRENT_ENGINEERING_FOCUS.md` updated | PASS | Stage line + main-line block rewritten to NOT-READY + Convergence Wave next. |
| Evidence index updated | PASS | Rows for the gate doc, the two product-flow authority documents, the validation script, and the CI test recorded. |

## 7. Forbidden-Scope Audit (rewrite mission "Do NOT" list)

| Red line | Status |
| --- | --- |
| No new runtime features | clean — file diff under `gateway/app/{services,routers,templates,lines,...}/` outside `gateway/app/services/tests/` is empty. |
| No reopening of Platform Runtime Assembly | clean. |
| No reopening of Capability Expansion | clean. |
| No contract / packet change unless a documentation conflict found | clean — no contract / packet file modified; no documentation conflict was found that required a contract/packet edit. |
| No Hot Follow behavior change | clean. |
| No re-versioning of the product-flow documents under cover of PR-5 | clean — both documents land verbatim plus an authority preamble; no substantive content was edited. |

## 8. Tests / Checks Run

- `scripts/recovery_pr5_trial_reentry_check.py` — exit 0 (all
  invariants PASS for the rewritten gate; the script itself was
  updated to assert the rewritten invariants — NOT-READY verdict
  present, both product-flow documents present with authority
  preamble, Plan A §13 + write-up §13 record NOT-READY, etc.).
- `gateway/app/services/tests/test_recovery_pr5_trial_reentry_gate.py`
  — all PASS on Python 3.9.6.
- Adjacent regression (post-recovery surfaces — sanity that PR-5
  documentation work did not break any code):
  - PR-1 publish-readiness suite — PASS.
  - PR-2 asset suite — PASS.
  - PR-3 matrix-script closure suite — PASS.
  - PR-4 digital-anchor closure suite — PASS.
  - Hot Follow + contract runtime suites — unchanged.

## 9. Residual Risks

- **NOT-READY verdict depends on documentation discipline.** The
  validation script + CI test pin the verdict's documentation
  invariants. A future commit that flips Plan A §13 or the gate
  doc §0 verdict to GO without an authored "Trial Re-Entry Gate v2"
  PR will fail the CI test.
- **Product-flow elevation is per-line, not cross-line.** The two
  product-flow documents are binding for Matrix Script / Digital
  Anchor surfaces only. Hot Follow has its own line-specific
  authority at
  [`docs/architecture/hot_follow_business_flow_v1.md`](../architecture/hot_follow_business_flow_v1.md);
  the Convergence Wave does not include Hot Follow because its
  workflow is already convergent at the line level.
- **Convergence Wave scope is bounded.** It maps existing recovered
  truth into the product-flow modules. It does NOT add new runtime
  features. If a product-flow module turns out to require a runtime
  capability that PR-1..PR-4 did not deliver, that is a Convergence
  Wave stop-condition; the wave pauses and a separate runtime PR is
  authored.
- **Plan E gate specs and Plan E phase closeout signoffs (A7 / UA7
  / RA7)** remain independently pending in Raobin / Alisa / Jackie's
  queue, untouched by PR-5. PR-5 does not advance them. They are
  separate paperwork carried forward as historical context.
- All other residual risks from PR-1 / PR-2 / PR-3 / PR-4 carry
  forward unchanged.

## 10. Exact Statement of What Remains After PR-5

The next allowable engineering action after PR-5 is the **Operator
Workflow Convergence Wave**:

- **Phase OWC-MS (first):** Matrix Script Task Area card §5.3 fields
  + Workbench §6.1 modules A/B/C/D/E + Delivery Center §7.1 standard
  deliverables + §7.2 publish rules — landing W7 + W8 + W9.
- **Phase OWC-DA (second):** Digital Anchor Task Area card §5.2
  fields + Workbench §6.1 modules A/B/C/D/E + Delivery Center §7.1
  standard deliverables + §7.2 delivery rules — landing W10 + W11 +
  W12.

After OWC-MS + OWC-DA close, a separate "Trial Re-Entry Gate v2"
document may be authored to reopen the real-trial decision. PR-5
does NOT pre-decide that gate.

The next allowable engineering action is **NOT** Platform Runtime
Assembly. It is **NOT** Capability Expansion. It is **NOT** real
operator trial.

## 11. References

- Decision: [`ApolloVeo_2.0_Operator_Capability_Recovery_Decision_v1.md`](ApolloVeo_2.0_Operator_Capability_Recovery_Decision_v1.md)
- Action: [`APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_GLOBAL_ACTION_v1.md`](APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_GLOBAL_ACTION_v1.md)
- Gate doc:
  [`APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR5_TRIAL_REENTRY_GATE_v1.md`](APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR5_TRIAL_REENTRY_GATE_v1.md)
- Plan A trial brief (rewritten §13 NOT READY):
  [`OPERATIONS_TRIAL_READINESS_PLAN_v1.md`](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md)
- Coordinator write-up (rewritten §13 NOT READY):
  [`PLAN_A_OPS_TRIAL_WRITEUP_v1.md`](PLAN_A_OPS_TRIAL_WRITEUP_v1.md)
- **Matrix Script line-specific execution authority (elevated by this PR-5):**
  [`matrix_script_product_flow_v1.md`](../product/matrix_script_product_flow_v1.md)
- **Digital Anchor line-specific execution authority (elevated by this PR-5):**
  [`digital_anchor_product_flow_v1.md`](../product/digital_anchor_product_flow_v1.md)
- Top-level abstract flow (factory-wide; unchanged):
  [`apolloveo_2_0_top_level_business_flow_v1.md`](../architecture/apolloveo_2_0_top_level_business_flow_v1.md)
- Predecessor execution logs:
  [`PR1`](APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR1_PUBLISH_READINESS_EXECUTION_LOG_v1.md),
  [`PR2`](APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR2_ASSET_SUPPLY_EXECUTION_LOG_v1.md),
  [`PR3`](APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR3_MATRIX_SCRIPT_WORKSPACE_EXECUTION_LOG_v1.md),
  [`PR4`](APOLLOVEO_2_0_OPERATOR_CAPABILITY_RECOVERY_PR4_DIGITAL_ANCHOR_WORKSPACE_EXECUTION_LOG_v1.md)
- Validation script: [`scripts/recovery_pr5_trial_reentry_check.py`](../../scripts/recovery_pr5_trial_reentry_check.py)
- CI test: [`gateway/app/services/tests/test_recovery_pr5_trial_reentry_gate.py`](../../gateway/app/services/tests/test_recovery_pr5_trial_reentry_gate.py)
