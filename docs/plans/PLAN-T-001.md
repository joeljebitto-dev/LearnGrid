# T-001 Project Setup Implementation Plan

## Summary
Implement `T-001 Project Setup` as the first runnable monorepo scaffold for LearnGrid LMS. Use the selected defaults: all documented backend services, `pnpm` for the React frontend, Poetry for Django services, and GitHub Actions for CI.

## Key Changes
- Create monorepo structure:
  - `frontend/` for `SVC-011 frontend-service`
  - `backend/services/` for `auth-service`, `user-service`, `course-service`, `content-service`, `enrollment-service`, `progress-service`, `assessment-service`, `grading-service`, `notification-service`, and `analytics-service`
  - `infrastructure/docker/`, `tests/`, `.github/workflows/`, and root developer files
- Add React baseline in `frontend/`:
  - Vite, React, TypeScript, Tailwind CSS, React Router, TanStack Query, Axios, React Hook Form, Zod
  - Minimal app shell showing LearnGrid LMS service identity
  - `pnpm` scripts for `dev`, `build`, `lint`, `typecheck`, and `test`
- Add Django REST Framework baseline for every backend service:
  - `manage.py`, `config/`, split settings: `base.py`, `local.py`, `test.py`, `production.py`
  - Domain app structure matching `BACKEND_ARCHITECTURE.md`
  - Public `GET /health/` endpoint returning service name and `ok` status
  - Poetry config with Django, DRF, PostgreSQL driver, pytest, Ruff, and type-check tooling
- Add local infrastructure:
  - Root `docker-compose.yml` for PostgreSQL and Redis
  - PostgreSQL init SQL creating all service databases: `auth_db` through `analytics_db`
  - `.env.example` files documenting local ports and database URLs
- Add GitHub Actions CI:
  - Frontend job: install with `pnpm`, lint, typecheck, test, build
  - Backend job: install each service with Poetry, run lint/check/tests
- Add developer docs:
  - Root `README.md` or `docs/DEVELOPMENT.md` with setup, run, test, and health-check commands
  - Update `docs/tasks/T-001-project-setup.md` to mark `T-001.01` through `T-001.08` complete only after verification passes

## Interfaces
- Backend health API for each service:
  - `GET /health/`
  - Response: `{ "service": "<service-name>", "status": "ok" }`
- Frontend service:
  - `SVC-011 frontend-service`
  - Runs through Vite locally and builds to static assets for later Nginx/CDN deployment
- Local service ports:
  - Frontend: `5173`
  - Backend services: `8001` through `8010`, assigned in architecture order from `auth-service` to `analytics-service`
  - PostgreSQL: `5432`
  - Redis: `6379`

## Test Plan
- Verify `docker compose up -d postgres redis` starts infrastructure.
- Verify frontend:
  - `pnpm install`
  - `pnpm lint`
  - `pnpm typecheck`
  - `pnpm test`
  - `pnpm build`
- Verify every backend service:
  - `poetry install`
  - `poetry run python manage.py check`
  - `poetry run pytest`
  - `poetry run python manage.py runserver <port>` and `GET /health/`
- Verify GitHub Actions workflow syntax and that CI commands match local commands.

## Assumptions
- “All services” means all currently documented backend services `SVC-001` through `SVC-010`; `certificate-service` is not added because certificates currently remain under `grading-service`.
- T-001 creates health endpoints and scaffolding only; domain APIs, models, migrations, auth flows, dashboards, and deployment manifests remain in later tasks.
- Exact dependency patch versions will be locked by `pnpm-lock.yaml` and `poetry.lock` during implementation.
