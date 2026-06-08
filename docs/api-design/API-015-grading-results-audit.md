# API-015 Grading, Results, And Audit

Related task: [T-015](../tasks/T-015-grading-results-audit.md)  
Related spec: [SPEC-015](../specs/015-grading-results-audit.md)  
Related database design: [DBD-015](../db-design/DBD-015-grading-results-audit.md)

## API-015-001 Assessment Grading Source Endpoints
| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `GET` | `/api/assessments/grading/quiz-attempts/<uuid>/` | Return grading-safe quiz attempt metadata | `grade.manage` or equivalent scoped permission |
| `GET` | `/api/assessments/grading/assignment-submissions/<uuid>/` | Return grading-safe assignment submission metadata | `grade.manage` or equivalent scoped permission |

Source responses include `submission_type`, `submission_id`, `student_profile_id`, `course_id`, `assessment_id`, `score`, `max_score`, `status`, and `source_payload`.

## API-015-002 Grading-Service Endpoints
| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `GET/POST` | `/api/grading/rules/` | List or create grading rules | `grade.view` or `grade.manage` |
| `GET/PATCH` | `/api/grading/rules/<uuid>/` | Read or update one grading rule | `grade.view` or `grade.manage` |
| `GET` | `/api/grading/records/` | List grade records | `grade.view` |
| `GET` | `/api/grading/records/<uuid>/` | Read a grade record with history and reviews | `grade.view` |
| `POST` | `/api/grading/records/calculate/` | Calculate an objective quiz grade from assessment-service source data | `grade.manage` |
| `POST` | `/api/grading/records/manual-reviews/` | Create a pending manual review | `grade.manage` |
| `POST` | `/api/grading/manual-reviews/<uuid>/complete/` | Complete review with score and feedback | `grade.manage` |
| `POST` | `/api/grading/records/<uuid>/override/` | Override score with required `change_reason` | `grade.manage` |
| `POST` | `/api/grading/records/<uuid>/publish/` | Publish a result and emit `GradePublished` | `grade.manage` |
| `GET` | `/api/grading/results/` | List published results | Owning student or `grade.view` |
| `GET` | `/api/grading/results/<uuid>/` | Read one published result | Owning student or `grade.view` |

## API-015-003 Request Parameters
Rule bodies use `course_id`, optional `assessment_id`, `rule_type`, `configuration`, and `created_by_profile_id`.
Grade calculation accepts `submission_type=quiz_attempt`, `submission_id`, and optional `rule_id`.
Manual review creation accepts `submission_type`, `submission_id`, and optional `reviewer_profile_id`.
Manual review completion accepts `score` and optional `feedback`.
Override accepts `score`, optional `max_score`, and required `change_reason`.
Publish accepts optional `published_feedback`.

## API-015-004 Behavior
Grading-service resolves course metadata from course-service for scoped authorization, resolves current profile from user-service when needed, and fetches grading-safe source data from assessment-service. Remote service failures return controlled `502` errors. Published results are visible to the owning student and scoped grade managers; unpublished grade records remain manager-only.
