ApolloVeo 2.0 · Operator-Visible Surface Validation Wave 指挥单 v1
文档性质：执行指挥单 / Operator Surface Brief 适用阶段：W2.1 First Provider Absorption 已通过；Matrix Script First Production Line 已签收；Digital Anchor Second Production Line 已签收；平台 runtime 总装配尚未启动 用途：在进入 Platform Runtime Assembly Wave 之前，先完成一轮运营可见 surface 的设计/实现收口与试用验证，形成真实运营反馈输入 当前结论：两条正式产线已具备 contract/projection/write-back 闭环，适合先做 operator-visible surface 验证，再进入平台底座总装配。

0. 使用声明（重要）
本文件是阶段指挥基线，不替代动态 authority、state、evidence 的读取与回写。
后续执行仍必须持续读取并回写：
* docs/baseline/PRODUCT_BASELINE.md
* docs/architecture/apolloveo_2_0_master_plan_v1_1.md
* docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md
* docs/execution/apolloveo_2_0_evidence_index_v1.md
* 当前 active execution log
* 当前 review / evidence / signoff 文档
* 当前 line packet / surface contract / delivery contract / feedback closure contract

1. 当前阶段定义
当前阶段正式定义为：
ApolloVeo 2.0 Operator-Visible Surface Validation Wave
其含义是：
1. Matrix Script 与 Digital Anchor 两条正式生产线已经闭环；
2. 当前优先目标不是继续扩 provider 或第三条线；
3. 当前优先目标是把运营真正能看到、能操作、能给反馈的 surface 收口出来；
4. 这轮结果将作为后续 Platform Runtime Assembly Wave 的真实输入；
5. 本阶段不做大平台，不做模型控制台，不做后台工具化。

2. 本阶段总目标
把 ApolloVeo 2.0 当前已闭环的产线能力，推进到运营可见、可试用、可反馈的 surface 形态。
完成后，应达到以下状态：
1. 任务区可看懂三条线的任务进入与状态区别；
2. 工作台可支撑 Matrix Script / Digital Anchor 的结构化操作与校对；
3. 交付中心可正确展示 final / required deliverables / non-blocking items / publish feedback；
4. UI 状态显示可追溯到 contract truth / artifact facts / current attempt；
5. 运营试用反馈可反向输入平台总装配优先级。

3. 总原则
3.1 先做运营可见，不做平台后台
本阶段目标是 operator-visible surfaces，不是工具后台。
3.2 只消费既有 truth
所有 UI/surface 必须消费：
* packet truth
* workbench projection truth
* delivery projection truth
* feedback closure truth
* derived gates
不得发明新的业务真相。
3.3 先可试用，再高保真
本阶段追求：
* 结构清楚
* 状态可信
* 交付可读
* 操作路径明确
不追求视觉风格完稿。
3.4 反馈用于指导平台总装配
这轮的价值不是“做漂亮页面”，而是让运营试用后，暴露平台装配缺口。

4. 角色任务分配
A. 产品经理
当前使命：
* 收口三条线的运营可见流程
* 明确任务区 / 工作台 / 交付中心的字段口径
* 明确哪些区块是本轮必须可见，哪些仍 deferred
B. 设计师
当前使命：
* 把已有五面 IA 与三大主 surface 低保真，推进到运营可测试结构稿
* 明确每个区块的 contract mapping notes
* 不发明状态字段，不直连供应商差异
C. 工程负责人
当前使命：
* 只做运营可见 surface 的最小接线
* 保证 UI 消费正式 projector / delivery binding / closure truth
* 不改 packet truth，不重写 line closure
D. 架构师
当前使命：
* 确认 UI 没有第二真相源
* 确认 operator-visible surface 仍按四层状态模型组织
* 识别需要进入 Platform Runtime Assembly 的真实 blocker
E. Reviewer / Merge Owner
当前使命：
* 关闭本轮 surface validation，不扩大范围
* 阻止任何偷偷混入 provider expansion / Hot Follow / 第三条线

5. 阶段拆分建议
Phase A — Operator Surface Scope Freeze
目标：
* 冻结本轮运营可见范围
* 明确任务区 / 工作台 / 交付中心 / line-specific panel / publish feedback visibility
Phase B — Testable Surface Landing
目标：
* 让 Matrix Script / Digital Anchor / reference Hot Follow 的关键 surface 进入可测试状态
* 形成 operator-visible 结构稿 + 最小数据接线
Phase C — Trial Feedback Consolidation
目标：
* 运营试跑
* 汇总结构问题 / 状态解释问题 / 交付判断问题
* 输出 platform runtime assembly 的输入清单

6. 当前只允许做
* task area 的 operator-visible 收口
* workbench 的 operator-visible 收口
* delivery center 的 operator-visible 收口
* Matrix Script variation panel 的正式可见挂载
* Digital Anchor role/speaker panel 的正式可见挂载
* publish feedback 的可见性与说明
* evidence / execution / review write-back

7. 当前禁止事项
当前阶段明确禁止：
* W2.2 / W2.3 扩张
* 第三条正式产线实现
* provider/model/vendor 控制台
* Hot Follow 新功能
* Matrix Script / Digital Anchor packet truth 改写
* React/Vite 全量平台重构
* Durable persistence / runtime API 正式化
* 工具后台平台化

8. 验收口径
本阶段 green only if：
1. 任务区 / 工作台 / 交付中心的 operator-visible shape 已落定
2. 每个区块都有 contract mapping
3. 所有状态显示都可追溯到 L2/L3 或 derived gates
4. line-specific panel 已作为正式 operator surface 挂载
5. 运营试跑反馈已形成结构化收口
6. evidence / review / execution log 回写完整

9. 与后续阶段关系
当前阶段
* ApolloVeo 2.0 Operator-Visible Surface Validation Wave
下一阶段
* ApolloVeo 2.0 Platform Runtime Assembly Wave
更后阶段
* Capability Expansion Gate Wave
* W2.2 / W2.3
* 第三条正式生产线 commissioning
* durable persistence / runtime API additive wave

10. 总控口令
Current execution focus is ApolloVeo 2.0 Operator-Visible Surface Validation. Do not expand into a third production line yet. Do not mutate the closed truth of Matrix Script or Digital Anchor. Product and Design must turn the current contract/projection baseline into operator-visible surfaces. Engineering only lands the minimum surface wiring. Architect validates truth ownership. Reviewer closes the wave independently. Only after this wave is green do we move into Platform Runtime Assembly.

11. 一句话总结
ApolloVeo 已完成两条正式产线闭环；在进入平台总装配前，先做一轮运营可见 surface 验证，让真实运营反馈来指导下一阶段的 runtime assembly 优先级。

