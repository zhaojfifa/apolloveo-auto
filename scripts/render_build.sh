#!/usr/bin/env bash
set -euo pipefail

echo "[build] python=$(python --version)"
echo "[build] pip=$(python -m pip --version)"

python -m pip install -U pip

echo "[build] installing deps from: gateway/requirements.txt"
python -m pip install -r "gateway/requirements.txt"

# ---- install static ffmpeg (no apt-get) ----
# Hardened: a previous build silently downloaded a 435-byte redirect/error page
# from johnvansickle.com (blocked from Render's egress) and fed it to `tar`,
# failing the build. We now: skip if ffmpeg is already present; download with
# curl -fL + retries to a temp file; validate size + file type; only then
# extract; locate the binaries wherever they land; and fail loudly with a clear
# message if every source fails (never feed an error page to tar).
mkdir -p .render/bin

if command -v ffmpeg >/dev/null 2>&1 && command -v ffprobe >/dev/null 2>&1; then
  echo "[build] ffmpeg/ffprobe already available on PATH; skipping static download"
else
  # Primary: BtbN static build (GitHub release asset — reliable from datacenter
  # IPs, unlike johnvansickle which Render's egress gets blocked/redirected on).
  # Fallback: johnvansickle release. Override either with FFMPEG_STATIC_URL.
  PRIMARY_URL="${FFMPEG_STATIC_URL:-https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz}"
  FALLBACK_URL="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"

  tmp="/tmp/ffmpeg-static.tar.xz"
  extract_dir="/tmp/ffmpeg-extract"
  rm -rf "$extract_dir"; mkdir -p "$extract_dir"

  download_ok=""
  for url in "$PRIMARY_URL" "$FALLBACK_URL"; do
    echo "[build] downloading ffmpeg static from: $url"
    if ! curl -fL --retry 3 --retry-delay 2 -o "$tmp" "$url"; then
      echo "[build] curl failed for: $url"; continue
    fi
    size="$(wc -c < "$tmp" | tr -d ' ')"
    echo "[build] downloaded ${size} bytes"
    if [ "${size:-0}" -lt 1000000 ]; then
      echo "[build] archive too small (${size} bytes) — likely a redirect/error page; first bytes:"
      head -c 300 "$tmp" || true; echo
      continue
    fi
    if command -v file >/dev/null 2>&1 && ! file "$tmp" | grep -qiE 'xz|tar|compress'; then
      echo "[build] unexpected file type: $(file "$tmp")"; continue
    fi
    if ! tar -xJf "$tmp" -C "$extract_dir"; then
      echo "[build] tar extraction failed for: $url"; continue
    fi
    download_ok="yes"; break
  done

  if [ -z "$download_ok" ]; then
    echo "[build] ERROR: ffmpeg static archive download/extraction failed from all sources." >&2
    echo "[build] Set FFMPEG_STATIC_URL to a reachable ffmpeg static .tar.xz and redeploy." >&2
    exit 2
  fi

  # Locate the binaries anywhere in the extracted tree (layout varies by source:
  # BtbN nests them under <dir>/bin/, johnvansickle puts them at <dir>/).
  ff="$(find "$extract_dir" -type f -name ffmpeg | head -n 1)"
  fp="$(find "$extract_dir" -type f -name ffprobe | head -n 1)"
  if [ -z "$ff" ] || [ -z "$fp" ]; then
    echo "[build] ERROR: ffmpeg/ffprobe binaries not found in extracted archive." >&2
    exit 2
  fi
  cp -f "$ff" "$fp" .render/bin/
  chmod +x .render/bin/ffmpeg .render/bin/ffprobe
  echo "[build] ffmpeg installed at .render/bin"
  .render/bin/ffmpeg -version | head -n 1 || true
fi
python -c "import multipart; print('multipart:', multipart.__version__)"
python -c "import boto3, botocore; print('boto3', boto3.__version__, 'botocore', botocore.__version__)"
python -c "import faster_whisper; print('faster_whisper', getattr(faster_whisper,'__version__','ok'))"
