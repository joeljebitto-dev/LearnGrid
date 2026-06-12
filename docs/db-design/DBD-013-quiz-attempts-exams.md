# DBD-013 Quiz Attempts And Exams

Related task: [T-013](../tasks/T-013-quiz-attempts-exams.md)  
Related spec: [SPEC-013](../specs/013-quiz-attempts-exams.md)  
Canonical schema: [assessment_db](../DATABASE_SCHEMA.md#assessment_db)

## DBD-013-001 Scope
`assessment-service` owns durable quiz/exam attempts, submitted answers, objective score snapshots, and submission audit logs. Grading records and published results are documented separately in [DBD-015](DBD-015-grading-results-audit.md).

## DBD-013-002 Tables
| Table ID | Table | Purpose |
| --- | --- | --- |
| `DB-ASSESS-006` | `quiz_attempts` | Student quiz/exam attempt lifecycle and score summary |
| `DB-ASSESS-007` | `quiz_answers` | Durable submitted answer payloads and per-question objective scores |
| `DB-ASSESS-010` | `submission_audit_logs` | Attempt start, submit, auto-submit, and randomized order audit metadata |

## DBD-013-003 Relationships And Constraints
- `quiz_attempts.quiz_id` is an in-service foreign key to `quizzes.id`.
- `quiz_answers.quiz_attempt_id` and `quiz_answers.question_id` are in-service foreign keys.
- `student_profile_id` is a cross-service UUID reference to user-service.
- Attempts are unique by quiz, student profile, and attempt number.
- Answers are unique by attempt and question.

## DBD-013-004 Behavior Notes
- Attempts enforce assessment windows, quiz `max_attempts`, and quiz `time_limit_seconds`.
- Randomized question order is persisted in `submission_audit_logs.metadata.question_order`.
- Answers are stored in PostgreSQL; Redis is not required for this baseline.
- Objective answers are scored locally so `quiz_attempts.score` is available before the later grading-service workflow.
- `QuizSubmitted` is emitted through the shared Kafka-capable event publisher documented in [EVT-020](../event-design/EVT-020-kafka-eventing.md).
