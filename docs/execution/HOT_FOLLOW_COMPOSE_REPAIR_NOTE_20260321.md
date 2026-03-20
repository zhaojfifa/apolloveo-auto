## Hot Follow Compose / Final Repair Note (2026-03-21)

### Scope

This patch is the narrow pre-redesign repair for the hot-follow compose/final
state reconciliation bug.

It does **not** introduce a compose-runs persistence model.
It does **not** redesign publish, dubbing, or broader task state architecture.

### Exact Root Cause

The workbench hub mixed three different truths:

1. compose execution truth
   - `compose.last.status`
   - final artifact existence

2. current-final freshness truth
   - whether the latest dub/subtitle revision already matches the latest final

3. compatibility / presentation overlays
   - legacy fields consumed by the workbench UI

The stale/pending bug happened when later layers re-projected current-final
state from a stale pre-normalization composed snapshot, even though:

- compose execution had already succeeded
- final artifact existence was already confirmed

### Narrow Fix Boundary

This repair only does the following:

1. `compute_composed_state(...)`
   - treats missing timestamps as missing, never as "now"
   - only performs timestamp comparisons when source timestamps exist
   - keeps stale only when there is explicit evidence that current dub/subtitle
     inputs are newer than the composed final

2. compose step projection
   - preserves compose execution result as `done`
   - separates "compose executed successfully" from "current final freshness"

3. `get_hot_follow_workbench_hub(...)`
   - recomputes composed state after normalization/backfill
   - rebuilds final-facing fields from the latest recomputed composed snapshot

4. compatibility overlays
   - cannot overwrite authoritative operational fields like:
     - `compose_status`
     - `final_exists`
     - `final_url`
     - `final_video_url`

### Explicit Non-Goals

- no compose-runs model yet
- no publish redesign
- no broad router refactor
- no UI-only workaround
