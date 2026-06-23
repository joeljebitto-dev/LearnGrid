# LearnGrid LMS

LearnGrid LMS is a web-based learning management platform scaffolded as a monorepo.

## Services
| ID | Service | Local port |
| --- | --- | --- |
| SVC-001 | auth-service | 8001 |
| SVC-002 | user-service | 8002 |
| SVC-003 | course-service | 8003 |
| SVC-004 | content-service | 8004 |
| SVC-005 | enrollment-service | 8005 |
| SVC-006 | progress-service | 8006 |
| SVC-007 | assessment-service | 8007 |
| SVC-008 | grading-service | 8008 |
| SVC-009 | notification-service | 8009 |
| SVC-010 | analytics-service | 8010 |
| SVC-011 | frontend-service | 5173 |

## Quick Start
1. Install required tools from [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).
2. Start the full local development stack:

```bash
pnpm dev
```

3. Or run the full hot-reload stack inside Docker Compose:

```bash
docker compose up --build
```

If another local app is using a default port, set the matching `*_HOST_PORT` variable before
starting Compose, for example `FRONTEND_HOST_PORT=15173 KAFKA_HOST_PORT=19092 docker compose up --build`.

4. For repeat starts after dependencies and migrations are already prepared:

```bash
pnpm dev:fast
```

5. Check service health:

```bash
curl http://127.0.0.1:8001/health/
curl -k https://127.0.0.1:8443/gateway/health
```

6. Add deterministic local demo data:

```bash
scripts/seed-sample-data.sh
```

When using the Docker Compose app stack, seed through the running service containers:

```bash
scripts/seed-sample-data-compose.sh
```

Run the visible Selenium GUI credential smoke through Compose:

```bash
docker compose --profile e2e up --abort-on-container-exit --exit-code-from selenium-e2e selenium-e2e
```

Open `http://127.0.0.1:7900` while tests run to watch the browser through noVNC. The default
viewer password is `secret`, and WebDriver is exposed on `http://127.0.0.1:4444`.

Demo bot credentials are listed in [LOCAL_BOT_USERS.txt](LOCAL_BOT_USERS.txt). The seed is
idempotent and safe to rerun; use `scripts/seed-sample-data.sh --reset-sample-data` to remove only
the seeded demo records before reseeding.

The default runner starts PostgreSQL, Redis, MinIO, all backend services, the frontend, and the
local Nginx API Gateway. The gateway is available at `http://127.0.0.1:8080` and
`https://127.0.0.1:8443`. Press `Ctrl+C` to stop app processes and the gateway. PostgreSQL, Redis,
and MinIO stay running; stop them with:

```bash
pnpm dev:infra:down
```

More details are in [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).
