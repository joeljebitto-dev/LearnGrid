from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SERVICES = [
    "auth-service",
    "user-service",
    "course-service",
    "content-service",
    "enrollment-service",
    "progress-service",
    "assessment-service",
    "grading-service",
    "notification-service",
    "analytics-service",
]


def test_all_services_require_production_secrets_and_secure_defaults():
    for service in SERVICES:
        production = (
            ROOT / "backend" / "services" / service / "config" / "settings" / "production.py"
        ).read_text(encoding="utf-8")

        assert "require_production_env(REQUIRED_PRODUCTION_ENV)" in production
        assert '"DJANGO_SECRET_KEY"' in production
        assert '"DATABASE_URL"' in production
        assert '"DJANGO_ALLOWED_HOSTS"' in production
        assert '"CORS_ALLOWED_ORIGINS"' in production
        assert "apply_django_security_defaults" in production
        assert "DEBUG = True" not in production


def test_security_baseline_kubernetes_templates_are_present():
    baseline = ROOT / "infrastructure" / "kubernetes" / "security-baseline"
    required_files = [
        "namespace.yaml",
        "service-accounts.yaml",
        "secrets.example.yaml",
        "configmap.example.yaml",
        "network-policies.yaml",
        "pod-security-context.yaml",
        "ingress-security.yaml",
    ]

    for file_name in required_files:
        assert (baseline / file_name).exists()

    namespace = (baseline / "namespace.yaml").read_text(encoding="utf-8")
    service_accounts = (baseline / "service-accounts.yaml").read_text(encoding="utf-8")
    network_policies = (baseline / "network-policies.yaml").read_text(encoding="utf-8")
    pod_context = (baseline / "pod-security-context.yaml").read_text(encoding="utf-8")
    ingress = (baseline / "ingress-security.yaml").read_text(encoding="utf-8")

    assert "pod-security.kubernetes.io/enforce: restricted" in namespace
    assert service_accounts.count("automountServiceAccountToken: false") >= len(SERVICES)
    assert "name: default-deny" in network_policies
    assert "runAsNonRoot: true" in pod_context
    assert "allowPrivilegeEscalation: false" in pod_context
    assert "nginx.ingress.kubernetes.io/force-ssl-redirect" in ingress
    assert "tls:" in ingress


def test_tracked_security_templates_do_not_contain_local_only_secret_values():
    scanned_paths = [
        ROOT / ".github" / "workflows" / "ci.yml",
        ROOT / "infrastructure" / "kubernetes" / "security-baseline",
    ]
    forbidden = [
        "insecure-local-change-me",
        "insecure-local-auth-service-change-me-32bytes",
        "learngrid-minio-secret",
    ]

    for path in scanned_paths:
        files = [path] if path.is_file() else list(path.rglob("*"))
        for file_path in files:
            if not file_path.is_file():
                continue
            text = file_path.read_text(encoding="utf-8")
            for value in forbidden:
                assert value not in text, f"{value} found in {file_path}"


def test_backup_restore_verification_script_documents_restore_flow():
    script = (ROOT / "scripts" / "verify-postgres-backup-restore.sh").read_text(
        encoding="utf-8"
    )

    assert "set -Eeuo pipefail" in script
    assert "pg_dump" in script
    assert "pg_restore" in script
    assert "dropdb" in script
    for database_name in [
        "auth_db",
        "user_db",
        "course_db",
        "content_db",
        "analytics_db",
    ]:
        assert database_name in script
