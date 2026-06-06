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
P1-3 PR-C: #211 Shot Material Upload / Storage Handle (msmaterial:// local_workspace bytes; resolvable, not yet consumed)
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
Matrix Script P1-3 PR-D — Regenerate Consumes Uploaded Material Bytes.
Goal: a V2 regeneration RESOLVES a stored msmaterial:// handle and CONSUMES its
bytes (the byte-store wiring PR-C deferred).
  - regen resolver resolves msmaterial:// → local_workspace path (asset:// still None)
  - renderer uses an uploaded image directly; an uploaded video's first frame is
    extracted; anything unresolved/unsupported falls back to the default asset
  - material_bytes_consumed=true ONLY when at least one uploaded file is actually
    used; V2 entry records consumed_materials (shot_id / material_name /
    material_kind / safe msmaterial:// handle / source)
  - workbench copy is honest: used → "已使用运营上传素材生成新预览";
    unresolved/unsupported → "已绑定运营素材引用，当前预览以素材引用标记生成。"
  - V1 stays current until confirm; delivery follows confirmed main only;
    discard / failure preserve V1
```

Boundary held by PR-D: no Akool live, no provider switching, no multi-variant,
no official publish, no public publish URL, no Hot Follow / Digital Anchor /
`artifact_storage.py` / schema-contract change. `official_publish_ready` remains
false. (PR-C established the storage handle; byte consumption is this PR.)
