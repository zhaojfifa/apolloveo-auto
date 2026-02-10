# UI 多语言（i18n）与语言切换基准（Tasks / Board / Wizard）

适用范围：
- /tasks（Board）
- /tasks/newtasks（Wizard Step 1：场景选择）
- /tasks/avatar/new、/tasks/hot/new、/tasks/baseline/new（各场景入口页）
- 后续所有新增页面必须复用同一套语言机制

## 0. 设计目标（为什么这么做）
1) URL 可复制：运营、产品、QA 用同一链接复现同一语言与同一页面状态  
2) 全站一致：跨页面跳转语言不丢失  
3) 物理隔离入口：Wizard 的存在用于隔离不同场景入口，避免参数混用导致 422；语言链路同样必须稳定携带  
4) 可扩展：从 2 语到 N 语，不引入“混杂状态”

---

## 1. 语言 SSOT：ui_locale 查询参数（唯一真相）
### 1.1 约定
- `?ui_locale=zh` 中文
- `?ui_locale=mm` 缅文
- `?ui_locale=en` 英文
- （未来扩展：th、vi、id…）

### 1.2 解析优先级（必须固化）
1) URL query：ui_locale（最高优先级）
2) cookie / localStorage（若工程已有）
3) 默认值：zh（或你们产品定义的 default）

> 禁止：页面内部“单独维护一份语言状态”，导致局部语言与全局语言不一致。

---

## 2. Topbar 语言切换行为（必须一致）
### 2.1 点击切换
- 切换语言 = 刷新当前页面
- 保留当前 path 与其它 query，仅修改/注入 ui_locale

### 2.2 站内链接携带规则（强制）
所有站内跳转都必须携带当前 ui_locale：
- /tasks?ui_locale=mm
- /tasks/newtasks?ui_locale=mm
- /tasks/avatar/new?ui_locale=mm
- /tasks/hot/new?ui_locale=mm
- /tasks/baseline/new?ui_locale=mm

> 尤其注意：Wizard 的三张卡片跳转必须带 ui_locale，否则会出现“入口页是缅文，下一页变回英文/中文”。

---

## 3. 文案渲染策略：服务端优先，前端兜底
### 3.1 服务端模板（Jinja）为主
- 模板中的静态文案必须使用：`{{ t("some.key") }}`
- 禁止把 `[some.key]` 当作“可接受的显示结果”

### 3.2 前端 i18n 仅做兜底/动态
仅允许用于：
- JS 动态插入的内容
- 兜底替换（极少数、不可依赖）

线上验收标准：
- 页面不允许出现 `[tasks.xxx]`、`[common.xxx]` 等未渲染 token

---

## 4. 新增语言的最小工作流（可扩展到 N 语）
### 4.1 新增语言 Checklist
1) 在后端支持语言列表加入新 locale（如 th）
2) 词典文件中补齐核心 key（至少覆盖 tasks/board/wizard/topbar/common buttons）
3) 字体栈补齐（例如泰语 Noto Sans Thai）
4) 验证 UI 不溢出：按钮、徽章、筛选栏、卡片标题 2 行截断
5) 验证全链路 URL：从 /tasks → /tasks/newtasks → /tasks/{scene}/new 都保留 ui_locale

### 4.2 Fallback 策略（必须明确）
- key 缺失：fallback 到 en（或 zh），并记录日志（可选）
- 线上严禁把 key 原样吐出为 `[key]`

---

## 5. 编码与换行规范（避免 Render/Jinja 解码崩溃）
### 5.1 强制规则
- `gateway/app/templates/**/*.html` 必须 UTF-8（允许 utf-8-sig）
- 禁止 GBK/GB18030 混入（会导致 UnicodeDecodeError）

### 5.2 自检与修复
- 若线上出现 `UnicodeDecodeError`：
  - 先检测文件编码
  - 统一转为 UTF-8 再提交

---

## 6. 现状文件清单（基于当前工程）
静态资源（已出现/已使用）：
- `gateway/app/static/i18n.css`
- `gateway/app/static/css/ui_v185.css`
- `gateway/app/static/js/i18n_v185.js`（若用于 token 替换/前端兜底）

页面模板：
- `gateway/app/templates/tasks.html`（Board）
- `gateway/app/templates/tasks_newtasks.html`（Wizard Step 1）
- `gateway/app/templates/tasks_avatar_new.html`（如存在）
- `gateway/app/templates/hot_follow_new.html` 或 `/tasks/hot/new` 对应模板（以工程为准）

服务端（以工程为准，核心是：能从 request 中得到 locale，并给 t() 提供上下文）：
- `gateway/app/i18n.py`（或同等模块）
- `gateway/app/web/templates.py`（TemplateResponse 注入上下文）

---

## 7. Tailwind CDN（当前是否作为基准？）
结论：
- 允许作为 v1.9 UI 原型/无构建链路阶段的“临时基准”
- 但不作为长期生产基准（控制台会有 `cdn.tailwindcss.com should not be used in production` 警告，且依赖外部 CDN）

临时基准要求：
- 引入位置要统一（避免每页各自引入导致版本不一致）
- 进入“生产加固阶段”时迁移为本地静态 CSS 产物

建议你现在就做的 2 个提交（非常小，但能把基准锁死）
# 1) 写入 skill
git checkout VeoScenes01
mkdir -p docs/skill
# 写入上面的 UI_I18N_LOCALE_BASELINE.md
git add docs/skill/UI_I18N_LOCALE_BASELINE.md
git commit -m "docs(skill): add UI i18n locale switching baseline (tasks/board/wizard)"
git push

# 2) 可选：加一个 docs/skill/README.md 索引（如果你们已经有 skill 索引就更新它）
