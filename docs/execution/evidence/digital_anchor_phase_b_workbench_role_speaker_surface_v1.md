# Digital Anchor Second Production Line Wave — Phase B Workbench Role / Speaker Surface v1

- Date: 2026-04-28
- Wave: ApolloVeo 2.0 **Digital Anchor Second Production Line Wave** — Phase B only
- Phase A signoff input: PASS (latest architect/reviewer signoff in current conversation)
- Authority:
  - `docs/architecture/apolloveo_2_0_master_plan_v1_1.md`
  - `docs/architecture/ApolloVeo_2.0_多角色实施指挥单_v1.md`
  - `docs/contracts/digital_anchor/task_entry_contract_v1.md`
  - `docs/contracts/digital_anchor/packet_v1.md`
  - `docs/contracts/digital_anchor/role_pack_contract_v1.md`
  - `docs/contracts/digital_anchor/speaker_plan_contract_v1.md`
  - `schemas/packets/digital_anchor/packet.schema.json`
  - `docs/design/panel_digital_anchor_role_speaker_lowfi_v1.md`
- Contract: `docs/contracts/digital_anchor/workbench_role_speaker_surface_contract_v1.md`

## Scope

Phase B establishes the formal Workbench Role / Speaker Surface for Digital Anchor.

In scope:

- formal definition of `role_surface`;
- formal definition of `speaker_surface`;
- formal role ↔ segment binding surface;
- scene binding projection notes at workbench scope;
- attribution / refs projection rules;
- a minimal read-only projection helper;
- focused tests and evidence/index/log write-back.

Out of scope:

- delivery binding;
- publish feedback write-back;
- provider/model/vendor/avatar-engine/TTS/lip-sync controls;
- packet/schema/sample redesign;
- Matrix Script mutation;
- Hot Follow business logic;
- W2.2 / W2.3 work;
- frontend heavy rebuild.

## Files added / updated

- Added `docs/contracts/digital_anchor/workbench_role_speaker_surface_contract_v1.md`
- Added `gateway/app/services/digital_anchor/workbench_role_speaker_surface.py`
- Added `gateway/app/services/digital_anchor/__init__.py`
- Added `tests/contracts/digital_anchor/test_workbench_role_speaker_phase_b.py`
- Updated `docs/execution/DIGITAL_ANCHOR_SECOND_PRODUCTION_LINE_LOG.md`
- Updated `docs/execution/apolloveo_2_0_evidence_index_v1.md`

## Projection summary

The formal projection helper:

`gateway.app.services.digital_anchor.workbench_role_speaker_surface.project_workbench_role_speaker_surface(packet)`

returns:

- `role_surface` from `digital_anchor_role_pack.delta`;
- `speaker_surface` from `digital_anchor_speaker_plan.delta`;
- `role_segment_binding_surface` by joining `segments[].binds_role_id` to `roles[].role_id`;
- `scene_binding_projection` as workbench-only notes with `scene_binding_writeback = not_implemented_phase_b`;
- `attribution_refs` from packet refs and capability plan;
- `phase_c_deferred` for delivery and feedback concerns.

The helper does not mutate the packet, resolve provider/vendor/engine choices, write delivery or feedback, call providers, or create runtime task state.

## Validation

Command:

```bash
python3.11 -m pytest tests/contracts/digital_anchor/test_workbench_role_speaker_phase_b.py -q
```

Expected result:

```text
9 passed
```

## Boundary confirmation

No provider code was added. No Matrix Script files were touched. No Hot Follow files were touched. No packet/schema/sample redesign was performed. No delivery binding or publish feedback write-back was implemented. Phase C and Phase D remain not started.

## Remaining blockers before Phase C

1. Phase B must be reviewed and accepted.
2. Phase C must define delivery pack projection / metadata / manifest separately.
3. Phase C must decide how result packet binding becomes a delivery-center visualization without changing the Phase B workbench projection.
