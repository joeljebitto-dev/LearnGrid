from __future__ import annotations

import os
import time

import pytest

from .pages import LoginCredentials


DEFAULT_DEMO_CREDENTIALS = {
    "admin": LoginCredentials(
        email="bot.admin@learngrid.local",
        password="BotAdmin123!",
    ),
    "institution_admin": LoginCredentials(
        email="bot.admin@learngrid.local",
        password="BotAdmin123!",
    ),
    "instructor": LoginCredentials(
        email="bot.instructor@learngrid.local",
        password="BotInstructor123!",
    ),
    "student": LoginCredentials(
        email="bot.student@learngrid.local",
        password="BotStudent123!",
    ),
    "super_admin": LoginCredentials(
        email="bot.superadmin@learngrid.local",
        password="BotSuperAdmin123!",
    ),
}


@pytest.fixture
def base_url() -> str:
    return os.getenv("E2E_BASE_URL", "http://127.0.0.1:5173")


def env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.lower() in {"1", "true", "yes", "on"}


def browser_options(webdriver, browser_name: str, *, headless: bool):
    if browser_name == "chrome":
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        return options

    if browser_name == "firefox":
        options = webdriver.FirefoxOptions()
        if headless:
            options.add_argument("-headless")
        return options

    pytest.skip(f"Unsupported Selenium browser: {browser_name}")


@pytest.fixture
def driver():
    webdriver = pytest.importorskip("selenium.webdriver")
    exceptions = pytest.importorskip("selenium.common.exceptions")
    remote_url = os.getenv("SELENIUM_REMOTE_URL")
    browser_name = os.getenv("SELENIUM_BROWSER", "chrome" if remote_url else "firefox").lower()
    headless = env_bool("SELENIUM_HEADLESS", default=remote_url is None)
    options = browser_options(webdriver, browser_name, headless=headless)

    try:
        if remote_url:
            browser = webdriver.Remote(command_executor=remote_url, options=options)
        elif browser_name == "chrome":
            browser = webdriver.Chrome(options=options)
        else:
            browser = webdriver.Firefox(options=options)
    except exceptions.WebDriverException as exc:
        pytest.skip(f"Selenium browser driver is unavailable: {exc}")

    browser.set_window_size(
        int(os.getenv("SELENIUM_WINDOW_WIDTH", "1440")),
        int(os.getenv("SELENIUM_WINDOW_HEIGHT", "1000")),
    )

    try:
        yield browser
    finally:
        quit_delay = float(os.getenv("E2E_DRIVER_QUIT_DELAY_SECONDS", "0"))
        if quit_delay > 0:
            time.sleep(quit_delay)
        browser.quit()


def credentials_for(role: str):
    email = os.getenv(f"E2E_{role.upper()}_EMAIL")
    password = os.getenv(f"E2E_{role.upper()}_PASSWORD")
    if email and password:
        return LoginCredentials(email=email, password=password)

    credentials = DEFAULT_DEMO_CREDENTIALS.get(role)
    if credentials:
        return credentials

    pytest.skip(f"E2E_{role.upper()}_EMAIL and E2E_{role.upper()}_PASSWORD are required.")
