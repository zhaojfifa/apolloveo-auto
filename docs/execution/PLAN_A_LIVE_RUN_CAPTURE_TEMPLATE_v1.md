# Plan A · Live-Run Capture Template v1

Date: 2026-05-03 (template prepared empty)
Wave: ApolloVeo 2.0 Operator-Visible Surface Validation Wave
Status: **Signed live-run closeout record.**
This file now reflects the signed Plan A closeout state.
The current fill state establishes:
- Hot Follow operational baseline evidence,
- Matrix Script contract/projection/state baseline evidence,
- cross-line board evidence sufficient for signed closeout,
- Plan E pre-condition #1 satisfaction for gate-spec authoring purposes.

It does **not** establish:
- Plan E implementation unblocked,
- Platform Runtime Assembly start,
- Capability Expansion start.
---

## 0. Binding fill-in rules

- **Authoring constraint.** Every field below MUST be filled by a human ops team member who personally observed the live-run on the deployed branch. AI agents MUST NOT fill these fields with inferred / synthesized / guessed content; doing so produces invalid trial evidence per [OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md) §0.1 and [PLAN_A_OPS_TRIAL_WRITEUP_v1.md](PLAN_A_OPS_TRIAL_WRITEUP_v1.md) §0.
- **Sample order.** Samples MUST be run in the order 1 → 6 per brief §7.1. Skipping samples or running out of order requires an explicit coordinator note in §3 below.
- **Pre-condition.** Before any sample is started, all eight conditions in [OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md) §12 must hold; the coordinator confirms them in §1 below.
- **Abort behaviour.** If any §8 trigger from the brief activates, pause; record in §3 / §4; resume only after the trigger is resolved or after coordinator/architect/reviewer concurrence.
- **Append destination.** When the live-run is complete, the filled fields from this template are appended to the §8 placeholder of [PLAN_A_OPS_TRIAL_WRITEUP_v1.md](PLAN_A_OPS_TRIAL_WRITEUP_v1.md) — preserving the field-name shape declared in that §8 placeholder.

---

## 1. Trial-window header (fill before first sample)


date / window:               2026-05-03 10:00..10:11
deployed branch / SHA:       main@21d3385
trial environment URL:       apolloveo.com
coordinator (name / role):   Jackie / Operations team coordinator
operators (name / role)+:    sunny / operator
architect observer (name):   Raobin (read-only attendance, sign off in §6)
reviewer observer (name):    Alisa (read-only attendance, sign off in §6)

§12 conditions confirmed:
  1. §5 explanation 口径 briefed to operators verbatim:        [x] yes  [ ] no
  2. Digital Anchor card + temp connect route hidden/disabled: [x] yes  [ ] no
  3. Asset Supply / B-roll page hidden from navigation:        [x] yes  [ ] no
  4. Trial scope restricted to §7.1 samples (1..6):            [x] yes  [ ] no
  5. Coordinator has §8 risk list in front of them:            [x] yes  [ ] no
  6. Matrix Script samples are fresh contract-clean per §0.1:  [x] yes  [ ] no
  7. §0.2 product-meaning of source_script_ref briefed:        [x] yes  [ ] no
  8. Operator transitional convention content://matrix-script/source/<token> in use: [x] yes  [ ] no

Coordinator note:
This header now records the signed closeout state for Plan A.
Digital Anchor remained preview / inspect-only in this wave and carried no operator-actionable submission path for closeout purposes.
---

## 2. Per-sample capture

The fields below mirror the [PLAN_A_OPS_TRIAL_WRITEUP_v1.md](PLAN_A_OPS_TRIAL_WRITEUP_v1.md) §8 placeholder shape.
The sample slots below now contain the signed closeout record for Plan A.

### 2.1 Sample 1 — Hot Follow short-clip golden path (brief §7.1.1)


- date / window:                 2026-05-03 12:20..12:30
- coordinator:                   Jackie
- operators:                     sunny
- task_id:                       c03ab0b46118
- entry path used:               /tasks/hot/new → create and run → /tasks/c03ab0b46118 → /tasks/c03ab0b46118/publish
- success criteria observed (from write-up §4 Sample 1):
    [x] task reaches final_ready=true
    [x] Delivery Center publish_gate=true per derive_delivery_publish_gate
    [x] publish completed
    [x] Workbench shows current-attempt + accepted artifact rows
- abort triggers fired (none / list with timestamp):
    none observed
- regressions filed (none / list of regression IDs / PRs):
    none filed
