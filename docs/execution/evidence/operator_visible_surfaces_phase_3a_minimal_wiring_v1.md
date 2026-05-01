# Evidence: Operator-Visible Surfaces Phase 3A — Minimal Wiring v1

Date: 2026-05-01
For: Phase 3A minimal surface wiring (Board / Workbench / Delivery / Hot Follow panel)
Authority cited: `docs/reviews/operator_visible_surface_wiring_feasibility_v1.md`,
`docs/reviews/architect_phase2_lowfi_review_v1.md`,
`docs/design/ApolloVeo_Operator_Visible_Surfaces_v1.md`

## What landed

A single new additive-projection module that the four operator-visible
surfaces consume. No truth moved, no packet mutation, no UI implementation,
no B-roll wiring.

Files added:

- `gateway/app/services/operator_visible_surfaces/__init__.py`
- `gateway/app/services/operator_visible_surfaces/projections.py`
- `tests/contracts/operator_visible_surfaces/__init__.py`
- `tests/contracts/operator_visible_surfaces/test_projections.py`

No existing files were modified. The three additive projections derive
from data already produced by:

- `gateway/app/services/contract_runtime/ready_gate_runtime.py`
  (`ready_gate.publish_ready`, `ready_gate.compose_ready`,
   `ready_gate.blocking[]`, `ready_gate.compose_reason`)
- `gateway/app/services/status_policy/hot_follow_state.py`
  (L2 `final.exists`, `final_stale_reason`)
- `gateway/app/services/matrix_script/publish_feedback_closure.py`
  and `gateway/app/services/digital_anchor/publish_feedback_closure.py`
  (task-side closure records — read-only)
- packet `line_specific_refs[]` per
  `schemas/packets/matrix_script/packet.schema.json` and
  `schemas/packets/digital_anchor/packet.schema.json`

## Projection-gap closure map

| Gap (per memo §5) | API in `operator_visible_surfaces.projections` | Inputs | Output keys |
| --- | --- | --- | --- |
| A1 — per-packet `publishable` boolean | `derive_board_publishable(ready_gate)` | `ready_gate.*` | `publishable`, `head_reason` |
| A2 — single derived Delivery publish gate | `derive_delivery_publish_gate(ready_gate, l2_facts)` | `ready_gate.*` + L2 `final.exists` / `final_stale_reason` | `publish_gate`, `publish_gate_head_reason` |
| A3 — Delivery last-publish-status mirror | `derive_delivery_publish_status_mirror(closure)` | task-side `publish_feedback_closure_v1` shape | `last_published_at`, `publish_status`, `publish_url`, `publish_channel` |
| Workbench mount resolver | `resolve_line_specific_panel(packet)` + `PANEL_REF_DISPATCH` | packet `line_specific_refs[].ref_id` | `panel_kind`, `refs[]` |

`PANEL_REF_DISPATCH` enumerates exactly the six frozen ref_ids from the
architect review §"Engineering Wiring Confirmation Items" item 3:

```
matrix_script_variation_matrix    -> matrix_script
matrix_script_slot_pack           -> matrix_script
digital_anchor_role_pack          -> digital_anchor
digital_anchor_speaker_plan       -> digital_anchor
hot_follow_subtitle_authority     -> hot_follow
hot_follow_dub_compose_legality   -> hot_follow
```

A combined entry point `project_operator_surfaces(...)` returns one payload
shape per surface — `board`, `workbench.line_specific_panel`,
`delivery.publish_gate`, `delivery.publish_status_mirror`,
`hot_follow_panel.{mounted, refs}` — and is what Phase 3B UI wiring would
read against.

## Red lines verified

- **No vendor / model / provider / engine / raw provider route in operator
  payload.** `FORBIDDEN_OPERATOR_KEYS` is enforced again at the surface
  boundary by `sanitize_operator_payload(...)`; resolver-emitted ref
  payloads are passed through it. Defense-in-depth on top of validator R3
  at `gateway/app/services/packet/validator.py:202`.
  Test coverage:
  `tests/contracts/operator_visible_surfaces/test_projections.py::test_sanitize_strips_all_forbidden_vendor_keys`,
  `::test_resolver_payload_is_sanitized`.
