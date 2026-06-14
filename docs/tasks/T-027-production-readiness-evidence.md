# T-027 Production Readiness Evidence

Related spec: [SPEC-023](../specs/023-ci-cd-deployment-observability.md)
Related docs: [deployment-design/](../deployment-design/README.md), [observability-design/](../observability-design/README.md), [SECURITY.md](../SECURITY.md), [TESTING_STRATEGY.md](../TESTING_STRATEGY.md)
Related tasks: [T-023](T-023-ci-cd-deployment-observability.md), [T-024](T-024-testing-quality.md)

- [ ] T-027.01 Capture successful staging deployment evidence from the manual production-readiness workflow.
- [ ] T-027.02 Capture staging gateway, frontend, backend health, OpenAPI, and Selenium smoke evidence.
- [ ] T-027.03 Capture production deployment smoke evidence after approved production rollout.
- [ ] T-027.04 Validate observability dashboards for latency, errors, Kafka lag, PostgreSQL, Redis, MinIO, pods, and user activity.
- [ ] T-027.05 Define and verify alerting rules, escalation paths, ownership, and notification channels.
- [ ] T-027.06 Capture backup and restore drill evidence for PostgreSQL and object storage.
- [ ] T-027.07 Document disaster recovery procedures with recovery time, recovery point, and restore-order expectations.
- [ ] T-027.08 Validate production secrets management, rotation procedure, and absence of local placeholder secrets.
- [ ] T-027.09 Document the security scan remediation workflow for image, dependency, and static-analysis findings.
- [ ] T-027.10 Validate Kubernetes resource sizing, HPA behavior, pod disruption budgets, and capacity headroom.
- [ ] T-027.11 Run Kafka, Redis Sentinel, PostgreSQL, and MinIO failure-mode tests and record recovery evidence.
- [ ] T-027.12 Create runbooks for common operational incidents, including failed deploy, database outage, Redis failover, Kafka lag, object storage outage, and gateway errors.
- [ ] T-027.13 Complete the final release checklist after staging and production evidence is attached to the release record.

Notes:
- `T-023.06` remains unchecked until real staging CI/CD deployment and post-deployment smoke evidence succeeds.
- `T-024.08` remains unchecked until real staging performance, resource, Kafka lag, and autoscaling evidence succeeds.
- Do not mark this task complete from repository-static checks alone; it requires captured runtime evidence.
