# DEPLOY-023 CI/CD, Deployment, And Observability

Related task: [T-023](../tasks/T-023-ci-cd-deployment-observability.md)  
Related spec: [SPEC-023](../specs/023-ci-cd-deployment-observability.md)

## Deployment Model
`OD-003` is resolved to on-prem Kubernetes. LearnGrid application images are built by GitHub
Actions, pushed to GHCR, and deployed to staging and production clusters through kubeconfig
secrets. Production deployment uses the GitHub `production` environment so manual approval is
enforced outside the workflow file.

## Images
- Backend images are built from the repository root with per-service Dockerfiles so shared path
  packages are available during Poetry install.
- Backend containers run `gunicorn config.wsgi:application`, default to
  `DJANGO_SETTINGS_MODULE=config.settings.production`, and expose port `8000`.
- `frontend-service` builds a Vite static bundle and serves it through Nginx on port `8080`.
- `api-gateway` uses a Kubernetes Nginx config with service-DNS upstreams and ingress-managed TLS.

## Helm Charts
Helm deployment is split into:

| Chart | Responsibility |
| --- | --- |
| `learngrid-platform` | Namespaces and restricted pod-security labels |
| `learngrid-runtime` | CloudNativePG PostgreSQL, MinIO, Strimzi Kafka, Redis, Kafka UI, Prometheus, Grafana, Loki, Tempo, Alloy, and exporters |
| `learngrid-app` | LearnGrid Deployments, Services, ConfigMaps, Secret references, HPAs, migration Jobs, probes, PDBs, Ingress, and NetworkPolicies |

The runtime chart expects CloudNativePG, Strimzi, and MinIO operator CRDs to be installed in the
cluster. PostgreSQL base backups and WAL archiving target in-cluster MinIO through CloudNativePG
`barmanObjectStore` configuration.

## CI/CD Gates
CI runs frontend checks, backend service checks, shared package checks, security/gateway checks,
deployment static tests, Helm lint/template/schema validation, image builds, Trivy scans, GHCR
pushes, staging deployment, staging smoke tests, production manual approval, production deployment,
and post-deploy smoke tests.

`scripts/verify-staging-release.sh` records rollout, gateway health, backend service health,
optional OpenAPI, and optional Selenium evidence. The manual
`.github/workflows/production-readiness.yml` workflow runs this script only when staging
kubeconfig and runtime credentials are available. `T-023.06` remains open until that real staging
evidence succeeds.
