from django.urls import path

from .views import (
    AdminInstitutionDashboardView,
    AdminSystemDashboardView,
    AssessmentSearchView,
    CourseSearchView,
    DashboardAggregateListCreateView,
    EnrollmentSearchView,
    EventIngestView,
    InstructorDashboardView,
    ReportGenerateView,
    ReportSnapshotListCreateView,
    SearchIndexRecordDeleteView,
    SearchIndexRecordUpsertView,
    SearchView,
    StudentDashboardView,
    SubmissionSearchView,
    UsageMetricListCreateView,
    UserSearchView,
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
    path("search/", SearchView.as_view(), name="search"),
    path("search/courses/", CourseSearchView.as_view(), name="search-courses"),
    path("search/users/", UserSearchView.as_view(), name="search-users"),
    path("search/enrollments/", EnrollmentSearchView.as_view(), name="search-enrollments"),
    path("search/assessments/", AssessmentSearchView.as_view(), name="search-assessments"),
    path("search/submissions/", SubmissionSearchView.as_view(), name="search-submissions"),
    path(
        "search/index-records/",
        SearchIndexRecordUpsertView.as_view(),
        name="search-index-records",
    ),
    path(
        "search/index-records/<str:resource_type>/<uuid:resource_id>/",
        SearchIndexRecordDeleteView.as_view(),
        name="search-index-record-delete",
    ),
    path(
        "dashboards/aggregates/",
        DashboardAggregateListCreateView.as_view(),
        name="dashboard-aggregates",
    ),
    path("usage-metrics/", UsageMetricListCreateView.as_view(), name="usage-metrics"),
    path("reports/snapshots/", ReportSnapshotListCreateView.as_view(), name="report-snapshots"),
    path("reports/generate/", ReportGenerateView.as_view(), name="report-generate"),
]
