from django.urls import path

from .views import (
    AdminInstitutionDashboardView,
    AdminSystemDashboardView,
    EventIngestView,
    InstructorDashboardView,
    ReportSnapshotListCreateView,
    StudentDashboardView,
)

urlpatterns = [
    path("dashboards/student/", StudentDashboardView.as_view(), name="dashboard-student"),
    path("dashboards/instructor/", InstructorDashboardView.as_view(), name="dashboard-instructor"),
    path("dashboards/admin/", AdminInstitutionDashboardView.as_view(), name="dashboard-admin"),
    path(
        "dashboards/admin/system/",
        AdminSystemDashboardView.as_view(),
        name="dashboard-admin-system",
    ),
    path("events/ingest/", EventIngestView.as_view(), name="event-ingest"),
    path("reports/snapshots/", ReportSnapshotListCreateView.as_view(), name="report-snapshots"),
]
