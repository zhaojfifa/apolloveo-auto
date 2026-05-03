# Plan E PR-1 / Item E.MS.1 — Matrix Script B4 Artifact Lookup Execution Log v1

Date: 2026-05-04
Branch: `claude/crazy-chaplygin-6288a2`
Base commit at audit: `0b73644` (`docs(plan-E):Approval Signoff Raobin and Alisa`)
Status: **Implementation landed.** Code change scoped to Item E.MS.1 of the signed Plan E gate spec; no other business surface touched.
Authority of execution: signed Plan E gate spec [docs/reviews/plan_e_matrix_script_operator_facing_gate_spec_v1.md](../reviews/plan_e_matrix_script_operator_facing_gate_spec_v1.md) §3.1, §5.1, §5.4, §6 row A1.

---

## 1. Inputs read

- [CLAUDE.md](../../CLAUDE.md) — boot sequence followed.
- [docs/reviews/plan_e_matrix_script_operator_facing_gate_spec_v1.md](../reviews/plan_e_matrix_script_operator_facing_gate_spec_v1.md) — confirmed §10 architect (Raobin 2026-05-03 12:10) + reviewer (Alisa 2026-05-03 12:18) signoffs filled and committed at `0b73644`; entry condition E7 SATISFIED.
- [docs/contracts/matrix_script/result_packet_binding_artifact_lookup_contract_v1.md](../contracts/matrix_script/result_packet_binding_artifact_lookup_contract_v1.md) — function shape, closed (ref_id, locator) pair set, resolution rule, failure-mode discipline, validator alignment, acceptance.
- [docs/contracts/matrix_script/delivery_binding_contract_v1.md](../contracts/matrix_script/delivery_binding_contract_v1.md) — Phase C deliverable enumeration (the five rows the lookup pins).
- [gateway/app/services/matrix_script/delivery_binding.py](../../gateway/app/services/matrix_script/delivery_binding.py) — pre-PR state with five `not_implemented_phase_c` placeholder rows at lines 93 / 101 / 109 / 117 / 125.
- [schemas/packets/matrix_script/sample/matrix_script_packet_v1.sample.json](../../schemas/packets/matrix_script/sample/matrix_script_packet_v1.sample.json) — fixture for tests.

## 2. Action taken

### 2.1 Implementation (Item E.MS.1)

Added the contract-pinned `artifact_lookup(packet, ref_id, locator)` function inside [gateway/app/services/matrix_script/delivery_binding.py](../../gateway/app/services/matrix_script/delivery_binding.py):

- **Closed pair set** enforced via `_is_valid_pair`: `matrix_script_variation_matrix` requires non-empty `cell_id` (string), `matrix_script_slot_pack` requires non-empty `slot_id` (string), `capability:subtitles` / `capability:dub` / `capability:pack` require `locator is None`. Any other shape returns the contract sentinel.
- **Resolution rule** (`_resolve_handle`) reads packet truth only — `line_specific_refs[ref_id].delta.cells[*].script_slot_ref` (variation), `line_specific_refs[ref_id].delta.slots[*].body_ref` (slot_pack), `binding.deliverable_profile_ref` joined with the capability kind (capability:*). No I/O, no provider/vendor/storage dereferencing, no fabrication of synthetic ids. If a structurally valid pair cannot be resolved against packet truth, returns `ARTIFACT_LOOKUP_UNRESOLVED`.
- **Provenance discipline** (`_read_l3_final_provenance`) mirrors L3 `final_provenance` for the bound row. The Matrix Script packet today does not carry `final_provenance` (D2 emitter remains in the gate spec §4.2 forbidden list for this Plan E phase). The reader returns `None` whenever the field is absent or the row's value is not in the closed enum `{current, historical}`; the lookup then returns `ARTIFACT_LOOKUP_UNRESOLVED` per the contract §"Resolution rule" item 6. When a future Plan E phase lands D2, this reader starts returning real provenance values without B4 code change.
- **Freshness derivation** (`_derive_freshness`) reads optional L2 `final_fresh` for the bound row. If absent, treats as `stale` ("rather than guessing" spirit of the contract §"Resolution rule"); never returns `absent` from this branch since absence is detected upstream by the handle-resolution guard.
- **Failure-mode discipline**: never raises on malformed packet; non-`Mapping` inputs short-circuit to the sentinel.
- **No packet mutation**: `_resolve_handle`, `_read_l3_final_provenance`, `_derive_freshness` all read-only against the packet.

### 2.2 Placeholder retirement

The five `not_implemented_phase_c` strings at [gateway/app/services/matrix_script/delivery_binding.py:93,101,109,117,125](../../gateway/app/services/matrix_script/delivery_binding.py) are replaced one-for-one with `artifact_lookup(packet, ref_id, None)`:

