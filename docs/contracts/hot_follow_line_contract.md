# Hot Follow Line Contract

## 1. Purpose

This document freezes the human-readable contract for the current `hot_follow_line`.

It is the docs-first baseline for the `VeoMVP01` refactor pass:

- the platform is organized by Production Line, not by model/tool
- Hot Follow remains one formal line, not a temporary router branch
- `tasks.py` / `hot_follow_api.py` must eventually consume this contract instead of behaving like an implicit transaction-script hub

This file is intentionally paired with the current runtime mirrors:

- structured line declaration: `docs/architecture/line_contracts/hot_follow_line.yaml`
- runtime line registration: `gateway/app/lines/hot_follow.py`

## 2. Contract Summary

| Contract Field | Frozen Value | Reference |
| --- | --- | --- |
| `line_id` | `hot_follow_line` | `docs/architecture/line_contracts/hot_follow_line.yaml`, `gateway/app/lines/hot_follow.py` |
| `task_kind` | `hot_follow` | `gateway/app/lines/hot_follow.py` |
| `target_result_type` | `final_video` | `docs/architecture/line_contracts/hot_follow_line.yaml` |
| `input_contract_ref` | link ingest + local video ingest into the same Hot Follow runtime | `docs/contracts/HOT_FOLLOW_RUNTIME_CONTRACT.md`, `docs/runbooks/hot_follow_sop.md` |
| `deliverable_profile_ref` | final video primary, subtitle/audio secondary, pack optional | `docs/architecture/line_contracts/hot_follow_line.yaml`, `docs/contracts/status_ownership_matrix.md` |
| `sop_profile_ref` | Hot Follow operator/engineer SOP baseline | `docs/runbooks/hot_follow_sop.md`, `gateway/app/lines/hot_follow.py` |
| `skills_bundle_ref` | runtime Hot Follow skills bundle path with stage modules and defaults | `skills/hot_follow`, `docs/contracts/skills_runtime_contract.md` |
| `worker_profile_ref` | hybrid worker execution under live gateway boundary | `docs/contracts/worker_gateway_runtime_contract.md` |
| `asset_sink_profile_ref` | deliverable sink is downstream of line/service truth, not worker-owned | `docs/contracts/status_ownership_matrix.md` |
| `confirmation_policy` | before publish only | this document, `docs/runbooks/hot_follow_sop.md` |
| `status_policy_ref` | `gateway/app/services/status_policy/hot_follow_state.py` | `docs/contracts/status_ownership_matrix.md` |
| `ready_gate_ref` | `docs/contracts/hot_follow_ready_gate.yaml` | runtime loader: `gateway/app/services/ready_gate/hot_follow_rules.py` |

## 3. Business Result Contract

### 3.1 Line Identity

- `line_id`: `hot_follow_line`
- `line_name`: `Hot Follow Line`
- `task_kind`: `hot_follow`
- `target_result_type`: `final_video`

### 3.2 Business Promise

Hot Follow is the production line that turns a source short video into a publishable localized final video through one operator-visible workbench and one runtime chain:

- ingest
- parse
- adapt
- dub
- compose
- review gate
- pack / publish / sink

The line remains singular even when it supports multiple target-language profiles such as Myanmar and Vietnamese.

## 4. Input Contract Reference

Hot Follow currently accepts two source-entry modes into the same line:

- link ingest
- local video ingest

Both entry paths must normalize into the same downstream Hot Follow truth shape:

- raw/source video becomes a line-owned artifact
- task kind remains `hot_follow`
- workbench / subtitle / dub / compose continue on the same runtime chain

Current contract references:

- runtime entry boundary: `docs/contracts/HOT_FOLLOW_RUNTIME_CONTRACT.md`
- operator flow: `docs/runbooks/hot_follow_sop.md`

Current supported source-language scope for local upload remains intentionally narrow:

- Chinese
- English

## 5. Deliverable Profile Reference

Hot Follow deliverables are frozen as:

- primary deliverable:
  - publishable final video
- secondary deliverables:
  - target subtitle artifact
  - dubbed audio artifact
- optional derivative deliverables:
  - pack / scene pack / non-core derivative outputs

Contract rule:

- optional derivative outputs must never override the truth of the primary final deliverable
- primary task completion is driven by main delivery truth and ready gate, not optional artifact presence

See:

- `docs/contracts/status_ownership_matrix.md`
- `docs/contracts/hot_follow_ready_gate.yaml`

## 6. SOP Profile Reference

The frozen SOP profile for this line is:

- `docs/runbooks/hot_follow_sop.md`

The current operator/engineer skeleton is:

- `ingest -> parse -> adapt -> dub -> compose -> review_gate -> pack_publish_sink`

Current runtime note:

