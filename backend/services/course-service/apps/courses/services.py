from __future__ import annotations

import json
import logging
import uuid
from typing import Any

import redis
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from rest_framework.exceptions import ValidationError

from .models import (
    Course,
    CourseCategory,
    CourseCategoryLink,
    CoursePrerequisite,
    CourseStatus,
    CourseTag,
    CourseTagLink,
    LearningOutcome,
)


logger = logging.getLogger(__name__)
CATALOG_CACHE_PREFIX = "course-service:catalog"


def normalize_slug(value: str) -> str:
    slug = slugify((value or "").strip()).lower()
    if not slug:
        raise ValidationError("Slug is required.")
    return slug


def create_course(*, validated_data: dict[str, Any], correlation_id: str | None = None) -> Course:
    metadata = _pop_metadata(validated_data)
    with transaction.atomic():
        course = Course.objects.create(
            institution_id=validated_data["institution_id"],
            owner_profile_id=validated_data["owner_profile_id"],
            title=validated_data["title"],
            slug=validated_data["slug"],
            description=validated_data.get("description"),
            difficulty_level=validated_data.get("difficulty_level"),
            thumbnail_asset_id=validated_data.get("thumbnail_asset_id"),
            status=CourseStatus.DRAFT,
        )
        replace_course_metadata(course=course, metadata=metadata)

    invalidate_catalog_cache()
    publish_course_event(
        event_type="CourseCreated",
        aggregate_id=course.id,
        correlation_id=correlation_id,
        payload={
            "institution_id": str(course.institution_id),
            "owner_profile_id": str(course.owner_profile_id),
            "status": course.status,
        },
    )
    return course


def update_course(*, course: Course, validated_data: dict[str, Any]) -> Course:
    metadata = _pop_metadata(validated_data)
    with transaction.atomic():
        for field in [
            "institution_id",
            "owner_profile_id",
            "title",
            "slug",
            "description",
            "difficulty_level",
            "thumbnail_asset_id",
        ]:
            if field in validated_data:
                setattr(course, field, validated_data[field])
        course.save()
        replace_course_metadata(course=course, metadata=metadata)

    _clear_prefetched_metadata(course)
    invalidate_catalog_cache()
    return course


def publish_course(*, course: Course, correlation_id: str | None = None) -> Course:
    course.status = CourseStatus.PUBLISHED
    course.deleted_at = None
    if course.published_at is None:
        course.published_at = timezone.now()
    course.save(update_fields=["status", "deleted_at", "published_at", "updated_at"])
    invalidate_catalog_cache()
    publish_course_event(
        event_type="CoursePublished",
        aggregate_id=course.id,
        correlation_id=correlation_id,
        payload={"institution_id": str(course.institution_id), "status": course.status},
    )
    return course


def archive_course(*, course: Course, correlation_id: str | None = None) -> Course:
    course.status = CourseStatus.ARCHIVED
    course.save(update_fields=["status", "updated_at"])
    invalidate_catalog_cache()
    publish_course_event(
        event_type="CourseArchived",
        aggregate_id=course.id,
        correlation_id=correlation_id,
        payload={"institution_id": str(course.institution_id), "status": course.status},
    )
    return course


def delete_course(*, course: Course) -> Course:
    course.status = CourseStatus.DELETED
    course.deleted_at = timezone.now()
    course.save(update_fields=["status", "deleted_at", "updated_at"])
    invalidate_catalog_cache()
    return course


def create_category(*, validated_data: dict[str, Any]) -> CourseCategory:
    category = CourseCategory.objects.create(
        institution_id=validated_data.get("institution_id"),
        name=validated_data["name"],
        slug=validated_data["slug"],
        parent_category_id=validated_data.get("parent_category_id"),
    )
    invalidate_catalog_cache()
    return category


def update_category(*, category: CourseCategory, validated_data: dict[str, Any]) -> CourseCategory:
    validated_data.pop("institution_id", None)
    for field in ["name", "slug", "parent_category_id"]:
        if field in validated_data:
            setattr(category, field, validated_data[field])
    category.save()
    invalidate_catalog_cache()
    return category


def delete_category(*, category: CourseCategory) -> None:
    category.delete()
    invalidate_catalog_cache()


def create_tag(*, validated_data: dict[str, Any]) -> CourseTag:
    tag = CourseTag.objects.create(
        institution_id=validated_data.get("institution_id"),
        name=validated_data["name"],
        slug=validated_data["slug"],
    )
    invalidate_catalog_cache()
    return tag


def update_tag(*, tag: CourseTag, validated_data: dict[str, Any]) -> CourseTag:
    for field in ["name", "slug"]:
        if field in validated_data:
            setattr(tag, field, validated_data[field])
    tag.save()
    invalidate_catalog_cache()
    return tag


def delete_tag(*, tag: CourseTag) -> None:
    tag.delete()
    invalidate_catalog_cache()


def replace_course_metadata(*, course: Course, metadata: dict[str, Any]) -> None:
    if "category_ids" in metadata:
        _replace_categories(course, metadata["category_ids"])
    if "tag_ids" in metadata:
        _replace_tags(course, metadata["tag_ids"])
    if "prerequisite_course_ids" in metadata:
        _replace_prerequisites(course, metadata["prerequisite_course_ids"])
    if "learning_outcomes" in metadata:
        _replace_learning_outcomes(course, metadata["learning_outcomes"])
    _clear_prefetched_metadata(course)


