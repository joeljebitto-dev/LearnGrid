# T-023 CI/CD, Deployment, And Observability Plan

## Summary
Resolve `OD-003` as **on-prem Kubernetes** and implement a Helm-based production deployment path. Build/push all LearnGrid images to GHCR, deploy via GitHub Actions using staging/production kubeconfig secrets, run staging smoke verification, require manual production approval, and add Grafana-stack observability with in-cluster stateful infrastructure.

## Key Changes
- Resolve `OD-003` in docs as on-prem Kubernetes. Use GHCR image publishing, GitHub Actions environments, and kubeconfig secrets: `KUBE_CONFIG_STAGING` and `KUBE_CONFIG_PRODUCTION`.
- Add production containerization:
  - One Dockerfile per backend service, using repo-root build context so shared packages install correctly.
  - Add `gunicorn` runtime dependency to all backend services; containers run non-root and default to `config.settings.production`.
  - Add `frontend-service` multi-stage Dockerfile: pnpm/Vite build, Nginx static serving, `/healthz`, SPA fallback, default `VITE_API_BASE_URL=/api`.
  - Add an API gateway image/config path for Kubernetes service DNS.
- Add runtime health and observability interfaces:
  - Keep existing `/health/`; add `/health/live/` and `/health/ready/` to all backend services.
  - Readiness checks PostgreSQL connectivity; Redis/Kafka remain non-blocking unless a service’s critical startup config is invalid.
  - Add `/metrics/` via `django-prometheus`; scrape only inside the cluster.
  - Add JSON stdout logging, OpenTelemetry OTLP export to Tempo, and Sentry initialization from `SENTRY_DSN`.
  - Add frontend Sentry support through `VITE_SENTRY_DSN`.
- Add Helm deployment under `infrastructure/helm/`:
  - Use Helm, not Kustomize.
  - Split into installable charts for platform/runtime/app to avoid CRD timing issues.
  - Platform/runtime installs CloudNativePG for PostgreSQL with WAL/base backups to in-cluster MinIO, Strimzi Kafka, Redis HA, MinIO tenant, Kafka UI, Prometheus, Grafana, Loki, Tempo, Alloy/log collection, PostgreSQL exporter, Redis exporter, and Kafka lag exporter/metrics.
  - App chart creates Deployment, Service, ConfigMap, Secret reference, HPA, ServiceAccount, NetworkPolicy, probes, resource limits, migration Job, and PodDisruptionBudget for every backend service plus frontend and gateway.
  - Use restricted pod security, non-root containers, read-only root filesystem where compatible, and default-deny network policies with explicit service allowances.
- Add CI/CD:
  - Keep existing frontend/backend/shared/security gates.
  - Add Docker build matrix for all backend services, frontend, and gateway.
  - Scan images with Trivy.
  - Push SHA and branch tags to GHCR.
  - Run `helm dependency build`, `helm lint`, `helm template`, and Kubernetes schema validation.
  - Deploy staging with `helm upgrade --install`, wait for rollout, run gateway/backend health smoke tests and Selenium dashboard smoke tests.
  - Deploy production only through the GitHub `production` environment with manual approval, then run post-deploy smoke tests.
- Add dashboards and docs:
  - Provision Grafana datasources and dashboards for API latency/errors, Kafka lag, PostgreSQL, Redis, Kubernetes pods, user activity, and assessment submissions.
  - Add deployment and observability design docs, update `.env.example`, service env examples, development/backend/testing docs, changelog, living document, and `T-023` checklist.
  - Mark T-023 items complete only after the real staging deploy/smoke workflow succeeds.

## Public Interfaces
- New backend endpoints: `/health/live/`, `/health/ready/`, `/metrics/`.
- New frontend endpoint: `/healthz`.
- New deployment env/settings:
  - `PORT`, `GUNICORN_WORKERS`, `GUNICORN_TIMEOUT_SECONDS`
  - `SENTRY_DSN`, `SENTRY_ENVIRONMENT`, `SENTRY_TRACES_SAMPLE_RATE`
  - `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_SERVICE_NAME`
  - `VITE_API_BASE_URL`, `VITE_SENTRY_DSN`
- GitHub secrets/environments:
  - `KUBE_CONFIG_STAGING`, `KUBE_CONFIG_PRODUCTION`
  - optional smoke credentials: `E2E_STUDENT_EMAIL`, `E2E_STUDENT_PASSWORD`, `E2E_INSTRUCTOR_EMAIL`, `E2E_INSTRUCTOR_PASSWORD`, `E2E_ADMIN_EMAIL`, `E2E_ADMIN_PASSWORD`
  - production environment must require manual approval.

## Test Plan
- Backend: for every changed service, run `poetry lock`, Ruff, Django check, migration dry run, and pytest.
- Frontend: `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build`.
- Containers: build every backend image, frontend image, and gateway image; run at least one backend container smoke check with required production env supplied.
- Helm/Kubernetes: `helm dependency build`, `helm lint`, `helm template`, kube schema validation, and repo tests asserting each service has Deployment, Service, ConfigMap, Secret reference, HPA, probes, resources, and NetworkPolicy.
- Observability: tests/static checks for Prometheus scrape config, Grafana dashboard JSON validity, Loki/Tempo datasource provisioning, exporter manifests, and no tracked real secrets.
- CI/CD: validate workflow syntax, image scan steps, GHCR tags, staging deploy ordering, production environment gate, and post-deploy smoke commands.
- Deployment verification: run the staging GitHub Actions deployment against the provided on-prem staging cluster and confirm smoke tests pass before marking T-023 complete.

## Assumptions
- `OD-003` is resolved to on-prem Kubernetes.
- PostgreSQL PITR uses CloudNativePG with backups/WAL archiving to in-cluster MinIO.
- Sentry is configured by DSN; the Sentry server itself is not deployed by the LearnGrid Helm charts.
- GHCR and real staging/production kubeconfig secrets are available for verification.
- Full load testing remains T-024; T-023 adds only the optional CI/CD hook or smoke-sized load subset if credentials are present.
