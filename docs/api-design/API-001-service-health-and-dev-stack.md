# API-001 Service Health And Dev Stack

Related task: [T-001 Project Setup](../tasks/T-001-project-setup.md)  
Related spec: [SPEC-001 Authentication Lifecycle](../specs/001-authentication-lifecycle.md)  
Related docs: [DEVELOPMENT.md](../DEVELOPMENT.md), [BACKEND_ARCHITECTURE.md](../BACKEND_ARCHITECTURE.md)

## Design Summary
T-001 introduced the runnable service baseline for the frontend and ten backend services. Backend services expose a public health endpoint. The root package scripts provide the local developer interface.

## Backend Health API
| Method | Path | Auth | Response |
| --- | --- | --- | --- |
| `GET` | `/health/` | Public | `{ "service": "<service-name>", "status": "ok" }` |

Implemented backend service ports:

| Service | Port |
| --- | --- |
| `auth-service` | `8001` |
| `user-service` | `8002` |
| `course-service` | `8003` |
| `content-service` | `8004` |
| `enrollment-service` | `8005` |
| `progress-service` | `8006` |
| `assessment-service` | `8007` |
| `grading-service` | `8008` |
| `notification-service` | `8009` |
| `analytics-service` | `8010` |

## Frontend Interface
- `SVC-011 frontend-service` runs through Vite at `http://127.0.0.1:5173`.
- The baseline app shell identifies LearnGrid LMS and is prepared for React Router, TanStack Query, Axios, React Hook Form, Zod, and Tailwind CSS.

## Developer Commands
| Command | Purpose |
| --- | --- |
| `pnpm dev` | Start full local stack with installs, migrations, health waits, and logs |
| `pnpm dev:fast` | Start full local stack while skipping installs and migrations |
| `pnpm dev:infra` | Start PostgreSQL and Redis only |
| `pnpm dev:infra:down` | Stop Docker Compose infrastructure |

## Failure Behavior
- Health endpoints are public and return service identity only.
- The run script fails early on missing required tools or local port conflicts.
- `Ctrl+C` stops spawned backend/frontend processes while leaving PostgreSQL and Redis running.

## Verification
T-001 verification covered frontend lint/typecheck/test/build, backend Ruff/check/pytest, backend health responses, and CI command alignment.
