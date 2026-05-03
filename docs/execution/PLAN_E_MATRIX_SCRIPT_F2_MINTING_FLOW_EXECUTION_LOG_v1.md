# Plan E PR-2 / Item E.MS.2 — Matrix Script Option F2 Minting Flow Execution Log v1

Date: 2026-05-04
Branch: `claude/crazy-chaplygin-6288a2`
Base commit at audit: `7a1e7a6` (`Merge pull request #100 from zhaojfifa/claude/crazy-chaplygin-6288a2` — PR-1 / Item E.MS.1 landed)
Status: **Implementation landed.** Code change scoped to Item E.MS.2 of the signed Plan E gate spec; no other business surface touched.
Authority of execution: signed Plan E gate spec [docs/reviews/plan_e_matrix_script_operator_facing_gate_spec_v1.md](../reviews/plan_e_matrix_script_operator_facing_gate_spec_v1.md) §3.2, §5.2, §5.4, §6 row A2.

---

## 1. Inputs read

- [CLAUDE.md](../../CLAUDE.md) — boot sequence followed.
- [docs/reviews/plan_e_matrix_script_operator_facing_gate_spec_v1.md](../reviews/plan_e_matrix_script_operator_facing_gate_spec_v1.md) — confirmed §10 architect (Raobin 2026-05-03 12:10) + reviewer (Alisa 2026-05-03 12:18) signoffs filled and committed at `0b73644`; entry condition E7 SATISFIED; PR-2 file-fence per §5.2.
- [docs/contracts/matrix_script/task_entry_contract_v1.md](../contracts/matrix_script/task_entry_contract_v1.md) — §"Source script ref shape" addendum + §"Operator transitional convention" sub-section naming Option F2 as the resolution path.
- [gateway/app/services/matrix_script/create_entry.py](../../gateway/app/services/matrix_script/create_entry.py) — `_validate_source_script_ref_shape` + `SOURCE_SCRIPT_REF_ACCEPTED_SCHEMES` = `(content, task, asset, ref)` (frozen by §8.F).
- [gateway/app/routers/tasks.py](../../gateway/app/routers/tasks.py) — Matrix Script POST handler shape; existing `JSONResponse` / `Request` / `pages_router` imports.
- [gateway/app/templates/matrix_script_new.html](../../gateway/app/templates/matrix_script_new.html) — operator-facing form, `source_script_ref` input, helper text already pinning the operator-discipline convention.

## 2. Action taken

### 2.1 Minting service (new module)

Added [gateway/app/services/matrix_script/source_script_ref_minting.py](../../gateway/app/services/matrix_script/source_script_ref_minting.py):

- **`mint_source_script_ref(*, requested_by=None) -> Mapping[str, str]`** — pure local function that allocates a fresh opaque token and wraps it in the closed `content://matrix-script/source/<token>` URI.
- **Token shape**: `mint-<16-hex-chars>` (UUID4-derived). The `mint-` prefix is a coordinator-readability convenience; the product binds **no semantic meaning** to it — the handle remains opaque to every downstream consumer per the §0.2 product-meaning of `source_script_ref`.
- **Internal acceptance assertion**: every minted handle round-trips through `_validate_source_script_ref_shape` before being returned. A future refactor that breaks the guard cannot ship.
- **`requested_by` sanitization**: optional operator-side record-keeping label only. Empty / non-string / oversize / non-printable / non-ASCII-alphabet values collapse to the empty string. Never appears in the minted handle or token; never returned as packet truth; never dereferenced.
- **Returned envelope** (closed key set): `{source_script_ref, token, minted_at, policy, requested_by}`. `policy = "operator_request_v1"` (closed enum starting set).
- **Discipline**: no I/O across runtime boundaries; no provider/vendor lookup; no asset-library backend; no operator-supplied input dereferencing; no packet mutation; no publisher-URL ingestion; no body-input handling.
- **Constants exported**: `MATRIX_SCRIPT_MINT_ROUTE = "/tasks/matrix-script/source-script-refs/mint"`, `MINTING_POLICY = "operator_request_v1"`, `MINT_TOKEN_PREFIX = "mint"`.

