# Matrix Script §8.E Workbench Shell Suppression — Execution Log v1

Date: 2026-05-03
Wave: ApolloVeo 2.0 Operator-Visible Surface Validation Wave (Plan A trial
correction set, follow-up blocker review v1, item §8.E)
Status: implementation green; ready for signoff
Authority:
- [docs/reviews/matrix_script_followup_blocker_review_v1.md](../reviews/matrix_script_followup_blocker_review_v1.md) §5 (§8.E — Workbench Shell Suppression), §8 (Recommended Ordering — §8.E lands second after §8.G), §9 (Gate Recommendation — §8.E READY)
- [docs/contracts/workbench_panel_dispatch_contract_v1.md](../contracts/workbench_panel_dispatch_contract_v1.md) (with §"Shared shell neutrality (addendum, 2026-05-03)" landed in this change)
- [docs/contracts/matrix_script/workbench_variation_surface_contract_v1.md](../contracts/matrix_script/workbench_variation_surface_contract_v1.md) (frozen Phase B projection contract — unchanged)
- [docs/execution/MATRIX_SCRIPT_G_RENDER_CORRECTNESS_EXECUTION_LOG_v1.md](MATRIX_SCRIPT_G_RENDER_CORRECTNESS_EXECUTION_LOG_v1.md) (§8.G — landed; render correctness fix, complementary to §8.E shell suppression)
- [docs/execution/MATRIX_SCRIPT_C_PHASE_B_AUTHORING_EXECUTION_LOG_v1.md](MATRIX_SCRIPT_C_PHASE_B_AUTHORING_EXECUTION_LOG_v1.md) (§8.C — landed)
- [docs/execution/MATRIX_SCRIPT_B_DISPATCH_CONFIRMATION_EXECUTION_LOG_v1.md](MATRIX_SCRIPT_B_DISPATCH_CONFIRMATION_EXECUTION_LOG_v1.md) (§8.B — confirmed)
- [docs/execution/MATRIX_SCRIPT_A_REF_SHAPE_GUARD_EXECUTION_LOG_v1.md](MATRIX_SCRIPT_A_REF_SHAPE_GUARD_EXECUTION_LOG_v1.md) (§8.A — landed)
- [docs/execution/MATRIX_SCRIPT_D_OPERATOR_BRIEF_CORRECTION_EXECUTION_LOG_v1.md](MATRIX_SCRIPT_D_OPERATOR_BRIEF_CORRECTION_EXECUTION_LOG_v1.md) (§8.D — landed)
- [ENGINEERING_RULES.md](../../ENGINEERING_RULES.md) §6 Contract-First, §10 Validation, §11 Scope Control
- [CURRENT_ENGINEERING_FOCUS.md](../../CURRENT_ENGINEERING_FOCUS.md)

## 1. Reading Declaration

There is **no top-level `CLAUDE.md`** in this repository. Per the standing
execution discipline carried in
[ENGINEERING_RULES.md](../../ENGINEERING_RULES.md),
[CURRENT_ENGINEERING_FOCUS.md](../../CURRENT_ENGINEERING_FOCUS.md),
[ENGINEERING_STATUS.md](../../ENGINEERING_STATUS.md),
[ENGINEERING_CONSTRAINTS_INDEX.md](../../ENGINEERING_CONSTRAINTS_INDEX.md),
[PROJECT_RULES.md](../../PROJECT_RULES.md), and
[docs/ENGINEERING_INDEX.md](../ENGINEERING_INDEX.md), the equivalent
authority chain followed for this work is:

- engineering rules / current focus / status / constraints index;
- docs index;
- the follow-up blocker review v1 (the active authority for §8.E /
  §8.F / §8.G);
- the prior trial blocker review and the §8.A / §8.B / §8.C / §8.D /
  §8.G execution logs (so §8.E builds on the contract-clean fresh-sample
  pipeline established by §8.A / §8.B / §8.C / §8.D and the render
  correctness fix landed by §8.G);
