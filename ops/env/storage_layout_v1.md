# ApolloVeo W2 Admission — Storage Layout v1

- Wave: ApolloVeo 2.0 W2 Admission Preparation — Phase B (row O-02)
- Authority:
  - `docs/architecture/ApolloVeo_2.0_W2_Admission_Preparation_Wave_指挥单_v1.md` §4 Phase B
  - `docs/donor/swiftcraft_donor_boundary_v1.md` §3.7
  - `docs/donor/swiftcraft_capability_mapping_v1.md` row O-02
- Companion: `ops/env/env_matrix_v1.md` §2.2

## 1. Backend split

- **R2 (Cloudflare R2 over the S3 protocol)** — primary object store for
  signed-URL artifacts and packs.
- **Local filesystem** — used when `FEATURE_STORAGE_ENABLED=false` and in
  local dev / unit tests.
- **S3 (vendor)** — not currently used in production; the alias key family
  (`R2_*`) is the canonical surface, and the R2 endpoint is the only deployed
  target. No vendor-S3 keys are pinned in the env matrix.

## 2. Path conventions (canonical)

| Concern | Local | Render / Production |
|---|---|---|
| pipeline scratch | `$VIDEO_WORKSPACE` (default `./video_workspace`) | `/opt/render/project/src/video_workspace` |
| persistent disk root | n/a | `$DISK_ROOT` (default `/var/data`) |
| model cache (HF) | per-engineer `$HF_HOME` | `$DISK_ROOT/cache/hf` |
| xdg cache | per-engineer | `$DISK_ROOT/cache/xdg` |
| whisper warmup sentinel | n/a | `$DISK_ROOT/models/.faster_whisper_<model>_ready` |
| pack output | `./deliver/packs` (configurable via `V17_PACKS_DIR`) | `$V17_PACKS_DIR` |
| signed-URL public base | n/a | `$R2_PUBLIC_BASE_URL` |

## 3. Object-key conventions (R2)

These conventions are pattern-only; they are not contract-bound and may be
refined before W2.1. They are recorded here so providers absorbed in W2 do
not invent new schemes ad-hoc:

- All keys live under a single bucket `$R2_BUCKET_NAME`.
- Per-task artifacts use a `tasks/<task_id>/...` prefix.
- Per-line packs use a `packs/<line_id>/<pack_version>/...` prefix.
- Provider-cached intermediate artifacts (when added in W2.1+) MUST use a
  `providers/<provider_id>/...` prefix and MUST NOT collide with `tasks/`
  or `packs/`.

## 4. Region / endpoint

- `R2_ENDPOINT` is the S3-protocol endpoint URL for the R2 bucket.
- `R2_REGION` defaults to `auto` (R2 ignores the region in most calls;
  the value is only meaningful for SDK-level defaulting).
- No multi-region replication is assumed in this wave.

## 5. Degraded behaviour

If any of the four R2 secrets is missing
(`R2_ENDPOINT`, `R2_BUCKET_NAME`, `R2_ACCESS_KEY`, `R2_SECRET_KEY`), the
storage feature is reported disabled at startup
(`gateway/app/main.py:248-251`) and the local filesystem path is used.
This is the only sanctioned degraded path — providers MUST NOT silently
skip writes.

## 6. Out of scope for this wave

- No bucket creation, IAM policy, or rotation runbook changes.
- No multi-region or multi-bucket layout.
- No migration of existing artifacts.
- No vendor-S3 absorption.