### 2.2 POST mint endpoint (router edit)

Added inside [gateway/app/routers/tasks.py](../../gateway/app/routers/tasks.py) right after the existing `create_matrix_script_task` POST handler:

```
@pages_router.post(MATRIX_SCRIPT_MINT_ROUTE)
async def mint_matrix_script_source_script_ref(request: Request) -> JSONResponse:
    ...
```

- Matrix-script-scoped JSON endpoint at `POST /tasks/matrix-script/source-script-refs/mint`.
- Accepts an empty body OR a small JSON body with optional `requested_by` (operator note string). Body-parse failures collapse silently to "no requested_by" — the mint service never depends on body content for handle allocation.
- Calls `mint_source_script_ref(requested_by=...)` and returns the envelope verbatim as JSON.
- New imports added at the existing import block: `MATRIX_SCRIPT_MINT_ROUTE` and `mint_source_script_ref`.
- No Hot Follow router code touched. No Digital Anchor router code touched. No temp-route promotion. No new HTTP dependency.

### 2.3 Operator affordance + helper text (template edit)

Modified [gateway/app/templates/matrix_script_new.html](../../gateway/app/templates/matrix_script_new.html):

- Added a small "铸造句柄" (Mint handle) button next to the `source_script_ref` input. The button is wired (via `data-mint-route` / `data-target-input`) to the POST mint endpoint and populates the input on success.
- Added two new helper-text paragraphs: one describing the recommended minting flow (preferred for new samples), one describing the operator-discipline transitional convention (still accepted; no migration required). The existing helper text rejecting external web URLs, bucket schemes, and body-text paste is preserved verbatim.
- Added a small inline `<script>` block that progressively enhances the affordance. Pure progressive enhancement: if JS is disabled or the fetch fails, the form continues to work with operator-discipline `<token>` handles. The script does not weaken the form's HTML5 `pattern` constraint or the `maxlength=512` cap.
- The form's `pattern` regex is unchanged (`^(?:(?:content|task|asset|ref)://\S+|[A-Za-z0-9][A-Za-z0-9._\-:/]{3,})$`); the §8.F-tightened scheme set is preserved.

### 2.4 Additive contract sub-section (documentation)

Appended a new sub-section to [docs/contracts/matrix_script/task_entry_contract_v1.md](../contracts/matrix_script/task_entry_contract_v1.md) §"Source script ref shape (addendum, 2026-05-02; tightened by §8.F on 2026-05-03)":

- **§"Operator-facing minting flow (Option F2 — addendum, 2026-05-04)"** — documents the endpoint, request envelope, response envelope, `<token>` allocation policy (`operator_request_v1`: stateless, UUID4-derived, no operator semantics), backward compatibility statement (operator-discipline handles still accepted; no migration required), and a "What this addendum does NOT do" closure that pins the §4 forbidden scope of the gate spec onto this contract surface.
- **Strictly additive.** Does not replace, weaken, remove, or widen any prior rule. The `_validate_source_script_ref_shape` guard, the §8.F-tightened `SOURCE_SCRIPT_REF_ACCEPTED_SCHEMES` closed set, the §0.2 product-meaning, the §8.A body-text rejection, and the operator-discipline `<token>` transitional convention remain in force unchanged.
- Authority pointer in the addendum cites the gate spec §3.2 / §5.2 verbatim.

### 2.5 Test module added

Created [gateway/app/services/tests/test_matrix_script_f2_minting_flow.py](../../gateway/app/services/tests/test_matrix_script_f2_minting_flow.py) covering 35 cases:

