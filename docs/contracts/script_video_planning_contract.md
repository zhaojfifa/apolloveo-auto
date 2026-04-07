# Script Video Planning Contract

## 1. Purpose

This document freezes the Phase-2 planning contract for a future `script_video_line`.

The contract exists to absorb the most useful planning structures identified in:

- `docs/reviews/review_jellyfish_importability_for_factory.md`

without importing studio-product truth ownership or UI shell semantics.

## 2. Planning Role

Script-video planning is an upstream draft layer.

It exists to:

- divide source script into execution-friendly segments and shots
- keep candidate assets separate from linked assets
- preserve planning provenance before business truth is accepted
- expose file-usage indexing hooks for later line execution

It is not:

- a final task truth table
- a publish truth source
- a direct deliverable writer
- a studio shell requirement

## 3. Core Draft Objects

### 3.1 ScriptVideoPlanningDraft

Minimal draft envelope:

```json
{
  "planning_id": "draft-id",
  "line_id": "script_video_line",
  "source_ref": "script or task ref",
  "status": "draft|reviewing|accepted|rejected",
  "segments": [],
  "shots": [],
  "candidate_assets": [],
  "linked_assets": [],
  "file_usage_index": []
}
```

### 3.2 SegmentDraft

Represents a logical script section before or alongside shot division.

Fields:

- `segment_id`
- `source_text`
- `narrative_role`
- `timing_hint`
- `prompt_template_ref`

### 3.3 ShotUnitDraft

Represents one planning-time shot candidate.

Fields:

- `shot_id`
- `segment_id`
- `shot_text`
- `shot_intent`
- `camera_hint`
- `location_hint`
- `required_roles`
- `required_props`
- `candidate_asset_refs`
- `linked_asset_refs`

## 4. Candidate vs Linked Dual-State

This is the key planning rule.

### 4.1 Candidate Asset

A candidate asset is:

- inferred
- suggested
- unconfirmed
- replaceable

Candidate state fields:

- `candidate_id`
- `asset_type`
- `source`
- `confidence`
- `evidence`
- `status`

Allowed candidate statuses:

- `suggested`
- `reviewing`
- `rejected`

### 4.2 Linked Asset

A linked asset is:

- operator-accepted or policy-accepted
- reference-stable enough to use in later execution
- still not itself a publish or deliverable truth write

Linked state fields:

- `link_id`
- `asset_ref`
- `linked_from_candidate_id`
- `accepted_by`
- `accepted_at`
- `usage_scope`

Allowed linked statuses:

- `linked`
- `superseded`
- `detached`

## 5. Planning File Usage Index

Planning must record where candidate or linked assets are used.

Minimal file-usage shape:

```json
{
  "usage_id": "usage-id",
  "planning_id": "draft-id",
  "scope_type": "segment|shot",
  "scope_id": "shot-12",
  "asset_ref": "file-or-asset-id",
  "usage_role": "reference|candidate|linked|prompt_input"
}
```

This index is planning metadata, not sink truth.

## 6. Prompt Template Registry Hook

Planning drafts may refer to a prompt template registry by reference only.

Allowed fields:

- `prompt_template_ref`
- `prompt_category`
- `template_variant`

Planning must not inline a hidden execution engine through this field.

## 7. Truth Ownership Boundary

Script-video planning may produce:

- drafts
- candidate sets
- link suggestions
- usage indexes
- review notes

It may not directly write:

- canonical line task status
- canonical deliverable keys
- publish truth
- asset sink truth
- final execution-ready acceptance without an explicit controller boundary

## 8. Relation To Future Lines

This contract is intended to support:

- `script_video_line` as planning-first upstream structure
- later feeding `action_replica_line`
- later feeding line-scoped worker execution without importing studio shell semantics

## 9. Explicit Non-Goals

This contract does not authorize:

- a chapter/project/studio product shell
- a workflow editor
- direct generator execution from planning drafts
- task-status writes from planning models
- broad UI construction in the same PR
