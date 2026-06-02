# Matrix Script Workbench Primary Operator Flow

Date: 2026-06-02

Scope: Workbench presentation only.

## Change

Matrix Script Workbench primary scan is reordered around the operator action:

1. 主视频预览 / 生成视频
2. 背景、素材、配乐调整
3. 交付入口
4. 视频变体
5. 脚本理解 / 故事理解
6. 技术诊断

The previous Phase 2B detail cards are preserved as hidden compatibility
markup and no longer drive the visible operator flow.

## Rules Preserved

- No Hot Follow change.
- No Digital Anchor change.
- No `artifact_storage.py` change.
- No schema / contract change.
- No generation path change.
- No Akool live path.
- `official_publish_ready=false` remains the only visible publish truth.

## Acceptance

Focused tests cover:

- ungenerated state has one primary `生成视频预览` action;
- invalid ungenerated actions are absent from Section A;
- generated state renders inline video;
- material / music adjustment follows the preview block;
- delivery CTA appears only when `delivery_candidate=true`;
- variants and script understanding are folded/de-emphasized;
- raw backend/provider/publish tokens are absent from the primary flow.
