# VeoMatrixVoice05 · Matrix Script Ingest Auth / JSON-Boundary P0 Fix · Report v1

Date: 2026-05-30
Status: **P0 fix PR — auth-error JSON boundary + safe login redirect only.** No contract / schema / packet / closed-enum / runtime-worker change. No Phase 3. No VoiceTrans bridge. No Asset Supply bridge. No Hot Follow / Digital Anchor behavior change. No faked media. No `main` merge. No new VeoMatrixVoice branch.

Authoring authority: user mission `[SYSTEM OVERRIDE]` 2026-05-30 (ApolloVeo Matrix Script Auth/Ingest P0 Fix Operator).

---

## 1. Branch and base

| Item | Value |
|---|---|
| Base branch | `VeoMatrixVoice05` |
| Base commit | `bb673b8` (`docs(matrix-script): record phase2c operator readability validation`) |
| Fix branch | `fix/veomatrixvoice05-ms-ingest-auth-json-boundary-20260530` |
| Commit message | `fix(matrix-script): return json auth errors for source script ingest` |

---

## 2. Root cause

On `/tasks/matrix-script/new?ui_locale=zh`, after pasting script text the operator saw:

```
Unexpected token '<', "<!doctype "... is not valid JSON
```

Two coupled defects:

1. **JSON boundary defect (primary).** The frontend fetch posts to
   `POST /tasks/matrix-script/source-script-refs/ingest`. That route lives
   under `/tasks/`, so the auth middleware's `_is_api_path(path)` (which only
   matches `/api/` and `/v1/`) did **not** classify it as an API path. When the
   operator session was absent/expired, the middleware fell through to the
   **HTML redirect branch** and returned `302 → /auth/login?next=…`. `fetch`
   transparently followed the 302 to the HTML login page, and the frontend then
   called `response.json()` on `<!doctype html>` — producing the
   "Unexpected token '<'" crash. Reproduced via TestClient: unauthenticated
   POST with `Accept: application/json` returned `302` with
   `Location: /auth/login?next=/tasks/matrix-script/source-script-refs/ingest`.

2. **Unsafe post-login `next` defect (secondary).** The `/auth/login` GET route
   passed the raw `next` query param straight to the template, and the redirect
   above made `next` the POST-only ingest endpoint. After a successful login the
   page would navigate (GET) to a POST-only JSON API — a broken landing.

---

## 3. Fix — defense in depth (A + B + C)

### A. Frontend fetch hardening — `gateway/app/templates/matrix_script_new.html`
- `ingestBody()` sends `Accept: application/json` and, **before** calling
  `resp.json()`, guards on `resp.status === 401 || 403`, `resp.redirected`, and
  a `text/html` content-type. Any of these throws an `authRequired` error
  carrying the operator message **「登录已失效，请重新登录后再提交脚本。」** —
  `resp.json()` is never called on a non-JSON body.
- A non-JSON, non-auth response throws a readable "非预期的响应格式 (HTTP …)".
- New shared `onIngestError(err)` handler restores the submit affordance, shows
  the message, and (only for `authRequired`) redirects after ~1.6s to
  `/auth/login?next=` + `encodeURIComponent('/tasks/matrix-script/new?ui_locale=zh')`
  — a **safe** next that returns to the operator page, never the ingest endpoint.
- Both the paste-path and upload-path `.catch(...)` blocks now delegate to
  `onIngestError` (previously inline handlers that reset to stale button text).

### B. Backend auth behavior — `gateway/app/main.py`
- New `_wants_json(request)` helper: true when `Accept` contains
  `application/json`, `X-Requested-With: XMLHttpRequest`, or the request
  content-type is `application/json`.
- In the unauthenticated branch of `auth_middleware`, JSON/XHR callers now
  receive **`401` JSON** instead of a `302` to HTML:
  ```json
  {"ok": false, "error": "auth_required", "message": "登录已失效，请重新登录后再提交脚本。"}
  ```
- Existing `/api/` + `/v1/` paths are **unchanged** — they still return
  `{"detail": "Unauthorized"}` (back-compat preserved). Browser/navigation
  (non-JSON) requests still get the `302 → /auth/login` redirect.

### C. Login `next` sanitization — `gateway/app/main.py`
- New `_safe_next(next)` helper, applied in `auth_login_page`. It honours only
  same-origin path-absolute targets and falls back to `/tasks` for: empty,
  non-`/`-prefixed, protocol-relative (`//host`), any scheme (`://`,
  `javascript:`), backslash, and the POST-only / JSON-body endpoints
  (`…/source-script-refs/ingest`, `…/mint`, any `…/source-script-refs/…`,
  `/api/`, `/v1/`).

### D / E — contract + security preserved
- The Matrix Script POST payload shape `{"source_kind": ..., "body": ...}` is
  **unchanged**; `source_script_ref` scheme `content://matrix-script/source/<token>`
  unchanged; no packet / schema / closed-enum touched.
- Auth is **not** bypassed and ingest is **not** made public — the fix changes
  only the *form* of the auth-denied response (JSON vs HTML) and the safety of
  the login redirect target.

---

## 4. Files changed

