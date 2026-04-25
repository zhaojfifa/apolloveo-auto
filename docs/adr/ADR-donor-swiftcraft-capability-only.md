# ADR: SwiftCraft as Capability Donor Only

- Status: Accepted
- Date: 2026-04-25
- Scope: ApolloVeo 2.0 backend supply layer; SwiftCraft repo (`https://github.com/zhaojfifa/swiftcraft`, local clone `/Users/tylerzhao/Code/swiftcraft`)
- Supersedes: none
- Authority: ApolloVeo 2.0 Overall Master Plan v1.1, Part I Q1 / Q11 / Q12, Part II Donor Integration Strategy

## 1. Context

ApolloVeo 2.0 is a contract-driven video production factory. Hot Follow is the frozen reference line. Three-layer factory architecture (result line / supply / floor) and four-layer state model (L1 step / L2 artifact facts / L3 current attempt / L4 ready gate) are baseline truths.

SwiftCraft is a separate repo originally built to provide provider-driven scenario execution (Fal / Akool / Azure / faster-whisper / Gemini translation / ffmpeg / R2 / S3) for action replica, localization, swap_face, swap_scene, and a placeholder follow_video. Its internal task model (`task_contract.py`, `task_manager.py`, `task_service.py`, `task_store.py`) and its engine registry are coupled to a scenario-shaped runtime that conflicts with ApolloVeo's line-contract / packet / four-layer-state model.

Two paths were on the table:

1. Integrate SwiftCraft as an external service or as a wholesale backend merge into ApolloVeo
2. Treat SwiftCraft as a capability donor and implementation reference, with no truth-source role

Path 1 would inject a parallel task model, a parallel delivery semantic, and provider-shaped runtime payloads into ApolloVeo, breaking the four-layer state discipline already verified by Hot Follow. Path 2 lets ApolloVeo absorb the capability surface (provider adapters, media helpers, manifest shaping, artifact bridges, env organization) while preserving its own contract layer as the only truth source.

## 2. Decision

SwiftCraft is admitted into ApolloVeo 2.0 as **capability donor and implementation reference only**. It is not an external service dependency, not a parallel task system, and not a truth source.

Concretely:

- ApolloVeo remains the only host of `Production Line Contract`, `factory-generic objects`, `line packet`, `four-layer state`, `ready gate`, `delivery contract`, `workbench contract`
- SwiftCraft contributes capability code (helpers, provider adapters, prompt shaping, artifact / manifest formatting, env organization patterns)
- Every absorbed module must be re-homed under Apollo-native paths (`gateway/app/services/...`, `skills/...`, `ops/env/...`) and conform to Apollo contracts before merge
- No `from swiftcraft.*` import is permitted in ApolloVeo source; the SwiftCraft repo is a code source, not a runtime dependency

## 3. Boundary

### 3.1 Forbidden imports / objects

These SwiftCraft modules and concepts MUST NOT enter ApolloVeo, by direct copy, import, or semantic re-implementation:

- `backend/app/services/task_contract.py`
- `backend/app/services/task_manager.py`
- `backend/app/services/task_service.py`
- `backend/app/services/task_store.py`
- `backend/app/engines/registry.py` (engine-as-truth registry)
- `backend/app/engines/base.py` (engine task base coupled to scenario truth)
- `backend/app/engines/mock_engine.py` (test scaffolding)
- `backend/app/engines/follow_video_placeholder_engine.py` (placeholder, not capability)
- `run_config_snapshot` payload shape and any provider-shaped task config snapshot
- Any fallback ASR / TTS path that treats fallback output as primary truth
- Any internal delivery / ready-gate decision logic shaped by scenario rather than line contract

### 3.2 Permitted absorption surface

These SwiftCraft modules MAY be absorbed, subject to capability-mapping document approval and Apollo-native rewriting:

- Media helpers: `backend/app/utils/ffmpeg_localization.py`, `media.py`, `subtitle_builder.py`, `serialize.py`, `zh_normalize.py`
- ASR / translate / TTS: `backend/app/utils/asr_worker.py`, `fastwhisper_asr.py`, `translate_gemini.py`, `translate_mm.py`, `dubbing_service.py`
- Provider clients: `backend/app/providers/akool_client.py`, `backend/app/services/akool_client.py`, `backend/app/services/r2_client.py`
- Vendor / asset bridge: `backend/app/services/vendor_asset_bridge.py`, `video_face_extractor.py`
- Engine prompt shaping (capability hints only, not engine truth): `backend/app/engines/action_replica_prompt.py`, prompt-only fragments of Fal / Kling / WAN / Akool engines
- Policies / ports patterns: `backend/app/policies/`, `backend/app/ports/` (as reference patterns, not as code import)
- Env / runtime / storage organization: `.env.example` shape, R2/S3 split, `provider env matrix`

### 3.3 Re-homing rule

Every absorbed module MUST be placed under one of:

