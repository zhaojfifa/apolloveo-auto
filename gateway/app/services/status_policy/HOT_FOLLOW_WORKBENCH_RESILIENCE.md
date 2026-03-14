Hot Follow workbench resilience rule

- Stable legacy payload is primary. Existing workbench fields must remain available even when newer presentation helpers fail.
- Presentation aggregation is an optional enhancement layer only.
- Optional derived blocks such as `artifact_facts`, `current_attempt`, and `operator_summary` must degrade to `{}` or `null`, not raise.
- `GET /api/hot_follow/tasks/{task_id}/workbench_hub` must never return HTTP 500 because of presentation-only logic.
- Regression tests must cover optional aggregation failure and still expect HTTP 200 from `workbench_hub`.
