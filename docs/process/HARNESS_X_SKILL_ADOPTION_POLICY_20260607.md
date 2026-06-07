# Harness X — Skill Adoption Policy (2026-06-07)

Status: **PROCESS POLICY — docs-only. Not automation code, not a runtime authority,
not a change to Harness X authority rules or to any Gate Spec.** It governs how
Claude Code **Skills / plugins** may be evaluated, installed, and trialled **Tyler-local
only**, in support of the Harness X workflow — without ever becoming a source of truth,
a private memory mechanism, or a runtime change.

Builds on `docs/process/HARNESS_X_ROLE_ENGINEERING_DESIGN_20260607.md` (the S0–S9 role
state machine) and `docs/process/HARNESS_X_AUTOPILOT_EXECUTION_POLICY_20260607.md` (the
L1/L2/L3 automation-readiness split). Where this policy conflicts with
`ENGINEERING_RULES.md`, `CURRENT_ENGINEERING_FOCUS.md`, Bucket A, or **CLAUDE.md §3 (No
Private Memory Rule)**, the underlying authority wins.

> **Hard inheritance from CLAUDE.md §3:** a Skill is *never* a source of truth, *never*
> a parallel/hidden state store, and *never* an off-index cognition file. Adopting a
> Skill does not introduce a new agent-memory mechanism into the **project** — it is a
> Tyler-local convenience for reading/checking/templating. Any skill that would persist
> project state outside the repo's native files is forbidden by this policy.

---

## 1. Skill categories

Skills are grouped by what they *do* for the Harness X workflow:

- **A. Workflow / structured-process skills** — guide a multi-step procedure
  (planning, slicing, checklist discipline, report templating). Example class:
  "Superpowers"-style structured-workflow skill packs.
- **B. Read-only code understanding / indexing skills** — search, map, summarize, or
  index the codebase for comprehension. They read; they do not write.
- **C. Review / verification skills** — diff review, security review, test/verify
  helpers (several already ship built-in: `code-review`, `review`, `security-review`,
  `verify`, `simplify`).
- **D. Research skills** — fan-out web research + synthesis (built-in `deep-research`).
- **E. Config / housekeeping skills** — settings, keybindings, permission tuning
  (built-in `update-config`, `keybindings-help`, `fewer-permission-prompts`, `loop`).
- **F. Provider / generation-capable skills** — anything that can call an external
  provider, generate media, deploy, or spend credits. **Out of scope for this
  workstream** (see §3, §9).

This workstream adopts from **A and B first**, then C/D/E as needed. **F is excluded.**

## 2. Tyler-local install boundary

- All installation and trial is **Tyler-local only**: the operator's personal Claude
  Code configuration (user scope), on Tyler's machine.
- **No skill is installed into the repository.** The repo carries *policy + summary
  docs only* — never skill code, never a marketplace registration, never a plugin
  payload.
- Installation is a **Tyler-performed local action** (run by Tyler, e.g. via the `!`
  prefix or the `/plugin` UI). This policy does **not** authorize an agent to silently
  auto-install external third-party code on Tyler's machine; external skills are vetted
  and installed by Tyler explicitly.
- A skill adopted here is a **personal productivity aid for the Harness X roles**, not
  a team/project dependency. Promoting any skill to a project-level dependency is a
  separate Owner decision under §10.

## 3. Read-only vs write-capable vs provider-capable classification

Every candidate skill MUST be classified before trial:

| Class | Capability | Adoption stance |
|-------|-----------|-----------------|
| **Read-only** | reads files / repo / web; produces text, maps, reports; no file writes, no shell side effects beyond read | **Preferred. Adopt first.** |
| **Write-capable (local docs)** | can write/edit files (e.g. scaffolding a docs report, templating) | Allowed **only** for docs-scope work; never permitted to touch forbidden repo paths (§6); changes still go through Harness X review. |
| **Write-capable (runtime)** | can edit `gateway/**`, services, tests, schemas, contracts | **Not adopted under this workstream.** Runtime change stays gate-spec-first + Owner-gated (S5→S6). |
| **Provider-capable** | calls external providers, generates media, deploys, spends credits, manages secrets | **Forbidden under this workstream** (no production video capability plugin; §9). |

