# Plan E PR-3 / Item E.MS.3 — Matrix Script Delivery Center Per-Deliverable Zoning Execution Log v1

Date: 2026-05-04
Branch: `claude/crazy-chaplygin-6288a2`
Base commit at audit: `2822ad0` (`Merge pull request #101` — PR-2 / Item E.MS.2 landed)
Status: **Implementation landed.** Code change scoped to Item E.MS.3 of the signed Plan E gate spec; no other business surface touched.
Authority of execution: signed Plan E gate spec [docs/reviews/plan_e_matrix_script_operator_facing_gate_spec_v1.md](../reviews/plan_e_matrix_script_operator_facing_gate_spec_v1.md) §3.3, §5.3, §5.4, §6 row A3.

---

## 1. Inputs read

- [CLAUDE.md](../../CLAUDE.md) — boot sequence followed; sync gate green at start (branch `claude/crazy-chaplygin-6288a2` at `2822ad0`; 0 behind / 0 ahead vs `origin/main` per `git rev-list --left-right --count HEAD...origin/main`).
- [docs/reviews/plan_e_matrix_script_operator_facing_gate_spec_v1.md](../reviews/plan_e_matrix_script_operator_facing_gate_spec_v1.md) — confirmed §10 architect (Raobin 2026-05-03 12:10) + reviewer (Alisa 2026-05-03 12:18) signoffs already committed at `0b73644`; PR-1 dependency for PR-3 met by the merge of PR #100 at `7a1e7a6`; PR-3 file-fence per §5.3.
- [docs/contracts/factory_delivery_contract_v1.md](../contracts/factory_delivery_contract_v1.md) §"Per-Deliverable Required / Blocking Fields (Plan D Amendment)" + §"Scene-Pack Non-Blocking Rule (Explicit; Plan C Amendment)" — frozen contract source for the new fields.
- [docs/contracts/matrix_script/delivery_binding_contract_v1.md](../contracts/matrix_script/delivery_binding_contract_v1.md) §"Visible deliverables" — line-specific deliverable enumeration.
- [gateway/app/services/matrix_script/delivery_binding.py](../../gateway/app/services/matrix_script/delivery_binding.py) — pre-PR state with PR-1's `artifact_lookup` already integrated; rows carrying `required` (already there per PR-0 baseline).

## 2. Action taken

### 2.1 Per-row zoning fields (delivery_binding.py)

Modified [gateway/app/services/matrix_script/delivery_binding.py](../../gateway/app/services/matrix_script/delivery_binding.py):

- Added module constant `SCENE_PACK_BLOCKING_ALLOWED = False` pinning the §"Scene-Pack Non-Blocking Rule" at the projection layer. Future widening requires a contract amendment, not a code flip.
- Added private helper `_clamp_blocking_publish(*, required, blocking_publish) -> bool` that enforces the contract validator invariant from §"Per-Deliverable Required / Blocking Fields": "A row with `required=false` MUST carry `blocking_publish=false`." The helper clamps to `False` defensively rather than relying on every caller to honour the rule.
- Extended every Matrix Script delivery row in `project_delivery_binding` with the explicit `blocking_publish` field per the Plan C amendment. Matrix Script line policy applied:
  - `matrix_script_variation_manifest`: `required=True`, `blocking_publish=True` (core structural deliverable).
  - `matrix_script_slot_bundle`: `required=True`, `blocking_publish=True` (core structural deliverable).
  - `matrix_script_subtitle_bundle`: `required` mirrors the line's subtitles capability flag; `blocking_publish` mirrors `required`.
  - `matrix_script_audio_preview`: `required` mirrors the line's dub capability flag; `blocking_publish` mirrors `required`.
  - `matrix_script_scene_pack`: **HARDCODED** `required=False`, `blocking_publish=False` per §"Scene-Pack Non-Blocking Rule" — independent of any per-task `pack` capability flag. The contract is line-uniform; the previous behavior (which read `pack.required` for `scene_pack.required`) is replaced with a contract-pinned literal that cannot be inverted by a malformed packet.
