# Known Issues And Open Decisions

Source: [SRD.pdf](SRD.pdf)

## OD-001 API Gateway Selection
Status: Open.  
Decision needed: Select Kong, Traefik, Nginx, or equivalent API Gateway.  
Related spec: [SPEC-019](specs/019-api-gateway.md).  
Related task: [T-019](tasks/T-019-api-gateway.md).

## OD-002 Object Storage Selection
Status: Open.  
Decision needed: Select MinIO for on-premise, S3-compatible cloud storage, or another object storage provider.  
Related spec: [SPEC-008](specs/008-content-upload-storage-access.md).  
Related task: [T-008](tasks/T-008-content-upload-storage-access.md).

## OD-003 Deployment Model
Status: Open.  
Decision needed: Select fully on-premise Kubernetes, cloud Kubernetes, or hybrid deployment.  
Related spec: [SPEC-023](specs/023-ci-cd-deployment-observability.md).  
Related task: [T-023](tasks/T-023-ci-cd-deployment-observability.md).

## OD-004 Authentication Model
Status: Open.  
Decision needed: Finalize JWT only, OAuth2, or SSO integration.  
Related specs: [SPEC-001](specs/001-authentication-lifecycle.md), [SPEC-002](specs/002-token-session-security.md).  
Related tasks: [T-001](tasks/T-001-project-setup.md), [T-002](tasks/T-002-token-session-security.md).

## OD-005 Analytics Storage
Status: Open.  
Decision needed: Select PostgreSQL reporting database, ClickHouse, or data warehouse.  
Related spec: [SPEC-018](specs/018-search-reporting-analytics.md).  
Related task: [T-018](tasks/T-018-search-reporting-analytics.md).

## OD-006 Video Delivery Strategy
Status: Open.  
Decision needed: Select direct object storage delivery, CDN delivery, or streaming server.  
Related spec: [SPEC-008](specs/008-content-upload-storage-access.md).  
Related task: [T-008](tasks/T-008-content-upload-storage-access.md).
