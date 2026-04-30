# ApolloVeo W2 Admission — Env / Secret Matrix v1

- Wave: ApolloVeo 2.0 W2 Admission Preparation — Phase B
- Authority:
  - `docs/architecture/ApolloVeo_2.0_W2_Admission_Preparation_Wave_指挥单_v1.md` §4 Phase B, §9
  - `docs/donor/swiftcraft_donor_boundary_v1.md` §3.7
  - `docs/donor/swiftcraft_capability_mapping_v1.md` rows O-01, O-02, O-03
  - `docs/reviews/W1_COMPLETION_REVIEW_v1.md` §3.1.3
- Scope: documentation only — pattern capture, no donor file copy, no provider
  client code, no runtime wiring.
- Companion files:
  - `ops/env/storage_layout_v1.md` (row O-02 detail)
  - `ops/env/secret_loading_baseline_v1.md` (loading rule + no-hardcoded-token rule)

> **Lifecycle**: this matrix is a contract for **how env keys are named, where
> they are sourced, and who owns them**. It does NOT hold any secret values.
> Secret values live in deploy systems / vaults, never in this repo.

---

## 0. Reading rules

- A key listed here is the **only** legal name for that capability. New code
  must consume the canonical name. Aliases (left-of-`or` fallbacks in
  `gateway/app/storage/r2.py` etc.) are read-only and frozen — no new aliases.
- Required vs optional is evaluated **per environment dimension** (local /
  render / production). A key may be required in production and optional in
  local dev when a degraded path exists.
- "Local source" means how a developer obtains the value on their workstation.
  "Render source" means the Render dashboard / `render.yaml`-equivalent
  injection. "Production source" is the canonical secret store.
- Fallback / degraded behaviour is the **only** sanctioned response when the
  key is missing in the environment dimensions where it is optional. New
  fallback paths require an ADR; in-line `or "default"` literals for new
  provider keys are forbidden (see `secret_loading_baseline_v1.md`).
- "Owner" is the role that holds the rotation authority for the secret.

---

## 1. Environment dimensions

| Dimension | Purpose | Authority |
|---|---|---|
| `local` | engineer workstation, unit / integration tests, no live provider calls by default | `.env.local` (gitignored), per-engineer |
| `render` | Render.com hosted preview / staging | Render service env (dashboard) |
| `production` | live tenant traffic | production secret store (vault) + Render production service env |

Same key name across all three dimensions. Different **values**, never
different **names**.

---

## 2. Row O-01 — Capability / Provider env matrix

### 2.1 Core platform

| Key | Required | Local source | Render source | Production source | Fallback / degraded | Owner | Notes |
|---|---|---|---|---|---|---|---|
| `DATABASE_URL` | required (prod), optional (local) | `.env.local` | Render env | vault | local default `sqlite:///./shortvideo.db` (`gateway/app/db.py`) | platform | rotate on db credential change |
| `AUTH_MODE` | optional | `.env.local` | Render env | Render env | default `both` (`gateway/app/auth.py:33`) | platform | controls cookie vs key auth |
| `OP_ACCESS_KEY` | required | `.env.local` | Render env | vault | none — auth fails closed | platform | rotate quarterly; reissue invalidates active op sessions |
| `SESSION_SECRET` | required | `.env.local` | Render env | vault | none — sessions cannot be issued | platform | rotate on suspected compromise; rotation invalidates all sessions |
| `OP_KEY_HEADER` | optional | n/a | Render env | Render env | default `X-Op-Access-Key` | platform | only override for header rename |
| `SESSION_TTL_SECONDS` | optional | n/a | Render env | Render env | default `43200` | platform | non-secret tuning |
| `DEFAULT_UI_LOCALE` | optional | n/a | Render env | Render env | default `zh` | product | non-secret |
| `LOG_LEVEL` / `APP_LOG_LEVEL` / `UVICORN_LOG_LEVEL` | optional | n/a | Render env | Render env | default per `core/logging_config.py` | platform | non-secret |
| `RENDER_GIT_COMMIT` / `GIT_SHA` / `COMMIT_SHA` | optional | n/a | Render auto-injected | Render auto-injected | reported as `unknown` in `/healthz` | platform | non-secret build metadata |