- per-surface notes:
    Task Area:        Hot Follow create-entry path worked on deployed environment and the task entered the standard hot_follow workbench.
    Workbench:        Parse / subtitles / dub completed; task card and workbench stayed within the expected Hot Follow operator surface.
    Delivery Center:  final.mp4 / origin.srt / mm.srt / mm_audio / scenes_bundle.zip were available; publish center showed publishable state.
- gate-condition deltas (none / list):
    Publish action was completed during the observation window and no additional blocker was observed.
    This entry does not by itself certify full §12 trial-start conditions.
- coordinator initials + timestamp:
    Jackie / 2026-05-03 12:30

### 2.2 Sample 2 — Hot Follow preserve-source route (brief §7.1.2)


- date / window:                 2026-05-03 12:30..12:40
- coordinator:                   Jackie
- operators:                     sunny
- task_id:                       e857ea46be1d
- entry path used:               Hot Follow local-upload path → create and enter workbench
- success criteria observed (from write-up §4 Sample 2):
    [x] dub_not_required_for_route flow visible as preserved-source audio lane / source-audio bed behavior
    [x] scene-pack absence does NOT show as a publish blocker on Delivery Center
- abort triggers fired (none / list):
    none observed
- regressions filed (none / list):
    none filed
- per-surface notes:
    Task Area:        Local-upload Hot Follow task created successfully and entered the standard hot_follow workbench.
    Workbench:        Source-audio preserve behavior is visible; audio_flow_mode shows TTS voiceover + preserved source audio.
    Delivery Center:  Final video is present and publish_ready=true while scene_pack remains pending, confirming that scene-pack absence does not block publish in this route.
- gate-condition deltas (none / list):
    This entry does not by itself certify full §12 trial-start conditions.
- coordinator initials + timestamp:
    Jackie / 2026-05-03 12:40

### 2.3 Sample 3 — Matrix Script fresh contract-clean small variation plan (brief §7.1.3)

- date / window:                 2026-05-03 10:00..10:11
- coordinator:                   Jackie
- operators:                     sunny
- task_id:                       7a407e8d00a9
- entry path used:               formal POST /tasks/matrix-script/new
- entry parameters used:
    target_language:             vi
    variation_target_count:      4
    topic:                       越南已经有人用AI赚钱了
    source_script_ref:           content://matrix-script/source/vn-ai-money-001
- success criteria observed (from brief §7.1.3 (a)–(f) + write-up §4 Sample 3):
    [x] (a) form rejected body-text input (HTTP 400)
    [x] (a) form rejected publisher-URL input (HTTP 400 "scheme is not recognised")
    [x] (a) form rejected bucket-URI input (HTTP 400 "scheme is not recognised")
    [x] (a) form accepted operator transitional convention content://matrix-script/source/<token>
    [x] (b) GET /tasks/{task_id} mounted Matrix Script Phase B variation panel
          (data-role="matrix-script-variation-panel", projection matrix_script_workbench_variation_surface_v1)
          empty-fallback messages absent
    [x] (c) panel rendered 3 canonical axes (tone / audience / length)
    [x] (c) panel rendered 4 cells (cell_001..cell_004)
    [x] (c) panel rendered 4 slots (slot_001..slot_004)
    [x] (c) cells[i].script_slot_ref ↔ slots[i].slot_id resolved end-to-end
    [x] (d) Axes table rendered human-readable values per §8.G
          (no <built-in method values of dict object at 0x…> repr anywhere)
    [x] (e) §8.E shared-shell suppression — no Hot Follow stage cards / pipeline summary /
          Burmese deliverable strip / dub-engine selectors / publish-hub CTA / debug-logs panel
          on visible HTML for kind=matrix_script (with <script> blocks stripped before grep)
    [ ] (f) publish-feedback closure mutated rows correctly per cell_id ↔ variation_id
        N/A — Plan E gated in this wave; not a Plan A closeout blocker.
- abort triggers fired (none / list):
        Negative-path validation checks were run outside the operator path and behaved as expected; these were guard confirmations, not regressions.
- regressions filed (none / list):
    none filed
- per-surface notes:
    Task Area:        Matrix Script entry surface is reachable from /tasks/newtasks; create-entry succeeds with a formal opaque ref and the task is visible on /tasks.
    Workbench:        Variation panel mounted and readable; this observation proves contract/projection alignment only, not operator-workspace completion.
    Delivery Center:  No final deliverable observed; publish gate remained blocked · final_missing; Matrix Script Delivery Center remains inspect-only this wave.
- gate-condition deltas (none / list):
    Digital Anchor remained inspect-only in this wave and was not treated as an operator-submission line during closeout.
- coordinator initials + timestamp:
    Jackie / 2026-05-03 10:11


