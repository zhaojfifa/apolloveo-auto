# Matrix Script — Slot Workflow v2 Product Plan (2026-06-07)

Status: **PRODUCT PLAN — docs-only. Not implementation authority. Not a new Matrix
Script IA / mock / reset that supersedes Bucket A. Authorizes no runtime, opens no
wave, modifies no Gate Spec.**

Author posture: ApolloVeo 2.0 Architect / Product Planner, operator-workflow lens
(Harness X §2.2 Product Planner role; this artifact is a Workflow Plan, **not**
authority — Harness X §4 artifact class: *not authority*).

Branch baseline: `main` at `65addcbc` (merge of #227, Guided Operator Workflow
closeout PR-6).

Source inputs (consumed, not superseded):
- Bucket A binding authority — `docs/design/MATRIX_SCRIPT_DESIGN_AUTHORITY_INDEX.md`.
- `docs/design/MATRIX_SCRIPT_GUIDED_OPERATOR_WORKFLOW_PLAN_20260607.md` (#216, planning input).
- `docs/design/MATRIX_SCRIPT_GUIDED_OPERATOR_WORKFLOW_GATE_SPEC_20260607.md` (#218, accepted UI gate spec).
- `docs/execution/MATRIX_SCRIPT_GUIDED_OPERATOR_WORKFLOW_CLOSEOUT_20260607.md` (#227, engineering closeout, PASS).
- `docs/process/HARNESS_X_ROLE_ENGINEERING_DESIGN_20260607.md` + `…AUTOPILOT_EXECUTION_POLICY_20260607.md`.

When this document's wording conflicts with Bucket A authority,
`ENGINEERING_RULES.md`, or `CURRENT_ENGINEERING_FOCUS.md`, the underlying repo
authority wins and this plan is corrected in a docs-only follow-up.

---

## 0. What this document is — and is not

This is a **Harness X Product Plan (S2 artifact)** raised in response to a fresh
Owner-judged problem after the Guided Operator Workflow wave engineering-closed
(PR-1..PR-6, all S9; closeout verdict PASS; human four-party signoff still `<fill>`).

The Guided Operator Workflow wave succeeded at what it set out to do: it turned the
#211–#215 capability field into one *guided narration* over the existing five-shot
expanded-card surface. The Owner's new judgment is that the **B区 model itself** —
all-shot expanded cards — does not scale, and that the next problem is **product-flow
/ design, not an implementation bug**. This plan addresses that, and only that.

This document does **not**:

- supersede or replace any Bucket A binding authority — it cites it and feeds a
  *future* gate spec amendment;
- reopen #220 / #223 / #224 / #225 / #226 / #227 — those slices are merged substrate;
  reviewer-fail or new-defect corrections (if ever needed) are separate narrow PRs,
  never re-litigation of merged scope;
- modify the accepted Guided Operator Workflow Gate Spec
  (`…GUIDED_OPERATOR_WORKFLOW_GATE_SPEC_20260607.md`) — a v2 model requires a Gate
  Spec *amendment* or a *new* Gate Spec authored under the standard discipline;
- author a new Information Architecture or a parallel Workbench flow (Design
  Authority Index Anti-Sprawl rules 2 & 4) — every regroup proposed here re-homes
  value into the **existing** A–E zones, never a new parallel surface;
- change generation, storage, contracts, schema, samples, templates, routes,
  providers, Akool, Hot Follow, or Digital Anchor;
- authorize, open, or sequence any engineering wave — engineering remains
  gate-spec-first per `ENGINEERING_RULES.md` and the wave gate.

---

## 1. Problem Statement

**The current B区 all-shot card expansion is not scalable for 10+ shots.**

The Guided Operator Workflow wave (PR-2, #223) converged each shot into a
five-question expanded card on B区 (`docs/.../GATE_SPEC…` §3.B): 这个镜头现在用了什么 /
为什么建议处理 / 这个镜头怎么处理 / 上传这个镜头的新素材 / 调整后会发生什么. That
convergence was correct *for the five-shot sample it was designed against*. It does
not generalize:

1. **Linear card stacking has no upper bound.** Every shot renders a full
   five-question card with three decision buttons, an upload control, a folded
   advanced-binding `<details>`, and a handoff nudge. At five shots this is dense; at
   ten shots it is an unreadable vertical wall. The operator scrolls a long flat list
   to find the one or two shots that actually need work.

2. **The five cards are already visually repetitive.** Each card repeats the same
   scaffolding (same labels, same three buttons, same upload affordance, same
   advanced-binding fold) regardless of whether the shot needs attention. The signal
   (which shot is weak, per R-SHOT-REASON) is buried inside identical-looking cards.
   Doubling the shot count doubles the repetition without adding navigational help.

3. **It is an expanded-card UI, not a scalable shot workflow.** All shots are
   simultaneously expanded and co-equal. There is no notion of "the shot I am working
   on now" versus "the shots I have already handled" versus "the shots I have not yet
   reached." Every shot demands equal screen real estate and equal operator attention
   at all times.

4. **The object model is unclear.** The current surface conflates *the shot* (a
   position in the storyboard), *what fills the shot* (visual material, copy,
   subtitle, voice), and *the operator's decision about it* (keep / supplement /
   replace, upload). There is no named distinction between Shot, Slot, and
   Assignment, so the UI cannot collapse, queue, or status-summarize cleanly — it can
   only stack full cards.

5. **Most per-card affordances are not actually actionable yet.** Material
   upload/replacement is the only path with a real backend action (#211–#212:
   `msmaterial://`, `bytes_resolvable=true`, V2 consumes uploaded bytes). The other
   per-shot affordances are status/display or future-workflow placeholders. Rendering
   them as co-equal, repeated controls on every card overstates the line's
   interactive surface and inflates the card.

Operationally inefficient at the scale operations actually runs (10+ shots), the B区
model needs to move from *"expand every shot"* to *"queue all shots, work one at a
time."*

---

## 2. Human Operator Trial Findings

Summarized from the human operator validation of the engineering-closed Guided
Operator Workflow (closeout verdict: engineering PASS; human validation: **PASS WITH
ISSUES**). These are operator-seat observations, not engineering defects:

- **A区 basically works.** The state-narration spine (现状 → 原因 → 下一步, #220 / Gate
  Spec §3.A) reads correctly; the operator can tell where they are and what to do
  next. No A区 change is requested by this plan.
- **B区 is too dense.** The all-shot expanded-card layout is the primary pain point
  (see §1). It is readable at five shots and operationally inefficient beyond that.
- **The current upload path works but is repeated per shot.** Upload is the only
  truly effective adjustment path, yet its full affordance is re-rendered on every
  card, multiplying the visual repetition.
- **Advanced binding is correctly folded but still repeated.** The
  `高级：绑定已有素材引用` `<details>` (Gate Spec §3.B.1, A-3) is correctly secondary
  per card, but it re-appears on every card — folded clutter is still clutter at
  scale.
- **Material upload/replacement is currently the only truly effective adjustment
  path.** It has a real backend action and changes V2 output (#211–#212). Everything
  else on the per-shot surface is status, display, or future-workflow.
- **Voice / subtitle / BGM should be represented as status or future slots unless
  real actions exist.** Today they have no operator-effective backend action on the
  Matrix Script line. Presenting them as editable controls overstates capability and
  invites operators to click affordances that do nothing.
- **The Shot / Slot / Assignment model is unclear.** The operator cannot tell what is
  a shot, what fills it, and what their decision about it is — because the surface
  never names those concepts.

---

## 3. Product Judgment

**This is a product-flow / design issue, not an implementation bug.** Nothing in the
merged PR-1..PR-6 substrate is broken: tests are green (1899 at PR-5), acceptance
rows A-1..A-15 all PASS, no leakage, forbidden-path clean, four-layer discipline
preserved, `official_publish_ready=false` throughout. The Guided Operator Workflow
delivered exactly the surface its Gate Spec specified. The problem is that the
**model that Gate Spec froze** — all-shot expanded cards — does not scale to the shot
counts operations actually runs. That is a design decision to revisit, not a bug to
patch.

This is the canonical Harness X lesson restated (role design §1 / §8): *capability
correct ≠ operationally usable; tests green ≠ operator can run it at scale.* The
correct response is the cheap-to-be-wrong path: **re-plan on paper and in a static
preview before any runtime code.**

**Runtime work MUST NOT start** until the controlled sequence completes:

> Product Plan (this doc, S2) → Static Preview (S3) → Operator Review (S4) → Gate
> Spec amendment or new Gate Spec (S5, §10 signoff) → only then runtime implementation
> (S6).

Per Harness X red lines: S4→S5 is a hard predecessor (no Gate Spec before Operator
Review PASS); S5→S6 requires §10 signoff merged and is an Owner-gated (L3) transition
per the Autopilot Execution Policy. No autopilot layer may cross S5→S6 on its own.

---

## 4. Proposed Workflow Model

A v2 B区 that scales by **queue + single active panel**, re-homed inside the existing
B区/C区 zones (no new IA, no parallel surface). The operator works one shot at a time
against a compact, scannable queue.

- **Compact Shot Queue** — a single dense list of *all* shots, one short row each:
  shot index + thumbnail/label + a status chip (待处理 / 处理中 / 已完成 / 无需处理) +
  the R-SHOT-REASON one-liner *only when flagged*. The queue is the navigation
  surface: scannable at any shot count, it lets the operator find the one or two weak
  shots instead of scrolling identical expanded cards. Rows are collapsed by default;
  exactly one is the active shot.

- **One active Current Shot Work Panel** — only the selected shot expands into the
  full work panel. This panel hosts the per-shot affordances that today are
  replicated across every card: the visual-source trace (这个镜头用了什么), the
  R-SHOT-REASON explanation, the keep/supplement/replace decision, the upload control,
  the folded advanced-binding `<details>`, and the R-UPLOAD-HANDOFF nudge. Selecting a
  different queue row moves the active panel; it never opens a second expanded card.

- **Slot Editor** — inside the active panel, the shot's *slots* are presented as a
  small typed set (visual material / text copy / subtitle / voiceover / BGM, §6). Each
  slot renders according to its honesty classification: actionable slots show a real
  control; display-only / future slots show a status label and are **not** rendered as
  editable. The Slot Editor is where the Shot/Slot/Assignment model becomes visible to
  the operator.

- **Assignment model** — the operator's *decision* for a slot (use current / supplement
  / replace, plus the uploaded material handle) is an Assignment: the binding between a
  Slot and what fills it. Assignments are the only operator-mutable object; Shots and
  Slots are read-only structure. Naming this lets the queue summarize each shot's
  status from its Assignments without re-expanding cards.

- **Batch regenerate entry** — a single regenerate entry (re-homed into C区, the named
  V1/V2 pivot from Gate Spec §3.C) that regenerates **once** after the operator has
  made all the per-shot Assignments they intend, rather than implying a regenerate per
  card. The C区 compare/confirm pivot is unchanged in intent: regenerate → compare
  V1/V2 → confirm/discard, V1 protected until explicit confirm, delivery follows the
  confirmed main only.

This model keeps every merged behavior (upload, V2 consumption, V1 protection,
delivery-follows-confirmed, `official_publish_ready=false`) and changes only how shots
are *navigated and presented*: queue + one active panel instead of N expanded cards.

---

## 5. Object Model

The three objects the v2 surface must name. **All field/action lists below are a
product proposal for a future gate-spec author to make binding; none is asserted as a
current contract, and none introduces a new producer or second source of truth.** All
truth is read from the existing #211–#215 projections + the #215-derived
`process_state`.

### Shot

- **Purpose:** a single position in the script-driven storyboard — one unit of the
  generated main video the operator reasons about.
- **Operator-facing fields:** shot index / order; a short label or thumbnail; an
  overall status chip derived from its Assignments (待处理 / 处理中 / 已完成 / 无需处理);
  the R-SHOT-REASON one-liner when flagged.
- **Truth source:** the existing script→shot-plan projection and #215 per-shot trace
  (visual source / shot-match / missing-material). Read-only.
- **Allowed actions:** select (make active), collapse/expand within the queue. Pure
  navigation — no state mutation.
- **Forbidden actions:** operator cannot create, delete, reorder, or re-author shots;
  no operator-driven Phase B / `roles[]` / `segments[]` authoring (inherited red
  line); shot structure is generated truth, not operator-editable.

### Slot

- **Purpose:** a typed fill-point within a Shot — *what kind of thing* fills this part
  of the shot (visual material, text copy, subtitle, voiceover, BGM). Slots make the
  shot's editable surface explicit and typed instead of an undifferentiated card.
- **Operator-facing fields:** slot type (§6); current fill summary / status label;
  honesty classification badge (actionable / display-only / future).
- **Truth source:** existing per-shot projection fields (visual-source label,
  consumed-material list, copy/subtitle/audio status as projected). Read-only
  structure; the *fill* changes only via an Assignment.
- **Allowed actions:** none directly — a Slot is a structural container. Operator acts
  on it *through* an Assignment, and only for slot types classified `active now`.
- **Forbidden actions:** no new slot type invented in the UI; no slot rendered as
  editable unless it is `active now` (§6); display-only / future slots are
  status-only and MUST NOT present a control that has no backend action.

### Assignment

- **Purpose:** the binding between a Slot and what currently fills it, carrying the
  operator's decision. The **only operator-mutable object** in the model.
- **Operator-facing fields:** decision (使用当前素材 / 补充这个镜头素材 /
  替换这个镜头素材, #214 copy); the uploaded material reference when present
  (operator sees a friendly label, never the raw `msmaterial://` / `asset://` handle);
  resulting per-shot status; "调整后会发生什么" outcome line.
- **Truth source:** the existing material-intent + upload + #212 byte-consumption
  path. Assignments record intent and uploaded bytes; they do not compute new truth.
- **Allowed actions (visual_material_slot only, today):** set decision; upload material
  (primary path); optionally bind an existing reference (folded advanced); the
  Assignment feeds the next batch regenerate.
- **Forbidden actions:** no Assignment may overwrite V1 (only explicit confirm promotes
  V2); no Assignment exposes raw handles / provider / publish fields as operator copy;
  no Assignment on a display-only / future slot type; no second regenerate path
  (regenerate is the single C区 batch entry).

---

## 6. Slot Types

Five slot types, each with an **honest** classification. The binding honesty rule: a
slot is rendered with a real control **only** if it has a real, operator-effective
backend action today. Otherwise it is status / display / future — never a dead
editable control.

| Slot type | Classification | Rationale |
|-----------|----------------|-----------|
| `visual_material_slot` | **active now** | Real backend action exists: per-shot material upload (`msmaterial://`, `bytes_resolvable=true`, #211) and V2 regeneration that actually consumes the uploaded bytes (#212). This is the **only** truly effective adjustment path today. Renders the full Assignment control set (decision + upload + folded advanced binding). |
| `text_copy_slot` | **display-only now** | Script/copy is projected understanding, not an operator-authored field on this line. No operator-effective copy-edit backend action exists; operator-driven Phase B authoring is a standing red line. Show as a read-only status/summary; do **not** render an editable copy field. Future workflow only if a real copy-edit action is gated in later. |
| `subtitle_slot` | **display-only now** (→ future workflow) | Subtitle is projected/derived, not independently operator-editable on the Matrix Script line today. Show subtitle status only. Becomes a `future workflow` slot if a real subtitle-edit backend action lands under its own gate spec. |
| `voiceover_slot` | **future workflow** (**should not appear as editable yet**) | No operator-effective voiceover action exists on this line today. MUST NOT be rendered as an editable slot. May appear as a clearly-labelled future/placeholder status at most, or be omitted until a real action exists. |
| `bgm_slot` | **future workflow** (**should not appear as editable yet**) | Same as voiceover: no real backend action today. MUST NOT be rendered as an editable control. Status/future label only, or omitted. |

Honest summary (as the trial demanded): **`visual_material_slot` is active now;
text / subtitle / voice / BGM are mostly display / future unless and until a real
backend action is supported.** The v2 surface must not present voice/BGM as editable,
and must present text/subtitle as status/display rather than as working editors.

---

## 7. UI Structure Proposal

Re-homed inside existing B区/C区/D区/E区 — no new panels, no parallel flow (Anti-Sprawl
rule 4). For a future gate-spec author to make binding; illustrative, not authority.

- **Compact shot queue (B区 top):** one dense, scannable list of all shots; one short
  row each (index + label/thumb + status chip + R-SHOT-REASON only when flagged).
  Collapsed by default; the navigation surface that scales to 10+ shots.
- **One expanded current shot (B区 body):** exactly one active Current Shot Work Panel
  hosting the Slot Editor + Assignment controls (visual-material upload primary;
  advanced binding folded; R-UPLOAD-HANDOFF nudge). Selecting another queue row moves
  the active panel — never opens a second expanded card.
- **Collapsed completed shots:** shots whose Assignments are settled collapse to their
  queue row with a 已完成 chip; 无需处理 shots collapse with that chip; the operator's
  eye goes to 待处理 / 处理中.
- **Skip / upload / replace / supplement workflow:** the per-shot decision set stays
  the clean three (使用当前素材 / 补充 / 替换, #214) plus a **skip / 无需处理** affordance
  so the operator can clear a shot from the work queue without an Assignment. Upload is
  the primary material path; replace/supplement record intent then prompt upload.
- **Batch regenerate after selected changes (C区):** a single regenerate entry that
  runs once after the operator has made all intended Assignments, feeding the existing
  C区 V1/V2 compare→confirm pivot. Not a per-card regenerate.
- **Advanced binding only inside the current shot or advanced mode:** the
  `高级：绑定已有素材引用` `<details>` lives only inside the active panel (or a global
  advanced mode), not replicated on every queue row.
- **Clear distinction between status-only slots and actionable slots:** the Slot Editor
  renders `visual_material_slot` with a real control and renders text/subtitle as
  status/display and voice/BGM as future/omitted (§6). Status-only slots are visually
  marked as non-actionable so the operator never clicks a dead control.

Inherited UI red lines carried verbatim from the Guided Operator Workflow Gate Spec
§3/§4: no raw `process_state` enum or raw token in primary copy; `正式交付就绪：否`
wording only (never raw `official_publish_ready=false`) in the primary D区; no
`local_path` / manifest / provider URL / publish URL / Akool task/model/credit
anywhere in the primary surface; raw fields stay in collapsed J区 diagnostics.

---

## 8. Harness X Path

The controlled, gate-spec-first sequence (Harness X role design §3 state machine;
Autopilot Execution Policy §3 layers). Each transition names its role and risk:

- **S0 — Problem Raised.** Owner judgment: B区 all-shot expansion does not scale; the
  next problem is product-flow/design, not an implementation bug. *(This plan records
  S0.)*
- **S1 — Architect Decision.** Classify as a **P-flow (product-flow) problem**, not a
  capability/bug; name the governing authority (Bucket A + the Guided Operator
  Workflow Gate Spec it would amend). Architect produces a Problem Decision Memo.
- **S2 — Product Plan.** *This document.* The Workflow Plan: scalable queue model,
  Shot/Slot/Assignment object model, honest slot classification, UI structure,
  non-authority statement.
- **S3 — Static Preview.** Preview Builder renders the queue + single-active-panel +
  Slot Editor as static HTML/CSS with one realistic 10-shot scenario + screenshot.
  Docs-only, no backend, no runtime (`gateway/**` untouched).
- **S4 — Operator Review.** Operator Reviewer judges from the front-line seat whether
  the v2 flow is independently operable at 10+ shots. PASS is the hard predecessor to
  any gate spec. `PASS WITH ISSUES` routes back to S2/S3 — never forward.
- **S5 — Gate Spec amendment or new Gate Spec.** Only after S4 PASS: either amend
  `…GUIDED_OPERATOR_WORKFLOW_GATE_SPEC_20260607.md` (preferred: a v2 B区 model
  amendment) or author a new Slot Workflow v2 Gate Spec, with binding zone rules,
  honesty classification, forbidden scope, PR slicing, acceptance rows, and a `<fill>`
  §10 signoff block.
- **only then runtime implementation (S6+).** Opens **only** after the gate spec's §10
  architect + reviewer signoff merges — an Owner-gated **L3** transition, one slice at
  a time, each new slice its own L3 decision per the Autopilot Execution Policy.

No step beyond S2 is authorized by this document. This plan stops at S2.

---

## 9. Scope Boundary

Stated explicitly:

- **docs-only** — this plan adds one `docs/design/` file and changes no runtime, no
  template, no service, no test.
- **not authority** — it is a Harness X Workflow Plan (artifact class: *not
  authority*); it does not supersede Bucket A or any contract.
- **does not reopen** #220 / #223 / #224 / #225 / #226 / #227 — those Guided Operator
  Workflow slices are merged substrate.
- **does not authorize runtime** — no implementation PR, no code, no S5→S6 transition.
- **does not modify the existing Gate Spec** — a v2 model requires a *future* Gate Spec
  amendment or new Gate Spec authored under the standard discipline (S5); this plan
  only recommends that path.
- **does not change generation / storage / routes / contracts / providers / delivery
  truth** — generation chain, `artifact_storage.py`, `shot_material_storage.py`,
  routes, `schemas/**`, `docs/contracts/**`, providers, Akool, delivery-candidate
  source, and the publish-readiness producer are all untouched; `official_publish_ready`
  stays `false`; Hot Follow and Digital Anchor get zero file touch and the DA five
  operations findings remain in force.

---

## 10. Deferred Items

Recorded only — **NOT fixed in this plan** (carried forward from the Guided Operator
Workflow closeout §6 and the Gate Spec §10):

1. **`基于素材意图`: supplement raw-enum copy** — the C区 compare block
   (`ms-regen-based-on`) renders the raw intent enum `supplement` instead of an
   operator label (e.g. 补充). Pre-existing copy issue; not addressed here.
2. **Legacy A-J delivery wording at `gateway/app/templates/task_workbench.html:1917`**
   (`ms-section-delivery-entry-line2`) — still shows
   `official_publish_ready=false；正式交付就绪：false` in the legacy A-J render (distinct
   from the primary D区, which already uses `正式交付就绪：否`). Left untouched by PR-4/PR-5
   per Owner instruction; not addressed here.
3. **Coordinator + PM §10 rows still `<fill>`** — the Guided Operator Workflow Gate
   Spec §10 and the closeout §7 four-party signoff Operations Coordinator + Product
   Manager rows remain `<fill>` (human signoff). This plan does not advance them.

A future docs-then-implementation follow-up (its own gate-spec-first, Owner-approved
slice) may address the copy items; the §10 human signoff is an Owner/operations
action. This plan modifies none of them.

---

*This is a docs-only Product Plan (Harness X S2). It authorizes no code, opens no
wave, supersedes no authority, modifies no Gate Spec, and does not advance any
signoff. The next controlled step is a Static Preview (S3) for Operator Review (S4),
and only a §10-signed Gate Spec amendment (S5) may open runtime implementation.*