- `gateway/app/lines/hot_follow.py` now mirrors `docs/runbooks/hot_follow_sop.md`
- compose/workbench/publish assembly now reads line contract metadata through the line binding service instead of leaving the line declaration ceremonial

## 7. Skills Bundle Reference

Hot Follow uses a composable skills bundle as a strategy layer, not as a business truth writer.

The current bundle scope is:

- input interpretation
- language routing / translation gating
- TTS routing
- compliance checks
- media compose parameter selection
- recovery / fallback guidance

Hard boundary:

- skills may propose or compute
- skills must not directly write repo truth
- skills must not directly write deliverable truth
- skills must not directly write asset sink truth
- skills must not directly finalize task status

Reference anchors:

- `skills/hot_follow`
- `docs/contracts/skills_runtime_contract.md`
- `docs/contracts/worker_gateway_contract.md`
- `docs/contracts/status_ownership_matrix.md`

## 8. Worker Profile Reference

Hot Follow runs with a hybrid worker profile:

- internal execution for local orchestration / FFmpeg / file staging
- external execution for provider-backed ASR / TTS / parsing where applicable
- hybrid execution when a single step spans both

The worker boundary is frozen by:

- `docs/contracts/worker_gateway_contract.md`

## 9. Asset Sink Profile Reference

Asset sink is downstream of line/service truth and remains a controlled write boundary.

Current sink behavior:

- final video may be auto-sunk
- subtitle/audio/pack may be sunk according to line policy
- sink promotion to canonical asset space remains an explicit operational decision

Hard boundary:

- worker and skills layers do not directly promote sink truth
- sink writes happen after service/controller acceptance of artifact truth

See:

- `docs/contracts/status_ownership_matrix.md`

## 10. Confirmation Policy

Hot Follow confirmation policy is intentionally narrow:

- before execute: no
- before result accept: no separate gate; workbench review is implicit
- before publish: yes
- before retry: no global confirmation requirement

Operator confirmation hooks are further referenced by:

- `docs/contracts/hot_follow_ready_gate.yaml`
- `docs/runbooks/hot_follow_sop.md`

## 11. Status Policy Reference

The current status policy entrypoint is:

- `gateway/app/services/status_policy/hot_follow_state.py`

The ownership rules for status, currentness, deliverable keys, and display projection are frozen in:

- `docs/contracts/status_ownership_matrix.md`

## 12. Ready Gate Reference

The docs-first ready gate declaration is:

- `docs/contracts/hot_follow_ready_gate.yaml`

The current runtime loader path is:

- `gateway/app/services/ready_gate/hot_follow_rules.py`
- `gateway/app/services/ready_gate/engine.py`

The current binding baseline is:

- `docs/architecture/line_contracts/HOT_FOLLOW_GATE_BINDING_CONTRACT.md`

## 13. Runtime Status Of This Contract

This contract is frozen before the full `tasks.py` decomposition, and runtime consumption is now partially bound:

- `LineRegistry.for_kind("hot_follow")` already exists
- ready gate already has a line-aware binding path
- publish/workbench/compose shell paths now consume bound line metadata at runtime
- PR-4 consumes the line registry, skills bundle, worker profile, deliverable profile, and asset sink profile references through `gateway/app/services/line_binding_service.py`
- the runtime payload exposes these consumed references under `line.runtime_refs`
- router/service assembly is not yet fully contract-driven
- `tasks.py` still carries orchestration and view responsibilities that should move out in P0/P1 refactor steps

That gap is intentional and documented, not hidden:

- `docs/adr/ADR-task-router-decomposition.md`

## 14. PR-4 Runtime Reference Freeze

The following references are runtime-bound for Hot Follow and are no longer ceremonial declarations:

| Runtime Reference | Consumed By | Frozen Boundary |
| --- | --- | --- |
| `line_registry` | `LineRegistry.for_kind("hot_follow")` through `get_line_runtime_binding(...)` | resolves the active production line for a Hot Follow task |
| `skills_bundle_ref` | `load_line_skills_bundle(line)` | loads the read-only skills bundle declaration and stage order |
| `worker_profile_ref` | line binding runtime reference resolver | confirms the worker profile contract file used by the line |
| `deliverable_profile_ref` | line binding runtime reference resolver | reads the Hot Follow line contract YAML to expose primary and secondary deliverable kinds |
| `asset_sink_profile_ref` | line binding runtime reference resolver | confirms the asset sink profile reference and exposes line sink policy flags |

Runtime reference consumption is introspective and read-only. It must not:

- write subtitle, dub, compose, deliverable, or sink truth
- change ready gate semantics
- make skills a truth owner
- introduce a second production line

The business execution path remains owned by the existing Hot Follow services and status policy.
