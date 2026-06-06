# Matrix Script P1 — Operator Edit Loop Closure (2026-06-06)

Status: **CLOSED — Matrix Script P1 operator edit loop established.**
main HEAD at closure: `cf9c47357772d74f763d83e348ce6e5dc3a7f95f`
(merge of #207 into `main`).

This is a documentation-only closure. It records the composition of the P1
operator edit loop on top of the P0 baseline. No code, contract, schema, or
architecture changes accompany it.

## Closure composition

```
P0 baseline:  #202 + #203
P1 PR-1:      #206  Shot Material Replacement Intent
P1 PR-2:      #207  Regenerate Preview Versioning
```

- **#202 + #203** form the P0 baseline: async preview lifecycle, artifact truth,
  failure finalization, stale guard, and an operator-visible main video result
  exposed as a delivery candidate. See
  `docs/execution/MATRIX_SCRIPT_ASYNC_STATE_MACHINE_CLOSURE_20260604.md`.
- **#206 — Shot Material Replacement Intent (P1 PR-1):** shot-level intent only
  (`supplement` / `replace` / `keep`). Marking an intent makes the material a
  dirty state; it does NOT upload, store, regenerate, version, overwrite the
  current main video, change the delivery candidate, or flip
  `official_publish_ready`.
- **#207 — Regenerate Preview Versioning (P1 PR-2):** with a current main (V1)
  and a dirty material intent, the operator regenerates → a V2 *candidate*
  preview is created in its own version slot WITHOUT touching V1. The operator
  then confirms V2 as main, discards it, or keeps tuning. Delivery candidate
  follows the confirmed current main version. `official_publish_ready` stays
  false throughout.

## Current operator edit loop

```
V1 current main visible
→ mark Shot 04 supplement / Shot 05 replace        (intent only, #206)
→ material_changed dirty state                      (operator must regenerate)
→ regenerate V2 candidate                           (own version slot, #207)
→ V1 preserved                                      (current main untouched)
→ confirm V2  OR  discard                           (operator decision)
    · confirm → V2 becomes current main; intents cleared
    · discard → V1 stays current main; candidate removed
→ Delivery follows the confirmed current main
→ official_publish_ready = false                    (throughout)
```

Failure path: a failed regeneration does NOT overwrite V1 and writes no V2
candidate; the projection shows a failed/retry state with V1 still the current
main and "再次生成预览" available.

## Four-layer state

```
L1 regenerate lifecycle
   queued / running / succeeded / failed / retry — V2 regeneration off the
   request thread; never overwrites V1.

L2 V1 / V2 preview artifact facts
   V1 main preview route; V2 candidate version slot with preview_url,
   created_at, source=material_regeneration, based_on_intents.

L3 current main / candidate readiness
   current_main_version (V1|V2), has_candidate_preview, operator_usable,
   delivery_candidate, official_publish_ready=false.

L4 operator projection
   current main video, dirty material badge, regenerate action, V2 candidate
   render (设为主版本 / 丢弃新预览 / 继续调整), failure + retry — operator-safe
   fields only.
```

## Boundaries

```
no upload / R2 attachment yet   — intent and regeneration carry no real material
                                  bytes; no object-storage attachment exists.
no Akool live                   — no Akool surface / task / model / credit touched.
no official publish             — official_publish_ready remains false at every
                                  checkpoint; delivery is a candidate, not a
                                  published deliverable.
```

No Hot Follow / Digital Anchor / `artifact_storage.py` / schema-contract changes.
The P1 PRs touched only Matrix-Script-scoped surfaces (`routers/tasks.py`,
`services/matrix_script/auto_preview_generation.py`,
`services/matrix_script/operator_workbench_view.py`,
`templates/task_workbench.html`, and the Matrix Script tests).

## Next recommended engineering

```
PR-A  Shot Material Attachment Handle
      Give a marked shot intent a concrete material attachment handle (the
      operator's replacement/supplement material reference), without yet
      changing how regeneration consumes it.

PR-B  Regenerate Uses Attached Material
      Make V2 regeneration consume the attached material handles from PR-A so
      the candidate reflects the operator's actual replacement intent.
```

These remain proposals. Upload / R2 / Akool / official publish are still out of
scope and are not started by this closure.
