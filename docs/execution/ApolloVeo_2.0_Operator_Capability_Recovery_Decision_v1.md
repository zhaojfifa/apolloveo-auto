# **ApolloVeo 2.0 · Operator Capability Recovery Decision v1**

**文档性质**：产品/架构联合裁决单 / Direction-Correction Decision
**角色定位**：由总架构师（codex）统一把握方向；由执行架构师/工程实施者（claude）按 PR 波次推进
**适用阶段**：Operator-Visible Surface Validation Wave 进行中；Platform Runtime Assembly 与 Capability Expansion 仍 blocked
**用途**：正式裁定当前“不具备真实试运营条件”，将主线从“直接执行运营试跑”纠偏为“先恢复最小运营能力，再进入试运营”
**状态**：立即生效

---

## **0\. 裁决声明**

ApolloVeo 2.0 当前**不具备真实试运营条件**。

现有仓库已经完成：

* 第一枪 W2.1 Provider 吸收证明；
* Matrix Script 第一条正式生产线闭环；
* Digital Anchor 第二条正式生产线在当前接受范围内闭环；
* 大量 packet / contract / projection / closure authority 冻结；

但这些事实并**不等于**已经具备真实运营能力。

当前 repo 的问题不是“没有文档”，而是：

* contract rich
* projection rich
* evidence rich
* operator capability poor

也就是说，系统更接近“已经证明架构/契约可行”，而不是“运营已经能工作”。

因此，本裁决正式宣布：

**暂停把“Plan A 直接运营试跑”作为当前唯一主线动作。**
Plan A 试跑不取消，但从“当前主线动作”降级为“最小运营能力恢复完成后的验证动作”。

---

## **1\. 当前判断**

### **1.1 为什么当前不能直接试运营**

以下任一项未具备，都会导致“看上去可试，实际上不可运营”：

1. **缺少最小可用的 Asset Supply / B-roll operator workspace**
   * 虽已有 product freeze 与 contract 冻结，但尚未形成最小可用的 operator-visible 能力；
   * 没有 B-roll / reusable asset / promote 意图闭环，运营无法形成持续生产。
2. **缺少统一的 publish\_readiness runtime 口径**
   * Board / Workbench / Delivery 对 publishable / publish\_gate 的理解不能继续分散；
   * 如果运营看到三套口径，就无法形成可信判断。
3. **缺少真正可用的 operator workspace**
   * 不是只有 line closure 就够；
   * 还必须有任务区、工作台、交付中心、反馈与素材复用的最小工作能力。
4. **当前“试运营”更多是 authority 试跑，不是运营生产试跑**
   * 这对架构验证有价值；
   * 但对真实运营价值不足。

### **1.2 裁决结论**

**当前主线由“Operator Trial Execution”切换为“Minimal Operator Capability Recovery”。**

---

## **2\. 当前阶段重新定义**

当前阶段正式定义为：

# **ApolloVeo 2.0 Minimal Operator Capability Recovery Wave**

其含义是：

1. 不推翻既有母计划、四层架构、packet-first、line-first 方向；
2. 不推翻 Matrix Script / Digital Anchor / Hot Follow 的既有闭环成果；
3. 纠正当前执行目标：
   * 不再把“直接试运营”当成当前唯一目标；
   * 改为“先补足最小运营能力，再回到试运营”；
4. 当前最重要的不是新增更多抽象，而是让运营具备最小可工作的能力。

---

## **3\. 本阶段总目标**

在不进入 Platform Runtime Assembly、也不进入 Capability Expansion 的前提下，先恢复 ApolloVeo 的**最小运营能力**。

恢复完成后，系统应达到：

1. 运营具备最小可工作的 B-roll / Asset Supply 入口；
2. Task / Workbench / Delivery 对 publishability 的判断口径统一；
3. 三条线的 operator-visible workspace 达到“可解释、可操作、可判断”的最低标准；
4. Plan A 试运营可以从“authority trial”升级为“真实运营试跑”。

