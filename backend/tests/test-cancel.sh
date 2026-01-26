#!/usr/bin/env bash
set -euo pipefail

API_KEY="${BABELDOC_API_KEY:-}"
BASE_URL="${BABELDOC_BASE_URL:-https://api.deepseek.com/v1}"
MODEL="${BABELDOC_MODEL:-deepseek-chat}"
SERVER_URL="${BABELDOC_SERVER_URL:-http://127.0.0.1:8000}"
PDF_PATH="${BABELDOC_PDF_PATH:-/home/ifzzh/Project/PDF-Babel/test-pdf/Kua.pdf}"
CANCEL_DELAY="${BABELDOC_CANCEL_DELAY:-2}"
WAIT_SECONDS="${BABELDOC_WAIT_SECONDS:-1200}"
POLL_INTERVAL="${BABELDOC_POLL_INTERVAL:-2}"

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

SSE_LOG="/tmp/babeldoc-cancel-${JOB_ID}.log"
RUN_OUT="/tmp/babeldoc-run-${JOB_ID}.json"

cleanup() {
  if [[ -n "${SSE_PID:-}" ]] && kill -0 "$SSE_PID" 2>/dev/null; then
    kill "$SSE_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

curl -N "$SERVER_URL/api/jobs/$JOB_ID/events" > "$SSE_LOG" 2>/dev/null &
SSE_PID=$!

sleep 1

# 启动翻译（异步接口，立即返回）
curl -sS -X POST "$SERVER_URL/api/jobs/$JOB_ID/run" > "$RUN_OUT"

# 等一会儿再取消
sleep "$CANCEL_DELAY"

echo "--- 发送取消 ---"
CANCEL_RES=$(curl -sS -X POST "$SERVER_URL/api/jobs/$JOB_ID/cancel")
echo "$CANCEL_RES" | jq .

echo "\n--- run 响应 ---"
if [[ -s "$RUN_OUT" ]]; then
  cat "$RUN_OUT" | jq .
else
  echo "run 输出为空"
fi

elapsed=0
status=""
while true; do
  status=$(curl -sSf "$SERVER_URL/api/jobs/$JOB_ID" | jq -r '.status')
  if [[ "$status" == "finished" || "$status" == "failed" || "$status" == "canceled" ]]; then
    break
  fi
  if (( elapsed >= WAIT_SECONDS )); then
    echo "等待超时，当前状态：$status" >&2
    break
  fi
  sleep "$POLL_INTERVAL"
  elapsed=$((elapsed + POLL_INTERVAL))
done

echo "\n--- 当前任务状态：$status ---"
curl -sSf "$SERVER_URL/api/jobs/$JOB_ID" | jq .

echo "\n--- SSE 日志（最后 50 行）---"
tail -n 50 "$SSE_LOG" || true
