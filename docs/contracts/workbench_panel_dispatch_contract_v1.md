# Workbench Panel Dispatch Contract v1

Date: 2026-05-02
Status: Plan D contract freeze (Operator-Visible Surface Validation Wave / Operations Upgrade Alignment). Contract-only.
Authority:
- `docs/reviews/operations_upgrade_gap_review_and_ops_plan_v1.md` §8.2 + §13 Plan D
- `docs/architecture/ApolloVeo_2.0_Operator_Visible_Surface_Validation_Wave_指挥单_v1.md`
- `docs/design/ApolloVeo_Operator_Visible_Surfaces_v1.md`
- `docs/design/panel_digital_anchor_role_speaker_lowfi_v1.md`
- `docs/design/panel_matrix_script_variation_lowfi_v1.md`
- Reference: `gateway/app/services/operator_visible_surfaces/projections.py:239-246` (today's in-code `PANEL_REF_DISPATCH` dict; this contract pins it as a closed contract object)

## Purpose

Pin the **closed `ref_id → panel_kind` map** the Workbench uses to mount line-specific panels. Today this dispatch is a Python dict at [gateway/app/services/operator_visible_surfaces/projections.py:239](../../gateway/app/services/operator_visible_surfaces/projections.py:239). Per gap review §8.2: "a third line will silently fall off the dispatch" if the map remains in-code only. This contract freezes it as a contract object so any new line MUST appear here before the Workbench may mount its panel.

This contract does not implement the dispatch resolver. It pins the closed map any future implementation MUST honor.

## Ownership

- Owner: contract layer (Plan D).
- Future runtime consumer: `gateway/app/services/operator_visible_surfaces/projections.py::resolve_line_specific_panel()` (Plan E gate; today's in-code map MUST be migrated to consume this contract).
- Non-owners: routers, presenters, frontend, donor modules, packet validator.

## Closed dispatch map

```
ref_id                                  →  panel_kind
----------------------------------------  ----------------
hot_follow_subtitle_authority           →  hot_follow
hot_follow_dub_compose_legality         →  hot_follow
matrix_script_variation_matrix          →  matrix_script
matrix_script_slot_pack                 →  matrix_script
digital_anchor_role_pack                →  digital_anchor
digital_anchor_speaker_plan             →  digital_anchor
```

The map mirrors today's in-code `PANEL_REF_DISPATCH` verbatim (verified against [gateway/app/services/operator_visible_surfaces/projections.py:239-246](../../gateway/app/services/operator_visible_surfaces/projections.py:239)). No entries are invented; no entries are dropped.

### Closed `panel_kind` enum

```
{ hot_follow, matrix_script, digital_anchor }
```

A new `panel_kind` value requires a re-version of this contract AND a new line wave under the master plan; donor / runtime modules MUST NOT add a `panel_kind` ad hoc.

### Closed `ref_id` set

The closed `ref_id` set is exactly the six values above. Adding a new `ref_id` requires:

1. The corresponding line-specific contract to define the ref (e.g. `digital_anchor_role_pack` is defined in `docs/contracts/digital_anchor/role_pack_contract_v1.md`).
2. An additive amendment to this contract listing the new `(ref_id, panel_kind)` pair.
3. The packet schema to declare the ref under `line_specific_refs[]`.

A `ref_id` that appears in a packet but is NOT in this contract MUST cause the resolver to leave the panel slot empty (panel_kind=None), per the existing rule in [gateway/app/services/operator_visible_surfaces/projections.py:259-260](../../gateway/app/services/operator_visible_surfaces/projections.py:259) ("If no known ref_id is present the slot stays empty").

## Closed-by-default rule (normative)

- **No silent extension.** A third line cannot mount a workbench panel without first appearing in this contract.
- **No vendor/model/provider/engine identifier** in `ref_id` or `panel_kind` (validator R3).
- **No state-shape suffix** in `ref_id` (`*_status`, `*_ready`, `*_done` are forbidden — they would imply ref-level state truth, which violates validator R5).
- **One panel_kind per ref_id.** A ref_id MUST NOT dispatch to multiple panel_kinds. A line that needs multi-panel rendering MUST author multiple distinct refs (each with its own `ref_id`).
- **One line per panel_kind.** A `panel_kind` value resolves to exactly one line; cross-line panel sharing is forbidden.

## Resolver shape (informational)

```
resolve_line_specific_panel(packet) -> {
  panel_kind: "hot_follow" | "matrix_script" | "digital_anchor" | null,
  refs:       [ { ref_id: string, ref_payload: Mapping }, ... ]
}
```

The resolver iterates `packet.line_specific_refs[]`, looks up each `ref_id` in this dispatch map, and returns the resolved panel kind plus the matching ref entries. When no known `ref_id` is present, `panel_kind=null` and `refs=[]`.

Resolver discipline:

- pure projection — no packet mutation, no I/O;
- never invents a `panel_kind`;
- never resolves vendor/storage information;
- never carries state-shape fields into its output.

## Forbidden

- new `panel_kind` values without a contract re-version + new line wave;
- new `ref_id` values without the additive amendment chain above;
- vendor / model / provider / engine identifiers anywhere;
- state-shape fields anywhere;
- multi-panel-kind dispatch from a single ref_id;
- cross-line panel sharing.

## Validator alignment

- Validator R3: no vendor/model/provider/engine identifier in any `ref_id` or `panel_kind`.
- Validator R5: no state-shape field in the dispatch map or resolver output.

## Acceptance

This contract is green when:

1. The closed map is exactly the six pairs above; verified against the in-code `PANEL_REF_DISPATCH` at the time of write (`gateway/app/services/operator_visible_surfaces/projections.py:239-246`).
2. The closed `panel_kind` enum is exactly `{hot_follow, matrix_script, digital_anchor}`.
3. The closed-by-default rule is binding: a packet ref_id absent from the map leaves `panel_kind=null`.
4. No forbidden field appears anywhere in the map or resolver output.

## What this contract does NOT do

- Does not implement migration of the in-code map (Plan E only).
- Does not author panel rendering logic.
- Does not introduce a third line.
- Does not unblock Platform Runtime Assembly, Capability Expansion, or frontend patching.

## References

- `docs/design/panel_digital_anchor_role_speaker_lowfi_v1.md`
- `docs/design/panel_matrix_script_variation_lowfi_v1.md`
- `docs/design/panel_hot_follow_lowfi_v1.md` (if present; otherwise reference to surface design)
- `docs/contracts/digital_anchor/role_pack_contract_v1.md`
- `docs/contracts/digital_anchor/speaker_plan_contract_v1.md`
- `docs/contracts/matrix_script/variation_matrix_contract_v1.md`
- `docs/contracts/matrix_script/slot_pack_contract_v1.md`
- `gateway/app/services/operator_visible_surfaces/projections.py` (read-only reference)
- `docs/reviews/operations_upgrade_gap_review_and_ops_plan_v1.md`

## Shared shell neutrality (addendum, 2026-05-03)

Authority: `docs/reviews/matrix_script_followup_blocker_review_v1.md` §5
(§8.E — Workbench Shell Suppression).

The dispatch map above governs `(ref_id → panel_kind)` mounting only.
The shared workbench shell that hosts the mounted panel is **line-neutral**:
the shell MUST NOT render line-specific stage controls, deliverable
strips, pipeline summaries, dub-engine selectors, voice picks, subtitle-
track meta rows, or per-line publish-flow CTAs alongside a panel of a
different `panel_kind`. Line-specific controls render only inside the
panel block selected by `panel_kind` (and only inside that block).

This rule:

- is presentation-layer discipline; it does not widen the closed map,
  add a new `ref_id`, add a new `panel_kind`, or change resolver shape;
- is asserted at the template surface (`gateway/app/templates/task_workbench.html`,
  the shared/default workbench shell); the implementation gates each
  Hot Follow-only template region with a whitelist predicate
  `{% if task.kind == "hot_follow" %}` so non-Hot-Follow tasks see the
  stripped shared shell (header card + operator surface + line-panel
  slot + the matched panel block);
- is a non-binding pointer for the per-line workbench templates that
  already exist (`hot_follow_workbench.html`,
  `task_workbench_apollo_avatar.html`): each per-line template owns
  its own line-specific shell and is unaffected by this rule;
- does NOT introduce per-line workbench template files for new lines;
  per `workbench_panel_dispatch_contract_v1` the per-panel mount
  inside a shared shell is the correct design;
- does NOT introduce capability flags
  (`shell_capabilities.has_dub_flow`, etc.) in this wave; the whitelist
  form `kind == "hot_follow"` is the simpler, lower-risk implementation
  approved by the follow-up blocker review §5.

This addendum is **additive**. The closed dispatch map (six pairs), the
closed `panel_kind` enum, the closed `ref_id` set, the closed-by-default
rule, the resolver shape, and the forbidden list are unchanged.
