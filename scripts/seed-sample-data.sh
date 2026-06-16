#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_ROOT="$ROOT_DIR/backend/services"

POETRY_BIN="${POETRY_BIN:-poetry}"
SKIP_MIGRATIONS=false
DRY_RUN=false
RESET_SAMPLE_DATA=false
TARGET_SERVICE=""
MANIFEST="$ROOT_DIR/scripts/sample-data/learngrid-demo.json"

POSTGRES_USER_VALUE="${POSTGRES_USER:-learngrid}"
POSTGRES_PASSWORD_VALUE="${POSTGRES_PASSWORD:-learngrid}"
POSTGRES_HOST_VALUE="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT_VALUE="${POSTGRES_PORT:-5432}"
REDIS_URL_VALUE="${REDIS_URL:-redis://localhost:6379/0}"
CONTENT_STORAGE_BUCKET_VALUE="${CONTENT_STORAGE_BUCKET:-learngrid-content}"
CONTENT_MINIO_ENDPOINT_URL_VALUE="${CONTENT_MINIO_ENDPOINT_URL:-http://127.0.0.1:9000}"
CONTENT_MINIO_ACCESS_KEY_VALUE="${CONTENT_MINIO_ACCESS_KEY:-learngrid}"
CONTENT_MINIO_SECRET_KEY_VALUE="${CONTENT_MINIO_SECRET_KEY:-learngrid-minio-secret}"
KAFKA_BOOTSTRAP_SERVERS_VALUE="${KAFKA_BOOTSTRAP_SERVERS:-127.0.0.1:9092}"

SERVICES=(
  "auth-service:auth_db:8001"
  "user-service:user_db:8002"
  "content-service:content_db:8004"
  "course-service:course_db:8003"
  "enrollment-service:enrollment_db:8005"
  "progress-service:progress_db:8006"
  "assessment-service:assessment_db:8007"
  "grading-service:grading_db:8008"
  "notification-service:notification_db:8009"
  "analytics-service:analytics_db:8010"
)

usage() {
  cat <<'EOF'
Usage: scripts/seed-sample-data.sh [options]

Seeds deterministic LearnGrid demo data into local service databases.

Options:
  --skip-migrations       Do not run Django migrations before seeding.
  --service <service>     Seed one service only. Accepts auth or auth-service forms.
  --dry-run               Print planned records without writing.
  --reset-sample-data     Delete demo records before reseeding.
  --manifest <path>       Manifest path. Defaults to scripts/sample-data/learngrid-demo.json.
  -h, --help              Show this help text.
EOF
}

log() {
  printf '[seed] %s\n' "$*"
}

fail() {
  printf '[seed] ERROR: %s\n' "$*" >&2
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

normalize_service_name() {
  local raw="$1"
  if [[ "$raw" == *-service ]]; then
    printf '%s' "$raw"
  else
    printf '%s-service' "$raw"
  fi
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --skip-migrations)
        SKIP_MIGRATIONS=true
        ;;
      --service)
        [[ $# -ge 2 ]] || fail "--service requires a service name."
        TARGET_SERVICE="$(normalize_service_name "$2")"
        shift
        ;;
      --dry-run)
        DRY_RUN=true
        ;;
      --reset-sample-data)
        RESET_SAMPLE_DATA=true
        ;;
      --manifest)
        [[ $# -ge 2 ]] || fail "--manifest requires a path."
        MANIFEST="$2"
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

preflight() {
  need_command docker "Install Docker with the Compose plugin."
  need_command python3 "Install Python 3.12+."
  if ! command -v "$POETRY_BIN" >/dev/null 2>&1; then
    fail "$POETRY_BIN is required. Install Poetry 2+ or set POETRY_BIN=/path/to/poetry."
  fi
  if [[ ! -f "$MANIFEST" ]]; then
    fail "Sample data manifest not found: $MANIFEST"
  fi
  if ! docker info >/dev/null 2>&1; then
    fail "Docker is not running or is not accessible for the current user."
  fi

  local service
  local database_name
  local port
  local matched=false
  for service_config in "${SERVICES[@]}"; do
    IFS=":" read -r service database_name port <<<"$service_config"
    [[ -d "$BACKEND_ROOT/$service" ]] || fail "Missing service directory: $BACKEND_ROOT/$service"
    if [[ -z "$TARGET_SERVICE" || "$TARGET_SERVICE" == "$service" ]]; then
      matched=true
    fi
  done
  [[ "$matched" == true ]] || fail "Unknown service: $TARGET_SERVICE"
}

start_postgres() {
  log "Starting PostgreSQL..."
  compose up -d postgres >/dev/null

  log "Waiting for PostgreSQL..."
  until compose exec -T postgres pg_isready -U "$POSTGRES_USER_VALUE" -d learngrid >/dev/null 2>&1; do
    sleep 1
  done
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
  export KAFKA_ENABLED=false
  export KAFKA_BOOTSTRAP_SERVERS="$KAFKA_BOOTSTRAP_SERVERS_VALUE"
}

selected_services() {
  local service
  local database_name
  local port
  for service_config in "${SERVICES[@]}"; do
    IFS=":" read -r service database_name port <<<"$service_config"
    if [[ -z "$TARGET_SERVICE" || "$TARGET_SERVICE" == "$service" ]]; then
      printf '%s\n' "$service_config"
    fi
  done
}

run_service_seed() {
  local service="$1"
  local database_name="$2"
  local port="$3"
  local service_dir="$BACKEND_ROOT/$service"
  local command_args=(--manifest "$MANIFEST")

  if [[ "$DRY_RUN" == true ]]; then
    command_args+=(--dry-run)
  fi
  if [[ "$RESET_SAMPLE_DATA" == true ]]; then
    command_args+=(--reset-sample-data)
  fi

  if [[ "$DRY_RUN" != true ]]; then
    ensure_database "$database_name"
  fi
  (
    cd "$service_dir"
    export_backend_env "$database_name" "$port"
    if [[ "$DRY_RUN" != true && "$SKIP_MIGRATIONS" != true ]]; then
      log "Running migrations for $service..."
      "$POETRY_BIN" run python manage.py migrate --noinput
    fi
    log "Seeding $service..."
    "$POETRY_BIN" run python manage.py seed_sample_data "${command_args[@]}"
  )
}

main() {
  parse_args "$@"
  preflight
  if [[ "$DRY_RUN" != true ]]; then
    start_postgres
  fi

  local selected_service_configs=()
  local service_config
  local service
  local database_name
  local port

  mapfile -t selected_service_configs < <(selected_services)
  for service_config in "${selected_service_configs[@]}"; do
    [[ -n "$service_config" ]] || continue
    IFS=":" read -r service database_name port <<<"$service_config"
    run_service_seed "$service" "$database_name" "$port"
  done

  log "Sample data seed complete."
}

main "$@"
