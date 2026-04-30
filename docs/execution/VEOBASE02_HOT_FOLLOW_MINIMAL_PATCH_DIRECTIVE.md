# VeoBase02 · Hot Follow 最小补丁指挥文件

## 1. 文件定位

本文件用于冻结 Hot Follow 在 `VeoBase02` 上的下一轮最小补丁边界。

目标不是继续大改，不是继续泛化 state policy，也不是扩 provider / compose / platform runtime。

目标只有一个：

**在不破坏当前已确认业务流的前提下，补齐 target subtitle materialization、stale pending 识别、本地 preserve 路径切回主链这三个最小缺口，保证状态不再漂。**

---

## 2. 当前冻结结论

### 2.1 不实施 broad refactor

当前阶段禁止：

- broad state policy rewrite
- route system 重做
- provider 策略扩展
- compose/post 优化扩展
- 其它产线联动改造
- UI 大改

### 2.2 先冻结 flow，再实施最小补丁

在 flow note 冻结之前：

- 不修改代码
- 不新增 patch
- 不调整 ready gate 大逻辑
- 不继续修补 helper 分支语义

### 2.3 冻结后的唯一推进分支

- 基座分支：`VeoBase02`
- 仅允许围绕本文件定义的最小补丁推进

---

## 3. Hot Follow 正式业务流冻结

### 3.1 URL 标准主链

正式主链定义为：

`raw -> origin.srt -> target subtitle materialization -> dub -> compose`

规则：

1. `origin.srt` 已存在，不等于 `vi.srt` 已成立。
2. `vi.srt` 必须通过正式 target subtitle materialization action 形成。
3. 没有 authoritative/current `vi.srt`，dub 不开始。
4. 没有 current audio，compose 不开始。
5. helper 仅为辅助输入或遥测，不是 subtitle truth owner。

### 3.2 本地上传 preserve 测试路径

本地运营测试允许存在合法旁路：

`raw -> preserve_source_route -> compose`

规则：

1. 允许 skip subtitles。
2. 允许 skip dub。
3. 允许保留原音直接合成。
4. 该路径为合法运营测试路径，不视为异常。

### 3.3 本地 preserve 路径切回字幕/配音主链

本地测试路径如果要继续做目标语言字幕 / 配音，必须通过正式 operator action 切回主链：

`preserve_source_route --(local_preserve_to_subtitle_dub_flow)--> raw -> origin.srt -> target subtitle materialization -> dub -> compose`

规则：

1. 该动作只表达 operator intent。
2. 该动作本身不写 `vi.srt`。
3. 该动作只负责启用 / 排队 target subtitle materialization action。
4. helper 不得承担 route switching owner 角色。

---

## 4. 最小补丁边界

### 4.1 补丁一：Formal target subtitle materialization action

新增显式 stage action，例如：

`materialize_target_subtitle_from_origin`

输入：

- current `origin.srt`
- target language
- task id

输出：

- authoritative `vi.srt`

硬规则：

1. 只能通过现有 Subtitle Stage owner 的 authoritative write path 写入。
2. 不能走 helper telemetry write path。
3. 失败结果必须显式化，例如：
   - no translated target produced
   - invalid target
   - provider error
   - stale source
4. helper success 只能作为该 action 的输入来源之一，不能直接形成 subtitle truth。

### 4.2 补丁二：Stale-pending detector

只增加只读检测器，不进行 broad state-policy rewrite。

目的：

区分以下两类状态：

1. **active translation running**
2. **stale pending without progress**

判定建议：

- active running：近期 `subtitles_status=running`，或存在有效 request marker / timestamp
- stale pending：`target_subtitle_translation_incomplete` / `helper_output_pending` 持续存在，但没有近期执行标记

硬规则：

1. 该 detector 只产出诊断 / 升级元数据。
2. 不得写 subtitle truth。
3. 不得改写 compose / dub readiness truth。

### 4.3 补丁三：Formal local preserve to subtitle/dub action

新增显式 operator action：

`local_preserve_to_subtitle_dub_flow`