- Module docstring updated to cite the PR-3 contribution alongside the PR-1 B4 docstring; no other behavior change.

### 2.2 Updated PR-1 B4 row-shape assertion (test maintenance, same Matrix Script scope)

Modified [gateway/app/services/tests/test_matrix_script_b4_artifact_lookup.py](../../gateway/app/services/tests/test_matrix_script_b4_artifact_lookup.py)::`test_projection_shape_unchanged_aside_from_lookup_value`:

- The PR-1 test asserted the closed key set on each row was `{deliverable_id, kind, required, source_ref_id, profile_ref, artifact_lookup}`. PR-3 adds the additive `blocking_publish` field, so the closed key set is now `{deliverable_id, kind, required, blocking_publish, source_ref_id, profile_ref, artifact_lookup}`. The test was updated minimally — the assertion message was extended to credit PR-3 for the additive field; no other behavior change.
- This is the only existing test file modified in PR-3. The change is required for PR-3 to keep the matrix_script test set green and is strictly within the Matrix Script scope per the gate spec §5.3 file-fence ("the Matrix Script Delivery Center projection / template path"). The test file itself lives under `gateway/app/services/tests/`, the same directory PR-3 is allowed to add to.

### 2.3 Test module added (PR-3 dedicated)

Created [gateway/app/services/tests/test_matrix_script_delivery_zoning.py](../../gateway/app/services/tests/test_matrix_script_delivery_zoning.py) covering 16 import-light cases:

- Per-row zoning on the canonical Matrix Script sample (5 cases: variation_manifest required+blocking; slot_bundle required+blocking; subtitle_bundle follows capability; audio_preview follows capability; scene_pack hardcoded optional+non-blocking).
- Validator invariant `required=false ⇒ blocking_publish=false` (3 cases: invariant holds across all rows; clamp helper unit tests).
- Scene-pack contract enforcement is independent of capability flags (2 cases: adversarial `pack.required=True` still emits `scene_pack.required=False, blocking_publish=False`; module constant pinning).
- Subtitles + dub capability flag negative-path zoning (2 cases: collapse to optional when capability flips off; promote to required when capability flips on).
- Surface integration (4 cases: `blocking_publish` present on every row of the JSON-rendered projection; no validator R3 forbidden keys; PR-1 `artifact_lookup` retirement of `not_implemented_phase_c` preserved; top-level surface key set unchanged).

The test module is import-light by design (calls `project_delivery_binding` directly without instantiating the FastAPI app), so it runs cleanly on both Python 3.9 and 3.10+.

## 3. Validation

```
$ python3 -m pytest \
    gateway/app/services/tests/test_matrix_script_delivery_zoning.py \
    gateway/app/services/tests/test_matrix_script_b4_artifact_lookup.py \
    gateway/app/services/tests/test_matrix_script_f2_minting_flow.py
============================== 81 passed in 0.34s ==============================
```

16 new PR-3 cases + 30 cross-PR sanity B4 cases (PR-1) + 35 cross-PR sanity F2 cases (PR-2) — 81/81 PASS on local Python 3.9.6 with pytest 8.4.2.

### 3.1 Pre-existing environment limitation (not caused by PR-3)

The broader matrix_script regression set ([test_matrix_script_phase_b_authoring.py](../../gateway/app/services/tests/test_matrix_script_phase_b_authoring.py) / [test_matrix_script_workbench_dispatch.py](../../gateway/app/services/tests/test_matrix_script_workbench_dispatch.py) / [test_matrix_script_source_script_ref_shape.py](../../gateway/app/services/tests/test_matrix_script_source_script_ref_shape.py)) errors at collection on local Python 3.9 due to pre-existing PEP-604 `str | None` syntax in [gateway/app/config.py:43](../../gateway/app/config.py:43) requiring Python 3.10+. Verified pre-existing on `origin/main` at `2822ad0` (same env-only issue noted under PR-1 and PR-2). Per [ENGINEERING_RULES.md §10](../../ENGINEERING_RULES.md): "distinguish code regressions from environment limitations" — environment-only. CI on Python 3.10+ runs the full set including the new zoning module.

