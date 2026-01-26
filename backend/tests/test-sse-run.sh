#!/usr/bin/env bash
set -euo pipefail

API_KEY="${BABELDOC_API_KEY:-}"
BASE_URL="${BABELDOC_BASE_URL:-https://api.deepseek.com/v1}"
MODEL="${BABELDOC_MODEL:-deepseek-chat}"
SERVER_URL="${BABELDOC_SERVER_URL:-http://127.0.0.1:8000}"
PDF_PATH="${BABELDOC_PDF_PATH:-/home/ifzzh/Project/PDF-Babel/test-pdf/Kua.pdf}"

if [[ -z "$API_KEY" ]]; then
  echo "缺少环境变量 BABELDOC_API_KEY" >&2
  echo "示例：export BABELDOC_API_KEY=sk-xxxx" >&2
  exit 1
fi

if [[ ! -f "$PDF_PATH" ]]; then
  echo "找不到 PDF：$PDF_PATH" >&2
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "未找到 jq，请先安装" >&2
  exit 1
fi

JOB_ID=$(curl -sSf -X POST "$SERVER_URL/api/jobs" \
  -F "file=@${PDF_PATH}" \
  -F 'options={"lang_in":"en","lang_out":"zh"}' \
  -F "source={\"mode\":\"custom\",\"channel_id\":\"deepseek\",\"credentials\":{\"base_url\":\"${BASE_URL}\",\"api_key\":\"${API_KEY}\",\"model\":\"${MODEL}\"}}" \
  | jq -r '.job_id')

if [[ -z "$JOB_ID" || "$JOB_ID" == "null" ]]; then
  echo "创建任务失败，未拿到 job_id" >&2
  exit 1
fi

echo "job_id: $JOB_ID"

SSE_LOG="/tmp/babeldoc-sse-${JOB_ID}.log"

cleanup() {
  if [[ -n "${SSE_PID:-}" ]] && kill -0 "$SSE_PID" 2>/dev/null; then
    kill "$SSE_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

curl -N "$SERVER_URL/api/jobs/$JOB_ID/events" > "$SSE_LOG" 2>/dev/null &
SSE_PID=$!

sleep 1

curl -sSf -X POST "$SERVER_URL/api/jobs/$JOB_ID/run" | jq .

echo "\n--- SSE 日志（最后 50 行）---"
tail -n 50 "$SSE_LOG" || true

echo "\n--- 文件列表 ---"
curl -sSf "$SERVER_URL/api/jobs/$JOB_ID/files" | jq .
