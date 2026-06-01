# Render FFmpeg Build Hotfix

Date: 2026-06-01
Branch: `hotfix/render-ffmpeg-download-guard`
Scope: `scripts/render_build.sh` only (deploy/build hardening). No app code, no schema/contract, no Matrix Script business logic, no Hot Follow / Digital Anchor, no `artifact_storage.py`, no Akool, no UI.

## Symptom

Render build of `main` failed at the static-ffmpeg step (after `pip install` succeeded):

```
[build] downloading ffmpeg static...
100   435  100   435 ...            # only 435 bytes downloaded
[build] extracting ffmpeg...
xz: (stdin): File format not recognized
tar: Child returned status 1
==> Build failed 😞
```

## Root cause

`scripts/render_build.sh` downloaded `ffmpeg-release-amd64-static.tar.xz` from `johnvansickle.com` with `curl -L` (no `-f`, no validation) and piped it straight to `tar -xJf`. From Render's egress that URL returned a **435-byte redirect/error page** (the same URL returns a valid 41 MB archive from other networks — johnvansickle blocks/redirects many datacenter IPs). `tar` then failed on the non-archive, aborting the build under `set -e`.

This is a **build/network issue**, unrelated to PR-A and to the Python pin (PR-188): `pip install` completed; PR-A runtime code never executed.

## Fix

Hardened the ffmpeg step:

1. **Skip** the download entirely if `ffmpeg` + `ffprobe` are already on PATH.
2. Download with `curl -fL --retry 3 --retry-delay 2` to a temp file (fail on HTTP errors; retry transient failures).
3. **Validate size** (> 1 MB) — a 435-byte page is rejected with its first bytes logged.
4. **Validate file type** (`file` → `xz|tar|compress`) when `file` is available.
5. **Extract only after validation**; if `tar` fails, try the next source.
6. **Primary source switched to the BtbN GitHub release** static build (`ffmpeg-master-latest-linux64-gpl.tar.xz`) — reliable from datacenter IPs; **fallback** kept as johnvansickle. Either is overridable via `FFMPEG_STATIC_URL`.
7. **Locate binaries anywhere** in the extracted tree (`find … -name ffmpeg/ffprobe`) — BtbN nests them under `<dir>/bin/`, johnvansickle puts them at `<dir>/`.
8. **Fail loudly** with a clear, actionable message (and `exit 2`) if every source fails — never feed an error page to `tar`, never silently ship without ffmpeg.

## Validation

- `bash -n scripts/render_build.sh` → syntax OK.
- Manually confirmed from this environment: the BtbN URL returns a **142 MB** valid `XZ` archive that extracts to `…/bin/ffmpeg` + `…/bin/ffprobe`; the size-guard correctly rejects a simulated small error page before `tar`.
- App-side ffmpeg degradation is already safe: ffmpeg is resolved lazily at runtime (`shutil.which`), app startup does not import it, and the tomato route returns HTTP 503 (never a fake `final.mp4`) if ffmpeg is absent.

## Boundary

Only `scripts/render_build.sh` (+ this doc) changed. No code/schema/contract change; no Hot Follow / Digital Anchor; `artifact_storage.py` untouched; no Akool live; no UI; no Python pin change (PR-188's `runtime.txt` stays).