- Minting service shape + acceptance (closed key set, `content://matrix-script/source/` prefix, guard round-trip, `SOURCE_SCRIPT_REF_ACCEPTED_SCHEMES` unchanged, ISO-8601 UTC `minted_at`, distinct handles across calls).
- `requested_by` sanitization (parametrized: None / empty / whitespace-only / non-string / dict / valid label / `op:wave-3/sample-2` / non-ASCII / newline-bearing). `requested_by` does not appear in the minted handle or token. Overlong values truncate then re-validate.
- §8.A regression — body-text rejection still HTTP 400 (parametrized 3 cases + oversize payload).
- §8.F regression — publisher-URL + bucket-URI rejection still HTTP 400 with `"scheme is not recognised"` (parametrized 4 cases: `https://`, `http://`, `s3://`, `gs://`).
- Backward compatibility — pre-§8.F operator-discipline handles still accepted (parametrized 6 cases covering `content://` / `task://` / `asset://` / `ref://`).
- Mint-route scope-fence sanity (route is matrix-script-scoped; does not collide with Hot Follow / Digital Anchor / generic temp routes).
- Coordinator-readability convention (minted handle has the `content://matrix-script/source/mint-` prefix).

The test module is intentionally **import-light** (calls the service + the `_validate_source_script_ref_shape` guard directly; never instantiates the FastAPI app), so it runs cleanly on both Python 3.9 and 3.10+.

## 3. Validation

```
$ python3 -m pytest gateway/app/services/tests/test_matrix_script_f2_minting_flow.py \
                    gateway/app/services/tests/test_matrix_script_b4_artifact_lookup.py -v
============================== 65 passed in 0.29s ==============================
```

35 new F2 cases + 30 existing B4 cases (cross-PR regression sanity), all PASS on Python 3.9.6 with pytest 8.4.2.

### 3.1 Pre-existing environment limitation (not caused by PR-2)

The broader matrix_script regression set ([test_matrix_script_phase_b_authoring.py](../../gateway/app/services/tests/test_matrix_script_phase_b_authoring.py) / [test_matrix_script_workbench_dispatch.py](../../gateway/app/services/tests/test_matrix_script_workbench_dispatch.py) / [test_matrix_script_source_script_ref_shape.py](../../gateway/app/services/tests/test_matrix_script_source_script_ref_shape.py)) errors at collection time on Python 3.9 due to PEP-604 `str | None` syntax in [gateway/app/config.py:43](../../gateway/app/config.py:43) which requires Python 3.10+. Verified pre-existing on `origin/main` at `7a1e7a6` (this is the same env-only issue the PR-1 execution log noted; per [ENGINEERING_RULES.md §10](../../ENGINEERING_RULES.md): "distinguish code regressions from environment limitations"). CI on Python 3.10+ will run the full set including the new F2 test file.

### 3.2 Per-PR regression scope (gate spec §5.4 PR-2)

| Regression check | Method | Result |
| --- | --- | --- |
| §8.A body-text rejection still HTTP 400 | `test_body_text_rejection_still_http_400` (3 parametrize) + `test_oversize_payload_rejected_as_400`. | **PASS** |
| §8.F publisher-URL rejection still HTTP 400 with `"scheme is not recognised"` | `test_publisher_url_and_bucket_uri_rejection_still_http_400` (`https://`, `http://`). | **PASS** |
| §8.F bucket-URI rejection still HTTP 400 with `"scheme is not recognised"` | `test_publisher_url_and_bucket_uri_rejection_still_http_400` (`s3://`, `gs://`). | **PASS** |
| Minted `content://matrix-script/source/<product-minted-token>` handle passes the §8.A + §8.F guards on round-trip | `test_minted_handle_passes_existing_validate_source_script_ref_shape_guard` + internal acceptance assertion in `mint_source_script_ref`. | **PASS** |
| Pre-existing operator-discipline handles still accepted (no operator migration) | `test_operator_discipline_handles_still_accepted` (6 parametrize). | **PASS** |
| `SOURCE_SCRIPT_REF_ACCEPTED_SCHEMES` not widened | `test_mint_does_not_widen_accepted_scheme_set`. | **PASS** |

## 4. What this PR does NOT do

