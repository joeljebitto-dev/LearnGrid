# API-008 Content Upload, Storage, And Access

Related task: [T-008](../tasks/T-008-content-upload-storage-access.md)  
Related spec: [SPEC-008](../specs/008-content-upload-storage-access.md)  
Related database design: [DBD-008](../db-design/DBD-008-content-upload-storage-access.md)

## API-008-001 Endpoints
| Method | Path | Purpose | Auth |
| --- | --- | --- | --- |
| `GET` | `/api/content/assets/` | Search content assets | `content.view` or `content.manage` |
| `POST` | `/api/content/assets/` | Register link metadata or existing MinIO object metadata | `content.manage` |
| `POST` | `/api/content/assets/uploads/presigned/` | Create draft asset and MinIO presigned PUT URL | `content.manage` |
| `POST` | `/api/content/assets/<uuid>/uploads/complete/` | Verify uploaded MinIO object and complete metadata | `content.manage` |
| `POST` | `/api/content/assets/uploads/proxy/` | Upload multipart file through content-service to MinIO | `content.manage` |
| `GET` | `/api/content/assets/<uuid>/` | Read one asset | `content.view` |
| `PATCH` | `/api/content/assets/<uuid>/` | Update asset metadata | `content.manage` |
| `DELETE` | `/api/content/assets/<uuid>/` | Soft-delete asset | `content.manage` |
| `POST` | `/api/content/assets/<uuid>/publish/` | Publish asset | `content.manage` |
| `GET/POST` | `/api/content/assets/<uuid>/permissions/` | List or create content grants | `content.manage` |
| `POST` | `/api/content/assets/<uuid>/access/` | Create signed access record | `content.view` plus content grant/owner |
| `GET` | `/api/content/download/<uuid>/?token=...` | Resolve signed access metadata | Signed token |
| `GET/POST` | `/api/content/assets/<uuid>/versions/` | List or create content versions | `content.manage` |

## API-008-002 Notes
OD-002 is resolved with MinIO as the only supported provider. Direct asset create accepts link
metadata or metadata for an object already present in MinIO. Presigned uploads return `upload_url`,
`upload_headers`, and `object_key`, then completion verifies object size and MIME type. Proxy
uploads stream multipart content through content-service into MinIO and record SHA-256 metadata.
Signed access returns a one-time internal access URL with a raw token while storing only a token
hash; resolving that token returns a short-lived MinIO presigned GET URL.
