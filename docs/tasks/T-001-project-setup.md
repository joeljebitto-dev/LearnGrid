# T-001 Project Setup

Related spec: [SPEC-001](../specs/001-authentication-lifecycle.md)  
Related docs: [ARCHITECTURE.md](../ARCHITECTURE.md), [BACKEND_ARCHITECTURE.md](../BACKEND_ARCHITECTURE.md), [FRONTEND_ARCHITECTURE.md](../FRONTEND_ARCHITECTURE.md)

- [x] T-001.01 Create monorepo folders for frontend, backend services, infrastructure, tests, and docs.
- [x] T-001.02 Create React, TypeScript, Tailwind CSS frontend baseline.
- [x] T-001.03 Create Django REST Framework service baseline structure.
- [x] T-001.04 Add service settings split by environment.
- [x] T-001.05 Add Docker Compose baseline for local PostgreSQL and Redis.
- [x] T-001.06 Add initial CI pipeline for linting, type checking, and tests.
- [x] T-001.07 Add local developer documentation for setup and service startup.
- [x] T-001.08 Verify frontend and backend health checks run locally.

## Verification Notes
- Frontend lint, typecheck, tests, and production build passed.
- All ten backend services passed Ruff, Django checks, and pytest.
- All ten backend `GET /health/` endpoints were started locally and returned `{"service":"<service-name>","status":"ok"}`.
- Docker Compose baseline was added, but runtime startup could not be verified in this environment because the current user cannot access the Docker API socket.
