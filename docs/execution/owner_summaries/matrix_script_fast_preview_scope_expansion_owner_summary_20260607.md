# Owner Summary / Report — Matrix Script Fast Preview Scope Expansion Batch (2026-06-07)

Docs companion to the Scope Expansion Batch (Fast Lane S5→S8). Not authority.

Resolves the two findings from the Production Smoke (#243):
1. operator projection didn't surface `scene_strategy` / QC as first-class fields;
2. the live service entry didn't thread `shot_images` (backbone never auto-engaged).

## What this batch is

Turns the proven ffmpeg fast-preview backbone from an *acceptance-proven artifact path*
into a *live Matrix Script service-consumable path*. **Implementation PR; NOT merged.**

## What it implements (allowed files only)

- **Operator projection** (`minimal_result_projection.py`) now surfaces three additive,
  operator-safe fields: `preview_mode` (operator label for the internal `scene_strategy`
  token — the **raw token is never surfaced**), `qc_passed` (bool / None on legacy), and
  `qc_summary` (operator-language sentence, e.g. `质检通过 · 画面规格 1080x1920`). Derived
  only from existing manifest/artifact facts; the closed-key forbidden-token guard still
  runs over the payload.
- **Record** (`minimal_result_record.py`): carries `qc_passed` / `qc_resolution`
  (hashable scalars — chosen over a dict so the frozen record stays hashable).
- **Live service entry** (`minimal_result_service.py`): `MatrixScriptMinimalResultRequest`
  gains an optional `shot_images` (shot_id → local still / resolved material), threaded
  into `run_minimal_result_loop`; the **ffmpeg backbone auto-engages** when valid stills
  exist, color-card fallback otherwise. The summary now carries `qc_passed` /
  `qc_resolution` from the manifest QC.

## Truth preserved

- **Legacy behavior stable**: no `shot_images` → color-card path, `qc_passed=None`,
  `preview_mode=快速预览·占位色卡`; 90 adjacent tests (record/projection/orchestrator/
  real-trial/closure/card) pass.
- **No new public input contract**: `shot_images` is an internal service-request field;
  no schema/contract/route/provider change. The manifest shape is unchanged
  (`minimal_result_record_to_dict` closed key set untouched).
- `official_publish_ready` stays **false**; delivery truth unchanged; no raw
  scene_strategy/vendor/provider token in the operator payload.

## Acceptance (real tomato-beach fixture)

Via the **live service entry** (`run_matrix_script_minimal_result(request, shot_images=...)`):
scene clips + `final.mp4` + manifest + ffprobe QC produced; `scene_strategy=ffmpeg_backbone_proxy`;
the operator projection shows `preview_mode=快速预览·镜头代理`, `qc_passed=True`,
`official_publish_ready=false`; color-card fallback preserved; legacy (no `shot_images`)
stays color-card. No leakage.

## Validation evidence

- `py_compile gateway/app/main.py` (+ touched modules) → OK.
- Focused: smoke (7) + minimal_result_loop (13) + backbone (35) = **55 passed**.
- Adjacent: record + projection + orchestrator + real-trial + closure + task-card = **90 passed**.
- `git diff --check` clean; **allowed files only** (`minimal_result_service.py` /
  `minimal_result_record.py` / `minimal_result_projection.py` + the smoke test + this doc);
  no route/endpoint change; forbidden-path clean; no-secret clean.
- Behavior preservation: additive optional fields only (defaults preserve legacy).
- Index note: this is an execution owner summary (evidence), not an index-tracked
  authority doc — no `docs/ENGINEERING_INDEX.md` change required.

## Boundary

runtime changed: **service/record/projection (operator-safe additive surfacing + input
threading)** · provider integration: **No** · credentialed calls: **No** · generative
adapter: **No** · subtitle/voiceover/bgm/broll/avatar: **No** · schemas/contracts: **No** ·
routes: **No** (no route behavior change; an internal request field only) · vendor UI:
**No** · delivery truth: **unchanged** · official_publish_ready: **unchanged (False)** ·
Slot v2 runtime: **none** · merged: **No**.

---

## 给 Claude 的指令

- **current Owner decision:** #243 merged; Scope Expansion Batch implemented under Fast
  Lane S5→S8; PR ready, **NOT merged**. Credentialed trial = HOLD. §13 = untouched. Slot
  v2 = CLOSED. No further PR after this batch without Owner approval.
- **allowed next actions (on Owner go):** **APPROVE S8→S9 merge** for this batch → merge +
  sync main + post-merge validation + merge report.
- **forbidden actions:** no merge without Owner S8→S9; no PR after this batch without Owner
  approval; no provider calls/credentials; no generative adapter; no subtitle/voiceover/
  bgm/broll/avatar; no schema/contracts; no route behavior change; no vendor UI; no
  delivery-truth/`official_publish_ready` change; no Slot v2 runtime; no §13 fill.
- **required outputs (delivered):** #243 merge report; implementation PR; this report.
- **validation checks:** focused (55) + adjacent (90) tests, py_compile, diff-check,
  allowed-files-only, forbidden-path, route check, no-secret, behavior-preservation — all clean.
- **stop point:** stop before merge; request S8→S9.
- **Owner Decision Needed:** APPROVE S8→S9 merge for the Scope Expansion Batch?
