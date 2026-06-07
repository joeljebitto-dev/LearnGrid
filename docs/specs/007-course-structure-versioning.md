# SPEC-007 Course Structure And Versioning

Source: [../SRD.pdf](../SRD.pdf)  
Related task: [T-007](../tasks/T-007-course-structure-versioning.md)  
Related schema: [course_db](../DATABASE_SCHEMA.md#course_db)

## Functional Requirements
- SPEC-007-FR-001 Courses shall be organized into modules.
- SPEC-007-FR-002 Modules shall be organized into lessons.
- SPEC-007-FR-003 Lessons may be organized into topics.
- SPEC-007-FR-004 Activities and assessments shall be attachable to the course structure.
- SPEC-007-FR-005 Courses and lessons shall support draft and published states.
- SPEC-007-FR-006 The system shall support future course versioning or content revision history.

## Non-Functional Requirements
- SPEC-007-NFR-001 Ordered course structures shall use deterministic position values.
- SPEC-007-NFR-002 Course structure updates shall be transactional inside course-service.
- SPEC-007-NFR-003 Published course views shall be cacheable and invalidated after harmful writes.

## Acceptance Criteria
- SPEC-007-AC-001 A course can contain ordered modules, lessons, and topics.
- SPEC-007-AC-002 Draft lessons are not visible to students until published.
- SPEC-007-AC-003 Future revision records can preserve course snapshots.
- SPEC-007-AC-004 Course publish events are produced according to [SPEC-020](020-kafka-eventing.md).
