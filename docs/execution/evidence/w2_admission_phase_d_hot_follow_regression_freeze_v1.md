# W2 Admission Preparation — Phase D: Hot Follow Regression Freeze (v1)

- Date: 2026-04-26
- Wave: ApolloVeo 2.0 W2 Admission Preparation — Phase D only
- Authority:
  - `docs/architecture/ApolloVeo_2.0_W2_Admission_Preparation_Wave_指挥单_v1.md` §4 Phase D, §9, §10
  - `docs/reviews/W1_COMPLETION_REVIEW_v1.md` §3.1.5, §3.2 R5
  - `docs/reviews/HOT_FOLLOW_CURRENT_BRANCH_FINAL_ACCEPTANCE_FREEZE.md`
  - `docs/execution/HOT_FOLLOW_BASELINE_FREEZE_AND_VEOBASE01_ALIGNMENT.md`
  - `docs/contracts/hot_follow_line_contract.md`
- Phase A evidence (already green): `docs/execution/evidence/w2_admission_phase_a_guardrail_foundation_v1.md`
- Phase B evidence (already green): `docs/execution/evidence/w2_admission_phase_b_env_matrix_v1.md`
- Phase C evidence (already green): `docs/execution/evidence/w2_admission_phase_c_donor_lifecycle_freeze_v1.md`

---

## 1. Scope

This wave delivers ONLY the Hot Follow regression baseline freeze required by
the W2 Admission directive §4 Phase D and W1 review §3.1.5. It captures the
current-mainline pass/fail state of the Hot Follow regression suite as the
authoritative reference snapshot so that any drift caused by later W2 waves
(in particular W2.2 Subtitles/Dub provider absorption and W2.3 Avatar/VideoGen)
is attributable.

This wave does NOT:

- modify any Hot Follow business code (subtitle authority, currentness,
  state policy, ready gate, projection, presenters, runtime bridges,
  router, helpers, advisory entry — all forbidden by directive §3.4 / §7);
- absorb any provider SDK or client;
- implement any AdapterBase lifecycle method;
- change any frozen contract under `docs/contracts/`;
- attempt to "fix" pre-existing red tests — fixing a Hot Follow business
  defect inside Phase D would itself be a Hot Follow business-logic
  modification and is therefore forbidden under directive §7 / Phase D
  scope rules. Pre-existing reds are recorded as part of the baseline
  (the freeze pins reality, not a wished-for state).
- expand env matrix or donor pin scope.

---

## 2. What this baseline protects

Phase D freezes the following surfaces. Any later W2.x wave that touches a
file in this set must (a) prove it does not regress the green tests in §4.1
and (b) not expand the known-red set in §4.2.

### 2.1 Frozen contract surfaces (read-only for W2.x)
- `docs/contracts/hot_follow_line_contract.md`
- `docs/contracts/hot_follow_ready_gate.yaml`
- `docs/contracts/hot_follow_projection_rules_v1.md`
- `docs/contracts/hot_follow_state_machine_contract_v1.md`
- `docs/contracts/four_layer_state_contract.md`
- `docs/contracts/status_ownership_matrix.md`
- `docs/contracts/workbench_hub_response.contract.md`
- `docs/architecture/hot_follow_business_flow_v1.md`
- `docs/architecture/line_contracts/hot_follow_line.yaml`
- `schemas/packets/hot_follow/sample/reference_packet_v1.json`

### 2.2 Frozen runtime modules (no W2.x edits without architect signoff)
- `gateway/app/services/hot_follow_subtitle_authority.py`
- `gateway/app/services/hot_follow_subtitle_currentness.py`
- `gateway/app/services/status_policy/hot_follow_state.py`
- `gateway/app/services/contract_runtime/current_attempt_runtime.py`
- `gateway/app/services/contract_runtime/ready_gate_runtime.py`
- `gateway/app/services/task_view_projection.py`
- `gateway/app/services/task_view_presenters.py`
- `gateway/app/routers/hot_follow_api.py`
- any module reachable from the above as a non-test transitive truth source

### 2.3 Frozen behavioural invariants (paraphrased from
`HOT_FOLLOW_CURRENT_BRANCH_FINAL_ACCEPTANCE_FREEZE.md` §3–§6, restated here so
later waves do not need to chase the original document):

- **L1/L2/L3/L4 separation.** Workbench / publish / projection layers must
  never recompute truth that is owned by L2 facts or L3 gates.
