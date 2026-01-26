#!/usr/bin/env bash
set -euo pipefail

SERVER_URL="${BABELDOC_SERVER_URL:-http://127.0.0.1:8000}"

if ! command -v jq >/dev/null 2>&1; then
  echo "未找到 jq，请先安装" >&2
  exit 1
fi

curl -sSf "$SERVER_URL/api/queue" | jq .
