# Engineering Status

## Current Stage

Factory Alignment Review Gate Active

## Current Main Line

- Hot Follow
- first business-validated Skills sample
- target subtitle currentness and source-audio policy truth-source fixes are now closed for the active Hot Follow path
- Hot Follow is the first business-validated line, but not yet the first fully standardized reusable engineering line

## Active Gate

- The factory alignment code review gate is committed on `main`.
- `docs/baseline/PROJECT_BASELINE_INDEX.md` treats it as:
  - post-2026-03-18 code validation baseline
  - prerequisite gate for new-line onboarding
  - required citation source for relevant PRs
- Root rules are synchronized through `ENGINEERING_RULES.md` and `PROJECT_RULES.md`.

## Current Completion

- Matrix Script Plan A trial correction §8.A landed: server-side ref-shape guard on `source_script_ref` rejects pasted script body and any non-reference payload before the formal Matrix Script payload is built; operator-facing input mirrors the closed accepted shape via `pattern` / `maxlength`; `task_entry_contract_v1` carries an addendum pinning the closed scheme set; trial sample created before §8.A is still invalid evidence per the blocker review §9
- Matrix Script Plan A trial correction §8.B confirmed (no narrow fix required): a fresh contract-clean Matrix Script sample created via the formal POST reaches the Phase B variation workbench surface — `resolve_line_specific_panel(packet)` returns `panel_kind="matrix_script"`, `wiring.py` attaches the `matrix_script_workbench_variation_surface_v1` projection, and `task_workbench.html` mounts the Matrix Script Variation Panel section with the contract projection name, both seeded ref_ids, and no empty-slot fallback; per-line dispatch is via `panel_kind` mounting inside the shared shell, not via per-line templates
- Matrix Script Plan A trial correction §8.C landed (Option C1 — minimal real Phase B authoring): `gateway/app/services/matrix_script/phase_b_authoring.py::derive_phase_b_deltas(entry, task_id)` synchronously emits populated `variation_matrix.delta` (3 canonical axes — `tone`/`audience`/`length` — and `variation_target_count` cells) and `slot_pack.delta` (1 slot per cell) inside `build_matrix_script_task_payload`, attached on both the packet mirror and the top-level mirror; `cells[i].script_slot_ref ↔ slots[i].slot_id` round-trip is provable for every k ∈ [1, 12]; `body_ref` is opaque (`content://matrix-script/{task_id}/slot/{slot_id}`); `task_entry_contract_v1.md` carries an additive §"Phase B deterministic authoring (addendum, 2026-05-03)" pinning the canonical axes, pairing rule, body_ref template, determinism statement, and Plan E removal path; the Phase B variation panel mounted by §8.B now renders real resolvable axes / cells / slots instead of empty fallbacks; trial samples created before §8.C are still invalid evidence per blocker review §9
- Matrix Script Plan A trial correction §8.D landed (operator brief correction, documentation-only): `docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md` adds §0.1 binding sample-validity rule (formal `/tasks/matrix-script/new` POST + opaque `source_script_ref` per §8.A guard + populated Phase B deltas per §8.C + mounted Matrix Script Phase B variation panel per §8.B); §3.1 / §3.2 / §3.3 / §5.2 / §6.2 / §7.1 / §7.2 / §8 / §11.1 / §12 rows refreshed to cite §8.A / §8.B / §8.C explicitly; old pre-§8.A invalid sample remains invalid evidence; Delivery Center stays inspect-only; Phase D.1 closure surface unchanged; `docs/execution/PLAN_A_OPS_TRIAL_WRITEUP_v1.md` carries an additive §11 "Matrix Script Plan A Trial Corrections — Addendum (2026-05-03)" overlay; no code, no contract, no schema, no template, no test changes — strictly documentation-only
- Hot Follow Skills MVP v0 closure remains frozen
- Hot Follow cleanup line is now near closure, not fully closed
- Myanmar target subtitles now use the same source-copy / translation-incomplete currentness discipline as Vietnamese
- `preserve original BGM/source audio` is bound into compose without being treated as current TTS dub
- workbench diagnostics and preview binding now distinguish preserved source audio from current TTS voiceover
- Hot Follow dub preview/download/file surfaces now bind to current true TTS voiceover instead of raw audio artifact presence
- Hot Follow dry TTS voiceover now has a dedicated authoritative key for dubbing preview/download/currentness, separated from final BGM/source-audio compose inputs
- Hot Follow dubbing truth now requires the strict dry TTS object shape under `config.tts_voiceover_key`; legacy `mm_audio_key` alone no longer satisfies dub semantics
- Hot Follow empty target subtitle / empty dub input now resolves to explicit `no_dub` skipped semantics instead of a failed TTS attempt
- Hot Follow final compose allowance now permits explicit empty-target/empty-input `no_dub` paths when final compose inputs are valid, without marking dub truth ready
- Hot Follow saved authoritative target subtitles now invalidate stale empty-subtitle `no_dub` skip state so dubbing can be rerun
- Hot Follow parse/source helper text is now separated from authoritative target subtitle and dub-input truth
- compose input selection now preserves source audio by using raw video as the carrier when `source_audio_policy=preserve`
- source-audio policy now persists across pipeline config storage, task config, workbench BGM upload, and backend BGM upload defaults
- workbench preview/player binding now uses explicit TTS preview fields instead of legacy voiceover aliases
- Hot Follow board/summary readiness now follows computed ready gate truth instead of raw final/audio/publish compatibility artifacts
- current business flow remains stable and non-blocking
- preserved source-audio bed in final compose no longer inherits a zero BGM mix value as effective mute

## Remaining Structural Risks

- `tasks.py` still structurally large
- `tasks.py` still exceeds structural safety for new-line onboarding
- `hot_follow_api.py` still carries oversized router orchestration weight
- `task_view.py` still mixes four-layer state projection concerns
- compatibility residue still exists
- some scenario-aware façade logic still remains
- some line/runtime profiles remain metadata-only instead of runtime-binding truth
- new-line onboarding remains blocked until gate prerequisites are cleared
- historical `mm_*` compatibility naming still exists and is intentionally out of scope for this fix
- source-audio preserve still needs real-material business sampling for mix quality and operator-facing mix review
- legacy Hot Follow tasks without the dedicated dry TTS key must be re-dubbed before exposing dub preview/download/currentness
- Hot Follow source-audio asset-flow fix sequence is complete through status truth binding; compatibility naming cleanup remains separate
- remaining Avatar / baseline router-space behavior is separately tracked, not part of Hot Follow closure

## Recommended Next Direction

- keep further Hot Follow fixes narrow and truth-source driven
- treat `docs/reviews/2026-03-18-plus_factory_alignment_code_review.md` as the active architecture gate for relevant PRs
- defer `mm_*` naming cleanup, translation bridge work, and localization-line expansion to separate scoped PRs
- keep source-audio / dub truth fixes separate from UI redesign or compose ownership redesign
- keep business regression and verification baseline mandatory
- avoid Avatar refactor, baseline rewrite, second-line expansion, or broad platformization by drift
