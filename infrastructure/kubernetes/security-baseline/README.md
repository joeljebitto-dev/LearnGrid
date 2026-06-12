# LearnGrid Security Baseline Templates

These manifests document the security baseline for future Kubernetes deployment work. They are
templates only; full Deployments, Services, HPAs, probes, and rollout wiring remain under T-023
after `OD-003 Deployment Model` is resolved.

Apply the ideas here to every LearnGrid workload:

- run in a namespace with the Kubernetes restricted pod security profile;
- use one ServiceAccount per workload and do not bind broad default permissions;
- mount secrets through Secret, SealedSecret, or Vault-managed references;
- deny pod-to-pod traffic by default and open only required service paths;
- terminate external traffic through TLS-enabled ingress with redirect and HSTS;
- run containers as non-root with privilege escalation disabled and a read-only root filesystem.