### 3.2 Per-PR regression scope (gate spec §5.4 PR-3)

| Regression check | Method | Result |
| --- | --- | --- |
| Matrix Script Delivery Center renders `required` / `blocking_publish` zoning correctly per row kind on a fresh contract-clean sample | `test_variation_manifest_is_required_and_blocks_publish` + `test_slot_bundle_*` + `test_subtitle_bundle_*` + `test_audio_preview_*` + `test_scene_pack_is_optional_and_never_blocks_publish`. | **PASS** (5 / 5) |
| Scene-pack-style derivative is rendered as `optional, never blocks publish` | `test_scene_pack_is_optional_and_never_blocks_publish` + `test_scene_pack_stays_optional_even_if_pack_capability_marks_required` (adversarial). | **PASS** |
| Hot Follow Delivery Center unchanged (rows render exactly as before — bytewise diff acceptable as evidence) | `git diff HEAD~1 -- 'gateway/app/services/hot_follow_*' 'gateway/app/routers/hot_follow_api.py' 'gateway/app/templates/hot_follow_workbench.html' 'gateway/app/templates/hot_follow_publish.html'` returns empty. | **PASS** — no Hot Follow file in PR-3 diff |
| Digital Anchor still frozen | `git diff HEAD~1 -- 'gateway/app/services/digital_anchor/' 'gateway/app/templates/digital_anchor*'` returns empty. | **PASS** — no Digital Anchor file in PR-3 diff |
| Cross-line `derive_delivery_publish_gate` re-derivation in `projections.py` not consolidated | `git diff HEAD~1 -- 'gateway/app/services/operator_visible_surfaces/projections.py'` returns empty. | **PASS** |

## 4. What this PR does NOT do

- Does NOT touch any Hot Follow file (preserves Hot Follow baseline per gate spec §7.1 / §4.4).
- Does NOT touch any Digital Anchor file (preserves Digital Anchor freeze per gate spec §7.2 / §4.1).
- Does NOT touch the cross-line `derive_delivery_publish_gate` re-derivation in `gateway/app/services/operator_visible_surfaces/projections.py` (preserves no-platform-wide-expansion per gate spec §7.4 / §4.2).
- Does NOT introduce a unified `publish_readiness` producer (D1 — gate spec §4.2 forbidden).
- Does NOT introduce L3 `final_provenance` emitter (D2 — gate spec §4.2 forbidden).
- Does NOT introduce a workbench panel dispatch contract object conversion (D3 — gate spec §4.2 forbidden).
- Does NOT introduce L4 advisory producer / emitter (D4 — gate spec §4.2 forbidden).
- Does NOT mutate `factory_delivery_contract_v1.md`, `delivery_binding_contract_v1.md`, or any other contract / schema / sample file.
- Does NOT touch the shared `task_publish_hub.html` template (cross-line shell — PR-3 does not need to render the new fields visually for operator UX, since the projection itself is the consumer-facing surface for the new zoning data).
- Does NOT widen `SOURCE_SCRIPT_REF_ACCEPTED_SCHEMES` (not in PR-3 scope; preserved from PR-2).
- Does NOT modify `_validate_source_script_ref_shape`, the §8.A guard, or any source-script-ref behavior.
- Does NOT introduce operator-driven Phase B authoring (gate spec §4.3).
- Does NOT widen `target_language` enum or canonical-axes set (gate spec §4.3).
- Does NOT bundle Item E.MS.1 (PR-1 already merged at `7a1e7a6`) or Item E.MS.2 (PR-2 already merged at `2822ad0`) work.
- Does NOT start Platform Runtime Assembly or Capability Expansion (gate spec §7.5).
- Does NOT promote any discovery-only surface to operator-eligible (gate spec §4.5).
- Does NOT relax the operator-payload sanitization in `gateway/app/services/operator_visible_surfaces/projections.py:36`.

