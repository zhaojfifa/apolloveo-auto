# Factory Workbench Mapping v1

Date: 2026-04-25
Status: Factory closeout baseline above verified Hot Follow

## Purpose

Define the factory-generic operator surface zones using the four-layer state
model, with Hot Follow as the verified reference mapping.

This document does not redesign UI. It freezes what each zone is allowed to
show from L2 truth, L3 gate/currentness, and L4 projection.

## Generic Workbench Zones

The factory-generic operator surface contains seven zones:

1. intake / source
2. parse / source understanding
3. subtitle authority
4. audio plan / dubbing
5. compose / final assembly
6. delivery / publish
7. advisory / operator actions

## Zone Mapping Rules

- L2 shows artifact existence, evidence, and accepted factual objects
- L3 shows currentness, selected route, blocking reasons, and ready-gate inputs
- L4 shows summaries, labels, aliases, and operator-safe surface wording only
- operator actions are explicit user actions
- automatic transitions come from execution and status-policy movement, not
  from workbench code

## Zone Table

| Zone | Show from L2 truth | Show from L3 gate/currentness | L4 projection only | Operator actions | Automatic transitions |
| --- | --- | --- | --- | --- | --- |
| Intake / source | normalized source asset, source locator, intake completeness | intake validation outcome, source-mode legality | input summary cards, intake labels | create task, retry ingest, adjust allowed overrides | source materialization, validation acceptance |
| Parse / source understanding | parse outputs, source text, structure evidence, content-mode probes | parse readiness for downstream planners, structure risk gating | parse summary rows, source-understanding labels | retry parse, inspect source evidence | parse step progression |
| Subtitle authority | authoritative target subtitle artifact, editable copy, helper side-channel facts | subtitle currentness, authoritative-source truth, missing-authority reasons | subtitle section wording, helper warning presentation | save subtitle, retry translation, manual subtitle intervention | subtitle save acceptance, helper completion |
| Audio plan / dubbing | audio artifact facts, voice plan inputs, preserved-bed facts | selected route, audio readiness, dub currentness, route legality | audio summary labels, preview aliases, route guidance text | select voice/provider, retry dub, inspect audio blocking | dub step progression, route re-evaluation |
| Compose / final assembly | current final artifact, historical final artifact, optional scene-pack artifacts | compose readiness, route allowance, requires-redub/recompose, final freshness | compose CTA state, pipeline summary wording | trigger compose, retry compose, inspect compose block | compose step progression, freshness recalculation |
| Delivery / publish | accepted deliverables, current-vs-historical delivery split | publish-ready, confirmation requirement, optional derivative non-blocking status | publish cards, delivery-center labels, download groupings | publish confirm, export, inspect historical output | publish step progression |
| Advisory / operator actions | none beyond evidence references | blocking reasons, retryable classes, route/action eligibility | operator summary, advisory messages, CTA hints | retry, override, continue QA, publish confirm | advisory recalculates when L2/L3 changes |

## Hot Follow Reference Mapping

### Intake / Source Zone

Hot Follow shows:

- source URL or uploaded raw artifact
- target language and operator metadata
- one normalized source-entry mode

It does not use intake summaries as delivery truth.

### Parse / Source Understanding Zone

Hot Follow shows:

- parsed source text
- normalized source text
- speech/text-density evidence
- content mode and source-audio semantics

These are structure facts and summaries only, not publish or dub truth.

### Subtitle Authority Zone

Hot Follow shows:

- authoritative target subtitle artifact
- current editable subtitle text
- `target_subtitle_current`
- `target_subtitle_authoritative_source`
- helper `output_state` and `provider_health`

Helper stays side-channel. Missing-authority wording must clear once
authoritative subtitle truth is current.

### Audio Plan / Dubbing Zone

Hot Follow shows:

- requested voice
- resolved voice
- provider
- selected compose route
- `audio_ready`
- `dub_current`
- no-dub/no-TTS legality only when explicit boundary facts exist

Retryable TTS/provider failure remains a route-state/advisory issue, not a
terminal no-TTS surface rewrite.

### Compose / Final Assembly Zone

Hot Follow shows:

- current final
- historical final
- compose readiness
- final freshness
- optional scene-pack residue

Scene-pack pending remains advisory once current final/publish truth is ready.

### Delivery / Publish Zone

Hot Follow shows:

- raw
- origin subtitle
- target subtitle
- audio
- final
- optional pack/scenes

Current fresh final plus ready gate dominates this zone.

### Advisory / Operator Actions Zone

Hot Follow shows:

- operator summary
- ready-gate blocking reasons
- route-safe retry or continue actions
- publish confirmation actions

This zone explains truth but does not write it.

## Surface Discipline

- workbench, publish, and task-detail must consume the same L2/L3-derived
  authoritative projection
- generic zones may vary visually by line, but not by truth ownership
- no zone may invent a second subtitle/audio/final readiness path

## Onboarding Rule

A future line is only ready for contract-first onboarding when it can fill all
seven zones with:

- L2 truth fields
- L3 current/gate fields
- L4 projection-only fields
- explicit operator actions
- explicit automatic transitions
