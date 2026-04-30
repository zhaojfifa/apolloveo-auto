# W2.1 Admission Signoff — Phase E (v1)

- Date: 2026-04-27
- Wave: ApolloVeo 2.0 W2 Admission Preparation — Phase E only
- Roles: ApolloVeo L5 Architect + Reviewer / Merge Owner (combined gate)
- Authority chain (read-only at this gate; no reopens):
  - `docs/architecture/ApolloVeo_2.0_W2_Admission_Preparation_Wave_指挥单_v1.md` §4 Phase E, §9, §10, §11
  - `docs/reviews/W1_COMPLETION_REVIEW_v1.md` §3.1, §3.2
  - `docs/execution/evidence/w2_admission_phase_a_guardrail_foundation_v1.md`
  - `docs/execution/evidence/w2_admission_phase_b_env_matrix_v1.md`
  - `docs/execution/evidence/w2_admission_phase_c_donor_lifecycle_freeze_v1.md`
  - `docs/reviews/W2_ADMISSION_ADAPTERBASE_LIFECYCLE_REVIEW_v1.md`
  - `docs/execution/evidence/w2_admission_phase_d_hot_follow_regression_freeze_v1.md`
- Latest mainline tip considered: `e98ca65` (Phase D evidence freeze commit)
- W2 donor SHA pin: `62b6da0` (recorded 2026-04-26 as the W2 admission pin)

> **Scope hard stop.** This document only opens and closes Phase E. It does not absorb provider code, does not implement AdapterBase lifecycle methods, does not edit Hot Follow, and does not reopen Phase A / B / C / D.

---

## 1. Combined admission baseline (A + B + C + D)

The four admission phases are read as one gate. Each phase's hard-stop discipline (no provider code, no Hot Follow business edits, no AdapterBase implementation) was preserved across the chain — verified by inspecting each evidence file's "What was intentionally not done" section and confirming no overlap or contradiction between phases.

| Phase | Deliverable | Evidence | State |
|---|---|---|---|
| A | `tests/guardrails/` host + provider-leak / donor-leak / fallback-never-primary-truth tests (7/7 passed; AST-based, zone inventory sanity assertions) | Phase A evidence v1 | ✅ green |
| B | `ops/env/env_matrix_v1.md` + `storage_layout_v1.md` + `secret_loading_baseline_v1.md`; O-01/O-02 lifecycle flipped `Not started → In progress` at PR-open per W1 review §3.1.6 | Phase B evidence v1 | ✅ green |
| C | Fresh W2 donor SHA pin (`62b6da0`, explicit re-pin not silent reuse — closes W1 review §3.1.1); mapping row lifecycle freeze (§3.1–§3.5); AdapterBase lifecycle review with 4 frozen gaps + 7 frozen rules | Phase C evidence v1 + AdapterBase lifecycle review v1 | ✅ green |
| D | Hot Follow regression baseline frozen at commit `c128b2b`: 183 green / 9 known-red pinned; guardrails 7/7; packet validator anchor 2/2; protected contracts (§2.1) and runtime modules (§2.2) frozen for W2.x | Phase D evidence v1 | ✅ green |

### 1.1 Cross-phase consistency check

- **No phase modified an earlier phase's artefact.** Phase B did not touch `tests/guardrails/`. Phase C did not touch `ops/env/` or `tests/guardrails/`. Phase D did not touch any of A/B/C. Verified per each phase's "files touched" section.
- **Donor pin discipline holds end-to-end.** Pin `62b6da0` is the W1 pin; Phase C explicitly re-records it as the W2 admission pin (closes the "no silent reuse" hard gate). Mapping doc lifecycle column matches reality (M-01..M-05 = Absorbed; O-01, O-02 = In progress; O-03 = Not started, deploy-pipeline move deferred).
- **Guardrail authority is uncontested.** Phase A guardrails enforce three contract-level invariants from the runtime side; Phase C lifecycle review §4 freezes seven governance rules from the boundary side; Phase D §2 freezes Hot Follow protected paths. The three layers compose without conflict.
- **Hot Follow is never the experimental ground.** Phase D §3.1/§3.2/§3.3 cite the exact behaviours W2.1, W2.2, and W2.3 may not break; the 9 known-red cases are explicitly attributed as pre-existing on mainline (`c128b2b` is mainline tip at Phase D open), not introduced by W2 admission work.

### 1.2 Directive §9 unlock conditions — combined status

