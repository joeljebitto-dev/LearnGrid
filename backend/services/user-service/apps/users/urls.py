from django.urls import path

from .views import (
    BatchDetailView,
    BatchListCreateView,
    DepartmentDetailView,
    DepartmentListCreateView,
    ImportJobPlaceholderView,
    InstitutionDetailView,
    InstitutionListCreateView,
    CurrentProfileView,
    ProfileDeactivateView,
    ProfileDetailView,
    ProfileListCreateView,
)


urlpatterns = [
    path("institutions/", InstitutionListCreateView.as_view(), name="institution-list-create"),
    path("institutions/<uuid:institution_id>/", InstitutionDetailView.as_view(), name="institution-detail"),
    path("departments/", DepartmentListCreateView.as_view(), name="department-list-create"),
    path("departments/<uuid:department_id>/", DepartmentDetailView.as_view(), name="department-detail"),
    path("batches/", BatchListCreateView.as_view(), name="batch-list-create"),
    path("batches/<uuid:batch_id>/", BatchDetailView.as_view(), name="batch-detail"),
    path("profiles/", ProfileListCreateView.as_view(), name="profile-list-create"),
    path("profiles/me/", CurrentProfileView.as_view(), name="profile-me"),
    path("profiles/<uuid:profile_id>/", ProfileDetailView.as_view(), name="profile-detail"),
    path(
        "profiles/<uuid:profile_id>/deactivate/",
        ProfileDeactivateView.as_view(),
        name="profile-deactivate",
    ),
    path("import-jobs/", ImportJobPlaceholderView.as_view(), name="import-job-placeholder"),
]
