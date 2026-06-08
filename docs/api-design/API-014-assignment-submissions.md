# API-014 Assignment Submissions

Related task: [T-014](../tasks/T-014-assignment-submissions.md)  
Related spec: [SPEC-014](../specs/014-assignment-submissions.md)  
Related database design: [DBD-014](../db-design/DBD-014-assignment-submissions.md)

## API-014-001 Endpoints
| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `GET` | `/api/assessments/assignments/<uuid>/submissions/` | List assignment submissions with `student_profile_id` and `status` filters | Own student submission or `submission.view` |
| `POST` | `/api/assessments/assignments/<uuid>/submissions/` | Save a draft or submit assignment work | Current student profile, `assessment.view`, active enrollment |
| `GET` | `/api/assessments/submissions/<uuid>/` | Read one assignment submission | Owner, `submission.view`, or `submission.manage` |
| `PATCH` | `/api/assessments/submissions/<uuid>/` | Update an own draft submission | Owner only |
| `POST` | `/api/assessments/submissions/<uuid>/submit/` | Finalize a draft and emit `AssignmentSubmitted` | Owner only |
| `POST` | `/api/assessments/submissions/<uuid>/mark-graded/` | Mark a submission graded after grading-service publication | `submission.manage` |

## API-014-002 Request Parameters
Create/update submission bodies accept `submission_text`, `attachment_asset_id`, and optional `submit`.
`submission_text` or `attachment_asset_id` is required on create. `attachment_asset_id` must exist in content-service.
`mark-graded` accepts optional `grade_record_id`.

## API-014-003 Response Shape
Submission responses include `id`, `assignment_id`, `assessment_id`, `course_id`, `student_profile_id`, `submission_text`, `attachment_asset_id`, `status`, `submitted_at`, `created_at`, and `updated_at`.

## API-014-004 Behavior
Submissions require a published assignment, a valid assessment availability window, current student profile context from user-service, and active course access from enrollment-service. Late submissions are rejected when the assignment disables late work; otherwise they are stored with status `late`. Remote content, user, enrollment, or course-service failures return controlled `502` errors where applicable.
