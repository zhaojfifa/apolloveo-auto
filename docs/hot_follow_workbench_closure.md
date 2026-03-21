# Hot Follow Workbench Closure

Date: 2026-03-21

## What Was Fixed

1. Input Config source link is now editable inside Hot Follow Workbench.
2. `final` and `historical_final` are no longer mirrored by default when they point to the same current healthy output.
3. Existing Save Subtitle -> Re-dub -> Re-compose closure behavior remains intact.

## Final Business Closure

- Operators can update `source_url` in the task workbench without leaving the page.
- Editing `source_url` updates task metadata only.
- Editing `source_url` does **not** invalidate subtitle/audio/compose freshness and does not force re-compose.
- `final` now represents only the current effective final output.
- `historical_final` is only exposed as fallback/reference when current final is not available/fresh.

## Current Object Model

- `final`
  - Current effective final only.
  - Requires freshness checks to pass.
  - Drives current final URL exposure and compose-ready gating.

- `historical_final`
  - Fallback/reference final only.
  - Exposed when a physically existing final is not current-fresh (for example stale-after-subtitle/stale-after-dub).
  - Not duplicated when current final is already healthy and current.

- `artifact_facts`
  - Physical existence layer.
  - Keeps visibility of available artifacts even when current final is stale.

## Current State Model

- Save Subtitle
  - Updates authoritative subtitle revision.
  - Marks current final stale when needed.

- Re-dub
  - Uses authoritative subtitle.
  - Updates current dub revision and invalidates stale final as needed.

- Re-compose
  - Uses authoritative subtitle + current dub + compose config.
  - Promotes fresh current final on success.
  - Keeps historical fallback semantics if current compose is stale/unavailable.

- Source URL edit
  - `PATCH /api/hot_follow/tasks/{task_id}/source_url`
  - Metadata-only update, no freshness side effects.

## Optional Future Optimization

1. Add i18n keys for the new source-link editing labels/messages in all locales.
2. Add browser-level UI automation coverage for source-link edit mode transitions.
3. If object-versioning is enabled in storage, persist explicit historical artifact ids for multi-version historical browsing.
