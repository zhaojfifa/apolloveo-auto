# REPO_LAYOUT_GUIDE (v1.9)

## Goal
Introduce hexagonal structure without breaking the current runtime.
No file moves in this PR.

## Where new code goes
- gateway/app/domain: pure rules, no FastAPI, no external providers
- gateway/app/application: orchestration, use ports only
- gateway/app/ports: Protocol/ABC interfaces (repos/storage/tools/models)
- gateway/app/adapters: concrete implementations (R2, ffmpeg, providers)

## Hard constraints
- Routers must not import adapters directly (routers -> application -> ports)
- Domain must not import application/routers/adapters
- status_policy is part of application-layer reconciliation (can stay under services for now, but new policies may be placed under application later)

## Migration strategy
- Do not move existing modules until STATUS_AND_DELIVERABLES_SPEC is frozen.
- When moving later, keep backward compatible re-export modules for one release.