- **No UI-authored truth.** All four surface fields are derived from inputs
  already produced upstream. Workbench mounts only via
  `line_specific_refs[].ref_id` — the resolver returns `panel_kind=None`
  when no known ref is present (test:
  `::test_resolver_returns_none_when_no_known_ref_id`).
- **No packet truth mutation.** Module is read-only; no functions accept a
  mutable packet handle and no upstream files were edited.
- **No publish-status written onto packet envelope.** Mirror reads only the
  task-side closure (`publish_feedback_closure_v1`); see contract reference
  `docs/contracts/status_ownership_matrix.md:39`. Module signature is
  `closure: Optional[Mapping]` and never returns a packet field.
- **Optional items never block publish.** Test
  `::test_optional_items_never_block_publish_gate` asserts that a missing
  `scene_pack` does not flip `publish_gate` to false when ready_gate +
  final-freshness are otherwise true.
- **No B-roll wiring.** No B-roll surfaces, no B-roll filter API, no
  B-roll Action Area in this module.

## Tests run

```
python3 -m pytest tests/contracts/operator_visible_surfaces/ -q
............................                                             [100%]
28 passed in 0.03s
```

Full contracts regression:

```
python3 -m pytest tests/contracts/ -q
158 passed in 0.29s
```

Test inventory (28 cases):

- Board publishable boolean: 4 cases (clean, blocker, fallback to compose_reason, missing ready_gate)
- Delivery publish gate: 5 cases (open, final missing, final stale, blocker head reason, optional non-blocking)
- Publish-status mirror: 5 cases (no closure, digital_anchor closure, matrix_script aggregate, mixed-pending, failed)
- Workbench resolver: 9 cases (6 parametric ref_id dispatches + unknown ref + missing refs + matrix_script sample + digital_anchor sample)
- Operator-payload hygiene: 2 cases (sanitize, resolver payload sanitized)
- Combined surface projection: 2 cases (digital_anchor end-to-end, hot_follow panel mount)

## What is now wired (backend projection layer)

- **Board** — `publishable` bucket boolean + `head_reason` chip text from
  `derive_board_publishable(ready_gate)`. UI can render `blocked`, `ready`,
  `publishable` directly off `ready_gate.*` plus this projection.
- **Workbench** — single line-specific panel mount via
  `resolve_line_specific_panel(packet)`; dispatches to one of three line
  panel kinds (`matrix_script` / `digital_anchor` / `hot_follow`) on
  `line_specific_refs[].ref_id`. L2 facts strip + L3 `current_attempt` strip
  payloads remain unchanged and are still sourced from
  `gateway/app/services/task_view_presenters.py` and
  `gateway/app/services/contract_runtime/current_attempt_runtime.py`.
- **Delivery** — single derived `publish_gate` boolean + head reason +
  `publish_status_mirror` (last published at / status / channel / url).
  Existing Final / Required / Optional zoning continues to come from
  `factory_delivery_contract` deliverables (per-item `required: bool`),
  unchanged.
- **Hot Follow panel** — `mounted` boolean + matched ref payloads via the
  same Workbench resolver, satisfying the rule that the panel mounts only
  through `line_specific_refs[]`.

## What remains blocked

- B-roll Action Area + B-roll filter API: still blocked on product freeze
  of the seven open questions (`docs/reviews/architect_phase2_lowfi_review_v1.md`
  §"Product Freeze Items"; `docs/design/broll_asset_supply_lowfi_v1.md`).
- Phase 3B (UI wiring): not started in this step. Frontend code is not
  modified. Phase 3B will consume `project_operator_surfaces(...)` once
  commissioning resumes.
- Wiring of these new projections into the live presenter / API response
  shape is intentionally not done in Phase 3A — the projection module is
  shipped as a pure additive surface that Phase 3B can adopt without
  reopening Phase 2 foundations.

## Hard stop

Per the directive, work stops here. No B-roll wiring. Awaiting product
freeze and next commissioning instruction.
