from django.db.models import QuerySet

from .models import AccessGrant, BatchEnrollment, CohortEnrollment, Enrollment, EnrollmentHistory


def enrollment_queryset() -> QuerySet[Enrollment]:
    return Enrollment.objects.all()


def search_enrollments(filters: dict) -> QuerySet[Enrollment]:
    queryset = enrollment_queryset()
    for field in ["student_profile_id", "course_id", "institution_id", "status"]:
        if value := filters.get(field):
            queryset = queryset.filter(**{field: value})
    return queryset.order_by(filters.get("sort") or "-created_at", "id")


def access_grant_queryset() -> QuerySet[AccessGrant]:
    return AccessGrant.objects.select_related("enrollment")


def history_queryset() -> QuerySet[EnrollmentHistory]:
    return EnrollmentHistory.objects.select_related("enrollment")


def batch_job_queryset() -> QuerySet[BatchEnrollment]:
    return BatchEnrollment.objects.all()


def cohort_job_queryset() -> QuerySet[CohortEnrollment]:
    return CohortEnrollment.objects.all()
