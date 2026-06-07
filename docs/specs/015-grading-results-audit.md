# SPEC-015 Grading, Results, And Audit

Source: [../SRD.pdf](../SRD.pdf)  
Related task: [T-015](../tasks/T-015-grading-results-audit.md)  
Related schema: [grading_db](../DATABASE_SCHEMA.md#grading_db)

## Functional Requirements
- SPEC-015-FR-001 The system shall calculate grades based on configured grading rules.
- SPEC-015-FR-002 The system shall support automated grading for objective questions.
- SPEC-015-FR-003 The system shall support manual grading for subjective submissions.
- SPEC-015-FR-004 Instructors shall review grades.
- SPEC-015-FR-005 Instructors shall override grades.
- SPEC-015-FR-006 Instructors shall publish grades.
- SPEC-015-FR-007 Students shall be notified when grades are published.
- SPEC-015-FR-008 The system shall maintain grade history and audit trails for changes.

## Non-Functional Requirements
- SPEC-015-NFR-001 Grade calculations shall be repeatable and auditable.
- SPEC-015-NFR-002 Grade publishing shall be transactional inside grading-service.
- SPEC-015-NFR-003 Grade access shall enforce object-level authorization.

## Acceptance Criteria
- SPEC-015-AC-001 Objective quiz submissions can produce calculated grades.
- SPEC-015-AC-002 Subjective submissions can enter manual review.
- SPEC-015-AC-003 Published grades become visible to the owning student.
- SPEC-015-AC-004 Grade changes create immutable history records.
- SPEC-015-AC-005 GradePublished events are emitted.