Default to the **least-capable** skill that does the job. When a skill's class is
ambiguous, grade it **up** (treat as more capable) and withhold until clarified.

## 4. Secret / token handling

- No skill may read, store, print, transmit, or require a secret/token/credential as a
  condition of this trial.
- No API keys, provider tokens, publish credentials, or `.env` contents are exposed to
  any skill. Skills that demand a key to function are **not adopted** under this
  workstream (they fall under the excluded provider-capable class).
- Skill configuration MUST NOT be used to smuggle a secret into `~/.claude/settings.json`
  or any repo file. Secret handling remains out of scope entirely here.

## 5. Allowed install locations

- **Allowed (Tyler-local, user scope):** `~/.claude/` — e.g. `~/.claude/plugins/`,
  `~/.claude/skills/`, and user `~/.claude/settings.json` for enabling a Tyler-local
  skill. This is Tyler's personal config and is the only place skills may live.
- **Forbidden:** the repository tree — including `.claude/` inside the repo,
  `.claude/settings.local.json`, `gateway/**`, `docs/**` (docs hold policy only, never
  skill payloads), and any committed path. Installing a skill into the repo, or
  committing a marketplace/plugin reference into repo settings, is a policy violation.

## 6. Forbidden repo paths

No skill (and no skill-assisted action) may modify, under this workstream:

```
gateway/**                         schemas/**
docs/contracts/**                  **/artifact_storage.py
gateway/app/services/hot_follow*   gateway/app/services/digital_anchor/
gateway/app/services/asset/        routers/  (no route behavior change)
CURRENT_ENGINEERING_FOCUS.md       any Gate Spec (*_GATE_SPEC_*.md)
.claude/** inside the repo         any test file (no real test mutation)
```

A skill that proposes a change to any of these is doing **runtime / authority work**,
which is out of scope here and must re-enter Harness X as its own Owner-gated task.

## 7. How skills interact with Harness X S0–S9

Skills **assist roles within phases**; they never advance a phase or grant authority.
Mapping to the role state machine:

| Phase | Skill assistance (allowed) | Never (skill may not) |
|-------|----------------------------|------------------------|
| S0 Problem Raised | summarize the complaint; gather context | declare the entry verdict |
| S1 Architect Decision | read authority, draft a classification | decide task type for the Owner |
| S2 Product Plan | templating, structure, research (read-only) | author authority / supersede Bucket A |
| S3 Static Preview | scaffold static HTML; never wire backend | connect runtime / real data |
| S4 Operator Review | none on code (operator reads preview only) | read code in lieu of the operator |
| S5 Gate Spec | templating, completeness checks | implement / open a wave / change authority |
| S6 Developer | read-only code understanding/indexing; local checks | self-author runtime under cover of a skill; touch forbidden paths |
| S7 Code Review | diff/leakage/forbidden-path scans (read-only) | replace the human/Owner review verdict |
| S8 Operator Trial | none (real operator path) | substitute for the live trial |
| S9 Merge / Deploy | none | **merge or deploy** (always Owner / L3) |

The Autopilot L1/L2/L3 split governs: a skill operates only within **L1 (read / check /
report)** and **L2 (recommend)**. A skill MUST NOT perform any **L3** action (merge,
deploy, scope/authority change, runtime start, unblocking, opening a new slice).

## 8. What skills may automate

Strictly L1/L2, side-effect-free or local-docs only:

- read indexes, authority pointers, and code for **comprehension**;
- search / map / index the codebase (read-only);
- run forbidden-path scans, `git diff --check`, leakage scans, focused test runs;
- generate report/templating scaffolds for the standard Harness X artifacts;
- recommend the next allowed transition or a retry target (advice only);
- web research with synthesis (read-only), with sources cited.

## 9. What skills must never automate

- **merge to `main` · deploy · scope expansion · authority change · S5→S6 runtime start
  · clearing a BLOCKED_\* · opening a new slice** (all L3 / Owner-only);
