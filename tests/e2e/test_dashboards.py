from __future__ import annotations

import os

import pytest

from .pages import DashboardPage, LoginCredentials, LoginPage


@pytest.fixture
def base_url() -> str:
    return os.getenv("E2E_BASE_URL", "http://127.0.0.1:5173")


@pytest.fixture
def driver():
    webdriver = pytest.importorskip("selenium.webdriver")
    exceptions = pytest.importorskip("selenium.common.exceptions")
    try:
        options = webdriver.FirefoxOptions()
        options.add_argument("-headless")
        browser = webdriver.Firefox(options=options)
    except exceptions.WebDriverException as exc:
        pytest.skip(f"Selenium browser driver is unavailable: {exc}")
    try:
        yield browser
    finally:
        browser.quit()


@pytest.mark.parametrize(
    ("email_env", "password_env", "expected_heading", "expected_nav"),
    [
        ("E2E_STUDENT_EMAIL", "E2E_STUDENT_PASSWORD", "Student Dashboard", "Student"),
        ("E2E_INSTRUCTOR_EMAIL", "E2E_INSTRUCTOR_PASSWORD", "Instructor Dashboard", "Instructor"),
        ("E2E_ADMIN_EMAIL", "E2E_ADMIN_PASSWORD", "Admin Dashboard", "Admin"),
    ],
)
def test_role_dashboard_smoke(
    driver,
    base_url: str,
    email_env: str,
    password_env: str,
    expected_heading: str,
    expected_nav: str,
):
    email = os.getenv(email_env)
    password = os.getenv(password_env)
    if not email or not password:
        pytest.skip(f"{email_env} and {password_env} are required for this smoke test.")

    LoginPage(driver, base_url).open().sign_in(LoginCredentials(email=email, password=password))

    dashboard = DashboardPage(driver, base_url)
    webdriver_wait = pytest.importorskip("selenium.webdriver.support.ui").WebDriverWait
    webdriver_wait(driver, 10).until(lambda _driver: expected_heading in dashboard.heading_text())
    assert expected_nav in dashboard.nav_labels()
