from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LoginCredentials:
    email: str
    password: str


class LoginPage:
    def __init__(self, driver, base_url: str):
        self.driver = driver
        self.base_url = base_url.rstrip("/")

    def open(self):
        self.driver.get(f"{self.base_url}/login")
        return self

    def sign_in(self, credentials: LoginCredentials):
        email = self.driver.find_element("id", "email")
        password = self.driver.find_element("id", "password")
        email.clear()
        email.send_keys(credentials.email)
        password.clear()
        password.send_keys(credentials.password)
        self.driver.find_element("css selector", "button[type='submit']").click()


class DashboardPage:
    def __init__(self, driver, base_url: str):
        self.driver = driver
        self.base_url = base_url.rstrip("/")

    def heading_text(self) -> str:
        return self.driver.find_element("css selector", "h2").text

    def nav_labels(self) -> list[str]:
        return [element.text for element in self.driver.find_elements("css selector", "nav a")]
