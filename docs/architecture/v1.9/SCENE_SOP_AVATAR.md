# SCENE_SOP_AVATAR (v1.9) — New Scenario Template

> Scenario: apollo_avatar  
> Purpose: define inputs / steps / deliverables / rerun semantics / failure taxonomy for avatar workflow.  
> This document is also a template for adding future scenarios.

---

## 1. Inputs

Required:
- task_id
- kind/category_key = pollo_avatar
- content_lang (e.g., mm)
- ui_lang (e.g., zh)

Scenario-specific inputs (example):
- source character image (optional if already stored)
- motion/reference video (optional depending on provider)
- provider config (kling/akool/etc.) via pipeline_config

---

## 2. Step Graph (v1.9 baseline)

Typical steps:
1) generate (provider call)
2) publish_hub (resolve deliverables and present operator actions)
3) publish (final artifact pointer + URL)

Optional steps (depending on config):
- subtitles (if generating localized subtitle overlays)
- dub (if generating localized audio)

---

## 3. Deliverables (truth source)

Minimum deliverables for "ready":
- publish_key or publish_url exists AND publish_status == ready
OR (fallback readiness)
- pack_path exists
- scenes_path exists

For avatar scenario, the primary deliverable is typically:
- publish_key (capcut_pack.zip or scenario-specific artifact)
- publish_url (signed URL)

---

## 4. Status Semantics (scenario specific)

### 4.1 Normalization
- Any done in status-like fields must be normalized to eady.

### 4.2 Ready Gate
If deliverable is ready (see section 3), final status must be eady.

### 4.3 Failure Gate
If:
- error_reason is set, OR any sub-status == failed
then final status is ailed.

---

## 5. Rerun / Replay Semantics

- Rerun should be safe: re-generating must not corrupt existing deliverables.
- Policy may allow orce=true to overwrite publish pointers for the same task_id.
- Operators should be able to re-run a single step (e.g., generate) without losing previous artifacts unless explicitly forced.

---

## 6. Failure Taxonomy (minimal)

- provider_failed: model adapter returned error / invalid response
- subtitles_failed: subtitle step failed
- dub_failed: dubbing step failed
- publish_failed: cannot produce deliverable pointer (key/url) or upload failure
- pipeline_failed: catch-all for unexpected exceptions

Each failure must map to:
- user-facing error_message
- step attribution (last_step)
- retryable flag (future)

---

## 7. Observability (required logs)

Per step:
- task_id, kind, step, provider, elapsed_ms
- deliverable pointer keys (masked if needed)
- status before/after reconcile (policy output)

---

## 8. Template Notes (for new scenarios)

When adding a new scenario:
1) define inputs
2) define step graph
3) define deliverables truth source
4) define ready gate + failure gate
5) implement StatusPolicy + register in registry
6) ensure baseline tasks are unaffected