- the workbench panel dispatch contract (the contract being amended
  with the shared-shell-neutrality addendum) and the matrix_script
  workbench variation surface contract (unchanged);
- read-only inspection of
  [gateway/app/services/workbench_registry.py](../../gateway/app/services/workbench_registry.py)
  (template-selection map: `default`/`apollo_avatar`/`hot_follow` are
  the registered kinds; `default` and `matrix_script` both resolve to
  `task_workbench.html`),
  [gateway/app/templates/_topbar.html](../../gateway/app/templates/_topbar.html)
  +
  [gateway/app/templates/_lang_tabs.html](../../gateway/app/templates/_lang_tabs.html)
  (where the global `window.__I18N__` payload is inlined; informs the
  test-scope decision about stripping `<script>` blocks before
  asserting),
  [gateway/app/templates/hot_follow_workbench.html](../../gateway/app/templates/hot_follow_workbench.html)
  (the per-line Hot Follow template — unaffected by this change).

No top-level `CLAUDE.md` update is needed. The standing instruction lives
in `ENGINEERING_RULES.md` / `CURRENT_ENGINEERING_FOCUS.md`; both have
been updated by this work.

## 2. Scope (binding)

This change implements **only** §8.E from the Matrix Script follow-up
blocker review v1: a pure shell-suppression execution step that
prevents the shared workbench template (`task_workbench.html`) from
rendering Hot Follow stage cards / pipeline summary / dub-engine
selectors / Burmese-specific deliverable rows / subtitle-track meta
row / publish-hub CTA / debug-logs panel / Hot Follow JS state machine
when `task.kind != "hot_follow"`.

Items §8.A (entry-form ref-shape guard — landed), §8.B (panel-dispatch
confirmation — confirmed), §8.C (Phase B deterministic authoring —
landed), §8.D (operator brief correction — landed), and §8.G (Phase B
panel render correctness — landed) are out of scope and remain as
already accepted. Item §8.F (opaque-ref discipline) is out of scope;
the review §9 ordering puts §8.F third and it remains a follow-up.

This is a **pure shell-suppression execution step**. It does not
re-check panel readability (covered by §8.G). It does not redesign the
workbench. The shared-shell-plus-panel-mount architecture from
[`workbench_panel_dispatch_contract_v1`](../contracts/workbench_panel_dispatch_contract_v1.md)
is preserved.

### 2.1 What this change adds

- A whitelist gating predicate `{% if task.kind == "hot_follow" %}`
  applied to four contiguous Hot Follow-only template regions in
  [gateway/app/templates/task_workbench.html](../../gateway/app/templates/task_workbench.html):
  1. **Header subtitle-track meta row + pipeline meta row** (the
     `字幕轨道` row + the `字幕: whisper+gemini · 配音: auto-fallback`
     pipeline summary). The `{% set pipeline = ... %}` block is left
     ungated so it runs harmlessly on every kind, but the visible
     meta-items render only on Hot Follow.
  2. **Deliverables panel + Scenes section panel** (the `{{
     t("workbench.deliverables") }}` block carrying `pack` / `scenes`
     / `video` / `mm_subtitles` / `mm_audio` cards, plus the
     `{{ t("workbench.scenes_section") }}` panel with the
     `btn-scenes` CTA).
  3. **Publish hub panel + Steps panel + Debug logs panel** (the
     `{{ t("workbench.publish_hub") }}` CTA, the `{{ t("workbench.steps") }}`
     stage cards `parse` / `dub` / `pack` / `subtitles` with the
     dub-engine + Burmese voice selectors + the subtitle compare /
     edit details, and the `<details id="debug-panel">` engineering
     env-summary section).
  4. **The inline Hot Follow JS state machine** (the entire `<script>`
     block at template lines 712-1474 — the one that wires Hot Follow
     downloads, parse status, subtitle compare, dub triggers, and
     `mm_edited` save — only the i18n bundle `<script src="/static/js/i18n_v185.js"></script>`
     is left ungated because it is the global translation runtime,
     not a Hot Follow control).
