# Matrix Script P1-2 State + P1-3 Active Focus (2026-06-06)

Short engineering state note. Execution evidence only — not implementation
authority. The index entry is `docs/ENGINEERING_INDEX.md` (Matrix Script
Changes); the round-1 closure is
`docs/execution/MATRIX_SCRIPT_P1_OPERATOR_EDIT_LOOP_CLOSURE_20260606.md`.

## Established on main

```
P0:        #202 artifact truth + #203 async lifecycle/polling/stale guard
P1 PR-1:   #206 Shot Material Replacement Intent
P1 PR-2:   #207 Regenerate Preview Versioning (V1 current main / V2 candidate)
P1 closure:#208 operator edit loop closure (docs)
P1-2 PR-A: #209 Shot Material Attachment Handle (asset:// reference on a shot intent)
P1-2 PR-B: #210 Regenerate records the attached material as based_on_assets
```

Key state fact:

```
material_bytes_consumed remains FALSE — asset:// attachment handles are operator
references with no byte store, so V2 regeneration records based_on_assets and
renders honest reference-label markers ("已绑定运营素材引用，当前预览以素材引用标
记生成。"); it never claims a real pixel replacement.
```

## Next active focus

```
Matrix Script P1-3 PR-C — Shot Material Upload / Storage Handle.
Goal: make attached material BYTES resolvable, WITHOUT consuming them in
regeneration yet.
  - operator uploads/binds a material file for a shot
  - stored under a Matrix-Script-scoped local workspace path (no artifact_storage.py)
  - shot intent entry records bytes_resolvable=true, storage_scope=local_workspace,
    material_source=operator_upload, a resolvable handle, and a preview/thumbnail
  - material_bytes_consumed stays FALSE (regeneration byte consumption is PR-D)
```

Boundary held by PR-C: no V2 byte consumption, no Akool live, no provider
switching, no multi-variant, no official publish, no Hot Follow / Digital Anchor
/ `artifact_storage.py` / schema-contract change. `official_publish_ready`
remains false.
