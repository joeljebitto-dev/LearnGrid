# API-013 Quiz Attempts And Exams

Related task: [T-013](../tasks/T-013-quiz-attempts-exams.md)  
Related spec: [SPEC-013](../specs/013-quiz-attempts-exams.md)  
Related database design: [DBD-013](../db-design/DBD-013-quiz-attempts-exams.md)

## API-013-001 Endpoints
| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `POST` | `/api/assessments/<uuid>/attempts/start/` | Start a quiz/exam attempt | `assessment.view`, current student profile, and active enrollment |
| `GET` | `/api/assessments/attempts/<uuid>/` | Read an attempt with ordered questions | Attempt owner with `assessment.view`, or manager |
| `PUT` | `/api/assessments/attempts/<uuid>/answers/` | Upsert durable answer payloads | Attempt owner with `assessment.view` |
| `POST` | `/api/assessments/attempts/<uuid>/submit/` | Submit an attempt and emit `QuizSubmitted` | Attempt owner with `assessment.view` |
| `POST` | `/api/assessments/attempts/<uuid>/auto-submit/` | Mark an attempt auto-submitted | Attempt owner with `assessment.view` |

## API-013-002 Response Shape
Attempt start/detail responses include:

- `attempt`: attempt identity, student profile UUID, attempt number, status, timestamps, score, and saved answers.
- `questions`: ordered student-facing question objects with `id`, `question_type`, `prompt`, `choices`, and `points`.
- `deadline_at`: computed from quiz time limit and assessment end window.

Student question responses never include `correct_answer`.

## API-013-003 Behavior
Attempt start enforces published status, availability windows, active enrollment, max attempts, and question availability. Randomized question order is persisted in `submission_audit_logs` and reused on later reads. Answer saves after expiry auto-submit when quiz `auto_submit` is enabled. Objective answers are scored locally, and grading-service consumes the grading-safe source endpoint documented in [API-015](API-015-grading-results-audit.md).
