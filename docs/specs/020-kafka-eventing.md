# SPEC-020 Kafka Eventing

Source: [../SRD.pdf](../SRD.pdf)  
Related task: [T-020](../tasks/T-020-kafka-eventing.md)  
Related schema: [analytics_db event facts](../DATABASE_SCHEMA.md#db-analytics-001-event_facts)

## Functional Requirements
- SPEC-020-FR-001 Kafka shall be used for asynchronous event-driven workflows.
- SPEC-020-FR-002 Topics shall include `user.events`, `course.events`, `enrollment.events`, `content.events`, `progress.events`, `assessment.events`, `grading.events`, `notification.events`, `audit.events`, and `analytics.events`.
- SPEC-020-FR-003 Events shall include `event_id`, `event_type`, `aggregate_id`, `producer_service`, `timestamp`, `version`, `correlation_id`, and `payload`.
- SPEC-020-FR-004 Kafka shall not be used for synchronous request-response queries.
- SPEC-020-FR-005 Event consumers shall be idempotent.

## Non-Functional Requirements
- SPEC-020-NFR-001 Kafka topics shall use partitions to support parallel consumers.
- SPEC-020-NFR-002 Failed events shall be retried using retry topics.
- SPEC-020-NFR-003 Poison messages shall move to dead-letter topics.
- SPEC-020-NFR-004 Consumer lag shall be monitored.

## Acceptance Criteria
- SPEC-020-AC-001 Enrollment, progress, assessment, grading, notification, audit, and analytics workflows publish or consume documented events.
- SPEC-020-AC-002 Consumers record processed event IDs or otherwise enforce idempotency.
- SPEC-020-AC-003 Retry and dead-letter behavior is tested.
- SPEC-020-AC-004 Consumer lag is visible in monitoring dashboards.
