# LearnGrid Helm Deployment

`T-023` resolves `OD-003` to on-prem Kubernetes and organizes deployment into three charts:

| Chart | Purpose |
| --- | --- |
| `learngrid-platform` | Namespaces and pod-security labels. |
| `learngrid-runtime` | In-cluster PostgreSQL, Redis, Kafka, MinIO, and Grafana-stack observability resources. |
| `learngrid-app` | LearnGrid backend, frontend, gateway, probes, HPAs, migration Jobs, and policies. |

Install order:

```bash
helm upgrade --install learngrid-platform infrastructure/helm/learngrid-platform --namespace learngrid-system --create-namespace
helm upgrade --install learngrid-runtime infrastructure/helm/learngrid-runtime --namespace learngrid --create-namespace
helm upgrade --install learngrid-app infrastructure/helm/learngrid-app --namespace learngrid --create-namespace
```

The runtime chart assumes CloudNativePG, Strimzi, and MinIO operator CRDs are available in the
cluster. The application chart consumes service secrets already created in the target namespace.
