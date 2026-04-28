ApolloVeo 2.0 · Capability Expansion Gate Wave 指挥单 v1
文档性质：预备指挥单 / HOLD 适用阶段：仅在 Platform Runtime Assembly Wave 签收后启用 用途：定义 W2.2 / W2.3 / durable persistence / runtime API 的解锁条件 当前状态：HOLD —— 不得提前执行

当前判断
在 Platform Runtime Assembly Wave 未签收前，以下事项不得启动：
* W2.2 Subtitles / Dub Provider
* W2.3 Avatar / VideoGen / Storage Provider
* durable persistence backend 正式化
* runtime API / callback handler 正式化
* 第三条正式生产线 commissioning

解锁条件
必须同时满足：
1. Shared Logic Port Merge 已签收
2. Compose / Large Service Extraction 已签收
3. Declarative Ready Gate 已签收
4. Runtime Assembly Skeleton 已签收
5. Matrix Script / Digital Anchor 闭环 truth 未被破坏
6. evidence index / authority wording 已清理完成
7. architect + reviewer 发出 platform assembly signoff

解锁顺序建议
1. W2.2 Subtitles / Dub Provider
2. W2.3 Avatar / VideoGen / Storage Provider
3. durable persistence additive wave
4. runtime API additive wave
5. third production line commissioning

红线
* 不得用 capability expansion 替代 platform assembly
* 不得把 provider fallback 写成 primary truth
* 不得把 durable persistence 嵌回 packet truth
* 不得把 runtime API 变成新的业务真相宿主
* 不得回写已闭环产线的 A/B/C/D truth 定义

