# Plan A · Live-Run Capture Template v1

Date: 2026-05-03 (template prepared empty)
Wave: ApolloVeo 2.0 Operator-Visible Surface Validation Wave
Status: **Empty capture template. To be filled by the human operations team during real execution; not AI-generated evidence.** Once the operations team completes a live-run, the contents of this template (after fill-in) get appended to [PLAN_A_OPS_TRIAL_WRITEUP_v1.md](PLAN_A_OPS_TRIAL_WRITEUP_v1.md) §8 (the placeholder section reserved for live-run results).

---

## 0. Binding fill-in rules

- **Authoring constraint.** Every field below MUST be filled by a human ops team member who personally observed the live-run on the deployed branch. AI agents MUST NOT fill these fields with inferred / synthesized / guessed content; doing so produces invalid trial evidence per [OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md) §0.1 and [PLAN_A_OPS_TRIAL_WRITEUP_v1.md](PLAN_A_OPS_TRIAL_WRITEUP_v1.md) §0.
- **Sample order.** Samples MUST be run in the order 1 → 6 per brief §7.1. Skipping samples or running out of order requires an explicit coordinator note in §3 below.
- **Pre-condition.** Before any sample is started, all eight conditions in [OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md) §12 must hold; the coordinator confirms them in §1 below.
- **Abort behaviour.** If any §8 trigger from the brief activates, pause; record in §3 / §4; resume only after the trigger is resolved or after coordinator/architect/reviewer concurrence.
- **Append destination.** When the live-run is complete, the filled fields from this template are appended to the §8 placeholder of [PLAN_A_OPS_TRIAL_WRITEUP_v1.md](PLAN_A_OPS_TRIAL_WRITEUP_v1.md) — preserving the field-name shape declared in that §8 placeholder.

---

## 1. Trial-window header (fill before first sample)

```
date / window:               <YYYY-MM-DD HH:MM..HH:MM TZ>
deployed branch / SHA:       <branch>@<short SHA at trial start>
trial environment URL:       <env hostname or environment label>
coordinator (name / role):   <name> / Operations team coordinator
operators (name / role)+:    <name> / <role>
                              <name> / <role>
                              ...
architect observer (name):   <name> (read-only attendance, sign off in §6)
reviewer observer (name):    <name> (read-only attendance, sign off in §6)

§12 conditions confirmed:
  1. §5 explanation 口径 briefed to operators verbatim:        [ ] yes  [ ] no
  2. Digital Anchor card + temp connect route hidden/disabled: [ ] yes  [ ] no
  3. Asset Supply / B-roll page hidden from navigation:        [ ] yes  [ ] no
  4. Trial scope restricted to §7.1 samples (1..6):            [ ] yes  [ ] no
  5. Coordinator has §8 risk list in front of them:            [ ] yes  [ ] no
  6. Matrix Script samples are fresh contract-clean per §0.1:  [ ] yes  [ ] no
  7. §0.2 product-meaning of source_script_ref briefed:        [ ] yes  [ ] no
  8. Operator transitional convention content://matrix-script/source/<token> in use: [ ] yes  [ ] no

If any condition is "no", DO NOT START the trial. Resolve and confirm before running Sample 1.
```

---

## 2. Per-sample capture

The fields below mirror the [PLAN_A_OPS_TRIAL_WRITEUP_v1.md](PLAN_A_OPS_TRIAL_WRITEUP_v1.md) §8 placeholder shape. Every sample slot is empty by design.

### 2.1 Sample 1 — Hot Follow short-clip golden path (brief §7.1.1)

```
- date / window:                 <fill>
- coordinator:                   <fill — name>
- operators:                     <fill — names>
- task_id:                       <fill — real task_id from deployed branch; AI must not guess>
- entry path used:               /tasks/newtasks → Hot Follow card → Hot Follow create surface
- success criteria observed (from write-up §4 Sample 1):
    [ ] task reaches final_ready=true
    [ ] Delivery Center publish_gate=true per derive_delivery_publish_gate
    [ ] publish completed
    [ ] Workbench shows current-attempt + accepted artifact rows
- abort triggers fired (none / list with timestamp):
    <fill>
- regressions filed (none / list of regression IDs / PRs):
    <fill>
- per-surface notes:
    Task Area:        <fill>
    Workbench:        <fill>
    Delivery Center:  <fill>
- gate-condition deltas (none / list):
    <fill>
- coordinator initials + timestamp:
    <fill>
```

### 2.2 Sample 2 — Hot Follow preserve-source route (brief §7.1.2)

```
- date / window:                 <fill>
- coordinator:                   <fill>
- operators:                     <fill>
- task_id:                       <fill>
- entry path used:               /tasks/newtasks → Hot Follow card → preserve-source compose
- success criteria observed (from write-up §4 Sample 2):
    [ ] dub_not_required_for_route flow visible
    [ ] scene-pack absence does NOT show as a publish blocker on Delivery Center
- abort triggers fired (none / list):
    <fill>
- regressions filed (none / list):
    <fill>
- per-surface notes:
    Task Area:        <fill>
    Workbench:        <fill>
    Delivery Center:  <fill>
- gate-condition deltas (none / list):
    <fill>
- coordinator initials + timestamp:
    <fill>
```

