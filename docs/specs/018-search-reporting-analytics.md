# SPEC-018 Search, Reporting, And Analytics

Source: [../SRD.pdf](../SRD.pdf)  
Related task: [T-018](../tasks/T-018-search-reporting-analytics.md)  
Related schema: [analytics_db](../DATABASE_SCHEMA.md#analytics_db)  
Resolved decision: [OD-005 Analytics Storage](../KNOWN_ISSUES.md#od-005-analytics-storage)

## Functional Requirements
- SPEC-018-FR-001 The system shall support searching courses.
- SPEC-018-FR-002 The system shall support searching users.
- SPEC-018-FR-003 The system shall support searching enrollments.
- SPEC-018-FR-004 The system shall support searching assessments.
- SPEC-018-FR-005 The system shall support searching submissions.
- SPEC-018-FR-006 The system shall provide admin reports for active users.
- SPEC-018-FR-007 The system shall provide admin reports for course enrollments.
- SPEC-018-FR-008 The system shall provide admin reports for completion rates.
- SPEC-018-FR-009 The system shall provide admin reports for assessment results.
- SPEC-018-FR-010 The system shall provide admin reports for system usage.

## Non-Functional Requirements
- SPEC-018-NFR-001 Heavy analytics queries shall not run against transactional databases.
- SPEC-018-NFR-002 Large-scale reports shall use a separate analytics database or reporting store.
- SPEC-018-NFR-003 Analytics consumers shall process Kafka events idempotently.
- SPEC-018-NFR-004 Search and reporting must enforce institution and role scope.

## Acceptance Criteria
- SPEC-018-AC-001 Admin users can run scoped reports.
- SPEC-018-AC-002 Search results include only permitted resources.
- SPEC-018-AC-003 Analytics event ingestion records event IDs for idempotency.
- SPEC-018-AC-004 Reporting does not require cross-service database joins.
