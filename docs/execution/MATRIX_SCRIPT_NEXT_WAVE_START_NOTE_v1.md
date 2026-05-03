# Matrix Script Next Wave — Engineering Start Note v1

Date: 2026-05-03
Status: **Documentation only. No code, no UI, no contract, no schema, no test, no template change.** This note is a navigation anchor, not a wave 指挥单, not a Plan E gate spec, not a replacement authority. Every load-bearing claim points at an existing repo file by path; the existing file remains the truth.
Authority of creation: documentation re-anchoring under [docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md](../architecture/apolloveo_2_0_unified_alignment_map_v1.md) §3.3 ("Documentation re-anchoring") + [PLAN_A_OPS_TRIAL_WRITEUP_v1.md](PLAN_A_OPS_TRIAL_WRITEUP_v1.md) §10–§11.

---

## 1. What this note IS

A thin pointer that names, in one place, the frozen posture under which the next engineering preparation step proceeds *after* Plan A live-trial completes. A cold reader picking up the project should land here and immediately see:

- where current posture is recorded (unified map + Plan A writeup),
- what is allowed today,
- what is gated and remains gated until Plan A live-trial closes,
- which file is the authoritative next step for each role.

## 2. What this note is NOT (binding non-scope)

This note does not, and must not, become any of the following:

- **Not a Plan E gate spec.** Plan E gate spec authoring is gated on Plan A live-trial completion + signoff per [unified map §7.2](../architecture/apolloveo_2_0_unified_alignment_map_v1.md). This note does not pre-decide Plan E pre-conditions, forbidden scope, permitted scope, or acceptance.
- **Not a wave 指挥单.** Wave-internal execution briefs live under `docs/architecture/ApolloVeo_2.0_*_Wave_*指挥单*_v1.md`. This note does not replicate or override their scope.
- **Not a contract / review / execution log.** It links to those; it does not redefine them.
- **Not a Plan E unblock.** It does not satisfy Plan E pre-condition #1.
- **Not a Platform Runtime Assembly start.** Platform Runtime Assembly remains gated on Plan E green per [unified map §7.4](../architecture/apolloveo_2_0_unified_alignment_map_v1.md).
- **Not a parallel ledger.** It does not duplicate posture state. It points at the native files that own posture.

If this note's wording ever conflicts with the underlying authority, the authority wins; this note is updated, not the underlying file.

## 3. Frozen posture (pointer; do not duplicate)

The posture under which the next engineering preparation step will proceed is already recorded by the repo's native files. This note names them; it does not restate their content.

| Posture element | Authority pointer |
| --- | --- |
| Hot Follow = operational baseline line | [unified map §4 / §4.1](../architecture/apolloveo_2_0_unified_alignment_map_v1.md), [PLAN_A_OPS_TRIAL_WRITEUP_v1.md §10](PLAN_A_OPS_TRIAL_WRITEUP_v1.md), [ENGINEERING_STATUS.md "Current Main Line"](../../ENGINEERING_STATUS.md) |
| Matrix Script = next operator-facing line | [unified map §4 / §4.2](../architecture/apolloveo_2_0_unified_alignment_map_v1.md), [PLAN_A_OPS_TRIAL_WRITEUP_v1.md §10](PLAN_A_OPS_TRIAL_WRITEUP_v1.md) |
| Digital Anchor = inspect-only / contract-aligned, no operator submission this wave | [unified map §4 / §4.3](../architecture/apolloveo_2_0_unified_alignment_map_v1.md), [PLAN_A_OPS_TRIAL_WRITEUP_v1.md §4 / §10](PLAN_A_OPS_TRIAL_WRITEUP_v1.md) |
| Plan A = PARTIAL — partial live evidence recorded; full samples + capture-template §6 signoff pending | [PLAN_A_OPS_TRIAL_WRITEUP_v1.md §8 / §10](PLAN_A_OPS_TRIAL_WRITEUP_v1.md), [PLAN_A_LIVE_RUN_CAPTURE_TEMPLATE_v1.md](PLAN_A_LIVE_RUN_CAPTURE_TEMPLATE_v1.md) |
| Plan E = BLOCKED — gated on Plan A live-trial completion + signoff | [unified map §3.1 / §7.1 / §7.2 / §7.6](../architecture/apolloveo_2_0_unified_alignment_map_v1.md), [PLAN_A_OPS_TRIAL_WRITEUP_v1.md §10](PLAN_A_OPS_TRIAL_WRITEUP_v1.md) |
| Platform Runtime Assembly = NOT STARTED — gated on Plan E green | [unified map §3.1 / §7.4](../architecture/apolloveo_2_0_unified_alignment_map_v1.md) |
| Capability Expansion = NOT STARTED — gated on Platform Runtime Assembly signoff | [unified map §3.1 / §7.5](../architecture/apolloveo_2_0_unified_alignment_map_v1.md) |

