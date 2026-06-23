# Docker Compose Full Dev Stack

## Summary
Add a Compose-native, hot-reload development stack so `docker compose up --build` runs LearnGrid end to end: infra, all Django services, Vite frontend, and API gateway. Keep the existing `pnpm dev` host-run workflow working.

## Key Changes
- Extend `docker-compose.yml` with:
  - `frontend-service` using `node:22-alpine`, bind-mounted repo source, named `node_modules`/pnpm store volumes, and `pnpm -C frontend dev --host 0.0.0.0 --port 5173`.
  - All 10 backend services built from existing Dockerfiles, bind-mounted service/shared source for hot reload, running `python manage.py migrate --noinput && python manage.py runserver 0.0.0.0:8000`.
  - Per-service host ports `8001` through `8010`, frontend port `5173`, gateway ports `8080` and `8443`.
  - Compose env using service DNS: `postgres`, `redis`, `kafka`, `minio`, and `http://auth-service:8000` style internal URLs.
  - Healthchecks and `depends_on` conditions for Postgres, Redis, MinIO init, Kafka init, backend services, frontend, and gateway.
- Add a Compose gateway config, e.g. `infrastructure/docker/nginx/compose.conf`, based on the current local gateway but routing to Compose service names and `frontend-service:5173`, with websocket upgrade support for Vite HMR.
- Preserve current host workflow by moving the existing host-proxy gateway to an `api-gateway-host` Compose service/profile and updating `scripts/run-dev.sh` to start/stop that service.
- Add a Compose cert-generation one-shot service so a clean `docker compose up` creates ignored local TLS files before Nginx starts.
- Update `frontend/vite.config.ts` so API proxy targets default to host ports but can be overridden in Compose with env vars like `LEARNGRID_AUTH_PROXY_TARGET=http://auth-service:8000`.
- Add an optional sample-data helper, likely `scripts/seed-sample-data-compose.sh`, that runs each service’s existing `seed_sample_data` management command inside the running Compose backend containers.

## Developer Interface
- Full containerized dev stack:

```bash
docker compose up --build
```

- Stop and remove stack:

```bash
docker compose down
```

- Optional demo data after the stack is healthy:

```bash
scripts/seed-sample-data-compose.sh
```

- Main URLs:
  - Frontend direct: `http://127.0.0.1:5173`
  - Gateway HTTP: `http://127.0.0.1:8080`
  - Gateway HTTPS: `https://127.0.0.1:8443`

## Test Plan
- Static/config checks:
  - `docker compose config`
  - `python -m pytest tests/gateway tests/contracts/test_sample_data_seed.py`
  - Add/update tests to assert the Compose gateway config uses service DNS and that compose declares all app services with healthchecks.
- Live smoke against Compose:
  - `docker compose up --build -d`
  - `curl http://127.0.0.1:5173`
  - `curl http://127.0.0.1:8001/health/` through `8010`
  - `curl -k https://127.0.0.1:8443/gateway/health`
  - `GATEWAY_BASE_URL=https://127.0.0.1:8443 GATEWAY_HTTP_URL=http://127.0.0.1:8080 python -m pytest tests/gateway`
  - `python -m pytest tests/integration`
  - `pnpm -C frontend test`
- Optional seeded journey smoke:
  - `scripts/seed-sample-data-compose.sh --reset-sample-data`
  - Run `tests/e2e` with the bot credentials from the sample manifest if local browser/driver dependencies are installed.

## Assumptions
- Compose should be a dev hot-reload stack, not the production static/Gunicorn-only stack.
- Tests run from the host against the Compose stack; no test-runner containers are added.
- Demo data is not seeded automatically on startup; it is an explicit optional command.
- Existing `pnpm dev`, `pnpm dev:fast`, and `pnpm dev:infra` remain supported.
