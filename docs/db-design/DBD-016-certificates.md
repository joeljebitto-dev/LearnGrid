# DBD-016 Certificates

Related task: [T-016](../tasks/T-016-certificates.md)  
Related spec: [SPEC-016](../specs/016-certificates.md)  
Canonical schema: [grading_db](../DATABASE_SCHEMA.md#grading_db)

## DBD-016-001 Scope
`grading-service` now owns certificate eligibility decisions and issued certificate records. Eligibility is calculated from course completion in progress-service plus published grade results in `grading_db`. Certificate PDF generation remains outside T-016; certificates may store an optional `certificate_asset_id` UUID.

## DBD-016-002 Tables
| Table ID | Table | Purpose |
| --- | --- | --- |
| `DB-GRADE-006` | `certificate_eligibility` | One eligibility decision per student and course |
| `DB-GRADE-007` | `certificates` | Issued certificate record, certificate number, optional asset reference, and revocation timestamp |

## DBD-016-003 Relationships And Constraints
- `certificate_eligibility` is unique by `student_profile_id` and `course_id`.
- `certificates.certificate_eligibility_id` is an in-service one-to-one relationship.
- `certificates.certificate_number` is unique and generated as `LG-YYYYMMDD-XXXXXXXXXX`.
- `student_profile_id`, `course_id`, and `certificate_asset_id` are cross-service UUID references.

## DBD-016-004 Behavior Notes
- Eligibility reasons use stable values: `eligible`, `course_progress_missing`, `course_incomplete`, `published_results_missing`, and `grade_below_threshold`.
- Eligible evaluations auto-issue a certificate if one does not already exist.
- Revocation sets `revoked_at`; certificate records are not deleted.
- `CertificateEligible` is emitted through the shared Kafka-capable event publisher documented in [EVT-020](../event-design/EVT-020-kafka-eventing.md).