| File | Status | Kind |
|---|---|---|
| `gateway/app/main.py` | MODIFIED | Auth middleware JSON-401 + `_safe_next` login sanitization |
| `gateway/app/templates/matrix_script_new.html` | MODIFIED | Fetch hardening + shared `onIngestError` |
| `gateway/app/services/tests/test_matrix_script_ingest_auth_json_boundary.py` | NEW | 9-case scoped regression test |

`git diff --stat`: 2 files changed (+113 / −12) + 1 new test file. **Zero** entries
under `docs/contracts/`, `schemas/`, `samples/`, any packet/closed-enum file, any
worker/generator module, or any Hot Follow / Digital Anchor / Asset Supply /
VoiceTrans runtime path. The ingest route handler in `gateway/app/routers/tasks.py`
was **not** modified.

---

## 5. Exact route / template fixed

- Route protected correctly: `POST /tasks/matrix-script/source-script-refs/ingest`
  (constant `MATRIX_SCRIPT_INGEST_ROUTE`).
- Middleware: `gateway/app/main.py` `auth_middleware` unauthenticated branch +
  `_wants_json` + `_safe_next`; login route `auth_login_page`.
- Frontend: `gateway/app/templates/matrix_script_new.html` `ingestBody` /
  `onIngestError`.

---

## 6. Tests run

New scoped file `test_matrix_script_ingest_auth_json_boundary.py` — **9 cases, all green**:

1. Unauthenticated ingest w/ `Accept: application/json` → **401 JSON**, not 302.
2. The 401 body is JSON and does **not** start with `<!doctype html>`.
3. Frontend JS guards (`resp.redirected` / `text/html` / 401 / 403) **precede**
   `resp.json()` — source-level.
4. Login default `next` is never the ingest endpoint (`_safe_next` + rendered page).
5. `_safe_next` rejects external / protocol-relative / `javascript:` / mint / `/api/`.
6. Authenticated ingest (`source_kind=operator_paste` + body) → **valid JSON
   envelope** with `content://matrix-script/source/<token>`.
7. New Task five-card structure + CTA `生成视频方案` preserved.
8. No VoiceTrans iframe / raw embed in the New Task page.
9. Ingest POST contract / scheme constant unchanged; preserved payload keys.

Focused regression run (Python 3.13 venv, `PYTHONPATH=.`):

```
test_auth_middleware_misconfig.py                              (503 misconfig back-compat)
test_matrix_script_source_script_ref_ingest.py
test_matrix_script_source_script_body_store.py
test_matrix_script_new_task_entry_cards_fidelity.py
test_matrix_script_workbench_phase2c_operator_readability.py
test_matrix_script_ingest_auth_json_boundary.py               (NEW — 9)
→ 107 passed
```

### 6.1 Pre-existing unrelated failures (NOT caused by this fix)

`test_matrix_script_source_script_ref_shape.py` has 2 stale assertions —
`test_template_helper_text_forbids_pasting_body` and
`test_template_helper_text_documents_transitional_convention` — that require the
New Task helper text to **forbid** pasting body (`"不要" in template`). The Phase
2C redesign deliberately **added** a paste-script tab, so these assertions are
stale. **Verified they fail identically on base commit `bb673b8` with this PR's
working tree stashed**, i.e. they pre-date and are independent of this auth/JSON
fix. They are out of scope here (this P0 fix must not redesign UI or change
contracts) and are flagged for a separate follow-up.

---

## 7. Manual validation status

Live browser smoke was simulated via TestClient (the operator-paste sample
「美女手中捧着一个透明的玻璃碗…」 path):

- Unauthenticated paste → middleware returns **401 JSON `auth_required`**; the
  frontend now shows 「登录已失效，请重新登录后再提交脚本。」 and routes to
  `/auth/login?next=/tasks/matrix-script/new?ui_locale=zh` (safe), instead of the
  prior "Unexpected token '<'" crash.
- Authenticated paste → ingest returns a valid JSON envelope with a fresh
  `content://matrix-script/source/<token>` handle and `body_char_count > 0`,
  then the form proceeds.

Recommended human re-test on VeoMatrixVoice05: open
`/tasks/matrix-script/new?ui_locale=zh`, paste the sample, confirm (a) with a
valid session it ingests and advances, and (b) with an expired session it shows
the readable auth message and lands back on the New Task page after login.

---

## 8. No-change statement (what this PR does NOT do)

This PR does NOT: start Phase 3; change any contract, schema, packet, or closed
enum; change the Matrix Script POST payload shape or `source_script_ref` scheme;
add a backend video worker; add a VoiceTrans bridge; add an Asset Supply bridge;
change Hot Follow or Digital Anchor behavior; fake `final_video` / media URL /
`publish_url` / generated media; expose provider / model / vendor / engine
controls; redesign the UI; bypass auth or make ingest public; create a new
VeoMatrixVoice branch; or merge to `main`.

---

## 9. Verdict

**P0 fixed.** The auth/ingest JSON boundary is closed at all three layers
(frontend guard + middleware JSON-401 + safe login redirect), the Matrix Script
POST contract and `source_script_ref` scheme are intact, auth remains enforced,
and the 9-case scoped suite plus 107-test focused regression are green (the only
2 failing tests are pre-existing, stale, and unrelated). **Ready to re-test
VeoMatrixVoice05 functional validation.**
