# Owner Summary — Matrix Script Credentialed Provider Trial Readiness (2026-06-07)

Docs-only. Readiness summary for the credentialed offline provider trial. **Prepared,
NOT run.** No provider call executes until the Owner explicitly approves AND credentials
are available. Not authority.

Plan: `docs/design/MATRIX_SCRIPT_CREDENTIALED_PROVIDER_TRIAL_PLAN_20260607.md` (#236, merged)
Source evidence: `docs/execution/MATRIX_SCRIPT_CAPABILITY_OFFLINE_TRIAL_REPORT_20260607.md`

## 1. Providers proposed for trial

- **image_to_video (generative):** Kling · Runway (or equivalent) · Veo — on BM-1
  (`02_tomato_bowl`) and BM-3 (`04_eat_tomato`).
- **voiceover:** Azure Speech (TTS) — on the BM-4 CTA line.
- **subtitle_style:** a freetype/libass-enabled ffmpeg build **or** a pre-rendered-PNG →
  `overlay` adapter (incl. a CJK font) — on BM-4. (No third-party API key needed; this is
  a local build/adapter + font-license check.)
- **Not in this trial:** broll_retrieval, bgm_select (pend library + license screen);
  avatar_segment, face_swap (future/gated).

## 2. Required credentials

| Capability | Provider | Minimum credential |
|------------|----------|--------------------|
| image_to_video | Kling | Kling API key/secret |
| image_to_video | Runway (or equiv) | Runway API key |
| image_to_video | Veo | Google/Vertex credential with Veo access + quota |
| voiceover | Azure Speech | Azure Speech key + region |
| subtitle_style | local ffmpeg build / adapter | none (font-license check only) |

A provider whose credential is unavailable is **SKIPPED** with reason — never substituted
or faked.

## 3. Where credentials will be supplied (no secrets in repo)

- Credentials are supplied by **Tyler in the trial environment only** — exported as shell
  env vars for the run, or held in the OS keychain — **outside** the repo tree.
- **Never** committed, never written to any tracked file, never referenced by path in a
  committed doc, never pasted into a PR/log.
- Used only against each provider's official endpoint over TLS; no third-party relay.
- After the run: env vars unset / keychain entry removed (nothing persisted).
- A pre-commit key-shaped-string / `Authorization` scan MUST pass before any results
  report is committed.

## 4. Cost cap

- **Default hard cap: USD 20 total** for the whole trial run (Owner may set a different
  cap on approval). Per-capability soft sub-caps: image_to_video ≤ $12, voiceover ≤ $3,
  remainder buffer.
- The run **stops** when the cumulative metered spend reaches the cap (see §9 stop
  conditions). Cost is logged per call (numbers only; no billing identifiers).
- If a single provider's per-clip cost would blow the cap in a few calls, it is capped to
  a minimal sample (e.g. 1–2 clips) and noted.

## 5. Expected inputs

- **image_to_video:** local stills `02_tomato_bowl.png` (BM-1) + `04_eat_tomato.png`
  (BM-3) + a short motion prompt; target 3s, 1080×1920.
- **subtitle_style:** a BM-3 clip + an English subtitle line + a CJK subtitle line (font
  path test) + a styled CTA card spec.
- **voiceover:** BM-4 CTA text (English + target market language) for TTS.
- All inputs are existing local assets / hand-authored text — no PII, no secret.

## 6. Expected outputs

- **image_to_video:** one short mp4 per provider per shot (h264, 1080×1920) + metrics.
- **subtitle_style:** a clip with burned/styled subtitle (English + CJK) proving the
  render path, or a documented failure.
- **voiceover:** an audio track + a composed BM-4 with synced audio + subtitle + metrics.
- A **redacted** results report (numbers + verdicts only) is the sole committed output.

## 7. Output artifact location

- Generated media + raw per-call logs land in a **scratch dir outside the repo**
  (e.g. `/tmp/ms_cred_trials/`); **binaries are NOT committed**.
- Only the **redacted results report** (docs) is committed, to
  `docs/execution/` (e.g. `MATRIX_SCRIPT_CREDENTIALED_TRIAL_REPORT_<date>.md`) + an Owner
  Summary under `docs/execution/owner_summaries/`.

## 8. Log redaction rules

- No key/token/region/endpoint/account-id in any committed file or printed log.
- Request/response captures strip `Authorization` and any credential echo before logging.
- Logs contain: latency, metered cost (number), quality scores (1–5 per dimension),
  pass/fail, failure mode — **no secret, no PII**.
- A redaction scan runs before committing any results report; a hit blocks the commit.

## 9. Stop conditions

The run STOPS immediately and reports if any of these occur:

- cumulative metered spend reaches the **cost cap** (§4);
- a provider returns an **auth / quota / rate-limit / content-policy** error (that
  provider is SKIPPED with reason; others may continue);
- a **secret would be written to the repo or a log** (hard stop — fix redaction first);
- a **ToS / content-rights / font-license** check fails for a candidate (that candidate
  is blocked, not trialled);
- the Owner withdraws approval, or credentials are unavailable.

## 10. Owner Decision Needed

Declare one:

- **approve running the credentialed offline trial** — *only if you will supply
  credentials*; then Tyler exports keys in the trial env, the run executes offline within
  the cost cap, and a redacted results report is produced;
- **hold** — keep this prepared; advance the ffmpeg backbone gate spec (#235, merged)
  toward a separate §12 signoff instead;
- **revise** — adjust providers, cap, inputs, or criteria.

**Recommendation:** **hold** until you choose to provide credentials and a cost cap; the
proven ffmpeg backbone path (gate spec merged via #235) can advance independently via its
own §12 signoff decision. When ready, approve this trial and it runs offline with secrets
kept entirely out of the repo.

---

## 给 Claude 的指令

- **current Owner decision:** Track A #235 (ffmpeg backbone Gate Spec) MERGED; Track B
  #236 (Credentialed Provider Trial Plan) MERGED as docs-only plan. Running credentialed
  provider calls is **NOT** authorized. §12 / §13 signoffs are **NOT** filled. ffmpeg
  backbone PR-1 is **NOT** started.
- **allowed next actions (only on explicit Owner instruction):** (a) if Owner approves
  the credentialed trial AND supplies credentials → run the offline trial per the plan
  within the cost cap and produce a **redacted** results report; (b) if Owner authorizes
  the backbone §12 signoff → author a separate docs-only §12 signoff PR; (c) otherwise →
  hold. All future work stays docs-first / Owner-gated.
- **forbidden actions:** no running provider calls without explicit Owner approval +
  credentials; no secrets in repo or logs; no runtime implementation; no `gateway/**` /
  services / templates / tests change; no provider adapter code; no generative-provider
  integration; no schemas/contracts change; no vendor exposure in UI; no four-layer state
  change; no ffmpeg backbone PR-1; no filling §12 / §13 signoff; no automatic provider
  routing decision.
- **required outputs (this round, delivered):** #235 merge report; #236 merge report;
  this readiness summary at
  `docs/execution/owner_summaries/matrix_script_credentialed_provider_trial_readiness_owner_summary_20260607.md`.
- **validation checks (run before any commit):** `git diff --check`; docs-only scan
  (all staged under `docs/`); forbidden-path scan (no `gateway/`, `schemas/`,
  `docs/contracts/`, `.py`, tests, routers); for any future results report, a
  secret/redaction scan.
- **stop point:** stop after the #235 merge report, the #236 merge report, and this
  readiness summary. Do **not** run provider calls; do **not** start runtime; do **not**
  fill signoffs.
- **Owner Decision Needed:** choose one — approve running the credentialed offline trial
  (with credentials + cost cap) · hold · revise (per §10).