- **Single-owner subtitle authority.** Authoritative subtitle truth is owned
  by `hot_follow_subtitle_authority.py`. Helpers, providers, and any future
  W2 adapter remain side-channel only once authoritative current truth
  exists.
- **Empty-body / non-authoritative subtitle saves remain blocked.**
- **URL voice-led standard dubbing stays rule-stable on
  `tts_replace_route`** for translation-incomplete and currentness-driven
  failure shapes.
- **Local preserve-source remains explicitly separated** by
  `preserve_source_route_no_target_subtitle_required`. W2 adapters must not
  collapse the preserve-source route into standard dubbing.
- **Historical skip / failure history does not override current truth.**
- **Helper coexistence.** Helper failure / recovery does not pollute
  recovered current truth, including manual save recovery (`my.srt` ↔
  `mm.srt` alias accepted for currentness).
- **Fallback never primary truth.** Reaffirmed from Phase A guardrail
  (`tests/guardrails/test_fallback_never_primary_truth.py`); any W2
  provider fallback path lands as advisory, never as artefact.

### 2.4 Frozen regression suite host
The 20 test files listed in §4 form the canonical Hot Follow regression
suite for W2 admission purposes. Adding tests is allowed; renaming,
deleting, or skipping any of the 192 currently-collected cases is a
regression unless paired with a Hot Follow review document that explicitly
retires the case.

---

## 3. What later waves may not break

### 3.1 W2.1 Understanding Provider Absorption
W2.1 binds to `UnderstandingAdapter` only. It must not:
- import or call any module in §2.2;
- modify any contract in §2.1;
- alter any test file in §4 (other than additive cases that pass);
- introduce a second subtitle / dub / preserve-source authority path.

### 3.2 W2.2 Subtitles / Dub Provider Absorption
W2.2 is the highest-risk wave because it overlaps Hot Follow's frozen
subtitle/dub paths (W1 review §3.2 R5). Before W2.2 opens, this Phase D
baseline must be re-run; W2.2 cannot land if any §4.1 green test has flipped
red, or if the §4.2 known-red set has grown by a single case attributable to
W2.2 work. Specifically W2.2 must not:
- change `selected_compose_route` semantics;
- change `tts_replace_route` vs `preserve_source_route_no_target_subtitle_required` selection;
- change `compose_allowed` / `compose_execute_allowed` / `compose_blocked`;
- change `publish_ready` derivation;
- change subtitle authority single-owner rule;
- change `my.srt` ↔ `mm.srt` alias acceptance;
- inject provider-side-channel fallbacks into the artefact path
  (must remain advisory — guarded by Phase A
  `tests/guardrails/test_fallback_never_primary_truth.py`).

### 3.3 W2.3 Avatar / VideoGen / Storage Provider Absorption
W2.3 is planning-only per directive §10. If unfrozen later it must not
touch §2.1 / §2.2 / §2.3 surfaces; in particular it must not insert a
second truth path for the final-video artefact.

### 3.4 Common rule across all W2 waves
Any change to a §2.2 module triggers a mandatory re-run of the §4 suite
and a same-PR diff against §4.1 / §4.2. Drift (green → red, or new red)
is a contract violation regardless of whether the failing test was
"already flaky".

---

## 4. Captured regression baseline (frozen state)

Reproduction command (the canonical Phase D regression run):

```
python3.11 -m pytest \
  gateway/app/services/tests/test_hot_follow_artifact_facts.py \
  gateway/app/services/tests/test_hot_follow_skills_advisory.py \
  gateway/app/services/tests/test_hot_follow_subtitle_currentness.py \
  gateway/app/services/tests/test_hot_follow_subtitle_binding.py \
  gateway/app/services/tests/test_hot_follow_helper_translation.py \
  gateway/app/services/tests/test_hot_follow_runtime_bridge.py \
  gateway/app/services/tests/test_hot_follow_state_commit_contract.py \
  gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py \
  gateway/app/services/status_policy/tests/test_hot_follow_publish_hub_final_url.py \
  gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py \
  gateway/app/services/status_policy/tests/test_hot_follow_dub_alignment.py \
  gateway/app/services/status_policy/tests/test_hot_follow_line_policy_layer.py \
  gateway/app/services/status_policy/tests/test_hot_follow_new_page_routes.py \
  gateway/app/services/status_policy/tests/test_hot_follow_phase_a_ops.py \
  gateway/app/services/status_policy/tests/test_hot_follow_plain_text_srt.py \
  gateway/app/services/status_policy/tests/test_hot_follow_provider_mismatch_gate.py \
  gateway/app/services/status_policy/tests/test_hot_follow_repo_refresh.py \
  gateway/app/services/status_policy/tests/test_hot_follow_state_line_binding.py \
  gateway/app/services/status_policy/tests/test_hot_follow_subtitle_only_compose.py \
  gateway/app/services/status_policy/tests/test_hot_follow_workbench_subtitle_template_semantics.py
```