- Does NOT widen `SOURCE_SCRIPT_REF_ACCEPTED_SCHEMES` (still `(content, task, asset, ref)`).
- Does NOT weaken `_validate_source_script_ref_shape` (the guard runs against minted handles unchanged).
- Does NOT turn `source_script_ref` into a body-input field, publisher-URL ingestion field, or currently-dereferenced content address (§0.2 product-meaning preserved).
- Does NOT touch any Hot Follow file (preserves Hot Follow baseline per gate spec §7.1 / §4.4).
- Does NOT touch any Digital Anchor file (preserves Digital Anchor freeze per gate spec §7.2 / §4.1).
- Does NOT touch any cross-line projection / advisory / publish_readiness / panel-dispatch file (preserves no-platform-wide-expansion per gate spec §7.4 / §4.2).
- Does NOT mint into any scheme other than `content://`.
- Does NOT introduce an Asset Library object service, promote intent service, asset-supply page, or any other cross-line surface (gate spec §4.2).
- Does NOT dereference the minted handle to body content (the product still does not currently dereference any handle).
- Does NOT introduce a Plan B B4 `result_packet_binding` URL-shaped-ref handling (PR-1 already landed B4 with sentinel discipline; this PR does not extend B4).
- Does NOT promote any discovery-only surface to operator-eligible (gate spec §4.5).
- Does NOT modify the `_validate_source_script_ref_shape` HTML form `pattern` constraint.
- Does NOT change the §8.C deterministic Phase B authoring output (`body_ref` template unchanged).
- Does NOT start Platform Runtime Assembly or Capability Expansion (gate spec §7.5).
- Does NOT bundle Item E.MS.1 or Item E.MS.3 work — PR-1 already merged; PR-3 awaits its own slice.

## 5. Files changed

- **ADD** [gateway/app/services/matrix_script/source_script_ref_minting.py](../../gateway/app/services/matrix_script/source_script_ref_minting.py) — minting service module.
- **MOD** [gateway/app/routers/tasks.py](../../gateway/app/routers/tasks.py) — new POST endpoint + import.
- **MOD** [gateway/app/templates/matrix_script_new.html](../../gateway/app/templates/matrix_script_new.html) — affordance + helper text + small JS handler.
- **MOD** [docs/contracts/matrix_script/task_entry_contract_v1.md](../contracts/matrix_script/task_entry_contract_v1.md) — additive sub-section §"Operator-facing minting flow (Option F2 — addendum, 2026-05-04)".
- **ADD** [gateway/app/services/tests/test_matrix_script_f2_minting_flow.py](../../gateway/app/services/tests/test_matrix_script_f2_minting_flow.py) — 35 test cases.
- **ADD** [docs/execution/PLAN_E_MATRIX_SCRIPT_F2_MINTING_FLOW_EXECUTION_LOG_v1.md](PLAN_E_MATRIX_SCRIPT_F2_MINTING_FLOW_EXECUTION_LOG_v1.md) — this log.
- **MOD** [ENGINEERING_STATUS.md](../../ENGINEERING_STATUS.md) — Current Completion gains a PR-2 landed bullet.
- **MOD** [CURRENT_ENGINEERING_FOCUS.md](../../CURRENT_ENGINEERING_FOCUS.md) — Allowed Next Work refreshed for PR-2 landed posture.

No other files modified.

## 6. Final-gate four-question check

- scope stayed inside Item E.MS.2: **YES** — gate spec §5.2 file-fence respected; only the listed minting service + thin POST endpoint + form affordance + additive contract sub-section + test + log + two root status files.
- Hot Follow untouched: **YES** — `git diff HEAD~1 -- 'gateway/app/services/hot_follow_*' 'gateway/app/routers/hot_follow_api.py' 'gateway/app/templates/hot_follow_workbench.html'` returns empty.
- Digital Anchor still frozen: **YES** — no `gateway/app/services/digital_anchor/*` or `gateway/app/templates/digital_anchor*` file touched; Plan A §2.1 hide guards still in force.
- PR-2 validation passed: **YES** — 35/35 F2 test cases PASS; cross-PR sanity 30/30 B4 cases also PASS; gate spec §5.4 PR-2 regression scope all rows PASS.
- ready for PR-3 next: **YES** — gate spec §5.5 PR ordering: PR-3 (Item E.MS.3 — Matrix Script Delivery Center per-deliverable `required` / `blocking_publish` rendering) may now open under signed §10; PR-1 has landed (`7a1e7a6`) so the dependency for PR-3 is met.

End of Plan E PR-2 / Item E.MS.2 Execution Log v1.
