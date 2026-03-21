# State Schema Four-Layer Template

## 1. Purpose

本模板用于冻结 ApolloVeo 当前可复用的四层状态语言，避免把“文件存在”“步骤跑过”“页面显示 ready”混成同一层语义。

它要解决的问题是：

- authoritative object 与 runtime attempt 混淆
- fact-derived truth 与 legacy/presentation status 混淆
- current output 与 historical output 混淆
- UI / advisory 误把存在性当成 readiness

当前该模板来源于 Hot Follow 的 post-review、post-VeoSop05 真实收口经验，但作为 cross-cutting reference 提供给后续 line/state/projection 设计使用。

## 2. The Four Layers

### Layer 1 — Object / Source Facts

这一层是当前任务的事实性对象与主输入来源。

典型内容：

- authoritative subtitle / script / scene plan / source asset
- output artifacts 的 object-level metadata
- revision identity，如 content hash、updated_at、sha256
- 与 freshness 无关的 operator-editable metadata，如 `source_url`

当前 Hot Follow 语义中，`mm.srt` 是 authoritative subtitle；final/historical_final 是对象语义，不是单纯下载链接。

### Layer 2 — Attempt / Runtime Operation State

这一层是系统最近一次或当前一次尝试做了什么。

典型内容：

- `current_attempt`
- `compose.last`
- step status / step error
- started_at / finished_at / failed_at

这一层只表达执行事实，不直接表达业务正确性。

### Layer 3 — Derived / Interpreted State

这一层由 object facts 与 attempt facts 推导出业务语义。

典型内容：

- freshness / stale reason
- requires_recompose / requires_retry
- ready gate 结果
- current final 是否成立
- publish_ready / composed_ready

当前 Hot Follow 中，这一层主要由 status policy + ready gate 主链承担，而不是由 UI 或 compatibility layer 兜底。

### Layer 4 — Projection / Presentation State

这一层是对外暴露给 workbench / task detail / publish hub / advisory layer 的 presentation-safe 结果。

典型内容：

- deliverables block
- workbench cards
- operator summary
- advisory input blocks
- final url / media exposure

这一层必须消费 Layer 3，而不能自行重新定义 truth。

## 3. Allowed Ownership

四层的所有权边界冻结如下：

- artifacts / deliverables owner:
  - 负责 Layer 1 的 object facts 与物理存在性
- runtime attempts owner:
  - 负责 Layer 2 的执行状态、错误、最近尝试记录
- ready gate / status policy owner:
  - 负责 Layer 3 的 freshness、stale reason、ready gate、current-vs-historical 语义
- presentation / workbench / advisory owner:
  - 负责 Layer 4 的展示与说明
  - 不拥有 fact truth，不拥有 freshness truth，不拥有 promotion truth

特别约束：

- `historical_final` 不是 current final 的默认镜像
- `final.exists` 不是 `final.fresh`
- advisory 不是新的 truth owner

## 4. Truth-Source Discipline

truth-source discipline 冻结如下：

- artifact / source facts 优先于 legacy display state
- derived state 优先于 presentation convenience flags
- presentation / advisory 只能消费 truth，不能覆盖 truth
- legacy status 只能作为兼容信息存在，不能压过 fact-derived state

这意味着：

- UI 不得仅因 `final.exists=true` 就把 final 视为 current-ready
- advisory 不得改写 `ready_gate`、`deliverables`、`pipeline`、`artifact_facts`
- compatibility layer 不得重新成为 status truth owner

## 5. Skills-Relevant Inputs

对于 Skills MVP v0，安全可读的输入范围只限于四层中的只读、presentation-safe 子集：

- Layer 1:
  - task object snapshot 中已暴露的 authoritative/source facts
  - deliverable/artifact existence 与 url 级事实
- Layer 2:
  - `current_attempt`
  - 当前已聚合出来的最近 step status/error 摘要
- Layer 3:
  - `ready_gate`
  - freshness / stale-related derived facts
  - current-vs-historical outcome semantics
- Layer 4:
  - `operator_summary`
  - `pipeline`
  - `pipeline_legacy`
  - `deliverables`
  - `media`
  - `source_video`

当前不允许 Skills MVP v0 直接读取未冻结的 provider 内部运行细节作为主决策来源。

## 6. Non-Goals

本模板当前明确不意味着：

- 不是 full platform-wide runtime loader
- 不是 universal multi-line schema enforcement engine
- 不是 automatic source-of-truth replacement layer
- 不是 generic plugin registry
- 不是对现有所有 line 的已完成 runtime 改造声明

当前它只意味着：

- 未来的 state / deliverable / workbench / advisory 设计必须先按这四层语言对齐
- Skills MVP 只能在这个 truth discipline 之下读取，不得反向改写

