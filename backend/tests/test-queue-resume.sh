#!/usr/bin/env bash
set -euo pipefail

API_KEY="${BABELDOC_API_KEY:-}"
BASE_URL="${BABELDOC_BASE_URL:-https://api.deepseek.com/v1}"
MODEL="${BABELDOC_MODEL:-deepseek-chat}"
SERVER_URL="${BABELDOC_SERVER_URL:-http://127.0.0.1:8000}"
PDF_PATH="${BABELDOC_PDF_PATH:-/home/ifzzh/Project/PDF-Babel/test-pdf/Kua.pdf}"
WAIT_SECONDS="${BABELDOC_WAIT_SECONDS:-1800}"
POLL_INTERVAL="${BABELDOC_POLL_INTERVAL:-2}"

SERVER_URL="${SERVER_URL//$'\r'/}"
SERVER_URL="${SERVER_URL%/}"

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

create_job() {
  curl -sSf -X POST "$SERVER_URL/api/jobs" \
    -F "file=@${PDF_PATH}" \
    -F 'options={"lang_in":"en","lang_out":"zh"}' \
    -F "source={\"mode\":\"custom\",\"channel_id\":\"deepseek\",\"credentials\":{\"base_url\":\"${BASE_URL}\",\"api_key\":\"${API_KEY}\",\"model\":\"${MODEL}\"}}" \
    | jq -r '.job_id'
}

JOB_ID_1=$(create_job)
JOB_ID_2=$(create_job)
FAKE_ID="00000000-0000-0000-0000-000000000000"

if [[ -z "$JOB_ID_1" || "$JOB_ID_1" == "null" ]]; then
  echo "创建任务1失败" >&2
  exit 1
fi
if [[ -z "$JOB_ID_2" || "$JOB_ID_2" == "null" ]]; then
  echo "创建任务2失败" >&2
  exit 1
fi

echo "job_id_1: $JOB_ID_1"
echo "job_id_2: $JOB_ID_2"

RUN1=$(curl -sSf -X POST "$SERVER_URL/api/jobs/$JOB_ID_1/run")
RUN2=$(curl -sSf -X POST "$SERVER_URL/api/jobs/$JOB_ID_2/run")
STATUS1=$(echo "$RUN1" | jq -r '.status')
STATUS2=$(echo "$RUN2" | jq -r '.status')
echo "run1: $STATUS1"
echo "run2: $STATUS2"

# 确保任务2进入 queued
elapsed=0
queued_ok=false
while true; do
QUEUE_SNAPSHOT=$(curl -sSf "$SERVER_URL/api/queue")
  if echo "$QUEUE_SNAPSHOT" | jq -e --arg id "$JOB_ID_2" '.queued | index($id) != null' >/dev/null; then
    queued_ok=true
    break
  fi
  if (( elapsed >= 30 )); then
    break
  fi
  sleep 1
  elapsed=$((elapsed + 1))
done

RESUME_TARGET="$JOB_ID_2"
if [[ "$queued_ok" != "true" ]]; then
  RESUME_TARGET=$(echo "$QUEUE_SNAPSHOT" | jq -r '.queued[0] // empty')
fi

if [[ -z "$RESUME_TARGET" || "$RESUME_TARGET" == "null" ]]; then
  echo "队列中没有可用于 resume 的任务（可能任务过快完成），请重试或使用更大的 PDF" >&2
  echo "$QUEUE_SNAPSHOT" | jq .
  exit 1
fi

echo "\n--- 队列快照（resume 前）---"
echo "$QUEUE_SNAPSHOT" | jq .

RESUME_PAYLOAD=$(printf '{"job_ids":["%s","%s","%s"]}' "$JOB_ID_1" "$RESUME_TARGET" "$FAKE_ID")
RESUME_RESP=$(curl -sSf -X POST "$SERVER_URL/api/queue/resume" \
  -H 'Content-Type: application/json' \
  -d "$RESUME_PAYLOAD")

echo "\n--- resume 响应 ---"
echo "$RESUME_RESP" | jq .

if ! echo "$RESUME_RESP" | jq -e --arg id "$RESUME_TARGET" '.accepted | index($id) != null' >/dev/null; then
  echo "resume 未接收 queued 的任务" >&2
  exit 1
fi

if ! echo "$RESUME_RESP" | jq -e --arg id "$FAKE_ID" '.skipped[] | select(.job_id==$id)' >/dev/null; then
  echo "resume 未返回不存在任务的 skipped" >&2
  exit 1
fi

# 等待两个任务完成
wait_final() {
  local job_id="$1"
  local elapsed_local=0
  local st
  while true; do
    st=$(curl -sSf "$SERVER_URL/api/jobs/$job_id" | jq -r '.status')
    if [[ "$st" == "finished" || "$st" == "failed" || "$st" == "canceled" ]]; then
      echo "$job_id -> $st"
      return
    fi
    if (( elapsed_local >= WAIT_SECONDS )); then
      echo "$job_id 等待超时，当前状态：$st" >&2
      return
    fi
    sleep "$POLL_INTERVAL"
    elapsed_local=$((elapsed_local + POLL_INTERVAL))
  done
}

wait_final "$JOB_ID_1"
wait_final "$JOB_ID_2"

echo "\n--- 队列快照（完成后）---"
curl -sSf "$SERVER_URL/api/queue" | jq .
