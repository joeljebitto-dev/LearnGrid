# Backend Architecture

Source: [SRD.pdf](SRD.pdf)

## BE-001 Service Pattern
Each backend service is a Django REST Framework application with a clean internal structure:

```text
config/
apps/<domain>/models.py
apps/<domain>/serializers.py
apps/<domain>/views.py
apps/<domain>/services.py
apps/<domain>/selectors.py
apps/<domain>/permissions.py
apps/<domain>/urls.py
apps/<domain>/tests/
```

## BE-002 Layer Responsibilities
| Layer | Responsibility |
| --- | --- |
| `views.py` | HTTP request and response logic only |
| `serializers.py` | Validation and representation |
| `services.py` | Business workflows and write operations |
| `selectors.py` | Optimized read queries |
| `permissions.py` | Role and object-level authorization |
| `models.py` | Database schema and constraints |

## BE-003 API Standards
- Protected APIs must enforce backend authorization.
- List APIs must support pagination, filtering, and sorting.
- APIs must expose OpenAPI documentation.
- APIs must validate all inputs through serializers and schema checks.
- API responses must handle validation errors, permission failures, empty states, and retry-safe failures.
- Sensitive endpoints must use Redis-backed rate limiting.

## BE-004 Data Standards
- Follow [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) for table ownership and field-level schema.
- Use migrations for all schema changes.
- Use indexes for foreign keys, lookup fields, status fields, and frequent filters.
- Avoid N+1 queries with `select_related`, `prefetch_related`, optimized serializers, and selectors.
- Use transactions for multi-step writes inside a service boundary.

## BE-005 Event Standards
- Kafka events follow [SPEC-020](specs/020-kafka-eventing.md).
- Events include `event_id`, `event_type`, `aggregate_id`, `producer_service`, `timestamp`, `version`, `correlation_id`, and `payload`.
- Consumers are idempotent and use retry and dead-letter topics.

## BE-006 Related Tasks
See [TASKS.md](TASKS.md) for implementation checklists, especially [T-001](tasks/T-001-project-setup.md), [T-020](tasks/T-020-kafka-eventing.md), and [T-024](tasks/T-024-testing-quality.md).
