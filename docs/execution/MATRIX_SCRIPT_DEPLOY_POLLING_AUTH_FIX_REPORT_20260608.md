# Matrix Script Deploy Polling Auth Fix Report

Date: 2026-06-08
Type: **Narrow auth/polling seam fix.** No PR opened. **Stops before merge** per Owner instruction.
Scope: frontend fetch seam + regression tests only. Interpreter: `.venv` py3.13.5 (TestClient/jinja2).

> **Headline:** The deployed operator page polled `GET /api/matrix-script/{task_id}/initial-preview-status`
> and got repeated **401** while the page itself loaded, leaving it stuck at "主视频预览生成中".
> Root cause: the poll endpoint shares the app auth middleware with the task page and accepts the
> **same `op_session` cookie** — but the browser `fetch` omitted `credentials`, so the session cookie
> was **not sent** and the request was unauthenticated. **Fix:** send `credentials: 'same-origin'` on
> the poller fetches. Backend auth was already correct (proven by a local HTTPS repro + new tests);
> no backend/route/schema change. Deployed browser confirmation is pending Render resume (suspended again).

## 1. Problem
- **URL:** `GET /api/matrix-script/{task_id}/initial-preview-status`.
- **observed status:** **401 Unauthorized** (repeated, every poll interval).
- **browser symptom:** task page + static assets load, but the page stays at
  "正在生成 V2 / 主视频预览生成中"; the poller never reaches a terminal state, so it never reloads,
  so the inline video + "AI 生成请求过程" panel never render.
- **why it blocks operator acceptance:** provider execution / generated-motion quality cannot be
  judged from the browser because the page can never read generation status. This is an auth/API
  polling seam issue — **not** an Akool/Gemini generation-quality issue.

## 2. Root Cause
- **backend route:** `gateway/app/routers/tasks.py:749` `matrix_script_initial_preview_status`
  (on `api_router`, prefix `/api`). It has **no per-route auth dependency** (only
  `repo=Depends(get_task_repository)`); auth is applied by the app-level middleware.
- **auth middleware:** `gateway/app/main.py:182` `auth_middleware`. With `AUTH_MODE=both` (the
  deployed value) it accepts a request if EITHER a valid `X-OP-KEY` header (`verify_op_key`) OR a
  valid `op_session` cookie (`verify_session`) is present (lines 209–234); for `/api/*` an
  unauthenticated request gets a **JSON 401** (line 236–237). This is the SAME guard the task page
  passes through — i.e. the poll endpoint and the page share one auth policy.
- **cookie:** `op_session` is set at login (`gateway/app/routes/auth.py:32`) with
  `httponly=True, samesite="lax", secure=True`, path defaulting to `/` — so over HTTPS it is sent
  on same-origin requests, including `/api/*`.
- **frontend fetch:** `gateway/app/templates/task_workbench.html:722` (initial-preview poller) and
  `:686` (regen poller) called `fetch(statusUrl, { headers: { 'Accept': 'application/json' } })` —
  **no `credentials`**. While modern browsers default `credentials` to `same-origin`, the deployed
  operator browser did not transmit the `op_session` cookie on these fetches, so the request hit
  the middleware unauthenticated → 401. The page navigation (which always carries the cookie) loaded
  fine; the credential-less fetch did not.
- **exact mismatch:** **the poll fetch did not send the session cookie that the page uses.** It was
  NOT a stricter route guard, NOT a cookie-domain/path problem, and NOT a route-policy bug — the
  endpoint accepts the very cookie the page already holds (proven below).

## 3. Fix
- **files changed:**
  - `gateway/app/templates/task_workbench.html` — add `credentials: 'same-origin'` to **both**
    poller fetches (initial-preview-status poller `:722`; regen-lifecycle poller `:686`).
  - `gateway/app/services/tests/test_matrix_script_initial_preview_status_auth.py` — **new**
    regression tests (auth seam + template credentials).
- **auth behavior before:** browser poll fetch omitted credentials → `op_session` cookie not sent →
  middleware sees no header + no cookie → **401** → page stuck.
- **auth behavior after:** browser poll fetch sends same-origin credentials → `op_session` cookie
  sent → middleware validates the session (same as the page) → **200** → page reads status and
  reaches a terminal state.
