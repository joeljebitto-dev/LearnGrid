from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LoginCredentials:
    email: str
    password: str


class BasePage:
    def __init__(self, driver, base_url: str):
        self.driver = driver
        self.base_url = base_url.rstrip("/")

    def visit(self, path: str):
        self.driver.get(f"{self.base_url}{path}")
        return self

    def text(self, selector: str) -> str:
        return self.driver.find_element("css selector", selector).text

    def visible_texts(self, selector: str) -> list[str]:
        return [element.text for element in self.driver.find_elements("css selector", selector)]


class LoginPage(BasePage):
    def open(self):
        return self.visit("/login")

    def sign_in(self, credentials: LoginCredentials):
        email = self.driver.find_element("id", "email")
        password = self.driver.find_element("id", "password")
        email.clear()
        email.send_keys(credentials.email)
        password.clear()
        password.send_keys(credentials.password)
        self.driver.find_element("css selector", "button[type='submit']").click()
        return DashboardPage(self.driver, self.base_url)


class DashboardPage(BasePage):
    def open(self, portal: str = ""):
        suffix = f"/{portal}" if portal else ""
        return self.visit(f"/dashboard{suffix}")

    def heading_text(self) -> str:
        return self.text("h2")

    def nav_labels(self) -> list[str]:
        return self.visible_texts("nav a")

    def section_titles(self) -> list[str]:
        return self.visible_texts("section h3")

    def sign_out(self):
        self.driver.find_element("xpath", "//button[normalize-space()='Sign out']").click()
        return LoginPage(self.driver, self.base_url)


class AdminCreateUserPage(BasePage):
    def open(self):
        return self.visit("/dashboard/admin/users/new")

    def fill_required_student_fields(self, *, email: str, password: str, student_number: str):
        self.driver.find_element("id", "new-email").send_keys(email)
        self.driver.find_element("id", "new-password").send_keys(password)
        self.driver.find_element("id", "first-name").send_keys("Quality")
        self.driver.find_element("id", "last-name").send_keys("Student")
        self.driver.find_element("id", "student-number").send_keys(student_number)
        return self

    def submit(self):
        self.driver.find_element("xpath", "//button[normalize-space()='Create user']").click()
        return self
