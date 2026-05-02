# Matrix Script Follow-up Blocker Review v1

Status: BLOCKING — Plan A live-run evidence collection on Matrix Script
remains suspended. The §8.A / §8.B / §8.C / §8.D chain that closed the
prior blocker review is **not sufficient** to authorize ops trial use:
new live operator observations have surfaced three additional defects
(§8.E / §8.F / §8.G) that the prior chain did not catch.

Authority: ApolloVeo 2.0 Chief Architect, under
[CURRENT_ENGINEERING_FOCUS.md](../../CURRENT_ENGINEERING_FOCUS.md)
(Factory Alignment Review Gate active),
[docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md)
(Operator-Visible Surface Validation Wave), and the prior blocker review
[docs/reviews/matrix_script_trial_blocker_and_realign_review_v1.md](matrix_script_trial_blocker_and_realign_review_v1.md).

Date: 2026-05-03.

---

## 1. Executive Conclusion

The previous correction chain (§8.A entry-form ref-shape guard, §8.B
panel-dispatch confirmation, §8.C Phase B deterministic authoring, §8.D
operator brief correction) is **all individually correct against its
own gate**, but the gate set itself was **incomplete**. Live operator
observations on a fresh post-§8.A/§8.B/§8.C/§8.D Matrix Script task
(`task_id=415ea379ebc6`) demonstrate three additional defects that
prevent the line from being operator-trial-ready:

1. **§8.E — Workbench shell contamination.** The Matrix Script Phase B
   variation panel mounts correctly per §8.B, but the **shared shell
   template** (`task_workbench.html`) unconditionally renders Hot
   Follow stage controls (parse / subtitle / dub / pack / Burmese
   subtitle / Burmese audio / `字幕轨道` / `whisper+gemini` /
   `auto-fallback`) on top of every task regardless of `kind`. The
   resulting page is a Hot Follow workbench *plus* a Matrix Script
   variation panel — not a Matrix Script workbench. This is a real
   shell defect that §8.B's "PASS — no narrow fix required"
   conclusion did not catch.
2. **§8.F — Source-ref discipline is semantically loose.** The §8.A
   guard accepts `https://` / `http://` as opaque-ref schemes, so an
   ordinary content URL (e.g. `https://news.qq.com/rain/a/...`) passes.
   The contract intent is "opaque ref handle"; operators are using
   article URLs because the repo has **no minting / lookup path** for
   `content://` / `task://` / `asset://` / `ref://`. §8.A closed the
   "raw script body" hole without tightening the "raw publisher URL"
   hole, and without giving operators a way to obtain the intended
   opaque handles.
3. **§8.G — Phase B panel rendering bug.** The `axes[].values` column
   in the Matrix Script variation panel renders as `<built-in method
   values of dict object at 0x…>` instead of the actual axis values.
   Root cause: a Jinja attribute-vs-item access bug
   (`{{ axis.values }}`) — Jinja resolves `.values` to the dict's
   built-in `values()` *method* (a bound callable) before falling back
   to the `"values"` key, so neither `is mapping` nor `is iterable`
   matches and the `else` branch renders the method repr. Cosmetic in
   appearance but operator-blocking in practice: the entire Phase B
   "what does this variation look like" inspection surface is unreadable.

§8.B did **overstate** success: it verified `panel_kind="matrix_script"`
resolves and the variation panel mounts inside the shared shell, but it
did not verify shell suppression of unrelated line controls. §8.D
remains correct as a documentation correction against the prior accepted
gate set; §8.D did not (and should not have) introduced new code
behavior.

The current mixed workbench result — and the publish-URL-as-ref
slippage and the axes-render bug — are **sufficient to keep Matrix
Script ops trial BLOCKED**. New gated correction items §8.E / §8.F /
§8.G are required before retry sample creation can proceed.

This review is the new authority. **Do not implement in this step.**

## 2. Reading Declaration

There is **no top-level `CLAUDE.md`** in this repository. Per the
standing repo discipline carried in
[ENGINEERING_RULES.md](../../ENGINEERING_RULES.md),
[CURRENT_ENGINEERING_FOCUS.md](../../CURRENT_ENGINEERING_FOCUS.md),
[ENGINEERING_STATUS.md](../../ENGINEERING_STATUS.md),
[ENGINEERING_CONSTRAINTS_INDEX.md](../../ENGINEERING_CONSTRAINTS_INDEX.md),
[PROJECT_RULES.md](../../PROJECT_RULES.md), and
[docs/ENGINEERING_INDEX.md](../ENGINEERING_INDEX.md), the equivalent
authority chain followed for this review:

- engineering rules / current focus / status / constraints index;
- docs index;
- prior blocker review [matrix_script_trial_blocker_and_realign_review_v1.md](matrix_script_trial_blocker_and_realign_review_v1.md);
- §8.A / §8.B / §8.C / §8.D execution logs;
- Plan A trial readiness brief and coordinator write-up;
- Matrix Script frozen contracts;
- workbench shell + projection + delivery + create-entry implementation surface (read-only inspection).

