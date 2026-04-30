# W2 Admission Preparation — Phase B: Env / Secret Matrix (v1)

- Date: 2026-04-26
- Wave: ApolloVeo 2.0 W2 Admission Preparation — Phase B only
- Authority:
  - `docs/architecture/ApolloVeo_2.0_W2_Admission_Preparation_Wave_指挥单_v1.md` §4 Phase B, §6, §9
  - `docs/donor/swiftcraft_donor_boundary_v1.md` §3.7
  - `docs/donor/swiftcraft_capability_mapping_v1.md` rows O-01, O-02, O-03
  - `docs/reviews/W1_COMPLETION_REVIEW_v1.md` §3.1.3
  - `docs/execution/evidence/w2_admission_phase_a_guardrail_foundation_v1.md` (Phase A closure)

## 1. Scope

This wave delivers ONLY the W2 admission env / secret baseline (directive
§4 Phase B). Specifically:

- O-01 — provider env matrix host (`ops/env/env_matrix_v1.md`)
- O-02 — storage layout (`ops/env/storage_layout_v1.md`)
- provider secret loading baseline (`ops/env/secret_loading_baseline_v1.md`)
- explicit no-hardcoded-token / no-hardcoded-key rule (write-back in both
  the matrix and the loading baseline)
- evidence write-back and Evidence Index v1 update
- mapping doc lifecycle update for O-01 and O-02 (`Not started → In
  progress`, per W1 review §3.1.6 "flip at PR-open, not PR-merge")

No provider code, no SDK absorption, no runtime wiring, no Hot Follow
behaviour change, no AdapterBase lifecycle changes, no donor SHA pin
update, no Hot Follow regression baseline freeze.

## 2. Files read

- `docs/architecture/ApolloVeo_2.0_W2_Admission_Preparation_Wave_指挥单_v1.md`
- `docs/reviews/W1_COMPLETION_REVIEW_v1.md`
- `docs/donor/swiftcraft_capability_mapping_v1.md` (rows O-01..O-03 only)
- `docs/execution/evidence/w2_admission_phase_a_guardrail_foundation_v1.md`
- `docs/execution/apolloveo_2_0_evidence_index_v1.md`
- `ops/env/README.md`
- `scripts/render_preflight.sh`
- `gateway/app/main.py` (storage feature gate, version reporting)
- `gateway/app/auth.py`, `gateway/app/db.py`, `gateway/app/config.py`,
  `gateway/app/deps.py`, `gateway/app/i18n.py`,
  `gateway/app/core/logging_config.py`
- `gateway/app/storage/r2.py`, `gateway/adapters/r2_s3_client.py`,
  `gateway/adapters/s3_client.py`, `gateway/app/services/publish_service.py`,
  `gateway/app/services/artifact_downloads.py`
- `gateway/app/providers/gemini_subtitles.py`,
  `gateway/app/providers/whisper_singleton.py`
- `gateway/app/services/steps_v1.py`, `gateway/app/steps/subtitles.py`,
  `gateway/app/steps/pipeline_v1.py`,
  `gateway/app/services/media/ffmpeg_localization.py`,
  `gateway/app/services/media/subtitle_builder.py`,
  `gateway/app/services/voice_service.py`,
  `gateway/app/services/compose_service.py`,
  `gateway/app/services/task_view_presenters.py`,
  `gateway/app/services/tools_registry.py`,
  `gateway/app/services/media_helpers.py`,
  `gateway/app/services/pack_service.py`,
  `gateway/app/services/gemini_brief.py`,
  `gateway/app/routers/tasks.py`, `gateway/app/routers/hot_follow_api.py`,
  `gateway/app/routes/v17_pack.py`, `gateway/routes/v1_actions.py`,
  `gateway/app/services/task_view_helpers.py`,
  `gateway/app/services/task_cleanup.py`

(All reads were for env-key inventory only. No code was modified.)

## 3. Files created

- `ops/env/env_matrix_v1.md`
- `ops/env/storage_layout_v1.md`
- `ops/env/secret_loading_baseline_v1.md`
- `docs/execution/evidence/w2_admission_phase_b_env_matrix_v1.md` (this file)

## 4. Files updated

- `docs/execution/apolloveo_2_0_evidence_index_v1.md` — added Phase B
  entries under Donor / Capability Mapping Evidence and updated the
  "capability adapter base missing" gap line to reflect Phase B closure.
- `docs/donor/swiftcraft_capability_mapping_v1.md` — flipped row O-01 and
  O-02 status from `Not started` to `In progress` per W1 review §3.1.6
  (lifecycle: `Not started → In progress` at PR-open).

## 5. What the env matrix now covers

`ops/env/env_matrix_v1.md` defines, per row, the eight required attributes
from the directive: provider/system, env var names, required vs optional,
local source, render source, production source, fallback/degraded
behaviour, owner, plus rotation/revocation notes where relevant. Sections:

