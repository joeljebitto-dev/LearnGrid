# DBD-015 Grading, Results, And Audit

Related task: [T-015](../tasks/T-015-grading-results-audit.md)  
Related spec: [SPEC-015](../specs/015-grading-results-audit.md)  
Canonical schema: [grading_db](../DATABASE_SCHEMA.md#grading_db)

## DBD-015-001 Scope
`grading-service` now owns grading rules, grade records, manual reviews, immutable grade history, and published result snapshots. Certificate eligibility and certificate issuance remain future [T-016](../tasks/T-016-certificates.md) scope.

## DBD-015-002 Tables
| Table ID | Table | Purpose |
| --- | --- | --- |
| `DB-GRADE-001` | `grading_rules` | Course or assessment grading rule configuration |
| `DB-GRADE-002` | `grade_records` | Student grade records for quiz attempts or assignment submissions |
| `DB-GRADE-003` | `manual_reviews` | Manual grading workflow for subjective submissions |
| `DB-GRADE-004` | `grade_history` | Immutable audit trail for score changes |
| `DB-GRADE-005` | `published_results` | Published student-facing result snapshots |

## DBD-015-003 Relationships And Constraints
- `manual_reviews.grade_record_id`, `grade_history.grade_record_id`, and `published_results.grade_record_id` are in-service foreign keys to `grade_records.id`.
- `published_results.grade_record_id` is unique so each grade record has one published result snapshot.
- `course_id`, `assessment_id`, `submission_id`, `student_profile_id`, and reviewer/publisher profile IDs are cross-service UUID references.
- Grade record statuses are `draft`, `calculated`, `reviewed`, `published`, and `overridden`.

## DBD-015-004 Behavior Notes
- Automated quiz calculation uses grading-safe score metadata from assessment-service.
- Manual reviews and overrides always create `grade_history` rows.
- Overrides require a non-empty reason.
- Publishing writes `published_results`, marks the grade record `published`, emits `GradePublished`, and asks assessment-service to mark assignment submissions graded when applicable.
- `GradeCalculated` and `GradePublished` are emitted through the local structured event publisher; Kafka transport remains future [T-020](../tasks/T-020-kafka-eventing.md) scope.
