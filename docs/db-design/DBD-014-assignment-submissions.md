# DBD-014 Assignment Submissions

Related task: [T-014](../tasks/T-014-assignment-submissions.md)  
Related spec: [SPEC-014](../specs/014-assignment-submissions.md)  
Canonical schema: [assessment_db](../DATABASE_SCHEMA.md#assessment_db)

## DBD-014-001 Scope
`assessment-service` now owns assignment submission drafts, final submissions, late submissions, grading status handoff, and audit records. File upload bytes remain owned by content-service; assessment-service stores only the submitted `attachment_asset_id` UUID reference.

## DBD-014-002 Tables
| Table ID | Table | Purpose |
| --- | --- | --- |
| `DB-ASSESS-009` | `assignment_submissions` | One submission record per assignment and student profile |
| `DB-ASSESS-010` | `submission_audit_logs` | Draft save, submit, late submit, and graded status audit trail |

## DBD-014-003 Relationships And Constraints
- `assignment_submissions.assignment_id` is an in-service foreign key to `assignments.id`.
- `student_profile_id` is a cross-service UUID reference to user-service.
- `attachment_asset_id` is a cross-service UUID reference to content-service.
- `assignment_submissions` is unique by `assignment_id` and `student_profile_id`.
- Submission status values are `draft`, `submitted`, `late`, `withdrawn`, and `graded`.

## DBD-014-004 Behavior Notes
- Draft and final submission content is durably stored in PostgreSQL.
- Content attachments are validated through content-service before storing the UUID reference.
- Due date and late-submission policy are enforced before final submit.
- `submission_audit_logs` captures created, saved, submitted, late, and graded events for assignment submissions.
- `AssignmentSubmitted` is emitted through the shared Kafka-capable event publisher documented in [EVT-020](../event-design/EVT-020-kafka-eventing.md).
