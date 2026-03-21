# Alignment Execution Review 2026-03-21

## 1. Purpose

本文围绕 `docs/reviews/ALIGNMENT_BASELINE_20260318.md` 再做一次面向执行的对齐 review。

目标不是重开平台大设计，而是回答三个当前必须冻结的问题：

- Hot Follow 四层架构当前真实收口到哪里
- `skills/state_schema_four_layer_template.md` 应如何升格为正式输入模板
- Skills MVP Entry Contract 的最小范围应冻结在哪里

在这三点冻结之前，不启动广义 Skills runtime 实现。

## 2. Executive Conclusion

当前 main 的结论可以直接冻结为：

- Hot Follow 已完成“四层状态模型”的第一条真实主链收口，但只限于 Hot Follow runtime，不代表平台级 schema 已正式化。
- `state_schema_four_layer_template` 已具备平台级设计价值，但目前仍只是 skills guidance 文档；下一步应先升格为正式 contract/template 输入，而不是直接变成 runtime loader。
- Skills MVP v0 的最小入口应继续冻结为 Hot Follow workbench 的只读 advisory hook；它不是 orchestration、不是 policy owner、不是 runtime truth source。

因此，当前正确动作是：

1. 冻结 Hot Follow 四层 state closure 的当前边界
2. 把四层 state skill 升格为正式输入模板
3. 冻结 Skills MVP Entry Contract 的最小范围
4. 在上述三点完成前，不启动 Skills runtime 大实现

## 3. Baseline vs Current Reality

`ALIGNMENT_BASELINE_20260318.md` 中的主要判断，当前需要按“已收口 / 部分收口 / 仍未开始”三类重新理解。

### 3.1 已收口

- Hot Follow compose 主链已进入 service contract 主链，不再只停留在 router 事务脚本层
- Hot Follow ready gate 已通过最小 line-aware binding 接上 `LineRegistry`
- Hot Follow current output / historical output / freshness / gate 的最关键业务语义已经落入统一状态聚合链
- Skills MVP 的第一入口边界已经有独立 execution review 与 contract 文档

### 3.2 部分收口

- Hot Follow 四层状态已经存在真实实现，但还没有被整理成平台正式输入模板
- line contract 已对 status/gate 产生真实绑定，但仍不是全面 line-aware runtime 装配
- workbench/detail/publish projection 语义已显著收口，但还没有成为多产线统一 projection schema

### 3.3 仍未开始

- broad Skills runtime
- second production line rollout
- generic multi-line profile loader
- 用 Skills 接管 compose / publish / status policy / ready gate

## 4. Hot Follow Four-Layer Closure Status

当前 main 上，Hot Follow 的四层架构已经不再只是 review 术语，而是有明确落点。

### 4.1 Layer 1 — Object State

当前已经具备的对象层事实包括：

- authoritative subtitle object（`mm.srt` 语义已冻结为主对象）
- audio object 及其 revision identity
- final / historical_final 的对象分离
- 可编辑但不参与 freshness 的 metadata（如 `source_url`）

这一层的业务原则已经被当前实现采用：

- authoritative subtitle 是主对象
- file existence 不等于 current-valid final
- current output 与 historical output 是不同对象语义

但这一层仍未形成平台正式 object schema template。

### 4.2 Layer 2 — Attempt State

当前已经形成真实 attempt 记录能力：

- `current_attempt`
- `compose.last`
- compose start / finish / error
- dub / compose 的状态与最近执行事实

这说明 Hot Follow 已经具备“执行事实层”和“对象语义层”分离的基础。

### 4.3 Layer 3 — Derived State

这是当前 Hot Follow 收口最实质的一层。

`gateway/app/services/status_policy/hot_follow_state.py` 已经承担：

- current final vs historical final 语义整理
- freshness / stale reason 推断
- `requires_recompose`
- `composed_ready`
- `ready_gate`
- projection side effects 的统一回写

这意味着：

- final freshness 不再只是 UI 解释
- stale/current/publish gate 已进入统一 derived state 主链
- “存在即正确”的旧判断方式已经不再是主逻辑

这一点与 `ALIGNMENT_BASELINE_20260318.md` 中“状态与交付物真相源仍散装”的判断相比，已经前进了一大步。

### 4.4 Layer 4 — Projection State

当前也已有真实 projection 收口，但仍是 Hot Follow 范围内的最小收口：

- `final` 只代表 current effective output
- `historical_final` 只代表 distinct previous output 或 fallback
- `deliverables.final` / `media.final_url` / workbench final exposure 已由 derived state 约束

但 projection 仍未 fully line-aware generalized：

- workbench/detail/publish 仍有 Hot Follow-specific assembly residue
- projection contract 还没有变成多产线通用 schema

## 5. What This Means for Hot Follow

对 Hot Follow 来说，现在可以冻结的现实表述是：

- 四层架构已经在 Hot Follow 上形成第一条真实闭环
- 闭环的 owner 是 status policy + ready gate + projection 这一条链，而不是 Skills
- Hot Follow 已可作为“四层 state schema”的第一条 reference implementation
- 但它还不是平台抽象完成，更不是 Skills runtime 已经 ready 的证明

换句话说，Hot Follow 现在适合“提炼模板”，不适合“立刻平台化扩张”。

## 6. Promoting `state_schema_four_layer_template` to a Formal Input Template

`skills/state_schema_four_layer_template.md` 现在的价值已经超过“skills guidance”。

