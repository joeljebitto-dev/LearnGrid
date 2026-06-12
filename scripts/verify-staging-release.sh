#!/usr/bin/env bash
set -Eeuo pipefail

NAMESPACE="${NAMESPACE:-learngrid}"
STAGING_BASE_URL="${STAGING_BASE_URL:-}"
EVIDENCE_DIR="${EVIDENCE_DIR:-artifacts/readiness}"
RUN_SELENIUM="${RUN_SELENIUM:-false}"
REQUIRE_OPENAPI="${REQUIRE_OPENAPI:-false}"
KUBECTL_TIMEOUT="${KUBECTL_TIMEOUT:-180s}"

SERVICES=(
  auth-service
  user-service
  course-service
  content-service
  enrollment-service
  progress-service
  assessment-service
  grading-service
  notification-service
  analytics-service
)

mkdir -p "$EVIDENCE_DIR"
REPORT="$EVIDENCE_DIR/staging-readiness.md"
JSON_REPORT="$EVIDENCE_DIR/staging-readiness.jsonl"
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

printf '# LearnGrid Staging Readiness Evidence\n\n' >> "$REPORT"
printf 'Namespace: `%s`\n\n' "$NAMESPACE" >> "$REPORT"

require_command kubectl

for deployment in api-gateway frontend-service "${SERVICES[@]}"; do
  kubectl -n "$NAMESPACE" rollout status "deployment/$deployment" --timeout="$KUBECTL_TIMEOUT"
  record "pass" "rollout:$deployment" "deployment rollout completed"
done

for service in "${SERVICES[@]}"; do
  kubectl -n "$NAMESPACE" run "learngrid-health-${service}-${RANDOM}" \
    --quiet \
    --rm \
    -i \
    --restart=Never \
    --image=curlimages/curl:8.10.1 \
    --command -- sh -c "curl -fsS http://${service}:8000/health/"
  record "pass" "health:$service" "cluster service /health/ returned success"
done

if [ -n "$STAGING_BASE_URL" ]; then
  require_command curl
  curl -fsS "$STAGING_BASE_URL/gateway/health" >/dev/null
  record "pass" "gateway:public-health" "$STAGING_BASE_URL/gateway/health returned success"

  if curl -fsS "$STAGING_BASE_URL/api/openapi.json" >/dev/null 2>&1; then
    record "pass" "openapi:public" "OpenAPI document is reachable"
  elif [ "$REQUIRE_OPENAPI" = "true" ]; then
    record "fail" "openapi:public" "OpenAPI document is required but not reachable"
    exit 1
  else
    record "skip" "openapi:public" "OpenAPI document not published for this staging run"
  fi
else
  record "skip" "gateway:public-health" "STAGING_BASE_URL was not provided"
  record "skip" "openapi:public" "STAGING_BASE_URL was not provided"
fi

if [ "$RUN_SELENIUM" = "true" ]; then
  require_command python
  E2E_BASE_URL="${E2E_BASE_URL:-$STAGING_BASE_URL}" python -m pytest tests/e2e
  record "pass" "selenium:e2e" "Selenium smoke suite completed"
else
  record "skip" "selenium:e2e" "RUN_SELENIUM is not true"
fi

printf '\nEvidence JSONL: `%s`\n' "$JSON_REPORT" >> "$REPORT"