- A **non-edit** for the existing Hot Follow operator panel block
  (`{% if ops_hot_follow_panel.mounted %}` at template lines 449-477):
  this block already self-gates on a packet-driven flag and is set by
  the operator-visible-surfaces wiring only for Hot Follow tasks. No
  change is required there; it is mentioned only to document that it
  is correctly gated already.
- An additive contract clarification at
  [docs/contracts/workbench_panel_dispatch_contract_v1.md](../contracts/workbench_panel_dispatch_contract_v1.md)
  §"Shared shell neutrality (addendum, 2026-05-03)": the dispatch
  contract governs `(ref_id → panel_kind)` mounting; the shared shell
  is now declared line-neutral (line-specific stage controls render
  only inside the matched panel block). The addendum is **additive** —
  the closed dispatch map (six pairs), closed `panel_kind` enum,
  closed `ref_id` set, closed-by-default rule, resolver shape, and
  forbidden list are unchanged.
- A new regression test
  `test_matrix_script_workbench_does_not_render_hot_follow_shell_controls`
  in
  [gateway/app/services/tests/test_matrix_script_phase_b_authoring.py](../../gateway/app/services/tests/test_matrix_script_phase_b_authoring.py)
  that POSTs a fresh contract-clean Matrix Script sample, GETs the
  workbench, strips `<script>` blocks (which inline the global
  `window.__I18N__` payload that necessarily contains Hot Follow
  i18n keys — those are not operator-visible controls), and asserts
  the visible HTML body **does not contain** the closed Hot Follow
  control token list drawn from the follow-up blocker review §5
  ("Required correction type") — pipeline tokens (`whisper+gemini`,
  `auto-fallback`), stage DOM ids (`btn-parse`, `btn-dub`, `btn-pack`,
  `btn-subtitles`, `btn-scenes`, `hard-subtitles-toggle`, `voice-id`,
  `dub-provider`, `parse-status`, `dub-status`, `pack-status`,
  `subs-status`, `audio-preview`, `debug-panel`), Burmese deliverable
  filenames (`mm.srt`, `mm.txt`, `origin.srt`, `mm_audio`,
  `/v1/tasks/`), and i18n labels for the Hot Follow stage / deliverable
  / publish / debug sections. The test also asserts as a positive
  anchor that the matrix_script panel is still mounted
  (`data-role="matrix-script-variation-panel"` and
  `data-panel-kind="matrix_script"`) so the negative assertions cannot
  pass on an empty render.
- This execution log.
- Standing repo guidance writeback to `ENGINEERING_STATUS.md`,
  `CURRENT_ENGINEERING_FOCUS.md`, the Matrix Script first-production-line
  log, and the ApolloVeo 2.0 evidence index.

### 2.2 What this change does NOT add (out of §8.E)

- no change to `workbench_registry.py` — the `default → task_workbench.html`
  mapping is unchanged (the Caveat from review §5 is observed: the
  `default` entry remains, the gating predicate handles the actual
  suppression);
- no per-line workbench template files for `matrix_script` /
  `digital_anchor` — per
  [`workbench_panel_dispatch_contract_v1`](../contracts/workbench_panel_dispatch_contract_v1.md)
  the per-panel mount inside a shared shell is the correct design;
