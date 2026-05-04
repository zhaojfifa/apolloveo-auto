# Plan E — Matrix Script UI Alignment PR-U1 (Task Area Comprehension) — Execution Log v1

Date: 2026-05-04
Branch: `claude/ui-u1-task-area-comprehension`
Base commit at audit: `d253553` (`Merge pull request #104 from zhaojfifa/claude/priceless-bell-8d28d9` — the docs-only signoff PR for the comprehension-phase gate spec)
Status: Implementation landed; per gate spec §6 row UA1-A.

Authority of execution:
- [docs/reviews/plan_e_matrix_script_operator_comprehensible_ui_alignment_gate_spec_v1.md](../reviews/plan_e_matrix_script_operator_comprehensible_ui_alignment_gate_spec_v1.md) §3 (allowed scope), §4 (forbidden scope), §5 (PR slicing), §7 (preserved freezes), §10 (gate-opening signoff completed 2026-05-04).
- User-mandated narrowing: gate spec §5 PR-UA1 → PR-UA6 collapsed to PR-U1 (Task Area) → PR-U2 (Workbench) → PR-U3 (Delivery Center). PR-U1 covers the Task Area surface, applying the operator-language tri-state badge (UA.5 spirit) and explicit workbench/delivery action zoning (UA.6 spirit) to a fourth Matrix Script-scoped surface (`tasks.html`) not enumerated in gate spec §3 file fences.

The Task Area scope was authorized by the user in the Step-3 mission text and is presentation-only over existing row truth; no contract / projection / packet / Hot Follow / Digital Anchor mutation. Hot Follow and Digital Anchor cards remain bytewise unchanged via a `{% if line_id == "matrix_script" %}` gate around the new block.

---

## 1. Scope landed

| # | Surface | Operator-visible delta |
| --- | --- | --- |
| 1 | Task Area card (`gateway/app/templates/tasks.html`) — Matrix Script rows only | Operator-language `主题` field + the existing title; new field row `当前变体数：{count} · 可发布版本数：— · 当前阻塞项：{operator-language label}`; tri-state badge re-rendered as `阻塞中 / 就绪 / 可发布` (English `blocked` / `ready` / `publishable` retained as `data-bucket` for the existing filter logic); two explicit action buttons `进入工作台` (primary) and `跳交付中心` (secondary) replacing the generic `查看详情`. |
| 2 | Hot Follow rows on `tasks.html` | **Bytewise unchanged** — `{% else %}` branch renders the prior block verbatim. |
| 3 | Digital Anchor rows on `tasks.html` | **Bytewise unchanged** — same `{% else %}` branch. |
| 4 | Baseline / Apollo Avatar rows | **Bytewise unchanged** — same `{% else %}` branch. |

## 2. Files added

- [gateway/app/services/matrix_script/task_card_summary.py](../../gateway/app/services/matrix_script/task_card_summary.py) — new pure-projection helper `derive_matrix_script_task_card_summary(row)`. Reads `row["title"]`, `row["board_bucket"]`, `row["head_reason"]`, `row["line_specific_refs"]` (or `row["packet"]["line_specific_refs"]`), `row["config"]["next_surfaces"]`. Emits the four operator-language card fields, the tri-state badge label, the publishable-count gating sentinel, and the two action hrefs. Returns `{}` for non-Matrix-Script rows.
- [gateway/app/services/tests/test_matrix_script_task_card_summary.py](../../gateway/app/services/tests/test_matrix_script_task_card_summary.py) — 30 import-light test cases covering: tri-state badge per bucket; subject / variation count fields; publishable-count gating sentinel; closed-set blocker code translation; unknown-blocker fallthrough; action href reading from `next_surfaces` and fallbacks; non-Matrix-Script empty summary; alias kind recognition; validator R3 alignment (no vendor / model / provider / engine identifier in the return value); helper-does-not-mutate-input invariant.

## 3. Files modified (Matrix Script-scoped only)

- [gateway/app/services/task_router_presenters.py](../../gateway/app/services/task_router_presenters.py) — three additions: (a) one new import line for `derive_matrix_script_task_card_summary`; (b) a `kind_value == "matrix_script"`-gated block at the end of the per-row loop in `build_tasks_page_rows` that copies `kind` / `line_specific_refs` / `config` from the source DB task `t` onto `row` and attaches `row["matrix_script_card_summary"]`. No Hot Follow code path touched. The Hot Follow `_bind_hot_follow_projection` block above stays verbatim.
- [gateway/app/templates/tasks.html](../../gateway/app/templates/tasks.html) — wrapped the per-card body inside the `for it in items` loop with `{% if line_id == "matrix_script" and ms_summary.is_matrix_script %}` (new operator-language block) and `{% else %}` (the prior rendering, verbatim). Outer `<div class="task-card task-row" data-line=... data-status=... data-bucket=...>` and the closing `</div>` stay verbatim so the existing `applyFilters()` JS still drives `display: none` per `data-line` / `data-status` / `data-bucket`.

