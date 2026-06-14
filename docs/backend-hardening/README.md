# Backend Hardening Evidence

Related task: [T-026](../tasks/T-026-backend-hardening-api-completion.md)
Related docs: [BACKEND_ARCHITECTURE.md](../BACKEND_ARCHITECTURE.md), [API_STRUCTURE.md](../API_STRUCTURE.md), [TESTING_STRATEGY.md](../TESTING_STRATEGY.md)

This folder records the repository-side evidence for backend hardening and API completion. It does
not replace the canonical API, schema, event, security, or deployment documents; it links those
sources into audit matrices that can be checked by reviewers and contract tests.

| Evidence ID | File | Purpose |
| --- | --- | --- |
| HARD-026-API | [HARD-026-api-completeness.md](HARD-026-api-completeness.md) | Service API completeness and pagination contract |
| HARD-026-AUTHZ | [HARD-026-authorization-tenant-isolation.md](HARD-026-authorization-tenant-isolation.md) | Authorization and tenant-isolation matrix |
| HARD-026-EVT | [HARD-026-eventing-async.md](HARD-026-eventing-async.md) | Kafka producer, consumer, retry, DLQ, replay, and idempotency coverage |
| HARD-026-RISK | [HARD-026-analytics-notifications-certificates-content.md](HARD-026-analytics-notifications-certificates-content.md) | High-risk workflow hardening evidence |
| HARD-026-MIG | [HARD-026-migrations-retention-compliance.md](HARD-026-migrations-retention-compliance.md) | Migration, backfill, rollback, retention, audit, and compliance policy |

Repository contract tests under [tests/contracts/](../../tests/contracts) verify the shared authz
dependency, remote authorization timeout setting, pagination conventions, migration reverse
operations, OpenAPI route inventory, and Kafka topic inventory.