Authority surface inspected (read-only):

- [CURRENT_ENGINEERING_FOCUS.md](../../CURRENT_ENGINEERING_FOCUS.md), [ENGINEERING_STATUS.md](../../ENGINEERING_STATUS.md), [ENGINEERING_RULES.md](../../ENGINEERING_RULES.md)
- [docs/product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md)
- [docs/reviews/matrix_script_trial_blocker_and_realign_review_v1.md](matrix_script_trial_blocker_and_realign_review_v1.md)
- [docs/execution/MATRIX_SCRIPT_A_REF_SHAPE_GUARD_EXECUTION_LOG_v1.md](../execution/MATRIX_SCRIPT_A_REF_SHAPE_GUARD_EXECUTION_LOG_v1.md)
- [docs/execution/MATRIX_SCRIPT_B_DISPATCH_CONFIRMATION_EXECUTION_LOG_v1.md](../execution/MATRIX_SCRIPT_B_DISPATCH_CONFIRMATION_EXECUTION_LOG_v1.md)
- [docs/execution/MATRIX_SCRIPT_C_PHASE_B_AUTHORING_EXECUTION_LOG_v1.md](../execution/MATRIX_SCRIPT_C_PHASE_B_AUTHORING_EXECUTION_LOG_v1.md)
- [docs/execution/MATRIX_SCRIPT_D_OPERATOR_BRIEF_CORRECTION_EXECUTION_LOG_v1.md](../execution/MATRIX_SCRIPT_D_OPERATOR_BRIEF_CORRECTION_EXECUTION_LOG_v1.md)
- [docs/contracts/matrix_script/task_entry_contract_v1.md](../contracts/matrix_script/task_entry_contract_v1.md) (with §8.A and §8.C addenda)
- [docs/contracts/matrix_script/workbench_variation_surface_contract_v1.md](../contracts/matrix_script/workbench_variation_surface_contract_v1.md)
- [docs/contracts/matrix_script/result_packet_binding_artifact_lookup_contract_v1.md](../contracts/matrix_script/result_packet_binding_artifact_lookup_contract_v1.md)
- [docs/contracts/workbench_panel_dispatch_contract_v1.md](../contracts/workbench_panel_dispatch_contract_v1.md)
- [gateway/app/templates/task_workbench.html](../../gateway/app/templates/task_workbench.html)
- [gateway/app/services/workbench_registry.py](../../gateway/app/services/workbench_registry.py)
- [gateway/app/services/matrix_script/create_entry.py](../../gateway/app/services/matrix_script/create_entry.py)
- [gateway/app/services/matrix_script/phase_b_authoring.py](../../gateway/app/services/matrix_script/phase_b_authoring.py)
- [gateway/app/services/matrix_script/workbench_variation_surface.py](../../gateway/app/services/matrix_script/workbench_variation_surface.py)
- [gateway/app/routers/tasks.py](../../gateway/app/routers/tasks.py) (workbench page handler at line 1481-1513)

## 3. Newly Observed Defects

Live observations on `task_id=415ea379ebc6`, a fresh post-§8.A/§8.B/§8.C
Matrix Script sample (created via the formal `/tasks/matrix-script/new`
POST under §8.A's guard, with §8.C's deterministic Phase B authoring
running at task creation):

| # | Observed fact | True cause class |
|---|---|---|
| 1 | Workbench renders `字幕轨道 / 字幕: whisper+gemini · 配音: auto-fallback / 步骤1-解析与下载 / 步骤2-字幕 / 步骤3-缅语配音 / 步骤4-打包 / 缅语配音 / 缅文字幕 / mm.srt / mm_audio` on a `kind=matrix_script` task. | (IV) **Shell contamination** — `task_workbench.html` is shared between Hot Follow and Matrix Script (and `default`); it renders Hot Follow stage controls unconditionally regardless of `kind`. §8.E. |
| 2 | Matrix Script Phase B variation panel also mounts correctly above. | (—) Per §8.B's PASS — dispatch is correct; the Hot Follow shell renders **alongside** the Phase B panel, not instead of it. |
| 3 | Operator submitted `https://news.qq.com/rain/a/20260502A05LYM00` as `source_script_ref` and the §8.A guard accepted it. | (V) **Source-ref semantic looseness** — `https`/`http` are in the §8.A accepted-scheme set, so any article URL passes. The contract intent ("opaque ref handle") is not enforceable while the accepted set includes general web schemes. §8.F. |
| 4 | Operators have no documented or implemented way to obtain `content://` / `task://` / `asset://` / `ref://` handles. | (V) **Operator usability gap** — the brief instructs operators to use opaque schemes but the repo has no minting / lookup service. The Plan C asset-library work (C1) that would provide this is gated to Plan E. §8.F. |
| 5 | `axes[].values` column renders as `<built-in method values of dict object at 0x7c7ce4739240>` for `tone`, `audience`, **and** `length`. | (VI) **Template attribute-vs-item access bug** — `{{ axis.values }}` resolves to the dict's bound `values()` method before the `"values"` key. Both `is mapping` and `is iterable and not string` test against the bound method (which is neither), so the `else` branch renders `repr(bound_method)`. §8.G. |

