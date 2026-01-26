#!/usr/bin/env bash
set -euo pipefail

API_KEY="${BABELDOC_API_KEY:-}"
BASE_URL="${BABELDOC_BASE_URL:-https://api.deepseek.com/v1}"
MODEL="${BABELDOC_MODEL:-deepseek-chat}"
SERVER_URL="${BABELDOC_SERVER_URL:-http://127.0.0.1:8000}"
PDF_PATH="${BABELDOC_PDF_PATH:-/home/ifzzh/Project/PDF-Babel/test-pdf/Kua.pdf}"
WAIT_SECONDS="${BABELDOC_WAIT_SECONDS:-1800}"
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

create_job() {
  curl -sSf -X POST "$SERVER_URL/api/jobs" \
    -F "file=@${PDF_PATH}" \
    -F 'options={"lang_in":"en","lang_out":"zh"}' \
    -F "source={\"mode\":\"custom\",\"channel_id\":\"deepseek\",\"credentials\":{\"base_url\":\"${BASE_URL}\",\"api_key\":\"${API_KEY}\",\"model\":\"${MODEL}\"}}" \
    | jq -r '.job_id'
}

JOB_ID_1=$(create_job)
JOB_ID_2=$(create_job)

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

echo "\n--- 队列快照（运行前）---"
curl -sSf "$SERVER_URL/api/queue" | jq .

RUN1=$(curl -sSf -X POST "$SERVER_URL/api/jobs/$JOB_ID_1/run")
RUN2=$(curl -sSf -X POST "$SERVER_URL/api/jobs/$JOB_ID_2/run")

STATUS1=$(echo "$RUN1" | jq -r '.status')
STATUS2=$(echo "$RUN2" | jq -r '.status')

echo "run1: $STATUS1"
echo "run2: $STATUS2"

if [[ "$STATUS1" != "running" ]]; then
  echo "第一个任务未进入 running，实际：$STATUS1" >&2
  exit 1
fi
if [[ "$STATUS2" != "queued" ]]; then
  echo "第二个任务未进入 queued，实际：$STATUS2" >&2
  exit 1
fi

echo "\n--- 队列快照（提交后）---"
QUEUE_SNAPSHOT=$(curl -sSf "$SERVER_URL/api/queue")
echo "$QUEUE_SNAPSHOT" | jq .

if ! echo "$QUEUE_SNAPSHOT" | jq -e --arg id "$JOB_ID_1" '.running | index($id) != null' >/dev/null; then
  echo "队列快照中未包含运行中的任务1" >&2
  exit 1
fi
if ! echo "$QUEUE_SNAPSHOT" | jq -e --arg id "$JOB_ID_2" '.queued | index($id) != null' >/dev/null; then
  echo "队列快照中未包含排队任务2" >&2
  exit 1
fi

echo "等待任务2从 queued 变为 running..."
elapsed=0
status=""
while true; do
  status=$(curl -sSf "$SERVER_URL/api/jobs/$JOB_ID_2" | jq -r '.status')
  if [[ "$status" == "running" || "$status" == "finished" || "$status" == "failed" || "$status" == "canceled" ]]; then
    break
  fi
  if (( elapsed >= WAIT_SECONDS )); then
    echo "等待超时，任务2状态：$status" >&2
    exit 1
  fi
  sleep "$POLL_INTERVAL"
  elapsed=$((elapsed + POLL_INTERVAL))

done

echo "任务2当前状态：$status"

echo "\n--- 队列快照（任务2开始后）---"
curl -sSf "$SERVER_URL/api/queue" | jq .

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
