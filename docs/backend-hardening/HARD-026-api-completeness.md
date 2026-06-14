# HARD-026 API Completeness

Related task: [T-026](../tasks/T-026-backend-hardening-api-completion.md)
Source API reference: [API_STRUCTURE.md](../API_STRUCTURE.md)
Related tests: [test_api_contracts.py](../../tests/contracts/test_api_contracts.py), [test_t026_backend_hardening.py](../../tests/contracts/test_t026_backend_hardening.py)

## HARD-026-API-001 Matrix

| Service | Implemented API areas | Contract evidence | Pagination and response rule |
| --- | --- | --- | --- |
| `auth-service` | Tokens, password reset, OIDC, session, accounts, RBAC, authorization checks | `EXPECTED_ROUTE_FRAGMENTS["auth-service"]` | Bounded RBAC catalog reads may return arrays; product collections are not exposed as open-ended catalog searches |
| `user-service` | Profiles, profile self lookup, institutions, departments, batches, import placeholder | `EXPECTED_ROUTE_FRAGMENTS["user-service"]` | Top-level lists use DRF pagination with `page_size` and `max_page_size=100` |
| `course-service` | Catalog, categories, tags, modules, lessons, topics, structure, revisions | `EXPECTED_ROUTE_FRAGMENTS["course-service"]` | Top-level catalog/category/tag lists are paginated; bounded course-structure children may return arrays |
| `content-service` | Assets, presigned upload, proxy upload, completion, permissions, signed access, download | `EXPECTED_ROUTE_FRAGMENTS["content-service"]` | Asset lists are paginated; signed access/download responses are single-resource workflows |
| `enrollment-service` | Enrollments, batch/cohort enrollment jobs, history, access grants, access checks | `EXPECTED_ROUTE_FRAGMENTS["enrollment-service"]` | Enrollment lists are paginated; history/access-check responses are bounded to one enrollment or request |
| `progress-service` | Lesson/video/assessment updates, course progress, progress events | `EXPECTED_ROUTE_FRAGMENTS["progress-service"]` | Course progress and event lists are paginated as of T-026 |
| `assessment-service` | Question banks, questions, assessments, attempts, assignment submissions, grading sources | `EXPECTED_ROUTE_FRAGMENTS["assessment-service"]` | Authoring and submission lists are paginated; attempt detail/answer writes are single-resource workflows |
| `grading-service` | Rules, records, reviews, publication, results, certificate eligibility, certificates | `EXPECTED_ROUTE_FRAGMENTS["grading-service"]` | Rule, record, result, eligibility, and certificate lists are paginated |
| `notification-service` | Templates, notifications, read state, preferences, deliveries, event ingestion | `EXPECTED_ROUTE_FRAGMENTS["notification-service"]` | Template, notification, preference, and delivery lists are paginated |
| `analytics-service` | Dashboards, event ingest, search, index records, aggregates, usage metrics, reports | `EXPECTED_ROUTE_FRAGMENTS["analytics-service"]` | Search/index/aggregate/usage/report lists are paginated; dashboard payloads are stable single-resource summaries |

## HARD-026-API-002 Common Behavior

- Protected endpoints require bearer JWT authentication and backend authorization.
- Remote authorization is deny-by-default, including auth-service network failures and timeouts.
- Collection and search endpoints use `count`, `next`, `previous`, and `results`.
- Common filters are `q`, `status`, `sort`, `page`, and `page_size` where the domain supports them.
- Empty collections return `200` with an empty `results` array; dashboard-style single-resource
  summaries return `200` with zeroed/empty portal payloads.
- Validation failures use DRF serializer errors and never create partial cross-service writes without
  an explicit compensation path.

## HARD-026-API-003 Follow-Up Handling

Any product API missing from [API_STRUCTURE.md](../API_STRUCTURE.md) is a feature-scope gap and
must be linked back to its owning task/spec. T-026 does not invent new product API contracts.
