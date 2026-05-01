# Hot Follow Rebuild Business Rule Index v1

Status: Wave 0 frozen
Branch: `VeoReBuild01`

## Source Indexes Consumed

Business/document entrypoints consumed:

- `docs/ENGINEERING_INDEX.md`
- `docs/README.md`
- directory index/listing for `docs/contracts/`
- directory index/listing for `docs/architecture/`
- directory index/listing for `docs/product/`
- directory index/listing for `docs/design/`
- directory index/listing for `docs/runbooks/`
- directory index/listing for `docs/sop/hot_follow/`

Selected business authorities:

- `docs/architecture/hot_follow_business_flow_v1.md`
- `docs/contracts/hot_follow_line_contract.md`
- `docs/architecture/line_contracts/hot_follow_line.yaml`
- `docs/runbooks/hot_follow_sop.md`
- `docs/runbooks/ops/hot_follow_delivery_sop.md`
- `docs/runbooks/ops/hot_follow_publish_sop.md`
- `docs/sop/hot_follow/hot_follow_v_1_9_operations_manual.md`
- `docs/product/asset_supply_matrix_v1.md`
- `docs/design/README.md`
- `docs/design/surface_workbench_lowfi_v1.md`

## Frozen Business Rules

1. Hot Follow remains one production line with `line_id=hot_follow_line`,
   `task_kind=hot_follow`, and `target_result_type=final_video`.
   Governing sources: `docs/contracts/hot_follow_line_contract.md`, `docs/architecture/line_contracts/hot_follow_line.yaml`.

2. Hot Follow source entry modes are link ingest and local video ingest, both
   normalized into the same downstream line truth shape.
   Governing sources: `docs/contracts/hot_follow_line_contract.md`, `docs/runbooks/hot_follow_sop.md`, `docs/architecture/hot_follow_business_flow_v1.md`.

3. The operator-facing production chain remains:
   `ingest -> parse -> adapt -> dub -> compose -> review_gate -> pack_publish_sink`.
   Governing sources: `docs/runbooks/hot_follow_sop.md`, `docs/contracts/hot_follow_line_contract.md`.

4. URL main flow for the rebuild is:
   `raw -> origin.srt -> target subtitle -> dub -> compose`.
   Governing sources: `docs/architecture/hot_follow_business_flow_v1.md`, `docs/runbooks/hot_follow_sop.md`, `docs/execution/HOT_FOLLOW_REBUILD_ON_STABLE_BACKEND_DIRECTIVE_V1.md`.

5. Local preserve flow for the rebuild is:
   `raw -> preserve_source_route -> compose`.
   Governing sources: `docs/contracts/hot_follow_state_machine_contract_v1.md`, `docs/architecture/hot_follow_business_flow_v1.md`, `docs/execution/HOT_FOLLOW_REBUILD_ON_STABLE_BACKEND_DIRECTIVE_V1.md`.

6. Local preserve re-entry is explicit:
   `preserve_source_route -> tts_replace_route subtitle/dub flow`.
   It must be command/event driven, not silently inferred from read-time
   currentness.
   Governing sources: `docs/execution/HOT_FOLLOW_REBUILD_ON_STABLE_BACKEND_DIRECTIVE_V1.md`, `docs/contracts/production_line_runtime_assembly_rules_v1.md`.

7. Authoritative target subtitle truth is the only subtitle truth that may
   satisfy workbench/publish readiness. Source subtitles, helper translation,
   editable candidate text, or `origin.srt` alone are not target subtitle truth.
   Governing sources: `docs/architecture/hot_follow_business_flow_v1.md`, `docs/contracts/hot_follow_state_commit_contract_v1.md`, `docs/contracts/status_ownership_matrix.md`.

8. Helper translation is a side-channel. It may assist source understanding or
   manual subtitle fill; it may fail without invalidating current authoritative
   target subtitle truth or legal preserve-source compose truth.
   Governing sources: `docs/contracts/hot_follow_state_machine_contract_v1.md`, `docs/architecture/hot_follow_business_flow_v1.md`, `docs/contracts/four_layer_state_contract.md`.

9. Dub is current only when it matches the authoritative target subtitle and
   current audio configuration. `dub_status=done` alone is not current dub
   truth.
   Governing sources: `docs/runbooks/hot_follow_sop.md`, `docs/contracts/status_ownership_matrix.md`, `docs/contracts/four_layer_state_contract.md`.

10. Compose readiness depends on current subtitle truth, current dub or an
    explicit approved no-dub/preserve route, compose input readiness, and final
    freshness. Historical final output cannot satisfy current-ready truth.
    Governing sources: `docs/runbooks/hot_follow_sop.md`, `docs/contracts/four_layer_state_contract.md`, `docs/contracts/workbench_hub_response.contract.md`.

11. Primary deliverable is publishable final video. Target subtitle and audio
    are secondary deliverables. Pack/scene pack is optional and non-blocking.
    Governing sources: `docs/contracts/hot_follow_line_contract.md`, `docs/product/asset_supply_matrix_v1.md`, `docs/runbooks/ops/hot_follow_delivery_sop.md`, `docs/runbooks/ops/hot_follow_publish_sop.md`.

12. Workbench and publish surfaces must agree through the same authoritative
    projection path. Workbench UI may not create a local state machine or invent
    status strings outside L2/L3/ready-gate truth.
    Governing sources: `docs/contracts/workbench_hub_response.contract.md`, `docs/design/README.md`, `docs/design/surface_workbench_lowfi_v1.md`.

13. Operator validation remains business-result oriented: stable final output,
    subtitle quality, dub correctness/currentness, final playback/download, and
    no contradictory workbench/publish messaging.
    Governing sources: `docs/sop/hot_follow/hot_follow_v_1_9_operations_manual.md`, `docs/runbooks/HOT_FOLLOW_BUSINESS_REGRESSION.md`, `docs/runbooks/ops/hot_follow_publish_sop.md`.

## Business Non-Scope For Wave 0

- no provider strategy redesign
- no compose optimization or post-processing expansion
- no UI redesign beyond contract alignment in later waves
- no new production line
- no runtime behavior change