- **any runtime / contract / schema / test change** (forbidden paths, §6);
- **any provider / media-generation / publish / credit-spending action** (no production
  video capability plugin under this workstream);
- **overriding an Operator Review FAIL or Operator Trial FAIL**;
- **persisting project state** outside the repo's native files, or acting as a source
  of truth / private memory (CLAUDE.md §3);
- **secret/token access or exposure** (§4).

A skill reaching any of these stops and surfaces an Owner Decision Request — identical
to the Autopilot L3 behavior.

## 10. Owner Summary requirement

Every change in this workstream (each install/trial round, each policy revision) MUST
produce / update an Owner Summary at
`docs/execution/harness_x_skill_adoption_owner_summary_20260607.md`: what was
evaluated, what class each skill is, what (if anything) Tyler installed locally, the
trial result, and the explicit boundary confirmations (no runtime, no repo install, no
secret, no source-of-truth). No skill adoption is considered recorded until its Owner
Summary entry exists.

## 11. Rollback / uninstall instructions

Because adoption is Tyler-local and the repo holds no skill payload, rollback is clean
and total:

- **Disable a skill:** remove its enable entry from `~/.claude/settings.json` (or toggle
  it off in `/plugin`). Effect is immediate for new sessions.
- **Uninstall a plugin/marketplace:** remove it via the `/plugin` UI, or delete the
  corresponding directory under `~/.claude/plugins/` (and any `~/.claude/skills/<name>/`
  for a standalone skill), then restart the session.
- **Full reset:** clear `~/.claude/plugins/` and `~/.claude/skills/` and restore
  `~/.claude/settings.json` to its prior content. Since nothing was committed to the
  repo, `git status` is unaffected and no repo revert is needed.
- **Verification after rollback:** `ls ~/.claude/plugins ~/.claude/skills` shows the
  removed entries gone; the repo tree is unchanged (these docs remain — they are policy,
  not payload).

## 12. First trial scope for Matrix Script Slot Workflow v2

The first trial is scoped to **supporting the already-validated Slot Workflow v2
documentation flow**, not to producing or implementing it:

- **Goal:** use a read-only / workflow skill to (a) re-read the v2 Gate Spec + preview +
  operator review for comprehension, and (b) help template the future PR-1..PR-4
  Harness X reports — **without** authoring runtime, opening PR-1, or touching the Gate
  Spec.
- **In scope:** read-only indexing of the Matrix Script Workbench view + template (for
  comprehension only); forbidden-path / leakage scan dry-runs against the Gate Spec
  §8/§12 lists; report-template scaffolding into a scratch (non-committed) buffer.
- **Out of scope (hard):** any edit to `gateway/app/templates/task_workbench.html` or
  `gateway/app/services/matrix_script/operator_workbench_view.py`; opening Slot Workflow
  v2 PR-1; modifying the Gate Spec; any provider/generation call. S5→S6 remains
  Owner-gated and is **not** authorized by this trial.
- **Success criterion:** the skill demonstrably speeds up reading/checking/templating
  with zero repo writes outside docs and zero forbidden-path touch — proving the skill
  is an L1/L2 aid, not an L3 actor.

---

## 13. Boundary & authority note

- **Docs-only process policy.** Adds no automation code and changes no runtime.
- Does **not** modify `gateway/**`, real templates/services/tests, `schemas/**`,
  `docs/contracts/**`, `artifact_storage.py`, providers, Akool, Hot Follow, Digital
  Anchor, or any Gate Spec; does **not** authorize S5→S6 or Slot Workflow v2 PR-1.
- Does **not** change Harness X authority rules — it constrains *skill adoption cadence*
  within the existing role state machine, red lines, and CLAUDE.md §3.
- Adopting any specific skill, or promoting one beyond Tyler-local, is an Owner decision
  recorded per §10 — not a side effect of merging this policy.

*A Skill is a faster pair of hands for reading, checking, and templating. It is never a
decision-maker, never a source of truth, and never a way around the wave gate.*
