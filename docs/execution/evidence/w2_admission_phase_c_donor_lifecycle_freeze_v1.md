# W2 Admission Preparation — Phase C: Donor / Lifecycle Freeze (v1)

- Date: 2026-04-26
- Wave: ApolloVeo 2.0 W2 Admission Preparation — Phase C only
- Authority:
  - `docs/architecture/ApolloVeo_2.0_W2_Admission_Preparation_Wave_指挥单_v1.md` §4 Phase C, §9
  - `docs/reviews/W1_COMPLETION_REVIEW_v1.md` §3.1.1 / §3.1.2 / §3.1.6
  - `docs/donor/swiftcraft_donor_boundary_v1.md` §3, §4, §5, §8
  - `docs/donor/swiftcraft_capability_mapping_v1.md` §0, §3 (post-Phase-C)
  - `docs/reviews/W2_ADMISSION_ADAPTERBASE_LIFECYCLE_REVIEW_v1.md`
- Phase A evidence (already green): `docs/execution/evidence/w2_admission_phase_a_guardrail_foundation_v1.md`
- Phase B evidence (already green): `docs/execution/evidence/w2_admission_phase_b_env_matrix_v1.md`

---

## 1. Scope

This wave delivers ONLY the governance / review artefacts required by the W2 Admission directive §4 Phase C:

1. fresh W2 donor SHA pin in mapping doc;
2. mapping row lifecycle freeze + update rules made explicit;
3. AdapterBase lifecycle review as a separate authority doc;
4. evidence write-back into the Evidence Index.

This wave does NOT:

- absorb provider SDK/client code;
- implement AdapterBase lifecycle methods (auth, retry, error envelope, construction hook);
- wire any provider runtime;
- modify Hot Follow main-line behaviour;
- expand the env / secret matrix beyond clarification fixes (none required this wave).

---

## 2. What was added / updated

### 2.1 Donor SHA pin (fresh W2 admission pin)
- File: `docs/donor/swiftcraft_capability_mapping_v1.md`
- Header line added: explicit "P2 absorption wave 2 admission" pin recorded 2026-04-26 with donor SHA `62b6da0`.
- §0 table reshaped: per-sub-wave rows (W2 admission, W2.1, W2.2, W2.3) with explicit notes.
- Donor HEAD verified equal to the W1 pin. The re-pin is *explicit*, not silent reuse — closing W1 review §3.1.1's hard gate ("do not silently reuse the W1 pin"). The rule that a wave records its own pin row even when SHA does not move is now codified at the bottom of §0.
- Verification command (re-runnable): `cd /Users/tylerzhao/Code/swiftcraft && git log -1 --format="%h"` returns `62b6da0` at the time of this evidence.

### 2.2 Mapping row lifecycle freeze
- File: `docs/donor/swiftcraft_capability_mapping_v1.md` §3 (replaced).
- §3 split into: state definitions (§3.1), freeze rules (§3.2), update rules (§3.3), drift control (§3.4), no-row-edit-without-PR rule (§3.5).
- Freeze rules pin: row id, donor path, Apollo target, strategy, capability/contract binding.
- Update rules constrain: status transitions (PR-open, not PR-merge — closes W1 review §3.1.6), acceptance criteria changes (tightening allowed; loosening only with architect signoff), pin row notes (SHA itself immutable).
- Drift control re-cites Phase A guardrails (`tests/guardrails/test_donor_leak_boundary.py`) and W1 attribution-header evidence as the runtime/audit detection paths.

### 2.3 AdapterBase lifecycle review (standalone authority doc)
- File created: `docs/reviews/W2_ADMISSION_ADAPTERBASE_LIFECYCLE_REVIEW_v1.md`.
- Surveys the existing `gateway/app/services/capability/adapters/base.py` against W2.1 needs.
- Identifies 4 deferred gaps (auth/credential, retry/timeout/cancellation, error envelope, construction-vs-invocation lifecycle) and 2 review-confirmed adequacies (advisory-vs-truth shape, rule-version provenance).
- Freezes 7 governance rules (§4) and 4 base-only-PR gates (§5) that must close before W2.1 first absorption PR.
- **Critical rule frozen:** any AdapterBase extension is its own PR; bundling with a provider absorption PR is a contract violation regardless of size.
- This review does NOT propose, draft, or implement any base code change. Phase C is review-only per directive §3.3.

### 2.4 Evidence Index write-back
- File updated: `docs/execution/apolloveo_2_0_evidence_index_v1.md`
- New rows added under §"Donor / Capability Mapping Evidence":
  - `W2 admission Phase C — donor / lifecycle freeze` → this file
  - `W2 admission Phase C — AdapterBase lifecycle review` → `docs/reviews/W2_ADMISSION_ADAPTERBASE_LIFECYCLE_REVIEW_v1.md`
- §"Current Known Evidence Gaps" line updated: Phase C closed; remaining blocker shrunk to Phases D + E plus the four base-only AdapterBase PRs identified by the lifecycle review.

---

## 3. What this Phase C now freezes

