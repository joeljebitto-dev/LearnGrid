# HARD-026 Migrations, Retention, Audit, And Compliance

Related task: [T-026](../tasks/T-026-backend-hardening-api-completion.md)
Related docs: [DATABASE_SCHEMA.md](../DATABASE_SCHEMA.md), [DB_STRUCTURE.md](../DB_STRUCTURE.md), [SECURITY.md](../SECURITY.md)

## HARD-026-MIG-001 Migration Policy

- Every schema change is represented by a Django migration in exactly one owning service database.
- Cross-service references are UUID fields, not cross-database foreign keys.
- Data migrations must define reverse behavior through a reverse function, `reverse_code`, or an
  explicit no-op when rollback cannot undo external effects.
- Backfills must be idempotent, restartable, and scoped to one service database at a time.
- Rollbacks must preserve externally visible identifiers and audit records unless a documented
  destructive maintenance window exists.

## HARD-026-MIG-002 Compatibility Policy

| Change type | Required approach |
| --- | --- |
| Add nullable column | Deploy migration before code writes; backfill; then tighten if needed |
| Add non-null column | Add nullable/default first; backfill; enforce non-null in a later migration |
| Rename column/table | Add new field and dual-read/write first; remove old field only after rollout |
| Enum/status expansion | Add new value and tests before producers emit it |
| Cross-service payload change | Version event/API payloads or keep old fields until consumers are updated |

## HARD-026-MIG-003 Retention And Audit Policy

| Record family | Retention/audit requirement |
| --- | --- |
| Auth tokens and login audit logs | Keep security audit records according to security policy; tokens store hashes only |
| RBAC and account lifecycle | Role assignment and authorization audit logs are durable sensitive-write records |
| User profiles and organizations | Soft-delete where documented; preserve historical foreign-key relationships |
| Course/content/enrollment/progress | Preserve learning history and object metadata required for audit and support |
| Assessment/grading/certificates | Preserve submissions, grading history, published results, and certificate revocation records |
| Notifications/analytics | Retain operational event and report records according to analytics retention policy |

## HARD-026-MIG-004 Test Evidence

- [test_t026_backend_hardening.py](../../tests/contracts/test_t026_backend_hardening.py) statically
  checks that data migrations using `RunPython` or `RunSQL` declare reverse operations.
- Service `makemigrations --check --dry-run` commands remain the source for schema drift checks.
