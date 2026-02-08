# SKILLS_CATALOG (v1.9)

> Scope: configuration-driven policies that govern language/subtitles/dubbing/fallback behavior.  
> Goal: reduce hard-coded branching in steps; enable adding new languages/providers without rewriting workflows.

## 1. Skill Types

### 1.1 Language Policy
Defines language handling for:
- content_lang (source/target)
- ui_lang (UI rendering language)
- locale-specific formatting

Fields:
- supported_content_langs
- supported_ui_langs
- default_ui_lang
- normalization rules (e.g., "MM" -> "mm")

### 1.2 Subtitles Policy
Defines subtitles generation rules:
- modes: whisper+gemini, gemini_only, whisper_only, ...
- retry policy (max retries, backoff)
- failure classification
- output formats (srt, txt)

Fields:
- subtitles_mode
- provider_order (e.g., whisper -> gemini refine)
- timeout_strategy
- output_contract (origin_srt_path, mm_srt_path, mm_txt_path)

### 1.3 Dubbing Policy
Defines dubbing rules:
- mode: uto-fallback, edge, lovo, ...
- fallback matrix (provider order)
- no_dub semantics (skip reasons)

Fields:
- dub_mode
- provider_order
- voice_preset mapping
- output_contract (mm_audio_path/mm_audio_key)

### 1.4 Fallback Matrix (cross-policy)
A unified matrix that maps:
- (scenario kind, step, primary provider) -> fallback provider(s)
- failure reason -> retryable vs terminal

---

## 2. Configuration Principle

- Skills must be **data-driven** (env/config) where possible.
- Steps should request capabilities via skill config, not hard-code providers.
- Policy dispatch by kind may override defaults for a scenario.

---

## 3. Minimal JSON-ish Shape (conceptual)

`json
{
  "language": {
    "supported_content_langs": ["mm", "th", "vi", "id", "ms"],
    "supported_ui_langs": ["zh", "en"],
    "default_ui_lang": "zh"
  },
  "subtitles": {
    "mode": "whisper+gemini",
    "providers": ["whisper", "gemini"],
    "timeouts": { "whisper": "dynamic", "gemini": "fixed" }
  },
  "dubbing": {
    "mode": "auto-fallback",
    "providers": ["edge", "lovo"],
    "voices": { "mm": "default_mm" }
  },
  "fallback": {
    "subtitles_failed": { "retry": true, "fallback_to": ["whisper_only"] },
    "dub_failed": { "retry": true, "fallback_to": ["edge"] }
  }
}
`

4. Implementation Notes (v1.9)

Skills are consumed by steps via pipeline_config.

Defaults exist to keep baseline stable.

Scenario-specific adjustments happen in StatusPolicy / Scene SOP, not in routers.
