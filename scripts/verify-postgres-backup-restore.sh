#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
POSTGRES_USER_VALUE="${POSTGRES_USER:-learngrid}"

DATABASES=(
  auth_db
  user_db
  course_db
  content_db
  enrollment_db
  progress_db
  assessment_db
  grading_db
  notification_db
  analytics_db
)

TMP_DIR="$(mktemp -d)"
RESTORE_DBS=()

cleanup() {
  local restore_db
  for restore_db in "${RESTORE_DBS[@]}"; do
    docker compose --project-directory "$ROOT_DIR" exec -T postgres \
      dropdb -U "$POSTGRES_USER_VALUE" --if-exists "$restore_db" >/dev/null 2>&1 || true
  done
  rm -rf "$TMP_DIR"
}

trap cleanup EXIT

wait_for_postgres() {
  until docker compose --project-directory "$ROOT_DIR" exec -T postgres \
    pg_isready -U "$POSTGRES_USER_VALUE" -d learngrid >/dev/null 2>&1; do
    sleep 1
  done
}

verify_database_restore() {
  local database_name="$1"
  local restore_db="${database_name}_restore_check_$(date +%s)_${RANDOM}"
  local dump_file="$TMP_DIR/${database_name}.dump"

  printf '[backup-restore] Dumping %s...\n' "$database_name"
  docker compose --project-directory "$ROOT_DIR" exec -T postgres \
    pg_dump -U "$POSTGRES_USER_VALUE" --format=custom --dbname="$database_name" >"$dump_file"

  printf '[backup-restore] Restoring %s into %s...\n' "$database_name" "$restore_db"
  docker compose --project-directory "$ROOT_DIR" exec -T postgres \
    createdb -U "$POSTGRES_USER_VALUE" "$restore_db"
  RESTORE_DBS+=("$restore_db")

  docker compose --project-directory "$ROOT_DIR" exec -T postgres \
    pg_restore -U "$POSTGRES_USER_VALUE" --dbname="$restore_db" --no-owner <"$dump_file"

  docker compose --project-directory "$ROOT_DIR" exec -T postgres \
    psql -U "$POSTGRES_USER_VALUE" -d "$restore_db" -tAc \
    "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';" >/dev/null
}

main() {
  wait_for_postgres
  local database_name
  for database_name in "${DATABASES[@]}"; do
    verify_database_restore "$database_name"
  done
  printf '[backup-restore] All service database restore checks passed.\n'
}

main "$@"
