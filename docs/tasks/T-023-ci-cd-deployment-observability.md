# T-023 CI/CD, Deployment, And Observability

Related spec: [SPEC-023](../specs/023-ci-cd-deployment-observability.md)  
Open decision: [OD-003](../KNOWN_ISSUES.md#od-003-deployment-model)

- [ ] T-023.01 Resolve deployment model decision.
- [ ] T-023.02 Add Dockerfile for each backend service.
- [ ] T-023.03 Add `frontend-service` (`SVC-011`) production build and Nginx or CDN deployment path.
- [ ] T-023.04 Add Kubernetes Deployment, Service, ConfigMap, Secret, and HPA for each service.
- [ ] T-023.05 Add readiness and liveness probes for each service.
- [ ] T-023.06 Implement CI/CD stages from checkout through post-deployment smoke tests.
- [ ] T-023.07 Configure Prometheus, Grafana, Loki or ELK, Jaeger or Tempo, Sentry, Kafka UI, PostgreSQL exporter, and Redis exporter.
- [ ] T-023.08 Add dashboards for latency, errors, Kafka lag, PostgreSQL, Redis, pods, user activity, and assessment submissions.