- no capability flags (`shell_capabilities.has_dub_flow`,
  `shell_capabilities.has_publish_hub`, etc.) — the whitelist form
  `kind == "hot_follow"` is the simpler, lower-risk implementation
  approved by the follow-up review §5 ("The whitelist form is simpler
  and lower-risk for this wave");
- no change to `hot_follow_workbench.html` — Hot Follow tasks resolve
  to `hot_follow_workbench.html` via the registry, never reaching the
  shared `task_workbench.html`; Hot Follow's per-line workbench is
  unaffected;
- no change to `task_workbench_apollo_avatar.html` — Apollo Avatar
  tasks resolve to their per-line template via the registry;
- no §8.F scheme tightening — `https`/`http` remain in the §8.A
  accepted-scheme set; opaque-ref discipline tightening is scoped to
  §8.F follow-up;
- no §8.D operator brief re-correction — §8.H is the natural successor
  once §8.E / §8.F / §8.G all land;
- no Phase B planner change — `phase_b_authoring.py` is consumed
  read-only;
- no projector change — `workbench_variation_surface.py` is consumed
  read-only;
- no router change — `tasks.py` is not touched;
- no schema / sample / packet re-version;
- no `PANEL_REF_DISPATCH` widening; no §8.B dispatch logic change;
- no §8.G axes-table change — the Jinja item-access fix lives inside
  the matrix_script panel block at template lines 295-303 and is
  unaffected by §8.E gating;
- no provider / model / vendor / engine controls;
- no Hot Follow / Digital Anchor scope reopening;
- no Runtime Assembly / Capability Expansion entry;
- no second production line onboarding;
- no Asset Library / promote (Plan C C1–C3) work;
- no Plan E gated items (B4, D1, D2, D3, D4) implementation;
- no CSS-only suppression (review §9 hard red line: "do not patch the
  workbench UI to fake suppression by CSS — suppression must be in the
  template render path so tests can assert it"); the suppression is
  in the Jinja render path, asserted by the new regression test;
- no audit of the `task_workbench.html` Hot Follow regions for further
  cleanup (the review explicitly bounds this to the whitelist gate;
  any future capability-flag refactor is out of wave).

## 3. Code / Docs Changes

| Change | File | Kind |
| ------ | ---- | ---- |
| Whitelist `{% if task.kind == "hot_follow" %}` gates around four contiguous Hot Follow-only template regions: (1) subtitle-track meta row + pipeline meta-item; (2) Deliverables panel + Scenes section panel; (3) Publish hub + Steps + Debug logs panels; (4) inline Hot Follow JS state machine. The shared `{% set pipeline = ... %}` declarations are kept ungated so any future generic readers do not crash; the visible meta-items render only on Hot Follow. The `<script src="/static/js/i18n_v185.js"></script>` (i18n runtime) is left ungated as a global runtime, not a Hot Follow control. | [gateway/app/templates/task_workbench.html](../../gateway/app/templates/task_workbench.html) | EDIT |
| New §"Shared shell neutrality (addendum, 2026-05-03)" appended to `workbench_panel_dispatch_contract_v1`: declares that the shared workbench shell is line-neutral; line-specific stage controls render only inside the matched panel block; the rule is asserted at `gateway/app/templates/task_workbench.html` via the `{% if task.kind == "hot_follow" %}` whitelist gate; per-line templates (`hot_follow_workbench.html`, `task_workbench_apollo_avatar.html`) are unaffected; no per-line workbench templates introduced for new lines; capability flags deferred. The addendum is additive — the closed dispatch map, closed `panel_kind` enum, closed `ref_id` set, closed-by-default rule, resolver shape, and forbidden list are unchanged. | [docs/contracts/workbench_panel_dispatch_contract_v1.md](../contracts/workbench_panel_dispatch_contract_v1.md) | EDIT |
| New `test_matrix_script_workbench_does_not_render_hot_follow_shell_controls` end-to-end regression. POST a fresh contract-clean Matrix Script sample, GET the workbench, strip `<script>` blocks (so the inlined global `window.__I18N__` payload — necessarily containing Hot Follow i18n keys — does not mask the test of the visible HTML surface), and assert the closed Hot Follow control token list is absent in the visible HTML. Positive anchor: the matrix_script panel is still mounted. | [gateway/app/services/tests/test_matrix_script_phase_b_authoring.py](../../gateway/app/services/tests/test_matrix_script_phase_b_authoring.py) | EDIT |
| This execution log. | [docs/execution/MATRIX_SCRIPT_E_SHELL_SUPPRESSION_EXECUTION_LOG_v1.md](MATRIX_SCRIPT_E_SHELL_SUPPRESSION_EXECUTION_LOG_v1.md) | NEW |
| Standing repo guidance writeback. | [ENGINEERING_STATUS.md](../../ENGINEERING_STATUS.md), [CURRENT_ENGINEERING_FOCUS.md](../../CURRENT_ENGINEERING_FOCUS.md), [docs/execution/MATRIX_SCRIPT_FIRST_PRODUCTION_LINE_LOG.md](MATRIX_SCRIPT_FIRST_PRODUCTION_LINE_LOG.md), [docs/execution/apolloveo_2_0_evidence_index_v1.md](apolloveo_2_0_evidence_index_v1.md) | EDIT |

**File-size budget.** `task_workbench.html` is a Jinja template, not a
Python module, so the ENGINEERING_RULES §1 file-size targets do not
apply. The edit is the addition of four `{% if task.kind ==
"hot_follow" %}` / `{% endif %}` gate pairs (eight new tokens) plus
the rearrangement of the `{% set pipeline = ... %}` block to live
above the gated meta-items. Net total: a few token additions; the
Hot Follow-only sections themselves are unchanged in shape (only their
visibility is gated). No router or service file edited; no god-file
growth; no new line-specific logic in `tasks.py`, `task_view.py`, or
`hot_follow_api.py`.

## 4. Validation Evidence

Interpreter: `~/.pyenv/versions/3.13.5/bin/python3` (Python 3.13.5),
matching the §8.A / §8.B / §8.C / §8.G execution logs.
Worktree path:
`/Users/tylerzhao/Code/apolloveo-auto/.claude/worktrees/unruffled-merkle-d9f22e`.
Branch: `claude/unruffled-merkle-d9f22e`. Baseline commit: `b0fad40`
(post-§8.G, the immediately prior accepted state). The old invalid
pre-§8.A sample is **not** used in any of the assertions below.

### 4.1 Targeted suite — §8.E shell suppression plus §8.G axes-table plus §8.C end-to-end render

```
~/.pyenv/versions/3.13.5/bin/python3 -m pytest \
  gateway/app/services/tests/test_matrix_script_phase_b_authoring.py -v
```

Result: **13 passed, 0 failed.** The 12 prior cases (11 §8.C
end-to-end + 1 §8.G axes-table) all stay green, plus the new §8.E
case `test_matrix_script_workbench_does_not_render_hot_follow_shell_controls`
passes (closed token list of 28 forbidden Hot Follow control tokens
asserted absent from the visible HTML; matrix_script panel mount
positively asserted).

### 4.2 Surrounding suites — no regression

```
~/.pyenv/versions/3.13.5/bin/python3 -m pytest \
  tests/contracts/matrix_script/test_phase_b_authoring_phase_c.py \
  gateway/app/services/tests/test_matrix_script_phase_b_authoring.py \
  gateway/app/services/tests/test_matrix_script_source_script_ref_shape.py \
  gateway/app/services/tests/test_matrix_script_workbench_dispatch.py \
  gateway/app/services/tests/test_new_tasks_surface.py \
  gateway/app/services/tests/test_task_router_presenters.py \
  tests/contracts/matrix_script/ \
  tests/contracts/operator_visible_surfaces/ \
  tests/guardrails/ -q
```

Result: **195 passed, 0 failed.** §8.A's 23, §8.B's 4, §8.C's
planner-unit 27 + end-to-end (now 13 = 11 prior + §8.G + §8.E),
`test_workbench_variation_phase_b`, the operator-visible-surface
contract suites, the wiring suite, and the guardrails all stay green.
The 194-case §8.G baseline becomes 195 here as a result of the new
§8.E case.

### 4.3 Hot Follow / workbench-specific sweep

```
~/.pyenv/versions/3.13.5/bin/python3 -m pytest \
  gateway/app/services/tests/ -q -k "workbench or hot_follow"
```

Result: **166 passed, 176 deselected, 0 failed.** Hot Follow's per-line
workbench tests (`hot_follow_workbench.html` is a separate template;
Hot Follow tasks never reach `task_workbench.html` in the live registry
flow) are unaffected. The Apollo Avatar workbench tests are also
unaffected (Apollo Avatar tasks resolve to
`task_workbench_apollo_avatar.html`).

### 4.4 Live render evidence (fresh sample, captured)

A direct end-to-end run against the live FastAPI app (in-memory repo,
fresh contract-clean sample, `task_id=2df7c79311a6`,
`variation_target_count=4`, `target_language=mm`,
`source_script_ref=content://matrix-script/source/8e-evidence-001`):

```
POST status: 303
GET status: 200

=== Visible HTML (with <script> blocks stripped) ===

--- PRESENT (matrix_script panel mount intact) ---
'data-role="matrix-script-variation-panel"' : True
'data-panel-kind="matrix_script"'           : True
'cell_001'                                  : True
'slot_001'                                  : True
'formal · casual · playful'                 : True   (§8.G axes table)
'b2b · b2c · internal'                      : True   (§8.G axes table)
'min=30 · max=120 · step=15'                : True   (§8.G axes table)

--- ABSENT (Hot Follow shell controls suppressed) ---
'whisper+gemini'              : False   pipeline summary
'auto-fallback'               : False   pipeline summary
'id="btn-parse"'              : False   stage card DOM
'id="btn-dub"'                : False   stage card DOM
'id="btn-pack"'               : False   stage card DOM
'id="btn-subtitles"'          : False   stage card DOM
'id="hard-subtitles-toggle"'  : False   subtitle controls
'id="voice-id"'               : False   dub voice picker
'id="audio-preview"'          : False   audio preview element
'id="debug-panel"'            : False   debug logs panel
'mm.srt'                      : False   Burmese deliverable
'mm_audio'                    : False   Burmese deliverable
'origin.srt'                  : False   Burmese deliverable
'/v1/tasks/'                  : False   Hot Follow API endpoints
'workbench.deliverables'      : False   i18n label
'workbench.scenes_section'    : False   i18n label
'workbench.publish_hub'       : False   i18n label
'workbench.steps'             : False   i18n label
'workbench.meta.subtitle_track': False  i18n label
'workbench.meta.pipeline'     : False   i18n label
'workbench.logs'              : False   i18n label
```

This is the load-bearing operator-visible evidence: a fresh
contract-clean Matrix Script sample now renders **only** the shared
header card, the operator surface strip, the line-specific panel slot,
and the Matrix Script Phase B variation panel (with §8.G's correctly
rendered axes table). The Hot Follow stage cards / pipeline summary /
Burmese deliverable strip / dub-engine selectors / publish-hub CTA /
debug-logs panel that the follow-up review §3 (defect #1, "shell
contamination") observed on `task_id=415ea379ebc6` are gone.

### 4.5 Manual proof of the four required §8.E validations

Mapping the §8.E "Required correction type" items from the follow-up
review §5 to evidence above:

| Required validation | Evidence |
| ------------------- | -------- |
| Shell defect: `task_workbench.html` learns to suppress Hot Follow stage cards / pipeline labels / dub engine controls / Burmese-specific deliverable rows when `kind != "hot_follow"`. | §3 code change (whitelist gates around four contiguous regions); §4.1 / §4.2 regression suite; §4.4 captured live evidence (all Hot Follow control tokens absent in visible HTML on a fresh matrix_script sample). |
| Equivalently: those sections must be wrapped in `{% if task.kind == "hot_follow" %}` (review §5). | §3 — exactly that predicate is used; the whitelist form is the simpler, lower-risk approach review §5 approved over capability flags. |
| The matrix_script branch (template lines 257-440) renders **without** the Hot Follow stage cards, deliverable strip, pipeline summary, and subtitle-track meta row. | §4.4 — `data-role="matrix-script-variation-panel"` is True; all listed Hot Follow tokens are False. |
| Regression test asserting that for `kind=matrix_script` the rendered HTML does **not** contain any of: `whisper+gemini`, `auto-fallback`, `mm_audio`, `mm.srt`, etc. | §3 — `test_matrix_script_workbench_does_not_render_hot_follow_shell_controls` asserts the closed token list including all those listed plus the stage DOM ids and the i18n labels for the Hot Follow sections. Scope note: the `<script>` blocks are stripped before assertion because the topbar inlines `window.__I18N__` (necessarily containing Hot Follow i18n keys) — those are JavaScript translation strings, not operator-visible controls. |
| Additive contract addendum on `workbench_panel_dispatch_contract_v1` declaring shell-shell neutrality. | §3 — `docs/contracts/workbench_panel_dispatch_contract_v1.md` §"Shared shell neutrality (addendum, 2026-05-03)". |
| Caveat: existing `task_workbench.html` is shared with `default`. | §3 — the gate predicate is `kind == "hot_follow"` (whitelist); on `default` and `matrix_script` the gated regions render nothing; on hypothetical future kinds that fall through to `default`, the gates still suppress correctly. |
| Caveat: `default` registry entry currently maps to `task_workbench.html`. | §3 — registry unchanged; the `default` template now renders as a stripped envelope (header card + operator surface strip + line-panel slot + matched panel block) on every non-Hot-Follow kind. Hot Follow's `hot_follow_workbench.html` template is unaffected. |
| Risk: existing `task_workbench.html` may be used by other lines in unexpected ways; regression sweep across `tests/contracts/operator_visible_surfaces/` and `gateway/app/services/tests/test_task_router_presenters.py` is prerequisite. | §4.2 regression sweep includes both — 195/195 cases pass. §4.3 also covers Hot Follow / workbench-specific tests — 166/166 pass. |

## 5. Contract Alignment Check

- `workbench_panel_dispatch_contract_v1`: respected, **additively
  amended**. The §"Shared shell neutrality (addendum, 2026-05-03)" is
  additive: the closed dispatch map (six pairs `(ref_id → panel_kind)`),
  the closed `panel_kind` enum `{hot_follow, matrix_script, digital_anchor}`,
  the closed `ref_id` set, the closed-by-default rule, the resolver
  shape, and the forbidden list (no new `panel_kind` / `ref_id` /
  vendor / state-shape, no multi-panel-kind dispatch, no cross-line
  panel sharing) all stand verbatim.
- `workbench_variation_surface_contract_v1`: respected, **unchanged**.
  The contract defines the matrix_script Phase B projection; the
  template gating is presentation-layer, not projection-layer. The
  matrix_script panel block (template lines 257-445) renders the
  projection unchanged.
- `task_entry_contract_v1`: respected, **unchanged**. The §8.A
  source-ref-shape addendum and the §8.C Phase B deterministic
  authoring addendum stand verbatim.
- `variation_matrix_contract_v1` / `slot_pack_contract_v1` / `packet_v1`:
  respected, **unchanged**. No new `status` / `ready` / `done` /
  `phase` / `current_attempt` / `delivery_ready` / `final_ready` /
  `publishable` field added at any scope. Validator R3 / R5 token sets
  unchanged.
- `tasks.py` did not receive new line-specific logic. The router still
  dispatches via the registry + the projection bundle. No router edit.
- No new vendor / model / provider / engine identifier was introduced.
- No second source of task or state truth was introduced. The
  template's gating is presentation-layer; the projector is a read-only
  projection of the packet; the packet remains the truth boundary.
- No CSS-only suppression — the review §9 hard red line "do not patch
  the workbench UI to fake suppression by CSS" is observed: the
  suppression is in the Jinja render path, asserted by the regression
  test.
- No silent change to `task_entry_contract_v1` semantics.
- No `PANEL_REF_DISPATCH` widening.

## 6. Final Gate

- **§8.E: PASS.** Whitelist gating predicate `{% if task.kind ==
  "hot_follow" %}` lands at template-level only; the shared workbench
  shell now suppresses Hot Follow stage cards, pipeline summary,
  Burmese deliverable strip, dub-engine selectors, subtitle-track meta
  row, publish-hub CTA, debug-logs panel, and Hot Follow JS state
  machine on `kind != "hot_follow"`; the matrix_script Phase B
  variation panel still mounts (and its §8.G-corrected axes table
  still renders); the workbench shell architecture is preserved
  (shared shell + per-panel mount).
- **Hot Follow controls suppressed on matrix_script: YES.** All 28
  forbidden tokens (pipeline summary + stage DOM ids + Burmese
  deliverable filenames + Hot Follow i18n labels) absent in the visible
  HTML on a fresh contract-clean matrix_script sample (per §4.4
  captured render evidence and §4.1 regression test).
- **Matrix Script panel mount preserved: YES.** `data-role="matrix-script-variation-panel"`
  and `data-panel-kind="matrix_script"` still present; §8.G axes table
  still renders `formal · casual · playful` / `b2b · b2c · internal` /
  `min=30 · max=120 · step=15`.
- **Hot Follow per-line workbench unaffected: YES.** Hot Follow's
  registry entry still resolves to `hot_follow_workbench.html` (a
  separate template); the §8.E gate has no observable effect on Hot
  Follow tasks.
- **Apollo Avatar per-line workbench unaffected: YES.** Apollo Avatar's
  registry entry still resolves to `task_workbench_apollo_avatar.html`.
- **Ready for §8.F: YES.** §8.E lands the shell suppression so the
  next item — §8.F opaque-ref scheme tightening — can proceed against
  a clean shell. §8.F remains BLOCKED on the explicit Options F1 / F2
  / F3 authority decision per the follow-up review §9; the §8.F
  recommendation is F1 (tighten + brief update).
- **Old invalid sample reusable: NO** (per follow-up review §1, §4.3,
  and §9; reaffirmed — no §8.E assertion uses the prior sample;
  evidence in §4.4 is on a fresh post-§8.A / §8.B / §8.C / §8.D / §8.G
  sample).
- **§8.A / §8.B / §8.C / §8.D / §8.G: not retracted.** §8.A guard,
  §8.B dispatch resolver, §8.C deterministic planner, §8.D operator
  brief, and §8.G render correctness fix all stand verbatim. §8.E is
  additive only.

## 7. Hard Red Lines (re-stated, observed)

This work observes every red line restated by the follow-up blocker
review §9 and the prior wave authority:

- Panel readability re-check: not done. §8.G is the binding correction
  for render readability; §8.E is shell-suppression only.
- Workbench redesign: no.
- Per-line workbench template files for matrix_script / digital_anchor:
  not added — per `workbench_panel_dispatch_contract_v1` the per-panel
  mount inside a shared shell is the correct design.
- CSS-only suppression: not used. Suppression is in the Jinja render
  path, asserted by tests.
- §8.A / §8.B / §8.C / §8.D / §8.G: not reopened.
- Hot Follow scope: not reopened. Hot Follow's
  `hot_follow_workbench.html` template is unaffected.
- Source-script-ref scheme policy: not touched. The §8.A
  accepted-scheme tuple and the §8.A contract addendum stand verbatim.
  §8.F is the binding correction for that defect; not landed here.
- `task_entry_contract_v1` semantics: not changed.
- Capability Expansion (asset-library / content-mint / new operator
  service): not entered.
- Platform Runtime Assembly: not entered.
- Provider / model / vendor / engine controls: not introduced.
- Workbench UI: not patched to fake suppression — the suppression is
  in the render path, the gated regions are not present in the visible
  HTML on `kind != "hot_follow"`.
- Delivery Center for Matrix Script: still inspect-only; not touched.
- Phase D publish-feedback closure: still contract-only; no write-back
  code added.
- State-shape fields (`delivery_ready`, `publishable`, `final_ready`,
  …): not added to any surface.
- Second production line: not onboarded; Digital Anchor implementation
  remains gated to Plan E.
- `tasks.py` / `task_view.py` / `hot_follow_api.py`: untouched.
- Old invalid sample: not used as evidence.
- Asset Library / promote (Plan C C1–C3): not entered.
- Plan E gated items (B4 `result_packet_binding`, D1 `publish_readiness`,
  D2 `final_provenance`, D3 panel-dispatch-as-contract-object,
  D4 advisory producer): not implemented.
- Promote Delivery Center beyond inspect-only for Matrix Script in
  this wave: not done.

End of v1.
