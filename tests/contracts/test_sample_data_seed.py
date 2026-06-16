import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "scripts" / "sample-data" / "learngrid-demo.json"
SCRIPT = ROOT / "scripts" / "seed-sample-data.sh"

SERVICES = {
    "auth-service": "authentication",
    "user-service": "users",
    "content-service": "content",
    "course-service": "courses",
    "enrollment-service": "enrollments",
    "progress-service": "progress",
    "assessment-service": "assessments",
    "grading-service": "grading",
    "notification-service": "notifications",
    "analytics-service": "analytics",
}


def test_sample_manifest_has_deterministic_bot_credentials():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert manifest["seed_namespace"] == "learngrid-demo"
    assert manifest["institution"]["code"] == "BOT"
    assert set(manifest["accounts"]) == {
        "super_admin",
        "institution_admin",
        "instructor",
        "student",
    }

    for account in manifest["accounts"].values():
        assert account["email"].endswith("@learngrid.local")
        assert account["password"]
        assert account["id"]
        assert account["profile_id"]


def test_seed_script_exposes_safe_local_options():
    script = SCRIPT.read_text(encoding="utf-8")

    for flag in [
        "--skip-migrations",
        "--service",
        "--dry-run",
        "--reset-sample-data",
        "--manifest",
    ]:
        assert flag in script

    assert "KAFKA_ENABLED=false" in script
    assert "auth-service:auth_db:8001" in script
    assert script.index("auth-service:auth_db:8001") < script.index("analytics-service:analytics_db:8010")


def test_every_backend_service_has_seed_management_command():
    for service, app_name in SERVICES.items():
        command = (
            ROOT
            / "backend"
            / "services"
            / service
            / "apps"
            / app_name
            / "management"
            / "commands"
            / "seed_sample_data.py"
        )
        assert command.exists(), f"Missing seed command for {service}"

