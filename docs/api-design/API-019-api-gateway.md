# API-019 API Gateway

Related task: [T-019](../tasks/T-019-api-gateway.md)  
Related spec: [SPEC-019](../specs/019-api-gateway.md)  
Resolved decision: [OD-001](../KNOWN_ISSUES.md#od-001-api-gateway-selection)

## API-019-001 Gateway Identity
LearnGrid uses Nginx as the local API Gateway baseline.

| URL | Purpose |
| --- | --- |
| `http://127.0.0.1:8080` | HTTP entrypoint; redirects to HTTPS |
| `https://127.0.0.1:8443` | HTTPS entrypoint with local self-signed TLS |
| `https://127.0.0.1:8443/gateway/health` | Gateway health response |

`scripts/generate-local-gateway-cert.sh` creates the untracked local TLS certificate and key.

## API-019-002 Routes
| Gateway prefix | Target |
| --- | --- |
| `/` | `frontend-service` on `5173` |
| `/api/auth/` | `auth-service` on `8001` |
| `/api/users/` | `user-service` on `8002` |
| `/api/courses/` | `course-service` on `8003` |
| `/api/content/` | `content-service` on `8004` |
| `/api/enrollments/` | `enrollment-service` on `8005` |
| `/api/progress/` | `progress-service` on `8006` |
| `/api/assessments/` | `assessment-service` on `8007` |
| `/api/grading/` | `grading-service` on `8008` |
| `/api/grades/` | Rewritten to `/api/grading/` on `grading-service` |
| `/api/notifications/` | `notification-service` on `8009` |
| `/api/analytics/` | `analytics-service` on `8010` |
| `/api/v1/...` | Rewritten to current `/api/...` routes |

## API-019-003 Gateway Controls
The Nginx gateway terminates TLS, emits JSON access logs with request IDs, forwards
`X-Request-ID`, enforces CORS for local origins, applies API rate limiting, and rejects requests
larger than `20m` with `413`.

## API-019-004 Development Behavior
`pnpm dev` and `pnpm dev:fast` start the gateway after backend and frontend services are healthy.
Direct service ports remain available for debugging. `Ctrl+C` stops backend/frontend processes and
the gateway container; PostgreSQL, Redis, and MinIO remain running.
