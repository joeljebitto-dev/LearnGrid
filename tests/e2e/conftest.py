from __future__ import annotations

import os

import pytest


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


def credentials_for(role: str):
    email = os.getenv(f"E2E_{role.upper()}_EMAIL")
    password = os.getenv(f"E2E_{role.upper()}_PASSWORD")
    if not email or not password:
        pytest.skip(f"E2E_{role.upper()}_EMAIL and E2E_{role.upper()}_PASSWORD are required.")
    from .pages import LoginCredentials

    return LoginCredentials(email=email, password=password)