Result captured at commit `c128b2b` (mainline tip at Phase D open):

- collected: 192 cases across 20 files
- passed: **183**
- failed: **9** (pre-existing on mainline; all predate Phase D and predate
  W2 admission Phase A/B/C; not introduced by any of the W2 admission
  waves)
- guardrail companion suite (`tests/guardrails/`): **7 / 7 passed**
- packet validator companion baseline
  (`tests/contracts/packet_validator/test_hot_follow_reference_baseline.py`):
  **2 / 2 passed**

### 4.1 Frozen GREEN set (must remain green for any future W2.x wave)

The 183 currently-green cases are pinned as the green baseline. The
canonical command in §4 is the authoritative way to enumerate them; the
baseline asserts that re-running the command on a clean later commit must
yield ≥ 183 passes with the same case ids passing as today, except for
additive cases.

### 4.2 Frozen KNOWN-RED set (may not grow)

The following 9 cases are pinned as the known-red baseline as of
`c128b2b`. Phase D does not unblock them; later waves may not grow this
set, and W2.2 must not attribute any new red to itself.

| # | File | Case |
|---|---|---|
| 1 | `gateway/app/services/tests/test_hot_follow_skills_advisory.py` | `test_hot_follow_advisory_noop_preserves_workbench_payload` |
| 2 | `gateway/app/services/tests/test_hot_follow_subtitle_binding.py` | `test_subtitle_render_signature_tracks_minimal_retune_defaults` |
| 3 | `gateway/app/services/tests/test_hot_follow_subtitle_binding.py` | `test_compose_subtitle_vf_uses_bottom_safe_zone_defaults_for_hot_follow` |
| 4 | `gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py` | `test_hot_follow_workbench_resolves_subtitles_terminal_success_when_authoritative_truth_is_current` |
| 5 | `gateway/app/services/status_policy/tests/test_hot_follow_workbench_hub_ready_gate.py` | `test_hot_follow_workbench_recovers_current_audio_preview_and_clears_stale_failed_residue` |
| 6 | `gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py` | `test_hot_follow_api_deliverables_use_dry_key_not_source_audio_key` |
| 7 | `gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py` | `test_patch_hot_follow_subtitles_syncs_saved_text_to_canonical_mm_srt` |
| 8 | `gateway/app/services/status_policy/tests/test_hot_follow_current_dub_state.py` | `test_patch_hot_follow_subtitles_rejects_semantically_empty_srt_without_replacing_truth` |
| 9 | `gateway/app/services/status_policy/tests/test_hot_follow_provider_mismatch_gate.py` | `test_hot_follow_provider_mismatch_blocks_compose_ready_even_if_final_exists` |

These reds were observed before Phase D opened; they are out of scope for
Phase D under directive §7 (no Hot Follow business-logic modification).
Resolving them requires a separate Hot Follow regression PR cited as a
W2.1/W2.2 prerequisite, **not** a Phase D edit. They are recorded here so
they cannot be used as an excuse to weaken the baseline.

### 4.3 Companion green evidence

- `tests/guardrails/` — 7 / 7 passed (Phase A foundation, unchanged).
- `tests/contracts/packet_validator/test_hot_follow_reference_baseline.py` —
  2 / 2 passed; this is the packet validator anchor for Hot Follow
  (`docs/execution/evidence/hot_follow_reference_packet_validation_v1.md`)
  and remains green at the Phase D open.

Both companion suites are required to remain green for any future W2
wave that runs the §4 command.

---

## 5. Baseline-validation procedure (how later waves use this)

Any future W2.x PR that touches §2.1 contracts, §2.2 modules, §2.3
invariants, or §2.4 test files MUST:

1. Run the §4 command on the PR HEAD.
2. Compare against this baseline:
   - assert `passed >= 183`;
   - assert that each case id in §4.1 still passes (re-flipping a §4.1
     case to red is a regression);
   - assert that no new case appears in the failed set beyond the §4.2
     list (growing §4.2 is a regression);
   - assert `tests/guardrails/` is 7 / 7 passed;
   - assert
     `tests/contracts/packet_validator/test_hot_follow_reference_baseline.py`
     is 2 / 2 passed.
