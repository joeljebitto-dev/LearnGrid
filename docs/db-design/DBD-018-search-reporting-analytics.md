# DBD-018 Search, Reporting, And Analytics

Related task: [T-018](../tasks/T-018-search-reporting-analytics.md)  
Related spec: [SPEC-018](../specs/018-search-reporting-analytics.md)  
Canonical schema: [analytics_db](../DATABASE_SCHEMA.md#analytics_db)

## DBD-018-001 Scope
`analytics-service` implements generalized search, dashboard aggregate management, usage metrics,
and report generation using PostgreSQL `analytics_db`. [OD-005 Analytics Storage](../KNOWN_ISSUES.md#od-005-analytics-storage)
is resolved to PostgreSQL for the implemented analytics scope.

## DBD-018-002 Tables
| Table ID | Table | T-018 use |
| --- | --- | --- |
| `DB-ANALYTICS-001` | `event_facts` | Idempotent analytics event facts used by report generation |
| `DB-ANALYTICS-002` | `dashboard_aggregates` | Stored dashboard aggregate records for institution/platform reporting |
| `DB-ANALYTICS-003` | `report_snapshots` | Saved generated report payloads |
| `DB-ANALYTICS-004` | `usage_metrics` | Time-bucketed reporting metrics |
| `DB-ANALYTICS-005` | `search_index_records` | Search documents for courses, users, enrollments, assessments, and submissions |

## DBD-018-003 Search Index
`search_index_records` stores one row per indexed resource using the unique
`resource_type + resource_id` constraint. `institution_id` is a cross-service UUID reference used
for scoped search. `metadata` stores report/search facets such as `status`, `course_id`,
`profile_type`, `assessment_type`, and `submission_status`; human-readable searchable content stays
in `search_text`.

## DBD-018-004 Indexes And Constraints
- Existing indexes from [DBD-011](DBD-011-dashboards-portals.md) remain in use.
- T-018 adds PostgreSQL index `gin_search_index_search_text` on
  `to_tsvector('simple', search_text)` for search text acceleration.
- SQLite test runs skip the PostgreSQL GIN DDL while preserving model behavior.

## DBD-018-005 Reporting Boundary
Report generation reads only analytics-owned tables. It does not join or query transactional service
databases owned by auth, user, course, enrollment, progress, assessment, grading, notification, or
content services.
