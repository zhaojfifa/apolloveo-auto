# Action Replica Planning Assets Contract

## 1. Purpose

This document freezes the Phase-2 planning asset model for a future `action_replica_line`.

It exists to give Action Replica a clean planning foundation without importing studio semantics directly into runtime truth.

## 2. Planning Asset Role

Action Replica planning assets represent identity and shot-scoped execution intent before generator/runtime execution.

They exist to describe:

- who appears
- what they wear
- what they hold
- which role appears in which shot
- which asset is only a candidate versus linked for execution use

They are not:

- final media outputs
- final publish truth
- direct generator tasks
- direct repo truth writes

## 3. Core Planning Asset Objects

### 3.1 ReplicaIdentity

Represents a planning-time identity anchor.

Fields:

- `replica_id`
- `display_name`
- `persona_notes`
- `identity_asset_candidates`
- `identity_asset_links`

### 3.2 Wardrobe

Represents a clothing/look asset scoped to a replica.

Fields:

- `wardrobe_id`
- `replica_id`
- `look_label`
- `asset_candidates`
- `asset_links`

### 3.3 HandProp

Represents a hand-held or action-relevant object.

Fields:

- `prop_id`
- `display_name`
- `usage_notes`
- `asset_candidates`
- `asset_links`

### 3.4 RoleBinding

Represents assignment of a replica identity into a scenario role.

Fields:

- `role_binding_id`
- `role_name`
- `replica_id`
- `wardrobe_id`
- `default_prop_ids`
- `status`

### 3.5 ShotBinding

Represents shot-scoped use of a role and assets.

Fields:

- `shot_binding_id`
- `shot_id`
- `role_binding_ids`
- `prop_ids`
- `camera_action_hint`
- `motion_hint`
- `candidate_asset_refs`
- `linked_asset_refs`

## 4. Candidate vs Linked Asset State

### 4.1 Candidate

Candidate assets are:

- inferred
- proposed
- reviewable
- replaceable

Required fields:

- `candidate_id`
- `asset_type`
- `scope_type`
- `scope_id`
- `evidence`
- `confidence`

### 4.2 Linked

Linked assets are:

- accepted for planning use
- stable enough to feed later execution
- still not treated as final business truth

Required fields:

- `link_id`
- `asset_ref`
- `scope_type`
- `scope_id`
- `linked_from_candidate_id`
- `accepted_by`

## 5. Usage Scope Model

Planning assets must support scoped usage.

Allowed usage scopes:

- `line`
- `role`
- `shot`

This supports:

- persistent identity across shots
- wardrobe changes between shots
- prop changes between shots

## 6. Mapping To Future Execution

Planning assets may later feed:

- prompt template inputs
- reference image sets
- worker gateway requests
- shot generation intents

But the mapping step must be explicit.

Planning assets must not silently become execution truth.

## 7. File Usage Index Hook

Action Replica planning assets must support file-usage indexing hooks consistent with the script-video planning contract.

Minimum fields:

- `usage_id`
- `scope_type`
- `scope_id`
- `asset_ref`
- `usage_role`

Allowed usage roles:

- `identity_reference`
- `wardrobe_reference`
- `prop_reference`
- `shot_reference`
- `prompt_input`

## 8. Truth Ownership Boundary

Planning assets may own:

- candidate state
- linked planning references
- review notes
- usage indexes

Planning assets may not directly own:

- final task status
- final deliverable keys
- publish truth
- asset sink truth
- ready-gate truth

## 9. Current Phase-2 Runtime Baseline Reference

Current code-level baseline reference:

- `gateway/app/services/planning/action_replica_planning.py`
- `gateway/app/services/planning/__init__.py`

The current runtime scope is intentionally limited to:

- planning asset objects
- role / shot binding structures
- line-scoped usage index hooks
- mapping skeleton to future execution needs

## 10. Explicit Non-Goals

This contract does not authorize:

- a giant action-replica workbench UI
- a direct generator overhaul
- importing studio project/chapter shell
- direct image/video generation from planning docs in the same PR
