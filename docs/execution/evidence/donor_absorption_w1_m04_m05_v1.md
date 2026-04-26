# Donor Absorption W1 — M-04 + M-05 Evidence v1

Date: 2026-04-26
Status: First absorption PR of P2 Wave 1 (Media helpers, pure-utility subset)
Authority:
- `docs/donor/swiftcraft_donor_boundary_v1.md` §3.1
- `docs/donor/swiftcraft_capability_mapping_v1.md` rows M-04, M-05
- `docs/adr/ADR-donor-swiftcraft-capability-only.md`

## Donor commit pin (W1)

- Repo: `https://github.com/zhaojfifa/swiftcraft` (local clone `/Users/tylerzhao/Code/swiftcraft`)
- Short SHA: `62b6da0`
- Full SHA: `62b6da0f6e23d83ee89564ae404375a1ad209432`
- Recorded by: zhaojfifa
- Recorded in mapping doc §0: yes (W1 row updated)

## Rows absorbed in this PR

| Row | Donor path | Apollo target | Strategy | Status (after PR) |
|---|---|---|---|---|
| M-04 | `backend/app/utils/serialize.py` | `gateway/app/services/media/serialize.py` | Wrap (verbatim) | In progress |
| M-05 | `backend/app/utils/zh_normalize.py` | `gateway/app/services/media/zh_normalize.py` | Wrap (verbatim) | In progress |

Status will move from `In progress` → `Absorbed` in the follow-up PR after merge,
per mapping doc §3 lifecycle.

## Files changed

- `gateway/app/services/media/serialize.py` (new)
- `gateway/app/services/media/zh_normalize.py` (new)
- `tests/services/__init__.py` (new)
- `tests/services/media/__init__.py` (new)
- `tests/services/media/test_serialize.py` (new)
- `tests/services/media/test_zh_normalize_guard_compat.py` (new)
- `docs/donor/swiftcraft_capability_mapping_v1.md` (W1 SHA pin + M-04/M-05 status)
- `docs/execution/evidence/donor_absorption_w1_m04_m05_v1.md` (this file)

## Behavior delta vs donor source

None. Both files are byte-equivalent to donor at SHA `62b6da0` for function
bodies. Only additions are:

- Module docstring with attribution + mapping row id + donor SHA pin
- No `swiftcraft.*` imports were present in donor; nothing to strip

## Test evidence

```
$ python3 -m pytest tests/services/media/ -v
============================= test session starts ==============================
collected 11 items

tests/services/media/test_serialize.py::test_dict_with_model_dump_takes_precedence PASSED
tests/services/media/test_serialize.py::test_dict_method_used_when_no_model_dump PASSED
tests/services/media/test_serialize.py::test_dataclass_via_asdict PASSED
tests/services/media/test_serialize.py::test_plain_object_via_dunder_dict PASSED
tests/services/media/test_serialize.py::test_unsupported_type_raises_type_error PASSED
tests/services/media/test_zh_normalize_guard_compat.py::test_empty_input_returns_empty PASSED
tests/services/media/test_zh_normalize_guard_compat.py::test_trad_to_simp_mapping_applied PASSED
tests/services/media/test_zh_normalize_guard_compat.py::test_inch_and_cm_normalization PASSED
tests/services/media/test_zh_normalize_guard_compat.py::test_fullwidth_punct_to_halfwidth_with_trailing_space PASSED
tests/services/media/test_zh_normalize_guard_compat.py::test_normalize_does_not_strip_cjk_so_guard_still_detects_it PASSED
tests/services/media/test_zh_normalize_guard_compat.py::test_normalize_preserves_srt_cue_index_lines_as_pure_text PASSED

============================== 11 passed in 0.05s ==============================
```

Guard-compat (M-05 acceptance) is asserted by
`test_normalize_does_not_strip_cjk_so_guard_still_detects_it`: it pipes a CJK
input through `normalize_zh_text` then through Apollo's existing
`gateway.app.services.dub_text_guard.clean_and_analyze_dub_text` with
`target_lang="my"`, and pins that the guard still flags the line as CJK
(`cjk_lines` non-empty, `warning` populated). If a future zh_normalize change
were to strip CJK codepoints, this test fails before the dub pipeline ships
wrong-language audio.

## Forbidden list compliance

- No `swiftcraft.*` import added (verified: donor source has none either).
- No provider client absorbed (boundary §3.3 — out of scope for this PR).
- No prompt-builder absorbed (boundary §3.5 — out of scope for this PR).
- No M-01 / M-02 / M-03 changes (those rows remain `Not started`; require
  contract-shape alignment in a follow-up PR).
- No truth writes added; both files are pure functions.

## Open follow-ups (not in this PR)

- Move M-04 / M-05 rows from `In progress` → `Absorbed` after this PR merges.
- Open a separate `tests/guardrails/` host directory if/when the
  front-end-leak red-line tests referenced by P2 directives are formalized.
  (No such directory exists in repo today; the M-05 guard-compat test lives
  under `tests/services/media/` per current convention.)
- M-01 / M-02 / M-03 absorption requires `factory_audio_plan` /
  `factory_language_plan` / `factory_scene_plan` shape alignment; out of scope.