## 4. Files NOT touched (binding under gate spec §4)

- Any Hot Follow file under `gateway/app/services/hot_follow_*`, `gateway/app/templates/hot_follow_*`, `gateway/app/routers/hot_follow_*`, `tasks.py` Hot Follow paths — gate spec §4.1 preserved.
- Any Digital Anchor file under `gateway/app/services/digital_anchor/*`, `gateway/app/templates/digital_anchor*`, the formal `/tasks/digital-anchor/new` route, the temp `/tasks/connect/digital_anchor/new` route — gate spec §4.2 preserved.
- Any contract file under `docs/contracts/` — gate spec §4.8 preserved.
- Any schema file under `schemas/` — same.
- The cross-line `gateway/app/services/operator_visible_surfaces/projections.py` `derive_board_publishable` / `derive_delivery_publish_gate` / `derive_workbench_panel_dispatch` paths — the new helper consumes `head_reason` and `board_bucket` already produced by these projections; no projection mutation. Gate spec §4.7 (no D1 unified `publish_readiness` producer) preserved — `publishable_variation_count` is intentionally `None` with an operator-language tooltip explaining the gating.
- `gateway/app/services/operator_visible_surfaces/advisory_emitter.py` (does not exist; this PR does not create it) — gate spec §4.7 preserved.
- `gateway/app/services/matrix_script/create_entry.py`, `phase_b_authoring.py`, `delivery_binding.py`, `source_script_ref_minting.py`, `workbench_variation_surface.py`, `publish_feedback_closure.py` — Matrix Script truth shapes from PR-1 / PR-2 / PR-3 unchanged. Gate spec §4.3 (Matrix Script truth / scope creep) preserved.
- `gateway/app/templates/matrix_script_new.html` — UA.1 (entry-surface comprehension) deferred to PR-U1's narrower Task Area focus per the user-mandated three-PR slicing; the matrix_script_new form stays untouched in this PR.
- `gateway/app/templates/task_workbench.html` — Workbench comprehension is owned by PR-U2; not touched.
- The Matrix Script Delivery Center surface — owned by PR-U3; not touched.
- [docs/execution/PLAN_E_MATRIX_SCRIPT_PHASE_CLOSEOUT_v1.md](PLAN_E_MATRIX_SCRIPT_PHASE_CLOSEOUT_v1.md) §3 first-phase A7 closeout signoff block — gate spec §4.10 + §7.6 preserved; A7 paperwork remains intentionally pending and is **NOT** advanced by this PR.

## 5. Validation

- `python3 -m pytest gateway/app/services/tests/test_matrix_script_task_card_summary.py -v` → **30/30 PASS** on local Python 3.9.6.
- Jinja parse check on the modified template → **OK** (no template syntax error).
- Direct module import `from gateway.app.services.matrix_script.task_card_summary import derive_matrix_script_task_card_summary` → **OK**.
- Broader presenter-level smoke import (`from gateway.app.services.task_router_presenters import build_tasks_page_rows`) blocks at collection on local Python 3.9 due to the pre-existing PEP-604 `str | None` syntax in [gateway/app/config.py:43](../../gateway/app/config.py) that requires Python 3.10+ — verified pre-existing across PR-1 / PR-2 / PR-3 execution logs (per `ENGINEERING_RULES.md §10` "distinguish code regressions from environment limitations"); CI on Python 3.10+ runs the full chain. NOT caused by PR-U1.
- Hot Follow file isolation: `git diff --name-only` shows zero Hot Follow files touched.
- Digital Anchor file isolation: `git diff --name-only` shows zero Digital Anchor files touched.

## 6. Hot Follow + Digital Anchor preservation

