# Verification Baseline

## 1. 目的

本文件冻结当前分支进入后续 PR 前的最小验证口径。

目标不是补齐全部 CI，而是把当前解释器前提、可跑测试范围、最小回归命令和本地/CI 口径写清楚。

## 2. Python 最低版本

当前文档冻结结论：

- Hot Follow 相关运行与测试基线按 `Python 3.10+` 处理

依据：

- 仓库当前已使用 `str | None` 等 Python 3.10+ 语法
- `gateway/requirements.txt` 未显式写出 `python_requires`
- baseline 文档已记录本机 `python3` 为 `Python 3.9.6`
- 依赖 `gateway.app.config` / router 的测试在 Python 3.9 下会在收集阶段失败

## 3. 当前测试解释器限制

### 3.1 Python 3.9

当前限制：

- 不能作为 Hot Follow 主线测试解释器基线
- 依赖 router / app / config 导入的测试可能在收集阶段失败

已知触发特征：

- `str | None`
- 其他 Python 3.10+ 类型语法

### 3.2 Python 3.10+

当前冻结口径：

- 作为后续 PR 的本地与 CI 最低验证解释器
- 需要用于 router/config 相关回归与更完整的 Hot Follow 测试

## 4. 最小回归命令

### 4.1 文档冻结的最低命令

```bash
python3 -m pytest gateway/app/services/status_policy/tests/test_ready_gate.py -q
```

用途：

- 验证最小 status/ready-gate 基线未被破坏

### 4.2 Python 3.10+ 环境下应追加的最小回归

```bash
python3 -m pytest gateway/app/services/status_policy/tests/test_app_import_smoke.py -q
```

用途：

- 验证 `gateway.app.main` 可导入
- 及早发现 router/config 级解释器不兼容

## 5. 本地 / CI 验证口径

### 5.1 本地

当前本地口径冻结为：

- 若本机只有 Python 3.9，则至少记录“ready gate 单测可跑，router/config 级测试受解释器阻断”
- 若本机具备 Python 3.10+，则应以 Python 3.10+ 执行最小回归

### 5.2 CI

当前 CI 口径冻结为：

- 后续新增或恢复 CI 时，最低 Python 版本按 3.10+ 设置
- CI 至少覆盖最小回归命令

本 PR 不做：

- 不新增 CI 配置
- 不扩大成全量测试矩阵

## 6. Python 3.9 vs 3.10+ 已知差异

- Python 3.9 无法稳定承载当前仓库已使用的 `X | None` 语法
- Python 3.10+ 才能作为当前 Hot Follow runtime 与测试基线
- 因此“ready gate 单测可跑”不等于“Hot Follow 主链在 3.9 可验证”

## 7. 当前做 / 当前不做

### 当前做

- 冻结 Python 3.10+ 最低基线
- 冻结当前最小回归命令
- 冻结本地与 CI 的最小验证口径

### 当前不做

- 不修改 `gateway/requirements.txt`
- 不补 `python_requires`
- 不承诺 Python 3.9 兼容
- 不在本 PR 中扩大测试面
