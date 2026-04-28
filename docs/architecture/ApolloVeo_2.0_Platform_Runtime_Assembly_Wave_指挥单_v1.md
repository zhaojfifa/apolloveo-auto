ApolloVeo 2.0 · Platform Runtime Assembly Wave 指挥单 v1
文档性质：执行指挥单 / Platform Assembly Brief 适用阶段：W2.1 First Provider Absorption 已通过；Matrix Script First Production Line 已签收；Digital Anchor Second Production Line 已签收 用途：统一 ApolloVeo 2.0 从“多条已闭环产线”推进到“平台 runtime 总装配”的下一阶段范围、角色边界、验收口径与回写要求 当前结论：ApolloVeo 已完成“两条正式产线 + 第一枪 provider 吸收”的闭环证明。下一阶段不应继续盲目扩线，而应进入平台底座的 runtime assembly。

0. 使用声明（重要）
本文件是阶段指挥基线，不替代动态 authority、state、evidence 的读取与回写。
后续执行仍必须持续读取并回写：
* docs/baseline/PRODUCT_BASELINE.md
* docs/architecture/apolloveo_2_0_master_plan_v1_1.md
* docs/architecture/apolloveo_2_0_top_level_business_flow_v1.md
* docs/execution/apolloveo_2_0_evidence_index_v1.md
* 当前 active execution log
* 当前 review / evidence / signoff 文档
* 当前 state / gate / line / adapter authority 文档
本文件定义阶段顺序、边界与验收口径，但不替代真实状态文件。

1. 当前阶段定义
当前阶段正式定义为：
ApolloVeo 2.0 Platform Runtime Assembly Wave
其含义是：
1. 第一条 Provider 吸收已验证成立；
2. Matrix Script / Digital Anchor 两条正式生产线已闭环；
3. 下一阶段的重点不是继续扩更多线，而是让 2.0 的平台底座真正 runtime 化；
4. 当前目标是建立从 contract → service → router → projection → feedback 的平台装配链；
5. 当前不追求多租户、复杂运营后台、第三第四条产线并行铺开。

2. 当前判断
2.1 已完成的前置事实
当前主线应已具备以下基础（实际执行前仍需重新读取 authority 确认）：
* W1 donor absorption 已闭环
* W2 Admission Preparation 已闭环
* B1–B4 AdapterBase base-only 已闭环
* 第一条 W2.1 Provider 吸收已闭环
* Matrix Script 第一条正式生产线已闭环
* Digital Anchor 第二条正式生产线已闭环
2.2 当前统一判断
* 允许做：平台级 runtime assembly
* 不允许做：第三条新产线直接实现
* 不允许做：W2.2 / W2.3 大范围扩张
* 不允许做：Hot Follow 业务扩写
* 不允许做：重前端平台化或模型控制台化

3. 本阶段总目标
把 ApolloVeo 从“已有两条闭环产线的基线仓库”推进到“具备平台 runtime 装配能力的 2.0 工厂底座”。
完成后，应达到以下状态：
1. 共享逻辑不再散落在 router / god-file 中；
2. line contract 能真正进入 runtime 装配链；
3. ready gate 从硬编码判断推进到声明式规则；
4. Skills bundle / Worker binding / Deliverable binding 有最小 runtime 骨架；
5. 两条已闭环产线能被视为统一底座上的标准 line，不只是各自独立闭环实现。

4. 总原则
4.1 先装底座，不扩更多线
本阶段重点是 runtime assembly，不是新线数量。
4.2 不改已闭环线的业务真相
Matrix Script / Digital Anchor 已闭环的 packet truth、projection truth、closure truth 不得被平台化反向改坏。
4.3 先收口 shared logic，再谈 skills/openclaw
先把共享逻辑、状态、ready gate、contract runtime 链打通，再引入更高层 skills/openclaw。
4.4 平台底座必须 additive
任何平台化改动都必须是 additive，不能回写成新的业务真相替代物。
4.5 每一步可独立 review / merge / rollback
本阶段仍必须波次化。

