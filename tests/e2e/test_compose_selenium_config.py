from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
DOCKER_COMPOSE = ROOT / "docker-compose.yml"


def test_compose_declares_visible_selenium_e2e_stack():
    compose_config = yaml.safe_load(DOCKER_COMPOSE.read_text(encoding="utf-8"))
    services = compose_config["services"]

    selenium = services["selenium-chrome"]
    runner = services["selenium-e2e"]

    assert selenium["profiles"] == ["e2e"]
    assert runner["profiles"] == ["e2e"]
    assert "${SELENIUM_WEBDRIVER_HOST_PORT:-4444}:4444" in selenium["ports"]
    assert "${SELENIUM_NOVNC_HOST_PORT:-7900}:7900" in selenium["ports"]
    assert selenium["environment"]["SE_START_XVFB"] == "true"
    assert selenium["environment"]["SE_VNC_PASSWORD"] == "${SELENIUM_VNC_PASSWORD:-secret}"
    assert runner["environment"]["SELENIUM_HEADLESS"] == "false"
    assert runner["environment"]["SELENIUM_REMOTE_URL"] == "http://selenium-chrome:4444/wd/hub"
    assert runner["environment"]["E2E_BASE_URL"] == "http://frontend-service:5173"
    assert "test_demo_credentials.py" in runner["environment"]["SELENIUM_PYTEST_ARGS"]
    assert "login rate-limit keys" in runner["command"]
