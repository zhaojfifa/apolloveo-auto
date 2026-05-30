# VeoMatrixVoice05 — Production Domain Switch Report (v1)

Status: docs-only record. No code, template, contract, schema, packet, closed-enum, route, worker, endpoint, runtime, Hot Follow, Digital Anchor, Asset Supply, VoiceTrans runtime, or Render setting was modified as part of this record. Phase 3 is not started.

---

## 1. Service Name

- Render service: `apolloveo-auto2`

## 2. Domain

- Primary: [www.apolloveo.com](https://www.apolloveo.com)
- Apex: `apolloveo.com`

## 3. Branch

- Branch deployed to the official domain service: `VeoMatrixVoice05`

## 4. Commit

- Commit shown in Render deploy: `517c6f8`

## 5. URLs Verified

- Matrix Script — New Task page (zh locale):
  https://www.apolloveo.com/tasks/matrix-script/new?ui_locale=zh
- Voice tool:
  https://www.apolloveo.com/voice-tool
- Tasks board:
  https://www.apolloveo.com/tasks

All three surfaces respond on the official domain under the `VeoMatrixVoice05` deploy.

## 6. Screenshots / Manual Evidence Summary

- Operator manually opened each of the three URLs above on the official domain.
- Matrix Script New Task page rendered the task-entry surface under `ui_locale=zh`.
- Voice tool rendered the standalone VoiceTrans surface.
- Tasks board rendered the tasks list surface.
- Render dashboard displayed service `apolloveo-auto2` with branch `VeoMatrixVoice05` and deploy commit `517c6f8`.
- No anomalies were observed during this manual walk-through that would block continued operation on the official domain.

## 7. Start Command (Unchanged)

The Render start command was not changed and remains:

```
bash -lc 'source ./scripts/render_preflight.sh && exec uvicorn gateway.main:app --host 0.0.0.0 --port ${PORT:-10000}'
```

## 8. Remaining Known Issue

- Matrix Script **Delivery Center is still not result-oriented enough**. The surface continues to expose process-shaped artifacts rather than fully result-shaped deliverables to the operator. This is a known carry-over and is not addressed by this domain switch record.

## 9. Next Recommended Docs-Only Work

The following are recommended next, and are docs-only (no runtime / contract / template changes):

1. **Matrix Script Delivery Center — result-oriented review.** A documentation-only review of the current Delivery Center surface against the result-oriented authority, identifying which fields/sections still leak process shape and what the result-shaped target looks like.
2. **Matrix Script Phase 3 — generation experiment plan.** A documentation-only plan describing the intended Phase 3 generation experiment scope, gates, evidence, and exit criteria. Phase 3 itself is **not** started by this report.

## 10. Explicit No-Change Statement

This report is a record of an already-deployed production state. As part of producing this record:

- No source code was modified.
- No templates were modified.
- No Render settings (including the start command, branch binding, or environment) were modified by this record.
- No contracts, schemas, packets, or closed enums were modified.
- No routes, workers, or endpoints were modified.
- No runtime behavior was modified.
- Hot Follow, Digital Anchor, Asset Supply, and VoiceTrans runtimes were not modified.
- Phase 3 was not started.

This document is additive to `docs/execution/` and does not re-author any state owned by other native authorities; where its wording conflicts with the unified alignment map, contracts, reviews, or the engineering status files, those authorities win.
