# DBD-011 Dashboards And Portals

Related task: [T-011](../tasks/T-011-dashboards-portals.md)  
Related spec: [SPEC-011](../specs/011-dashboards-portals.md)  
Canonical schema: [analytics_db](../DATABASE_SCHEMA.md#analytics_db)

## DBD-011-001 Scope
`analytics-service` now owns the dashboard/report foundations used by student, instructor, and admin portals. PostgreSQL `analytics_db` is the current implementation store while [OD-005 Analytics Storage](../KNOWN_ISSUES.md#od-005-analytics-storage) remains open for larger-scale analytics storage.

## DBD-011-002 Tables
| Table ID | Table | Purpose |
| --- | --- | --- |
| `DB-ANALYTICS-001` | `event_facts` | Idempotent analytics event facts keyed by `event_id` |
| `DB-ANALYTICS-002` | `dashboard_aggregates` | Latest dashboard metrics by `student`, `instructor`, `institution`, `course`, or `platform` scope |
| `DB-ANALYTICS-003` | `report_snapshots` | Saved admin dashboard/report snapshots |
| `DB-ANALYTICS-004` | `usage_metrics` | Time-bucketed usage metrics |
| `DB-ANALYTICS-005` | `search_index_records` | Search index metadata reserved for broader T-018 search work |

## DBD-011-003 Relationships And Constraints
- Analytics records use cross-service UUID references for accounts, profiles, institutions, courses, and aggregates; no database-level foreign keys cross service boundaries.
- `event_facts.event_id` is unique for idempotent event ingestion.
- `dashboard_aggregates` is unique by `scope_type`, `scope_id`, and `metric_date`.
- `report_snapshots.generated_by_profile_id` stores the user-service profile UUID that created the snapshot when available.
- `search_index_records` is unique by `resource_type` and `resource_id`.

## DBD-011-004 Indexes
Implemented Django-compatible names:

| Table | Index or constraint |
| --- | --- |
| `event_facts` | `event_id` unique, `idx_event_facts_type_time`, `idx_event_facts_inst_time`, `idx_event_facts_aggregate_id` |
| `dashboard_aggregates` | `uq_dash_aggr_scope_date`, `idx_dash_aggr_scope_type` |
| `report_snapshots` | `idx_report_snap_inst_type`, `idx_report_snap_generated` |
| `usage_metrics` | `idx_usage_metrics_name_bucket`, `idx_usage_metrics_scope_bucket` |
| `search_index_records` | `uq_search_index_resource`, `idx_search_index_resource_type`, `idx_search_index_institution` |

## DBD-011-005 Notes
Dashboard metric payloads are stored in `JSONB` because each portal has a different aggregate shape.
The stable API shapes are documented in [API-011](../api-design/API-011-dashboards-portals.md).
`search_index_records` was introduced with the analytics schema foundation and is now used by
[T-018](../tasks/T-018-search-reporting-analytics.md), documented in
[DBD-018](DBD-018-search-reporting-analytics.md).