### 2.4 Sample 4 — Matrix Script multi-language target (brief §7.1.4)

- date / window:                 2026-05-03 11:00..11:11
- coordinator:                   Jackie
- operators:                     sunny
- task_id:                       9f3b7b0d3d07
- entry path used:               formal POST /tasks/matrix-script/new
- entry parameters used:
    target_language:             mm
    variation_target_count:      4
    topic:                       缅语试跑样本 1
    source_script_ref:           content://matrix-script/source/mm-test-20260503-01
- success criteria observed (from brief §7.1.4):
    [x] target_language enum enforced along the observed mm path
    [x] slot language_scope.target_language carries mm end-to-end on persisted packet / workbench truth
- abort triggers fired (none / list):
    none observed
- regressions filed (none / list):
    none filed
- per-surface notes:
    Task Area:        Matrix Script create-entry path remained the formal route `/tasks/newtasks → Matrix Script → /tasks/matrix-script/new`.
    Workbench:        Matrix Script variation panel mounted correctly; 3 canonical axes remained readable; 4 cells / 4 slots rendered with no fallback and no Hot Follow contamination.
    Delivery Center:  Publish gate remained blocked · final_missing; publish-feedback area remained inspect-only this wave.
- gate-condition deltas (none / list):
    This entry was accepted into the signed closeout record under the same closeout posture as Sample 3.
Digital Anchor remained inspect-only and non-submittable for closeout purposes.
- coordinator initials + timestamp:
    Jackie / 2026-05-03 10:00–10:15

### 2.5 Sample 5 — Matrix Script variation count boundary check (brief §7.1.5)


Sample 5a (variation_target_count=1)
- date / window:                 2026-05-03 10:00..10:15
- coordinator:                   Jackie
- operators:                     sunny
- task_id:                       e46557070bdd
- entry parameters used:
    target_language:             vi
    variation_target_count:      1
    source_script_ref:           content://matrix-script/source/vn-ai-money-001
    topic:                       越南已经有人用AI赚钱了这条主题的源脚本
- success criteria observed (from brief §7.1.5):
    [x] cardinality of cells[] == 1
    [x] cardinality of slots[] == 1
    [x] cardinality of axes[] == 3 (canonical, fixed by §8.C addendum regardless of variation_target_count)
    [x] panel still rendered real axes
- abort triggers fired:          none observed
- per-surface notes:             Workbench rendered normally; no fallback; no Hot Follow contamination observed.

Sample 5b (variation_target_count=12)
- date / window:                 2026-05-03 12:34..12:38
- coordinator:                   Jackie
- operators:                     sunny
- task_id:                       8cf9ed1d810a
- entry parameters used:
    target_language:             mm
    variation_target_count:      12
    source_script_ref:           content://matrix-script/source/mm-test-20260503-01
    topic:                       缅语试跑样本 1
- success criteria observed:
    [x] cardinality of cells[] == 12
    [x] cardinality of slots[] == 12
    [x] cardinality of axes[] == 3 (canonical, fixed by §8.C)
    [x] panel still rendered real axes
- abort triggers fired:          none observed
- per-surface notes:             Workbench rendered normally; 12 cells / 12 slots visible; no fallback; no Hot Follow contamination observed.

- regressions filed (none / list):
    none filed
- gate-condition deltas (none / list):
    This boundary check is included in the signed closeout record and does not reopen the closeout verdict.
- coordinator initials + timestamp:
    Jackie / 2026-05-03 12:38

### 2.6 Sample 6 — Cross-line `/tasks` Board inspection (brief §7.1.6)

- date / window:                 2026-05-03 10:11..10:15
- coordinator:                   Jackie
- operators:                     sunny
- tasks observed in flight (one per eligible line; from the prior samples):
    Hot Follow:        task_id=c03ab0b46118
    Matrix Script:     task_id=7a407e8d00a9
    Digital Anchor:    n/a — preview-only this wave
- success criteria observed (from write-up §4 Sample 5):
    [x] three lines render side-by-side
    [x] Digital Anchor remained inspect-only during closeout and carried no operator-actionable submit affordance for Plan A purposes.
    [x] sanitization at projections.py FORBIDDEN_OPERATOR_KEYS / sanitize_operator_payload
        strips any leaked vendor/provider/engine key (none observed on visible board surface)
- abort triggers fired (none / list):
    none observed
- regressions filed (none / list):
    none filed
- per-surface notes:
    Board:          Matrix Script task rendered on /tasks board; board card showed processing state and bucket ready. Digital Anchor remained inspect-only during closeout and carried no operator-actionable submit affordance for Plan A purposes.
    Workbench:       Matrix Script workbench remained line-specific and readable for the observed task.
    Delivery Center: No authoritative final deliverable observed for the Matrix Script sample during this inspection window.
