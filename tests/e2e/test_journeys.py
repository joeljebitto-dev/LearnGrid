from __future__ import annotations

import os
from uuid import uuid4

import pytest

from .conftest import credentials_for
from .pages import AdminCreateUserPage, DashboardPage, LoginPage
from .test_dashboards import wait_for_heading


def test_student_learning_journey_surfaces_courses_assessments_grades_and_logout(driver, base_url: str):
    dashboard = LoginPage(driver, base_url).open().sign_in(credentials_for("student"))
    wait_for_heading(driver, dashboard, "Student Dashboard")

    sections = set(dashboard.section_titles())
    assert {"Active courses", "Pending assessments", "Grades"} <= sections
    dashboard.sign_out()


def test_student_feature_routes_surface_learning_tools(driver, base_url: str):
    LoginPage(driver, base_url).open().sign_in(credentials_for("student"))
    dashboard = DashboardPage(driver, base_url)

    for path, heading in [
        ("/dashboard/student/courses", "Course Catalog"),
        ("/dashboard/student/progress", "Learning Progress"),
        ("/dashboard/student/certificates", "Certificates"),
        ("/dashboard/student/notifications", "Notification Center"),
    ]:
        dashboard.visit(path)
        wait_for_heading(driver, dashboard, heading)


def test_instructor_course_and_assessment_journey_surfaces_management_data(driver, base_url: str):
    dashboard = LoginPage(driver, base_url).open().sign_in(credentials_for("instructor"))
    wait_for_heading(driver, dashboard, "Instructor Dashboard")

    sections = set(dashboard.section_titles())
    assert {"Assessment status", "Course summaries", "Learner engagement"} <= sections


def test_instructor_feature_routes_surface_authoring_and_grading_tools(driver, base_url: str):
    LoginPage(driver, base_url).open().sign_in(credentials_for("instructor"))
    dashboard = DashboardPage(driver, base_url)

    for path, heading in [
        ("/dashboard/instructor/courses", "Course Management"),
        ("/dashboard/instructor/content", "Content Upload"),
        ("/dashboard/instructor/assessments", "Assessment Authoring"),
        ("/dashboard/instructor/grading", "Grading And Manual Reviews"),
        ("/dashboard/instructor/reports", "Analytics And Reporting"),
    ]:
        dashboard.visit(path)
        wait_for_heading(driver, dashboard, heading)


def test_admin_rbac_denial_redirects_student_away_from_admin_page(driver, base_url: str):
    LoginPage(driver, base_url).open().sign_in(credentials_for("student"))
    DashboardPage(driver, base_url).visit("/dashboard/admin")

    dashboard = DashboardPage(driver, base_url)
    wait_for_heading(driver, dashboard, "Student Dashboard")
    assert "/dashboard/student" in driver.current_url


def test_admin_feature_routes_surface_management_tools(driver, base_url: str):
    LoginPage(driver, base_url).open().sign_in(credentials_for("admin"))
    dashboard = DashboardPage(driver, base_url)

    for path, heading in [
        ("/dashboard/admin/users/new", "Create User"),
        ("/dashboard/admin/enrollments", "Enrollment Management"),
        ("/dashboard/admin/reports", "Analytics And Reporting"),
        ("/dashboard/admin/notifications", "Notification Center"),
    ]:
        dashboard.visit(path)
        wait_for_heading(driver, dashboard, heading)


def test_admin_create_user_journey_when_enabled(driver, base_url: str):
    if os.getenv("E2E_CREATE_USER_ENABLED", "false").lower() != "true":
        pytest.skip("Set E2E_CREATE_USER_ENABLED=true to run the mutating admin user journey.")

    LoginPage(driver, base_url).open().sign_in(credentials_for("admin"))
    AdminCreateUserPage(driver, base_url).open().fill_required_student_fields(
        email=f"quality-{uuid4()}@example.com",
        password=os.getenv("E2E_NEW_USER_PASSWORD", "QualityPassword123!"),
        student_number=f"Q-{uuid4()}",
    ).submit()

    webdriver_wait = pytest.importorskip("selenium.webdriver.support.ui").WebDriverWait
    webdriver_wait(driver, 10).until(lambda _driver: "Created user:" in driver.page_source)
