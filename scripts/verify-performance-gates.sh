#!/usr/bin/env bash
set -Eeuo pipefail

STAGING_BASE_URL="${STAGING_BASE_URL:-${LOAD_BASE_URL:-}}"
PROMETHEUS_URL="${PROMETHEUS_URL:-}"
EVIDENCE_DIR="${EVIDENCE_DIR:-artifacts/readiness}"
RUN_K6="${RUN_K6:-false}"
K6_SCRIPT="${K6_SCRIPT:-tests/load/staging.js}"
MAX_P95_MS="${MAX_P95_MS:-300}"
MAX_ERROR_RATE="${MAX_ERROR_RATE:-0.02}"
MIN_THROUGHPUT_RPS="${MIN_THROUGHPUT_RPS:-1}"
MAX_POSTGRES_CONNECTIONS="${MAX_POSTGRES_CONNECTIONS:-500}"
MAX_REDIS_MEMORY_BYTES="${MAX_REDIS_MEMORY_BYTES:-1073741824}"
MAX_KAFKA_LAG="${MAX_KAFKA_LAG:-100}"
MAX_CPU_CORES="${MAX_CPU_CORES:-8}"
MAX_MEMORY_BYTES="${MAX_MEMORY_BYTES:-8589934592}"

mkdir -p "$EVIDENCE_DIR"
REPORT="$EVIDENCE_DIR/performance-gates.md"
JSON_REPORT="$EVIDENCE_DIR/performance-gates.jsonl"
: > "$REPORT"
: > "$JSON_REPORT"

record() {
  local status="$1"
  local check="$2"
  local detail="$3"
  printf '{"status":"%s","check":"%s","detail":"%s"}\n' \
    "$status" "$check" "${detail//\"/\\\"}" >> "$JSON_REPORT"
  printf -- '- **%s** `%s`: %s\n' "$status" "$check" "$detail" >> "$REPORT"
}

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    record "fail" "command:$1" "$1 is required"
    exit 1
  fi
}

compare_metric() {
  local name="$1"
  local value="$2"
  local operator="$3"
  local threshold="$4"
  python - "$name" "$value" "$operator" "$threshold" <<'PY'
import operator
import sys

name, raw_value, op_name, raw_threshold = sys.argv[1:]
ops = {
    "le": operator.le,
    "lt": operator.lt,
    "ge": operator.ge,
    "gt": operator.gt,
}
value = float(raw_value)
threshold = float(raw_threshold)
if not ops[op_name](value, threshold):
    raise SystemExit(f"{name}={value} failed {op_name} {threshold}")
PY
}

prometheus_query() {
  local query="$1"
  require_command curl
  require_command python
  curl -fsG "$PROMETHEUS_URL/api/v1/query" --data-urlencode "query=$query" |
    python -c 'import json, sys; payload = json.load(sys.stdin); results = payload.get("data", {}).get("result", []); print("0" if not results else results[0]["value"][1])'
}

printf '# LearnGrid Performance Gate Evidence\n\n' >> "$REPORT"

if [ "$RUN_K6" = "true" ]; then
  if [ -z "$STAGING_BASE_URL" ]; then
    record "fail" "k6:base-url" "STAGING_BASE_URL or LOAD_BASE_URL is required for k6"
    exit 1
  fi
  require_command k6
  LOAD_BASE_URL="$STAGING_BASE_URL" k6 run "$K6_SCRIPT" --summary-export "$EVIDENCE_DIR/k6-summary.json"
  record "pass" "k6:staging" "k6 completed with script $K6_SCRIPT"
else
  record "skip" "k6:staging" "RUN_K6 is not true"
fi

if [ -z "$PROMETHEUS_URL" ]; then
  record "skip" "prometheus" "PROMETHEUS_URL was not provided"
else
  p95_ms="$(prometheus_query 'histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) * 1000')"
  error_rate="$(prometheus_query 'sum(rate(http_requests_total{status=~"5.."}[5m])) / clamp_min(sum(rate(http_requests_total[5m])), 1)')"
  throughput="$(prometheus_query 'sum(rate(http_requests_total[5m]))')"
  postgres_connections="$(prometheus_query 'sum(pg_stat_activity_count)')"
  redis_memory="$(prometheus_query 'max(redis_memory_used_bytes)')"
  kafka_lag="$(prometheus_query 'max(kafka_consumergroup_lag)')"
  cpu_cores="$(prometheus_query 'sum(rate(container_cpu_usage_seconds_total{namespace="learngrid"}[5m]))')"
  memory_bytes="$(prometheus_query 'sum(container_memory_working_set_bytes{namespace="learngrid"})')"

  compare_metric "p95_ms" "$p95_ms" le "$MAX_P95_MS"
  record "pass" "prometheus:p95_latency" "$p95_ms ms <= $MAX_P95_MS ms"
  compare_metric "error_rate" "$error_rate" le "$MAX_ERROR_RATE"
  record "pass" "prometheus:error_rate" "$error_rate <= $MAX_ERROR_RATE"
  compare_metric "throughput" "$throughput" ge "$MIN_THROUGHPUT_RPS"
  record "pass" "prometheus:throughput" "$throughput rps >= $MIN_THROUGHPUT_RPS rps"
  compare_metric "postgres_connections" "$postgres_connections" le "$MAX_POSTGRES_CONNECTIONS"
  record "pass" "prometheus:postgres_connections" "$postgres_connections <= $MAX_POSTGRES_CONNECTIONS"
  compare_metric "redis_memory" "$redis_memory" le "$MAX_REDIS_MEMORY_BYTES"
  record "pass" "prometheus:redis_memory" "$redis_memory <= $MAX_REDIS_MEMORY_BYTES bytes"
  compare_metric "kafka_lag" "$kafka_lag" le "$MAX_KAFKA_LAG"
  record "pass" "prometheus:kafka_lag" "$kafka_lag <= $MAX_KAFKA_LAG"
  compare_metric "cpu_cores" "$cpu_cores" le "$MAX_CPU_CORES"
  record "pass" "prometheus:cpu" "$cpu_cores <= $MAX_CPU_CORES cores"
  compare_metric "memory_bytes" "$memory_bytes" le "$MAX_MEMORY_BYTES"
  record "pass" "prometheus:memory" "$memory_bytes <= $MAX_MEMORY_BYTES bytes"
fi

printf '\nEvidence JSONL: `%s`\n' "$JSON_REPORT" >> "$REPORT"
