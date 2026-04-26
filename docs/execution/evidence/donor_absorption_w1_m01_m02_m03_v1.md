# Donor Absorption W1 — M-01 + M-02 + M-03 Evidence v1

Date: 2026-04-26
Status: Closing absorption PR of P2 Wave 1 (Media helpers, contract-bound subset)
Authority:
- `docs/donor/swiftcraft_donor_boundary_v1.md` §3.1
- `docs/donor/swiftcraft_capability_mapping_v1.md` rows M-01, M-02, M-03
- `docs/adr/ADR-donor-swiftcraft-capability-only.md`

## Donor commit pin (W1)

- Repo: `https://github.com/zhaojfifa/swiftcraft`
- Short SHA: `62b6da0` (same pin as M-04/M-05; W1 wave is single-pin per §0)
- Recorded in mapping doc §0: yes (W1 row already present)

## Rows absorbed in this PR

| Row | Donor path | Apollo target | Strategy | Status (after merge) |
|---|---|---|---|---|
| M-01 | `backend/app/utils/ffmpeg_localization.py` | `gateway/app/services/media/ffmpeg_localization.py` | Wrap (verbatim) | Absorbed |
| M-02 | `backend/app/utils/media.py` | `gateway/app/services/media/media_helpers.py` | Wrap + sever | Absorbed |
| M-03 | `backend/app/utils/subtitle_builder.py` | `gateway/app/services/media/subtitle_builder.py` | Wrap (rebrand) | Absorbed |

## Files landed (commit `09ec391`)

- `gateway/app/services/media/ffmpeg_localization.py` (new, M-01)
- `gateway/app/services/media/media_helpers.py` (new, M-02)
- `gateway/app/services/media/subtitle_builder.py` (new, M-03)
- `tests/services/media/test_ffmpeg_localization.py` (new)
- `tests/services/media/test_media_helpers_donor.py` (new — includes AST severance assertion)
- `tests/services/media/test_subtitle_builder.py` (new)
- `docs/donor/swiftcraft_capability_mapping_v1.md` (M-01/M-02/M-03 → Absorbed)

## Behavior delta vs donor source

- **M-01** — byte-equivalent function bodies; only attribution docstring added. No donor cross-imports existed.
- **M-02** — donor `from app.models.task import InputMetadata` severed and replaced
  with a local `MediaProbeResult` dataclass (Wave-1 red-line: no SwiftCraft task model
  may enter Apollo). Function behavior preserved. The new file is a distinct surface
  from the pre-existing `gateway/app/services/media_helpers.py` (BGM/URL probe);
  no callers were rewired in this PR.
- **M-03** — `parents[3] → parents[4]` for Apollo layout depth; default ASS title
  rebranded from donor brand to ApolloVeo. Plain-text SRT path preserved (Hot
  Follow frozen rule). No language-plan logic invented.

## Severance assertion (M-02)

`tests/services/media/test_media_helpers_donor.py::test_no_donor_task_model_leak`
performs both a runtime and an AST check:

- `assert not hasattr(mh, "InputMetadata")`
- `assert "app.models.task" not in sys.modules`
- AST scan of the source file: no `app.models` import node present

If a future edit reintroduces the donor task-model coupling, this test fails
before merge.

## Test evidence

```
$ python3 -m pytest tests/services/media/ -q
...........................................                              [100%]
43 passed in 0.11s

$ python3 -m pytest tests/ -q
........................................................................ [ 91%]
.......                                                                  [100%]
79 passed in 0.12s
```

Suite covers M-01..M-05 plus pre-existing packet-validator contracts. No
regressions vs the M-04/M-05 baseline (+32 cases for M-01/M-02/M-03).

## Forbidden list compliance

- No `swiftcraft.*` / `app.models.*` import in absorbed files (grep + AST verified).
- No provider client touched (boundary §3.3 — W2 territory).
- No prompt-builder touched (boundary §3.5 — W5 territory).
- No engine / orchestration code touched (boundary §4.2 forbidden list).
- No truth writes; no router rewiring; no auto-promote paths.

## W1 closure

This PR is the last open absorption item for Wave 1. Combined with merged
commit `dcb49ca` (M-04/M-05), all five Media-helper rows are now `Absorbed`.
The W1 wave is closed; W2 (ASR/translate/TTS) is gated by the prerequisites
listed in `docs/reviews/W1_COMPLETION_REVIEW_v1.md` §3.