### 2.3 Sample 3 — Matrix Script fresh contract-clean small variation plan (brief §7.1.3)

```
- date / window:                 <fill>
- coordinator:                   <fill>
- operators:                     <fill>
- task_id:                       <fill>
- entry path used:               formal POST /tasks/matrix-script/new
- entry parameters used:
    target_language:             mm
    variation_target_count:      4
    topic:                       <fill — operator-chosen>
    source_script_ref:           content://matrix-script/source/<token>     (operator-chosen <token>)
- success criteria observed (from brief §7.1.3 (a)–(f) + write-up §4 Sample 3):
    [ ] (a) form rejected body-text input (HTTP 400)
    [ ] (a) form rejected publisher-URL input (HTTP 400 "scheme is not recognised")
    [ ] (a) form rejected bucket-URI input (HTTP 400 "scheme is not recognised")
    [ ] (a) form accepted operator transitional convention content://matrix-script/source/<token>
    [ ] (b) GET /tasks/{task_id} mounted Matrix Script Phase B variation panel
          (data-role="matrix-script-variation-panel", projection matrix_script_workbench_variation_surface_v1)
          empty-fallback messages absent
    [ ] (c) panel rendered 3 canonical axes (tone / audience / length)
    [ ] (c) panel rendered 4 cells (cell_001..cell_004)
    [ ] (c) panel rendered 4 slots (slot_001..slot_004)
    [ ] (c) cells[i].script_slot_ref ↔ slots[i].slot_id resolved end-to-end
    [ ] (d) Axes table rendered human-readable values per §8.G
          (no <built-in method values of dict object at 0x…> repr anywhere)
    [ ] (e) §8.E shared-shell suppression — no Hot Follow stage cards / pipeline summary /
          Burmese deliverable strip / dub-engine selectors / publish-hub CTA / debug-logs panel
          on visible HTML for kind=matrix_script (with <script> blocks stripped before grep)
    [ ] (f) publish-feedback closure mutated rows correctly per cell_id ↔ variation_id
- abort triggers fired (none / list):
    <fill>
- regressions filed (none / list):
    <fill>
- per-surface notes:
    Task Area:        <fill>
    Workbench:        <fill>
    Delivery Center:  <fill — note: Matrix Script Delivery Center is inspect-only this wave>
- gate-condition deltas (none / list):
    <fill>
- coordinator initials + timestamp:
    <fill>
```

### 2.4 Sample 4 — Matrix Script multi-language target (brief §7.1.4)

```
- date / window:                 <fill>
- coordinator:                   <fill>
- operators:                     <fill>
- task_id:                       <fill>
- entry path used:               formal POST /tasks/matrix-script/new
- entry parameters used:
    target_language:             vi
    variation_target_count:      <fill — operator-chosen>
    topic:                       <fill>
    source_script_ref:           content://matrix-script/source/<token>
- success criteria observed (from brief §7.1.4):
    [ ] target_language enum enforced (mm / vi only)
    [ ] slot language_scope.target_language carries vi end-to-end on persisted packet
- abort triggers fired (none / list):
    <fill>
- regressions filed (none / list):
    <fill>
- per-surface notes:
    Task Area:        <fill>
    Workbench:        <fill>
    Delivery Center:  <fill>
- gate-condition deltas (none / list):
    <fill>
- coordinator initials + timestamp:
    <fill>
```

### 2.5 Sample 5 — Matrix Script variation count boundary check (brief §7.1.5)

```
Sample 5a (variation_target_count=1)
- date / window:                 <fill>
- coordinator:                   <fill>
- operators:                     <fill>
- task_id:                       <fill>
- entry parameters used:
    target_language:             <fill — mm or vi>
    variation_target_count:      1
    source_script_ref:           content://matrix-script/source/<token>
- success criteria observed (from brief §7.1.5):
    [ ] cardinality of cells[] == 1
    [ ] cardinality of slots[] == 1
    [ ] cardinality of axes[] == 3 (canonical, fixed by §8.C addendum regardless of variation_target_count)
    [ ] panel still rendered real axes
- abort triggers fired:          <fill>
- per-surface notes:             <fill>

Sample 5b (variation_target_count=12)
- date / window:                 <fill>
- coordinator:                   <fill>
- operators:                     <fill>
- task_id:                       <fill>
- entry parameters used:
    target_language:             <fill — mm or vi>
    variation_target_count:      12
    source_script_ref:           content://matrix-script/source/<token>
- success criteria observed:
    [ ] cardinality of cells[] == 12
    [ ] cardinality of slots[] == 12
    [ ] cardinality of axes[] == 3 (canonical, fixed by §8.C)
    [ ] panel still rendered real axes
- abort triggers fired:          <fill>
- per-surface notes:             <fill>

- regressions filed (none / list):
    <fill>
- gate-condition deltas (none / list):
    <fill>
- coordinator initials + timestamp:
    <fill>
```

