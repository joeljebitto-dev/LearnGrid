from django.db.models import Prefetch, Q, QuerySet

from .models import (
    Course,
    CourseCategory,
    CourseCategoryLink,
    CoursePrerequisite,
    CourseStatus,
    CourseTag,
    CourseTagLink,
)


def course_queryset(*, include_deleted: bool = False) -> QuerySet[Course]:
    queryset = Course.objects.all()
    if not include_deleted:
        queryset = queryset.exclude(status=CourseStatus.DELETED).filter(deleted_at__isnull=True)
    return queryset.prefetch_related(
        Prefetch(
            "category_links",
            queryset=CourseCategoryLink.objects.select_related("category").order_by("category__name"),
            to_attr="prefetched_category_links",
        ),
        Prefetch(
            "tag_links",
            queryset=CourseTagLink.objects.select_related("tag").order_by("tag__name"),
            to_attr="prefetched_tag_links",
        ),
        Prefetch(
            "prerequisites",
            queryset=CoursePrerequisite.objects.select_related("prerequisite_course").order_by(
                "prerequisite_course__title"
            ),
            to_attr="prefetched_prerequisites",
        ),
        "learning_outcomes",
    )


def category_queryset() -> QuerySet[CourseCategory]:
    return CourseCategory.objects.select_related("parent_category")


def tag_queryset() -> QuerySet[CourseTag]:
    return CourseTag.objects.all()


def search_courses(filters: dict, *, management: bool = False) -> QuerySet[Course]:
    include_deleted = management and filters.get("status") == CourseStatus.DELETED
    queryset = course_queryset(include_deleted=include_deleted)

    if institution_id := filters.get("institution_id"):
        queryset = queryset.filter(institution_id=institution_id)
    if owner_profile_id := filters.get("owner_profile_id"):
        queryset = queryset.filter(owner_profile_id=owner_profile_id)
    if management:
        if status := filters.get("status"):
            queryset = queryset.filter(status=status)
    else:
        queryset = queryset.filter(status=CourseStatus.PUBLISHED, deleted_at__isnull=True)
    if difficulty_level := filters.get("difficulty_level"):
        queryset = queryset.filter(difficulty_level=difficulty_level)
    if category_id := filters.get("category_id"):
        queryset = queryset.filter(category_links__category_id=category_id)
    if tag_id := filters.get("tag_id"):
        queryset = queryset.filter(tag_links__tag_id=tag_id)
    if q := (filters.get("q") or "").strip():
        queryset = queryset.filter(Q(title__icontains=q) | Q(description__icontains=q))

    return queryset.order_by(filters.get("sort") or "-created_at", "id").distinct()


def search_categories(filters: dict) -> QuerySet[CourseCategory]:
    queryset = category_queryset()
    if "institution_id" in filters:
        queryset = queryset.filter(institution_id=filters["institution_id"])
    if q := (filters.get("q") or "").strip():
        queryset = queryset.filter(Q(name__icontains=q) | Q(slug__icontains=q))
    return queryset.order_by(filters.get("sort") or "name", "id")


def search_tags(filters: dict) -> QuerySet[CourseTag]:
    queryset = tag_queryset()
    if "institution_id" in filters:
        queryset = queryset.filter(institution_id=filters["institution_id"])
    if q := (filters.get("q") or "").strip():
        queryset = queryset.filter(Q(name__icontains=q) | Q(slug__icontains=q))
    return queryset.order_by(filters.get("sort") or "name", "id")