### 2.2 Storage (also see `storage_layout_v1.md`)

R2/S3 has two historical alias families. **Canonical names** are the left
column. `gateway/adapters/r2_s3_client.py` keeps the alias `or` chain for
backwards compatibility; new code must read canonical names only.

| Key (canonical) | Aliases (read-only) | Required | Local source | Render source | Production source | Fallback / degraded | Owner |
|---|---|---|---|---|---|---|---|
| `R2_ENDPOINT` | `R2_ENDPOINT_URL` | required (prod) | `.env.local` (optional) | Render env | vault | storage feature disabled if any of the four R2 keys missing (`gateway/app/main.py:248-251`) | platform |
| `R2_BUCKET_NAME` | `R2_BUCKET` | required (prod) | `.env.local` (optional) | Render env | vault | as above | platform |
| `R2_ACCESS_KEY` | `R2_ACCESS_KEY_ID` | required (prod) | `.env.local` (optional) | Render env | vault | as above | platform |
| `R2_SECRET_KEY` | `R2_SECRET_ACCESS_KEY` | required (prod) | `.env.local` (optional) | Render env | vault | as above | platform |
| `R2_REGION` | — | optional | n/a | Render env | Render env | default `auto` | platform |
| `R2_PUBLIC_BASE_URL` | — | required if signed-URL bypass desired | n/a | Render env | Render env | signed URL fallback path | platform |
| `FEATURE_STORAGE_ENABLED` | — | optional | `.env.local` | Render env | Render env | default `false` — local filesystem path | platform |
| `SIGNED_URL_EXPIRES` | — | optional | n/a | Render env | Render env | default `900` | platform |
| `PUBLISH_PROVIDER` | — | optional | n/a | Render env | Render env | default `local` | platform |
| `STORAGE_BACKEND` / `TASK_REPO_BACKEND` | — | optional | `.env.local` | Render env | Render env | default `file` (`gateway/app/routers/tasks.py:1530`) | platform |
| `V17_PACKS_DIR` | — | optional | n/a | Render env | Render env | default `deliver/packs` | platform |
| `MAX_LOCAL_UPLOAD_MB` | — | optional | n/a | Render env | Render env | default `200` | platform |
| `MAX_BGM_UPLOAD_MB` | — | optional | n/a | Render env | Render env | default `50` | platform |
| `DISK_ROOT` | — | required (render/prod) | n/a | Render env | Render env | default `/var/data` (`scripts/render_preflight.sh`) | platform |
| `VIDEO_WORKSPACE` | — | optional | n/a | Render env | Render env | default `/opt/render/project/src/video_workspace` | platform |
| `DEMO_ASSET_BASE_URL` | — | optional | n/a | Render env | Render env | empty string | platform |

### 2.3 Provider — ASR / Whisper (W2.1 admission target)

| Key | Required | Local source | Render source | Production source | Fallback / degraded | Owner | Notes |
|---|---|---|---|---|---|---|---|
| `ASR_BACKEND` | optional | `.env.local` | Render env | Render env | default `whisper` (`gateway/app/services/steps_v1.py:804`) | capability | non-secret routing |
| `WHISPER_MODEL` | optional | `.env.local` | Render env | Render env | default `small` (preflight) | capability | non-secret |
| `FASTER_WHISPER_MODEL` | optional | `.env.local` | Render env | Render env | falls back to `WHISPER_MODEL` | capability | non-secret |
| `SUBTITLES_ASR_TIMEOUT_RTF` | optional | n/a | Render env | Render env | default `3.0` | capability | non-secret tuning |
| `SUBTITLES_ASR_LANG_HINT` | optional | n/a | Render env | Render env | none | capability | non-secret |
| `HF_HOME` / `XDG_CACHE_HOME` | optional | n/a | Render env (set by preflight) | Render env (set by preflight) | derived from `DISK_ROOT` | platform | model cache locations |

