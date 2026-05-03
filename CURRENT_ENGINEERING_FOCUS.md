# Current Engineering Focus

## Current Stage

Factory Alignment Review Gate Active

## Current Main Line

- active architecture gate from `docs/reviews/2026-03-18-plus_factory_alignment_code_review.md`
- Plan A trial correction set from `docs/reviews/matrix_script_trial_blocker_and_realign_review_v1.md` complete (items §8.A, §8.B, §8.C, and §8.D all PASS; the fresh corrected Matrix Script trial sample is now fully briefed and the operations team may proceed with §7.1 sample creation per `docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md`)
- Matrix Script follow-up blocker review v1 from `docs/reviews/matrix_script_followup_blocker_review_v1.md` accepted as current authority; §8.G (Phase B panel render correctness), §8.E (workbench shell line-conditional rendering), and §8.F (opaque-ref discipline — Option F1 accepted; Options F2 / F3 rejected in this wave) all PASS; §8.H (operator brief re-correction) is the last in-wave follow-up; ops trial retry stays BLOCKED until §8.H completes the chain; Plan E retains Option F2 (in-product minting flow) as the eventual replacement for the §8.F operator transitional convention `content://matrix-script/source/<token>`
- execution-path migration only under the current factory alignment gate
- live provider / media validation for Hot Follow Burmese (`my`) and Vietnamese (`vi`)
- action replica planning-to-runtime binding preparation without reopening Phase-2 foundation refactors

## Allowed Next Work

- execution-path migration only where it is required for live validation
- live provider / media validation for `my` and `vi`
- action replica planning-to-runtime binding preparation only when it does not bypass the new-line onboarding gate
- scoped docs / runbook / verification maintenance tied to Phase-3 execution validation
- docs / runbook / validation maintenance tied to Phase-2 controlled execution

## Forbidden Work

- generic agent platform build
- second production line business rollout
- second/new production line onboarding before factory alignment gate prerequisites clear
- OpenClaw expansion beyond boundary preparation
- broad studio shell / product-shell import
- unrelated runtime rewrites
- reopening Phase-2 foundation refactors in the same task
- new line-specific logic in `tasks.py`
- new mixed four-layer projection expansion in `task_view.py`

## Merge Gates

- business regression is mandatory
- verification baseline is mandatory
- relevant PRs must cite `docs/reviews/2026-03-18-plus_factory_alignment_code_review.md` and appendices
- scope boundary must be stated
- progress log / execution docs must be updated when stage semantics change

## Structural Risk Reminders

- do not let `tasks.py` regrow
- do not let bridge / compatibility files become new God files
- do not reintroduce router-to-router coupling
- do not let presentation drift away from artifact truth
- do not let skills or workers become hidden truth writers
