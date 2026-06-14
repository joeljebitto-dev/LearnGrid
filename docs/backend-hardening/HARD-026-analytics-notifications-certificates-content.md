# HARD-026 High-Risk Workflow Hardening

Related task: [T-026](../tasks/T-026-backend-hardening-api-completion.md)
Related docs: [API_STRUCTURE.md](../API_STRUCTURE.md), [SECURITY.md](../SECURITY.md)

## HARD-026-RISK-001 Analytics

- Search, dashboard aggregate, usage metric, and report snapshot lists are paginated with
  `max_page_size=100`.
- Reports use `analytics_db` only and do not join across service databases.
- Empty dashboard aggregates return stable zero/empty payloads.
- Search authorization maps resource types to resource-specific view permissions before returning
  records.

## HARD-026-RISK-002 Notifications

- Templates and preferences are first-class records before delivery attempts are created.
- Event ingestion is idempotent by source event metadata.
- Read/unread endpoints update only recipient-owned notifications unless management permission is
  present.
- Delivery attempts are persisted and retry-safe; notification event handlers can be replayed from
  Kafka retry/DLQ topics.

## HARD-026-RISK-003 Certificates

- Eligibility is unique per `student_profile_id + course_id` and certificate issuance is idempotent
  per eligibility record.
- Revocation sets `revoked_at`; default student lists hide revoked certificates and responses compute
  `valid=false`.
- Optional `certificate_asset_id` is validated through content-service before linking.
- Owning students can read their certificates; unrelated students are denied; managers require
  scoped `grade.view` or `grade.manage`.

## HARD-026-RISK-004 Content

- Object keys are normalized and validated before MinIO interactions.
- File metadata enforces provider, MIME type, file extension, file size, checksum, and upload status.
- Optional malware scanning is fail-closed when enabled and scanner execution fails.
- Proxy upload failures clean up or avoid orphaned database records where possible; presigned
  completion verifies object existence, size, and content type before marking upload complete.

## HARD-026-RISK-005 Evidence

Service tests cover denial paths, empty responses, idempotency, upload validation, notification
preferences, certificate revocation, and analytics report/search filters. Repo-level security,
integration, contract, and load smoke checks are documented in [TESTING_STRATEGY.md](../TESTING_STRATEGY.md).
