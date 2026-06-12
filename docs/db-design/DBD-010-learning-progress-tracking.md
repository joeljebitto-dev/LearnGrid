# DBD-010 Learning Progress Tracking

Related task: [T-010](../tasks/T-010-learning-progress-tracking.md)  
Related spec: [SPEC-010](../specs/010-learning-progress-tracking.md)  
Canonical schema: [progress_db](../DATABASE_SCHEMA.md#progress_db)

## DBD-010-001 Scope
`progress-service` owns lesson, video, assessment, and course progress records plus idempotent consumed-event records.

## DBD-010-002 Tables
| Table ID | Table | Purpose |
| --- | --- | --- |
| `DB-PROGRESS-001` | `lesson_progress` | Lesson views and completion |
| `DB-PROGRESS-002` | `video_progress` | Video playback completion |
| `DB-PROGRESS-003` | `assessment_progress` | Quiz/exam/assignment progress |
| `DB-PROGRESS-004` | `course_progress` | Course progress summary |
| `DB-PROGRESS-005` | `progress_events` | Idempotency and audit for consumed events |

## DBD-010-003 Notes
Progress updates recalculate course progress from completed lessons and submitted/graded assessments. Event ingestion handles `LessonViewed`, `VideoCompleted`, `QuizSubmitted`, and `AssignmentSubmitted` idempotently. Course progress updates, completion events, and Kafka-consumed assessment events follow [EVT-020](../event-design/EVT-020-kafka-eventing.md).
