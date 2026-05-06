# Matrix Script Result-Capability Recovery Wave Gate Spec v1

Date: 2026-05-06
Status: Documentation only. Gate spec authoring step. **No code, no UI, no contract, no schema, no test, no template change.** Authoring this gate spec does NOT open the Matrix Script Result-Capability Recovery Wave implementation gate; §10 architect (Raobin) + reviewer (Alisa) signoff is required for the implementation gate to open.
Wave: ApolloVeo 2.0 Matrix Script Result-Capability Recovery Wave (Track B of the post-amendment bifurcated sequence).
Phase position: Authorised by [Matrix Script Result-Capability Recovery Amendment v1](../product/OPERATIONS_TRIAL_READINESS_MATRIX_SCRIPT_RECOVERY_AMENDMENT_v1.md) §2.5 / §8 (single next docs-only step). Sits after the trial re-entry review §8 signoff (`7e2ad59`) and the recovery amendment merge (PR [#146](https://github.com/zhaojfifa/apolloveo-auto/pull/146) squash `8eb8242`). Runs in parallel with Track A (Hot-Follow-only Plan A live-trial window). Predecessor substrate: OWC-MS Closeout PASS (MS-W1..MS-W8 merged, signoff `b1160b3`); OWC-DA Closeout PASS (PR [#139](https://github.com/zhaojfifa/apolloveo-auto/pull/139)); Operator Capability Recovery PR-1..PR-4 merged.

This gate spec cites the recovery amendment as authority and observes its §7 hard boundaries verbatim. It does NOT re-litigate OWC-MS, does NOT re-author packet truth, does NOT widen any closed enum, does NOT touch Hot Follow / Digital Anchor / Asset Supply files, and does NOT advance Plan E A7 / UA7 / RA7 closeout signoffs.

---

## 1. Authority Stack

This gate spec is bound by, in priority order:

1. [CLAUDE.md](../../CLAUDE.md) bootloader.
2. [ENGINEERING_RULES.md](../../ENGINEERING_RULES.md) (with §13 Product-Flow Module Presence).
3. **[docs/product/OPERATIONS_TRIAL_READINESS_MATRIX_SCRIPT_RECOVERY_AMENDMENT_v1.md](../product/OPERATIONS_TRIAL_READINESS_MATRIX_SCRIPT_RECOVERY_AMENDMENT_v1.md)** — recovery amendment (binding scope authoriser; §2.5 / §7 / §8).
4. [docs/product/matrix_script_product_flow_v1.md](../product/matrix_script_product_flow_v1.md) — Matrix Script line-specific execution authority.
5. [docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md](../architecture/apolloveo_2_0_top_level_business_flow_v1.md) — factory-wide abstract flow.
6. [docs/design/ApolloVeo_Operator_Visible_Surfaces_v1.md](../design/ApolloVeo_Operator_Visible_Surfaces_v1.md) — operator-visible surface authority.
7. [docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md](../architecture/apolloveo_2_0_unified_alignment_map_v1.md) §7 — bifurcated frozen next engineering sequence.
8. [docs/reviews/owc_ms_gate_spec_v1.md](owc_ms_gate_spec_v1.md) — preserved substrate; surfaces consumed by recovery wave.
9. [docs/execution/APOLLOVEO_2_0_OWC_MS_PHASE_CLOSEOUT_v1.md](../execution/APOLLOVEO_2_0_OWC_MS_PHASE_CLOSEOUT_v1.md) §8 — tracked gaps inherited (NOT closed by this wave; surfaced operator-visibly).
10. [docs/reviews/trial_reentry_review_v1.md](trial_reentry_review_v1.md) — SIGNED; §4 / §7 MS scope superseded for live-trial purposes by the recovery amendment per amendment §2.3, but informational substrate stands.
11. PR-1..PR-4 Operator Capability Recovery execution logs — frozen substrate.

When this gate spec conflicts with any authority above, the higher authority wins.

---

## 2. Recovery Verdict (binding)

**Matrix Script is not trial-capable until it can produce an operator-understandable result path.**

Surface convergence is necessary but not sufficient. The OWC-MS engineering verdict PASS stands; the eight already-merged operator-visible modules (MS-W1..MS-W8) remain on `main` as substrate. However, an operator who creates a Matrix Script task today cannot identify, on the existing surfaces alone:

- **What is usable now** — which variation / version is currently a deliverable artifact, not just a populated cell.
- **What is blocked** — which variation is gated by a missing input vs by a closed advisory vs by a sentinel-state field.
- **Which version is recommended** — the per-task "recommended variation marker" exists in the Workbench C projection but is not framed as an actionable result decision.
- **What next action is required** — the surfaces show diagnostic state but do not present an operator-language "do X next."

This wave delivers the Hot Follow operator outcome lens applied to Matrix Script's existing data, by reorganization of existing OWC-MS surfaces over already-merged Recovery PR-1..PR-4 substrate. The recovery wave is **at the operator surface / workflow reframe layer**, not at the contract / schema / packet truth layer.

The recovery wave closes when:

1. The four implementation PRs in §5 below merge with their acceptance evidence recorded.
2. The Closeout document records all acceptance rows PASS.
3. A follow-on trial re-entry review for Matrix Script is authored and signed by architect + reviewer + coordinator + product manager.

Until those three conditions hold, **Matrix Script remains NOT a trial candidate** under the recovery amendment §2.3 classification.

---

## 3. Minimum Operator-Usable Result (binding)

Matrix Script must produce, by the end of the recovery wave, all of the following — every item delivered as a re-presentation of existing data on existing surfaces, with no new contract, no new structural surface module, and no closed-enum widening:

| ID | Minimum result element | What "usable" means at the operator surface |
| --- | --- | --- |
| RC-R1 | Operator-readable script output | Per-variation Hook / Body / CTA text (or copy-equivalent) is rendered as readable strings, not sentinel placeholders, when the underlying data exists. When data is genuinely absent, the row renders an explicit operator-language tracked-gap with the next action to take. |
| RC-R2 | Hook / Body / CTA structure | Each variation card exposes a Hook / Body / CTA decomposition that mirrors matrix_script_product_flow §4.1 + §6.1A. The structure is preserved even when one or more sections is empty (sentinel rendered, structure not collapsed). |
| RC-R3 | Multiple variant candidates | The Workbench C 预览对比区 lists all variation candidates with a one-line per-variant readable summary (axis tuple + script differentiator) so the operator can compare candidates without opening each variant. |
| RC-R4 | Recommended version | One variant per task is marked as the recommended version with operator-language reason text derived from the existing PR-1 unified `publish_readiness` producer's `head_reason`. The marker is framed as an actionable decision, not a passive badge. |
| RC-R5 | Delivery-ready copy/script package | The Delivery Center exposes, per variation, a delivery-ready copy/script package (script body + copy_bundle + per-deliverable status) so the operator can take a single readable bundle to a downstream channel. Existing MS-W7 single-source discipline preserved; gaps remain as explicit tracked-gap rows. |
| RC-R6 | Blocked / next-action state | Every operator-visible card exposes one of two operator-language statements: (a) "ready: do X next" with a concrete next action, or (b) "blocked: missing Y" naming exactly what is missing. No sentinel-only row is acceptable as a terminal operator state. |
| RC-R7 | Publish / backfill readiness surface | The publish-hub backfill view explains, per variation, what is and is not ready for publish: which variations are publishable now, which are gated, which already have a closure publish event, and what remaining input is required. Read-only over closure; no schema widening. |
| RC-R8 | No fake `final_video` | When no final video artifact exists for a variation, the surface MUST render an explicit tracked-gap with operator-language reason. **No synthesised `final_video_url`, no placeholder media, no "preview" labelled as deliverable.** |

These eight elements RC-R1..RC-R8 are the binding minimum. Any element not delivered at acceptance time fails the wave.

---

## 4. Forbidden Scope (binding red lines)

Recovery Wave PRs MUST NOT do any of the following. Any landed PR violating this section is rejected. These mirror amendment §7 verbatim plus the recovery-wave-specific scope-boundary additions.

### 4.1 Truth-source / contract preservation
- **No new contract authoring.** The recovery wave consumes existing contracts only (`matrix_script` packet truth; closure shape envelope; PR-1 `publish_readiness` producer; L3 `final_provenance`; L4 advisory emitter; `REVIEW_ZONE_VALUES`).
- **No closed-enum widening.** `task_entry_contract_v1`, `D1_EVENT_KINDS`, `D1_PUBLISH_STATUS_VALUES`, `D1_ROW_SCOPES`, `RECORD_KINDS`, `REVIEW_ZONE_VALUES`, `target_language` axis, canonical Phase B axes `{tone, audience, length}`, and `source_script_ref` accepted-scheme set `{content, task, asset, ref}` all remain frozen.
- **No second authoritative truth source.** Recommended-version reasoning, publish readiness, and advisory emission stay bound to the existing single producers.
- **No `source_script_ref` repurposing** as body-input or URL-ingestion or dereferenced content address.
- **No new packet truth** for `final_provenance`, copy_bundle subfields, or any other previously-unsourced data.

### 4.2 Cross-line preservation
- **No Hot Follow file touched** (Hot Follow stays benchmark; Hot Follow business behavior reopening forbidden).
- **No Digital Anchor file touched** (DA freeze preserved; DA remains NOT a trial candidate; the five operations findings unchanged).
- **No Asset Supply expansion** beyond consuming existing PR-2 read-only browse.
- No cross-cutting wiring change outside the existing per-line branches gated by `panel_kind == "matrix_script"` / `_ms_kind == "matrix_script"` / `kind == "matrix_script"`.

### 4.3 Wave-position preservation
- **No Platform Runtime Assembly** Phases A–E.
- **No Capability Expansion** W2.2 / W2.3 / durable persistence / runtime API / third production line.
- **No Plan A live-trial reopen for Matrix Script.** Plan A live-trial Matrix Script execution is sequenced after this wave closes AND a follow-on trial re-entry review for Matrix Script signs.
- **No Digital Anchor widening.** No DA scope re-evaluation.
- **No new operator-eligible discovery surface promotion.**

### 4.4 Scope-boundary preservation
- **No new structural surface modules.** No MS-W9 or wider. The recovery wave reorganizes / re-frames the existing eight MS-W* modules; it does not author a ninth.
- **No OWC-MS re-litigation.** OWC-MS PR-1 / PR-2 / PR-3 substrate stays merged. Reviewer-fail / new-defect corrections must be authored as separate narrow follow-up PRs citing the merged squash commits per existing forbidden-scope discipline; they are not rolled into this wave.
- **No surface deletion / removal.** The eight already-merged operator-visible modules stay rendered on `tasks.html`, `task_workbench.html`, `task_publish_hub.html`. The recovery wave reframes them; it does not delete them.
- **No provider / model / vendor / engine controls** or operator selector.
- **No donor namespace import** (`from swiftcraft.*`).
- **No React / Vite full rebuild** or new component framework / new build dependency.
- **No durable persistence backend swap**; in-process closure store is acceptable per Recovery Decision §4.3.
- **No bundling** of the recovery wave PR slices into a single PR; the §5 PR slicing plan is binding.

### 4.5 Closeout-paperwork independence
- Forcing, accelerating, conditioning, or tying the Recovery Wave implementation gate opening or closing to any prior closeout signoff (Recovery PR-1..PR-4 closeouts, Plan E A7 / UA7 / RA7 phase closeouts, OWC-MS Closeout MS-A7, OWC-DA Closeout DA-A7, Track A Hot-Follow-only window signoff) is forbidden. Each closeout stays independently pending in its respective owner queue.
- Track A (Hot-Follow-only Plan A live-trial window) signoff is **informational input only**, not a hard predecessor on this gate spec authoring, on §10 signoff, or on implementation-PR opening (per amendment §6).

---

## 5. PR Slicing Plan (binding)

The recovery wave lands in exactly four sequential implementation PRs followed by one aggregating closeout PR. Bundling is forbidden.

| PR | Title | Slice (RC-R items) | Ordering |
| --- | --- | --- | --- |
| RC PR-1 | Result-oriented Task Area / Workbench summary projection | RC-R6 (blocked / next-action state on Task Area cards + Workbench summary header) — operator-language "ready: do X next" / "blocked: missing Y" framing layered over the existing PR-1 `publish_readiness` + L4 advisory output already rendered by MS-W2 / MS-W6 | First; opens after §10 signoff |
| RC PR-2 | Operator-readable script / variant candidate package | RC-R1 + RC-R2 + RC-R3 — readable Hook / Body / CTA per variation in the Workbench A read-view; multi-variant candidate listing with one-line per-variant summary in Workbench C; explicit tracked-gap when underlying data is absent | After RC PR-1 merged + reviewed |
| RC PR-3 | Recommended-version + next-action lane | RC-R4 — recommended-version marker promoted from passive badge to actionable decision row (operator-language reason from existing `head_reason`; link / scroll target to the next action surface); preserves single-producer discipline | After RC PR-2 merged + reviewed |
| RC PR-4 | Delivery-ready copy/script package + publish/backfill readiness | RC-R5 + RC-R7 + RC-R8 — Delivery Center per-variation delivery-ready bundle row; publish-hub backfill readiness explanation per variation; explicit tracked-gap (NEVER synthesised) when `final_video` is absent | After RC PR-3 merged + reviewed |
| RC Closeout | Aggregating audit + signoff | (none — paperwork only) | After RC PR-4 merged + reviewed |

### 5.1 Per-PR file isolation contract

Each Recovery Wave PR MUST satisfy:

- Service files: only `gateway/app/services/matrix_script/*` and the cross-cutting wiring seam files (`wiring.py`, `task_view_helpers.py`, `task_view_presenters.py`, `task_router_presenters.py`, `publish_hub_pr3_attach.py`) restricted to the existing matrix_script branch.
- Templates: only the existing `{% if line_id == "matrix_script" %}` block in `tasks.html`, the existing matrix_script panel branch in `task_workbench.html`, and the existing `_ms_kind == "matrix_script"` block in `task_publish_hub.html`. The eight MS-W* modules already rendered remain in place; the recovery wave reframes their projection, not their position.
- Tests: each new helper / projection module gets a dedicated import-light test file under `gateway/app/services/tests/`.
- Hot Follow files: byte-stable.
- Digital Anchor files: byte-stable.
- Asset Supply files: read-only consumption only.

### 5.2 Test floor per PR

- RC PR-1: ≥25 test cases covering blocked / next-action derivation across the eight Task Area stages, isolation from Hot Follow / Digital Anchor.
- RC PR-2: ≥35 test cases covering readable script-structure derivation, multi-variant candidate listing, tracked-gap rendering when source data absent, no operator authoring of `source_script`.
- RC PR-3: ≥25 test cases covering recommended-version actionable row, single-producer discipline (head_reason / publish_readiness consumed verbatim), no second producer.
- RC PR-4: ≥35 test cases covering per-variation delivery bundle row, publish-hub backfill readiness explanation, no fake `final_video` synthesis, no closure schema widening.

---

## 6. Acceptance Evidence (binding rows)

The Recovery Wave Closeout document MUST record the following rows as PASS / FAIL with explicit evidence pointer. Each PR MUST prove **not just that fields are visible**, but that the operator can understand what to do next.

| Row | Check | Evidence requirement |
| --- | --- | --- |
| RC-A1 | RC PR-1 implementation green and merged | execution log + diff + PR # + squash commit |
| RC-A2 | RC PR-2 implementation green and merged | execution log + diff + PR # + squash commit |
| RC-A3 | RC PR-3 implementation green and merged | execution log + diff + PR # + squash commit |
| RC-A4 | RC PR-4 implementation green and merged | execution log + diff + PR # + squash commit |
| RC-A5 | Operator-comprehension demonstration (per PR) — at least one sample task per PR scope produces usable script / copy / package output that an operator can act on without consulting the engineering log; recorded as a captured operator-language walkthrough in each PR's execution log | per-PR operator walkthrough block in execution log |
| RC-A6 | No fake `final_video` audit — every code path that renders a delivery / publish-hub row when no closure / artifact exists is verified to emit an explicit tracked-gap, never a synthesised URL or media reference | row table in closeout pointing at the relevant tests in §5.2 |
| RC-A7 | No second truth source audit — recommended-version, publish readiness, and advisory emission consume only the PR-1 unified producer / L3 emitter / L4 emitter; no parallel derivation introduced | row table in closeout pointing at the producer call sites |
| RC-A8 | No vendor / model UI audit — no `vendor_id` / `model_id` / `provider_id` / `engine_id` / donor namespace identifier surfaces on any operator-visible payload | row table in closeout aggregating across PR-1..PR-4 |
| RC-A9 | No Digital Anchor widening audit — DA files byte-stable; the five operations findings (post-OWC addendum §2.3.1) unchanged | row table in closeout pointing at `git diff --stat` excerpt |
| RC-A10 | No Hot Follow runtime change audit — Hot Follow files byte-stable; golden-path live regression confirmation block | coordinator confirmation block in closeout |
| RC-A11 | §4 forbidden-scope audit (full pass on §4.1–§4.5) | row table in closeout matching §4 sub-sections |
| RC-A12 | Product-Flow Module Presence rule (ENGINEERING_RULES §13) — each MS-W* module reframed by the recovery wave is verified to still render operator-visibly on the relevant template, and the new result-oriented projection is verified to be operator-comprehensible | reviewer walks through `tasks.html` / `task_workbench.html` / `task_publish_hub.html` Matrix Script blocks |
| RC-A13 | Recovery Wave Closeout signoff (Architect Raobin + Reviewer Alisa + Coordinator Jackie + Product Manager) | filled signoff block in closeout |

The §3 minimum result elements RC-R1..RC-R8 map to the acceptance rows as follows: RC-R1+R2+R3 → RC-A2 + RC-A5 (PR-2 walkthrough); RC-R4 → RC-A3 + RC-A5 (PR-3 walkthrough); RC-R5+R7 → RC-A4 + RC-A5 (PR-4 walkthrough); RC-R6 → RC-A1 + RC-A5 (PR-1 walkthrough); RC-R8 → RC-A6.

---

## 7. Preserved Freezes (binding)

The following are preserved verbatim by every Recovery Wave PR. Any PR that mutates them is rejected.

- Hot Follow runtime + workbench + delivery + publish + reference packet.
- Digital Anchor formal entry route + payload builder + closure binding + role/speaker surface attachment + D.1 write-back + DA-W1..DA-W9 modules as shipped by OWC-DA PR-1..PR-3.
- The five Digital Anchor operations findings (post-OWC addendum §2.3.1) — DA remains NOT a trial candidate.
- Asset Supply minimum capability as shipped by Recovery PR-2.
- PR-1 unified `publish_readiness` producer + L3 `final_provenance` emitter + L4 `advisory_emitter`.
- Matrix Script §8.A–§8.H closeout truth (correction chain CLOSED).
- Matrix Script frozen packet truth (envelope E1–E5 + validator R1–R5 admission cells PASS).
- OWC-MS MS-W1..MS-W8 merged substrate (reframed, not deleted).
- Closure shape envelope, `D1_EVENT_KINDS`, `D1_PUBLISH_STATUS_VALUES`, `D1_ROW_SCOPES`, `RECORD_KINDS`, `REVIEW_ZONE_VALUES` (both Matrix Script and Digital Anchor).
- Trial re-entry review §8 four-party signoff (binding audit record on the review as authored — never retracted).
- Plan E phase closeout signoffs (A7 / UA7 / RA7), OWC-MS Closeout MS-A7, OWC-DA Closeout DA-A7 — all remain independently pending in Raobin / Alisa / Jackie / product-manager queues and are NOT advanced by any Recovery Wave PR.

---

## 8. Stop Conditions (binding)

A Claude execution agent MUST stop and request architect review if any Recovery Wave PR encounters:

- A required result-capability element cannot land without packet / schema / contract / closed-enum mutation.
- A required projection cannot derive from existing four-layer state + Recovery PR-1..PR-4 substrate + OWC-MS reframed substrate.
- Hot Follow business behavior must change to make a test pass.
- Digital Anchor file must be touched.
- A second authoritative producer is required.
- A new structural surface module (MS-W9 or wider) is required.
- The only way to satisfy RC-R8 (no fake `final_video`) is to synthesise a placeholder URL or to re-route a non-final artifact as final.

The default action on a stop condition is to NOT widen scope. Re-plan via a new gate-spec authoring step instead.

---

## 9. Review / Signoff Rule

Recovery Wave PR review applies ENGINEERING_RULES §13 (Product-Flow Module Presence) plus the existing five-row review augmented with one result-capability row:

| Row | Check | Source |
| --- | --- | --- |
| R1 | Contract / runtime truth — no out-of-scope mutation; no new contract; no closed-enum widening | recovery amendment §7 + ENGINEERING_RULES §6 / §7 |
| R2 | Byte-isolation — Hot Follow + Digital Anchor unchanged; matrix_script edits inside per-line gates | recovery amendment §7 + Recovery Global Action §2 |
| R3 | Forbidden-scope — no Platform Runtime Assembly / Capability Expansion / provider controls / new line / Asset Supply expansion / React rebuild / new structural surface module | recovery amendment §7 + this gate spec §4 |
| R4 | Unified-producer consumption — no second truth source; PR-1 producers consumed verbatim | PR-1 acceptance + this gate spec §4.1 |
| R5 | **Product-flow module presence** — each MS-W* module reframed by the PR is operator-visible on the relevant template | ENGINEERING_RULES §13 + matrix_script_product_flow §§5–7 |
| R6 | **Result-capability presence** — the PR's RC-R items in scope deliver an operator-understandable, result-oriented deliverable path; the PR's execution log carries the §6 RC-A5 operator walkthrough block | this gate spec §3 + §6 |

Recovery Wave Closeout signoff matrix:

- Architect (Raobin) — R1 + R2 + R3 + R4 audit; recovery amendment §7 hard-boundary audit.
- Reviewer (Alisa) — independent re-verification of R1..R6.
- Product Manager — R5 product-flow conformance audit + R6 result-capability conformance audit + go/no-go.
- Coordinator (Jackie) — byte-isolation regression + Hot Follow / Digital Anchor / Asset Supply preservation + RC-A5 operator walkthrough confirmation.

---

## 10. Architect + Reviewer Signoff (gate-opening)

§10 lines must be filled in a documentation-only PR before Recovery Wave RC PR-1 may open. **The implementation gate is gate spec §10 architect (Raobin) + reviewer (Alisa) signoff merging to `main`** — not Track A's Hot Follow live-trial signoff. Until both are filled, the Recovery Wave implementation gate is CLOSED.

- **Architect** (Raobin): `<fill>` — filled at `<YYYY-MM-DD HH:MM>` against this gate spec authoring commit.
- **Reviewer** (Alisa): `<fill>` — filled at `<YYYY-MM-DD HH:MM>` against this gate spec authoring commit.
- **Operations Coordinator** (Jackie): `<fill>` — coordinator signoff binds Recovery Wave Closeout row RC-A13, not gate opening.
- **Product Manager**: `<fill>` — product manager signoff binds Recovery Wave Closeout row RC-A13, not gate opening.

---

## 11. Successor Phase

Successor sequence (per recovery amendment §6 Track B steps B5..B8):

1. **Recovery Wave Closeout** — aggregating audit + signoff per §6 / §10 above.
2. **Follow-on trial re-entry review for Matrix Script** — separate docs-only review evaluating, against the post-recovery state, whether Matrix Script meets a result-capability bar sufficient for live-trial re-entry. Updates Plan A §12 readiness conclusion for Matrix Script. Signed by architect + reviewer + coordinator + product manager.
3. **Plan A live-trial Matrix Script execution** — operations team runs Plan A §7.1 samples 3 / 4 / 5 (`mm` / `vi` / post-§8.F) plus the Matrix Script portion of sample 6 (cross-line Board inspection).
4. **Matrix Script live-trial findings + four-party signoff** (Track B step B8).

**Other waves remain BLOCKED** per the recovery amendment §6 + §8:

- **Platform Runtime Assembly Wave**: BLOCKED until **both** Track A's Hot Follow live-trial signoff (Track A step A3) AND Track B's Matrix Script live-trial signoff (Track B step B8) land. The Recovery Wave's gate spec, implementation, and closeout are all internal to Track B; they do not unblock Platform Runtime Assembly on their own.
- **Capability Expansion Gate Wave**: BLOCKED until Platform Runtime Assembly signoff.
- **Plan E A7 / UA7 / RA7 closeout signoffs**: remain independently pending.
- **Digital Anchor scope widening**: forbidden; the five operations findings remain in force.

---

## 12. Authority Pointers

- [docs/product/OPERATIONS_TRIAL_READINESS_MATRIX_SCRIPT_RECOVERY_AMENDMENT_v1.md](../product/OPERATIONS_TRIAL_READINESS_MATRIX_SCRIPT_RECOVERY_AMENDMENT_v1.md)
- [docs/product/matrix_script_product_flow_v1.md](../product/matrix_script_product_flow_v1.md)
- [docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md](../architecture/apolloveo_2_0_top_level_business_flow_v1.md)
- [docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md](../architecture/apolloveo_2_0_unified_alignment_map_v1.md) §7
- [docs/design/ApolloVeo_Operator_Visible_Surfaces_v1.md](../design/ApolloVeo_Operator_Visible_Surfaces_v1.md)
- [docs/reviews/owc_ms_gate_spec_v1.md](owc_ms_gate_spec_v1.md)
- [docs/reviews/trial_reentry_review_v1.md](trial_reentry_review_v1.md)
- [docs/execution/APOLLOVEO_2_0_OWC_MS_PHASE_CLOSEOUT_v1.md](../execution/APOLLOVEO_2_0_OWC_MS_PHASE_CLOSEOUT_v1.md) §8 (tracked gaps inherited)
- [docs/execution/apolloveo_2_0_evidence_index_v1.md](../execution/apolloveo_2_0_evidence_index_v1.md)
- [docs/contracts/matrix_script/](../contracts/matrix_script/) (frozen substrate; no mutation)
- [docs/contracts/publish_readiness_contract_v1.md](../contracts/publish_readiness_contract_v1.md) (PR-1; consumed verbatim)
- [docs/contracts/workbench_panel_dispatch_contract_v1.md](../contracts/workbench_panel_dispatch_contract_v1.md)
- [docs/contracts/factory_delivery_contract_v1.md](../contracts/factory_delivery_contract_v1.md) (Plan C amendments)

---

## 13. Reading Declaration

Authority files read before authoring this gate spec, in `CLAUDE.md` §2 boot-sequence order:

1. `CLAUDE.md` (bootloader).
2. `ENGINEERING_RULES.md` (engineering governance, §13 Product-Flow Module Presence).
3. `CURRENT_ENGINEERING_FOCUS.md` (active wave + forbidden work, post-amendment state).
4. `ENGINEERING_STATUS.md` (stage / gate / completion log).
5. `docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md` (§7 bifurcated frozen sequence).
6. `docs/product/OPERATIONS_TRIAL_READINESS_MATRIX_SCRIPT_RECOVERY_AMENDMENT_v1.md` (binding scope authoriser).
7. `docs/product/matrix_script_product_flow_v1.md` (line-specific product flow).
8. `docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md` (factory-wide flow).
9. `docs/design/ApolloVeo_Operator_Visible_Surfaces_v1.md` (operator-visible surface authority).
10. `docs/reviews/trial_reentry_review_v1.md` (SIGNED; partially superseded for MS scope by amendment).
11. `docs/reviews/owc_ms_gate_spec_v1.md` (preserved substrate; surface module template).
12. `docs/execution/APOLLOVEO_2_0_OWC_MS_PHASE_CLOSEOUT_v1.md` (tracked gaps §8 inherited).
13. `docs/execution/apolloveo_2_0_evidence_index_v1.md` (evidence index format).

No code files were read. No contract or schema files were read. No implementation work is opened by this gate spec.
