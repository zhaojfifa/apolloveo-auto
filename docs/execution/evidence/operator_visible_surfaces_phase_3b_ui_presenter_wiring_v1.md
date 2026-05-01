# Evidence: Operator-Visible Surfaces Phase 3B — UI / Presenter Minimal Wiring v1

Date: 2026-05-01
For: Phase 3B presenter / API / UI wiring of the four operator-visible
surfaces (Board / Workbench / Delivery / Hot Follow panel) on top of the
Phase 3A projection module.

Authority cited:

- `docs/design/ApolloVeo_Operator_Visible_Surfaces_v1.md`
- `docs/reviews/architect_phase2_lowfi_review_v1.md`
- `docs/reviews/operator_visible_surface_wiring_feasibility_v1.md`
- `docs/design/surface_task_area_lowfi_v1.md`
- `docs/design/surface_workbench_lowfi_v1.md`
- `docs/design/surface_delivery_center_lowfi_v1.md`
- `docs/design/panel_hot_follow_subtitle_authority_lowfi_v1.md`
- `gateway/app/services/operator_visible_surfaces/projections.py`
- `docs/execution/evidence/operator_visible_surfaces_phase_3a_minimal_wiring_v1.md`
- `docs/execution/apolloveo_2_0_evidence_index_v1.md`

## What landed

A pure additive presenter / API / template wiring layer. The Phase 3A
projection module is now read by the live Board, Workbench, and Delivery
presenters; the Hot Follow panel mounts as a Workbench right-rail
surface through the same projection resolver.

Files added:

- `gateway/app/services/operator_visible_surfaces/wiring.py` —
  presenter-side adapter (`build_board_row_projection`,
  `build_operator_surfaces_for_workbench`,
  `build_operator_surfaces_for_publish_hub`) that maps the existing
  task / authoritative-state / closure shapes onto the projection
  module's input contract.
- `tests/contracts/operator_visible_surfaces/test_wiring.py` —
  11 wiring-layer tests.

Files modified:

- `gateway/app/services/operator_visible_surfaces/__init__.py` —
  re-exports the wiring helpers and `project_operator_surfaces`.
- `gateway/app/services/task_router_presenters.py` —
  - `build_tasks_page_rows`: appends `publishable`, `head_reason`, and
    `board_bucket` to every row, derived only from the row's existing
    `ready_gate`.
  - `build_task_workbench_task_json`: appends
    `task_json["operator_surfaces"]` carrying the full
    `project_operator_surfaces(...)` shape so the template can render
    the L3 strip, the line-specific panel mount, and the Hot Follow
    right-rail panel.
- `gateway/app/services/task_view_presenters.py` —
  - `_operator_surfaces_for_publish_hub` helper + `_build_hot_follow_publish_surface_payload`
    appends `operator_surfaces` (publish-gate + publish-status mirror +
    line-specific panel) to the publish-hub payload.
- `gateway/app/templates/tasks.html` — Board bucket legend, per-row
  bucket badge + head-reason chip, bucket filter wired into existing
  `applyFilters()` JS.
- `gateway/app/templates/task_workbench.html` — operator surface strip,
  line-specific panel mount slot, and Hot Follow right-rail panel mount.
- `gateway/app/templates/task_publish_hub.html` — publish-gate strip
  with publish-status mirror plus the
  `renderOperatorSurfaces(data.operator_surfaces || {})` consumer.
- `gateway/app/services/tests/test_task_router_presenters.py` —
  augments existing exact-equality test with the additive Board
  projection keys; adds two new presenter cases for Board projection
  enrichment and Workbench `operator_surfaces` attachment.

Existing documentation indexes updated to record this Phase 3B evidence:

- `docs/execution/logs/PHASE2_PROGRESS_LOG.md`
- `docs/execution/apolloveo_2_0_evidence_index_v1.md`

## Wiring map

| Surface | Live consumer in this wave | Projection input | Projection output rendered |
| --- | --- | --- | --- |
| Board | `build_tasks_page_rows` (`gateway/app/services/task_router_presenters.py`) → `tasks.html` | row `ready_gate` | `publishable` boolean, `head_reason`, `board_bucket` enum (blocked/ready/publishable), bucket filter |
| Workbench L3 strip + panel mount | `build_task_workbench_task_json` → `task_workbench.html` | `task_json` `ready_gate`, `final` / `final_stale_reason`, packet `line_specific_refs[]` | `operator_surfaces.delivery.publish_gate(_head_reason)`, `board.publishable`, `workbench.line_specific_panel.{panel_kind, refs[]}` |
| Delivery (publish hub) | `_build_hot_follow_publish_surface_payload` → `task_publish_hub.html` | `authoritative_state.ready_gate`, `final` / `final_stale_reason`; closure currently `None` | `operator_surfaces.delivery.{publish_gate, publish_gate_head_reason, publish_status_mirror, line_specific_panel}` |
| Hot Follow panel | Workbench right-rail (`task_workbench.html`) | `operator_surfaces.hot_follow_panel.{mounted, refs}` driven by the same resolver | subtitle authority, subtitle source, dub/compose legality, helper explanation (read-only) |

## Tests run

```
python3.11 -m pytest tests/contracts/operator_visible_surfaces/ -q
.......................................                                  [100%]
39 passed
```

(28 Phase 3A projection cases + 11 Phase 3B wiring cases.)

```
python3.11 -m pytest tests/contracts/ -q
.........................................................................
.........................................................................
......................                                                   [100%]
169 passed in 0.13s
```

