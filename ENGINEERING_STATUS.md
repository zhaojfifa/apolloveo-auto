# Engineering Status

## Current Stage

Hot Follow Status Truth Binding Alignment

## Current Main Line

- Hot Follow
- first business-validated Skills sample
- target subtitle currentness and source-audio policy truth-source fixes are now closed for the active Hot Follow path

## Current Completion

- Hot Follow Skills MVP v0 closure remains frozen
- Hot Follow cleanup line is now near closure, not fully closed
- Myanmar target subtitles now use the same source-copy / translation-incomplete currentness discipline as Vietnamese
- `preserve original BGM/source audio` is bound into compose without being treated as current TTS dub
- workbench diagnostics and preview binding now distinguish preserved source audio from current TTS voiceover
- Hot Follow dub preview/download/file surfaces now bind to current true TTS voiceover instead of raw audio artifact presence
- Hot Follow dry TTS voiceover now has a dedicated authoritative key for dubbing preview/download/currentness, separated from final BGM/source-audio compose inputs
- Hot Follow dubbing truth now requires the strict dry TTS object shape under `config.tts_voiceover_key`; legacy `mm_audio_key` alone no longer satisfies dub semantics
- Hot Follow empty target subtitle / empty dub input now resolves to explicit `no_dub` skipped semantics instead of a failed TTS attempt
- Hot Follow parse/source helper text is now separated from authoritative target subtitle and dub-input truth
- compose input selection now preserves source audio by using raw video as the carrier when `source_audio_policy=preserve`
- source-audio policy now persists across pipeline config storage, task config, workbench BGM upload, and backend BGM upload defaults
- workbench preview/player binding now uses explicit TTS preview fields instead of legacy voiceover aliases
- Hot Follow board/summary readiness now follows computed ready gate truth instead of raw final/audio/publish compatibility artifacts
- current business flow remains stable and non-blocking
- preserved source-audio bed in final compose no longer inherits a zero BGM mix value as effective mute

## Remaining Structural Risks

- `tasks.py` still structurally large
- compatibility residue still exists
- some scenario-aware façade logic still remains
- historical `mm_*` compatibility naming still exists and is intentionally out of scope for this fix
- source-audio preserve still needs real-material business sampling for mix quality and operator-facing mix review
- legacy Hot Follow tasks without the dedicated dry TTS key must be re-dubbed before exposing dub preview/download/currentness
- Hot Follow source-audio asset-flow fix sequence is complete through status truth binding; compatibility naming cleanup remains separate
- remaining Avatar / baseline router-space behavior is separately tracked, not part of Hot Follow closure

## Recommended Next Direction

- keep further Hot Follow fixes narrow and truth-source driven
- defer `mm_*` naming cleanup, translation bridge work, and localization-line expansion to separate scoped PRs
- keep source-audio / dub truth fixes separate from UI redesign or compose ownership redesign
- keep business regression and verification baseline mandatory
- avoid Avatar refactor, baseline rewrite, second-line expansion, or broad platformization by drift
