from django.urls import path

from .views import (
    AccessCheckView,
    BatchEnrollmentListCreateView,
    CohortEnrollmentListCreateView,
    EnrollmentDetailView,
    EnrollmentHistoryView,
    EnrollmentListCreateView,
    EnrollmentTransitionView,
)


urlpatterns = [
    path("", EnrollmentListCreateView.as_view(), name="enrollment-list-create"),
    path("access/check/", AccessCheckView.as_view(), name="enrollment-access-check"),
    path(
        "batch-enrollments/",
        BatchEnrollmentListCreateView.as_view(),
        name="batch-enrollment-list-create",
    ),
    path(
        "cohort-enrollments/",
        CohortEnrollmentListCreateView.as_view(),
        name="cohort-enrollment-list-create",
    ),
    path("<uuid:enrollment_id>/", EnrollmentDetailView.as_view(), name="enrollment-detail"),
    path(
        "<uuid:enrollment_id>/transition/",
        EnrollmentTransitionView.as_view(),
        name="enrollment-transition",
    ),
    path(
        "<uuid:enrollment_id>/history/", EnrollmentHistoryView.as_view(), name="enrollment-history"
    ),
]
