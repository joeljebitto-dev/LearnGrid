# SPEC-010 Learning Progress Tracking

Source: [../SRD.pdf](../SRD.pdf)  
Related task: [T-010](../tasks/T-010-learning-progress-tracking.md)  
Related schema: [progress_db](../DATABASE_SCHEMA.md#progress_db)

## Functional Requirements
- SPEC-010-FR-001 The system shall track lesson views.
- SPEC-010-FR-002 The system shall track video progress.
- SPEC-010-FR-003 The system shall track quiz attempts.
- SPEC-010-FR-004 The system shall track assignment submissions.
- SPEC-010-FR-005 The system shall track course completion percentage.
- SPEC-010-FR-006 Progress updates shall use Kafka asynchronously where appropriate.
- SPEC-010-FR-007 The system shall produce CourseProgressUpdated and CourseCompleted events.

## Non-Functional Requirements
- SPEC-010-NFR-001 Progress updates shall be idempotent.
- SPEC-010-NFR-002 Progress dashboards shall be cacheable where stale data is acceptable.
- SPEC-010-NFR-003 Course progress queries shall be indexed by student, course, and status.

## Acceptance Criteria
- SPEC-010-AC-001 Lesson view events update lesson progress.
- SPEC-010-AC-002 Video completion events update video and course progress.
- SPEC-010-AC-003 Quiz and assignment submissions update assessment progress.
- SPEC-010-AC-004 Course completion is recorded and published as an event.