### 2.6 Sample 6 — Cross-line `/tasks` Board inspection (brief §7.1.6)

```
- date / window:                 <fill>
- coordinator:                   <fill>
- operators:                     <fill>
- tasks observed in flight (one per eligible line; from the prior samples):
    Hot Follow:        task_id=<fill>
    Matrix Script:     task_id=<fill>
    Digital Anchor:    n/a — preview-only this wave
- success criteria observed (from write-up §4 Sample 5):
    [ ] three lines render side-by-side
    [ ] Digital Anchor row contains no operator-actionable submit affordance
    [ ] sanitization at projections.py FORBIDDEN_OPERATOR_KEYS / sanitize_operator_payload
        strips any leaked vendor/provider/engine key (none observed)
- abort triggers fired (none / list):
    <fill>
- regressions filed (none / list):
    <fill>
- per-surface notes:
    Board:           <fill>
    Workbench:       <fill — for any task drilled into during the inspection>
    Delivery Center: <fill>
- gate-condition deltas (none / list):
    <fill>
- coordinator initials + timestamp:
    <fill>
```

---

## 3. Cross-cutting observations (fill after Sample 6)

```
Coordinator pre-trial guards retained throughout:           [ ] yes  [ ] no  + notes: <fill>
Any §7.2 (forbidden) sample attempted by an operator:       [ ] no   [ ] yes (record + halt action: <fill>)
Any vendor / model / provider / engine selector observed:   [ ] no   [ ] yes (HALT — file regression: <fill>)
Any third-line URL resolved:                                [ ] no   [ ] yes (HALT — file regression: <fill>)
Any operator-confusing publishable divergence (Board vs Workbench vs Delivery): [ ] no  [ ] yes  + notes: <fill>
Any drift from §3.1 / §3.2 static evidence on the deployed branch (compare against the pre-trial audit): [ ] no  [ ] yes (list: <fill>)

Free-text coordinator narrative (≤ 250 words):
<fill>
```

---

## 4. Regression / blocker capture (fill if anything was filed)

For each regression filed during the trial, record:

```
- regression_id / PR / issue:    <fill>
- date / time filed:             <fill>
- trigger (which §8 row):        <fill>
- task_id observed on:           <fill>
- one-line description:          <fill>
- temporary mitigation applied:  <fill>
- live-trial paused:             [ ] yes  [ ] no  (if yes, resume time: <fill>)
- coordinator initials:          <fill>
```

Repeat the block for each filed regression.

---

## 5. Final live-run judgment (fill at end of trial wave)

```
Total samples completed:                <fill> / 6
Samples aborted mid-run (list):         <fill>
Samples skipped (with reason):          <fill>
Total regressions filed:                <fill>
Net trial verdict (coordinator-side):
    [ ] PASS    — every §7.1 sample completed; no §8 trigger persisted; no scope drift.
    [ ] PARTIAL — at least one sample completed; one or more §8 triggers fired; resolution noted.
    [ ] FAIL    — coordinator unable to complete the wave per §12 conditions; reasons: <fill>

Plan E pre-condition #1 (per brief §9.1) — at least one full sample-wave entry recorded: [ ] satisfied  [ ] not satisfied
```

---

## 6. Signoff (fill after §1–§5 are complete)

```
Operations team coordinator
  Name:               <fill>
  Date / time:        <fill>
  Signature / handle: <fill>
  Statement:          I confirm §1–§5 entries reflect what I personally observed during the
                      live-run; the eight §12 conditions held throughout; no scope drift was
                      authored or hidden.

Architect
  Name:               <fill>
  Date / time:        <fill>
  Signature / handle: <fill>
  Statement:          I confirm no Plan E preparation, Platform Runtime Assembly entry,
                      Capability Expansion work, or frontend patching occurred during this
                      trial. The trial stayed inside the Operator-Visible Surface Validation
                      Wave gate.

Reviewer
  Name:               <fill>
  Date / time:        <fill>
  Signature / handle: <fill>
  Statement:          I confirm Plan E pre-condition #1 (per brief §9.1) is now satisfied;
                      remaining pre-conditions #2..#6 (per brief §9) hold.
```

---

## 7. Handoff back to the write-up

When §1–§6 are filled and signed, append the contents of §1 (header) and §2.1–§2.6 (per-sample capture) and §3–§5 (cross-cutting + regression + verdict) and §6 (signoff) to [PLAN_A_OPS_TRIAL_WRITEUP_v1.md](PLAN_A_OPS_TRIAL_WRITEUP_v1.md) §8 placeholder, preserving the field-name shape from that §8 placeholder. Do **not** mutate any other section of the write-up. Do **not** mutate the brief. Plan E gate spec authoring then becomes the next allowed engineering action per [docs/architecture/apolloveo_2_0_unified_alignment_map_v1.md](../architecture/apolloveo_2_0_unified_alignment_map_v1.md) §7.2.

End of empty live-run capture template.