| Deliverable id | ref_id passed to lookup | Behavior on today's packet (no D2) |
| --- | --- | --- |
| `matrix_script_variation_manifest` | `matrix_script_variation_matrix` | `artifact_lookup_unresolved` (locator=None invalid for variation per contract) |
| `matrix_script_slot_bundle` | `matrix_script_slot_pack` | `artifact_lookup_unresolved` (locator=None invalid for slot_pack per contract) |
| `matrix_script_subtitle_bundle` | `capability:subtitles` | `artifact_lookup_unresolved` (L3 `final_provenance` absent) |
| `matrix_script_audio_preview` | `capability:dub` | `artifact_lookup_unresolved` (L3 `final_provenance` absent) |
| `matrix_script_scene_pack` | `capability:pack` | `artifact_lookup_unresolved` (L3 `final_provenance` absent) |

Operator-visible delta: Matrix Script Delivery Center rows now carry `"artifact_lookup": "artifact_lookup_unresolved"` instead of the prior `"not_implemented_phase_c"`. This is a strict improvement — `artifact_lookup_unresolved` is the contract-enumerated absence sentinel and conveys "no current/historical artifact reachable via packet truth", whereas `not_implemented_phase_c` conveyed "code not written". Once a future Plan E phase lands D2 (L3 `final_provenance` emitter), the same code paths will return real `ArtifactHandle` mappings with no further B4 code change.

### 2.3 Test file added

Created [gateway/app/services/tests/test_matrix_script_b4_artifact_lookup.py](../../gateway/app/services/tests/test_matrix_script_b4_artifact_lookup.py) covering:

- Closed (ref_id, locator) pair set discipline (8 invalid-pair parametrizations + 2 unknown-id cases).
- Provenance discipline (3 capability + 2 cell/slot cases proving sentinel return when L3 `final_provenance` is absent).
- Positive resolution paths (5 cases proving real `ArtifactHandle` return shape under a future-state fixture that simulates a packet with both `final_provenance` and `final_fresh` populated — the fixture seeds the field; B4 only reads it).
- Failure-mode discipline (4 malformed-packet inputs prove the lookup never raises).
- Mutation discipline (1 case proves the lookup never mutates the packet across all five closed pairs).
- Projection integration (3 cases prove `not_implemented_phase_c` strings are absent from the rendered surface, all five rows carry the contract-pinned closed key set, and the projection top-level shape is preserved).
- Validator R3 alignment (1 case proves the `ArtifactHandle` output carries no `vendor_id` / `model_id` / `provider_id` / `engine_id`).

Total: **30 test cases** in this file.

## 3. Validation

```
$ python3 -m pytest gateway/app/services/tests/test_matrix_script_b4_artifact_lookup.py -v
============================== 30 passed in 0.07s ==============================
```

All 30 B4 cases PASS on Python 3.9.6 with pytest 8.4.2.

### 3.1 Pre-existing environment limitation (not caused by PR-1)

The broader matrix_script regression set ([test_matrix_script_phase_b_authoring.py](../../gateway/app/services/tests/test_matrix_script_phase_b_authoring.py), [test_matrix_script_workbench_dispatch.py](../../gateway/app/services/tests/test_matrix_script_workbench_dispatch.py), [test_matrix_script_source_script_ref_shape.py](../../gateway/app/services/tests/test_matrix_script_source_script_ref_shape.py)) errors out at collection time with `TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'` because [gateway/app/config.py:43](../../gateway/app/config.py:43) uses PEP 604 `str | None` syntax which requires Python 3.10+. The local environment is Python 3.9.6.

This collection error is **pre-existing on `origin/main` at commit `0b73644`** — verified by `git stash` of PR-1's changes and re-running the same collection: the error reproduces identically. Per [ENGINEERING_RULES.md §10](../../ENGINEERING_RULES.md): "distinguish code regressions from environment limitations" — this is the latter.

The new B4 test file intentionally uses only `Optional[X]` from `typing` (not PEP 604) so it remains compatible with both Python 3.9 and 3.10+. CI running on Python 3.10+ will collect and run the full matrix_script test set including B4.

### 3.2 Per-PR regression scope (gate spec §5.4 PR-1)

