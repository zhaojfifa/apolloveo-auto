#!/usr/bin/env bash
set -euo pipefail

echo "[build] python=$(python --version)"
echo "[build] pip=$(python -m pip --version)"

python -m pip install -U pip

echo "[build] installing deps from: gateway/requirements.txt"
python -m pip install -r "gateway/requirements.txt"

# ---- install static ffmpeg (no apt-get) ----
mkdir -p .render/bin /tmp/ffmpeg

FFMPEG_URL="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"

echo "[build] downloading ffmpeg static..."
curl -L "$FFMPEG_URL" -o /tmp/ffmpeg/ffmpeg.tar.xz

echo "[build] extracting ffmpeg..."
tar -xJf /tmp/ffmpeg/ffmpeg.tar.xz -C /tmp/ffmpeg

FFDIR="$(find /tmp/ffmpeg -maxdepth 1 -type d -name 'ffmpeg-*' | head -n 1)"
test -n "$FFDIR"

cp -f "$FFDIR/ffmpeg" "$FFDIR/ffprobe" .render/bin/
chmod +x .render/bin/ffmpeg .render/bin/ffprobe

echo "[build] ffmpeg installed at .render/bin"
python -c "import multipart; print('multipart:', multipart.__version__)"
python -c "import boto3, botocore; print('boto3', boto3.__version__, 'botocore', botocore.__version__)"
python -c "import faster_whisper; print('faster_whisper', getattr(faster_whisper,'__version__','ok'))"
