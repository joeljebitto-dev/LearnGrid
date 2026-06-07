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

3. For repeat starts after dependencies and migrations are already prepared:

```bash
pnpm dev:fast
```

4. Check service health:

```bash
curl http://127.0.0.1:8001/health/
```

The default runner starts PostgreSQL, Redis, MinIO, all backend services, and the frontend. Press
`Ctrl+C` to stop app processes. PostgreSQL, Redis, and MinIO stay running; stop them with:

```bash
pnpm dev:infra:down
```

More details are in [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).
