# Appendix: Line Contract / Skill Readiness

Date: 2026-04-20

## Runtime Line Binding

Implemented:

- `gateway/app/lines/base.py::ProductionLine`
- `gateway/app/lines/base.py::LineRegistry`
- `gateway/app/lines/hot_follow.py::HOT_FOLLOW_LINE`
- `gateway/app/services/line_binding_service.py::get_line_runtime_binding`

Hot Follow runtime fields:

- `line_id="hot_follow_line"`
- `line_version="1.9.0"`
- `target_result_type="final_video"`
- `task_kind="hot_follow"`
- `input_contract_ref="docs/contracts/HOT_FOLLOW_RUNTIME_CONTRACT.md"`
- `deliverable_profile_ref="docs/architecture/line_contracts/hot_follow_line.yaml"`
- `sop_profile_ref="docs/runbooks/hot_follow_sop.md"`
- `skills_bundle_ref="skills/hot_follow"`
- `worker_profile_ref="docs/contracts/worker_gateway_runtime_contract.md"`
- `asset_sink_profile_ref="docs/contracts/status_ownership_matrix.md"`
- `ready_gate_ref="docs/contracts/hot_follow_ready_gate.yaml"`
- `status_policy_ref="gateway/app/services/status_policy/hot_follow_state.py"`

Readiness: **runtime-bound metadata with partial execution use**.

## Contract Element Matrix

| Element | Declared where | Runtime consumed where | Status | Notes |
| --- | --- | --- | --- | --- |
| Line id / task kind | `hot_follow.py`, YAML/docs | `LineRegistry.for_kind`, line binding | Implemented | Real runtime binding |
| Input contract | `HOT_FOLLOW_RUNTIME_CONTRACT.md` | Not loaded as schema | Documented | Runtime still accepts dict/HTTP fields |
| Deliverable profile | `hot_follow_line.yaml` | `task_view.py::hf_deliverables` hand-codes deliverables | Partial/documented | Not profile-driven |
| SOP profile | `docs/runbooks/hot_follow_sop.md` | Not runtime-executed | Documented | SOP is operator/doc guide, not step graph |
| Skills bundle | `skills/hot_follow` | `skills_runtime.py`, `hot_follow_skills_advisory.py` | Implemented MVP | Read-only advisory only |
| Worker profile | `worker_gateway_runtime_contract.md` | passed in `WorkerRequest.worker_profile_ref` | Partial | Registry hard-codes Hot Follow compose adapter |
| Asset sink profile | `status_ownership_matrix.md` | not runtime sink engine | Ceremonial/documented | Ownership doc only |
| Confirmation policy | `ProductionLine.confirmation_policy` | exposed in line metadata | Mostly ceremonial | No generic confirmation executor |
| Ready gate | `hot_follow_ready_gate.yaml` | `ready_gate/hot_follow_rules.py` | Implemented | YAML-backed runtime spec |
| Status policy | `status_policy_ref` metadata | `status_policy/registry.py` kind-based | Partial | Ref is not dynamically loaded |

## Skills Runtime Reality

Implemented files:

- `gateway/app/services/skills_runtime.py`
- `gateway/app/services/hot_follow_skills_advisory.py`
- `skills/hot_follow/input_skill.py`
- `skills/hot_follow/routing_skill.py`
- `skills/hot_follow/quality_skill.py`
- `skills/hot_follow/recovery_skill.py`
- `skills/hot_follow/config/defaults.yaml`

Actual flow:

```text
line binding
  -> hot_follow_skills_advisory.maybe_build_hot_follow_advisory
  -> build_hot_follow_advisory_input
  -> skills_runtime.load_line_skills_bundle
  -> run stage_order: input, routing, quality, recovery
  -> normalize advisory output
  -> attach to workbench payload
```

Allowed behavior:

- read `ready_gate`
- read `artifact_facts`
- read `current_attempt`
- read `operator_summary`
- produce advisory output

Disallowed and currently not implemented:

- repo writes
- deliverable writes
- ready gate writes
- status writes
- worker execution
- asset sink promotion

## Skill Stage Reality

### `input_skill.py`

Real behavior:

- normalizes target language
- reads subtitle/audio/compose/publish readiness
- reads compose route/input/execution split
- exposes final/artifact/current attempt facts for downstream advisory stages

Boundary: read-only fact extraction.

### `routing_skill.py`

Real behavior:

- prioritizes subtitle source mismatch
- compose blocked
- compose input unready / derive failed
- no-dub terminal route
- recompose required
- compose missing final
- refresh dub
- review subtitles
- final ready

Boundary: advisory route key only. It does not execute.

### `quality_skill.py`

Real behavior:

- maps routing decision key to configured advisory.
- formats explanation from input facts.

Boundary: advisory formatting only.

### `recovery_skill.py`

Real behavior:

- copies evidence fields from facts into advisory evidence.

Boundary: no recovery execution.

## Implicit Skills Still In Non-Skill Code

| Skill class | Current code location | Should move? | Boundary |
| --- | --- | --- | --- |
| Content mode classification | `subtitle_helpers.py`, `task_view.py`, `hot_follow_api.py` compatibility helpers | Yes, eventually | Read-only recommendation first |
| Compose route interpretation | `hot_follow_route_state.py` | Maybe, after state safety | Must not own execute truth |
| TTS/provider preference | `tts_policy.py`, `voice_state.py`, `tasks.py::_run_dub_job` | Yes | Skills can suggest provider; service owns execution/write |
| Subtitle quality/readability | `dub_text_guard.py`, subtitle currentness helpers | Yes | Advisory only |
| Recovery recommendation | `CompositionService.recover_stale_running_compose`, skills advisory | Partially already | Service owns actual recovery writes |
| Reference/source understanding | `hot_follow_subtitle_currentness.py`, subtitle lane helpers | Partially | Currentness truth must remain status/service owned |

## New Line Readiness Gate

Before a new line can be added, require:

1. `ProductionLine` declaration.
2. Human-readable contract.
3. Machine-readable line contract or manifest.
4. Deliverable profile that is actually loaded by runtime.
5. Four-layer state map.
6. Ready gate contract and runtime spec.
7. Status policy entrypoint.
8. Workbench/publish response schema.
9. Skills bundle only if it has read-only input/output schema.
10. Worker profile and registered execution adapters.
11. Tests proving line binding, ready gate binding, deliverable assembly, state derivation, and no direct skill/worker truth writes.

## Current New-Line Verdict

Current readiness: **not safe yet**.

Reason:

- Hot Follow is runtime-bound but not generic enough to clone.
- Critical profiles are metadata-only.
- Workbench response assembly is not contract-first.
- Task writes are not centralized.
- Router transaction scripts remain too large and too authoritative.

Minimum safe target:

- new line code should not modify `tasks.py` except route registration or generic dispatch.
- new line code should not copy `task_view.py::build_hot_follow_workbench_hub`.
- new line code should be contract-first and line-runtime-bound before endpoint exposure.