def get_catalog_cache(key: str) -> Any | None:
    try:
        cached = _redis_client().get(key)
    except (redis.RedisError, OSError):
        return None
    if not cached:
        return None
    try:
        return json.loads(cached)
    except (TypeError, ValueError):
        return None


def set_catalog_cache(key: str, value: Any) -> None:
    try:
        _redis_client().setex(
            key,
            settings.COURSE_CATALOG_CACHE_TTL_SECONDS,
            json.dumps(value),
        )
    except (redis.RedisError, OSError, TypeError, ValueError):
        return


def catalog_cache_key(kind: str, params: dict[str, Any]) -> str:
    normalized = json.dumps(params, sort_keys=True, default=str)
    return f"{CATALOG_CACHE_PREFIX}:{kind}:{normalized}"


def invalidate_catalog_cache() -> None:
    try:
        client = _redis_client()
        for key in client.scan_iter(f"{CATALOG_CACHE_PREFIX}:*"):
            client.delete(key)
    except (redis.RedisError, OSError):
        return


def publish_course_event(
    *,
    event_type: str,
    aggregate_id,
    payload: dict[str, Any],
    correlation_id: str | None = None,
) -> dict[str, Any]:
    event = {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "aggregate_id": str(aggregate_id),
        "producer_service": settings.SERVICE_NAME,
        "timestamp": timezone.now().isoformat(),
        "version": 1,
        "correlation_id": correlation_id,
        "payload": payload,
    }
    logger.info("course_event %s", json.dumps(event, sort_keys=True))
    return event


def _redis_client():
    return redis.from_url(settings.REDIS_URL, decode_responses=True)


def _clear_prefetched_metadata(course: Course) -> None:
    for attr in [
        "prefetched_category_links",
        "prefetched_tag_links",
        "prefetched_prerequisites",
    ]:
        if hasattr(course, attr):
            delattr(course, attr)
    if hasattr(course, "_prefetched_objects_cache"):
        course._prefetched_objects_cache = {}


def _pop_metadata(validated_data: dict[str, Any]) -> dict[str, Any]:
    metadata = {}
    for field in [
        "category_ids",
        "tag_ids",
        "prerequisite_course_ids",
        "learning_outcomes",
    ]:
        if field in validated_data:
            metadata[field] = validated_data.pop(field)
    return metadata


def _replace_categories(course: Course, category_ids: list) -> None:
    categories = _scoped_objects(
        model=CourseCategory,
        object_ids=category_ids,
        institution_id=course.institution_id,
        field_name="category_ids",
    )
    CourseCategoryLink.objects.filter(course=course).delete()
    CourseCategoryLink.objects.bulk_create(
        [CourseCategoryLink(course=course, category=category) for category in categories]
    )


def _replace_tags(course: Course, tag_ids: list) -> None:
    tags = _scoped_objects(
        model=CourseTag,
        object_ids=tag_ids,
        institution_id=course.institution_id,
        field_name="tag_ids",
    )
    CourseTagLink.objects.filter(course=course).delete()
    CourseTagLink.objects.bulk_create([CourseTagLink(course=course, tag=tag) for tag in tags])


def _replace_prerequisites(course: Course, prerequisite_course_ids: list) -> None:
    normalized_ids = _unique_ids(prerequisite_course_ids)
    if course.id in normalized_ids:
        raise ValidationError({"prerequisite_course_ids": "Course cannot require itself."})
    prerequisites = list(
        Course.objects.filter(
            id__in=normalized_ids,
            status__in=[CourseStatus.DRAFT, CourseStatus.PUBLISHED, CourseStatus.ARCHIVED],
            deleted_at__isnull=True,
        )
    )
    if len(prerequisites) != len(normalized_ids):
        raise ValidationError({"prerequisite_course_ids": "One or more prerequisite courses were not found."})
    if any(prerequisite.institution_id != course.institution_id for prerequisite in prerequisites):
        raise ValidationError(
            {"prerequisite_course_ids": "Prerequisites must belong to the same institution."}
        )
    CoursePrerequisite.objects.filter(course=course).delete()
    CoursePrerequisite.objects.bulk_create(
        [
            CoursePrerequisite(course=course, prerequisite_course=prerequisite)
            for prerequisite in prerequisites
        ]
    )


def _replace_learning_outcomes(course: Course, outcomes: list[dict[str, Any]]) -> None:
    LearningOutcome.objects.filter(course=course).delete()
    LearningOutcome.objects.bulk_create(
        [
            LearningOutcome(
                course=course,
                description=outcome["description"],
                position=outcome["position"],
            )
            for outcome in outcomes
        ]
    )


def _scoped_objects(*, model, object_ids: list, institution_id, field_name: str) -> list:
    normalized_ids = _unique_ids(object_ids)
    objects = list(model.objects.filter(id__in=normalized_ids))
    if len(objects) != len(normalized_ids):
        raise ValidationError({field_name: "One or more values were not found."})
    if any(item.institution_id not in (None, institution_id) for item in objects):
        raise ValidationError({field_name: "Values must be global or in the course institution."})
    object_map = {item.id: item for item in objects}
    return [object_map[item_id] for item_id in normalized_ids]


def _unique_ids(values: list) -> list:
    seen = set()
    normalized = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        normalized.append(value)
    return normalized
