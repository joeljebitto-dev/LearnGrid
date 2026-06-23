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
    dashboard = LoginPage(driver, base_url).open().sign_in(credentials_for("student"))
    wait_for_heading(driver, dashboard, "Student Dashboard")
    dashboard = DashboardPage(driver, base_url)

    for path, heading in [
        ("/dashboard/student/courses", "Course Catalog"),
        ("/dashboard/student/progress", "Learning Progress"),
        ("/dashboard/student/certificates", "Certificates"),
        ("/dashboard/student/notifications", "Notification Center"),
    ]:
        dashboard.visit(path)
        wait_for_heading(driver, dashboard, heading)

    selenium_ui = pytest.importorskip("selenium.webdriver.support.ui")
    wait = selenium_ui.WebDriverWait(driver, 10)
    dashboard.visit("/dashboard/student/courses")
    wait_for_heading(driver, dashboard, "Course Catalog")
    wait.until(lambda _driver: driver.find_elements("xpath", "//a[normalize-space()='View course']"))
    driver.find_element("xpath", "//a[normalize-space()='View course']").click()
    wait.until(lambda _driver: "Course overview" in driver.page_source)
    wait.until(lambda _driver: driver.find_elements("xpath", "//a[normalize-space()='Start learning']"))
    driver.find_element("xpath", "//a[normalize-space()='Start learning']").click()
    wait_for_heading(driver, dashboard, "Learning Player")
    wait.until(lambda _driver: "Student" in driver.page_source and "Learn" in driver.page_source)
    assert "Course outline" in driver.page_source
    assert "Module" in driver.page_source
    assert "Lesson" in driver.page_source


def test_instructor_course_and_assessment_journey_surfaces_management_data(driver, base_url: str):
    dashboard = LoginPage(driver, base_url).open().sign_in(credentials_for("instructor"))
    wait_for_heading(driver, dashboard, "Instructor Dashboard")

    sections = set(dashboard.section_titles())
    assert {"Assessment status", "Course summaries", "Learner engagement"} <= sections


def test_instructor_feature_routes_surface_authoring_and_grading_tools(driver, base_url: str):
    dashboard = LoginPage(driver, base_url).open().sign_in(credentials_for("instructor"))
    wait_for_heading(driver, dashboard, "Instructor Dashboard")
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


def test_instructor_course_workspace_opens_overview_and_builder(driver, base_url: str):
    dashboard = LoginPage(driver, base_url).open().sign_in(credentials_for("instructor"))
    wait_for_heading(driver, dashboard, "Instructor Dashboard")
    dashboard.visit("/dashboard/instructor/courses")
    wait_for_heading(driver, dashboard, "Course Management")

    selenium_ui = pytest.importorskip("selenium.webdriver.support.ui")
    wait = selenium_ui.WebDriverWait(driver, 10)
    wait.until(lambda _driver: driver.find_elements("xpath", "//a[normalize-space()='Open']"))
    driver.find_element("xpath", "//a[normalize-space()='Open']").click()

    wait_for_heading(driver, dashboard, "Course overview")
    assert "Overview" in driver.page_source
    assert "Builder" in driver.page_source
    assert driver.find_elements("xpath", "//nav[@aria-label='Course']")
    assert not driver.find_elements("xpath", "//nav[@aria-label='Portal']")
    driver.find_element("xpath", "//nav[@aria-label='Course']//a[normalize-space()='Builder']").click()
    wait.until(lambda _driver: "Course Builder" in driver.page_source)
    assert driver.find_elements("xpath", "//nav[@aria-label='Course']")
    assert not driver.find_elements("xpath", "//nav[@aria-label='Portal']")

    wait.until(lambda _driver: driver.find_elements("xpath", "//button[normalize-space()='Add structure']"))
    driver.find_element("xpath", "//button[normalize-space()='Add structure']").click()
    wait.until(lambda _driver: driver.find_elements("xpath", "//*[@role='dialog' and @aria-label='Add structure']"))
    assert not driver.find_elements("xpath", "//label[normalize-space()='Module ID']")
    assert not driver.find_elements("xpath", "//label[normalize-space()='Lesson ID']")

    selenium_ui.Select(driver.find_element("id", "builder-action")).select_by_value("lesson")
    wait.until(lambda _driver: driver.find_elements("id", "builder-module"))
    assert driver.find_elements(
        "xpath",
        "//label[starts-with(normalize-space(), 'Module') and not(contains(normalize-space(), 'ID'))]",
    )
    driver.find_element("xpath", "//button[normalize-space()='Cancel']").click()
    wait.until(lambda _driver: not driver.find_elements("xpath", "//*[@role='dialog']"))

    for label, heading in [
        ("Question banks", "Question banks"),
        ("Participants", "Participants"),
        ("Assessments", "Assessments"),
    ]:
        driver.find_element("xpath", f"//nav[@aria-label='Course']//a[normalize-space()='{label}']").click()
        wait_for_heading(driver, dashboard, heading)
        assert driver.find_elements("xpath", "//nav[@aria-label='Course']")
        assert not driver.find_elements("xpath", "//nav[@aria-label='Portal']")


def test_admin_rbac_denial_redirects_student_away_from_admin_page(driver, base_url: str):
    dashboard = LoginPage(driver, base_url).open().sign_in(credentials_for("student"))
    wait_for_heading(driver, dashboard, "Student Dashboard")
    DashboardPage(driver, base_url).visit("/dashboard/admin")

    dashboard = DashboardPage(driver, base_url)
    wait_for_heading(driver, dashboard, "Student Dashboard")
    assert "/dashboard/student" in driver.current_url


def test_admin_feature_routes_surface_management_tools(driver, base_url: str):
    dashboard = LoginPage(driver, base_url).open().sign_in(credentials_for("admin"))
    wait_for_heading(driver, dashboard, "Admin Dashboard")
    dashboard = DashboardPage(driver, base_url)

    for path, heading in [
        ("/dashboard/admin/users", "Users"),
        ("/dashboard/admin/courses", "Courses"),
        ("/dashboard/admin/enrollments", "Enrollment Management"),
        ("/dashboard/admin/reports", "Analytics And Reporting"),
        ("/dashboard/admin/notifications", "Notification Center"),
    ]:
        dashboard.visit(path)
        wait_for_heading(driver, dashboard, heading)


def test_admin_courses_add_people_panel_is_available(driver, base_url: str):
    dashboard = LoginPage(driver, base_url).open().sign_in(credentials_for("admin"))
    wait_for_heading(driver, dashboard, "Admin Dashboard")
    dashboard.visit("/dashboard/admin/courses")
    wait_for_heading(driver, dashboard, "Courses")

    webdriver_wait = pytest.importorskip("selenium.webdriver.support.ui").WebDriverWait
    wait = webdriver_wait(driver, 10)
    wait.until(lambda _driver: driver.find_elements("xpath", "//button[normalize-space()='Add people']"))
    driver.find_element("xpath", "//button[normalize-space()='Add people']").click()
    wait.until(lambda _driver: "Add student" in driver.page_source and "Add instructor" in driver.page_source)


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
