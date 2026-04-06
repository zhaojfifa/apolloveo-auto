# Hot Follow SOP

## 1. Purpose

This runbook freezes Hot Follow in operator/engineer language for the current factory baseline.

The line skeleton is:

- `ingest -> parse -> adapt -> dub -> compose -> review_gate -> pack_publish_sink`

This SOP does not introduce a new line or UI shell. It describes the existing Hot Follow line in stable operational terms.

## 2. Scope

Hot Follow takes a source short video and produces a publishable localized final video.

Current entry modes:

- link ingest
- local video ingest

Current priority target-language profiles:

- Myanmar
- Vietnamese

Current local-upload source-language scope:

- Chinese
- English

## 3. SOP Stages

### 3.1 Ingest

Goal:

- create a normal `hot_follow` task
- normalize the source into a line-owned raw/source video artifact

Operator actions:

- choose source mode
- provide link or upload local video
- choose target language and basic audio profile

Truth outputs:

- task record exists
- raw/source video reference exists
- entry metadata such as source mode / target language / ingest mode is persisted

Current stop conditions:

- source missing
- unsupported source input
- provider/probe failure for link ingest

### 3.2 Parse

Goal:

- establish source-ready parse truth for the task

Operator expectation:

- link ingest should validate and normalize the upstream source
- local upload should use existing raw video as source-ready input and must not require link validation

Truth outputs:

- parse success/failure recorded
- source metadata and raw artifact references available for downstream steps

Current stop conditions:

- parse provider error
- source not reachable
- local source missing raw artifact

### 3.3 Adapt

Goal:

- extract source subtitle lane
- generate / edit authoritative target subtitle lane
- resolve voice profile and audio config

Operator actions:

- inspect source/target subtitles
- edit target subtitle if needed
- choose dub voice
- adjust dub speed if needed

Truth outputs:

- authoritative target subtitle artifact
- subtitle freshness inputs such as content hash / updated timestamp
- active dub config inputs

Important rule:

- source subtitle lane remains source truth
- target subtitle lane remains authoritative target truth
- edited target subtitle invalidates stale dub/final outputs

### 3.4 Dub

Goal:

- generate the current authoritative dub for the current target subtitle and current audio config

Current main path:

- standard dub

Operational rule:

- dub is current only when it matches:
  - the authoritative target subtitle
  - the current audio config including voice/speed

Truth outputs:

- dubbed audio artifact
- dub snapshot inputs for freshness comparison

Current stop conditions:

- target subtitle not ready/current
- TTS provider failure
- invalid voice/config

### 3.5 Compose

Goal:

- generate the current final composite using:
  - current raw/source video
  - current authoritative target subtitle
  - current dub or approved no-dub branch
  - current cleanup/layout render policy

Operational rule:

- compose readiness depends on current subtitle + current dub + current render inputs
- stale final output does not count as current-ready

Truth outputs:

- final video artifact
- final freshness / render signature inputs

### 3.6 Review Gate

Goal:

- operator confirms the current final is acceptable for publish

Checks:

- target subtitle correctness/readability
- dub correctness/currentness
- cleanup/layout result
- final download/playback availability

Important rule:

- optional pack/scenes outputs are secondary
- they do not override main deliverable truth

### 3.7 Pack / Publish / Sink

Goal:

- handle optional derivative outputs
- publish accepted final
- sink accepted artifacts according to policy

Operational rule:

- publish depends on ready gate and operator confirmation
- asset sink is downstream of accepted truth, not an execution-layer shortcut

Truth outputs:

- publish status / publish references
- sunk deliverables where applicable
- optional pack artifacts if requested

## 4. Operator Notes

- Hot Follow remains one line even when more than one target-language profile is supported.
- Standard dub remains the operator-default path.
- Optional artifacts such as pack/scenes are secondary outputs, not the main completion definition.

## 5. Engineer Notes

- do not let workers or skills write business truth directly
- do not use UI projection fields as source-of-truth
- board/workbench/publish should agree through ready gate + deliverable truth
- router decomposition must preserve this SOP order, not invent a second orchestration path
