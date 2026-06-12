# Known Issues And Open Decisions

Source: [SRD.pdf](SRD.pdf)

## OD-001 API Gateway Selection
Status: Resolved.
Decision: Use Nginx as the LearnGrid API Gateway baseline for local development and gateway
configuration. Production deployment can reuse the same routing policy behind the future deployment
model selected under [OD-003](#od-003-deployment-model).
Related spec: [SPEC-019](specs/019-api-gateway.md).  
Related task: [T-019](tasks/T-019-api-gateway.md).

## OD-002 Object Storage Selection
Status: Resolved.
Decision: Use MinIO as the canonical object storage provider for local, staging, and production deployments.
Notes: S3 or other providers require a future explicit architecture decision. Production MinIO must be durable, clustered, or managed rather than the local Docker container.
Related spec: [SPEC-008](specs/008-content-upload-storage-access.md).
Related task: [T-008](tasks/T-008-content-upload-storage-access.md).

## OD-003 Deployment Model
Status: Resolved.
Decision: Use on-prem Kubernetes as the LearnGrid deployment model. Application images are built
and pushed to GHCR, then deployed to staging and production clusters with Helm through GitHub
Actions kubeconfig secrets. PostgreSQL, Redis, Kafka, MinIO, and the Grafana observability stack run
inside the on-prem cluster.
Related spec: [SPEC-023](specs/023-ci-cd-deployment-observability.md).  
Related task: [T-023](tasks/T-023-ci-cd-deployment-observability.md).

## OD-004 Authentication Model
Status: Resolved.
Decision: Use generic OAuth2/OIDC SSO as an optional login path alongside the existing JWT
email/password baseline. OIDC links only to existing active accounts by verified email or an
existing `issuer + subject` external identity; it does not create accounts, profiles, or roles.
Related specs: [SPEC-001](specs/001-authentication-lifecycle.md), [SPEC-002](specs/002-token-session-security.md).  
Related tasks: [T-001](tasks/T-001-project-setup.md), [T-002](tasks/T-002-token-session-security.md).

## OD-005 Analytics Storage
Status: Resolved.
Decision: Keep PostgreSQL `analytics_db` as the LearnGrid analytics, search-index, dashboard, and
reporting store for the implemented platform scope. ClickHouse or an external warehouse can be
reconsidered only after real scale evidence requires it.
Related spec: [SPEC-018](specs/018-search-reporting-analytics.md).  
Related task: [T-018](tasks/T-018-search-reporting-analytics.md).

## OD-006 Video Delivery Strategy
Status: Resolved.
Decision: Use MinIO signed URLs for video delivery. Content-service issues short-lived signed URLs
after authorization and signed-access validation; CDN or streaming-server delivery remains a future
optimization, not the current baseline.
Related spec: [SPEC-008](specs/008-content-upload-storage-access.md).  
Related task: [T-008](tasks/T-008-content-upload-storage-access.md).
