# Phase-2 Progress Log

## PR-9 Action Replica Planning Asset View MVP

Date: 2026-04-07

This node completed:

- introduced a code-level `action_replica_line` planning asset baseline
- introduced planning asset models for `ReplicaIdentity`, `Wardrobe`, `HandProp`, `RoleBinding`, and `ShotBinding`
- introduced planning-side relationship binding between identity, wardrobe, prop, role, and shot structures
- introduced a small execution-mapping skeleton that converts planning assets into future execution needs without writing truth

Scope boundary:

- planning-first only
- no UI shell or workbench expansion
- no Action Replica execution overhaul
- no provider migration

Intentionally not done:

- did not introduce Action Replica routes or editor UI
- did not bind planning assets into repo truth
- did not move worker/provider execution into Action Replica planning
- did not start generator or publish-path implementation

Verification:

- action replica planning view can build identity / wardrobe / prop / role / shot structures
- candidate and linked asset refs remain dual-state after linking
- usage index stays line-scoped and run-scoped
- execution-need mapping prefers linked refs and keeps planning ownership only
- existing Script Video planning, Hot Follow skills, Worker Gateway, and import smoke remain green

Remaining risks:

- current mapping skeleton is intentionally non-executable and does not submit worker requests
- there is still no Action Replica line runtime binding or editor surface
- planning assets remain in-memory service structures only in this PR

## PR-8 Script Video Planning Layer MVP

Date: 2026-04-07

This node completed:

- introduced a code-level `script_video_line` planning draft baseline
- introduced candidate-vs-linked asset dual-state in executable planning code
- introduced line-scoped planning usage indexing hooks
- introduced a minimal prompt template registry skeleton for planning use

Scope boundary:

- planning-first only
- no studio shell or project/chapter navigation
- no execution truth writes
- no provider migration

Intentionally not done:

- did not introduce planning routes or UI
- did not bind planning drafts into repo truth
- did not start Action Replica execution or asset view work
- did not migrate worker/provider paths

Verification:

- planning registry resolves the default `script_video_line` template family
- planning service builds draft/segment/shot/entity structures
- candidate and linked assets remain dual-state after linking
- planning usage index remains line-scoped and run-scoped
- existing Hot Follow skills/worker/import smoke regressions remain green

Remaining risks:

- current planning service is intentionally deterministic and hint-driven, not a full script extraction pipeline
- prompt template registry is a skeleton, not a broad prompt product system
- route/UI/editor integration is deferred by design

## PR-7 Worker Gateway MVP

Date: 2026-04-07

This node completed:

- introduced explicit Worker Gateway request / result runtime objects
- introduced execution-mode support for `internal`, `external`, and `hybrid`
- added a minimal gateway registry and dispatcher
- routed Hot Follow compose FFmpeg execution through the Worker Gateway internal adapter
- aligned Hot Follow line metadata so `worker_profile_ref` points to the runtime worker contract

Scope boundary:

- kept the change narrow to execution boundary
- preserved repo truth, deliverable truth, publish truth, and status truth outside the gateway
- did not start a broad provider rewrite

Intentionally not done:

- did not migrate every provider-backed path into Worker Gateway
- did not introduce OpenClaw runtime integration
- did not add new business features or UI work
- did not let Worker Gateway perform repo or status writes

Verification:

- Worker Gateway registry dispatch is covered for external/hybrid mode selection
- internal subprocess adapter timeout surface is covered
- compose `_run_ffmpeg(...)` now executes through Worker Gateway in tests
- Hot Follow publish/workbench line binding and import smoke remain green

Remaining risks:

- the only live execution path in this PR is compose FFmpeg internal execution
- external and hybrid modes are real runtime contract types, but broader provider migration is still deferred
- parse / ASR / TTS provider branching remains outside the gateway for now

## PR-6 Hot Follow Skills Runtime MVP

Date: 2026-04-07

This node completed:

- introduced a minimal line-scoped skills runtime loader
- added the first live Hot Follow skills bundle at `skills/hot_follow`
- moved Hot Follow advisory judgment into `input / routing / quality / recovery` stage modules
- updated Hot Follow line metadata so `skills_bundle_ref` points to the real runtime bundle path

Scope boundary:

- kept the runtime narrow to Hot Follow
- preserved current advisory/workbench behavior
- kept all status, deliverable, publish, and sink writes outside skills

Intentionally not done:

- did not implement worker gateway
- did not introduce a generic multi-line plugin platform
- did not move compose or publish truth ownership into skills
- did not start planning-line runtimeization

Verification:

- bundle loader resolves `skills/hot_follow` from live line binding
- existing Hot Follow advisory outputs remain stable in tests
- workbench payload still attaches advisory as read-only secondary guidance
- import smoke and line binding tests remain green

Remaining risks:

- current loader is intentionally minimal and line-scoped; generic multi-line expansion is deferred
- only advisory-oriented strategy logic moved in this PR; broader execution routing stays for PR-7
- top-level engineering focus still needs explicit branch-stage alignment if Phase-2 implementation broadens further

## PR-5 Phase-2 Docs / Contracts / ADR Freeze

Date: 2026-04-07

This node completed:

- froze the Phase-2 Skills Runtime contract baseline
- froze the Phase-2 Worker Gateway runtime contract baseline
- froze the planning-first contracts for `script_video_line` and `action_replica_line`
- froze the Phase-2 ADR and execution runbook
- added a dedicated Phase-2 progress log and updated docs indexes for discoverability

Scope boundary:

- docs-first only
- no runtime code changes
- no Skills Runtime implementation
- no Worker Gateway implementation
- no planning UI shell

Intentionally not done:

- did not start PR-6 skills bundle code
- did not start PR-7 worker gateway code
- did not bind planning contracts into runtime
- did not change Hot Follow business behavior

Verification:

- confirmed all new docs files exist in the expected buckets
- updated docs index / ADR index / execution log index to include Phase-2 materials
- reviewed contract boundaries against existing Phase-1 line/ready-gate/status ownership baseline

Remaining risks:

- top-level engineering focus still reflects the post-VeoSop05 continuation stage and will need explicit alignment before broad Phase-2 implementation lands
- the new contracts are frozen before runtime implementation, so some fields remain hook-only until PR-6/PR-7
- planning contracts intentionally remain non-executable until later PRs
