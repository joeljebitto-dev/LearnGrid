from __future__ import annotations

import pytest

from .conftest import credentials_for
from .pages import DashboardPage, LoginPage


def wait_for_heading(driver, dashboard: DashboardPage, expected_heading: str):
    webdriver_wait = pytest.importorskip("selenium.webdriver.support.ui").WebDriverWait
    webdriver_wait(driver, 10).until(lambda _driver: expected_heading in dashboard.heading_text())


@pytest.mark.parametrize(
    ("role", "expected_heading"),
    [
        ("student", "Student Dashboard"),
        ("instructor", "Instructor Dashboard"),
        ("admin", "Admin Dashboard"),
        ("super_admin", "Admin Dashboard"),
    ],
)
def test_seeded_demo_username_password_login(
    driver,
    base_url: str,
    role: str,
    expected_heading: str,
):
    dashboard = LoginPage(driver, base_url).open().sign_in(credentials_for(role))

    wait_for_heading(driver, dashboard, expected_heading)
