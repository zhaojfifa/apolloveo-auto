# Matrix Script Real Result Baseline (2026-06-01)

Status: **Baseline / governance document. No code, no UI, no contract, no schema change in this artifact.** This is the single target + constraint set for the next engineering project. It supersedes the fragmented PR-by-PR narrative as the cognitive anchor; the underlying repo authorities (four-layer state, factory contracts, PR-0 design plan) remain the truth.
Branch: `phase3/matrix-script-real-result-baseline`
Main baseline: `origin/main = 3ecff9e0d61ffc677bd22015dc143c2db5c01540` (through PR-184; PR-185 delivery-render-path-fix open).
Authorization to start implementation: **NOT YET.** Implementation begins only after this baseline is reviewed.

---

## 1. Current Conversation Summary

### 1.1 Completed mainline (Matrix Script Phase 3)

| PR | Result |
| --- | --- |
| PR-0 #165 | Phase 3 Akool real-generation design plan (docs) |
| PR-1 #166 | Akool capability adapter skeleton (mocked) |
| PR-2 #167 | Shot plan skeleton |
| PR-3 #168 | Scene artifact / manifest skeleton |
| PR-4R #169 | Minimal result loop — real `final.mp4` (ffmpeg) |
| PR-5R #170 | Minimal result service bridge |
| PR-6R #171 | Minimal result record |
| PR-7R #172 | Result projection (operator + delivery) |
| PR-8R #173 | Surface view |
| PR-9R #174 | Workbench minimal result read-only block |
| PR-10R #175 | Minimal result orchestrator |
| PR-11R #176 | Internal minimal result command |
| PR-12R #177 | Internal minimal result route |
| PR-13R #178 | Workbench action MVP |
| PR-14R #180 | Operator Visibility Wave (Workbench trace + Delivery local result) |
| PR-15R #181 | Akool real one-shot gate (default off) |
| PR-16R #182 | Artifact staged persistence |
| PR-17R #183 | Real operator trial route |
| PR-184 | R2 / artifact preview staging — `final.mp4` openable via `preview_url` |
| PR-185 (open) | Delivery render-path fix (staged candidate renders via `ms_pub`) |

### 1.2 Proven to hold
- Four-layer architecture is not an empty doc; the four-layer state model supports Workbench/Delivery state interpretation.
- Matrix Script runs as an independent Production Line under the ApolloVeo 2.0 factory-shaped architecture.
- `final_video` / subtitles / audio / manifest / scene clips enter an `artifact_staged` structure.
- Provider URLs do not surface; `official_publish_ready` stays `false`; Workbench/Delivery invent no state truth.
- The technical chain runs end to end: task → Workbench trigger → route → ffmpeg → real `final.mp4` → `artifact_staged` → browser-openable `preview_url`.

### 1.3 The real exposed problem
The blocker is **not** the low-level chain. It is: **the generated result is not operator-usable.**
Validation (incl. the tomato-beach trial) showed: `final.mp4` plays and `preview_url` opens, **but the content is fallback / color-card / technical placeholder** — no beach, no cherry tomatoes, no product close-up, no person/action, no juicy bite, no CTA hand-off.

Binding distinctions for all future work:
```
Generated mp4      != Operator usable video
Preview URL opens  != Valid content
Artifact staged    != Real delivery candidate
```
The prior wave proved "the system can generate an mp4"; it did **not** prove "the system can generate a usable video from an operator script."

---

## 2. Architecture Judgment

**ApolloVeo 2.0 factory-shaped architecture HOLDS. Matrix Script continues as an independent production line.**

Basis: ApolloVeo 2.0 is an AI content-production factory oriented to final-video delivery; a production line is organized around a single primary result; Matrix Script's primary result is `final_video`; the line is supported by SOP / Skills / Worker / Deliverable / Asset Sink.

**Not reopened this round:** factory architecture; production-line boundary; Workbench/Delivery separation; `artifact_staged` vs `local_workspace`; provider-leakage boundary; official-publish gate.

---

## 3. Four-Layer State Judgment

**The four-layer state model HOLDS and remains the binding boundary.**

- **L1 — Pipeline Step Status:** did each step run — script plan / scene generation / audio / subtitles / assembly / staging.
- **L2 — Artifact Facts:** existence of `final.mp4` / subtitles / audio / manifest / artifact refs.
- **L3 — Current Attempt / Readiness:** is the current generation still current; does the current result meet operator-candidate conditions; or is it only a technical preview.
- **L4 — Operator Summary / Workbench / Delivery:** consumes L2/L3 only; invents no state truth; must not present fallback as a delivery candidate.

