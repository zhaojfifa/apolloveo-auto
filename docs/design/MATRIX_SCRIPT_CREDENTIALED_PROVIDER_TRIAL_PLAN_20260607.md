# Matrix Script — Credentialed Provider Trial Plan (2026-06-07)

Status: **TRIAL PLAN — docs-only. PREPARED, NOT RUN. No provider call is made until the
Owner explicitly approves a credentialed trial AND credentials are available.** Not
implementation authority, not a Gate Spec, not a provider integration.

Purpose: design the **credentialed, offline** trials that settle the gaps the
secret-free ffmpeg trial could not measure — generative `image_to_video`, a working
`subtitle_style` path, and `voiceover` — so a future runtime gate spec for those
capabilities rests on real data. The proven ffmpeg backbone is handled separately by
`docs/design/MATRIX_SCRIPT_FFMPEG_BACKBONE_RUNTIME_GATE_SPEC_20260607.md`.

Source: `docs/execution/MATRIX_SCRIPT_CAPABILITY_OFFLINE_TRIAL_REPORT_20260607.md`,
`docs/design/MATRIX_SCRIPT_CAPABILITY_TRIAL_PLAN_20260607.md`,
`docs/reviews/MATRIX_SCRIPT_VIDEO_CAPABILITY_UPGRADE_REVIEW_20260607.md`.

When this plan conflicts with Bucket A, `ENGINEERING_RULES.md`,
`CURRENT_ENGINEERING_FOCUS.md`, or the Skill Adoption Policy, the underlying authority
wins.

> **RUN GATE (binding):** no command in this plan executes until **both** (1) the Owner
> explicitly approves the credentialed trial, and (2) credentials are available in the
> trial environment. Absent either, this remains a plan only.

---

## 0. Focus

Three capability gaps, all offline (Tyler-local / sandbox), all on the tomato-beach
benchmark stills:

1. **generative `image_to_video`** — Kling / Runway / Veo on BM-1 / BM-3 (product
   close-up, hook).
2. **working `subtitle_style` path** — a freetype/libass-enabled ffmpeg build **or** a
   pre-rendered-PNG → `overlay` adapter (incl. a CJK font), on BM-4.
3. **`voiceover`** — Azure Speech (TTS) on the BM-4 CTA line.

(`broll_retrieval`, `avatar_segment`, `bgm_select`, `face_swap` are **not** in this
trial: broll/bgm pend a library + license screen, avatar/face_swap remain future/gated.)

## 1. Required credentials

Per candidate, the **minimum** credential, supplied by Tyler in the trial environment
only (never committed, never logged):

| Capability | Candidate | Required credential |
|------------|-----------|---------------------|
| image_to_video | Kling | Kling API key/secret (account access) |
| image_to_video | Runway (or equiv) | Runway API key |
| image_to_video | Veo | Google/Vertex credential with Veo access + quota |
| voiceover | Azure Speech | Azure Speech key + region |
| subtitle_style | freetype/libass ffmpeg build | none (local rebuild/install) **or** a font license check for any bundled CJK font |

If a candidate's credential is unavailable, that candidate is **SKIPPED** for the run and
recorded as such — never substituted, never faked.

## 2. Secret handling

- **No secrets in the repo. Ever.** No key, token, region, endpoint, or `.env` is
  committed, referenced by path in committed files, or pasted into any doc/PR.
- Credentials live **only** in the trial environment's process env (e.g. shell env vars
  Tyler exports for the run), or an OS keychain — **outside** the repo tree.
- **No secret is logged.** Trial logs/metrics redact keys; request/response captures
  strip auth headers and any credential echo. Cost/quality logs contain numbers and
  verdicts only.
- Provider keys are **never** sent anywhere except the provider's official endpoint over
  TLS; no third-party relay.
- After the trial, env vars are unset / keychain entry removed (rollback = nothing
  persisted).
- Aligns with the Skill Adoption Policy §4 (no skill/tool may read or require a secret as
  a condition of a trial) — provider trials here are **Owner-gated and Tyler-run**, not
  skill-driven.

## 3. No secrets in repo (restatement — binding)

The repository carries **only** this plan and, after a run, a results report with
**redacted** metrics. No credential material, no raw request with auth, no provider
account identifier enters any committed file. A pre-commit scan (grep for key-shaped
strings / `Authorization` / provider key prefixes) MUST pass before any results report is
committed.

## 4. Trial inputs

- **image_to_video:** the real stills `02_tomato_bowl.png` (BM-1) and `04_eat_tomato.png`
  (BM-3) + a short motion prompt; target 3s, 1080×1920.
- **subtitle_style:** a BM-3 clip + a subtitle line (English + a CJK line to test the
  font path) + a styled CTA card spec.
- **voiceover:** the BM-4 CTA text (English + the target market language) for TTS.
- All inputs are existing local assets / hand-authored text; no operator PII, no secret.

## 5. Expected outputs

