# L4 Advisory Producer Output Contract v1

Date: 2026-05-02
Status: Plan D contract freeze (Operator-Visible Surface Validation Wave / Operations Upgrade Alignment). Contract-only; **producer implementation lives in Plan E gate**.
Authority:
- `docs/reviews/operations_upgrade_gap_review_and_ops_plan_v1.md` §10.5 + §13 Plan D
- `docs/architecture/ApolloVeo_2.0_Operator_Visible_Surface_Validation_Wave_指挥单_v1.md`
- `docs/contracts/four_layer_state_contract.md`
- `docs/contracts/hot_follow_projection_rules_v1.md` lines 272-335 (frozen advisory taxonomy)
- `docs/contracts/hot_follow_current_attempt_contract_v1.md` (L3 input)
- `docs/contracts/hot_follow_ready_gate.yaml` (L4 ready gate input)
- `docs/contracts/publish_readiness_contract_v1.md` (Plan D sibling — consumes advisory refs)

## Purpose

Pin the **input → output shape** of the future L4 advisory producer. The advisory taxonomy is already frozen at `docs/contracts/hot_follow_projection_rules_v1.md:272-335` (`hf_advisory_translation_waiting_retryable`, `hf_advisory_final_ready`, `hf_advisory_retriable_dub_failure`, `hf_advisory_no_dub_route_terminal`). What is missing per gap review §10.5 is the producer: no service emits these advisories, so Workbench / Publish surfaces cannot consume them.

This contract pins the producer's I/O shape. Implementation lands at `gateway/app/services/operator_visible_surfaces/advisory_emitter.py` when Plan E gate opens.

## Ownership

- Owner: contract layer (Plan D).
- Future runtime producer: `gateway/app/services/operator_visible_surfaces/advisory_emitter.py` (Plan E gate).
- Future runtime consumers: Workbench advisory strip; `publish_readiness_contract_v1`'s `blocking_advisories[]` field; per-line analogues.
- Non-owners: workers, vendor adapters, packet validator, frontend platform, donor modules.

## Function shape

```
emit_advisories(l3_current_attempt, ready_gate) -> list[Advisory]
```

### Inputs

| Input                  | Source layer | Source contract                                                |
| ---------------------- | ------------ | -------------------------------------------------------------- |
| `l3_current_attempt`   | L3           | `docs/contracts/hot_follow_current_attempt_contract_v1.md` (with Plan D `final_provenance` amendment); per-line analogues use the same shape |
| `ready_gate`           | L4           | `docs/contracts/hot_follow_ready_gate.yaml` and per-line analogues |

The producer reads ONLY these two inputs. It MUST NOT read packet truth directly, MUST NOT read L1 step status directly, MUST NOT read L2 facts directly, MUST NOT call workers or storage providers, and MUST NOT mutate any state.

### Output

```
Advisory = {
  id:                        enum (closed; from advisory taxonomy below),
  kind:                      enum: { operator_guidance },
  level:                     enum: { info, warning, error },
  recommended_next_action:   enum (closed; from taxonomy),
  operator_hint:             string (verbatim from taxonomy),
  explanation:               string (verbatim from taxonomy; localized rendering is consumer's job),
  evidence_fields:           list of L3/L4 field names (verbatim from taxonomy)
}
```

The producer returns an **ordered list** of advisories. Order is determined by the advisory_resolution_contract `selection` block at `docs/contracts/hot_follow_projection_rules_v1.md:272-281` — the highest-priority applicable advisory comes first.

### Closed advisory taxonomy (verbatim source)

The closed advisory id set is the union of those declared in `hot_follow_projection_rules_v1.md:272-335`:

```
{
  hf_advisory_translation_waiting_retryable,
  hf_advisory_final_ready,
  hf_advisory_retriable_dub_failure,
  hf_advisory_no_dub_route_terminal
}
```

Each advisory's `kind`, `level`, `recommended_next_action`, `operator_hint`, `explanation`, and `evidence_fields` MUST be reproduced verbatim from the projection rules file. The producer MUST NOT mint a new advisory id, mutate the operator hint, or extend the evidence fields.

## Purity rules (normative)

1. **Pure projection.** The producer reads only `l3_current_attempt` + `ready_gate`. No I/O across runtime boundaries.
2. **No truth invention.** Every emitted advisory MUST be derivable from input fields per the `advisory_resolution_contract` selection rules already frozen in the projection rules file. The producer never invents new emission criteria.
3. **No state mutation.** The producer MUST NOT mutate packet, closure, ready_gate, L3 current attempt, or any side-channel state.
4. **No vendor/model/provider/engine identifier** in inputs, intermediate state, or outputs.
5. **No new advisory codes.** Adding a new advisory requires an additive amendment to `hot_follow_projection_rules_v1.md`'s taxonomy first; this producer contract follows the taxonomy, never leads it.
6. **Cross-line analogues** reuse this same producer shape. Matrix Script and Digital Anchor advisory taxonomies (when authored) will live alongside the Hot Follow taxonomy in the same projection rules file (or a per-line projection rules file with the same shape) and feed the same producer signature.

## Consumer rules (normative)

1. The unified `publish_readiness_contract_v1` consumer reads the producer's output and projects it into `blocking_advisories[]`.
2. Workbench advisory strip reads the producer's output for its rendering.
3. Consumers MUST NOT compute advisories independently; the producer is the single emitter.
4. Consumers MUST NOT mutate the producer's output before rendering (verbatim per advisory taxonomy).

## Forbidden

- new advisory codes outside the frozen taxonomy;
- new evidence_fields outside the frozen list per advisory id;
- vendor / model / provider / engine identifiers anywhere;
- packet, closure, ready_gate, or L3 mutation;
- worker / storage / adapter calls;
- per-surface ad-hoc derivation;
- cross-line invention (no Matrix Script-only or Digital Anchor-only advisory until the corresponding taxonomy lands additively in the projection rules file).

## Validator alignment

- Validator R3: no vendor/model/provider/engine identifier in input/output schema.
- Validator R5: advisories carry no truth-shape state field; `level` is advisory severity, not packet/L3 readiness.
- Cross-check: every emitted `Advisory.id` MUST appear in the closed taxonomy at `hot_follow_projection_rules_v1.md:272-335`.

## Acceptance

This contract is green when:

1. The function shape is exactly `emit_advisories(l3_current_attempt, ready_gate) -> list[Advisory]`.
2. The `Advisory` object shape is the closed shape declared above.
3. The closed advisory id set is exactly the taxonomy at `hot_follow_projection_rules_v1.md:272-335`.
4. Purity rules are binding — no I/O, no mutation, no truth invention.
5. Consumers are bound to read-only consumption — no per-surface derivation.

## What this contract does NOT do

- Does not implement the producer (Plan E only).
- Does not extend the advisory taxonomy.
- Does not author per-line advisory taxonomies.
- Does not change L3 or L4 input contracts.
- Does not unblock Platform Runtime Assembly, Capability Expansion, or frontend patching.

## References

- `docs/contracts/hot_follow_projection_rules_v1.md` (frozen taxonomy at lines 272-335)
- `docs/contracts/hot_follow_current_attempt_contract_v1.md` (L3 input shape)
- `docs/contracts/hot_follow_ready_gate.yaml` (L4 input shape)
- `docs/contracts/publish_readiness_contract_v1.md` (consumer)
- `docs/contracts/four_layer_state_contract.md`
- `docs/reviews/operations_upgrade_gap_review_and_ops_plan_v1.md`
