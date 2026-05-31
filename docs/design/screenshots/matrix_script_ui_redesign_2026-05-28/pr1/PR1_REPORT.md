# PR-1 · New Task Boundary Polish — Implementation Report

Branch: `redesign/ms-new-task-boundary-pr1-20260528`
Wave: Matrix Script Operator Experience Implementation — PR-1 of 4
Date: 2026-05-28

## Reading Declaration

Authored from the approved design plan (this conversation) + the visual
validation baseline. Files re-read before editing:

- [docs/design/screenshots/matrix_script_ui_redesign_2026-05-28/visual/VISUAL_VALIDATION_REPORT.md](../visual/VISUAL_VALIDATION_REPORT.md) (26/35 baseline; Issue #5 = responsive degradation).
- [gateway/app/templates/matrix_script_new.html](../../../../gateway/app/templates/matrix_script_new.html) (current implementation).
- [gateway/app/routers/tasks.py](../../../../gateway/app/routers/tasks.py) lines 620–688 (route handler + form POST).
- [gateway/app/services/tests/test_matrix_script_new_page_redesign_2026_05_28.py](../../../../gateway/app/services/tests/test_matrix_script_new_page_redesign_2026_05_28.py) (existing source-only assertions).

Authority for the wave: User-approved design plan (this conversation,
2026-05-28) + binding product decisions (`?technical=1` gating; mint
button removal from operator surface; responsive degradation fix).

## Files changed

```
 gateway/app/routers/tasks.py                          | 24 ++++++++--
 gateway/app/templates/matrix_script_new.html          | 80 ++++++++++++++++-----------
 .../tests/test_matrix_script_new_page_redesign_2026_05_28.py | 113 ++++++++++++++++++++++++++++++++++++----
 3 files changed, 178 insertions(+), 39 deletions(-)
```

### gateway/app/routers/tasks.py
Added `technical_mode = request.query_params.get("technical") == "1"` to the
GET handler and threaded it into the template context. Operator default:
`technical_mode = False`. Architect query: `?technical=1` → `True`.
**No** change to the POST handler; the `source_script_ref` form field
contract is bytewise unchanged.

### gateway/app/templates/matrix_script_new.html
- Wrapped the architect-only `<details data-role="ms-new-technical-ref">`
  (and its source_script_ref text input + mint button) in
  `{% if technical_mode %}` ... `{% else %}` ... `{% endif %}`.
- In the `{% else %}` operator branch: render a single
  `<input type="hidden" name="source_script_ref" id="source_script_ref"
   data-role="ms-new-source-script-ref">` so the JS ingest pipeline still
  populates it before form submit and the server contract is intact.
- Renamed the technical-ref summary from "高级：..." to
  "架构师 / 工程师：手动指定不透明脚本句柄（技术引用）" to make the
  architect-only nature explicit when revealed.
- Added `open` attribute to the technical-ref `<details>` when
  `technical_mode=True` so architects don't need an extra click.
- Trimmed the paste-tab textarea placeholder from a 4-line essay to a
  single short prompt ("将脚本正文粘贴到这里..."); the volatility +
  no-vendor-leak disclosure stays in the helper paragraph below the
  textarea.
- Added a `@media (max-width: 880px)` block that:
  - Stacks the page-head row vertically so the matrix-script pill drops
    BELOW the title (was floating above per Visual Validation issue #5).
  - Left-aligns the pill (`align-self: flex-start; margin-top: 4px`).
  - Shrinks the page-head title to 20px on narrow viewport.
  - Lets the source-tabs row wrap (`flex-wrap: wrap`).

### gateway/app/services/tests/test_matrix_script_new_page_redesign_2026_05_28.py
- Updated three existing source-only tests to reflect the renamed
  literal and the new `{% if technical_mode %}` gating
  (`test_technical_ref_inside_technical_mode_gate`,
  `test_source_script_ref_input_preserved_for_form_post`,
  `test_mint_empty_button_only_inside_technical_mode_branch`).
- Added 6 new PR-1 tests:
  - `test_operator_mode_renders_hidden_source_script_ref_input_only`
  - `test_technical_mode_query_param_is_consumed_server_side`
  - `test_paste_textarea_placeholder_is_short_operator_language`
  - `test_responsive_degradation_media_query_for_narrow_viewport`
  - `test_no_opaque_handle_vocabulary_visible_in_operator_mode_branch`
  - `test_route_handler_signature_change_documented_in_template_comment`

## Scope boundary

**Inside PR-1**:
- `gateway/app/routers/tasks.py` GET handler for `MATRIX_SCRIPT_CREATE_ROUTE` only.
- `gateway/app/templates/matrix_script_new.html` only.
- Tests for the above only.

**Outside PR-1 (deferred to PR-2A..D / PR-3 / PR-4)**:
- Workbench changes (PR-2A..2D).
- Delivery Center changes (PR-3).
- Cross-page IA + new presenter helpers (PR-2A: `main_video_result_view.py`).
- Full visual validation report (PR-4).

**Bytewise unchanged** (verified via `git diff --name-only` audit):
- All `gateway/app/services/hot_follow*`
- All `gateway/app/services/digital_anchor/*`
- All `gateway/app/services/asset/*`
- All `docs/contracts/`
- All closed-enum modules (`publish_feedback_closure.py`,
  `EVENT_KINDS`, `REVIEW_ZONE_VALUES`, `RECORD_KINDS`, etc.)
- All `schemas/`
- The POST `/tasks/matrix-script/new` handler (only the GET handler changed).
- The mint service (`source_script_ref_minting.py`) and its endpoint.
- The body store + ingest endpoint.

## Screenshots

Captured at 2026-05-28 from a running `uvicorn gateway.app.main:app`
gateway on pyenv Python 3.13.5 + `AUTH_MODE=off` +
`WORKSPACE_ROOT=.local_workspace`. Real browser renders via the Claude
Preview MCP; inline images are in the implementation transcript above.
HTML snapshots saved here for diff parity:

| # | Capture | Viewport | URL | HTML on disk | Verification |
|---|---|---|---|---|---|
| 1 | Operator-mode default (no `?technical`) | 1280×800 | `/tasks/matrix-script/new` | [`01_operator_mode_default_1280x800.html`](01_operator_mode_default_1280x800.html) | `ms-new-technical-ref` = absent, `ms-new-mint-button` = absent, `source_script_ref` input `type=hidden` ✓ |
| 2 | Architect technical-mode | 1280×800 | `/tasks/matrix-script/new?technical=1` | [`02_technical_mode_query_1280x800.html`](02_technical_mode_query_1280x800.html) | `ms-new-technical-ref` = present + `open`, `ms-new-mint-button` = present, `source_script_ref` input `type=text` ✓ |
| 3 | Operator-mode narrow viewport | 820×800 | `/tasks/matrix-script/new` | [`03_operator_mode_narrow_820x800.html`](03_operator_mode_narrow_820x800.html) | Matrix-script pill stacks BELOW title (was floating above pre-PR-1); tabs wrap if needed; single-column form layout ✓ |

DOM probes (run via `preview_eval` against each render) confirm the
gating works at runtime, not just in the template source:

```js
// Screenshot 1 (operator mode)
[!!document.querySelector('[data-role="ms-new-technical-ref"]'),    // false
 !!document.querySelector('[data-role="ms-new-mint-button"]'),       // false
 document.querySelector('input[name="source_script_ref"]')?.type]    // "hidden"

// Screenshot 2 (technical mode)
[!!document.querySelector('[data-role="ms-new-technical-ref"]'),    // true
 !!document.querySelector('[data-role="ms-new-mint-button"]'),       // true
 document.querySelector('input[name="source_script_ref"]')?.type,    // "text"
 document.querySelector('[data-role="ms-new-technical-ref"]')?.open] // true
```

## Tests

```
$ python3 -m pytest gateway/app/services/tests/test_matrix_script_new_page_redesign_2026_05_28.py -v
============================= 26 passed in 0.08s ==============================
```

All 26 tests pass: 17 carried over from the prior wave (still asserting
operator-language copy, mission subtitle, paste tab default, ingest /
mint endpoint references, JS submit pipeline, etc.) + 3 updated to
match the renamed literal & new gating + 6 new PR-1 acceptance tests
(operator-mode hidden-input only; technical-mode query param consumed;
short placeholder; responsive media query; no-opaque-handle vocabulary
in operator branch; route-handler comment preserved).

No regressions in the broader collectable matrix_script suite
(`1005 passed, 1 failed pre-existing, 17 skipped` — same as the
PR-0 baseline; the single failure
`test_block_d_resolved_subfield_has_status_resolved_when_caption_present`
is pre-existing on `main` per the earlier visual-validation pass and is
unrelated to PR-1).

## Explicit no-change statement

This PR does **NOT**:
- Touch any contract under `docs/contracts/`.
- Touch any packet shape, closed enum, or `kind_label_zh` value.
- Modify the POST `/tasks/matrix-script/new` handler.
- Modify the ingest, peek, or mint endpoints or their services.
- Modify any Hot Follow file.
- Modify any Digital Anchor file.
- Modify any Asset Supply file.
- Add, expose, or hide any provider / model / vendor / engine selector.
- Fake any final_video, publish_url, or media reference.
- Add any backend generation capability.

## Remaining backend limitations (unchanged from PR-0 baseline)

- No variant generation backend; the Phase B authoring step still runs
  a deterministic seed at task creation only.
- No `final_video` worker; the Delivery Center continues to render
  honest absence for all variants.
- Body store remains volatile (in-process, lost on gateway restart).
- Closure store remains volatile.
- The architect `?technical=1` surface preserves the §8.F / §8.H
  opaque-ref discipline; external URL / bucket schemes still rejected
  at HTTP 400 by the existing `_validate_source_script_ref_shape` guard.

## Forbidden vocabulary audit on operator surface (PR-1 acceptance)

Source grep against the rendered operator-mode HTML (Screenshot 1
`01_operator_mode_default_1280x800.html`):

- `content://` outside the JS placeholder strings: **absent**.
- `task://` / `asset://` / `ref://`: **absent** from operator surface.
- "铸造空句柄" / mint button: **absent** from operator surface.
- "高级：手动指定不透明脚本句柄（技术引用）": **absent** (technical-ref
  gated behind `{% if technical_mode %}`).
- `publish_readiness` / `head_reason` / `final_video` / `RC-R8` /
  `artifact_lookup`: **absent** from this page (these belong to
  Workbench, addressed in PR-2D).
- `vendor` / `model` / `provider` / `engine` as selectors: **absent**
  (validator R3 preserved).

## Verdict

**PR-1 ready to merge.**

The New Task page operator boundary is clean: operators see paste /
upload / select tabs, the system-minted opaque handle is invisible to
them, and the architect technical path is still available via
`?technical=1` for debugging or scripted flows. Responsive degradation
at narrow viewport is improved (matrix-script pill now stacks below
the title instead of floating above).

**This wave does NOT claim Matrix Script becomes production-operable.**
The redesign continues to make the UI honestly verifiable. Generation
backend, durable persistence, and real publish remain gated to
Platform Runtime Assembly + Capability Expansion Waves and are
explicitly out of scope for PR-1 through PR-4.

**Next step**: PR-2A (Workbench main video result block) authoring,
which opens only after this PR merges.