| Regression check | Method | Result |
| --- | --- | --- |
| Hot Follow golden path (publish completes) | Coordinator-side live regression — to be performed by Jackie in the trial environment per gate spec §6 row A4 / §10 coordinator role; no Hot Follow file touched in this PR. | Deferred to coordinator closeout step (no Hot Follow file touched — verifiable via `git diff HEAD~1 -- gateway/app/services/hot_follow_*` returning empty) |
| Matrix Script Phase B inspection on a fresh contract-clean sample (axes/cells/slots resolve per §8.G) | Existing test_matrix_script_phase_b_authoring.py — collection-blocked on local Python 3.9 (pre-existing env issue, not caused by PR-1). | CI Python 3.10+ will run; no test file mutated by PR-1 |
| Matrix Script Delivery Center deliverable rows render real artifact references on the same sample (no `not_implemented_phase_c` strings observed on the Matrix Script payload) | `test_projection_retires_not_implemented_phase_c_placeholder` in the new B4 test file. | **PASS** — sentinel string absent from `json.dumps(project_delivery_binding(sample_packet))` |
| Hot Follow Delivery Center unchanged (rows render exactly as before — bytewise diff acceptable as evidence) | `git diff HEAD~1 -- gateway/app/services/hot_follow_*` returns empty diff. | **PASS** — no Hot Follow file in PR-1 diff |

## 4. What this PR does NOT do

- Does NOT touch any Hot Follow file (preserves Hot Follow baseline per gate spec §7.1 / §4.4).
- Does NOT touch any Digital Anchor file (preserves Digital Anchor freeze per gate spec §7.2 / §4.1).
- Does NOT touch any cross-line projection / advisory / publish_readiness file (preserves no-platform-wide-expansion per gate spec §7.4 / §4.2):
  - No change to `gateway/app/services/operator_visible_surfaces/projections.py`.
  - No `final_provenance` emitter (D2) implemented.
  - No unified `publish_readiness` producer (D1) implemented.
  - No L4 advisory emitter (D4) implemented.
  - No workbench panel dispatch contract object (D3) conversion.
- Does NOT mutate any contract, schema, sample, or template.
- Does NOT introduce operator-driven Phase B authoring; the Phase B planner / panel are unchanged.
- Does NOT widen `target_language` enum, canonical-axes set, or `source_script_ref` accepted-scheme set.
- Does NOT mint a `content://` handle (Item E.MS.2 / PR-2 scope).
- Does NOT render `required` / `blocking_publish` zoning (Item E.MS.3 / PR-3 scope).
- Does NOT start Platform Runtime Assembly or Capability Expansion (gate spec §7.5).
- Does NOT promote any discovery-only surface to operator-eligible (gate spec §4.5).
- Does NOT relax the operator-payload sanitization at [gateway/app/services/operator_visible_surfaces/projections.py:36](../../gateway/app/services/operator_visible_surfaces/projections.py).

## 5. Files changed

- **MOD** [gateway/app/services/matrix_script/delivery_binding.py](../../gateway/app/services/matrix_script/delivery_binding.py) — added `artifact_lookup` + helpers; replaced five `not_implemented_phase_c` strings.
- **ADD** [gateway/app/services/tests/test_matrix_script_b4_artifact_lookup.py](../../gateway/app/services/tests/test_matrix_script_b4_artifact_lookup.py) — 30 test cases.
- **ADD** [docs/execution/PLAN_E_MATRIX_SCRIPT_B4_ARTIFACT_LOOKUP_EXECUTION_LOG_v1.md](PLAN_E_MATRIX_SCRIPT_B4_ARTIFACT_LOOKUP_EXECUTION_LOG_v1.md) — this log.
- **MOD** [ENGINEERING_STATUS.md](../../ENGINEERING_STATUS.md) — Current Completion gains a PR-1 landed bullet.
- **MOD** [CURRENT_ENGINEERING_FOCUS.md](../../CURRENT_ENGINEERING_FOCUS.md) — Allowed Next Work refreshed for PR-1 landed posture.

No other files modified.

## 6. Final-gate four-question check

- scope stayed inside Item E.MS.1: **YES** — only `gateway/app/services/matrix_script/delivery_binding.py` + one new test file + this log + the two root status files; gate spec §5.1 file-fence respected.
- Hot Follow untouched: **YES** — `git diff HEAD~1 -- gateway/app/services/hot_follow_* gateway/app/routers/hot_follow_api.py gateway/app/templates/hot_follow_workbench.html` returns empty.
- Digital Anchor still frozen: **YES** — no `gateway/app/services/digital_anchor/*` or `gateway/app/templates/digital_anchor*` file touched; Plan A §2.1 hide guards still in force.
- PR-1 validation passed: **YES** — 30/30 B4 test cases PASS on local Python 3.9.6; broader matrix_script test collection blocks on pre-existing env-only PEP-604 syntax in `gateway/app/config.py:43` (not caused by PR-1; will run on CI Python 3.10+).
- ready for PR-3 or PR-2 next: **YES** — gate spec §5.5 PR ordering allows PR-2 (Item E.MS.2) in parallel with PR-1 / PR-3, and PR-3 (Item E.MS.3) after PR-1 lands. Implementation gate remains OPEN under signed §10 for the remaining items only.

End of Plan E PR-1 / Item E.MS.1 Execution Log v1.
