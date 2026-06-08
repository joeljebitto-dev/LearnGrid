# API-012 Assessment Authoring

Related task: [T-012](../tasks/T-012-assessment-authoring.md)  
Related spec: [SPEC-012](../specs/012-assessment-authoring.md)  
Related database design: [DBD-012](../db-design/DBD-012-assessment-authoring.md)

## API-012-001 Endpoints
| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `GET` | `/api/assessments/question-banks/` | Search question banks | `assessment.view` at institution/platform scope |
| `POST` | `/api/assessments/question-banks/` | Create a question bank | `assessment.manage` at institution scope |
| `GET/PATCH/DELETE` | `/api/assessments/question-banks/<uuid>/` | Read, update, or soft-delete a question bank | `assessment.view/manage` at bank institution |
| `GET` | `/api/assessments/question-banks/<uuid>/questions/` | Search bank questions | `assessment.view` at bank institution |
| `POST` | `/api/assessments/question-banks/<uuid>/questions/` | Create a question | `assessment.manage` at bank institution |
| `GET/PATCH/DELETE` | `/api/assessments/questions/<uuid>/` | Read, update, or soft-delete a question | `assessment.view/manage` at bank institution |
| `GET` | `/api/assessments/` | Search assessments | `assessment.view`; drafts require `assessment.manage` |
| `POST` | `/api/assessments/` | Create quiz, exam, or assignment shell | `assessment.manage` at course/institution scope |
| `GET/PATCH/DELETE` | `/api/assessments/<uuid>/` | Read, update, or archive assessment | Published read uses `assessment.view`; non-published read/write uses `assessment.manage` |
| `PUT` | `/api/assessments/<uuid>/questions/` | Replace ordered quiz/exam questions | `assessment.manage` |
| `POST` | `/api/assessments/<uuid>/publish/` | Publish assessment and emit `AssessmentPublished` | `assessment.manage` |
| `POST` | `/api/assessments/<uuid>/close/` | Close assessment and emit `AssessmentClosed` | `assessment.manage` |

## API-012-002 Payload Notes
Question payloads accept `question_type`, `prompt`, optional `choices`, optional `correct_answer`, `points`, and `status`. Supported question types are `multiple_choice`, `multiple_select`, `true_false`, `short_answer`, `essay`, and `file_upload`; `coding` returns a validation error.

Assessment create/update accepts `course_id`, optional `lesson_id`, `created_by_profile_id`, `assessment_type`, `title`, optional `description`, optional availability window, optional `quiz_config`, optional `assignment_config`, and optional ordered `questions`.

## API-012-003 Failure Behavior
Authoring resolves course metadata through course-service, then checks course-scope `assessment.manage` first and institution-scope `assessment.manage` second. Remote service failures return controlled API errors. Draft, closed, archived, or soft-deleted assessments are hidden from normal student discovery.