- §1 — environment dimensions (local / render / production) with the rule
  that key **names** are constant across dimensions; only **values** vary.
- §2.1 — core platform keys (auth, db, locale, logging, build metadata).
- §2.2 — storage keys (R2 canonical names + frozen alias chain, feature
  gate, signed URL, disk roots).
- §2.3 — ASR / Whisper provider keys (W2.1 admission target).
- §2.4 — subtitles / Gemini provider keys, including `GOOGLE_API_KEY`
  alias freeze.
- §2.5 — dub / voice routing keys; W2.2 provider secrets explicitly
  deferred.
- §2.6 — avatar / videogen routing key; W2.3 provider secrets explicitly
  deferred.
- §2.7 — ffmpeg / media non-secret tuning (W1 absorbed).
- §2.8 — pipeline runtime non-secret flags.
- §3 — pointer to `storage_layout_v1.md` (O-02 detail).
- §4 — `scripts/render_preflight.sh` env contract (O-03; move deferred).
- §5 — explicit no-hardcoded-token / no-hardcoded-key rule.
- §6 — change discipline (append-only within a wave; rename / remove rules).
- §7 — out of scope for this wave.

`ops/env/storage_layout_v1.md` covers the R2 / local-fs split, path
conventions, object-key prefix conventions for future provider caches,
region/endpoint assumptions, and the only sanctioned degraded path.

`ops/env/secret_loading_baseline_v1.md` defines the canonical loading
pattern (canonical names only, no literal defaults for secrets, fail
closed, no per-call re-reads, test isolation, no secret echoing) and the
W2 PR checklist that reviewers will use.

## 6. What was intentionally not done

Per directive §0 / §7 and the user's hard stop instructions:

- No provider client / SDK code added or modified.
- No new `os.getenv` call sites introduced anywhere.
- No changes to existing platform `os.getenv` call sites (auth, db,
  storage, media). The matrix documents them; it does not refactor them.
- No `render.yaml` or other deploy descriptor authored.
- No Hot Follow main-line behaviour change.
- No AdapterBase lifecycle changes (Phase C territory).
- No donor SHA pin update (Phase C territory).
- No Hot Follow regression baseline freeze (Phase D territory).
- No new `tests/guardrails/` tests authored — the literal-default scan
  for provider keys is reserved for the first W2.1 provider PR.
- No move of `scripts/render_preflight.sh` to `ops/runbooks/` (O-03's
  Wrap target). The contract is captured; the move is deferred until a
  deploy-pipeline change authorizes it.
- No relocation of W1 absorption tests.
- No frontend / workbench scope expansion.

## 7. Validation

This wave is docs/evidence-only. Per directive §6 "如果 code scaffolding
not required, keep this wave docs/evidence only." No tests authored, no
code changed.

Sanity check that nothing in this wave broke the existing guardrail host
from Phase A:

```
python3 -m pytest tests/guardrails/ -q
=> 7 passed (expected, unchanged from Phase A baseline)
```

(Run is optional verification only; no Phase B file is under
`tests/guardrails/` scrutiny.)

## 8. Acceptance vs. directive §4 Phase B

| Acceptance criterion | Status |
|---|---|
| O-01..O-03 env matrix exists | DONE (`ops/env/env_matrix_v1.md`) |
| local / render / production split explicit | DONE (matrix §1, all rows) |
| provider secret loading baseline | DONE (`ops/env/secret_loading_baseline_v1.md`) |
| explicit no-hardcoded-token rule write-back | DONE (matrix §5 + baseline §4) |
| evidence / execution log update | DONE (this file + index entry) |
| no provider code touched | DONE |
| no Hot Follow business logic touched | DONE |
| no AdapterBase lifecycle change | DONE |
| mapping row lifecycle obeyed (PR-open flip) | DONE (O-01, O-02 → In progress) |

## 9. Remaining blockers before Phase C / W2.1 unlock

Per directive §4 Phases C–E and §9, still required:

- Phase C — fresh W2 donor SHA pin in
  `docs/donor/swiftcraft_capability_mapping_v1.md`; mapping row
  lifecycle freeze; `AdapterBase` lifecycle review (separate PR per W1
  review §3.1.2).
- Phase D — Hot Follow regression baseline freeze with green run
  evidence (W1 review §3.1.5).
- Phase E — W2.1 admission review and signoff (architect + reviewer).
- O-03 deploy-pipeline decision (move `scripts/render_preflight.sh` to
  `ops/runbooks/` or formally Skip the move).

## 10. Hard stop confirmation

This wave stops at Phase B. No donor SHA pin work, no AdapterBase
lifecycle implementation, no provider code. Awaiting review and next
instruction.
