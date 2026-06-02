# Matrix Script Workbench Operator-First Layout

## Scope

This change is a narrow Workbench layout adjustment after the Matrix Script cleanup baseline.

It changes only the operator-visible ordering and presentation in `task_workbench.html`, plus Matrix Script Workbench tests. It does not add generation capability, runtime wiring, routes, schemas, contracts, or provider integration.

## Operator Flow

The Matrix Script Workbench primary scan is now:

1. A. 主视频结果
2. B. 镜头与素材调整
3. C. 声音、字幕与音乐
4. D. 交付入口
5. E. 视频变体
6. F. 脚本理解
7. G. 技术诊断

## Result Preview

When a PR-A result is `operator_usable=true` and has `preview_url`, the main result block renders a real HTML video player bound to that preview URL.

The open-video link remains secondary. `official_publish_ready` remains false.

## Shot Adjustment

The previous storyboard acceptance list is presented as shot/material cards. Each card carries:

- current material
- source
- semantic status
- included-in-current-video state
- disabled replacement/regeneration action positions

Fallback semantic reuse shots show an operator note recommending additional real tasting / handoff material.

## Boundary

No Hot Follow, Digital Anchor, artifact storage, schema, contract, Akool live, publish URL, or official publish readiness behavior is changed.