5. 角色任务分配
A. 工程负责人
当前使命：把 2.0 平台底座从“文档定义 + 局部实现”推进到“最小 runtime 装配成立”。
当前只允许做：
* shared logic / port merge / service extraction
* declarative ready gate
* line runtime assembly skeleton
* minimal skills runtime skeleton
* minimal worker / adapter binding cleanup
* evidence / execution write-back
当前禁止做：
* 直接扩第三条新产线
* Hot Follow 新功能
* W2.2 / W2.3 大规模 provider 扩张
* React/Vite 全量前端平台重构
* 新的 packet/state truth 发明
B. 架构师
当前使命：确认平台 runtime 装配是否真正建立，而不是继续停留在“registry 声明层”。
必须确认：
1. contract → service → router 是否开始形成绑定链
2. ready gate 是否转入声明式规则
3. shared logic 是否从 god-file 中下沉
4. Skills / Worker / Deliverable 的 runtime 位置是否清楚
5. 两条已闭环线是否未被破坏
C. Reviewer / Merge Owner
当前使命：关闭平台装配波次，不扩大范围。
必须确认：
1. 是否以平台 runtime 装配为主，而不是偷偷扩业务
2. 是否没有破坏 Matrix Script / Digital Anchor 既有闭环
3. 是否没有混入 Hot Follow 功能扩写
4. 是否 evidence chain 完整
5. main 继续保持单一 authority baseline

6. 阶段拆分建议
Phase A — Shared Logic Port Merge
目标：消除大文件之间的共享逻辑互相导入，把可复用 helper / service 下沉到稳定服务层。
最小范围：
* 共享 helper 分类下沉
* router 间循环依赖削减
* constants / artifact / task view / voice / subtitle / compose helpers 归位
Phase B — Compose / Large Service Extraction
目标：把超长 compose / workbench / projection 逻辑从 router/god-file 中抽到独立服务。
最小范围：
* composition service
* result object / plan object
* subprocess timeout / cleanup discipline
* 单元测试可覆盖
Phase C — Declarative Ready Gate
目标：把 ready gate 从硬编码判断推进到按 line 加载的声明式规则。
最小范围：
* gate rule model
* per-line gate config
* workbench/publish 消费 gate 输出
* 不改已闭环线的 truth definition
Phase D — Runtime Assembly Skeleton
目标：建立最小 runtime 装配骨架，让 line contract、skills bundle、worker profile、deliverable profile 开始进入可装配状态。
最小范围：
* production line runtime assembly skeleton
* skills bundle loader skeleton
* worker binding skeleton
* deliverable binding skeleton
Phase E — OpenClaw / External Control Stub（可选，后置）
目标：仅建立最小 control mesh stub，不吞业务真相。

7. 当前禁止事项
当前阶段明确禁止：
* 直接并行推进第三条正式产线
* W2.2 / W2.3 大范围 provider 实现
* Hot Follow 业务功能扩写
* 复杂 provider/model 控制台
* 重前端平台化
* 改写 Matrix Script / Digital Anchor 已闭环 truth
* 引入新的全局状态真相

8. 交付与回写要求
每个阶段完成后，必须同步回写：
* docs/execution/apolloveo_2_0_evidence_index_v1.md
* 当前 active execution log
* platform assembly 对应 evidence / review 文档
* 必要的 architecture / contract clarification 文档
至少写清楚：
1. 做了什么
2. 明确没做什么
3. 当前 blocker 还剩什么
4. 下一棒交给谁

9. 下一阶段关系
当前阶段
* ApolloVeo 2.0 Platform Runtime Assembly Wave
后续阶段（仅在本阶段绿后允许）
* W2.2 Subtitles / Dub Provider
* W2.3 Avatar / VideoGen / Storage Provider
* 第三条正式生产线 commissioning
* Durable persistence / runtime API additive wave
* OpenClaw control mesh formalization

10. 总控口令
Current execution focus is ApolloVeo 2.0 Platform Runtime Assembly. Do not expand into a third production line yet. Do not mutate the closed truth of Matrix Script or Digital Anchor. First merge shared logic and reduce god-file ownership. Then extract compose/runtime services. Then land declarative ready gate. Then assemble minimal line/skills/worker runtime skeleton. Architect signs the platform assembly boundary. Reviewer closes the wave independently.

11. 一句话总结
ApolloVeo 现在已经证明了“provider absorption + two production lines closure”能够成立；下一阶段不应继续扩线，而应把 2.0 的平台 runtime 总装配真正落下来。

