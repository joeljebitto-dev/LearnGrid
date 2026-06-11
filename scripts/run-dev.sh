#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_ROOT="$ROOT_DIR/backend/services"

SKIP_INSTALL=false
SKIP_MIGRATIONS=false
POETRY_BIN="${POETRY_BIN:-poetry}"

POSTGRES_USER_VALUE="${POSTGRES_USER:-learngrid}"
POSTGRES_PASSWORD_VALUE="${POSTGRES_PASSWORD:-learngrid}"
POSTGRES_HOST_VALUE="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT_VALUE="${POSTGRES_PORT:-5432}"
REDIS_URL_VALUE="${REDIS_URL:-redis://localhost:6379/0}"
CONTENT_STORAGE_BUCKET_VALUE="${CONTENT_STORAGE_BUCKET:-learngrid-content}"
CONTENT_MINIO_ENDPOINT_URL_VALUE="${CONTENT_MINIO_ENDPOINT_URL:-http://127.0.0.1:9000}"
CONTENT_MINIO_ACCESS_KEY_VALUE="${CONTENT_MINIO_ACCESS_KEY:-learngrid}"
CONTENT_MINIO_SECRET_KEY_VALUE="${CONTENT_MINIO_SECRET_KEY:-learngrid-minio-secret}"

SERVICES=(
  "auth-service:auth_db:8001"
  "user-service:user_db:8002"
  "course-service:course_db:8003"
  "content-service:content_db:8004"
  "enrollment-service:enrollment_db:8005"
  "progress-service:progress_db:8006"
  "assessment-service:assessment_db:8007"
  "grading-service:grading_db:8008"
  "notification-service:notification_db:8009"
  "analytics-service:analytics_db:8010"
)

APP_PORTS=(5173 8001 8002 8003 8004 8005 8006 8007 8008 8009 8010 8080 8443)
PIDS=()
CLEANED_UP=false
GATEWAY_STARTED=false

usage() {
  cat <<'EOF'
Usage: scripts/run-dev.sh [options]

Options:
  --skip-install      Skip pnpm and Poetry dependency installation.
  --skip-migrations  Skip Django migrations.
  -h, --help         Show this help text.

Environment:
  POETRY_BIN         Poetry executable to use. Defaults to "poetry".
  POSTGRES_USER      Local PostgreSQL user. Defaults to "learngrid".
  POSTGRES_PASSWORD  Local PostgreSQL password. Defaults to "learngrid".
  POSTGRES_HOST      Local PostgreSQL host. Defaults to "localhost".
  POSTGRES_PORT      Local PostgreSQL port. Defaults to "5432".
  REDIS_URL          Local Redis URL. Defaults to "redis://localhost:6379/0".
  CONTENT_STORAGE_BUCKET      Local MinIO bucket. Defaults to "learngrid-content".
  CONTENT_MINIO_ENDPOINT_URL  Local MinIO endpoint. Defaults to "http://127.0.0.1:9000".
  CONTENT_MINIO_ACCESS_KEY    Local MinIO access key. Defaults to "learngrid".
  CONTENT_MINIO_SECRET_KEY    Local MinIO secret key. Defaults to "learngrid-minio-secret".
EOF
}

log() {
  printf '[dev] %s\n' "$*"
}

fail() {
  printf '[dev] ERROR: %s\n' "$*" >&2
  exit 1
}

compose() {
  docker compose --project-directory "$ROOT_DIR" -f "$ROOT_DIR/docker-compose.yml" "$@"
}

need_command() {
  local command_name="$1"
  local install_hint="$2"

  if ! command -v "$command_name" >/dev/null 2>&1; then
    fail "$command_name is required. $install_hint"
  fi
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --skip-install)
        SKIP_INSTALL=true
        ;;
      --skip-migrations)
        SKIP_MIGRATIONS=true
        ;;
      -h | --help)
        usage
        exit 0
        ;;
      *)
        fail "Unknown option: $1"
        ;;
    esac
    shift
  done
}

