# Docs Structure And Placement

This file is the docs directory structure entry point. It defines where documentation belongs and how new docs should be placed.

For task-oriented engineering/business reading, use `docs/ENGINEERING_INDEX.md`.
For root-level engineering constraints, use `ENGINEERING_CONSTRAINTS_INDEX.md`.

## Target Layout

The normalized docs layout is:

```text
docs/
  README.md
  ENGINEERING_INDEX.md

  baseline/
  reviews/
  execution/
  contracts/
  architecture/
    line_contracts/
  runbooks/
  skills/
  adr/
  archive/
```

Current legacy exceptions:

- `docs/scenarios/`: retained until scenario material is reclassified into `runbooks/`, `architecture/`, or `archive/`.
- `docs/sop/`: retained until old SOP references are migrated into `runbooks/` or line contract docs.
- `docs/hot_follow_workbench_closure.md`: root-level docs exception; future closure notes should go under `docs/execution/`.

Do not add new top-level docs folders without updating this file and `docs/ENGINEERING_INDEX.md`.

## Placement Rules

### `baseline/`

Belongs here:

- long-lived project/product/architecture/execution baseline
- current gate or baseline index documents
- durable statements of what is true now

Does not belong here:

- one-PR execution notes
- investigation drafts
- future proposals not accepted as baseline

### `reviews/`

Belongs here:

- diagnostic reviews
- architecture review notes
- drift maps
- evidence and analysis used to inform baseline or contract changes

Does not belong here:

- runtime contracts
- permanent rules
- execution logs

Review conclusions must be promoted into baseline, contract, architecture, ADR, or execution docs before they become active authority.

### `execution/`

Belongs here:

- current execution plans
- PR/phase validation notes
- closure notes
- recovery notes
- validation logs and branch-specific evidence

Does not belong here:

- permanent architecture rules
- reusable runtime contracts
- historical material after it is superseded

Execution logs record what happened; they do not create permanent architecture policy.

### `contracts/`

Belongs here:

- runtime contracts
- schema files
- state contracts
- response contracts
- ownership matrices
- ready-gate contracts

Does not belong here:

- exploratory review analysis
- one-off execution notes
- implementation plans without a contract surface

Contracts are active source-of-truth for runtime boundaries until superseded by a newer contract.

### `architecture/`

Belongs here:

- architecture baselines
- reconstruction baselines
- line contract examples
- structural design docs
- accepted object models shared across lines

`architecture/line_contracts/` is for line-specific architecture contract examples and binding docs.

Does not belong here:

- temporary execution evidence
- issue diagnosis that has not become architecture

### `runbooks/`

Belongs here:

- repeatable verification procedures
- operator/developer procedures
- setup and regression instructions
- business guardrail procedures

Does not belong here:

- architecture decisions
- review conclusions
- runtime schemas

### `skills/`

Belongs here:

- skill documentation
- skill onboarding material
- skill-specific behavior notes

Skill docs do not make skills truth-write owners. Skill runtime ownership must still follow contracts and state ownership docs.

### `adr/`

Belongs here:

- accepted architecture decisions
- durable decision records with context and consequences

Does not belong here:

- open-ended review notes
- branch execution logs

### `archive/`

Belongs here:

- superseded docs
- legacy contracts
- historical baseline packages
- material retained only for archaeology

Archive docs are reference-only. They are not active implementation sources.

## File Priority Matrix

Use this authority order when docs disagree:

1. Root governance files: `PROJECT_RULES.md`, `ENGINEERING_RULES.md`, `CURRENT_ENGINEERING_FOCUS.md`, `ENGINEERING_STATUS.md`
2. Root engineering constraints: `ENGINEERING_CONSTRAINTS_INDEX.md`
3. Baseline/gate docs: `docs/baseline/PROJECT_BASELINE_INDEX.md` and active gate docs
4. Contracts: `docs/contracts/*`
5. Architecture docs: `docs/architecture/*`
6. ADRs: `docs/adr/*`
7. Execution logs: `docs/execution/*`
8. Reviews: `docs/reviews/*`
9. Archive: `docs/archive/*`

## Write Rules

Before adding or moving a doc:

1. Choose the bucket by purpose, not by author or date.
2. Check whether the doc creates a permanent rule, a runtime contract, an architecture decision, or only execution evidence.
3. Update `docs/ENGINEERING_INDEX.md` if the doc becomes a required reading path.
4. Update this file if a new placement category is needed.
5. Do not let review or execution docs become hidden runtime contracts.
