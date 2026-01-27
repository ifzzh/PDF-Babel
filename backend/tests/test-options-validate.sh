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

function post_job() {
  local options_json=$1
  local source_json=$2
  shift 2
  curl -sS -X POST "$BASE_URL/api/jobs" \
    -F "file=@$PDF_PATH" \
    -F "options=$options_json" \
    -F "source=$source_json" \
    "$@"
}

source_json=$(cat <<JSON
{"mode":"custom","channel_id":"${CHANNEL_ID}","credentials":{"base_url":"${BASE_API_URL}","api_key":"${API_KEY}","model":"${MODEL}"}}
JSON
)

pass_count=0
fail_count=0

function expect_400() {
  local label=$1
  local options_json=$2
  local body_file
  body_file=$(mktemp)
  local http_code
  set +e
  http_code=$(post_job "$options_json" "$source_json" -o "$body_file" -w "%{http_code}" 2>/tmp/opt-validate.err)
  local code=$?
  set -e
  if [[ $code -eq 0 && "$http_code" == "400" ]]; then
    echo "[PASS] $label -> 400"
    pass_count=$((pass_count+1))
    rm -f "$body_file"
    return
  fi
  echo "[FAIL] $label (expected 400)"
  echo "http_code: $http_code"
  cat "$body_file"
  cat /tmp/opt-validate.err
  rm -f "$body_file"
  fail_count=$((fail_count+1))
}

function expect_200() {
  local label=$1
  local options_json=$2
  local body_file
  body_file=$(mktemp)
  local http_code
  set +e
  http_code=$(post_job "$options_json" "$source_json" -o "$body_file" -w "%{http_code}" 2>/tmp/opt-validate.err)
  local code=$?
  set -e
  if [[ $code -eq 0 && "$http_code" == "200" ]]; then
    echo "[PASS] $label -> 200"
    pass_count=$((pass_count+1))
    rm -f "$body_file"
    return
  fi
  echo "[FAIL] $label (expected 200)"
  echo "http_code: $http_code"
  cat "$body_file"
  cat /tmp/opt-validate.err
  rm -f "$body_file"
  fail_count=$((fail_count+1))
}

expect_400 "no_dual + no_mono" '{"lang_in":"en","lang_out":"zh","no_dual":true,"no_mono":true}'
expect_400 "qps < 1" '{"lang_in":"en","lang_out":"zh","qps":0}'
expect_400 "invalid watermark_output_mode" '{"lang_in":"en","lang_out":"zh","watermark_output_mode":"both"}'
expect_400 "invalid primary_font_family" '{"lang_in":"en","lang_out":"zh","primary_font_family":"comic"}'
expect_200 "valid watermark_output_mode" '{"lang_in":"en","lang_out":"zh","watermark_output_mode":"no_watermark"}'

printf "\nSummary: %d passed, %d failed\n" "$pass_count" "$fail_count"
if [[ $fail_count -ne 0 ]]; then
  exit 1
fi