| §9 item | Source | Status |
|---|---|---|
| 1. `tests/guardrails/` built and passing | Phase A | ✅ green |
| 2. Provider leak tests in place | Phase A | ✅ green |
| 3. Fallback-never-primary-truth tests in place | Phase A | ✅ green |
| 4. O-01 ~ O-03 env matrix in place | Phase B | ✅ green |
| 5. Fresh W2 donor SHA pin in mapping doc | Phase C | ✅ green |
| 6. AdapterBase lifecycle review passed | Phase C | ✅ green (review-only; 4 base-only gap-closing PRs identified as W2.1 prerequisites) |
| 7. Hot Follow regression baseline freeze done | Phase D | ✅ green (183 green / 9 known-red pinned) |
| 8. Reviewer signoff ready | Phase E (this doc) | ✅ green — see §3 |
| 9. Architect signoff ready | Phase E (this doc) | ✅ green — see §2 |

All nine items are now green. Phase E does not unlock provider code on its own; it unlocks the next allowed unit of work, which is the four base-only AdapterBase PRs (see §5).

---

## 2. Architect signoff (combined A+B+C+D)

**Acting as ApolloVeo L5 Chief Architect.**

I have read the directive `ApolloVeo_2.0_W2_Admission_Preparation_Wave_指挥单_v1.md` end-to-end and the four phase evidence files plus the AdapterBase lifecycle review. My architectural assessment:

1. **The admission room is correctly sealed.** Three independent enforcement layers exist (runtime guardrails, governance lifecycle rules, regression baseline), and they do not duplicate or contradict. The "fallback never primary truth" rule is enforced from runtime (Phase A test), boundary (Phase C lifecycle review §4 rule 7), and Hot Follow protected-path freeze (Phase D §2.3).
2. **The donor surface is correctly frozen.** SHA `62b6da0` is explicitly re-pinned, the mapping row lifecycle is now codified (states, transitions, frozen attributes, drift-control), and the no-row-edit-without-PR rule closes the silent-drift vector W1 review §3.1.6 flagged.
3. **AdapterBase is correctly bounded.** The lifecycle review's 4 frozen rules (separate-PR discipline, closed kind set, vendor-pin prohibition, no truth writes) plus the 4 deferred gaps (auth, retry, error envelope, construction lifecycle) form a complete admission contract. The base is *adequate as a skeleton* and *inadequate as a W2.1 launch contract* — exactly the right framing.
4. **Hot Follow is correctly insulated.** The 183-green / 9-known-red snapshot at `c128b2b` is reproducible (canonical pytest command pinned), and the §3.1/§3.2/§3.3 invariants tell each W2.x sub-wave precisely what it may not break. The 9 known-red set is correctly attributed to pre-existing mainline state and not weaponised as an excuse to weaken the baseline.
5. **No scope creep.** None of the four phases absorbed provider code, implemented AdapterBase lifecycle methods, modified Hot Follow business logic, or expanded frontend / workbench scope. The directive's red lines (§7) are all preserved.

**Architect verdict on combined A+B+C+D as the W2.1 admission baseline:** **PASS.** The admission room is built, sealed, and audit-ready. The base-only AdapterBase PRs are the only remaining work between this signoff and the first W2.1 provider absorption PR; Phase E does not block on those PRs landing because they are W2.1 prerequisites, not Phase E prerequisites (per Phase C evidence §6 item 2 and Phase D evidence §8 item 2).

---

## 3. Reviewer / Merge Owner signoff (combined A+B+C+D)

**Acting as W2 Admission Wave Merge Owner.**

I have audited the four admission phases against the directive's §6 reviewer checklist and §11 总控口令:

