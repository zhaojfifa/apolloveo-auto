# New-Line Onboarding Template

## Purpose

This template freezes the minimum onboarding package required before any future
production line can move from design preparation into implementation.

It is a preparation artifact only. Filling this template does not authorize a
second line to be implemented.

## Preconditions

Before a new-line onboarding packet is drafted, all of the following must
already be true on the active VeoBase01 baseline:

1. `docs/contracts/four_layer_state_contract.md` is still the active state
   authority.
2. `docs/contracts/workbench_hub_response.contract.md` is still the active
   presenter authority.
3. `docs/contracts/skills_runtime_contract.md` and
   `docs/contracts/skills_bundle_boundary.md` are the active skills boundary.
4. `docs/contracts/line_job_state_machine.md` is the active line-job lifecycle
   reference.
5. Existing Hot Follow regression validation remains green.
6. No implementation scope for the new line has been started in the same PR.

## Required Packet

Every onboarding packet must provide the following sections.

### 1. Line Identity

- `line_id`
- `line_name`
- `line_version`
- `task_kind`
- `target_result_type`
- target operator/business outcome
- explicit statement that the line reuses VeoBase01 four-layer state

### 2. Contract References

- `input_contract_ref`
- `sop_profile_ref`
- `skills_bundle_ref`
- `worker_profile_ref`
- `deliverable_profile_ref`
- `asset_sink_profile_ref`
- `status_policy_ref`
- `ready_gate_ref`

These refs must point to concrete docs or code entrypoints. Placeholder prose
without a concrete ref is not sufficient.

### 3. Schema Packet

The onboarding packet must include or reference all frozen example shapes:

- `docs/contracts/line_contract.example.yaml`
- `docs/contracts/worker_profile.example.yaml`
- `docs/contracts/deliverable_profile.example.yaml`
- `docs/contracts/asset_sink_profile.example.yaml`

The proposed line may add fields later, but it may not remove the frozen
minimum identity and ownership fields without a contract PR.

### 4. Four-Layer Ownership Mapping

The packet must state which components are expected to:

- write L1 operational status
- write L2 accepted artifact truth
- derive L3 currentness and stale/fresh judgments
- derive L4 ready gate, operator summary, and advisory

If any section implies more than one writer for the same truth family, the line
is not ready to onboard.

### 5. Line-Job State Machine Mapping

The packet must map the proposed line to the states defined in
`docs/contracts/line_job_state_machine.md`:

- how the line enters `submitted`
- when it becomes `line_bound`
- what conditions advance it into execution
- what facts can block it at review/publish time
- how it reaches `completed`, `failed`, or `cancelled`

The packet must not invent a separate lifecycle that bypasses the shared
line-job states unless a later contract PR explicitly freezes that change.

### 6. Skills Bundle Boundary

The packet must describe:

- bundle path
- stage coverage
- read-only inputs
- allowed output classes
- deterministic fallback when skills are unavailable
- proof that the bundle does not become a truth writer

See `docs/contracts/skills_bundle_boundary.md`.

### 7. Multi-Role Harness Preconditions

A new line may not claim harness readiness unless all of the following are
explicit:

1. role names and ownership boundaries are documented
2. each role consumes the same frozen glossary terms
3. each role reads the same line contract refs
4. no role can write L2/L3/L4 truth outside its declared owner path
5. harness assertions cover role handoff, not only single-step success
6. the existing Hot Follow line remains the reference line for shared behavior

### 8. Second-Line Onboarding Gate

The packet must end with a gate decision in one of these forms:

- `blocked_for_preparation_only`
- `ready_for_future_implementation_pr`

For VeoBase01 PR-5, the only allowed gate result is
`blocked_for_preparation_only`.

The gate decision must name what remains missing before implementation may
start, including runtime ownership, validation, and review expectations.

## Review Checklist

Use this checklist before accepting an onboarding packet:

1. The packet names concrete refs instead of describing aspirational modules.
2. The packet reuses the unified glossary terms without creating synonyms.
3. The packet reuses the shared line-job state machine.
4. The packet keeps skills, workers, deliverables, and asset sinks inside their
   frozen boundaries.
5. The packet does not authorize runtime implementation in the same PR.
6. The packet records whether the line is still blocked.

## Non-Goals

- implementing the next production line
- changing translation, dub, or compose semantics
- rewriting ready-gate meaning
- changing the current workbench wire contract
