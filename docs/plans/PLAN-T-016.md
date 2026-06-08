# T-016 Certificates Implementation Plan

## Summary
Implement `T-016` in `grading-service`. Certificates will be auto-issued when a student is eligible, using course completion from `progress-service` plus published grade results from `grading_db`. Certificate asset generation remains out of scope; certificates may store an optional `certificate_asset_id` UUID and validate it through content-service when supplied.

## Key Changes
- Add grading models and migration for:
  - `CertificateEligibility` mapped to `certificate_eligibility`.
  - `Certificate` mapped to `certificates`.
  - Unique eligibility per `student_profile_id + course_id`.
  - Unique certificate per eligibility and unique public `certificate_number`.
  - `revoked_at` timestamp for revocation instead of deleting certificates.

- Add grading-service settings:
  - `PROGRESS_SERVICE_BASE_URL=http://127.0.0.1:8006`.
  - `CONTENT_SERVICE_BASE_URL=http://127.0.0.1:8004`.
  - `GRADING_CERTIFICATE_DEFAULT_PASS_PERCENT=70`.

- Add certificate calculation behavior:
  - `POST /api/grading/certificates/eligibility/evaluate/`.
  - Body: `student_profile_id`, `course_id`, optional `certificate_asset_id`.
  - Requires `grade.manage` scoped to the course.
  - Fetch course progress from `GET /api/progress/courses/?student_profile_id=<uuid>&course_id=<uuid>`.
  - Require course progress `status=completed` or `completion_percent >= 100`.
  - Calculate grade percent from published results for the same student/course using `sum(published_score) / sum(max_score) * 100`.
  - Use latest course-level grading rule `configuration.certificate_min_percent` when present; otherwise use `GRADING_CERTIFICATE_DEFAULT_PASS_PERCENT`.
  - If eligible, upsert eligibility, auto-create a certificate if one does not exist, generate a unique certificate number, optionally link `certificate_asset_id`, and emit `CertificateEligible`.
  - If not eligible, upsert eligibility with `eligible=false` and a stable reason such as `course_progress_missing`, `course_incomplete`, `published_results_missing`, or `grade_below_threshold`.

- Add certificate APIs under `/api/grading/certificates/`:
  - `GET /eligibility/`: list eligibility records with `student_profile_id`, `course_id`, and `eligible` filters; requires `grade.view`.
  - `GET /eligibility/<uuid>/`: read one eligibility record; requires `grade.view`.
  - `POST /eligibility/evaluate/`: evaluate and auto-issue when eligible; requires `grade.manage`.
  - `GET /`: list certificates with `student_profile_id`, `course_id`, and optional `include_revoked`; owning students see only their own non-revoked certificates by default, managers use `grade.view`.
  - `GET /<uuid>/`: read one certificate; owning student or scoped `grade.view`.
  - `PATCH /<uuid>/`: update optional `certificate_asset_id`; requires `grade.manage`.
  - `POST /<uuid>/revoke/`: set `revoked_at`; requires `grade.manage`.
  - Certificate responses include `valid=true` only when `revoked_at` is null.

- Add certificate internals:
  - Serializers for eligibility evaluation, eligibility records, certificate records, asset linking, and revocation.
  - Selectors for filtered eligibility/certificate reads.
  - Service functions for progress lookup, content asset validation, eligibility calculation, certificate number generation, auto-issue idempotency, event emission, and revocation.
  - Certificate number format: `LG-YYYYMMDD-XXXXXXXXXX`, where the suffix is uppercase random alphanumeric and retried until unique.

- Update documentation:
  - Add `docs/db-design/DBD-016-certificates.md`.
  - Add `docs/api-design/API-016-certificates.md`.
  - Update `DATABASE_SCHEMA.md`, `DB_STRUCTURE.md`, `API_STRUCTURE.md`, `DEVELOPMENT.md`, `CHANGELOG.md`, `LIVING_DOCUMENT.md`, design README indexes, and `docs/tasks/T-016-certificates.md`.
  - Remove stale notes saying certificate tables are future T-016 scope.
  - Mark `T-016.01` through `T-016.08` complete only after verification passes.

## Test Plan
- Grading-service tests:
  - Eligible student with completed course progress and passing published grades gets `eligible=true`, `CertificateEligible`, and an auto-issued certificate.
  - Repeated eligibility evaluation is idempotent and does not create duplicate certificates.
  - Incomplete progress, missing progress, missing published results, and below-threshold grades produce `eligible=false` with stable reasons.
  - Course-level grading rule `configuration.certificate_min_percent` overrides the default pass threshold.
  - Certificate numbers are unique and follow the documented format.
  - Optional `certificate_asset_id` can be linked and is validated through content-service.
  - Revocation sets `revoked_at`, makes `valid=false`, and hides revoked certificates from default student lists.
  - Owning students can read their own valid certificates; unrelated students cannot.
  - `grade.view` and `grade.manage` are enforced for manager reads, evaluation, asset linking, and revocation.
  - Progress-service and content-service failures return controlled API errors.

- Verification commands:
  - `poetry run ruff check .`
  - `poetry run python manage.py check`
  - `poetry run python manage.py makemigrations --check --dry-run`
  - `poetry run pytest`

## Assumptions
- You selected automatic certificate issuance when eligibility is true.
- Eligibility requires both complete course progress and a passing published grade percentage.
- Certificate PDF/content generation is not implemented in T-016; only optional `certificate_asset_id` linking is added.
- Notification delivery for certificate events remains future `T-017`.
- Kafka transport remains future `T-020`; `CertificateEligible` is emitted through the existing local structured publisher pattern.
