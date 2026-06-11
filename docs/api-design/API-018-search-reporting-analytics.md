# API-018 Search, Reporting, And Analytics

Related task: [T-018](../tasks/T-018-search-reporting-analytics.md)  
Related spec: [SPEC-018](../specs/018-search-reporting-analytics.md)  
Related database design: [DBD-018](../db-design/DBD-018-search-reporting-analytics.md)

## API-018-001 Search APIs
| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `GET` | `/api/analytics/search/` | Search all permitted resource types | Resource-specific view permissions |
| `GET` | `/api/analytics/search/courses/` | Search course index records | `course.view` |
| `GET` | `/api/analytics/search/users/` | Search user index records | `profile.view` |
| `GET` | `/api/analytics/search/enrollments/` | Search enrollment index records | `enrollment.view` |
| `GET` | `/api/analytics/search/assessments/` | Search assessment index records | `assessment.view` |
| `GET` | `/api/analytics/search/submissions/` | Search submission index records | `submission.view` |

Query parameters: `q`, `institution_id`, `resource_type`, `status`, `course_id`,
`profile_type`, `assessment_type`, `submission_status`, `sort`, `page`, and `page_size`.
The combined search endpoint filters results to resource types allowed by auth-service.

## API-018-002 Index Management
| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `POST` | `/api/analytics/search/index-records/` | Upsert one search index record | `analytics.view` at institution/platform scope |
| `DELETE` | `/api/analytics/search/index-records/<resource_type>/<uuid>/` | Delete one search index record | Platform `analytics.view` |

Upsert body parameters: `resource_type`, `resource_id`, optional `institution_id`, `search_text`,
and optional `metadata`. Duplicate `resource_type + resource_id` updates the existing row.

## API-018-003 Aggregate And Metric APIs
| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `GET/POST` | `/api/analytics/dashboards/aggregates/` | List or upsert dashboard aggregate records | `analytics.view` |
| `GET/POST` | `/api/analytics/usage-metrics/` | List or create usage metric records | `analytics.view` |

Aggregate body parameters: `scope_type`, optional `scope_id`, `metric_date`, and `metrics`. Direct
API writes are limited to `platform` and `institution` aggregates. Usage metric body parameters:
`metric_name`, `metric_value`, optional `scope_type`, optional `scope_id`, `bucket_start_at`, and
`bucket_end_at`.

## API-018-004 Report Generation
| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `POST` | `/api/analytics/reports/generate/` | Generate and save a report snapshot | `analytics.view` |

Body parameters: optional `institution_id`, `report_type`, and optional `parameters`. Supported
report types are `active_users`, `enrollments`, `completion_rates`, `assessment_results`, and
`system_usage`. The response is a `report_snapshots` record whose `result_payload` contains a stable
`summary` object.

## API-018-005 Failure Behavior
Malformed filters return `400`. Missing or denied auth-service authorization returns `403`.
Reports are generated only from `analytics_db`; remote service outages do not affect report
calculation except for auth/profile authorization checks.
