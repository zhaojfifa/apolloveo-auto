# STATUS_AND_DELIVERABLES_SPEC (v1.9)

## Scope & Non-goals

**Scope:** define status semantics and deliverables truth sources for baseline + apollo_avatar scenarios.
This spec hardens the v1.9 baseline with a single status normalization rule-set and explicit API error semantics.

**Non-goals:**
- Do not infer/repair historical dirty data (assume DB reset/clean baseline).
- Do not redesign steps or change mainline workflow behavior.

---

## Canonical Deliverables (truth source)

**Publish deliverable (highest priority):**
- `publish_status == ready` AND (`publish_key` OR `publish_url`) exists.

**Fallback deliverables (baseline compatibility):**
- `pack_path` exists → deliverable ready.
- `scenes_path` exists → deliverable ready.

**Rule:** UI must only use these deliverable checks to determine readiness.
Do not infer readiness from subtitles/dub/pack/scenes legacy statuses.

---

## Final Status Normalization (global rule)

- `status: done` → `status: ready`
- `*_status: done` → `*_status: ready`

**Failed gate:**
- if `error_reason` is set, OR any `*_status == failed` → `status = failed`

**Ready gate:**
- if deliverable_ready AND not failed → `status = ready`

**Otherwise:**
- `status = running`

---

## API Error Semantics (401 / 404 / 409)

### 401 Unauthorized
Missing session/token, expired token, or insufficient permission.

Response:
```json
{"error_code":"unauthorized","message":"...","next":"/auth/login?next=..."}
```

### 404 Not Found
Task does not exist or not owned (multi-tenant).

Response:
```json
{"error_code":"not_found","message":"task not found","task_id":"...","kind":"..."}
```

### 409 Conflict
Invalid state for the requested operation (e.g., publish_hub requires ready).

Response:
```json
{"error_code":"conflict","message":"invalid state","current":{"status":"..."},"expected":{"status":["ready"]},"hint":"..."}
```

---

## Write Boundary: repo.upsert (single entry)

All task mutations must flow through **policy_upsert(...)**.
Direct `repo.upsert(task_id, updates)` calls are disallowed for workflow steps.

Purpose:
- single reconciliation point
- consistent status across list/detail/events
- scenario-specific policy enforcement

---

## Status Matrix (baseline vs apollo_avatar)

| Step | Baseline fields written | Substatus | Deliverable impact | Apollo Avatar notes |
|------|-------------------------|-----------|--------------------|---------------------|
| parse | raw_path, duration_sec | — | none | not used |
| subtitles | origin_srt_path, mm_srt_path, mm_txt_path | subtitles_status | none | optional (can be skipped) |
| dub | mm_audio_path/mm_audio_key | dub_status | none | optional (can be skipped) |
| scenes | scenes_key/scenes_path | scenes_status | scenes_path => ready | can be skipped |
| pack | pack_key/pack_path | pack_status | pack_path => ready | optional; publish deliverable preferred |
| publish | publish_key/publish_url | publish_status | publish deliverable => ready | primary deliverable |

**Apollo Avatar:**
- scenes_status may be `skipped`
- subtitles_status / dub_status may be `skipped`
- ready is driven by publish deliverables

---

## Invariants (v1.9)

- deliverables are the truth source for ready status
- done is normalized to ready in all response fields
- status_policy is the only reconciliation layer
- list/detail/events must align via single policy_upsert writes
