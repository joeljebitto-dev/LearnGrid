# API-016 Certificates

Related task: [T-016](../tasks/T-016-certificates.md)  
Related spec: [SPEC-016](../specs/016-certificates.md)  
Related database design: [DBD-016](../db-design/DBD-016-certificates.md)

## API-016-001 Endpoints
| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `GET` | `/api/grading/certificates/eligibility/` | List eligibility records with `student_profile_id`, `course_id`, and `eligible` filters | `grade.view` |
| `GET` | `/api/grading/certificates/eligibility/<uuid>/` | Read one eligibility record | `grade.view` |
| `POST` | `/api/grading/certificates/eligibility/evaluate/` | Evaluate eligibility and auto-issue when eligible | `grade.manage` |
| `GET` | `/api/grading/certificates/` | List certificates with `student_profile_id`, `course_id`, and `include_revoked` filters | Owning student or `grade.view` |
| `GET` | `/api/grading/certificates/<uuid>/` | Read one certificate | Owning student or `grade.view` |
| `PATCH` | `/api/grading/certificates/<uuid>/` | Update optional `certificate_asset_id` | `grade.manage` |
| `POST` | `/api/grading/certificates/<uuid>/revoke/` | Set `revoked_at` | `grade.manage` |

## API-016-002 Request And Response Shape
Eligibility evaluation accepts `student_profile_id`, `course_id`, and optional `certificate_asset_id`. The response includes `eligibility`, `certificate`, `grade_percent`, and `threshold_percent`.

Certificate responses include `id`, `certificate_eligibility_id`, `student_profile_id`, `course_id`, `certificate_number`, `certificate_asset_id`, `issued_at`, `revoked_at`, and `valid`.

## API-016-003 Behavior
Eligibility requires completed course progress from progress-service and a passing published-grade percentage from `published_results` plus related `grade_records.max_score`. Course-level grading rule `configuration.certificate_min_percent` overrides `GRADING_CERTIFICATE_DEFAULT_PASS_PERCENT`; the default is `70`. Optional certificate asset UUIDs are validated through content-service. Revoked certificates have `valid=false` and are hidden from default student lists.