W2.1 absorption may add a Whisper-provider key (e.g. `WHISPER_API_KEY` if a
hosted variant is wired). That row will be added when the W2.1 PR opens, not
preemptively here.

### 2.4 Provider — Subtitles / Gemini

| Key | Required | Local source | Render source | Production source | Fallback / degraded | Owner | Notes |
|---|---|---|---|---|---|---|---|
| `GEMINI_API_KEY` | required when `SUBTITLES_BACKEND=gemini` | `.env.local` | Render env (secret) | vault | provider falls back per existing degraded path; no in-code default | capability | rotate via Google AI Studio; revoke on key leak |
| `GOOGLE_API_KEY` | optional alias | `.env.local` | Render env (secret) | vault | read as fallback for `GEMINI_API_KEY` (`gateway/app/providers/gemini_subtitles.py:17`) | capability | freeze — no new code should consume this alias |
| `GEMINI_BASE_URL` | optional | n/a | Render env | Render env | default `https://generativelanguage.googleapis.com/v1beta` | capability | non-secret |
| `GEMINI_MODEL` | optional | n/a | Render env | Render env | default `gemini-2.0-flash` | capability | non-secret |
| `SUBTITLES_BACKEND` | optional | `.env.local` | Render env | Render env | default `gemini` | capability | non-secret routing |
| `REVIEW_BRIEF_PROMPT_VERSION` | optional | n/a | Render env | Render env | default `v1` | capability | non-secret |

### 2.5 Provider — Dub / Voice

| Key | Required | Local source | Render source | Production source | Fallback / degraded | Owner | Notes |
|---|---|---|---|---|---|---|---|
| `DUB_PROVIDER` | optional | `.env.local` | Render env | Render env | request body wins; env is fallback (`gateway/app/services/steps_v1.py:1026`) | capability | non-secret routing |
| `DUB_SKIP` | optional | `.env.local` | Render env | Render env | default disabled | capability | non-secret tuning |
| `DEFAULT_MM_LANG` | optional | n/a | Render env | Render env | default `my` | capability | non-secret |
| `DEFAULT_MM_VOICE_ID` | optional | n/a | Render env | Render env | default `mm_female_1` | capability | non-secret |
| `HF_LIPSYNC_ENABLED` | optional | n/a | Render env | Render env | default `0` | capability | Hot Follow flag — frozen by W2 admission §3.4 |
| `HF_LIPSYNC_SOFT_FAIL` | optional | n/a | Render env | Render env | default `1` | capability | Hot Follow flag — frozen |

W2.2 dub providers (Azure, ElevenLabs, etc.) will introduce keys such as
`AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION`, `ELEVENLABS_API_KEY` — those rows
land with the W2.2 admission PR, not here.

### 2.6 Provider — Avatar / VideoGen (W2.3, planning only)

| Key | Required | Local source | Render source | Production source | Fallback / degraded | Owner | Notes |
|---|---|---|---|---|---|---|---|
| `APOLLO_AVATAR_PROVIDER` | optional | `.env.local` | Render env | Render env | default `fal_wan26_flash` (`gateway/app/config.py:141`) | capability | non-secret routing only; provider key NOT yet bound |

Avatar / VideoGen / Storage providers are W2.3 planning territory. No
provider-secret rows are pinned here. They will be added when the W2.3
admission PR is reviewed.

### 2.7 ffmpeg / media tuning (non-secret)

