# ARCHITECTURE_BASELINE_v1.9

> Scope: v1.9 refactor baseline (docs-first).  
> Goal: stabilize baseline task pipeline while enabling multi-scenario parallelism (e.g., baseline + apollo_avatar) through a policy/registry dispatch, without regressing existing mainline behavior.

## 1. Product Positioning (L4)

**ApolloVeo is an L4 orchestration layer**: AI-driven, business-facing workflow engine oriented to structured outputs (deliverables).  
It is not a single model product. It composes:
- models (Gemini/Whisper/Akool/Kling/…)
- tools (ffmpeg, keyframe extraction, packaging)
- storage (R2)
- workflows (Task → Steps → Deliverables)

Primary success metric: **repeatable delivery** (stable artifacts, retriable runs, operator-friendly UX), not “one-off generation”.

---

## 2. Hexagonal Architecture Boundaries

### 2.1 Core rule
**Domain/workflow must not depend on framework/web.**  
Routers are thin; they call workflow/application services through ports.

### 2.2 Layers (conceptual)
- **Routers (HTTP)**: FastAPI endpoints, input validation, response shaping.
- **Application / Workflow**: step execution, orchestration, policy dispatch, retry semantics.
- **Domain**: Task, Step, Deliverable, Status model (pure rules).
- **Ports**: repositories, storage, tool/model clients.
- **Adapters**: R2 adapter, model adapters (Gemini/Akool), local tool adapters (ffmpeg), etc.

> Current repo may not fully reflect this yet; v1.9 baseline establishes the invariants and the extension mechanism first.

---

## 3. Core Objects (stable contracts)

### 3.1 Task
A Task is the unit of orchestration. It has:
- **identity**: task_id, kind/category_key
- **workflow state**: status, last_step, error_reason/error_message
- **sub-status**: subtitles_status, dub_status, scenes_status, pack_status, publish_status
- **deliverables pointers**: *key/path/url* fields (e.g., publish_key/publish_url, pack_path, scenes_path)
- **config**: pipeline_config (subtitles_mode, dub_mode, etc.)
- **metadata**: platform/account/template/langs

### 3.2 Step
A Step is a workflow stage (parse/subtitles/dub/scenes/pack/publish/...).  
Steps can be:
- required
- skipped
- failed
- retried / replayed

### 3.3 Deliverable (truth source)
A Deliverable is an **artifact pointer** that must be verifiable:
- key/path/url
- content-type
- existence / readiness

> v1.9 baseline principle: **deliverables are the truth source**, status is derived.

---

## 4. Write Boundary (single write strategy)

### 4.1 The only write gate
All mutations to task fields must go through **repo.upsert** (single entry policy).  
No scattered “repo.update” from multiple places.

### 4.2 Why
- Prevent inconsistent status graphs across scenarios
- Ensure multi-scenario parallelism works
- Ensure derived status can be reconciled centrally

### 4.3 Post-write reconciliation hook
After a step generates updates, a **StatusPolicy** runs to reconcile:
- normalization (e.g., done → ready)
- scenario-specific status semantics
- final status derivation rules (ready gate / failed gate)

---

## 5. Extension Mechanism: Status Policy / Registry

### 5.1 Motivation
Different scenarios (baseline vs apollo_avatar) have different step graphs and readiness criteria.
We keep core pipeline stable and extend status semantics via policy.

### 5.2 StatusPolicy contract
- Runs after a step produces updates
- Returns filtered/augmented updates to persist
- Default policy is no-op + shared coercion helpers

### 5.3 Registry dispatch
Policy is chosen by **task.kind/category_key** (e.g., "apollo_avatar").
- baseline tasks use DefaultStatusPolicy
- apollo_avatar uses ApolloAvatarStatusPolicy

### 5.4 Import discipline (anti-circular)
- utils.py must be pure functions (no registry import)
- egistry.py imports policy classes and returns an instance
- ase.py can import utils, but utils must not import registry

---

## 6. Tools & Model Integration (Ports/Adapters view)

### 6.1 Tools (local/remote)
Tools are operational capabilities used by steps:
- local ffmpeg (cut, merge, xfade, keyframes)
- packaging tools (capcut pack assembler)
- optional external tools (future)

**Design constraints**
- Tools must be addressable by id (tools hub)
- Tool invocation must be observable (logs + step context)
- Tool failures must map to step failures, not crash the service

### 6.2 Model adapters
Model providers (Gemini/Whisper/Akool/Kling/...) are treated as adapters:
- strict request/response shaping
- retries and fallback per policy
- cost/latency observability

**Key rule**
- Workflow calls provider via port interface
- Provider errors are captured into task error_reason/error_message

---

## 7. Multi-scenario Parallelism (baseline invariant)

We must support:
- baseline: download/upload → subtitles → dub → scenes/pack → publish
- apollo_avatar: generate → publish_hub → publish (and optional subtitles/dub as configured)

**Invariant**
- Different scenarios may have different step graphs.
- They must not share incompatible status derivation logic.
- Policy-based reconciliation provides per-kind semantics without forking routers or breaking baseline.

---

## 8. Deliverables & Status (this doc only states invariants)

Status model and deliverables spec are defined in STATUS_AND_DELIVERABLES_SPEC.md (next milestone).  
For v1.9 baseline, we enforce:
- deliverables are truth source
- final status must coerce to eady when deliverables are ready
- "done" must be normalized to "ready" in response fields

---

## 9. Roadmap (docs-first)

P0 (this commit):
- add v1.9 baseline doc
- add skills catalog (configurable policies)
- add avatar SOP template (new scenario template)

P1:
- STATUS_AND_DELIVERABLES_SPEC.md
- UI refactor for multi-scenario operator UX
- live avatar provider integration (adapter hardening)
