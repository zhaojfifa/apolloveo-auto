# Factory Line Template Design v1

Date: 2026-04-25
Status: Factory closeout baseline above verified Hot Follow

## Purpose

Define the factory-level production-line template that future lines must fit
before runtime onboarding is allowed.

This document uses verified Hot Follow runtime truth as the reference line. It
does not authorize a new line implementation.

## What A Production Line Template Is

A production line template is the factory-generic assembly model that defines:

- which contract objects a line must provide
- which four-layer state boundaries the line must obey
- which runtime references are required before execution is allowed
- which surfaces must consume shared authoritative truth

It is the template for line design, not a router/runtime implementation.

## Fixed Across Lines

The following parts stay fixed across lines:

- Layer 0 to Layer 3 architecture order
- four-layer state discipline
- single-owner truth discipline
- ready-gate and delivery truth precedence rules
- shared workbench/delivery-center truth path requirements
- factory contract-object families:
  - input
  - content structure
  - scene plan
  - audio plan
  - language plan
  - delivery

## What Varies By Line

The following parts are line-specific:

- supported source entry modes
- target result type
- language profiles
- audio route policies
- scene-pack relevance
- deliverable profile
- worker profile
- skills bundle
- line-specific ready-gate rules
- line-specific advisory mappings

## Template Layers

### Template Layer A — Factory Contract Objects

Every line must provide or bind:

- `factory_input_contract_v1`
- `factory_content_structure_contract_v1`
- `factory_scene_plan_contract_v1`
- `factory_audio_plan_contract_v1`
- `factory_language_plan_contract_v1`
- `factory_delivery_contract_v1`

### Template Layer B — Line Contract Binding

Every line must provide:

- line identity
- task kind
- target result type
- input contract binding
- deliverable profile binding
- worker/skills/sink bindings
- ready-gate reference
- status policy reference

### Template Layer C — State And Projection Binding

Every line must prove:

- L1/L2/L3/L4 separation
- current-vs-historical output discipline
- ready-gate derivation from authoritative truth
- workbench and delivery-center truth-path alignment

## Hot Follow Reference Mapping

Hot Follow is the first verified reference line for the template. It maps into
the factory objects as follows.

### A. Factory Input Contract

| Factory object field | Hot Follow binding |
| --- | --- |
| intake source type | link ingest or local upload into one `hot_follow` task kind |
| platform/source locator | source URL, upload path, raw artifact key |
| local upload vs URL | one authoritative source-entry mode only |
| operator-provided overrides | target language, voice/provider choices, subtitle edits, compose overrides |
| language target | `target_lang` / content-language normalization |
| subtitle mode | authoritative target-subtitle required; helper is side-channel only |
| audio policy | preserve-source vs TTS-capable route inputs, not current route truth |

Promote to factory-generic:

- source-entry taxonomy
- normalized source locator envelope
- operator metadata envelope
- language target slot
- subtitle-mode slot
- source-audio policy slot

Keep line-specific:

- Hot Follow source-language restrictions
- Hot Follow local-upload admission rules
- Hot Follow-specific default voice/provider choices

### B. Factory Content Structure Contract

| Factory object field | Hot Follow binding |
| --- | --- |
| source material | raw video artifact and source-media probes |
| parsed source text | parse output, raw source text, normalized source text |
| target subtitle | authoritative target subtitle artifact and edited text |
| helper side-channel output | helper translated text, helper status, helper provider health |
| current editable text | operator-facing edited subtitle text |
| current authoritative copy | `target_subtitle_current=true` plus authoritative subtitle artifact |

Promote to factory-generic:

- source material summary
- parsed source text slots
- authoritative target-subtitle object
- helper side-channel object
- editable-copy vs authoritative-copy split

Keep line-specific:

- exact subtitle filename conventions such as `mm_srt_path`
- Hot Follow-only compatibility aliases

### C. Factory Audio Plan Contract

| Factory object field | Hot Follow binding |
| --- | --- |
| voice plan | requested voice, resolved voice, provider |
| dub provider | provider binding and provider health for current TTS path |
| source-audio policy | preserve-source, BGM, or TTS-expected route legality |
| preserved audio bed | source-audio lane / preserved-bed facts |
| TTS artifact | current voiceover artifact, provider output, preview URL |
| current dub truth | `audio_ready`, `audio_ready_reason`, `dub_current`, `dub_current_reason`, selected route |

Promote to factory-generic:

- intended route vs current route split
- voice-plan object
- provider binding object
- preserved-audio-bed slot
- TTS artifact slot
- current dub truth fields

Keep line-specific:

- exact route precedence
- exact no-TTS/no-dub allowances
- provider catalog and voice catalog

### D. Factory Scene Plan Contract

Hot Follow binds scene planning as minimal / optional / deferred.

- scene-pack and scenes outputs are optional secondary derivatives
- scene-plan absence does not block current subtitle/audio/final truth
- scene-pack residue remains advisory after final-ready / publish-ready truth

Promote to factory-generic:

- optional scene-plan object family
- required-vs-optional derivative distinction

Keep line-specific:

- whether a line uses real scene planning at all
- scene-pack validation thresholds

### E. Factory Delivery Contract

| Delivery object field | Hot Follow binding |
| --- | --- |
| raw | raw/source video artifact |
| origin subtitle | origin subtitle artifact |
| target subtitle | authoritative target subtitle artifact |
| audio | current dubbed audio / preview artifact |
| final | current fresh final deliverable |
| pack/scenes | optional secondary outputs only |

Promote to factory-generic:

- current vs historical delivery split
- primary vs optional derivative precedence
- publishability from ready-gate plus current delivery truth

Keep line-specific:

- exact filenames and sink/export policies
- line-specific publish confirmation hooks

## Mandatory Vs Optional Objects For New Lines

Mandatory before runtime onboarding:

- input contract binding
- content structure binding
- language plan binding
- audio plan binding
- delivery contract binding
- line contract with ready-gate, projection-rules, and status-policy refs

Optional only when the line actually uses them:

- scene plan binding
- scene-pack derivative profile
- line-specific advisory families beyond the shared operator-action envelope

## How Hot Follow Maps Into The Template

Hot Follow already supplies the first accepted sample for:

- a concrete line contract
- four-layer state separation
- current-vs-historical final distinction
- route-aware audio/language logic
- shared workbench/publish truth discipline
- optional scene-pack non-blocking delivery semantics

What Hot Follow still does not authorize:

- copying its runtime directly into a second line
- using its router/service residue as the line-template standard

## New-Line Checklist

Every new line must fill this checklist before runtime onboarding:

1. input contract binding
2. content structure binding
3. subtitle authority policy
4. language plan binding
5. audio plan policy
6. compose route policy
7. deliverable profile
8. ready-gate binding
9. projection-rules binding
10. forbidden-invariants binding
11. worker/skills/sink bindings
12. current-vs-historical delivery rule
13. workbench/delivery-center truth-path proof

## Design Rule

The next engineering layer after verified Hot Follow is contract-object design,
not scenario runtime implementation.

That means:

- create/edit contract objects first
- bind them into line templates second
- permit runtime onboarding only after the gate is explicitly lifted

## Non-Scope

- no new runtime line
- no scenario execution logic
- no multi-role harness
- no reopening Hot Follow internals without a new acceptance regression