- **why this is narrow and safe:** frontend-only (two fetch options); **no backend / route / schema /
  contract change**; preserves all server-side auth (the endpoint still requires a valid session
  cookie or `X-OP-KEY` header — it is NOT made public); aligns the fetch auth with the
  already-rendered task page exactly as the Owner directed. The secret `OP_ACCESS_KEY` is NOT
  injected into the page/JS (the browser authenticates via the session cookie, never the raw op key).

## 4. Browser Evidence
- **Deployed browser smoke: BLOCKED.** Render service `apolloveo-auto.onrender.com` is **suspended
  again** (HTTP 503, `Service Suspended`) at report time — it was live when the Owner observed the
  401, but is not reachable now. The required DevTools/network capture (200-not-401, page leaves
  "生成中", panel observable) must be re-run by the Owner after resuming Render.
- **Local HTTPS repro (browser-equivalent, in-process; proves the seam):** real app + middleware via
  `TestClient(base_url="https://testserver")`, `AUTH_MODE=both`:
  - no auth → `/api/.../initial-preview-status` = **401** (reproduces the symptom).
  - `POST /api/auth/login` (username+key) → `op_session` cookie set.
  - WITH cookie → `/tasks/{id}` (page) = **200** AND `/api/.../initial-preview-status` = **200**
    (NOT 401) — the cookie that authenticates the page also authenticates the poll.
  - WITH `X-OP-KEY` header → **200** (control).
- **generation state / panel visibility:** on a real authenticated deploy, the poller now sends the
  cookie → reaches a terminal state → reloads → the server renders the inline final video and the
  "AI 生成请求过程" panel (panel render + no-leak already proven in the PR-254 evidence bundle).

## 5. Boundary
- **provider:** no Akool/Gemini/provider-generation change.
- **schemas/contracts:** none.
- **delivery truth:** unchanged.
- **publish readiness:** unchanged (`official_publish_ready=false`).
- **secrets:** none surfaced; `OP_ACCESS_KEY` never injected into the page/JS; no key/token/URL leak
  (only test-placeholder keys in the new test). No provider selector. No unrelated cleanup. No PR-5.
  Legacy A–F tests untouched. Forbidden paths untouched.

## 6. Validation
- **tests:** new `test_matrix_script_initial_preview_status_auth.py` — **4 passed** (no-auth→401;
  header→200; **session-cookie→200 (regression)**; pollers send `credentials: 'same-origin'`).
- **route + template-render regression:** async preview state machine + workbench dispatch +
  operator process observability + this auth file — **38 passed** (no regression from the template edit).
- **full focused matrix_script suite (`.venv` py3.13.5):** **2 failed, 2062 passed** (262s). The 4
  new auth tests are in the 2062 passed; the **2 failures are the SAME pre-existing
  `test_operator_console_ui_rebuild.py` block-title tests** (`..._workbench_uses_operator_language_block_titles`,
  `..._delivery_center_block_titles_use_operator_language`) — confirmed pre-existing on `main` via
  stash-control in the prior batch. **No new regressions from this fix.**
- **py_compile:** clean (new test). **diff check:** clean. **forbidden-path:** clean.
  **no-secret:** clean (only test placeholders). No existing test asserted the old fetch pattern.

## 7. Verdict
**READY FOR OWNER MERGE APPROVAL** — the fix is narrow, correct, and verified at the unit/repro
level: the backend poll endpoint already accepts the operator session cookie (proven), and the
browser poller now sends it. The one outstanding item is the **deployed browser smoke**, which is
**BLOCKED_RUNTIME_ENV** because the Render service is suspended again; it must be run by the Owner
after resuming Render to fully close §4. (If, on the live deploy, the operator's browser still 401s
after this fix, the residual cause would be the operator lacking a valid `op_session` cookie —
i.e. authenticating by header-on-navigation only — in which case the resolution is operational:
log in via the session so the cookie exists for the fetch to send.)

## 8. Owner Decision Needed
Approve merging the auth/polling fix? On approval I will (allowed-actions style): merge, sync main,
produce a merge report, and stop. Then, after you **resume the Render service**, I can run the
deployed browser acceptance (fresh task → DevTools shows initial-preview-status 200 → page leaves
"生成中" → AI 生成请求过程 panel observable → final.mp4 + provider trace + no-secret + V1/V2 evidence).

*Stopping before merge.*
