# SPEC-011 Dashboards And Portals

Source: [../SRD.pdf](../SRD.pdf)  
Related task: [T-011](../tasks/T-011-dashboards-portals.md)  
Related docs: [FRONTEND_ARCHITECTURE.md](../FRONTEND_ARCHITECTURE.md), [analytics_db](../DATABASE_SCHEMA.md#analytics_db)

## Functional Requirements
- SPEC-011-FR-001 Students shall see active courses.
- SPEC-011-FR-002 Students shall see completed lessons.
- SPEC-011-FR-003 Students shall see pending assessments.
- SPEC-011-FR-004 Students shall see grades and upcoming deadlines.
- SPEC-011-FR-005 Instructors shall see learner engagement.
- SPEC-011-FR-006 Instructors shall see progress distribution.
- SPEC-011-FR-007 Instructors shall see assessment status.
- SPEC-011-FR-008 Admin users shall see institution and system usage views according to [SPEC-018](018-search-reporting-analytics.md).

## Non-Functional Requirements
- SPEC-011-NFR-001 Dashboards shall handle loading, error, empty, and retry states.
- SPEC-011-NFR-002 Dashboard server state shall use frontend caching.
- SPEC-011-NFR-003 Role-specific layouts shall not replace backend authorization.

## Acceptance Criteria
- SPEC-011-AC-001 A student sees only their own course and progress data.
- SPEC-011-AC-002 An instructor sees only assigned course data.
- SPEC-011-AC-003 An admin sees only permitted institution or platform dashboards.
- SPEC-011-AC-004 Dashboard APIs meet pagination and performance standards where list data is returned.
