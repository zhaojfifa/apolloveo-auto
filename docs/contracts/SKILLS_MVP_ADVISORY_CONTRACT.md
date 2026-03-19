# Skills MVP Advisory Contract

## Purpose

本 contract 只定义 Skills MVP v0 的第一个 read-only advisory hook。

它不是：

- Skills runtime framework
- orchestration contract
- multi-line plugin system

## Read-Only Nature

该 hook 只能读取当前 Hot Follow workbench hub 已存在的事实层与聚合层数据，并输出 advisory。

它不能成为新的 runtime truth source。

## Allowed Inputs

- `task`
- line contract reference
- `ready_gate`
- `pipeline`
- `pipeline_legacy`
- `deliverables`
- `media`
- `source_video`
- `artifact_facts`
- `current_attempt`
- `operator_summary`

## Allowed Outputs

- `advisory.id`
- `advisory.kind`
- `advisory.level`
- `advisory.recommended_next_action`
- `advisory.operator_hint`
- `advisory.explanation`
- `advisory.evidence`

输出必须是 non-blocking 的说明性数据。

## Forbidden Behaviors

- write repo state
- override `ready_gate`
- override status / pipeline / deliverables truth
- trigger compose / publish / parse / dub
- mutate artifacts
- become a hidden orchestration or policy layer

## Integration Boundary

Skills MVP v0 的唯一建议集成边界是：

- Hot Follow workbench / operator guidance payload 的只读 advisory block

当前不允许的集成边界：

- compose service
- ready gate engine
- status policy truth derivation
- publish runtime
- compatibility bridge as runtime owner
