from django.db.models import Q, QuerySet

from .models import Batch, Department, Institution, UserProfile


def institution_queryset() -> QuerySet[Institution]:
    return Institution.objects.filter(deleted_at__isnull=True)


def department_queryset() -> QuerySet[Department]:
    return Department.objects.select_related("institution").filter(deleted_at__isnull=True)


def batch_queryset() -> QuerySet[Batch]:
    return Batch.objects.select_related("institution", "department").filter(deleted_at__isnull=True)


def search_institutions(filters: dict) -> QuerySet[Institution]:
    queryset = institution_queryset()
    if status := filters.get("status"):
        queryset = queryset.filter(status=status)
    if q := (filters.get("q") or "").strip():
        queryset = queryset.filter(Q(name__icontains=q) | Q(code__icontains=q))
    return queryset.order_by(filters.get("sort") or "name", "id")


def search_departments(filters: dict) -> QuerySet[Department]:
    queryset = department_queryset()
    if institution_id := filters.get("institution_id"):
        queryset = queryset.filter(institution_id=institution_id)
    if status := filters.get("status"):
        queryset = queryset.filter(status=status)
    if q := (filters.get("q") or "").strip():
        queryset = queryset.filter(Q(name__icontains=q) | Q(code__icontains=q))
    return queryset.order_by(filters.get("sort") or "name", "id")


def search_batches(filters: dict) -> QuerySet[Batch]:
    queryset = batch_queryset()
    if institution_id := filters.get("institution_id"):
        queryset = queryset.filter(institution_id=institution_id)
    if department_id := filters.get("department_id"):
        queryset = queryset.filter(department_id=department_id)
    if status := filters.get("status"):
        queryset = queryset.filter(status=status)
    if q := (filters.get("q") or "").strip():
        queryset = queryset.filter(Q(name__icontains=q))
    return queryset.order_by(filters.get("sort") or "name", "id")


def profile_queryset() -> QuerySet[UserProfile]:
    return UserProfile.objects.select_related("institution").select_related(
        "student_profile__batch",
        "student_profile__department",
        "student_profile__guardian_profile",
        "instructor_profile__department",
        "admin_profile__department",
    )


def search_profiles(filters: dict) -> QuerySet[UserProfile]:
    queryset = profile_queryset().filter(deleted_at__isnull=True)

    if institution_id := filters.get("institution_id"):
        queryset = queryset.filter(institution_id=institution_id)
    if status := filters.get("status"):
        queryset = queryset.filter(status=status)
    if q := (filters.get("q") or "").strip():
        queryset = queryset.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(display_name__icontains=q)
        )

    if profile_type := filters.get("profile_type"):
        queryset = queryset.filter(**{f"{profile_type}_profile__isnull": False})
    if department_id := filters.get("department_id"):
        queryset = queryset.filter(
            Q(student_profile__department_id=department_id)
            | Q(instructor_profile__department_id=department_id)
            | Q(admin_profile__department_id=department_id)
        )
    if batch_id := filters.get("batch_id"):
        queryset = queryset.filter(student_profile__batch_id=batch_id)

    return queryset.order_by(filters.get("sort") or "last_name", "id").distinct()