cleanup() {
  if [[ "$CLEANED_UP" == true ]]; then
    return
  fi
  CLEANED_UP=true

  if ((${#PIDS[@]} > 0)); then
    log "Stopping backend and frontend processes..."
    for pid in "${PIDS[@]}"; do
      kill -TERM "-$pid" >/dev/null 2>&1 || kill -TERM "$pid" >/dev/null 2>&1 || true
    done
    sleep 1
    for pid in "${PIDS[@]}"; do
      if kill -0 "$pid" >/dev/null 2>&1; then
        kill -KILL "-$pid" >/dev/null 2>&1 || kill -KILL "$pid" >/dev/null 2>&1 || true
      fi
    done
    wait "${PIDS[@]}" >/dev/null 2>&1 || true
  fi

  if [[ "$GATEWAY_STARTED" == true ]]; then
    log "Stopping API gateway..."
    compose stop api-gateway >/dev/null 2>&1 || true
  fi
}

preflight() {
  need_command docker "Install Docker with the Compose plugin."
  need_command pnpm "Install pnpm 11+."
  need_command python3 "Install Python 3.12+."
  need_command setsid "Install util-linux or provide a shell environment with setsid."
  need_command openssl "Install OpenSSL for local gateway TLS certificates."

  if ! command -v "$POETRY_BIN" >/dev/null 2>&1; then
    fail "$POETRY_BIN is required. Install Poetry 2+ or set POETRY_BIN=/path/to/poetry."
  fi

  if ! docker info >/dev/null 2>&1; then
    fail "Docker is not running or is not accessible for the current user."
  fi

  python3 - "${APP_PORTS[@]}" <<'PY'
import socket
import sys

busy = []
for raw_port in sys.argv[1:]:
    port = int(raw_port)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.25)
        if sock.connect_ex(("127.0.0.1", port)) == 0:
            busy.append(raw_port)

if busy:
    print("Ports already in use: " + ", ".join(busy), file=sys.stderr)
    sys.exit(1)
PY
}

start_infrastructure() {
  log "Starting PostgreSQL, Redis, and MinIO..."
  MINIO_ROOT_USER="$CONTENT_MINIO_ACCESS_KEY_VALUE" \
    MINIO_ROOT_PASSWORD="$CONTENT_MINIO_SECRET_KEY_VALUE" \
    CONTENT_STORAGE_BUCKET="$CONTENT_STORAGE_BUCKET_VALUE" \
    compose up -d postgres redis minio

  log "Waiting for PostgreSQL..."
  until compose exec -T postgres pg_isready -U "$POSTGRES_USER_VALUE" -d learngrid >/dev/null 2>&1; do
    sleep 1
  done

  log "Waiting for Redis..."
  until compose exec -T redis redis-cli ping >/dev/null 2>&1; do
    sleep 1
  done

  log "Waiting for MinIO..."
  until python3 - "$CONTENT_MINIO_ENDPOINT_URL_VALUE/minio/health/ready" <<'PY' >/dev/null 2>&1; do
import sys
from urllib.request import urlopen

with urlopen(sys.argv[1], timeout=2) as response:
    if response.status >= 500:
        raise SystemExit(1)
PY
    sleep 1
  done

  log "Ensuring MinIO bucket exists..."
  MINIO_ROOT_USER="$CONTENT_MINIO_ACCESS_KEY_VALUE" \
    MINIO_ROOT_PASSWORD="$CONTENT_MINIO_SECRET_KEY_VALUE" \
    CONTENT_STORAGE_BUCKET="$CONTENT_STORAGE_BUCKET_VALUE" \
    compose up minio-init >/dev/null
}

ensure_database() {
  local database_name="$1"
  local exists

  exists="$(
    compose exec -T postgres psql \
      -U "$POSTGRES_USER_VALUE" \
      -d postgres \
      -tAc "SELECT 1 FROM pg_database WHERE datname = '$database_name';" |
      tr -d '[:space:]'
  )"

  if [[ "$exists" != "1" ]]; then
    log "Creating PostgreSQL database $database_name..."
    compose exec -T postgres psql \
      -U "$POSTGRES_USER_VALUE" \
      -d postgres \
      -v ON_ERROR_STOP=1 \
      -c "CREATE DATABASE $database_name;" >/dev/null
  fi
}

ensure_service_databases() {
  local service
  local database_name
  local port

  log "Ensuring service databases exist..."
  for service_config in "${SERVICES[@]}"; do
    IFS=":" read -r service database_name port <<<"$service_config"
    ensure_database "$database_name"
  done
}

install_dependencies() {
  local service
  local database_name
  local port
  local service_dir

  if [[ "$SKIP_INSTALL" == true ]]; then
    log "Skipping dependency installation."
    return
  fi

  log "Installing frontend dependencies..."
  (cd "$ROOT_DIR" && pnpm install)

  for service_config in "${SERVICES[@]}"; do
    IFS=":" read -r service database_name port <<<"$service_config"
    service_dir="$BACKEND_ROOT/$service"
    log "Installing backend dependencies for $service..."
    (cd "$service_dir" && "$POETRY_BIN" install --no-interaction)
  done
}

export_backend_env() {
  local database_name="$1"
  local port="$2"

  export DJANGO_SETTINGS_MODULE=config.settings.local
  export DJANGO_DEBUG=true
  export DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
  export CORS_ALLOWED_ORIGINS=http://localhost:5173
  export SERVICE_PORT="$port"
  export DATABASE_URL="postgresql://${POSTGRES_USER_VALUE}:${POSTGRES_PASSWORD_VALUE}@${POSTGRES_HOST_VALUE}:${POSTGRES_PORT_VALUE}/${database_name}"
  export REDIS_URL="$REDIS_URL_VALUE"
  export CONTENT_STORAGE_PROVIDER=minio
  export CONTENT_STORAGE_BUCKET="$CONTENT_STORAGE_BUCKET_VALUE"
  export CONTENT_MINIO_ENDPOINT_URL="$CONTENT_MINIO_ENDPOINT_URL_VALUE"
  export CONTENT_MINIO_ACCESS_KEY="$CONTENT_MINIO_ACCESS_KEY_VALUE"
  export CONTENT_MINIO_SECRET_KEY="$CONTENT_MINIO_SECRET_KEY_VALUE"
  export CONTENT_MINIO_SECURE="${CONTENT_MINIO_SECURE:-false}"
  export AUTH_SERVICE_BASE_URL="${AUTH_SERVICE_BASE_URL:-http://127.0.0.1:8001}"
  export AUTH_JWT_SIGNING_KEY="${AUTH_JWT_SIGNING_KEY:-${DJANGO_SECRET_KEY:-insecure-local-auth-service-change-me-32bytes}}"
  export AUTH_JWT_ISSUER="${AUTH_JWT_ISSUER:-learngrid-auth-service}"
  export AUTH_JWT_ALGORITHM="${AUTH_JWT_ALGORITHM:-HS256}"
}

run_migrations() {
  local service
  local database_name
  local port
  local service_dir

  if [[ "$SKIP_MIGRATIONS" == true ]]; then
    log "Skipping backend migrations."
    return
  fi

  for service_config in "${SERVICES[@]}"; do
    IFS=":" read -r service database_name port <<<"$service_config"
    service_dir="$BACKEND_ROOT/$service"
    log "Running migrations for $service..."
    (
      cd "$service_dir"
      export_backend_env "$database_name" "$port"
      "$POETRY_BIN" run python manage.py migrate --noinput
    )
  done
}

start_backend_service() {
  local service="$1"
  local database_name="$2"
  local port="$3"
  local service_dir="$BACKEND_ROOT/$service"

  log "Starting $service on http://127.0.0.1:$port..."
  (
    cd "$service_dir"
    export_backend_env "$database_name" "$port"
    exec setsid "$POETRY_BIN" run python manage.py runserver "127.0.0.1:$port" --noreload
  ) > >(sed -u "s/^/[$service] /") 2>&1 &
  PIDS+=("$!")
}

start_frontend() {
  log "Starting frontend-service on http://127.0.0.1:5173..."
  (
    cd "$ROOT_DIR"
    exec setsid pnpm -C frontend dev
  ) > >(sed -u "s/^/[frontend-service] /") 2>&1 &
  PIDS+=("$!")
}

start_applications() {
  local service
  local database_name
  local port

  for service_config in "${SERVICES[@]}"; do
    IFS=":" read -r service database_name port <<<"$service_config"
    start_backend_service "$service" "$database_name" "$port"
  done

  start_frontend
}

check_app_processes() {
  local pid

  for pid in "${PIDS[@]}"; do
    if ! kill -0 "$pid" >/dev/null 2>&1; then
      fail "An app process exited before startup completed. Check the prefixed logs above."
    fi
  done
}

wait_for_http() {
  local name="$1"
  local url="$2"
  local timeout_seconds="${3:-60}"
  local deadline=$((SECONDS + timeout_seconds))

  while ((SECONDS < deadline)); do
    check_app_processes
    if python3 - "$url" <<'PY' >/dev/null 2>&1; then
import sys
from urllib.request import urlopen

with urlopen(sys.argv[1], timeout=2) as response:
    if response.status >= 500:
        raise SystemExit(1)
PY
      return
    fi
    sleep 1
  done

  fail "$name did not become ready at $url within ${timeout_seconds}s."
}

wait_for_applications() {
  local service
  local database_name
  local port

  log "Waiting for backend health endpoints..."
  for service_config in "${SERVICES[@]}"; do
    IFS=":" read -r service database_name port <<<"$service_config"
    wait_for_http "$service" "http://127.0.0.1:$port/health/" 90
  done

  log "Waiting for frontend..."
  wait_for_http "frontend-service" "http://127.0.0.1:5173/" 90
}

start_gateway() {
  log "Preparing local API gateway TLS certificate..."
  "$ROOT_DIR/scripts/generate-local-gateway-cert.sh"

  log "Starting api-gateway on http://127.0.0.1:8080 and https://127.0.0.1:8443..."
  compose up -d api-gateway >/dev/null
  GATEWAY_STARTED=true

  log "Waiting for api-gateway..."
  until python3 - "https://127.0.0.1:8443/gateway/health" <<'PY' >/dev/null 2>&1; do
import ssl
import sys
from urllib.request import urlopen

context = ssl._create_unverified_context()
with urlopen(sys.argv[1], context=context, timeout=2) as response:
    if response.status >= 500:
        raise SystemExit(1)
PY
    sleep 1
  done
}

print_running_summary() {
  cat <<'EOF'
[dev] LearnGrid LMS is running.
[dev] Frontend: http://127.0.0.1:5173
[dev] API Gateway HTTP: http://127.0.0.1:8080
[dev] API Gateway HTTPS: https://127.0.0.1:8443
[dev] MinIO API: http://127.0.0.1:9000
[dev] MinIO Console: http://127.0.0.1:9001
[dev] Backend health endpoints:
[dev]   auth-service         http://127.0.0.1:8001/health/
[dev]   user-service         http://127.0.0.1:8002/health/
[dev]   course-service       http://127.0.0.1:8003/health/
[dev]   content-service      http://127.0.0.1:8004/health/
[dev]   enrollment-service   http://127.0.0.1:8005/health/
[dev]   progress-service     http://127.0.0.1:8006/health/
[dev]   assessment-service   http://127.0.0.1:8007/health/
[dev]   grading-service      http://127.0.0.1:8008/health/
[dev]   notification-service http://127.0.0.1:8009/health/
[dev]   analytics-service    http://127.0.0.1:8010/health/
[dev] Press Ctrl+C to stop app processes. PostgreSQL, Redis, and MinIO stay running.
EOF
}

wait_until_stopped() {
  set +e
  wait -n "${PIDS[@]}"
  local status=$?
  set -e

  log "An app process exited; stopping the remaining app processes."
  cleanup
  exit "$status"
}

main() {
  parse_args "$@"
  trap cleanup EXIT
  trap 'exit 130' INT
  trap 'exit 143' TERM

  preflight
  start_infrastructure
  ensure_service_databases
  install_dependencies
  run_migrations
  start_applications
  wait_for_applications
  start_gateway
  print_running_summary
  wait_until_stopped
}

main "$@"