Binding constraints:
```
UI must not reverse-edit truth.
Presenter must not invent artifacts.
Delivery must not treat a technical preview as a delivery candidate.
artifact_staged != automatically operator_usable.
official_publish_ready must not be opened.
```

**Conclusion:** the base is sufficient to support the next production-line project. The next stage must **not** keep proving the base. It must turn to: **generate operator-visible results from a given script.**

---

## 4. Next Engineering Goal

**Project name:** Matrix Script Real Operator Result Project.

**Sole goal:** using the fixed script 《海边与圣女果的盛夏约定》, produce one short-video result that an operator can open, watch, and that is broadly semantically matched.

**NOT the goal:** re-prove route / ffmpeg / artifact ref / `preview_url`; build more color-card fallback; re-slice low-level record / projection / surface.

---

## 5. Fixed Tomato Script (《海边与圣女果的盛夏约定》)

```
【场景1：海风与初见（吸睛前3秒）】
画面意境：阳光明媚的海滩，蓝天白云。一位穿着白色吊带裙、长发飘飘的美女迎着海风，对着镜头露出甜美灿烂的笑容。
文案旁白：这个夏天，总要去趟海边吧？去吹吹海风，去尝尝属于夏天的味道。

【场景2：产品惊艳亮相（核心卖点）】
画面意境：镜头特写。美女手中捧着一个透明的玻璃碗，里面装满了刚洗干净、还带着晶莹水珠的红色小番茄。阳光照在番茄上，红润剔透，像一颗颗红宝石。
文案旁白：看！这是刚刚从温室采摘来的小番茄。每一颗都吸饱了阳光，圆润饱满，外皮薄得仿佛一碰就会破。

【场景3：沉浸式品尝（大口吃动作）】
画面意境：中景转近景特写。美女坐在海边的沙滩椅上，伸出纤细的手指，轻轻捏起一颗饱满的红色小番茄放进嘴里。
动作细节：她闭上眼睛，大口咬下去，脸上瞬间洋溢出满足和幸福的表情。可以听到清脆的“咔嚓”爆汁声。
文案旁白：轻轻咬上一口，清甜的汁水瞬间在舌尖炸开！酸甜适中，满满的维C，这才是夏日海滩的绝配！

【场景4：情感共鸣（互动收尾）】
画面意境：美女对着镜头调皮地眨眨眼，将手中的玻璃碗向前递向镜头，仿佛在邀请屏幕前的观众一起品尝。背景是渐渐退潮的海浪。
文案旁白：一口爆汁，满嘴清香。这个夏天，和我一起炫一碗爆汁小番茄吧！
```

---

## 6. Fixed 5-Shot Target (no free drift)

| Shot | Visual | Voiceover |
| --- | --- | --- |
| 01 — 海边 Hook | beach, sea, summer sunlight, blue sky, woman smiling in breeze | 这个夏天，总要去趟海边吧？去吹吹海风，去尝尝属于夏天的味道。 |
| 02 — 小番茄产品特写 | red cherry tomatoes, glass bowl, water drops, sunlight, fresh product close-up | 看！这是刚刚从温室采摘来的小番茄。每一颗都吸饱了阳光，圆润饱满。 |
| 03 — 拿起小番茄 | hand / woman picks up a cherry tomato near beach / summer table / beach chair | 轻轻捏起一颗，薄薄的外皮包着满满汁水。 |
| 04 — 品尝爆汁 | person eats / bites cherry tomato, satisfied expression, juicy food reaction | 一口咬下去，清甜的汁水瞬间在舌尖炸开！酸甜适中，满满夏日感。 |
| 05 — 递向镜头 CTA | glass bowl of tomatoes offered toward camera, invitation gesture, sea / summer background | 这个夏天，和我一起炫一碗爆汁小番茄吧！ |

---

## 7. Acceptance Model

### 7.1 Technical success (chain only — NOT final success)
```
final.mp4 exists · preview_url opens · ffprobe duration > 0 · artifact_staged exists · official_publish_ready=false
```

### 7.2 Operator success (required)
```
operator_usable=true
technical_preview=false
delivery_candidate=true
visual_semantic_match = partial_pass | pass
official_publish_ready=false
```
Minimum bar:
1. `final.mp4` opens in a browser.
2. video is NOT pure color block / pure subtitle card / pure placeholder.
3. ≥ 5 shots.
4. ≥ 3 shots semantically match the script.
5. ≥ 1 shot uses real generation or real material.
6. picture conveys "beach + cherry tomatoes + summer 种草".
7. voiceover or subtitles correspond to the script.
8. Workbench shows the `operator_usable` judgment.
9. Delivery shows the staged preview.
10. `official_publish_ready=false`.