3. Cite this evidence file by path in the PR description.
4. If the wave intentionally introduces new green cases, count is
   allowed to grow above 183; that is additive, not a regression.

If a wave needs to retire a §4.1 case, that requires a Hot Follow line
review document (separate from the W2.x PR) signed by the architect,
explicitly citing the case and explaining why the invariant it covers is
no longer required.

---

## 6. Acceptance check (against directive §9)

| §9 item | Phase contribution | Status |
|---|---|---|
| 1. `tests/guardrails/` built and passing | Phase A | ✅ green (re-verified 7/7 in this wave) |
| 2. Provider leak tests in place | Phase A | ✅ green |
| 3. Fallback-never-primary-truth tests in place | Phase A | ✅ green |
| 4. O-01 ~ O-03 env matrix in place | Phase B | ✅ green |
| 5. fresh W2 donor SHA pin | Phase C | ✅ green |
| 6. AdapterBase lifecycle review passed | Phase C | ✅ green |
| 7. Hot Follow regression baseline freeze done | **Phase D (this wave)** | ✅ baseline frozen (183 green / 9 known-red pinned; companion suites green; protected-path set frozen) |
| 8. Reviewer signoff ready | Phase E | ⏳ not started |
| 9. Architect signoff ready | Phase E | ⏳ not started |

Phase D's directive deliverables (per the §4 commander brief):

| Deliverable | Where it lives |
|---|---|
| 1. one explicit Hot Follow regression baseline review/evidence doc | this file |
| 2. clear definition of what paths are protected | §2 above |
| 3. green-run validation evidence | §4.1, §4.3 above (reproduction command pinned) |
| 4. evidence index / execution log write-back | `docs/execution/apolloveo_2_0_evidence_index_v1.md` updated by this wave |
| 5. explicit statement of what later waves may not break | §3 above |

---

## 7. What was intentionally not done

Per Phase D scope rules, this wave did NOT:

- modify any Hot Follow runtime module listed in §2.2;
- modify any Hot Follow contract listed in §2.1;
- modify any test file in §4 (no test additions, deletions, renames, or
  marker changes);
- attempt to fix the 9 known-red cases (would require Hot Follow
  business-logic edits, which are forbidden);
- absorb any provider SDK / client (W2.1 not started);
- implement any AdapterBase lifecycle method (Phase C explicitly deferred
  these to four base-only PRs);
- modify env / secret matrix (Phase B closed; no clarification needed);
- modify donor SHA pin or mapping rows (Phase C closed);
- touch `tests/guardrails/` rules (Phase A closed; only re-ran them);
- start Phase E (W2.1 admission signoff) — directive hard-stop.

---

## 8. Remaining blockers before Phase E

1. **Phase E (W2.1 admission signoff)** — reviewer signoff + architect
   signoff for the entire W2 admission preparation (Phases A+B+C+D) as a
   single gate. Phase E is the next allowed unit of work after this wave;
   it is NOT auto-started by Phase D per directive §3.5 and §7.
2. **Four base-only AdapterBase PRs** identified by Phase C lifecycle
   review §5 (auth/credential, retry/timeout/cancellation, error envelope,
   construction-vs-invocation). These are PREREQUISITES TO W2.1 (the first
   provider absorption PR), not to Phase E (admission signoff). They can
   land in parallel with Phase E review.
3. **9 Hot Follow known-red cases (§4.2)** — these are PREREQUISITES TO
   W2.2 (the subtitle/dub provider wave), not to Phase E or W2.1. They
   must be resolved by a separate Hot Follow regression PR cited as a
   W2.2 prerequisite. Phase D does not block on them being fixed; it only
   pins them so they cannot be silently grown.
4. **W2.1 entry note** — produced at the start of W2.1, not in W2
   admission. Must restate the donor SHA pin, env matrix, guardrails
   reference, and this Phase D baseline.

No Phase A, Phase B, or Phase C artefact was modified by this wave.

---

## 9. Files touched by this wave

- created: `docs/execution/evidence/w2_admission_phase_d_hot_follow_regression_freeze_v1.md` (this file)
- updated: `docs/execution/apolloveo_2_0_evidence_index_v1.md` (new row + gap-line update)

No code under `gateway/`, `tests/`, `ops/env/`, `services/`, or any donor-derived directory was touched.

---

## 10. Hard stop

After this wave, work stops and waits for review / next instruction. Phase
E is NOT auto-started. Provider code is NOT to be opened. The next allowed
unit of work is Phase E (W2.1 admission signoff). Hot Follow business code
remains frozen.
