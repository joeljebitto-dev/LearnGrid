# T-008 Content Upload, Storage, And Access

Related spec: [SPEC-008](../specs/008-content-upload-storage-access.md)  
Related schema: [content_db](../DATABASE_SCHEMA.md#content_db)  
Resolved decision: [OD-002](../KNOWN_ISSUES.md#od-002-object-storage-selection) selects MinIO.
Resolved decision: [OD-006](../KNOWN_ISSUES.md#od-006-video-delivery-strategy)

- [x] T-008.01 Implement content asset and file metadata models.
- [x] T-008.02 Implement upload validation for file type and file size.
- [x] T-008.03 Integrate object storage after OD-002 is resolved.
- [x] T-008.04 Implement signed URL or authenticated download access.
- [x] T-008.05 Implement content permission checks.
- [x] T-008.06 Implement content version metadata.
- [x] T-008.07 Emit ContentUploaded, ContentPublished, and ContentDeleted events.
- [x] T-008.08 Add tests for valid upload, invalid upload, permission failure, and secure download.
