#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: BASE_URL=http://localhost:10000 AUTH='X-OP-KEY: xxx' $0 <task_id>" >&2
  exit 2
fi

TASK_ID="$1"
BASE_URL="${BASE_URL:-http://localhost:10000}"
AUTH_HEADER="${AUTH:-}"
TIMEOUT_SEC="${TIMEOUT_SEC:-180}"
INTERVAL_SEC="${INTERVAL_SEC:-3}"

auth_args=()
if [[ -n "$AUTH_HEADER" ]]; then
  auth_args=(-H "$AUTH_HEADER")
fi

echo "[smoke] enqueue scenes for task=$TASK_ID"
curl -sS "${auth_args[@]}" -X POST "${BASE_URL}/api/tasks/${TASK_ID}/scenes" >/tmp/smoke_scenes_enqueue.json
cat /tmp/smoke_scenes_enqueue.json
echo

deadline=$(( $(date +%s) + TIMEOUT_SEC ))
while true; do
  now=$(date +%s)
  if (( now > deadline )); then
    echo "[smoke] timeout waiting for scenes_key/scenes_error" >&2
    exit 1
  fi

  payload="$(curl -sS "${auth_args[@]}" "${BASE_URL}/api/tasks/${TASK_ID}")"
  scenes_key="$(printf '%s' "$payload" | python -c 'import json,sys; d=json.load(sys.stdin); print((d.get("scenes_key") or "").strip())')"
  scenes_error="$(printf '%s' "$payload" | python -c 'import json,sys; d=json.load(sys.stdin); e=d.get("scenes_error"); print("" if e in (None,"",{}) else e)')"
  status="$(printf '%s' "$payload" | python -c 'import json,sys; d=json.load(sys.stdin); print(d.get("scenes_status") or "")')"
  elapsed="$(printf '%s' "$payload" | python -c 'import json,sys; d=json.load(sys.stdin); print(d.get("scenes_elapsed_ms") or "")')"

  echo "[smoke] status=${status} elapsed_ms=${elapsed} scenes_key=${scenes_key:-<nil>}"
  if [[ -n "$scenes_key" ]]; then
    echo "[smoke] success: scenes_key=${scenes_key}"
    break
  fi
  if [[ -n "$scenes_error" ]]; then
    echo "[smoke] failed: scenes_error=${scenes_error}" >&2
    exit 1
  fi
  sleep "$INTERVAL_SEC"
done

echo "[smoke] HEAD /v1/tasks/${TASK_ID}/scenes"
curl -sSI "${auth_args[@]}" "${BASE_URL}/v1/tasks/${TASK_ID}/scenes" | head -n 1
