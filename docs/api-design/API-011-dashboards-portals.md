# API-011 Dashboards And Portals

Related task: [T-011](../tasks/T-011-dashboards-portals.md)  
Related spec: [SPEC-011](../specs/011-dashboards-portals.md)  
Related database design: [DBD-011](../db-design/DBD-011-dashboards-portals.md)

## API-011-001 Frontend Routes
| Route | Purpose | Auth behavior |
| --- | --- | --- |
| `/login` | Token issue form | Public |
| `/dashboard` | Role redirect | Requires stored access token and successful session/profile lookup |
| `/dashboard/student` | Student portal | Requires `student` primary role |
| `/dashboard/instructor` | Instructor portal | Requires `instructor` or `teaching_assistant` primary role |
| `/dashboard/admin` | Admin portal | Requires `super_admin` or `institution_admin` primary role |
| `/dashboard/no-access` | Unsupported role state | Public fallback |

## API-011-002 Backend Endpoints
| Method | Path | Service | Purpose | Auth |
| --- | --- | --- | --- | --- |
| `GET` | `/api/auth/session/` | `auth-service` | Return account identity, active role assignments, and `primary_role` | Bearer access token |
| `GET` | `/api/users/profiles/me/` | `user-service` | Return current profile from JWT subject | Bearer access token plus `profile.view` |
| `GET` | `/api/analytics/dashboards/student/` | `analytics-service` | Return current student dashboard aggregate | Bearer access token; current profile must be student |
| `GET` | `/api/analytics/dashboards/instructor/` | `analytics-service` | Return current instructor dashboard aggregate | Bearer access token plus `analytics.view` |
| `GET` | `/api/analytics/dashboards/admin/?institution_id=<uuid>` | `analytics-service` | Return institution admin dashboard aggregate | Bearer access token plus institution-scoped `analytics.view` |
| `GET` | `/api/analytics/dashboards/admin/system/` | `analytics-service` | Return platform dashboard aggregate | Bearer access token plus platform `analytics.view` |
| `POST` | `/api/analytics/events/ingest/` | `analytics-service` | Store an analytics event idempotently | Bearer access token plus `analytics.view` |
| `GET` | `/api/analytics/reports/snapshots/` | `analytics-service` | List report snapshots | Bearer access token plus `analytics.view` |
| `POST` | `/api/analytics/reports/snapshots/` | `analytics-service` | Create report snapshot | Bearer access token plus `analytics.view` |

## API-011-003 Dashboard Shapes
Student dashboard response fields: `portal`, `profile`, `institution_id`, `aggregate`, `active_courses`, `completed_lessons`, `pending_assessments`, `grades`, `upcoming_deadlines`, and `summary`.

Instructor dashboard response fields: `portal`, `profile`, `institution_id`, `aggregate`, `learner_engagement`, `progress_distribution`, `assessment_status`, `course_summaries`, and `summary`.

Admin dashboard response fields: `portal`, `profile`, `institution_id`, `aggregate`, `active_users`, `enrollments`, `completion_rates`, `assessment_results`, `system_usage`, and `summary`.

If no `dashboard_aggregates` row exists, each dashboard returns `200` with `aggregate = null`, empty arrays, and zero summary values.

## API-011-004 Event And Report Payloads
`POST /api/analytics/events/ingest/` body parameters: `event_id`, `event_type`, `producer_service`, `aggregate_id`, optional `institution_id`, `occurred_at`, and optional `payload`. Duplicate `event_id` returns `200` with `created = false`.

`POST /api/analytics/reports/snapshots/` body parameters: optional `institution_id`, `report_type`, optional `parameters`, and optional `result_payload`. The service resolves `generated_by_profile_id` through `/api/users/profiles/me/`.

## API-011-005 Failure Behavior
Frontend protected routes redirect unauthenticated users to `/login`. Role mismatch redirects to the permitted portal or `/dashboard/no-access`. Backend authorization denial or remote auth/profile lookup failure denies access by default. Dashboard queries expose loading, error/retry, empty, and populated states through TanStack Query.
