# Matrix Script Phase 3 — PR-4R Minimal Result Loop (Execution Note)

Date: 2026-05-31
Branch: `phase3/pr4r-matrix-script-minimal-result-loop`
Base: `main` @ `d80bdfe541309fc4807a0de6ce7268afe4ce1188`
Status: First **result-oriented** Matrix Script loop. Produces a real, playable local `final.mp4` from a script/outline. **No Akool, no provider URL, no artifact-storage write, no UI/route change.**

---

## Reading Declaration

### Root indexes / governance
- `README.md`, `ENGINEERING_CONSTRAINTS_INDEX.md`, `docs/README.md`, `docs/ENGINEERING_INDEX.md`
- `CLAUDE.md`, `PROJECT_RULES.md`, `ENGINEERING_RULES.md`, `CURRENT_ENGINEERING_FOCUS.md`, `ENGINEERING_STATUS.md`

### Task-specific authority
- `docs/design/matrix_script_phase3_akool_real_generation_plan_v1.md` §5 (first real controlled route) / §6 (artifact + manifest model; provider URL never deliverable)
- `docs/execution/MATRIX_SCRIPT_PHASE3_PR2_SHOT_PLAN_SKELETON.md`, `MATRIX_SCRIPT_PHASE3_PR3_SCENE_ARTIFACT_MANIFEST_SKELETON.md`
- Reused: `shot_plan.py`, `shot_plan_builder.py`, `scene_artifacts.py`, `scene_manifest.py`

---

## What was added

| File | Purpose |
| --- | --- |
| `gateway/app/services/matrix_script/simple_scene_renderer.py` | Minimal FFmpeg primitives: `render_color_scene_clip` (lavfi color card), `generate_silent_audio` (anullsrc), `assemble_final_video` (concat + mux), `probe_duration_seconds` (ffprobe), `ffmpeg_available`, `FFmpegUnavailableError`. |
| `gateway/app/services/matrix_script/minimal_result_loop.py` | Orchestrator `run_minimal_result_loop(outline, output_dir, ...)`: outline → shot_plan (PR-2) → scene slots (PR-3) → scene clips → silent audio → `subtitles.srt` → assembled `final.mp4` → `manifest.json`. Pure helpers `build_srt`, `build_manifest_dict`. |
| `gateway/app/services/tests/test_matrix_script_minimal_result_loop.py` | Two-tier tests (logic always-run; real render gated on ffmpeg). |
| `docs/execution/MATRIX_SCRIPT_PHASE3_PR4R_MINIMAL_RESULT_LOOP.md` | This note. |

### Output tree (written to a caller-supplied / test temp directory)
```
matrix_script_result/
  shots/scene_001.mp4 … scene_00N.mp4
  audio/narration.wav            (silent fallback)
  subtitles/subtitles.srt
  final/final.mp4
  manifest.json
```

### Strategy markers on the manifest (binding)
- `scene_strategy = ffmpeg_color_card`
- `audio_strategy = silent_fallback`
- `generation_provider = none`
- `final_video_path` + `scene_clip_paths` are **local relative paths**, never an artifact key / provider URL / download URL.

---

## Validation evidence

Environment: ffmpeg 8.1.1 / ffprobe present (installed locally for this run). On a host without ffmpeg the real-render tests **skip** with a clear reason — a fake `final.mp4` is never produced.

- `python3.11 -m pytest gateway/app/services/tests/test_matrix_script_minimal_result_loop.py` → **10 passed** (8 logic + 2 real-render). (Without ffmpeg: 8 passed, 2 skipped.)
- `python3.11 -m pytest .../test_matrix_script_shot_plan.py .../test_matrix_script_scene_artifacts.py` → **34 passed** (PR-2/PR-3 regression).
- `py_compile` both modules → OK; `git diff --check` → clean.

Real artifact proof (one demo run, 5 shots, target 8.0s):
```
shots/scene_001.mp4   2947 bytes      audio/narration.wav  705678 bytes
shots/scene_002.mp4   2947 bytes      subtitles/subtitles.srt 259 bytes
shots/scene_003.mp4   2947 bytes      final/final.mp4      14683 bytes
shots/scene_004.mp4   2947 bytes      manifest.json          655 bytes
shots/scene_005.mp4   2948 bytes
ffprobe(final/final.mp4) duration = 8.0 s   generation_provider = none
```

---

## What was explicitly NOT added (PR-4R forbidden scope)

No Akool live API / adapter import; no webhook / polling / provider async job store; no provider URL (`generation_provider = none`); no `artifact_storage` / R2 write (output only to the caller's temp dir); no real publish logic; no UI / template / Delivery Center runtime change; no schema / packet / contract change (`envelope.py` untouched); no Hot Follow / Digital Anchor change; debt branch untouched. When ffmpeg is missing the loop raises `FFmpegUnavailableError` — never a fake `final.mp4`.

Real generation via Akool (and copy-into-Apollo artifact storage) remains gated behind the Capability Expansion Gate Wave (W2.3) per PR-0 §2 / §10. This loop is the local, provider-free baseline that proves the assembly path end to end.
