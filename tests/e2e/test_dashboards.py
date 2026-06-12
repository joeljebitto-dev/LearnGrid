from __future__ import annotations

import pytest

from .conftest import credentials_for
from .pages import DashboardPage, LoginPage


def wait_for_heading(driver, dashboard: DashboardPage, expected_heading: str):
    webdriver_wait = pytest.importorskip("selenium.webdriver.support.ui").WebDriverWait
    webdriver_wait(driver, 10).until(lambda _driver: expected_heading in dashboard.heading_text())


@pytest.mark.parametrize(
    ("role", "expected_heading", "expected_nav"),
    [
        ("student", "Student Dashboard", "Student"),
        ("instructor", "Instructor Dashboard", "Instructor"),
        ("admin", "Admin Dashboard", "Admin"),
    ],
)
def test_role_dashboard_smoke(driver, base_url: str, role: str, expected_heading: str, expected_nav: str):
    dashboard = LoginPage(driver, base_url).open().sign_in(credentials_for(role))

    wait_for_heading(driver, dashboard, expected_heading)
    assert expected_nav in dashboard.nav_labels()


def test_logout_returns_user_to_login(driver, base_url: str):
    dashboard = LoginPage(driver, base_url).open().sign_in(credentials_for("student"))
    wait_for_heading(driver, dashboard, "Student Dashboard")

    dashboard.sign_out()

    webdriver_wait = pytest.importorskip("selenium.webdriver.support.ui").WebDriverWait
    webdriver_wait(driver, 10).until(lambda _driver: "/login" in driver.current_url)
    assert "Sign in" in driver.page_source
