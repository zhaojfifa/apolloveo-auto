# Verification Baseline

## 1. 目的

本文件冻结当前分支的最小验证口径，目标是让工程团队能在相同解释器前提下稳定复现最小回归集，而不是在本 PR 中扩成全量 CI。

## 2. Python 基线

当前冻结结论：

- 工程最低验证基线：`Python 3.10+`
- 当前仓库推荐执行解释器：`./venv/bin/python`

当前仓库实测：

- 系统 `python3`：`Python 3.9.6`
- `./venv/bin/python`：`Python 3.11.15`

原因：

- 仓库已使用 `str | None` 等 Python 3.10+ 语法
- `gateway.app.config` / `gateway.app.main` 相关导入链不再以 Python 3.9 为目标
- 因此 Python 3.9 不能作为 Hot Follow runtime 主线验证解释器

## 3. 当前测试解释器要求

### 3.1 可在系统 `python3` 下跑的最低纯单测

当前仅把不穿透 `gateway.app.main` 导入链的纯单测视为 Python 3.9 可尝试项，例如：

```bash
python3 -m pytest gateway/app/services/status_policy/tests/test_ready_gate.py -q
```

用途：

- 验证最小 deliverable/status 单测仍可执行

限制：

- 这不代表 Hot Follow 主链可在 Python 3.9 下验证
- 这也不代表 router/config/import smoke 在 Python 3.9 下可通过

### 3.2 必须在 `Python 3.10+` 或 `./venv/bin/python` 下跑的测试

以下回归应视为 `Python 3.10+` 测试：

```bash
./venv/bin/python -m pytest gateway/app/services/ready_gate/tests/test_line_binding.py -q
./venv/bin/python -m pytest gateway/app/services/status_policy/tests/test_line_runtime_binding.py -q
./venv/bin/python -m pytest gateway/app/services/status_policy/tests/test_hot_follow_state_line_binding.py -q
./venv/bin/python -m pytest gateway/app/services/status_policy/tests/test_app_import_smoke.py -q
```

用途：

- 验证 line-aware gate binding 已真实接线
- 验证 `compute_hot_follow_state()` 已消费 runtime 绑定入口
- 验证 `gateway.app.main` 导入链在推荐解释器下可工作

## 4. 最小回归命令

### 4.1 PR-4 推荐最小回归集

```bash
python3 -m pytest gateway/app/services/status_policy/tests/test_ready_gate.py -q
./venv/bin/python -m pytest gateway/app/services/ready_gate/tests/test_line_binding.py -q
./venv/bin/python -m pytest gateway/app/services/status_policy/tests/test_line_runtime_binding.py -q
./venv/bin/python -m pytest gateway/app/services/status_policy/tests/test_hot_follow_state_line_binding.py -q
./venv/bin/python -m pytest gateway/app/services/status_policy/tests/test_app_import_smoke.py -q
```

说明：

- 第一条是系统 `python3` 可尝试的最低纯单测
- 后四条是当前推荐的 `Python 3.10+` 回归集
- 当前仓库里 `./venv/bin/python` 就是本地推荐执行入口

### 4.2 当前仓库中的 `./venv/bin/python` 角色

- 它是本仓库当前最接近 CI 的推荐解释器
- 它承载 router/config/import smoke 与 line-binding 回归
- 若本机系统 `python3` 仍停留在 3.9，则本地验证应优先使用它

## 5. 本地 / CI 验证口径

### 5.1 本地

当前本地口径冻结为：

- 允许用系统 `python3` 跑最低纯单测
- 推荐用 `./venv/bin/python` 跑完整的最小回归集
- 提交 PR 时，若只跑了 Python 3.9 纯单测，应明确说明 3.10+ 项是否未跑

### 5.2 CI

当前 CI 口径冻结为：

- 最低 Python 版本按 `3.10+`
- 恢复或新增 CI 时，至少覆盖本文件中的 PR-4 推荐最小回归集

本 PR 不做：

- 不新增 CI 配置
- 不补全量矩阵
- 不承诺 Python 3.9 兼容

## 6. Python 3.9 vs 3.10+ 已知差异

- Python 3.9 不能作为当前 Hot Follow runtime 主线测试解释器
- `gateway.app.main` / router / config 相关测试应视为 `Python 3.10+` 项
- `Python 3.10+` 才是当前 line-aware binding 与 import smoke 的推荐基线

## 7. 当前做 / 当前不做

### 当前做

- 冻结 Python 3.10+ 最低验证基线
- 冻结系统 `python3` 与 `./venv/bin/python` 的职责边界
- 冻结 PR-4 最小回归命令

### 当前不做

- 不修改 `gateway/requirements.txt`
- 不补 `python_requires`
- 不新增完整 CI
- 不把纯单测可跑误写成“全仓库 Python 3.9 兼容”