---

## **4\. 当前只允许做什么**

本阶段只允许围绕以下四类事项开工：

### **4.1 Asset Supply / B-roll Minimum Usable Capability**

目标：

* 把已冻结的 Asset Library / Promote / Closure contract 推进到最小可用 operator capability；
* 先支持查询、引用、promote intent，不做完整资产平台。

### **4.2 Unified Publish Readiness Producer**

目标：

* 不再允许 Board / Workbench / Delivery 各自解释 publishable；
* 形成唯一、统一、可消费的 runtime producer。

### **4.3 Operator Workspace Minimum Completion**

目标：

* Hot Follow 继续作为 baseline reference；
* Matrix Script 从 inspect-first 推到可用于真实运营判断；
* Digital Anchor 从 inspection-only 推到可进入真实 operator workspace。

### **4.4 Trial Re-entry Preparation**

目标：

* 在 4.1–4.3 具备后，重新打开 Plan A live trial；
* 这时的试跑才是面向真实运营的试跑。

---

## **5\. 当前明确禁止什么**

本阶段明确禁止：

* 进入 Platform Runtime Assembly Wave
* 进入 Capability Expansion Gate Wave
* 开第三条正式生产线
* 做完整资产平台 / 后台工具化
* 做 provider/model/vendor 控制台
* 做 React/Vite 全量重构
* 重开 Hot Follow 业务功能
* 改写 Matrix Script / Digital Anchor 已闭环 truth
* 把临时 placeholder / discovery-only surface 直接暴露为正式运营入口

---

## **6\. 角色分工**

### **A. Codex（总架构师 / 总协调者）**

当前职责：

1. 统一把握本裁决方向；
2. 防止工程继续陷入局部 UI patch 或 contract-only drift；
3. 将本阶段切分为若干个可独立 review / merge / rollback 的 PR 波次；
4. 明确每个 PR 的 scope、红线、验收口径；
5. 在每一波次结束后做 narrow review，决定是否进入下一波。

Codex 当前不应做：

* 大范围代码实现
* 跳过波次直接开 Platform Runtime Assembly
* 直接恢复 Plan A 试运营

### **B. Claude（执行架构师 / 工程实施者）**

当前职责：

* 按 codex 切分好的 PR 波次执行
* 每个 PR 严格守 scope
* 每个 PR 做 evidence / execution log / index write-back
* 不扩 scope，不顺手修 unrelated 问题

Claude 当前不应做：

* 自行决定新波次
* 自行扩大到 Platform Runtime Assembly / Capability Expansion
* 把 placeholder surface 直接做成运营正式入口

### **C. 产品经理**

当前职责：

* 明确最小运营能力标准
* 定义 B-roll / Asset Supply 的“最小可用”范围
* 定义真实试运营的 go/no-go 口径
* 做每一波次的业务验收

### **D. Reviewer / Merge Owner**

当前职责：

* 按波次独立 review / close
* 阻止 scope drift
* 阻止提前开下一阶段
* 保证 `main` 继续作为唯一 authority baseline

---

## **7\. PR 波次拆分（强制执行顺序）**

## **PR-1 · Unified Publish Readiness Runtime Recovery**

**目标**：先统一运营最关键的“是否可发布”判断。

### **必做**

* 落地统一的 `publish_readiness` runtime producer
* Board / Workbench / Delivery 全部消费同一结果
* 落地 `final_provenance` 的真实 producer / emitter
* 交付中心消费 `required` / `blocking_publish`
* 不再允许各面各自重算 publishable

### **禁止**

* 不做 UI 美化
* 不做 B-roll 页面
* 不做新 provider
* 不做平台总装配

### **验收**

* 三个 surface 的 publish/readiness 口径一致
* no second truth source
* evidence / tests / logs 完整

---

## **PR-2 · B-roll / Asset Supply Minimum Usable Operator Capability**