作用：

- 标记 operator 明确离开 `preserve_source_route`
- 正式进入：
  `raw -> origin.srt -> target subtitle -> dub -> compose`

硬规则：

1. 该动作本身不得 materialize subtitle truth。
2. 该动作只负责启用 / 排队 target subtitle materialization。
3. 不得由 helper 成功与否隐式决定 route switch。

### 4.4 补丁四：Helper remains auxiliary

冻结 helper 角色：

1. helper 可以提供：
   - draft translated text
   - provider telemetry
   - retryable / pending / unavailable 诊断
2. helper success 可以喂给 materialization action。
3. helper 绝不能拥有：
   - route switching
   - target subtitle closure
   - dub readiness
   - compose readiness
   - subtitle truth write ownership

---

## 5. 四层状态纪律

### L1 — Pipeline Step Execution

只记录步骤执行：

- parse
- subtitles
- dub
- compose

不得在 L1 发明 artifact truth。

### L2 — Artifact Facts

只记录真实产物事实：

- origin.srt exists
- vi.srt exists
- audio exists
- final exists

不得把 helper telemetry 当作 artifact truth。

### L3 — Current Attempt / Currentness

只记录：

- 当前 subtitle 是否 current
- 当前 dub 是否 current
- 当前 compose 是否 current
- 是否 stale / requires_redub / requires_recompose

### L4 — Projection / Ready Gate / Operator Surface

只消费 L1/L2/L3。

禁止：

- invent subtitle truth
- invent route truth
- invent dub readiness
- invent compose readiness

---

## 6. 当前已确认问题与本轮补丁对应关系

### 问题 A：`origin.srt` 已有，但 `vi.srt` 容易长期不 materialize

对应补丁：

- Formal target subtitle materialization action
- Stale-pending detector

### 问题 B：helper pending / unavailable 被保留，但没有真实 target subtitle write

对应补丁：

- Helper remains auxiliary
- Stale-pending detector

### 问题 C：本地 preserve 测试路径后，运营想继续做字幕/配音，但缺正式切回动作

对应补丁：

- Formal local preserve to subtitle/dub action

### 问题 D：状态容易飘，running / pending / blocked / skipped 混淆

对应补丁：

- 仅通过 flow freeze + stale-pending detector 收口
- 本轮不做 broad state rewrite

---

## 7. 实施顺序冻结

后续如批准实施，必须严格按以下顺序：

1. 冻结本 flow note
2. 实施 `materialize_target_subtitle_from_origin`
3. 实施 stale-pending detector
4. 实施 `local_preserve_to_subtitle_dub_flow`
5. 最后再接 helper 输入到 materialization action

禁止换顺序。

---

## 8. 验收口径

### 8.1 URL 主链验收

1. `origin.srt` 已存在后，系统能够通过正式 action 形成 authoritative `vi.srt`，而不是仅停留在 helper pending telemetry。
2. URL 等待翻译状态能区分：
   - active running
   - stale pending
3. 没有 `vi.srt` 时，dub 不开始；但 UI 不得把 active running 误呈现为死阻塞。

### 8.2 本地 preserve 路径验收

1. preserve-source 路径保持合法。
2. 保留原音合成按钮与业务 truth 一致。
3. helper 失败不应破坏当前 preserve-source compose 合法性。
4. 运营可通过正式动作切回 subtitle/dub 主链。

### 8.3 四层纪律验收

1. helper 不直接写 `vi.srt` truth。
2. L4 不得发明 subtitle / route / compose truth。
3. 所有 surface 只消费同一条 route decision 与 subtitle truth。

---

## 9. 当前执行要求

当前要求如下：

- 本文件冻结前：不实施代码改动
- 本文件冻结后：仅按本文 4 项最小补丁推进
- 未经新增批准：不得扩 scope

---

## 10. 执行口令

本文件冻结后，VeoBase02 上仅允许执行以下口径：

**Freeze flow first. Implement only the minimal patch set defined here. No broad refactor. No route-system rewrite. No helper-owned truth.**
