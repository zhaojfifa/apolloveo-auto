# Factory Delivery Contract v1

Date: 2026-04-24
Status: Baseline draft above frozen Hot Follow

## Purpose

Define the factory-generic object that describes accepted delivery outputs,
their readiness semantics, and the relationship between primary delivery truth
and optional derivative outputs.

## Ownership

- contract owner: factory contract layer
- runtime consumers: line deliverable profiles, ready-gate evaluation, delivery
  center
- non-owners: workers, presenters, optional derivative generators

## Required Inputs

- line contract reference
- accepted deliverable profile
- current artifact facts
- current-attempt state
- ready-gate output

## Allowed Outputs

- delivery object with primary and secondary deliverables
- current vs historical delivery distinction
- publishability declaration
- optional derivative visibility policy
- delivery validation results

## Validation Rules

- primary delivery truth must dominate optional derivative state
- historical output may be visible but must not satisfy current-ready truth
- optional pack / scene-pack / archive outputs may remain non-blocking when the
  current final delivery is fresh and publishable
- delivery center must consume shared authoritative truth instead of inventing a
  second readiness path

## Per-Deliverable Required / Blocking Fields (Plan D Amendment)

Every deliverable row in a line's delivery binding MUST carry the following two
explicit fields, in addition to its `kind`:

- `required: boolean` — true when the line cannot reach `ready` without this
  deliverable kind being declared and reachable; false when the deliverable is
  optional. Mirrors the `required` column in
  `docs/product/asset_supply_matrix_v1.md` §"Matrix · line-produced
  deliverables".
- `blocking_publish: boolean` — true when this deliverable's absence or
  staleness contributes to `ready_gate.blocking[]` and therefore prevents the
  unified `publish_readiness_contract_v1` consumer from emitting
  `publishable=true`. Optional derivatives (scene_pack, archive, pack_zip, etc.)
  MUST carry `blocking_publish=false`.

Validator rules:

- A row with `required=true` MAY carry either `blocking_publish=true` or
  `blocking_publish=false` depending on the line's policy (e.g. subtitle bundle
  may be required for delivery completeness yet not block publish in some line
  policies). The mapping is line-specific and is owned by the line's delivery
  binding contract; this generic contract pins the field shape only.
- A row with `required=false` MUST carry `blocking_publish=false`. A row that is
  not required cannot block publish.
- Surfaces (Board / Workbench / Delivery) MUST consume the `blocking_publish`
  field via the unified `publish_readiness_contract_v1` projection rather than
  re-derive blocking semantics from `kind`.

## Scene-Pack Non-Blocking Rule (Explicit; Plan C Amendment)

Per the gap review §10.4 and Plan C §C4: scene-pack non-blocking is **explicit
contract truth**, not implicit absence. Every line packet MUST satisfy:

- `scene_pack_blocking_allowed: false` — declared at the delivery contract
  layer (this section). Any line packet that asserts `blocking_publish=true` on
  a deliverable row whose `kind` is `scene_pack` (or any descendant kind such
  as `scene_pack_ref`) fails validation.
- The `scene_pack` row, when present in a line's delivery binding, MUST carry
  `required=false` AND `blocking_publish=false`.
- The packet validator MUST reject any line packet that adds `scene_pack` to
  `ready_gate.blocking[]`.

This rule is normative across all lines (Hot Follow, Matrix Script, Digital
Anchor) and applies to any future line. Adding a new derivative kind that
should follow scene-pack semantics requires an additive amendment to this
contract; donor or runtime modules MUST NOT bypass the rule.

## Relation To Four-Layer State

- L1: publish/pack/scenes steps report execution only
- L2: delivery artifacts are factual existence and freshness truth
- L3: publish-ready and delivery-currentness derive from L2 plus route state
- L4: workbench/delivery center surface delivery truth after ready-gate
  evaluation

## Relation To Line Runtime

Each line binds the generic delivery contract to a line-specific deliverable
profile and readiness policy, but must preserve the primary-vs-optional
distinction.

## Relation To Workbench And Delivery Center

- workbench shows operator-safe delivery state
- delivery center exposes accepted deliverables and historical outputs
- both must consume the same authoritative projection path

## Factory-Generic Vs Line-Specific

Factory-generic:

- delivery object shape
- current vs historical distinction
- primary vs optional derivative precedence
- delivery validation vocabulary

Line-specific:

- exact deliverable kinds
- required vs optional outputs per route
- publish confirmation hooks
- sink/export profiles