All `FFMPEG_TIMEOUT_SEC*`, `FFPROBE_TIMEOUT_SEC`, `ASR_SILENCE_DB`,
`ASR_SILENCE_MIN_SEC`, `ASS_FONT_NAME`, `ASS_FONTS_DIR` keys are non-secret
tuning knobs absorbed in W1 (`gateway/app/services/media/`). They may live
in any of the three environments and have safe in-code defaults. They are
listed here for completeness; they do NOT require vault placement.

### 2.8 Pipeline runtime flags (non-secret)

Non-secret flags: `RUN_STEPS_ASYNC`, `HF_COMPOSE_STALE_RUNNING_SEC`,
`TOOLS_REGISTRY_PATH`. Same rule as §2.7 — Render env, no vault.

---

## 3. Row O-02 — Storage layout

Detailed storage layout (R2 vs S3, prefix conventions, regional assumptions)
is captured in `ops/env/storage_layout_v1.md` to keep this matrix focused on
key names. The two documents are co-authoritative for W2 admission Phase B.

---

## 4. Row O-03 — Render preflight

`scripts/render_preflight.sh` already exists in the Apollo tree
(absorbed earlier). The matrix declares its env contract:

- Inputs: `DISK_ROOT`, `FASTER_WHISPER_MODEL`, `WHISPER_MODEL`.
- Outputs: warmed `faster_whisper` model under `$DISK_ROOT/models`,
  `$HF_HOME` and `$XDG_CACHE_HOME` exported.
- Owner: platform.
- Production behaviour: invoked by Render build pipeline; non-fatal warmup.
- Local behaviour: not invoked; engineers run unit tests without preflight.

The mapping doc target `ops/runbooks/render_preflight.sh` is a future move
target. We do **not** copy or move the script in this wave; the canonical
location remains `scripts/render_preflight.sh` until a deploy-pipeline change
authorizes the move. Row O-03 status remains **Not started** for the move;
its env contract is captured here.

---

## 5. Hardcoded-token / hardcoded-key rule (write-back)

> **Rule (binding)**: provider secrets MUST be loaded from environment
> variables listed in this matrix. They MUST NOT be:
>
> 1. Committed to the repository in any form (no `.env` files, no example
>    `.env.example` containing live values, no fixtures, no test data, no
>    docstrings, no comments).
> 2. Hard-coded as Python literals, including as `default=` values in
>    `os.getenv("KEY", "...")`.
> 3. Embedded in Render `render.yaml` or any other versioned deploy
>    descriptor.
> 4. Transmitted via shared chat tools, screenshots, or pull-request
>    descriptions.

The rule is enforced operationally via:

- `secret_loading_baseline_v1.md` §3 (canonical loading pattern)
- `tests/guardrails/test_donor_leak_boundary.py` (literal-token scan,
  currently for `swiftcraft`; pattern reusable for provider names)
- security-review on the first W2.1 PR (per W1 review §3.2 R6)

Adding a new provider key means: (a) edit this matrix, (b) edit
`secret_loading_baseline_v1.md` if the loading pattern is non-standard,
(c) open the W2 admission PR. No silent additions.

---

## 6. Change discipline

- This matrix is **append-only** within a wave. Renaming a key is a
  separate, reviewed change (it breaks deployed environments).
- Each W2.x admission PR appends one section per provider it absorbs.
  No PR may add a provider key here that it does not also wire correctly
  to the canonical loader.
- Removing a key requires citing the deprecation path and grace period in
  the PR description, plus a follow-up cleanup PR after the grace period.

---

## 7. Out of scope for this wave

Per the W2 admission directive §0 / §7, Phase B explicitly does NOT cover:

- Provider client / SDK absorption code.
- Runtime wiring of any provider key (no new `os.getenv` call sites in
  provider clients in this PR).
- Hot Follow main-line behaviour changes.
- AdapterBase lifecycle review or implementation (Phase C).
- Donor SHA pin update (Phase C).
- Hot Follow regression baseline freeze (Phase D).
- Render deploy descriptor (`render.yaml` etc.) authorship.