After this wave, the following are governance-frozen and may not be edited without a same-PR or follow-up PR citing architect signoff:

1. **W2 donor SHA pin** (`62b6da0`, 2026-04-26). All W2 admission artefacts and any future W2.x absorption PRs that reuse this admission pin must cite it. A W2.x sub-wave that opens at a moved donor HEAD MUST add its own pin row.
2. **Row lifecycle states and transitions.** `Not started → In progress (at PR-open) → Absorbed (at PR-merge) / Skipped (at decision-time)`. Status drift between doc and reality is a contract violation.
3. **Frozen row attributes.** Row id, donor path, Apollo target, strategy, capability/contract binding — frozen for the lifetime of the wave that owns the row.
4. **Closed AdapterBase capability set.** `understanding`, `subtitles`, `dub`, `video_gen`, `avatar`, `face_swap`, `post_production`, `pack`. Opening this set is a Master Plan amendment, not a W2.x decision.
5. **AdapterBase extension discipline.** Any change to `AdapterBase` / `AdapterInvocation` / `AdapterResult` / kind subclasses is a separate PR. No bundling with provider absorption.
6. **No truth writes from adapters.** `AdapterResult` (artefacts + advisories + rule_versions) is the only adapter return path.
7. **No I/O at import.** Module import remains side-effect-free; once construction hook lands (separate PR), construction must also remain side-effect-free; first I/O is `invoke`-only.
8. **Fallback never primary truth.** Provider fallback paths land under `advisories`, never under `artefacts` — runtime-enforced by `tests/guardrails/test_fallback_never_primary_truth.py`.

---

## 4. What was intentionally not done

Per the directive's Phase C scope rules, this wave intentionally did NOT:

- absorb any provider SDK / client (W2.1 is not yet started; A-row / P-row provider absorption is forbidden until §5 base-only PRs land);
- implement any AdapterBase lifecycle method (auth, retry, error envelope, construction hook) — these are the four separate base-only PRs called out by the lifecycle review §5;
- modify any vendor adapter under `gateway/app/services/workers/adapters/`;
- modify any provider client under `gateway/app/services/providers/`;
- touch `tests/guardrails/` (Phase A artefact);
- touch `ops/env/` (Phase B artefact, no clarification needed this wave);
- modify Hot Follow path (Phase D scope; not opened);
- expand env matrix scope (none of the Phase B docs required clarification fixes).

---

## 5. Acceptance check (against directive §9)

The directive §9 lists the W2.1 unlock conditions. This Phase C closes items 5 and 6:

| §9 item | Phase C contribution | Status after this wave |
|---|---|---|
| 1. `tests/guardrails/` built and passing | Phase A | ✅ green |
| 2. Provider leak tests in place | Phase A | ✅ green |
| 3. Fallback-never-primary-truth tests in place | Phase A | ✅ green |
| 4. O-01 ~ O-03 env matrix in place | Phase B | ✅ green |
| 5. fresh W2 donor SHA pin written into mapping doc | **Phase C (this wave)** | ✅ green |
| 6. AdapterBase lifecycle review passed | **Phase C (this wave)** | ✅ green (review existed standalone; 4 base-only gap-closing PRs identified) |
| 7. Hot Follow regression baseline freeze done | Phase D | ⏳ not started |
| 8. Reviewer signoff ready | Phase E | ⏳ not started |
| 9. Architect signoff ready | Phase E | ⏳ not started |

---

## 6. Remaining blockers before Phase D

1. Hot Follow regression baseline freeze — Phase D scope; not opened in this wave.
2. The four base-only AdapterBase PRs identified by `docs/reviews/W2_ADMISSION_ADAPTERBASE_LIFECYCLE_REVIEW_v1.md` §5. These are PREREQUISITES TO W2.1, not to Phase D. Phase D does not block on them; Phase E (W2.1 admission signoff) does.
3. W2.1 entry note (donor SHA pin restatement, env matrix restatement, guardrails restatement) — produced at the start of W2.1, not in W2 admission.

No Phase A or Phase B artefact was modified by this Phase C wave.

---

## 7. Files touched by this wave

- created: `docs/reviews/W2_ADMISSION_ADAPTERBASE_LIFECYCLE_REVIEW_v1.md`
- created: `docs/execution/evidence/w2_admission_phase_c_donor_lifecycle_freeze_v1.md` (this file)
- updated: `docs/donor/swiftcraft_capability_mapping_v1.md` (header pin line; §0 table; §3 lifecycle rules)
- updated: `docs/execution/apolloveo_2_0_evidence_index_v1.md` (new rows; gap line)

No code under `gateway/`, `tests/guardrails/`, `ops/env/`, `services/`, or any donor-derived directory was touched.

---

## 8. Hard stop

After this wave, work stops and waits for review / next instruction. Phase D is NOT auto-started. Provider code is NOT to be opened. The next allowed unit of work is either Phase D (Hot Follow regression baseline freeze) or one of the four base-only AdapterBase PRs identified by the lifecycle review §5 — both require fresh authorisation.
