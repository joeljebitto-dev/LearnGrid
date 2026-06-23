#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

SKIP_MIGRATIONS=false
DRY_RUN=false
RESET_SAMPLE_DATA=false
TARGET_SERVICE=""
MANIFEST="$ROOT_DIR/scripts/sample-data/learngrid-demo.json"

SERVICES=(
  "auth-service"
  "user-service"
  "content-service"
  "course-service"
  "enrollment-service"
  "progress-service"
  "assessment-service"
  "grading-service"
  "notification-service"
  "analytics-service"
)

usage() {
  cat <<'EOF'
Usage: scripts/seed-sample-data-compose.sh [options]

Seeds deterministic LearnGrid demo data through the running Docker Compose backend containers.
Start the full stack first with:

  docker compose up --build

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
  printf '[seed-compose] %s\n' "$*"
}

fail() {
  printf '[seed-compose] ERROR: %s\n' "$*" >&2
  exit 1
}

compose() {
  docker compose --project-directory "$ROOT_DIR" -f "$ROOT_DIR/docker-compose.yml" "$@"
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
        shift
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

selected_services() {
  local service
  local matched=false

  for service in "${SERVICES[@]}"; do
    if [[ -z "$TARGET_SERVICE" || "$TARGET_SERVICE" == "$service" ]]; then
      matched=true
      printf '%s\n' "$service"
    fi
  done

  [[ "$matched" == true ]] || fail "Unknown service: $TARGET_SERVICE"
}

preflight() {
  if ! command -v docker >/dev/null 2>&1; then
    fail "docker is required. Install Docker with the Compose plugin."
  fi
  if ! docker info >/dev/null 2>&1; then
    fail "Docker is not running or is not accessible for the current user."
  fi

  if [[ "$MANIFEST" != /* ]]; then
    MANIFEST="$ROOT_DIR/$MANIFEST"
  fi
  if [[ ! -f "$MANIFEST" ]]; then
    fail "Sample data manifest not found: $MANIFEST"
  fi
}

ensure_service_running() {
  local service="$1"

  if ! compose ps --status running --services | grep -Fxq "$service"; then
    fail "$service is not running. Start the full stack with: docker compose up --build"
  fi
}

container_manifest_path() {
  local service="$1"
  local default_manifest_dir="$ROOT_DIR/scripts/sample-data"

  case "$MANIFEST" in
    "$default_manifest_dir"/*)
      local relative_path="${MANIFEST#$default_manifest_dir/}"
      printf '/app/scripts/sample-data/%s' "$relative_path"
      ;;
    *)
      log "Copying custom manifest into $service..."
      compose cp "$MANIFEST" "$service:/tmp/learngrid-seed-manifest.json" >/dev/null
      printf '/tmp/learngrid-seed-manifest.json'
      ;;
  esac
}

run_service_seed() {
  local service="$1"
  local manifest_path
  local command_args=()

  ensure_service_running "$service"
  manifest_path="$(container_manifest_path "$service")"
  command_args=(--manifest "$manifest_path")

  if [[ "$DRY_RUN" == true ]]; then
    command_args+=(--dry-run)
  fi
  if [[ "$RESET_SAMPLE_DATA" == true ]]; then
    command_args+=(--reset-sample-data)
  fi

  if [[ "$DRY_RUN" != true && "$SKIP_MIGRATIONS" != true ]]; then
    log "Running migrations for $service..."
    compose exec -T "$service" python manage.py migrate --noinput
  fi

  log "Seeding $service..."
  compose exec -T "$service" python manage.py seed_sample_data "${command_args[@]}"
}

main() {
  parse_args "$@"
  preflight

  local selected=()
  local service
  mapfile -t selected < <(selected_services)

  for service in "${selected[@]}"; do
    [[ -n "$service" ]] || continue
    run_service_seed "$service"
  done

  log "Sample data seed complete."
}

main "$@"