- Per the `{% if line_id == "matrix_script" %} ... {% else %} ...prior verbatim... {% endif %}` gate in `tasks.html`, Hot Follow and Digital Anchor cards render through the unchanged `{% else %}` branch — bytewise identical to pre-PR rendering.
- The presenter's Matrix Script-only block in `build_tasks_page_rows` is gated on `kind_value == "matrix_script"`; Hot Follow rows continue to flow through `_bind_hot_follow_projection`; Digital Anchor rows are unaffected.
- The cross-line `applyFilters()` JS inside `tasks.html` still drives the existing scene / status / bucket tab filtering on `data-line` / `data-status` / `data-bucket` attributes which remain on the outer `<div>` for every card kind.

## 7. Acceptance evidence (gate spec §6 row UA1-A spirit, narrowed to Task Area)

| # | Acceptance row | Status | Evidence |
| --- | --- | --- | --- |
| UA1-A (Task Area narrowing) | Operator-language tri-state badge (`阻塞中` / `就绪` / `可发布`) renders on Matrix Script cards | PASS (static) | `test_tri_state_badge_label_per_bucket` (3 cases) + `test_unknown_bucket_falls_back_to_ready` |
| UA1-A (subject) | `主题：{title}` renders on Matrix Script cards | PASS (static) | `test_subject_field_renders_title` |
| UA1-A (current variation) | `当前变体数：{cells_length}` renders, including `0` and packet-shape fallback | PASS (static) | `test_current_variation_count_*` (3 cases) |
| UA1-A (publishable variation gating) | `可发布版本数：—` with operator-language tooltip naming the unified `publish_readiness` producer gating | PASS (static) | `test_publishable_variation_count_intentionally_none_for_d1_gating` |
| UA1-A (current blocker) | `当前阻塞项：{operator-language}` for known closed-set codes; verbatim fallthrough for unknown codes; `无` when none | PASS (static) | `test_known_blocker_codes_translate_to_operator_language` (7 cases) + `test_unknown_blocker_code_falls_through_verbatim` + `test_no_blocker_when_head_reason_empty_or_missing` |
| UA1-A (action zoning) | `进入工作台` + `跳交付中心` action buttons replace generic `查看详情` for Matrix Script rows; hrefs from `config.next_surfaces`; canonical-path fallback | PASS (static) | `test_action_hrefs_*` (3 cases) |
| HF-PRES (PR-U1) | Hot Follow Task Area card unchanged | PASS (file isolation) | `git diff --name-only` shows no Hot Follow files touched; Hot Follow rows render via `{% else %}` branch verbatim |
| DA-PRES (PR-U1) | Digital Anchor Task Area card unchanged | PASS (file isolation) | `git diff --name-only` shows no Digital Anchor files touched; Digital Anchor rows render via `{% else %}` branch verbatim |
| FORBID (PR-U1) | No gate spec §4 forbidden item landed | PASS | No contract mutation; no projection mutation; no D1 unified `publish_readiness` producer (gating sentinel emitted instead); no D2 / D3 / D4; no provider/model/vendor/engine identifier in summary (covered by `test_summary_carries_no_vendor_model_provider_engine_keys`); no Asset Library; no promote service; no Digital Anchor implementation; no Hot Follow change; no contract addendum; no React/Vite footprint; no first-phase A7 signoff touched |

## 8. Final gate (PR-U1)

| # | Question | Verdict |
| --- | --- | --- |
| 1 | PR-U1 (Task Area comprehension) opened on a narrow operator-visible scope | **YES** — Matrix Script-row-gated `tasks.html` block + new helper + 30 tests |
| 2 | Hot Follow baseline preserved | **YES** — file isolation; `{% else %}` renders prior content verbatim |
| 3 | Digital Anchor freeze preserved | **YES** — no Digital Anchor file touched; Plan A §2.1 hide guards still in force |
| 4 | No Platform Runtime Assembly | **YES** — no Phase A–E work |
| 5 | No vendor/model/provider controls in UI | **YES** — covered by `test_summary_carries_no_vendor_model_provider_engine_keys`; sanitization at the operator boundary preserved |
| 6 | No contract-truth mutation | **YES** — no `docs/contracts/` file touched; no schema file touched |
| 7 | No full frontend rebuild | **YES** — no new component framework, no new style system, no new build dependency, no React/Vite footprint |
| 8 | First-phase A7 closeout signoff still intentionally pending | **YES** — `PLAN_E_MATRIX_SCRIPT_PHASE_CLOSEOUT_v1.md` §3 untouched |

PR-U2 (Workbench comprehension) and PR-U3 (Delivery Center comprehension) remain pending and will be opened only **after** PR-U1 lands per the user-mandated sequence.

---

End of Plan E Matrix Script UI Alignment PR-U1 (Task Area Comprehension) — Execution Log v1.
