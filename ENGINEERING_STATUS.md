# Engineering Status

## Current Stage

Hot Follow Source Audio Semantics Alignment

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
- current business flow remains stable and non-blocking

## Remaining Structural Risks

- `tasks.py` still structurally large
- compatibility residue still exists
- some scenario-aware façade logic still remains
- historical `mm_*` compatibility naming still exists and is intentionally out of scope for this fix
- source-audio preserve still needs real-material business sampling for mix quality and operator-facing mix review
- remaining Avatar / baseline router-space behavior is separately tracked, not part of Hot Follow closure

## Recommended Next Direction

- keep further Hot Follow fixes narrow and truth-source driven
- defer `mm_*` naming cleanup, translation bridge work, and localization-line expansion to separate scoped PRs
- keep source-audio / dub truth fixes separate from UI redesign or compose ownership redesign
- keep business regression and verification baseline mandatory
- avoid Avatar refactor, baseline rewrite, second-line expansion, or broad platformization by drift
