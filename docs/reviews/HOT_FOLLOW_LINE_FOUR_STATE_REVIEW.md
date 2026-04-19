# Hot Follow Line Four State Layer Review

Date: 2026-04-19

## Scope

This review covers only the Hot Follow production line after the runtime rollback to the pre-PR-A/PR-B compose baseline.

The rollback is intentionally separate from repair work:

- Runtime rollback PR: `revert(compose): restore hot follow pre-pr-a-b runtime`
- Rollback target: pre-PR-A/PR-B baseline at `46dede8`
- Review docs and execution logs are retained.

## Live Evidence Inputs

### Task `ffe9083de6ee`

Observed production facts:

- `compose` is already blocked by `bitrate_too_high`
- `compose_allowed = false`
- `compose_input_policy.mode = blocked`
- task card still presents compose-ready / compose-not-done style messaging

Conclusion:

- blocked compose truth exists in lower state, but it is not the SSOT for presenter messaging.

### Task `c3a11f7852e2`

Observed production facts:

- raw video exists
- subtitles remain `running` while subtitle artifacts/text are empty
- `audio_flow_mode = muted_no_tts`
- `no_dub = false`
- `no_dub_compose_allowed = false`

Conclusion:

- the no-dub / bgm-only legal line is not modeled as a real Hot Follow line path.
- empty subtitle / no-TTS outcomes can remain fake-running instead of terminal.

## Four-Layer Review Table

| Task | Artifact Facts Layer | Line Policy / Ready Gate Layer | Attempt / Runtime Terminal Layer | Presenter / Advisory Layer |
| --- | --- | --- | --- | --- |
| `ffe9083de6ee` | Compose input facts identify a blocked input: `compose_input_policy.mode=blocked`, reason `bitrate_too_high`. Final output is not the current ready artifact. | Hot Follow line policy should export `compose_allowed=false`, `compose_blocked=true`, `compose_allowed_reason=bitrate_too_high`. `compose_blocked` must override `compose_not_done` for line readiness. | Current compose attempt should be terminal as `compose_blocked_terminal`, not pending/running. This is not a real concurrent compose. | Task card, current attempt, operator summary, advisory, and workbench card text should project blocked input. They must not show compose-ready, recompose, or compose-not-done guidance as the primary message. |
| `c3a11f7852e2` | Raw video exists. Subtitle artifacts/text are empty. Audio lane facts report `audio_flow_mode=muted_no_tts`. Voiceover artifact is not the path. Final output is not ready. | Hot Follow line policy needs an explicit legal no-dub / bgm-only / preserve route when audio is intentionally muted/no-TTS and raw/source audio or BGM compose lane is valid. Today `no_dub=false` and `no_dub_compose_allowed=false`, so the line cannot distinguish legal no-dub from missing voiceover. | Subtitle attempt should terminate as `subtitle_empty_terminal` or `no_dub_route_terminal` when artifacts/text are empty and the line chooses muted/no-TTS. It must not remain fake `running`. | Presenter should project the terminal no-dub/bgm-only route. It should not recommend subtitle review merely because subtitle artifacts are empty when the line has selected a legal no-dub route, and it should not show a running subtitle step after terminal empty/no-dub resolution. |

## Layer Rules

### 1. Artifact Facts Layer

Artifact facts must answer only what exists or is observed:

- raw exists
- subtitle exists and has text
- voiceover exists
- source audio / BGM / preserved audio facts exist
- final exists and is current
- compose input is direct, derived, blocked, or unknown

Artifact facts must not decide presenter wording.

### 2. Line Policy / Ready Gate Layer

The Hot Follow line policy must consume artifact facts and decide what is allowed:

- `compose_allowed`
- `compose_blocked`
- `compose_allowed_reason`
- `subtitle_ready`
- `no_dub`
- `no_dub_compose_allowed`
- `publish_ready`

Blocked compose must override compose-not-done.

No-dub / bgm-only / preserve must become legal line states when the actual audio lane is `muted_no_tts` and the compose lane can proceed without generated TTS.

### 3. Attempt / Runtime Terminal Layer

Runtime attempts must end in a truthful terminal state:

- `compose_blocked_terminal`
- `subtitle_empty_terminal`
- `no_dub_route_terminal`
- `failed`
- `done`
- `pending`
- `running`
- `never`

An empty subtitle/no-TTS route must not remain `running` after the line has enough evidence to terminalize it.

### 4. Presenter / Advisory Layer

Presenter and advisory must be pure projection:

- No business recomputation in task card, current attempt, operator summary, advisory, or workbench card text.
- No compose-ready wording when lower layers say `compose_blocked=true`.
- No review-subtitles recommendation when the line has terminalized a legal no-dub/no-subtitle route.
- Presenter text must read from lower-layer exported fields.

## Required Repair Split

### PR-1: Artifact Facts Repair

- Formalize compose input facts.
- Formalize audio-lane facts.
- No presenter changes.

### PR-2: Line Policy / Ready Gate Repair

- `compose_blocked` must override `compose_not_done`.
- Model no-dub / bgm-only / preserve as legal line states where appropriate.
- No presenter changes except fields required for truth export.

### PR-3: Attempt / Runtime Terminal Repair

- Blocked compose becomes a real terminal attempt.
- Empty subtitle / no-dub route does not remain fake running.
- Finalize attempt state cleanly.

### PR-4: Presenter / Advisory Repair

- Pure projection only.
- No compose-ready wording when blocked.
- No review-subtitles recommendation when no subtitle artifact exists because a legal no-dub route is selected.
- No business recomputation in presenter.

## Acceptance

1. Blocked compose cannot coexist with compose-ready messaging.
2. No-dub / bgm-only legal line is modeled explicitly.
3. Empty subtitle/no-TTS terminal outcomes are not shown as running.
4. Presenter becomes a pure projection of lower-layer truth.
5. Hot Follow line behavior is repaired without patching other lines.