Cause classes (IV) / (V) / (VI) extend the (I) / (II) / (III) taxonomy
of the prior blocker review §3.

## 4. Reassessment of Prior Gates

### 4.1 §8.A

**Verdict: still PASS for the narrow gate it defined; SCOPE-LIMITED.**

§8.A enforced "no body text in `source_script_ref`" via single-line /
no-whitespace / ≤512-char / closed-scheme-or-bare-token rules. Its
contract addendum at `task_entry_contract_v1.md` §"Source script ref
shape (addendum, 2026-05-02)" pinned the closed scheme set as
exhaustive at v1.

What §8.A did not do:

- did not narrow accepted schemes to "ones the operator can actually
  obtain inside this product" — `https`/`http` were left in for
  pragmatic reasons (operators were known to have URLs already), but
  this leaves the contract-intended "opaque" property unenforceable
  against general content URLs.
- did not provide a minting / lookup path for `content://` /
  `task://` / `asset://` / `ref://`.
- did not author operator-facing documentation explaining how to
  obtain an opaque handle.

§8.A is **not retracted**. The body-text-paste hole is closed. The
remaining gap is a §8.F concern, not a §8.A regression.

### 4.2 §8.B

**Verdict: PASS for what it asserted; OVERSTATED what it implied.**

§8.B asserted (and proved) that `resolve_line_specific_panel(packet)`
returns `panel_kind="matrix_script"` and that `task_workbench.html`
mounts the Phase B variation panel section with the projection name,
both ref_ids, and no empty-slot fallback — for a fresh contract-clean
sample. All those assertions remain true on the current branch.

What §8.B's "PASS — no narrow fix required" conclusion implied that
turns out to be wrong:

- it implied the operator-visible result on `GET /tasks/{task_id}` for
  `kind=matrix_script` is "the Matrix Script workbench". The actual
  result is "the **shared shell** plus the Matrix Script variation
  panel mounted on top". The shared shell renders Hot Follow stage
  controls (parse / subtitle / dub / pack / Burmese-specific items)
  unconditionally because no `{% if task.kind != "matrix_script" %}`
  (or equivalent) gates them. This is exactly the "the operator
  could not tell" hypothesis from the prior blocker review §5
  ("Workbench model" verdict) — but it materialises as **wrong shell
  controls visible alongside the right panel**, not as **the right
  panel missing**.
- the §8.B execution log §3.3 explicitly noted that `task_workbench.html`
  is "the shared workbench shell, not a 'generic engineering shell'
  in the sense of 'no line-specific surface'", and that "per-line
  dispatch in this wave is via `panel_kind` mounting inside the
  shared shell, not via per-line template files". That description
  is accurate for what the dispatch contract guarantees, but it did
  not extend to "the shared shell is line-aware about which non-panel
  controls it renders". §8.B did not test for shell suppression
  because it accepted that the shell was the shared shell and
  reasoned that mounting was sufficient.