**目标**：补足真实运营最缺的一块。

### **必做**

* 最小 asset library read-only service
* 最小 promote request path
* 最小 promote feedback closure path
* 最小 operator-visible asset surface
* 支持 query / filter / reference / promote intent
* 显式保证 scene\_pack non-blocking

### **禁止**

* 不做完整资产平台
* 不做 admin 系统
* 不做复杂 CRUD
* 不做平台化资产中心

### **验收**

* 运营可查看和筛选最小资产集
* 可发起 promote intent
* 可看到 promote 状态闭环
* 不破坏 line truth

---

## **PR-3 · Matrix Script Operator Workspace Promotion**

**目标**：把 Matrix Script 从 inspect-first 推到真实运营可用。

### **必做**

* 补齐 delivery binding / artifact lookup 的可用支撑
* 让 Delivery Center 不再只是 placeholder inspect
* 保证 variation/workbench/delivery/feedback 是可操作闭环

### **禁止**

* 不改 packet truth
* 不重开已关闭的 §8.A–§8.H correction chain
* 不扩到其他线

### **验收**

* Matrix Script 可作为第一条真实 operator trial line
* 交付判断可支撑运营

---

## **PR-4 · Digital Anchor Operator Workspace Recovery**

**目标**：把 Digital Anchor 从 inspection-only 推到真实运营入口。

### **必做**

* formal `/tasks/digital-anchor/new`
* create-entry payload builder
* publish feedback D.1 write-back implementation
* role/speaker panel 真正生产可见
* 禁止 page-first drift

### **禁止**

* 不扩 provider/model/vendor controls
* 不扩到 avatar 平台化
* 不开第三条线

### **验收**

* Digital Anchor 不再是 preview-only
* operator 可真实进入任务、工作台、反馈闭环

---

## **PR-5 · Real Operator Trial Re-entry Gate**

**目标**：在 PR-1 \~ PR-4 全部完成后，重新打开真实试运营。

### **必做**

* 重写 Plan A 试运营入口口径
* 明确 operator-eligible surfaces
* 明确不再只是 authority trial
* 组织真实试运营样本与 write-up

### **禁止**

* 不进入 Platform Runtime Assembly
* 不进入 Capability Expansion

### **验收**

* 产品经理签发 go/no-go
* coordinator / architect / reviewer signoff
* 真实试运营开始

---

## **8\. 当前 accepted baseline 与本裁决的关系**

本裁决**不推翻**以下基线：

* `apolloveo_2_0_master_plan_v1_1.md`
* `apolloveo_2_0_top_level_business_flow_v1.md`
* Matrix Script / Digital Anchor / Hot Follow 既有 contract 与 line closure
* donor capability-only
* packet/envelope/validator discipline
* four-layer architecture baseline

本裁决只是对**当前执行方向**做出修正：

从“先试运营，再看缺什么”
调整为
“先恢复最小运营能力，再试运营”。

---

## **9\. 总控口令**

**Current execution focus is ApolloVeo 2.0 Minimal Operator Capability Recovery.**
**Real operator trial is NO-GO at the current repo state.**
**Do not enter Platform Runtime Assembly.**
**Do not enter Capability Expansion.**
**First recover unified publish readiness.**
**Then land minimum B-roll / Asset Supply operator capability.**
**Then promote Matrix Script to a real operator trial line.**
**Then recover Digital Anchor from inspection-only to real operator workspace.**
**Only after PR-1 through PR-4 are green may PR-5 reopen real operator trial.**
**Codex owns direction and PR slicing.**
**Claude executes one PR at a time.**

---

## **10\. 一句话总结**

**ApolloVeo 当前不是“可以直接试运营”的状态，而是“架构和契约已证明成立，但最小运营能力尚未恢复”的状态。当前主线必须切换为 Minimal Operator Capability Recovery；先恢复能力，再重新进入真实试运营。**