(no regression vs Phase 3A's 158 contract cases; +11 from this wave.)

```
python3.11 -m pytest gateway/app/services/tests/test_task_router_presenters.py -q
68 passed
```

Wider gateway-services suite was also exercised; one pre-existing
`test_op_download_proxy_uses_attachment_redirect_for_final_video`
failure is reproducible on `main` without these changes (verified by
`git stash`+rerun) and is unrelated to this wave.

## Test inventory (11 new wiring cases)

- Board row projection: 3 cases (open gate → publishable, blocking →
  head_reason, missing ready_gate)
- Workbench bundle: 4 cases (all four surface keys present, hot_follow
  panel mount via packet refs, fallback from task `ready_gate` when
  authoritative state lacks it, packet envelope fallback for
  `line_specific_refs`)
- Publish-hub bundle: 4 cases (final-stale blocks gate, digital_anchor
  closure mirror, optional items never block, vendor-key sanitisation
  through ref payloads)

Plus 2 new presenter-integration cases in
`gateway/app/services/tests/test_task_router_presenters.py`:

- `test_build_tasks_page_rows_attaches_operator_visible_board_projection`
- `test_build_task_workbench_task_json_attaches_operator_surfaces`

## What is now live

- **Board** — Operators see per-row `publishable` boolean, head-reason
  chip, and a Blocked / Ready / Publishable bucket filter on `/tasks`.
  All three are derived from the row's existing `ready_gate`.
- **Workbench** — Operators see the L3 publish-gate strip, board bucket,
  and a line-specific panel mount slot. When a packet exposes a
  `hot_follow_*` ref, the right-rail Hot Follow panel mounts and shows
  subtitle authority, subtitle source, dub/compose legality, and a
  helper line. Existing L2 facts strip and L3 `current_attempt` strip
  data continue to flow from `task_view_presenters.py` /
  `current_attempt_runtime.py` unchanged.
- **Delivery** — Operators see the single derived publish gate, its
  head reason, and the read-only publish-status mirror (status,
  channel, link, last_published_at) above the existing deliverables
  zoning. Final / Required / Optional zoning continues to come from
  `factory_delivery_contract` deliverables; Optional items remain
  visually subordinate and are excluded from publish gating by
  construction.
- **Hot Follow panel** — Mounted as a Workbench right-rail surface only
  when the packet carries `hot_follow_subtitle_authority` or
  `hot_follow_dub_compose_legality`. The panel explains truth only and
  never authors it.

## Red lines preserved

- **No vendor / model / provider / engine / raw_provider_route in any
  operator-visible payload.** `sanitize_operator_payload` remains the
  boundary on ref payloads (covered by
  `tests/contracts/operator_visible_surfaces/test_projections.py::test_resolver_payload_is_sanitized`
  and the new
  `tests/contracts/operator_visible_surfaces/test_wiring.py::test_publish_hub_bundle_never_carries_vendor_keys`).
- **No UI-authored truth.** Templates render only projection output;
  the Workbench line-specific slot stays empty when no known ref_id is
  present (mirrors Phase 3A `panel_kind=None` rule).
- **No packet truth mutation.** The wiring layer accepts `Mapping`
  inputs and returns new dicts; the projection module is unchanged.
- **No publish-status written onto packet envelope.** The Delivery
  mirror reads the task-side closure shape (currently passed as `None`
  on the live Hot Follow path) and returns a flat read-only mirror —
  it never returns a packet field. Per
  `docs/contracts/status_ownership_matrix.md:39`.
- **No recomputation of gate / current-attempt truth in UI.** Templates
  display projection output verbatim.
- **Optional items never block publish.** `scene_pack`, `pack_zip`,
  `edit_bundle_zip`, helper / attribution exports are excluded from
  the gate AND inputs by construction (asserted by
  `test_publish_hub_bundle_optional_items_never_block_gate`).
- **No B-roll wiring.** No B-roll surfaces, no B-roll Action Area, no
  B-roll filter API in this wave.
- **No new page tree.** No Matrix Script / Digital Anchor / Hot Follow
  truth redesign. No W2.2 / W2.3 / third production line expansion.

## What remains blocked

- B-roll Action Area + B-roll filter API: still blocked on product
  freeze of the seven open questions
  (`docs/reviews/architect_phase2_lowfi_review_v1.md`
  §"Product Freeze Items";
  `docs/design/broll_asset_supply_lowfi_v1.md`).
- Platform Runtime Assembly: explicitly not started per directive.
- Live `publish_feedback_closure` materialisation on the Hot Follow
  task surface: pass-through path is wired in
  `_operator_surfaces_for_publish_hub` (the closure parameter is
  accepted and forwarded), but the closure itself is not yet
  surfaced on the live task today; the mirror returns the empty
  `not_published` shape until that materialisation lands. Additive
  follow-up.
- Live mounting of Matrix Script / Digital Anchor line-specific panels
  via real packets: the resolver and template slot are in place;
  production tasks do not carry packets today, so `panel_kind=None` is
  the natural empty result. No truth widening required to enable
  these — only packet attachment to live tasks.

## State sync write-back completed

- `docs/execution/logs/PHASE2_PROGRESS_LOG.md` — appended Phase 3B node
- `docs/execution/apolloveo_2_0_evidence_index_v1.md` — appended Phase 3B
  evidence row

## Hard stop

Per directive, work stops here. No B-roll wiring. No Platform Runtime
Assembly. Awaiting review / next commissioning.