§8.B is **not retracted** as a dispatch confirmation. The new
authority required is §8.E ("workbench shell line-conditional
rendering"), which is a separately scoped concern: dispatch puts the
right panel in; shell hygiene takes the wrong stage controls out.

### 4.3 §8.C

**Verdict: PASS for the planner; PARTIAL for the projector→template
join, due to §8.G.**

§8.C produced a deterministic planner that emits populated
`variation_matrix.delta.axes[]/cells[]` and `slot_pack.delta.slots[]`,
proved round-trip integrity, and asserted "rendered HTML carries real
axes/cells/slots". The render markers asserted by §8.C's tests
(`cell_001..cell_004`, `slot_001..slot_004`, axis ids `tone /
audience / length`, at least one tone token, at least one audience
token, empty-fallback messages absent) **are still all present**. The
planner output is correct.

What §8.C tests did not catch:

- the `axes[].values` column-cell rendering. The §8.C test
  `test_get_workbench_renders_real_axes_cells_slots` asserts
  presence of axis ids and presence of *some* tone / audience
  tokens in the response body, but it does not assert that the
  values are rendered correctly *next to their axis ids*. The
  tone-token assertion passes because `formal` / `casual` /
  `playful` appear elsewhere on the page (in cell axis selections
  like `tone=formal`), so the broken `{{ axis.values }}` rendering
  in the axes table escapes the assertion.

§8.C is **not retracted** as a planner. §8.G is a narrow template
fix orthogonal to the planner; it does not invalidate §8.C's authored
truth.

### 4.4 §8.D

**Verdict: still PASS as a documentation correction against the prior
gate set.**

§8.D corrected the operator brief and the coordinator write-up to
reflect the accepted §8.A / §8.B / §8.C results. It made no code,
contract, or schema changes by design. The brief's §0.1 binding
sample-validity rule is correct on its own terms — a fresh
post-§8.A/§8.B/§8.C sample really does carry populated deltas, the
panel really does mount, the dispatch really does resolve.

What §8.D could not have caught (because the source authority was the
prior gate set):

- §8.E shell contamination — §8.D inherited §8.B's "panel mounts ⇒
  workbench is correct" reasoning; the §0.1 sample-validity rule's
  fourth criterion ("workbench mounts the Matrix Script Phase B
  variation panel … with real resolvable axes / cells / slots") is
  still true on a fresh sample, but the rule is **silent** about
  which other shell controls render alongside.
- §8.F semantic-loose ref — §8.D inherited §8.A's accepted-scheme
  set verbatim; the brief's §3.2 / §6.2 ref-shape enumeration lists
  `https://` / `http://` as accepted, so an operator following the
  brief literally would still get a publisher article URL through.
- §8.G axes-render bug — §8.D had no test surface to inherit; the
  planner-side §8.C tests passed, so the brief reasonably assumed
  the panel renders correctly.

§8.D should be **extended** (not retracted) once §8.E / §8.F / §8.G
land — at that point the brief's §0.1 rule needs three additional
criteria (no Hot Follow shell controls present; opaque ref minted via
the documented path; axes table renders human-readable values) and
the §6.2 sample profile needs the `https`/`http` scheme entries
removed (or qualified). That is a §8.H follow-up, not a §8.D
retraction.

## 5. §8.E Review — Workbench Shell Suppression

### Observed defect

[`gateway/app/templates/task_workbench.html`](../../gateway/app/templates/task_workbench.html)
is the template selected by [`workbench_registry.py:46-48`](../../gateway/app/services/workbench_registry.py:46)
when `task.kind` is anything other than `apollo_avatar` or
`hot_follow` (the only two registered alternatives). For
`kind=matrix_script`, that means `WORKBENCH_REGISTRY["default"]` →
`task_workbench.html` is rendered.

That template currently renders, **unconditionally for every task**:

- the pipeline summary `字幕: {subtitles_mode} · 配音: {dub_mode}` at
  lines 187-193 (showing Hot Follow's `whisper+gemini` /
  `auto-fallback` defaults even when the line has no dub flow);
- the `字幕轨道` (subtitle track) meta row at lines 170-181;
- the Hot Follow stage cards `步骤1-解析与下载 / 步骤2-字幕 /
  步骤3-缅语配音 / 步骤4-打包` at lines 562-635;
- the Hot Follow deliverables strip including `缅文字幕` / `mm.srt /
  mm.txt / origin.srt` and `缅语配音` / `mm_audio` at lines 479-530;
- the dub-engine selectors and Burmese-specific voice picks at
  lines 579-635.

The Matrix Script Phase B variation panel mounts at lines 257-440
(under `{% if ops_workbench_panel.panel_kind == "matrix_script" %}`),
so it appears **in addition to** all the Hot Follow controls.

Live observation on `task_id=415ea379ebc6` confirms this exactly: the
`pipeline_config` JSON `{"subtitles_mode": "whisper+gemini",
"dub_mode": "auto-fallback"}` is persisted on the row regardless of
kind (visible in the task JSON), and the template surfaces it
verbatim.

### Authority mismatch

- [`workbench_panel_dispatch_contract_v1`](../contracts/workbench_panel_dispatch_contract_v1.md)
  governs `(ref_id → panel_kind)` mounting only. It is **silent** on
  what other controls the surrounding shell may render. The §8.B
  execution log §3.3 correctly noted this as a contract scope
  observation, not a defect — and it is correct that the contract
  does not require `(panel_kind → template)` per-line files. But the
  contract also does not say "the shared shell is line-neutral", and
  the implementation drifted into the opposite — "the shared shell
  is Hot Follow-shaped".
- [`workbench_variation_surface_contract_v1`](../contracts/matrix_script/workbench_variation_surface_contract_v1.md)
  defines the Matrix Script Phase B panel contents but does not
  define the workbench page envelope.
- The Plan A trial brief
  [`OPERATIONS_TRIAL_READINESS_PLAN_v1.md`](../product/OPERATIONS_TRIAL_READINESS_PLAN_v1.md)
  §3.1 promises Matrix Script "End-to-end **except Delivery Center
  binding**" — which an operator reasonably reads as "no Hot Follow
  flow controls". §8.D extended this in §0.1 / §3.2 / §3.3 / §5.2 /
  §6.2 / §7.1 with explicit "fresh corrected Matrix Script sample"
  criteria, but did not add a "no Hot Follow shell controls" bullet
  because §8.B's dispatch-correct conclusion implied it.

### Required correction type

This is a **shell defect with contract-level implications**:

- **Shell defect:** `task_workbench.html` must learn to suppress Hot
  Follow stage cards / pipeline labels / dub engine controls /
  Burmese-specific deliverable rows when `kind != "hot_follow"`.
  Equivalently: those sections must be wrapped in `{% if task.kind
  == "hot_follow" %}` (or a more explicit feature predicate, e.g.
  `{% if line_capabilities.has_dub_flow %}`).
- **Contract-level implication:** the implicit assumption "shared
  shell is line-neutral, line-specific controls only render inside
  the panel" should be **made explicit** somewhere — either as an
  addendum to `workbench_panel_dispatch_contract_v1` ("the shared
  shell is line-neutral; line-specific stage controls render only
  inside the panel kind") or a new shell-envelope contract. Without
  the contract addendum, the next line onboarding (Digital Anchor
  at Plan E) would face the same ambiguity.

The simplest in-wave correction is the shell-defect fix; the contract
addendum can be additive in the same PR.

### Whether implementation can be narrow

**Yes, with caveats.** The narrow implementation:

1. wrap each Hot Follow-only section of `task_workbench.html` in
   `{% if task.kind == "hot_follow" %}` (or introduce a
   `template_kind` / `shell_capabilities` ctx variable for cleaner
   gating);
2. ensure the matrix_script branch (lines 257-440) renders
   **without** the Hot Follow stage cards, deliverable strip,
   pipeline summary, and subtitle-track meta row;
3. add a regression test asserting that for `kind=matrix_script`
   the rendered HTML does **not** contain any of: `whisper+gemini`,
   `auto-fallback`, `字幕轨道`, `mm_audio`, `mm.srt`,
   `缅语配音`, `缅文字幕`, `步骤1-解析与下载`, `步骤2-字幕`,
   `步骤3-缅语配音`, `步骤4-打包`;
4. land an additive contract addendum on
   `workbench_panel_dispatch_contract_v1` declaring shell-shell
   neutrality.

Caveats:

- the existing `task_workbench.html` is shared with `default` (i.e.
  any unregistered kind also renders it). The gating predicate must
  be either `kind == "hot_follow"` (whitelist Hot Follow-only) or a
  capability flag (`shell_capabilities.has_dub_flow`, etc.). The
  whitelist form is simpler and lower-risk for this wave.
- the `default` registry entry currently maps to
  `task_workbench.html`. After §8.E lands, the `default` template
  will be a stripped envelope (header + line-panel slot + delivery
  + publish). Hot Follow continues to use the `hot_follow` registry
  entry → `hot_follow_workbench.html`, which is unaffected.

Risk: the existing `task_workbench.html` may be used by other lines
in unexpected ways (`apollo_avatar` has its own template, but other
test fixtures may rely on the current shape). A regression sweep
across `tests/contracts/operator_visible_surfaces/` and
`gateway/app/services/tests/test_task_router_presenters.py` is
prerequisite work.

## 6. §8.F Review — Opaque Ref Discipline vs Operator Usability

### Observed defect

The §8.A guard at
[`create_entry.py:57-66`](../../gateway/app/services/matrix_script/create_entry.py:57)
declares:

```
SOURCE_SCRIPT_REF_ACCEPTED_SCHEMES = (
    "content", "task", "asset", "ref",
    "s3", "gs", "https", "http",
)
```

The contract addendum at `task_entry_contract_v1.md` §"Source script
ref shape (addendum, 2026-05-02)" pins this set as exhaustive at v1.
The `https` / `http` entries were included to allow operators to use
URLs they already had on hand.

The live observation: an operator submitted
`https://news.qq.com/rain/a/20260502A05LYM00` (a publisher article
URL) and the guard accepted it. The contract intent is "opaque ref
handle" — i.e. a value that is dereferenceable inside this product's
content / asset / task systems, not a value that points outside the
boundary. A `news.qq.com` URL is a **content URL** in the
operator-readable sense, but it is **not** an opaque handle in the
contract-intent sense; the product cannot dereference it to authored
script content.

### Contract intent

`task_entry_contract_v1` (read in conjunction with the
`slot_pack_contract_v1` §"Forbidden" no-body-embedding rule and the
Phase A "line truth vs operator hint" classification) treats
`source_script_ref` as a **line-truth** field that crosses to packet
truth as `packet.config.entry.source_script_ref` and is
deterministically mapped into `slots[*].body_ref` via §8.C's planner.
A `body_ref` of `content://matrix-script/{task_id}/slot/{slot_id}` is
opaque-by-construction (the product owns the dereferencing path); a
publisher article URL is **not** opaque-by-construction (the product
does not own dereferencing of arbitrary external URLs, and any
dereferencing would amount to web scraping / external fetch — out of
scope for this wave).

The contract intent is therefore: opaque-ref schemes only.
`content://` / `task://` / `asset://` / `ref://` are
opaque-by-construction inside the product. `s3://` / `gs://` are
opaque by convention (the product owns the bucket / object). `https`
/ `http` are **not** opaque in this sense; they were a pragmatic
allowance during §8.A but are inconsistent with the contract intent.

### Operator usability gap

The repo has **no minting / lookup path** for opaque refs:

- there is no asset-library service (Plan C C1, contract-frozen,
  not implemented; gated to Plan E);
- there is no `content://` mint endpoint;
- there is no documented "how do I obtain a `content://` handle for
  my script source" runbook in `docs/runbooks/` or
  `docs/product/`;
- the §8.A contract addendum lists the accepted schemes but does
  not tell operators where the handles come from;
- the §8.D operator brief §6.2 / §7.1 sample 3 example shows
  `content://matrix-script/source/<your-id>` but does not explain
  what `<your-id>` is or how to assign it.

Consequence: operators have no path forward except `https://`. The
guard is structurally permissive enough to let them use it, so they
do.

### Decision options and tradeoffs

Three options, in increasing order of in-wave scope:

**Option F1 — Tighten the scheme set, accept the operator pain.**
Drop `https` / `http` (and possibly `s3` / `gs`) from
`SOURCE_SCRIPT_REF_ACCEPTED_SCHEMES`. Update the §8.A addendum to
match. Add a §8.D-style brief update telling operators that until
Plan C C1 lands, the only acceptable opaque-ref form is a manually
crafted `content://matrix-script/source/<token>` (where `<token>` is
operator-chosen and uniquely identifies their script source within
the product, treated as an opaque label by the product itself).

- Pros: contract intent is enforced; no new service work in this
  wave; aligns with the §8.C `body_ref` template
  (`content://matrix-script/{task_id}/slot/{slot_id}`) which is
  already opaque-by-construction with no external dereference.
- Cons: operator usability suffers — operators must invent
  `<token>` values themselves; if two operators pick the same
  token, they collide silently (the guard does not check
  uniqueness); no product-side dereference exists either, so the
  ref is genuinely opaque (the body lives wherever the operator
  put it, and the product never reads it back).
- Best for: Plan A trial only, where the contract enforcement
  matters and the lack of a dereference path is acceptable because
  Plan B B4 / Plan C C1 / Plan E are the proper resolution paths.

**Option F2 — Keep the scheme set, add an in-product minting flow.**
Implement a minimal `POST /assets/mint?kind=script_source` endpoint
that takes operator-supplied content (or a URL) and returns a
`content://` handle. Keep `https` / `http` in the accepted set as
a fallback during the transition.

- Pros: operator usability is good; the product owns the
  dereferencing path.
- Cons: this is a new operator-facing service — squarely in Plan C
  C1 scope, which is gated to Plan E. Implementing it during the
  Plan A trial correction wave would expand wave scope beyond the
  blocker-review charter and arguably violate the "do not enter
  Capability Expansion" red line.
- Best for: Plan E, not now.

**Option F3 — Accept the slippage; document it.**
Keep `https` / `http` in the accepted set. Update the §8.A
addendum and the §8.D brief to explicitly state that `https` /
`http` URLs are accepted as a transitional convenience, that they
are *not* opaque in the contract-intent sense, and that operators
should expect the artifact-lookup path (Plan B B4) to behave
differently for URL-shaped refs vs handle-shaped refs once it
lands.

- Pros: zero code change; preserves operator-usability today.
- Cons: the §8.A contract addendum becomes self-contradictory
  ("opaque ref" + "we accept publisher URLs"). The Plan B B4
  artifact-lookup contract has no defined behavior for URL-shaped
  refs, so this option leaks the decision into the next wave
  without resolving it.
- Best for: nobody — this is the do-nothing option that lets the
  observed defect become permanent.

### Recommended decision

**Option F1 (tighten + brief update), with §8.E / §8.G landing
first** so the operator has a usable workbench to retest against once
the scheme set narrows. Option F2 is the right Plan E posture but
must not be back-fitted into Plan A; Option F3 is unacceptable.

§8.F is therefore **primarily a contract-tightening problem** (the
accepted scheme set was too permissive at §8.A) **AND a product
usability problem** (no minting path exists, so operators have no
ergonomic alternative). The contract tightening is in-wave; the
product minting is Plan E. Bridging the two requires the brief
update.

## 7. §8.G Review — Phase B Panel Render Correctness

### Observed defect

[`gateway/app/templates/task_workbench.html:295-302`](../../gateway/app/templates/task_workbench.html:295)
contains:

```jinja
{% if axis.values is mapping %}
  min={{ axis.values.min }} · max={{ axis.values.max }} · step={{ axis.values.step }}
{% elif axis.values is iterable and axis.values is not string %}
  {{ axis.values | join(" · ") }}
{% else %}
  {{ axis.values }}
{% endif %}
```

Live render on `task_id=415ea379ebc6` shows `<built-in method values
of dict object at 0x7c7ce4739240>` for `tone`, the same with a
different `0x...` for `audience`, and similar for `length`. All
three rows fall through to the `else` branch.

### Root cause class

Jinja2's attribute-vs-item resolution: when the template writes
`axis.values`, Jinja first calls `getattr(axis, "values")`. Because
`axis` is a Python `dict`, `getattr(axis, "values")` returns the
dict's bound `values()` method — a callable, not the value of the
`"values"` key. Jinja's `is mapping` test (which essentially asks
"does this look like a dict?") returns False for a bound method;
`is iterable and is not string` returns False as well (a bound
method is not iterable until called). The `else` branch wins, and
`{{ axis.values }}` renders `repr(bound_method)`.

This is a well-known Jinja gotcha for dict keys that collide with
dict method names: `keys`, `values`, `items`, `get`, `update`, etc.
The fix is to use **item access** instead of attribute access:
`axis["values"]` (or `axis.get("values")`).

The §8.C planner's authored output is correct — the Python dict
literally has `{"axis_id": "tone", "kind": "categorical", "values":
["formal", "casual", "playful"], "is_required": True}`. The
projector and the wiring carry it through unchanged. Only the
template-level access pattern is wrong.

### Narrow-fix suitability

**Highly suitable.** The fix:

1. change three occurrences in
   [`task_workbench.html:295-302`](../../gateway/app/templates/task_workbench.html:295):
   `axis.values is mapping` → `axis["values"] is mapping`,
   `axis.values.min` / `.max` / `.step` → `axis["values"]["min"]`
   / `["max"]` / `["step"]`, `axis.values is iterable and axis.values
   is not string` → `axis["values"] is iterable and axis["values"]
   is not string`, `axis.values | join(" · ")` → `axis["values"] |
   join(" · ")`, and the final `{{ axis.values }}` →
   `{{ axis["values"] }}`. Optionally store to a local with
   `{% set values = axis["values"] %}` and use `values` thereafter.
2. add a regression test that asserts the rendered HTML for
   `task_id=...` (a fresh §8.C sample) contains `formal`, `casual`,
   `playful` (tone values) and `b2b`, `b2c`, `internal` (audience
   values) **in the axes table specifically** (e.g. via a CSS
   selector or via asserting they appear inside a row with the
   matching `axis_id` cell). The §8.C test
   `test_get_workbench_renders_real_axes_cells_slots` only asserts
   presence somewhere in the body, which is why the bug escaped.
3. additionally: audit the rest of `task_workbench.html` for the
   same pattern (`{{ thing.values }}`, `{{ thing.keys }}`,
   `{{ thing.items }}`, `{{ thing.get }}`) — there may be other
   instances waiting to surface.

§8.G is independently fixable. It does not depend on §8.E (shell
suppression) or §8.F (scheme tightening) — the axes table is inside
the `{% if ops_workbench_panel.panel_kind == "matrix_script" %}`
block, so the fix is line-conditional regardless of whether the
surrounding shell is suppressed. After §8.E lands, the same fix
remains correct (the matrix_script branch survives intact).

## 8. Recommended Ordering

The right next sequence is:

1. **§8.G first — narrow render bug.** Lowest scope, highest
   immediate operator-readability gain, no contract change, no
   shell change. A one-template-file fix plus a tightened
   regression test. Lands and unblocks the operator's ability to
   *read* the Phase B panel; this is currently the most operator-
   visible "looks broken" defect.
2. **§8.E second — shell suppression.** Medium scope. One template
   file (`task_workbench.html`) plus a `default` template envelope
   audit plus a contract addendum on
   `workbench_panel_dispatch_contract_v1`. Lands the shell hygiene
   so a fresh Matrix Script task no longer carries Hot Follow's
   parse / subtitle / dub / pack / Burmese controls. After §8.E
   the workbench page is operator-trustable as "this is the Matrix
   Script workbench".
3. **§8.F third — contract / usability decision.** Highest authority
   weight: requires explicit Chief-Architect decision among Options
   F1 / F2 / F3 (recommendation: F1). Touches the §8.A contract
   addendum, the §8.A guard accepted-scheme set, and the §8.D
   operator brief. Should land after §8.E so that a freshly
   created task with a tightened ref scheme is testable against a
   clean shell.

After §8.E / §8.F / §8.G land, a §8.H "operator brief re-correction"
mirroring §8.D's documentation-only posture should refresh the §0.1
sample-validity rule, the §3.2 / §6.2 ref-shape enumeration, and the
§7.1 / §8 risk-list rows to reflect the new shell + scheme + render
gates. §8.H is the natural successor to this review.

### Items blocked on authority

- §8.F requires explicit decision among Options F1 / F2 / F3. This
  review **recommends** F1 but does not bind. Implementation should
  not start until the recommendation is accepted (or replaced).

### Items implementable as narrow fixes

- §8.G: yes, narrow template fix + regression-test tightening.
- §8.E: mostly narrow (template gating + contract addendum); the
  scope-controlled form is "whitelist Hot Follow-only sections"
  rather than the larger "introduce capability flags" refactor.
- §8.F (Option F1): narrow code (drop two strings from a tuple),
  narrow contract addendum (one-line update to the §8.A addendum),
  narrow brief update (refresh the §3.2 / §6.2 ref-shape enumeration).

### Items that must NOT be expanded into broader work

- per-line workbench template files for matrix_script /
  digital_anchor (out of scope; per `workbench_panel_dispatch_contract_v1`
  the per-panel mount inside a shared shell is the correct design);
- new asset-library / content-mint service (Plan C C1, gated to
  Plan E);
- workbench redesign;
- Hot Follow business behavior reopening;
- Runtime Assembly / Capability Expansion entry;
- second production line onboarding.

## 9. Gate Recommendation

- **§8.E (workbench shell line-conditional rendering): READY** —
  scope is clear, narrow implementation path is identified, no
  blocking authority decision required. Land second after §8.G.
- **§8.F (opaque-ref discipline): BLOCKED on authority decision
  among Options F1 / F2 / F3.** Recommendation: F1 (tighten
  scheme set; defer minting to Plan E; brief operators on the
  transitional `<token>` convention). Once accepted, F1 is
  READY and narrow. Land third after §8.E.
- **§8.G (Phase B panel render correctness): READY** — narrow
  template fix; one file, three lines of edit, plus a regression
  test. Land first.

- **Immediate implementation allowed: NO** — this review is
  authority-only. After §8.F's authority decision is recorded
  (either by accepting the F1 recommendation or by counter-decision),
  §8.G then §8.E then §8.F may proceed as separate gated
  correction items, each with its own execution log and tests, in
  the style of §8.A / §8.B / §8.C.

### Required answers to the four explicit judgments

- **Did §8.B overstate success? YES.** §8.B correctly verified
  dispatch + mount but implicitly claimed "the operator-visible
  result is the Matrix Script workbench". The actual result is
  "the shared shell (Hot Follow-shaped) plus the Matrix Script
  variation panel". The §8.E correction is required to make §8.B's
  implied claim true.
- **Is the current mixed workbench result sufficient to block
  Matrix Script ops trial? YES.** An operator looking at the
  current page cannot distinguish "Matrix Script line in trial"
  from "Hot Follow line that happens to also have a Matrix Script
  panel attached". The shell contamination defeats the trial's
  purpose (validating the operator-visible Matrix Script
  experience).
- **Is §8.F primarily a contract-tightening problem, a product
  usability problem, or both? BOTH** — and in this order:
  contract-tightening is the in-wave correction (Option F1);
  product-usability (Option F2 / Plan C C1) is Plan E. The bridge
  between them is a brief update.
- **Can §8.G be handled as an isolated narrow fix? YES** —
  one-template-file change; not coupled to §8.E or §8.F; landable
  first.
- **What is the correct order? §8.G → §8.E → §8.F → (§8.H docs
  re-correction).** §8.G first because it is immediate
  operator-readability; §8.E second because it makes the workbench
  trustable as a Matrix Script workbench; §8.F third because the
  scheme tightening should land against a clean shell so the next
  trial sample exercises both gates together. §8.H is the §8.D
  successor that re-aligns the operator brief once §8.E / §8.F /
  §8.G are accepted.

### Hard red lines (re-stated)

While correcting:

- do not implement fixes in this review step;
- do not reopen Hot Follow business behavior — Hot Follow's
  workbench is the `hot_follow_workbench.html` template, which is
  unaffected by §8.E (which gates the **shared/default** template);
- do not enter Platform Runtime Assembly;
- do not enter Capability Expansion (specifically: no asset-library
  service in this wave; no content-mint endpoint);
- do not introduce per-line workbench template files for Matrix
  Script — the per-panel mount inside a shared shell is the
  correct design per `workbench_panel_dispatch_contract_v1`;
- do not silently change `task_entry_contract_v1` semantics — the
  §8.A addendum scheme set is the contract truth; any change goes
  via an additive same-PR addendum with the explicit reasoning
  recorded;
- do not patch the workbench UI to fake suppression by CSS —
  suppression must be in the template render path so tests can
  assert it;
- do not weaken the §8.A guard (the body-text rejection rules
  stay; only the accepted-scheme set changes under Option F1);
- do not promote Delivery Center beyond inspect-only for Matrix
  Script in this wave;
- do not add state-shape fields (`delivery_ready`, `publishable`,
  `final_ready`, etc.) to any surface;
- do not onboard a second production line until §8.E / §8.F / §8.G
  / §8.H are gated through.

End of v1.
