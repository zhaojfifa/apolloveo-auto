# Matrix Script P1-3 — Material Bytes Closure (2026-06-06)

Status: **CLOSED — Matrix Script P1-3 uploaded-material byte loop established.**
main HEAD at closure: `9ede298561712e3f1aff67e3eaeee1b5475a9624`
(merge of #212 into `main`).

This is a documentation-only closure. It records the composition of the P1-3
uploaded-material byte loop on top of the P1 / P1-2 operator edit loop. No code,
contract, schema, or architecture changes accompany it. The prior closure is
`docs/execution/MATRIX_SCRIPT_P1_OPERATOR_EDIT_LOOP_CLOSURE_20260606.md`; the
intermediate state note is
`docs/execution/MATRIX_SCRIPT_P1_2_STATE_AND_P1_3_FOCUS_20260606.md`.

## Closure composition

```
P1 / P1-2 established:  #206 #207 #209 #210 (intent → V1/V2 versioning →
                        attachment handle → based_on_assets reference)
P1-3 PR-C:              #211  Shot Material Upload / Storage Handle
P1-3 PR-D:              #212  Regenerate Consumes Uploaded Material Bytes
```

P1 / P1-2 carried only operator *references* (`asset://`): a marked shot could
record an attachment handle and a V2 regeneration could record it as
`based_on_assets`, but no real bytes existed, so `material_bytes_consumed`
remained false and the projection used honest reference-label copy. P1-3 closes
that gap: real uploaded bytes become resolvable (PR-C) and are actually consumed
by V2 regeneration (PR-D).

### #211 — Shot Material Upload / Storage Handle (P1-3 PR-C)

The operator uploads a real material file for a shot; it is validated and
persisted, and the shot intent entry is upgraded from a bare reference to a
resolvable storage handle.

- Stored under a Matrix-Script-scoped **local workspace** path
  (`storage_scope=local_workspace`) — no `artifact_storage.py`, provider, or
  publish surface is touched.
- The shot intent entry records an operator-safe resolvable handle
  `material_ref=msmaterial://<task>/<shot>/<file>`,
  `material_source=operator_upload`, `bytes_resolvable=true`, and a local
  preview/thumbnail url.
- Strict validation: image/video only; declared-kind mismatch, empty,
  oversized, unsupported-kind, and missing-file are rejected safely.
- A path-safe file-serving route returns the stored bytes for operator preview;
  unknown task/shot/file is a safe 404 and traversal attempts fail.
- **Workbench B 区** displays the uploaded material metadata — 素材名称 / 素材类型
  / 来源「运营上传素材」/ 状态「已上传，等待再次生成预览」.
- Boundary held by PR-C: bytes are RESOLVABLE but NOT consumed —
  `material_bytes_consumed` stays false (consumption is PR-D). `local_path` is
  backend-only and never projected in the primary operator UI.

### #212 — Regenerate Consumes Uploaded Material Bytes (P1-3 PR-D)

A V2 regeneration now resolves a stored `msmaterial://` handle and consumes its
bytes — honestly, only when the renderer actually uses them.

- The regeneration resolver resolves `msmaterial://` handles through the
  Matrix-Script-scoped storage layer only; `asset://` references still resolve
  to nothing.
- **Image** material is used directly as the shot's visual source.
- **Video** material is consumed only when first-frame extraction succeeds;
  anything unresolved / zero-byte / unsupported / failed-extraction falls back
  to the shot's default asset and is reported NOT consumed.
- `material_bytes_consumed=true` **only** when the renderer actually consumed at
  least one uploaded file (i.e. `consumed_materials` is non-empty).
- `consumed_materials` is operator-safe: it records `shot_id` / label /
  `material_name` / `material_kind` / the safe `msmaterial://` handle / source —
  and `local_path` is never projected.
- Honest copy: consumed uploaded bytes →「已使用运营上传素材生成新预览」;
  unresolved / unsupported →「已绑定运营素材引用，当前预览以素材引用标记生成」.
  A false「真实替换画面」claim is never shown unless bytes were actually consumed.
- The temporary renderer carrier key (`consumed_material_shot_ids`) is popped
  and never persisted in the stored V2 payload.

## Current operator flow

```
V1 current main visible
→ upload Shot 04 / Shot 05 material            (msmaterial:// bytes resolvable, #211)
→ material_changed dirty state                  (operator must regenerate)
→ regenerate V2 candidate                       (own version slot, #207/#212)
→ V2 uses uploaded bytes when supported         (image direct / video first frame, #212)
    · unsupported / unresolved → honest reference-label copy, not consumed
→ V1 preserved                                  (current main untouched)
→ confirm V2  OR  discard                       (operator decision)
    · confirm → V2 becomes current main; delivery follows V2; intents cleared
    · discard → V1 stays current main; candidate removed
→ Delivery follows the confirmed current main
→ official_publish_ready = false                (throughout)
```

Failure path: a failed regeneration does NOT overwrite V1 and writes no V2
candidate; the projection shows a failed/retry state with V1 still the current
main and "再次生成预览" available.

## Four-layer state

```
L1 regenerate lifecycle
   queued / running / succeeded / failed / retry — V2 regeneration off the
   request thread; never overwrites V1.

L2 uploaded material bytes + V1 / V2 preview artifact facts
   uploaded material persisted under a local_workspace path with a resolvable
   msmaterial:// handle (bytes_resolvable=true); V1 main preview route; V2
   candidate version slot with preview_url, created_at,
   source=material_regeneration.

L3 current main / candidate / consumed_materials readiness
   current_main_version (V1|V2), has_candidate_preview,
   material_bytes_consumed (true only when bytes actually consumed),
   consumed_materials, based_on_assets, operator_usable, delivery_candidate,
   official_publish_ready=false.

L4 operator projection
   current main video, uploaded material metadata (B 区), dirty material badge,
   regenerate action, V2 candidate render with honest usage copy + consumed
   material list (设为主版本 / 丢弃新预览 / 继续调整), failure + retry —
   operator-safe fields only; local_path never projected.
```

## Boundaries

```
no Akool live                   — no Akool surface / task / model / credit touched.
no provider switching           — no provider promoted into operator payloads.
no official publish             — official_publish_ready remains false at every
                                  checkpoint; delivery is a candidate, not a
                                  published deliverable.
```

No Hot Follow / Digital Anchor / `artifact_storage.py` / schema-contract
changes. The P1-3 PRs touched only Matrix-Script-scoped surfaces
(`routers/tasks.py`, `services/matrix_script/shot_material_storage.py`,
`services/matrix_script/auto_preview_generation.py`,
`services/matrix_script/tomato_real_result_orchestrator.py`,
`services/matrix_script/operator_workbench_view.py`,
`templates/task_workbench.html`, and the Matrix Script tests).

## Next recommended engineering

```
1. Production browser validation
   Prove the end-to-end operator flow in a real browser: upload Shot material →
   regenerate V2 from uploaded bytes → confirm V2 → delivery follows V2, with
   the honest usage copy and V1 protection observed live.

2. P2 provider / quality integration — only AFTER the operator flow is proven
   Provider / quality work (and any Akool surface) stays out of scope until the
   uploaded-material operator loop is validated in production.
```

These remain proposals. Akool / provider switching / official publish are still
out of scope and are not started by this closure.