### 7.3 Fallback handling (binding)
If the result is still color-card / fallback:
```
technical_preview=true
operator_usable=false
delivery_candidate=false
visual_semantic_match=failed
blocked_reason=fallback_only_or_missing_real_visuals
official_publish_ready=false
```
**Fallback video must never be treated as an operator candidate.**

---

## 8. Engineering Constraints

### 8.1 Forbidden directions (proven insufficient — do not slice PRs around these)
```
local-only record · projection wrapper · surface wrapper · template polish ·
mock-only test · color-card fallback · technical-preview-only
```

### 8.2 Allowed engineering actions (only around real results)
```
Gemini shot plan / prompt · Akool one-shot generation · real material / B-roll ingestion ·
Azure TTS · ffmpeg assembly · semantic acceptance gate · artifact/R2 preview ·
Workbench / Delivery acceptance display
```

### 8.3 Capability use principles
Allowed: Gemini (script understanding, shot prompt, semantic check); Akool (≥1 real visual shot, prefer Shot 02 or Shot 04); ffmpeg (concat, subtitles, audio); Azure (TTS); Artifact/R2 (staged preview + result sink).
Must obey: `provider_url` not surfaced; Akool task id not surfaced; model/credit not surfaced; `temporary_url` not final truth; only artifact/R2 staged is an operator preview entry; `official_publish_ready=false`.

### 8.4 Immovable boundaries (forbidden to change)
```
four-layer state model · factory contracts · schema/packet (unless absolutely necessary) ·
Hot Follow · Digital Anchor · artifact_storage.py · official_publish_ready=true ·
publish_url / publish_status · provider_url surfacing
```
If a schema/packet/contract/runtime change seems necessary, STOP and report — do not widen scope.

---

## 9. PR Plan (max two PRs)

### PR-A — Tomato Real Result Path
```
script → fixed 5-shot semantic plan → real/fallback visual generation →
TTS/subtitle → ffmpeg final.mp4 → artifact_staged → preview_url → operator acceptance
```
Must include: ≥ 1 real visual shot; ≥ 3/5 semantic shot matches; `operator_usable` computation; `delivery_candidate` computed from operator acceptance; **no color-card-only success**.

### PR-B — Operator Acceptance Surface
Workbench / Delivery display: `preview_url`, `operator_usable`, `technical_preview`, `visual_semantic_match`, shot checklist, `blocked_reason`.

If PR-A can complete the page display, PR-A and PR-B may merge into one PR. **Do not split into a string of low-level micro-PRs.**

---

## 10. Validation Report Template

```md
# Matrix Script Tomato Real Result Validation Report

## 1. Environment
- branch: / commit: / host: / task_id: / Akool enabled: / storage backend: / ffmpeg: / Azure TTS:

## 2. Input
- script: / target platform: / target duration: / target language:

## 3. Generation Path
- Gemini shot plan: / Akool attempted: / real visual shot: / Azure TTS: / ffmpeg assembly: / artifact/R2 staging:

## 4. Shot Result
| Shot | Expected | Actual | Source | Pass |
|---|---|---|---|---|
| 01 | 海边 Hook |  |  |  |
| 02 | 小番茄特写 |  |  |  |
| 03 | 拿起小番茄 |  |  |  |
| 04 | 品尝爆汁 |  |  |  |
| 05 | 递向镜头 CTA |  |  |  |

## 5. Final Video
- preview_url: / duration: / resolution: / has_audio: / has_subtitles: / storage_scope: / delivery_candidate: / official_publish_ready:

## 6. Operator Acceptance
- operator_usable: / visual_semantic_match: / technical_preview: / shot_match_count: / real_visual_count: / blocked_reason: / biggest issue:

## 7. Boundary
- no provider_url: / no publish_url: / no Akool task/model/credit: / no schema/contract changes: / no Hot Follow/Digital Anchor changes:

## 8. Verdict
- PASS / PASS WITH LIMITATIONS / FAIL
- next action:
```

---

## 11. Stop Condition

This file is the precondition for starting the next project. Per the launch instruction:
1. baseline file created — **this document**;
2. next engineering plan is clear — §4 / §9;
3. **no implementation begins until this baseline is reviewed.**

No coding starts in this turn. Awaiting review.
