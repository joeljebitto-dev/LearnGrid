# SPEC-008 Content Upload, Storage, And Access

Source: [../SRD.pdf](../SRD.pdf)  
Related task: [T-008](../tasks/T-008-content-upload-storage-access.md)  
Related schema: [content_db](../DATABASE_SCHEMA.md#content_db)  
Resolved decision: [OD-002](../KNOWN_ISSUES.md#od-002-object-storage-selection) selects MinIO.
Open decisions: [OD-006](../KNOWN_ISSUES.md#od-006-video-delivery-strategy)

## Functional Requirements
- SPEC-008-FR-001 Instructors shall upload and manage videos, PDFs, documents, images, links, and assignment resources.
- SPEC-008-FR-002 Content metadata shall be stored in PostgreSQL.
- SPEC-008-FR-003 Actual files shall be stored in MinIO object storage.
- SPEC-008-FR-004 Secure file access shall use signed URLs or authenticated download endpoints.
- SPEC-008-FR-005 Uploads shall validate file type, file size, and user permissions.
- SPEC-008-FR-006 The system shall optionally support future video transcoding and adaptive streaming.

## Non-Functional Requirements
- SPEC-008-NFR-001 Permanent academic records shall not be stored only in Redis.
- SPEC-008-NFR-002 File access shall be audited where needed.
- SPEC-008-NFR-003 Uploaded files may be scanned for malware when the security control is enabled.

## Acceptance Criteria
- SPEC-008-AC-001 A permitted instructor can upload a valid content asset.
- SPEC-008-AC-002 Invalid file type or size is rejected.
- SPEC-008-AC-003 Unauthorized users cannot download protected content.
- SPEC-008-AC-004 Content upload, publish, and delete events are produced according to [SPEC-020](020-kafka-eventing.md).
