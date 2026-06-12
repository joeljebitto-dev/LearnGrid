# DBD-008 Content Upload, Storage, And Access

Related task: [T-008](../tasks/T-008-content-upload-storage-access.md)  
Related spec: [SPEC-008](../specs/008-content-upload-storage-access.md)  
Canonical schema: [content_db](../DATABASE_SCHEMA.md#content_db)

## DBD-008-001 Scope
`content-service` owns content metadata, upload validation metadata, MinIO object metadata, content grants, signed access records, and content versions. [OD-002](../KNOWN_ISSUES.md#od-002-object-storage-selection) is resolved with MinIO as the canonical object storage provider.

## DBD-008-002 Tables
| Table ID | Table | Purpose |
| --- | --- | --- |
| `DB-CONTENT-001` | `content_assets` | Asset metadata and lifecycle |
| `DB-CONTENT-002` | `file_metadata` | Object storage metadata for uploaded files |
| `DB-CONTENT-003` | `content_permissions` | Profile/course/institution/role grants |
| `DB-CONTENT-004` | `signed_access_records` | Hashed signed access tokens and audit state |
| `DB-CONTENT-005` | `content_versions` | Version metadata |

## DBD-008-003 Notes
Uploads validate MIME type and size before metadata is stored. Direct metadata registration verifies that the MinIO object exists; presigned uploads store pending upload state in `content_assets.metadata` until completion; proxy uploads write to MinIO before creating DB metadata. `file_metadata.storage_provider` is always `minio`. Signed access stores only HMAC hashes of access tokens and resolves to short-lived MinIO presigned GET URLs. Content upload, publish, and delete events use the shared Kafka-capable event design in [EVT-020](../event-design/EVT-020-kafka-eventing.md).