它实际承担的是：

- 统一 object / attempt / derived / projection 的分层语言
- 统一 freshness / stale / gate / current vs historical output 语义
- 为新产线 contract、state review、projection review 提供输入模板

因此，推荐的升格路径不是 runtime 化，而是 contract/template 化。

### 6.1 Recommended Promotion

建议把它升格为以下角色之一：

- `docs/contracts/STATE_SCHEMA_FOUR_LAYER_TEMPLATE.md`
- 或 `docs/architecture/STATE_SCHEMA_FOUR_LAYER_TEMPLATE.md`

角色定义应冻结为：

- platform-level input template
- 新产线 / 新状态聚合 / 新 projection 设计的必读模板
- review 与 implementation 之前的 schema 对齐输入

### 6.2 What Promotion Should Mean

升格后的正式模板应回答：

- authoritative object 是什么
- attempt record 是什么
- freshness 如何定义
- derived state 谁来算
- projection 如何避免把 existence 当 readiness
- current output 与 historical output 如何区分

它应该成为：

- line contract 设计输入
- status policy 设计输入
- deliverable / hub / publish projection 设计输入

它不应该成为：

- runtime plugin loader
- generic config registry
- Skills runtime 执行器

### 6.3 Minimum Freeze Before Runtime Work

在任何 Skills runtime 实现之前，至少应先冻结：

- 四层命名基线
- snapshot / freshness 字段命名基线
- current output vs historical output 语义基线
- gate 消费 derived/projection state 的约束

如果这些还没有冻结，就去做 Skills runtime，最终只会把旧的语义模糊放大到更大范围。

## 7. Skills MVP Entry Contract — Minimum Scope

当前最稳的最小范围，仍然是：

- Hot Follow workbench / operator guidance payload 的只读 advisory hook

这个边界已有两份正式锚点：

- `docs/execution/SKILLS_MVP_ENTRY_REVIEW.md`
- `docs/contracts/SKILLS_MVP_ADVISORY_CONTRACT.md`

### 7.1 What Is In Scope

- 读取现有 truth-source blocks
- 读取 line reference
- 输出 non-blocking advisory block
- 给运营一个结构化建议，而不是控制执行

### 7.2 What Is Out of Scope

- compose runtime
- publish runtime
- ready gate engine
- status truth derivation
- artifact mutation
- deliverable truth overwrite
- hidden orchestration

### 7.3 Why This Scope Must Stay Small

当前 main 虽然已经完成 Hot Follow state closure 的关键部分，但还没完成：

- platform formal schema freeze
- multi-line line-aware runtime
- unified projection contract across lines

这时如果直接把 Skills 推进到 runtime ownership，会导致：

- truth-source ownership 再次漂移
- workbench advisory 重新侵入业务状态
- line contract / state schema / skills contract 三层边界重新混在一起

所以 Skills MVP 的最小范围必须继续维持为只读 advisory。

## 8. Freeze Decisions Before Any Broad Skills Runtime

在任何 Skills runtime 大实现之前，应先冻结以下三点。

### 8.1 Freeze A — Hot Follow Four-Layer Closure Boundary

冻结结论：

- Hot Follow 是第一条四层 state reference implementation
- 当前 owner 链为：
  - object revision
  - attempt facts
  - derived freshness/gate
  - projection exposure
- 当前范围只宣称 Hot Follow closure，不外推为完整平台 closure

### 8.2 Freeze B — Formal State Template

冻结结论：

- `state_schema_four_layer_template` 升格为正式输入模板
- 先成为 contract/template，不进入 runtime loader
- 后续任何新 line、新 deliverable 语义、新 hub/publish projection，都应先按此模板过设计 review

### 8.3 Freeze C — Skills MVP Entry Contract

冻结结论：

- Skills MVP v0 只允许 workbench advisory hook
- 只读、non-blocking、不可写真相
- 不得侵入 compose / publish / ready gate / status policy 主链

## 9. Recommended Execution Order

当前推荐执行顺序如下：

1. 把四层 state template 升格为正式 template/contract 文档
2. 在 Hot Follow runtime / execution baseline 中引用该模板，明确它是第一条 reference implementation
3. 冻结 Skills MVP advisory contract 与入口位置
4. 继续 Hot Follow cleanup（router residue / compatibility residue / projection residue）
5. 只有在上述冻结后，才讨论 Skills runtime 的更大实现

## 10. Explicit Non-Goals

本 review 明确不支持以下动作在当前阶段提前启动：

- 启动 broad Skills runtime
- 把 Skills 接进 compose service
- 把 Skills 接进 ready gate engine
- 把 Skills 接进 status policy truth derivation
- 以“平台化”为名跳过 Hot Follow 当前 cleanup
- 在未冻结 state schema 前扩第二条产线

## 11. Final Assessment

面向执行的最终判断是：

- `ALIGNMENT_BASELINE_20260318.md` 里的大方向仍然成立
- 但 main 的现实已经比当时更前进：Hot Follow 四层状态闭环已经形成最小主链
- 当前最该做的不是启动 Skills runtime 大实现，而是把这条已跑通的状态主链提炼成正式模板，并把 Skills MVP 入口冻结在只读 advisory 边界

只有这样，后续 Localization、Avatar、Swap、Scene Pack、Publish Hub 才能在同一套 state language 下扩展，而不是再次把“存在、尝试、当前、可发布”混成一层。

