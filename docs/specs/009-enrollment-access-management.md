# SPEC-009 Enrollment And Access Management

Source: [../SRD.pdf](../SRD.pdf)  
Related task: [T-009](../tasks/T-009-enrollment-access-management.md)  
Related schema: [enrollment_db](../DATABASE_SCHEMA.md#enrollment_db)

## Functional Requirements
- SPEC-009-FR-001 Admins or instructors shall enroll students into courses.
- SPEC-009-FR-002 The system shall support individual enrollment.
- SPEC-009-FR-003 The system shall support batch-based enrollment.
- SPEC-009-FR-004 The system shall support cohort-based enrollment.
- SPEC-009-FR-005 Enrollments shall track active, completed, expired, cancelled, and suspended states.
- SPEC-009-FR-006 Enrollment changes shall publish Kafka events.
- SPEC-009-FR-007 Non-enrolled students shall be prevented from accessing protected courses.

## Non-Functional Requirements
- SPEC-009-NFR-001 Enrollment access checks shall be efficient and index-backed.
- SPEC-009-NFR-002 Enrollment status changes shall preserve history.
- SPEC-009-NFR-003 Enrollment event producers shall be idempotent where retry is possible.

## Acceptance Criteria
- SPEC-009-AC-001 A permitted admin or instructor can enroll an individual student.
- SPEC-009-AC-002 Batch and cohort jobs produce enrollment records or clear failure summaries.
- SPEC-009-AC-003 Course access is granted only for active enrollment.
- SPEC-009-AC-004 StudentEnrolled, StudentRemovedFromCourse, and CourseAccessExpired events are emitted.