- `gateway/app/services/media/` — media helpers and ffmpeg routines
- `gateway/app/services/providers/<vendor>/` — provider clients (akool, fal, azure, gemini, whisper, r2)
- `gateway/app/services/workers/adapters/<vendor>/` — worker-side adapters bound to capability adapter base
- `gateway/app/services/artifacts/` — artifact shaping and vendor asset bridge
- `gateway/app/services/manifests/` — manifest shaping and delivery output formatting
- `skills/<line>/` — prompt shaping and provider route hints, line-scoped
- `ops/env/` — env matrix, deploy and runbook patterns

No absorbed file may retain `swiftcraft.*` package paths or import sibling SwiftCraft modules that are not themselves absorbed.

### 3.4 Truth-write rule

Absorbed modules MUST NOT write to:

- L1 pipeline step status
- L2 artifact facts
- L3 current attempt
- L4 ready gate / advisory / presentation
- delivery contract output
- asset library (Apollo Asset Sink) — Asset Library may only receive entries via Apollo's explicit `promote` flow

Absorbed modules return values to Apollo callers; Apollo callers (services, skills, workers) are the only writers of any truth field.

### 3.5 Front-end isolation rule

No ApolloVeo front-end module may import any absorbed donor helper, provider client, or worker adapter directly. Front-end code consumes only contract objects and derived gates exposed by ApolloVeo gateway routers. Verified in P0 Guardrail Test Suite via static-import scanning.

## 4. Sequencing

Absorption is gated by ApolloVeo Master Plan v1.1 phase order:

1. **P1.5 Donor Phase** — boundary doc, capability mapping doc, host directories, capability adapter base interfaces, this ADR. No code absorption PR is allowed during P1.5.
2. **P2 (after P1.5 cap)** — first absorption PRs in dependency order: helpers first (media, subtitle, serialize), then provider clients (akool, fal, gemini, whisper), then prompt-shaping skill fragments. Each PR cites the corresponding row of `swiftcraft_capability_mapping_v1.md` in its description.
3. **P3** — first new line runtime (Matrix Script) consumes absorbed capabilities through the capability adapter / routing layer. SwiftCraft engines are never directly invoked.

## 5. Consequences

### 5.1 Positive

- ApolloVeo retains a single, contract-driven truth model
- Capability surface gains breadth quickly via curated absorption rather than re-implementation
- License / attribution / commercial scope is centralized in `swiftcraft_donor_boundary_v1.md`
- Front-end / back-end hard boundary holds; no surface for accidental donor leakage

### 5.2 Negative / costs

- Each absorption PR carries rewriting overhead (Apollo-native paths, capability-adapter packaging, contract re-binding)
- Some SwiftCraft engine code cannot be absorbed wholesale because it co-mingles capability with task-truth; only prompt and provider segments survive
- A second mapping document and a new ADR phase (P1.5) are needed before any absorption PR can land

### 5.3 Risk controls

- Static-import scanner in P0 Guardrail Test Suite blocks `from swiftcraft.*` imports
- CI contract test asserts no absorbed module re-introduces `task_*` / `engine registry` / `run_config_snapshot` shapes
- Every absorption PR must reference a capability-mapping row; mapping doc is the audit trail

## 6. Alternatives Considered

### 6.1 Wholesale backend merge
Rejected. Would inject SwiftCraft's task / state / delivery semantics into ApolloVeo and violate four-layer state discipline. Hot Follow's frozen baseline would be at risk of regression.

### 6.2 SwiftCraft as remote service
Rejected. Adds an external runtime dependency without solving the truth-source ambiguity, and produces brittle cross-repo coupling for media / provider operations that are inherently in-process work.

### 6.3 Re-implement from scratch in ApolloVeo
Rejected for cost reasons. The SwiftCraft helper layer is mature and well-shaped; re-implementing media / provider scaffolding from zero would delay P3 by weeks without architectural benefit.

### 6.4 Capability donor only (this decision)
Accepted. Smallest blast radius, preserves ApolloVeo truth model, retains optionality to drop or replace any donor module without disturbing line contracts.

## 7. References

- `docs/architecture/apolloveo_2_0_master_plan_v1_1.md` — Part I Q1 / Q9 / Q11 / Q12, Part II, Part III P1.5
- `docs/donor/swiftcraft_donor_boundary_v1.md` — full boundary tables (license, attribution, forbidden / permitted lists)
- `docs/donor/swiftcraft_capability_mapping_v1.md` — module-by-module mapping required before any absorption PR
- `docs/contracts/factory_packet_envelope_contract_v1.md`, `docs/contracts/factory_packet_validator_rules_v1.md` — packet boundary that absorbed providers must respect
- `docs/contracts/hot_follow_line_contract.md`, `hot_follow_state_machine_contract_v1.md`, `hot_follow_projection_rules_v1.md` — frozen baseline that absorption MUST NOT regress