## 4. Single next allowed engineering action

Per [unified map §3.3](../architecture/apolloveo_2_0_unified_alignment_map_v1.md) and [unified map §7.1](../architecture/apolloveo_2_0_unified_alignment_map_v1.md), the only wave-internal engineering action that is allowed today is:

**Plan A live-trial completion** — operations team coordinator + architect + reviewer complete capture-template §6 signoff and append the remaining Plan A sample-wave evidence (samples 1, 2, 4, 5a, 5b, 6) from [PLAN_A_LIVE_RUN_CAPTURE_TEMPLATE_v1.md](PLAN_A_LIVE_RUN_CAPTURE_TEMPLATE_v1.md) §2.1–§2.6 / §3 / §4 / §5 / §6 into [PLAN_A_OPS_TRIAL_WRITEUP_v1.md](PLAN_A_OPS_TRIAL_WRITEUP_v1.md) §8 per that template's §7 handoff rule.

Always-allowed maintenance (no wave gate required), per [unified map §3.3](../architecture/apolloveo_2_0_unified_alignment_map_v1.md):

- Documentation re-anchoring (this note is itself an instance).
- Evidence write-back on already-shipped corrections.
- Architect / reviewer signoff of W2.1 B1–B4 (paperwork only).

## 5. Hard red lines (sequence-wide; pointer to map §7.6)

Per [unified map §7.6](../architecture/apolloveo_2_0_unified_alignment_map_v1.md):

- **Do not skip Step 1** by running Plan E preparation in parallel — the Plan E gate spec depends on Plan A live-run findings.
- **Do not preempt Step 4** by running W2.2 / W2.3 work — Capability Expansion is gated on Platform Runtime Assembly signoff.
- **Do not treat any "discovery-only" surface as a milestone.**
- **Do not let any signoff document this map without re-reading the eight root files first** ([unified map §6.1](../architecture/apolloveo_2_0_unified_alignment_map_v1.md)).

Additional red lines binding this note specifically:

- **Do not** treat this note as authority. Authority lives in the linked files.
- **Do not** add Plan E content (pre-conditions, forbidden / permitted scope, acceptance, sequence) to this note.
- **Do not** start operator-facing Matrix Script implementation work, frontend patching beyond what is shipped, contract semantic changes, runtime binding work, or third-line commissioning under this note.
- **Do not** open second-line / new-line onboarding ahead of factory alignment gate prerequisites, per [CURRENT_ENGINEERING_FOCUS.md "Forbidden Work"](../../CURRENT_ENGINEERING_FOCUS.md).

## 6. Reading order for the engineering preparation step

When the engineering preparation step begins, read in this order. Do not skip; do not reorder.

1. The eight root files in [unified map §6.1](../architecture/apolloveo_2_0_unified_alignment_map_v1.md).
2. [docs/README.md](../README.md), [docs/ENGINEERING_INDEX.md](../ENGINEERING_INDEX.md).
3. [docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md](../architecture/apolloveo_2_0_unified_alignment_map_v1.md) — confirm wave / line / surface position.
4. [docs/contracts/engineering_reading_contract_v1.md](../contracts/engineering_reading_contract_v1.md) — index-first discipline + reading declaration template.
5. [PLAN_A_OPS_TRIAL_WRITEUP_v1.md](PLAN_A_OPS_TRIAL_WRITEUP_v1.md) and [PLAN_A_LIVE_RUN_CAPTURE_TEMPLATE_v1.md](PLAN_A_LIVE_RUN_CAPTURE_TEMPLATE_v1.md) — current Plan A state and the §6 signoff still pending.
6. [docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md) — sample-validity and pre-condition rules.
7. The active wave 指挥单 — [docs/architecture/ApolloVeo_2.0_Operator_Visible_Surface_Validation_Wave_指挥单_v1.md](../architecture/ApolloVeo_2.0_Operator_Visible_Surface_Validation_Wave_指挥单_v1.md).
8. Per-line authority for any line the preparation step touches (Matrix Script: [docs/contracts/matrix_script/packet_v1.md](../contracts/matrix_script/packet_v1.md) and addenda).

After Plan A signoff lands, the next-step authority for Plan E gate-spec authoring is owned by [unified map §7.2](../architecture/apolloveo_2_0_unified_alignment_map_v1.md). This note does not pre-decide that authoring.

## 7. Note maintenance rules

- Update this note only when posture pointers above shift in the underlying authority files; do not edit it per PR.
- Do not embed contract content, review verdicts, or execution evidence here. Reference; do not duplicate.
- This note is closed for additive content beyond pointer updates. Any deeper content belongs in its native authority file.
- When Plan A live-trial closes (capture-template §6 signoff + samples appended into writeup §8), update §3 and §4 of this note to point at the closed Plan A artifacts and at the (then-allowed) Plan E gate-spec authoring step.

End of Matrix Script Next Wave Engineering Start Note v1.
