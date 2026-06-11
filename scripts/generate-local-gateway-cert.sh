#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CERT_DIR="$ROOT_DIR/infrastructure/docker/nginx/certs"
CERT_FILE="$CERT_DIR/learngrid-local.crt"
KEY_FILE="$CERT_DIR/learngrid-local.key"

mkdir -p "$CERT_DIR"

if [[ -f "$CERT_FILE" && -f "$KEY_FILE" ]]; then
  exit 0
fi

if ! command -v openssl >/dev/null 2>&1; then
  printf '[gateway-cert] ERROR: openssl is required to generate local TLS certificates.\n' >&2
  exit 1
fi

openssl req \
  -x509 \
  -newkey rsa:2048 \
  -sha256 \
  -days 365 \
  -nodes \
  -keyout "$KEY_FILE" \
  -out "$CERT_FILE" \
  -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

chmod 600 "$KEY_FILE"
printf '[gateway-cert] Generated local gateway certificate at %s\n' "$CERT_FILE"
