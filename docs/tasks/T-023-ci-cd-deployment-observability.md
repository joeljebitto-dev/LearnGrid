# T-023 CI/CD, Deployment, And Observability

Related spec: [SPEC-023](../specs/023-ci-cd-deployment-observability.md)  
Resolved decision: [OD-003](../KNOWN_ISSUES.md#od-003-deployment-model)

- [x] T-023.01 Resolve deployment model decision.
- [x] T-023.02 Add Dockerfile for each backend service.
- [x] T-023.03 Add `frontend-service` (`SVC-011`) production build and Nginx or CDN deployment path.
- [x] T-023.04 Add Kubernetes Deployment, Service, ConfigMap, Secret, and HPA for each service.
- [x] T-023.05 Add readiness and liveness probes for each service.
- [ ] T-023.06 Implement CI/CD stages from checkout through post-deployment smoke tests.
- [x] T-023.07 Configure Prometheus, Grafana, Loki or ELK, Jaeger or Tempo, Sentry, Kafka UI, PostgreSQL exporter, and Redis exporter.
- [x] T-023.08 Add dashboards for latency, errors, Kafka lag, PostgreSQL, Redis, pods, user activity, and assessment submissions.

Notes:
- `OD-003` is resolved to on-prem Kubernetes.
- Repository CI/CD, Helm charts, image build/scan/push jobs, staging deployment, production manual
  approval wiring, and smoke commands are implemented.
- `T-023.06` remains unchecked until a real staging GitHub Actions deployment with
  `KUBE_CONFIG_STAGING` succeeds, because deployment tasks require staging verification before
  production completion.
