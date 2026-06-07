# SPEC-013 Quiz Attempts And Exams

Source: [../SRD.pdf](../SRD.pdf)  
Related task: [T-013](../tasks/T-013-quiz-attempts-exams.md)  
Related schema: [assessment_db](../DATABASE_SCHEMA.md#assessment_db)

## Functional Requirements
- SPEC-013-FR-001 The system shall support quiz attempts.
- SPEC-013-FR-002 The system shall support exam attempts.
- SPEC-013-FR-003 Attempts shall support time limits.
- SPEC-013-FR-004 Attempts shall support start and end windows.
- SPEC-013-FR-005 Attempts shall support randomization.
- SPEC-013-FR-006 Attempts shall support auto-submit.
- SPEC-013-FR-007 Objective answers shall be eligible for automated grading.

## Non-Functional Requirements
- SPEC-013-NFR-001 Attempt state may use Redis only for temporary workflow data.
- SPEC-013-NFR-002 Submitted answers shall be persisted durably in PostgreSQL.
- SPEC-013-NFR-003 Attempt submission shall be auditable.

## Acceptance Criteria
- SPEC-013-AC-001 An enrolled student can start an available quiz.
- SPEC-013-AC-002 A student cannot exceed configured attempt limits.
- SPEC-013-AC-003 Auto-submit persists the attempt when the time limit or window expires.
- SPEC-013-AC-004 QuizSubmitted events are emitted after successful submission.
