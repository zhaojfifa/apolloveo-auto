# Factory Runtime Boundary Design v1

Date: 2026-04-25
Status: Factory closeout baseline above verified Hot Follow

## Purpose

Freeze the factory runtime boundary set that Hot Follow now binds to as one
concrete line implementation.

This document exists so future lines plug into stable boundary contracts instead
of extending router or god-file control flow directly.

## Boundary Set

The factory runtime boundary set is:

1. intake / task creation
2. parse
3. subtitle authority
4. audio plan / dub
5. compose
6. publish / delivery
7. projection / workbench

Every line binds to this same set. A line may vary inputs, planners, and route
rules, but it may not skip the separation itself.

## Boundary Rules

- each boundary has one ownership declaration
- each boundary writes only its owned L1/L2 truth
- L3 is derived by status-policy / route-resolution consumers, not router-local
  branches
- L4 is projection only
- line-specific adapters are allowed only at declared adapter points
- no future line should need to extend `tasks.py` or `hot_follow_api.py`
  directly to add business rules

## Boundary Table

| Boundary | Ownership | Inputs | Outputs | Write authority | Line-specific adapters | State layer |
| --- | --- | --- | --- | --- | --- | --- |
| Intake / task creation | factory input normalization plus line input binding | raw request, line contract, source locator, operator metadata | normalized input object, initial ingest facts, task row seed | task creation path only | yes, for source-mode normalization and line validation | L2 preconditions only |
| Parse | parse service / parser worker binding | normalized input object, source artifact, line parse policy | parse step status, parsed source text, structure evidence | parse execution path only | yes, parser/provider adapters | L1 writes parse status, L2 writes parse evidence |
| Subtitle authority | subtitle service plus language-plan binding | parse evidence, authoritative target-subtitle save path, helper side-channel results | authoritative target subtitle facts, helper side-channel facts | subtitle/service acceptance path only | yes, line subtitle authority adapters | L1 subtitle status, L2 subtitle facts, helper side-channel facts |
| Audio plan / dub | audio-plan binding plus dub execution path | language plan, content structure, voice plan, source-audio policy | audio plan, current audio artifact facts, dub execution status | dub/service acceptance path only | yes, provider/voice adapters | L1 dub status, L2 audio facts, L3 derives current route/audio readiness |
| Compose | compose planner / renderer binding | current route, subtitle/audio currentness, optional scene plan, delivery profile | current final facts, compose execution status, optional scene derivative facts | compose/service acceptance path only | yes, line compose adapters | L1 compose status, L2 final and scene derivative facts |
| Publish / delivery | delivery profile plus ready-gate consumer | delivery contract, current artifact facts, ready gate, confirmation policy | current/historical delivery object, publish status, derivative visibility | publish/service acceptance path only | yes, line sink/export adapters | L1 publish status, L2 delivery facts, L3 publish-ready derivation |
| Projection / workbench | projection rules plus presenter-safe surface shaping | L2 artifact facts, L3 current-attempt truth, ready gate, operator summary, advisory | workbench, publish, task-detail payloads | none; projection only | yes, line surface shapers after authoritative projection | L4 only |

## Hot Follow Binding

Hot Follow is the first bound reference line for this boundary set.

### Intake / Task Creation

- binds link ingest and local upload into one normalized `hot_follow` task kind
- writes source-entry facts only
- does not decide subtitle/audio/final readiness

### Parse

- produces parse status and parsed source structure/text
- does not claim subtitle authority merely because parse is done

### Subtitle Authority

- authoritative target subtitle is the single mainline subtitle truth
- helper translation is explicit side-channel output only
- subtitle currentness remains L3 derived truth

### Audio Plan / Dub

- intended route and current route stay distinct
- retryable TTS failure remains on the TTS-expected route family unless
  explicit no-TTS boundary facts exist

### Compose

- consumes current subtitle/audio truth and selected route
- scene-pack semantics remain optional derivatives, not mainline truth owners

### Publish / Delivery

- current fresh final plus ready gate determines publishability
- optional pack/scenes residue may remain visible without downgrading publish
  truth

### Projection / Workbench

- consumes one authoritative projection path
- does not create a second route, subtitle, audio, or publish truth path

## Boundary Ownership Summary

- boundary owners write only operational truth and accepted artifact truth
- L3 is owned by route/state policy consumers of L1/L2
- ready gate, operator summary, advisory, and surfaces consume L3 rather than
  re-owning it
- helper/provider evidence is never allowed to become a cross-boundary write
  path into mainline subtitle/audio/final truth

## Onboarding Rule

Before a future line enters runtime onboarding, it must bind each boundary with:

- owner
- declared inputs
- declared outputs
- explicit write authority
- allowed adapter points
- layer classification

If any of these are missing, onboarding remains blocked.