1. **`tests/guardrails/` is established and executable.** Confirmed: 7/7 passing on Phase A; re-verified 7/7 on Phase D. AST-based scanning eliminates substring false positives; zone-inventory sanity assertions prevent silent vacuity under future layout moves.
2. **Env matrix is in place and reusable downstream.** Confirmed: `ops/env/env_matrix_v1.md` + `storage_layout_v1.md` + `secret_loading_baseline_v1.md`; key-name constancy across local/render/production is explicit; the no-hardcoded-token rule is written in two places (matrix §5 + baseline §4) for redundancy. The W2.1 PR checklist already exists in the loading baseline.
3. **Donor pin and mapping lifecycle are synchronised.** Confirmed: SHA `62b6da0` is explicitly stamped as the W2 admission pin; mapping rows for M-01..M-05 = Absorbed (W1 closure); O-01, O-02 = In progress (PR-open flip); lifecycle states / transitions / frozen attributes are codified in §3 of the mapping doc.
4. **Hot Follow baseline freeze has objective evidence.** Confirmed: reproducible pytest command, 192 cases at `c128b2b`, 183/9 green/red split, guardrails companion suite green, packet validator anchor green. The 9 known-red set is enumerated by file + case id so future drift is line-attributable.
5. **No provider absorption code is present in this wave.** Confirmed: no files added under `gateway/app/services/providers/`, `gateway/adapters/`, or `gateway/app/services/capability/adapters/`; no `os.getenv` call sites added; no Hot Follow runtime module touched; no AdapterBase implementation diff.
6. **`main` is a valid sole baseline for W2.1 entry.** Confirmed: tip is `e98ca65`; admission chain commits (Phase A test host #60, Phase B matrix #61, Phase C donor/lifecycle freeze, Phase D Hot Follow freeze) form a clean linear ancestry; Evidence Index v1 indexes all four artefacts.

**Reviewer verdict on combined A+B+C+D as the W2.1 admission baseline:** **PASS.** The admission wave is closeable, scope is clean, and no provider PR was smuggled in. I do not approve any W2.2 / W2.3 scope, any Hot Follow business edit, any AdapterBase implementation diff, or any "while we're here" cleanup as part of this signoff.

---

## 4. Explicit judgment

### 4.1 Required judgment form (verbatim per the W2.1 admission directive)

- **Phase E admission: PASS** (combined architect + reviewer signoff, no contradictions across A+B+C+D, all §9 items 1–7 green, signoffs 8 & 9 issued by this document).
- **W2.1 implementation: BLOCKED** (admission gate is open; first provider absorption PR is still blocked on the four base-only AdapterBase PRs — see §5).
- **W2.2: BLOCKED** (admission gate does not authorise W2.2; additional W2.2-specific blockers listed in §6).
- **W2.3: NOT EVALUATED** (planning-only per directive §10; explicitly out of scope for this signoff).

### 4.2 Is W2.1 admission conditionally approved?

**Yes — W2.1 is conditionally admitted.** The admission *room* is open; the admission *condition* attached to entering W2.1 implementation is the closure of the four base-only AdapterBase PRs identified by `W2_ADMISSION_ADAPTERBASE_LIFECYCLE_REVIEW_v1.md` §5. Until those land as separate, base-only PRs (no provider code, no provider absorption bundling), the first W2.1 provider absorption PR may not open.

### 4.3 Separation of blockers

Per the directive's instruction to keep these explicitly separated:

#### 4.3.1 Phase E blocker — **NONE REMAINING**
Phase E is closed by this document. Architect signoff issued (§2). Reviewer signoff issued (§3). Admission gate state for Phases A+B+C+D is now PASS.

#### 4.3.2 W2.1 implementation blocker — **FOUR BASE-ONLY ADAPTERBASE PRs**
The first W2.1 (Understanding Provider Absorption) PR may NOT open until all four of the following land as separate, base-only PRs (each its own review, each cited by the W2.1 entry note):

1. **B1.** `AdapterBase` auth / credential surface — credential resolver injected at construction, not at `invoke`. Closes lifecycle review §3.1.
2. **B2.** `AdapterBase` retry / timeout / cancellation policy — declarable on the base; not provider-SDK-specific. Closes lifecycle review §3.2.
3. **B3.** `AdapterBase` error envelope (`AdapterError` or equivalent) — advisory-shaped, not truth-shaped, preserves no-truth-writes invariant. Closes lifecycle review §3.3.
4. **B4.** `AdapterBase` construction-vs-invocation lifecycle — forbids I/O at construction; first I/O reachable only via `invoke`. Closes lifecycle review §3.5.

These four PRs are also the *exact* allowed scope for any AdapterBase extension before W2.1 (lifecycle review §5). Anything else is out of scope until W2.2 or later.

In addition, per directive §10 W2.1 entry rules, the W2.1 entry note must (when authorised) restate: donor SHA pin `62b6da0`, env matrix reference, guardrails reference, and Phase D baseline as the regression anchor. That entry note is produced at W2.1 open, not at this signoff.

#### 4.3.3 W2.2 blocker — **HOT FOLLOW REGRESSION RESOLUTION + W2.2-SCOPED REVIEW**
W2.2 (Subtitles / Dub Provider Absorption) is the highest-risk wave per W1 review §3.2 R5 because it overlaps Hot Follow's frozen subtitle/dub paths. W2.2 is BLOCKED until:

1. **HF1.** The 9 known-red cases pinned in Phase D §4.2 are resolved by a separate Hot Follow regression PR cited as a W2.2 prerequisite (Phase D evidence §8 item 3). Phase D explicitly does not block on these for W2.1 admission, but does block on them for W2.2.
2. **HF2.** Phase D regression baseline is re-run on the W2.2 candidate HEAD and the green set has not regressed (Phase D §5 procedure).
3. **HF3.** A W2.2-specific lifecycle/risk review exists for `SubtitlesAdapter` and `DubAdapter` covering the Hot Follow adjacency invariants in Phase D §3.2 (no `selected_compose_route` change, no `tts_replace_route` vs preserve-source collapse, no `compose_*` derivation change, no subtitle-authority second owner, no provider-side fallback into the artefact path).
4. **HF4.** W2.1 itself must be CLOSED first per directive §10 sequencing.

#### 4.3.4 W2.3 — **NOT EVALUATED THIS WAVE**
W2.3 (Avatar / VideoGen / Storage Provider Absorption) is planning-only per directive §10. No admission attempt may be made for W2.3 before W2.2 is closed and a W2.3-scoped admission preparation wave is authorised. Directive §10 requires duplicate reconciliation (Akool P-01 vs P-02 collision per W1 review §3.2 R3) prior to any W2.3 PR.

---

## 5. The four base-only AdapterBase PRs (commission target, not implementation)

This signoff *commissions* the four base-only PRs B1–B4 (§4.3.2) but does NOT start them. Each must:

- be its own PR with its own review,
- touch only `gateway/app/services/capability/adapters/base.py` and (where strictly required) the kind subclasses,
- carry no provider SDK / client code,
- carry no env-matrix or guardrail edit,
- carry no Hot Follow edit,
- cite this signoff (`docs/reviews/W2_ADMISSION_SIGNOFF_v1.md` §4.3.2 + the lifecycle review §5),
- preserve the seven frozen rules in lifecycle review §4 (in particular: no I/O at import or construction, donor-free base, fallback never primary truth, vendor-pin prohibition).

Bundling any two of B1–B4 into one PR is a contract violation. Bundling any of B1–B4 with a provider absorption PR is a contract violation regardless of size (lifecycle review §4 rule 1).

The order in which B1–B4 land is the next commander's call; this signoff does not pre-order them.

---

## 6. What this signoff does NOT authorise (red lines preserved)

Per directive §7 and the user's hard-stop instructions accompanying this Phase E request:

- ❌ No provider SDK / client absorption.
- ❌ No AdapterBase lifecycle method implementation in this wave (B1–B4 are commissioned, not implemented).
- ❌ No Hot Follow business code change. The 9 known-red cases are not resolved by Phase E.
- ❌ No reopening of Phase A / B / C / D (no contradiction was found across the chain that would justify a reopen).
- ❌ No W2.2 admission, no W2.3 admission.
- ❌ No frontend / workbench scope expansion.
- ❌ No `scripts/render_preflight.sh` move to `ops/runbooks/` (O-03 deploy-pipeline decision is still deferred, per Phase B §6).
- ❌ No relocation of W1 absorption tests out of `tests/services/media/` (Phase A §4 already declined this; Phase E does not reopen).

---

## 7. Hard stop confirmation

After this signoff, work stops and waits for the four base-only AdapterBase PRs (B1–B4) to be commissioned by the commander. W2.1 code absorption is NOT to be started yet. Hot Follow business code remains frozen. The next allowed unit of work is one of: (a) commissioning B1–B4 as four separate base-only PRs, or (b) authorising an unrelated wave outside W2 admission.

Phase E's hard stop is symmetrical with each prior phase's hard stop: this document closes the gate it opened, and does not auto-start the next gate.

---

## 8. Files touched by this wave

- created: `docs/reviews/W2_ADMISSION_SIGNOFF_v1.md` (this file)

No code under `gateway/`, `tests/`, `ops/env/`, `services/`, donor-derived directories, or any Phase A / B / C / D evidence file was modified by this wave.

The Evidence Index v1 update for this signoff is the single follow-up write-back required by directive §8; that write-back is owned by the merge step that lands this document (it is not a reopen of any prior phase).

---

## 9. One-line verdict

**Phase E: PASS. W2.1 implementation: BLOCKED on B1–B4. W2.2: BLOCKED on HF1–HF4 + W2.1 closure. W2.3: NOT EVALUATED. Stop here and wait for B1–B4 commissioning.**