- **image_to_video:** a short mp4 per provider per shot (h264, 1080×1920), plus a
  metrics record (latency, cost, quality verdict, failure mode).
- **subtitle_style:** a clip with burned/styled subtitle (English + CJK) proving the
  font/render path; or a documented failure if the build/adapter is insufficient.
- **voiceover:** an audio track (and a composed BM-4 with synced audio + subtitle), plus
  metrics.
- Outputs land in a scratch trial dir (e.g. `/tmp/ms_cred_trials/`), **not committed**;
  only the redacted results report is committed.

## 6. Cost logging

- Record **actual** cost per call (provider billing units → currency where derivable):
  per-clip for image_to_video, per-character/second for TTS, per-minute for any compute.
- Log the cumulative trial spend and the per-shot unit cost, so a Phase D decision can
  compare cost-per-acceptable-clip across providers.
- Cost numbers only (no account/billing identifiers) reach the committed report.

## 7. Quality scoring

Score each output against the review §9 quality gate, 1–5 per dimension + a pass/fail:

- visual relevance · product visibility · motion quality (generative) · subtitle
  readability (incl. CJK) · audio sync · duration fit.
- Each scored against the same BM success criteria as the offline trial plan, so results
  are comparable across providers and against the ffmpeg proxy baseline.

## 8. Failure logging

- Record failure mode per call: auth error, quota/rate limit, timeout, content-policy
  refusal, malformed output, quality-gate fail.
- Failures are **kept** (not hidden) and feed the decision criteria (§11); a provider
  that fails auth/quota is SKIPPED with reason, not substituted.
- No secret appears in a failure log (redaction per §2).

## 9. ToS / license checks

Before any call to a provider, confirm and record:

- the provider's **Terms of Service** permit this evaluation use;
- **generated-content rights** (who owns the output; usage constraints);
- for `subtitle_style` fonts: the **font license** (esp. any bundled CJK font) permits
  burn-in/redistribution;
- for any GitHub donor tool used as an adapter: a **license + security screen** (no
  unvetted code execution, no secret egress) per the capability review §5.
- A candidate that fails a ToS/license/rights check is **blocked** and not trialled.

## 10. Adapter difficulty

For each candidate that produces acceptable output, record the effort to wrap it behind
the internal capability-kind contract (review §4/§5), without UI/state change:

- API shape vs the internal `image_to_video` / `voiceover` / `subtitle_style` contract;
- async/polling vs sync; artifact retrieval; error mapping;
- secret-injection point (env only, never repo);
- estimated adapter size + test surface.

## 11. Decision criteria for entering a runtime Gate Spec

A credentialed candidate advances toward a **future runtime gate spec** only if **all**
hold on the benchmarks:

1. passes the §9 quality gate on its target shot(s) at a clearly better level than the
   ffmpeg proxy baseline (for generative image_to_video) or fills a blocked gap
   (subtitle_style / voiceover);
2. latency meets a documented fast-preview-or-final target;
3. cost-per-acceptable-output is recorded and acceptable;
4. ToS / content-rights / license are clear and acceptable (no blocked flags);
5. adapter fits the internal capability-kind contract with **no UI/state change** and a
   **secret-injection point that keeps keys out of the repo**.

A candidate failing any of (1)–(5) is reclassified donor-reference / future / unsuitable
with the reason logged. Entering runtime still requires authoring a **separate**
gate spec and its §-signoff — this plan does not pre-authorize integration.

## 12. Boundary

- **docs-only; prepared, not run.** No provider call, no generation, until Owner
  approval + credentials (§0 run gate).
- no runtime integration · no `gateway/**` / services / templates / tests change · no
  provider adapter code · no schemas/contracts change (unless separately approved) · no
  secrets in repo · no vendor exposure in UI · no four-layer state change.
- does **not** authorize Slot Workflow v2 PR-1, does **not** fill any §13 / §12 signoff,
  does **not** make a provider routing decision, does **not** touch Hot Follow / Digital
  Anchor.

## 13. Owner Decision Needed

Recommend exactly one:

- **approve the credentialed trial** *(only if you intend to provide credentials)* — then
  Tyler supplies keys in the trial env and the §4 inputs are run offline per §1–§11,
  producing a **redacted** results report;
- **hold** — keep this as a prepared plan; proceed with the ffmpeg backbone gate spec
  (PR #235) alone for now;
- **revise the plan**.

**Recommendation:** **hold the credentialed trial** until you choose to provide
credentials; advance the **proven ffmpeg backbone gate spec** (PR #235) independently in
the meantime. When you are ready to settle the generative / subtitle / voiceover gaps,
approve this trial and it runs offline with secrets kept entirely out of the repo.

---

*This is a docs-only, prepared-not-run trial plan. It executes no provider call, commits
no secret, integrates nothing, and changes no contract/schema or the four-layer state
model. Running it requires explicit Owner approval and available credentials.*
