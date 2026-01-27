#!/usr/bin/env bash
set -euo pipefail

BASE_URL=${BASE_URL:-"http://127.0.0.1:8000"}
PDF_PATH=${PDF_PATH:-"/home/ifzzh/Project/PDF-Babel/test-pdf/Kua.pdf"}
CHANNEL_ID=${CHANNEL_ID:-"deepseek"}
API_KEY=${BABELDOC_API_KEY:-""}
MODEL=${MODEL:-"deepseek-chat"}
BASE_API_URL=${BASE_API_URL:-"https://api.deepseek.com/v1"}

if [[ -z "$API_KEY" ]]; then
  echo "BABELDOC_API_KEY is required" >&2
  exit 1
fi

source_json=$(cat <<JSON
{"mode":"custom","channel_id":"${CHANNEL_ID}","credentials":{"base_url":"${BASE_API_URL}","api_key":"${API_KEY}","model":"${MODEL}"}}
JSON
)

options_json='{"lang_in":"en","lang_out":"zh","auto_extract_glossary":true,"save_auto_extracted_glossary":true}'

job_id=$(curl -sS -X POST "$BASE_URL/api/jobs" \
  -F "file=@$PDF_PATH" \
  -F "options=$options_json" \
  -F "source=$source_json" | jq -r '.job_id')

if [[ -z "$job_id" || "$job_id" == "null" ]]; then
  echo "Failed to create job" >&2
  exit 1
fi

echo "job_id: $job_id"

curl -sS -X POST "$BASE_URL/api/jobs/$job_id/run" | jq . >/dev/null

status="queued"
for _ in {1..120}; do
  status=$(curl -sS "$BASE_URL/api/jobs/$job_id" | jq -r '.status')
  if [[ "$status" == "finished" || "$status" == "failed" || "$status" == "canceled" ]]; then
    break
  fi
  sleep 1
 done

echo "status: $status"

files=$(curl -sS "$BASE_URL/api/jobs/$job_id/files")

echo "$files" | jq .

if echo "$files" | jq -e '.[] | select(.type=="glossary")' >/dev/null; then
  echo "[PASS] glossary file found"
else
  echo "[WARN] glossary file not found (可能自动抽取无结果)"
fi