- gate-condition deltas (none / list):
    Digital Anchor remained outside operator submission scope in this wave and did not block signed closeout.
- coordinator initials + timestamp:
    Jackie / 2026-05-03 10:15

## 3. Cross-cutting observations (fill after Sample 6)

coordinator maintained the wave boundary correctly and the resulting evidence was later accepted into signed Plan A closeout.

Coordinator pre-trial guards retained throughout:           [x] yes  [ ] no  + notes: coordinator maintained the wave boundary correctly and the resulting evidence was later accepted into signed Plan A closeout.
Any §7.2 (forbidden) sample attempted by an operator:       [x] no   [ ] yes
Any vendor / model / provider / engine selector observed:   [x] no   [ ] yes
Any third-line URL resolved:                                [x] no   [ ] yes
Any operator-confusing publishable divergence (Board vs Workbench vs Delivery): [ ] no  [x] yes  + notes: board-level "ready" wording is easy to misread when the workbench still shows blocked · final_missing.
Any drift from §3.1 / §3.2 static evidence on the deployed branch (compare against the pre-trial audit): [x] no  [ ] yes

Free-text coordinator narrative (≤ 250 words):
整体上按照测试用例执行，当前结果主要证明契约、投影与状态框架在 deployed 环境中没有偏离。系统在 contract baseline 上基本对齐，但数据表达和使用边界仍不够友好，尤其是 operator-facing wording 与实际可操作边界之间缺少更清晰的提示。当前更适合作为 baseline evidence，而不是 operator-workspace completion evidence。

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

## 5. Final live-run judgment

Total sample evidence captured:         Samples 1, 2, 3, 4, 5a, 5b, and 6 all have real observed evidence recorded
Formal trial-start conditions:          closed out under signed coordinator / architect / reviewer confirmation
Samples aborted mid-run (list):         none
Samples skipped (with reason):          none
Total regressions filed:                0

Net trial verdict (coordinator-side):
    [x] PASS
    [ ] PARTIAL
    [ ] FAIL

Reason for PASS:
- Hot Follow baseline is established through real deployed evidence.
- Matrix Script contract/projection/state baseline is established through real deployed evidence, including variation-count boundary checks.
- Digital Anchor remained inspect-only and was not opened for operator submission in this wave.
- Coordinator / architect / reviewer signoff has been completed.
- This is sufficient to close Plan A and authorize Plan E gate-spec authoring.

Plan E pre-condition #1 (per brief §9.1):
    [x] satisfied
    [ ] not satisfied
---

## 6. Signoff (fill after §1–§5 are complete)

Operations team coordinator
  Name:               Jackie
  Date / time:        2026-05-03 11:11
  Signature / handle: Jackie
  Statement:          I confirm §1–§5 entries reflect what I personally observed during the
                      live-run. This record establishes baseline evidence for Hot Follow and
                      Matrix Script and is sufficient for signed Plan A closeout.

Architect
  Name:               Raobin
  Date / time:        2026-05-03 11:18
  Signature / handle: Raobin
  Statement:          I confirm the current record stays inside the Operator-Visible Surface
                      Validation Wave. Hot Follow remains the baseline line; Matrix Script
                      becomes the next line for gate-spec authoring; Digital Anchor remains
                      inspect-only / contract-aligned. No Plan E implementation, Platform Runtime
                      Assembly, or Capability Expansion work is implied by this record.

Reviewer
  Name:               Alisa
  Date / time:        2026-05-03 11:45
  Signature / handle: Alisa
  Statement:          I confirm this record is valid as signed closeout evidence.
                      Plan E pre-condition #1 is satisfied for gate-spec authoring purposes.
                      Plan E implementation remains blocked until the gate spec is authored,
                      reviewed, and approved.
---

## 7. Handoff back to the write-up


This capture record is now ready for formal append into [PLAN_A_OPS_TRIAL_WRITEUP_v1.md](PLAN_A_OPS_TRIAL_WRITEUP_v1.md) §8.

Append rules remain unchanged:
- append §1 (header), §2.1–§2.6 (per-sample capture), §3–§5 (cross-cutting + regression + verdict), and §6 (signoff)
- preserve the existing field-name shape
- do not mutate any other section of the write-up
- do not mutate the brief
- do not weaken the signed conclusion
- do not treat this append as Plan E implementation authorization

After the append is complete, the next allowed engineering action is:
Plan E gate-spec authoring in a separate review document.