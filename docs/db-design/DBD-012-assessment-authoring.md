# DBD-012 Assessment Authoring

Related task: [T-012](../tasks/T-012-assessment-authoring.md)  
Related spec: [SPEC-012](../specs/012-assessment-authoring.md)  
Canonical schema: [assessment_db](../DATABASE_SCHEMA.md#assessment_db)

## DBD-012-001 Scope
`assessment-service` owns authoring data for reusable question banks, questions, quiz/exam/assignment shells, quiz configuration, ordered quiz questions, and assignment configuration. Assignment submission persistence is documented separately in [DBD-014](DBD-014-assignment-submissions.md).

## DBD-012-002 Tables
| Table ID | Table | Purpose |
| --- | --- | --- |
| `DB-ASSESS-001` | `question_banks` | Institution-owned reusable question collections |
| `DB-ASSESS-002` | `questions` | Reusable authored questions with choices and correct-answer metadata |
| `DB-ASSESS-003` | `assessments` | Shared shell for quizzes, exams, and assignments |
| `DB-ASSESS-004` | `quizzes` | Quiz/exam configuration including limits and randomization |
| `DB-ASSESS-005` | `quiz_questions` | Ordered question selection for quizzes and exams |
| `DB-ASSESS-008` | `assignments` | Assignment-specific due date, late submission, points, and resource metadata |

## DBD-012-003 Relationships And Constraints
- `questions.question_bank_id` is an in-service foreign key to `question_banks.id`.
- `quizzes.assessment_id` and `assignments.assessment_id` are one-to-one in-service foreign keys to `assessments.id`.
- `quiz_questions.quiz_id` and `quiz_questions.question_id` are in-service foreign keys.
- `course_id`, `lesson_id`, `created_by_profile_id`, `institution_id`, `owner_profile_id`, and `resource_asset_id` are cross-service UUID references without database-level foreign keys.
- Quiz question position and question membership are unique per quiz.

## DBD-012-004 Behavior Notes
- `question_banks`, `questions`, and `assessments` support soft delete through `deleted_at`.
- `coding` remains schema-reserved; the implemented API rejects it until a future coding-assessment task.
- Correct-answer metadata is stored for authoring and scoring, but student attempt responses omit it.
- Published quizzes and exams must have at least one linked question.
