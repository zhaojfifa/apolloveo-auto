# Matrix Script Phase 3 — PR-13R Workbench Action MVP (Execution Note)

Date: 2026-06-01
Branch: `phase3/pr13r-matrix-script-workbench-action`
Base: `main` @ `d38e306656b6497bcfe299c9424dbe31925039dc`
Status: Matrix Script Production Action MVP — the operator can trigger a local minimal result from the Workbench and see it. NOT official delivery, NOT a publish gate, NOT Akool live.

---

## Reading Declaration

### Root indexes / governance
- `README.md`, `ENGINEERING_CONSTRAINTS_INDEX.md`, `docs/README.md`, `docs/ENGINEERING_INDEX.md`
- `CLAUDE.md`, `PROJECT_RULES.md`, `ENGINEERING_RULES.md` (§8 truth-source, §13 product-flow module presence), `CURRENT_ENGINEERING_FOCUS.md`, `ENGINEERING_STATUS.md`

### Task-specific authority
- `docs/design/matrix_script_phase3_akool_real_generation_plan_v1.md` §5/§7
- Phase 3 execution notes PR-9R (workbench block) + PR-12R (internal route)
- `gateway/app/templates/task_workbench.html` (matrix_script branch; §A region; §8.E shell gating), `gateway/app/services/tests/test_matrix_script_workbench_phase2b_product_fidelity.py` (fidelity invariants)

### Why sufficient
PR-13R adds one client-side trigger block to the matrix_script Workbench branch that POSTs to the already-merged PR-12R route and renders its read-only payload. No new server logic; no contract/schema change.

### Missing-authority handling
None.

---

## What was added / changed

| File | Change |
| --- | --- |
| `gateway/app/templates/task_workbench.html` | **+1 block** in the matrix_script branch (after §A): "本地最小成片" card with a `生成本地最小成片` button + status + result container + a small inline `<script>`. Gated by `{% if ms_main_video_result.is_matrix_script %}`. |
| `gateway/app/services/tests/test_matrix_script_minimal_result_workbench_action.py` | **new** — static template assertions + ffmpeg-gated end-to-end via the route. |
| `docs/execution/MATRIX_SCRIPT_PHASE3_PR13R_WORKBENCH_ACTION_MVP.md` | **new** — this note. |

`wiring.py` and `minimal_result_workbench_block.py` were **not** modified (the action is client-side; the server block module/wiring need no change). No JS framework introduced — a single vanilla IIFE in the existing template.

### Operator action
- Button `生成本地最小成片` → `POST /api/matrix-script/{task_id}/minimal-result` (endpoint read from a `data-endpoint` attribute).
- States: idle → `生成中…` (running) → `已生成` (done) / `生成失败（<status>）` (error).
- On success, renders the returned surface payload client-side via `textContent` (no `innerHTML`, no injection): 结果 / 状态 / 本地路径 / 时长（秒）/ 镜头数 / 存储范围 / 正式交付就绪 / 提示.

### Visible result (from the PR-12R payload)
`本地最小成片` · `final_video_path` (local) · `duration_seconds` · `shot_count` · `storage_scope=local_workspace` · `official_publish_ready=false` · operator note `尚未进入正式交付存储`.

---

## Validation

Environment: ffmpeg 8.1.1 / ffprobe present. The end-to-end route test runs here; it **skips** (no fake output) where ffmpeg is absent.

- `pytest test_matrix_script_minimal_result_workbench_action.py` → pass (static action assertions + leak-free + gating + section-order + real route payload).
- `pytest test_matrix_script_minimal_result_route.py` → pass (PR-12R regression).
- `pytest test_matrix_script_workbench_phase2b_product_fidelity.py` → **pass (acceptance #9: existing fidelity green)**.
- `git diff --check` → clean.
- Forbidden-path guard (hot_follow / digital_anchor / contracts / schemas / packet / envelope.py / artifact_storage.py) → none.

---

## What was explicitly NOT added (PR-13R forbidden scope)

No Akool live API / adapter usage; no `artifact_storage` / R2 write; no official publish gate / `publish_url` / `publish_status`; no Delivery Center runtime; no schema / packet / contract change; no Hot Follow / Digital Anchor change (action is gated to matrix_script tasks only); no big UI refactor (one card + one small inline script). Local `final_video_path` is shown but explicitly labelled `storage_scope=local_workspace` + `official_publish_ready=false`. Real generation via Akool + copy-into-Apollo storage remain gated behind the Capability Expansion Gate Wave (W2.3).