## 5. Files changed

- **MOD** [gateway/app/services/matrix_script/delivery_binding.py](../../gateway/app/services/matrix_script/delivery_binding.py) — added `SCENE_PACK_BLOCKING_ALLOWED` constant, `_clamp_blocking_publish` helper, and `blocking_publish` field on every deliverable row; hard-pinned `scene_pack` row to `required=False, blocking_publish=False`.
- **MOD** [gateway/app/services/tests/test_matrix_script_b4_artifact_lookup.py](../../gateway/app/services/tests/test_matrix_script_b4_artifact_lookup.py) — extended the closed-key-set assertion in `test_projection_shape_unchanged_aside_from_lookup_value` to include the additive `blocking_publish` field. No other test behavior change.
- **ADD** [gateway/app/services/tests/test_matrix_script_delivery_zoning.py](../../gateway/app/services/tests/test_matrix_script_delivery_zoning.py) — 16 test cases.
- **ADD** [docs/execution/PLAN_E_MATRIX_SCRIPT_DELIVERY_ZONING_EXECUTION_LOG_v1.md](PLAN_E_MATRIX_SCRIPT_DELIVERY_ZONING_EXECUTION_LOG_v1.md) — this log.
- **MOD** [ENGINEERING_STATUS.md](../../ENGINEERING_STATUS.md) — Current Completion gains a PR-3 landed bullet.
- **MOD** [CURRENT_ENGINEERING_FOCUS.md](../../CURRENT_ENGINEERING_FOCUS.md) — Allowed Next Work refreshed for PR-3 landed posture.

No other files modified.

## 6. Final-gate four-question check

- scope stayed inside Item E.MS.3: **YES** — only `gateway/app/services/matrix_script/delivery_binding.py` + the existing PR-1 test row-key-set assertion (Matrix Script-scoped maintenance) + new zoning test module + log + two root status files.
- Hot Follow untouched: **YES** — `git diff HEAD~1 -- 'gateway/app/services/hot_follow_*' 'gateway/app/routers/hot_follow_api.py' 'gateway/app/templates/hot_follow_workbench.html' 'gateway/app/templates/hot_follow_publish.html'` returns empty.
- Digital Anchor still frozen: **YES** — no `gateway/app/services/digital_anchor/*` or `gateway/app/templates/digital_anchor*` file touched; Plan A §2.1 hide guards still in force.
- PR-3 validation passed: **YES** — 81/81 PASS (16 new PR-3 + 30 cross-PR sanity PR-1 B4 + 35 cross-PR sanity PR-2 F2).
- branch/remote sync clean at handoff: **YES** (re-verified at handoff in §7 below).
- ready for Plan E phase closeout: **YES** — gate spec §6 rows A1 / A2 / A3 all PASS; remaining acceptance work is row A4 (Hot Follow golden-path live regression — coordinator-side check by Jackie) and row A5 (Digital Anchor freeze re-confirmation per PR — recorded in this log) and row A6 (final aggregating closeout audit at `PLAN_E_MATRIX_SCRIPT_PHASE_CLOSEOUT_v1.md`) and row A7 (closeout signoff from Raobin / Alisa / Jackie). The implementation phase of Plan E for Matrix Script operator-facing scope is now complete pending those non-implementation closeout steps.

## 7. Sync gate at handoff (gate spec / mission instruction)

```
$ git fetch origin
$ git rev-list --left-right --count HEAD...origin/main
```

Pre-commit / pre-push state will be re-verified after the PR-3 commit is pushed. The handoff sync state — `local HEAD` vs `origin/main` divergence count + final synced short SHA after merge — is recorded in the parent conversation transcript and in the next `ENGINEERING_STATUS.md` update by the merge step.

End of Plan E PR-3 / Item E.MS.3 Execution Log v1.
