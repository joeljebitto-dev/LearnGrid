from __future__ import annotations

import json
import logging
from contextlib import contextmanager
from typing import Any

import redis
from django.conf import settings
from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from django.utils.text import slugify
from learngrid_redis import RedisKeyBuilder
from learngrid_redis import RedisLockNotAcquired
from learngrid_redis import digest_json
from learngrid_redis import get_json_cache
from learngrid_redis import redis_client
from learngrid_redis import redis_lock
from learngrid_redis import set_json_cache
from learngrid_events import publish_event as publish_kafka_event
from rest_framework.exceptions import APIException
from rest_framework.exceptions import ValidationError

from .models import (
    Course,
    CourseCategory,
    CourseCategoryLink,
    CourseModule,
    CoursePrerequisite,
    CourseRevision,
    CourseStatus,
    CourseTag,
    CourseTagLink,
    LearningOutcome,
    Lesson,
    StructureStatus,
    Topic,
)


logger = logging.getLogger(__name__)


class CourseStructureLockUnavailable(APIException):
    status_code = 409
    default_code = "course_structure_lock_unavailable"
    default_detail = "Course structure is currently being updated. Try again."


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


def create_module(*, course: Course, validated_data: dict[str, Any]) -> CourseModule:
    position = validated_data.get("position") or _next_position(CourseModule, course=course)
    _ensure_position_available(
        CourseModule.objects.filter(course=course),
        position,
        "position",
    )
    module = CourseModule.objects.create(
        course=course,
        title=validated_data["title"],
        description=validated_data.get("description"),
        position=position,
        status=validated_data.get("status", StructureStatus.DRAFT),
    )
    invalidate_catalog_cache()
    return module


def update_module(*, module: CourseModule, validated_data: dict[str, Any]) -> CourseModule:
    if "position" in validated_data:
        _ensure_position_available(
            CourseModule.objects.filter(course=module.course),
            validated_data["position"],
            "position",
            exclude_id=module.id,
        )
    for field in ["title", "description", "position", "status"]:
        if field in validated_data:
            setattr(module, field, validated_data[field])
    module.save()
    invalidate_catalog_cache()
    return module


def archive_module(*, module: CourseModule) -> CourseModule:
    module.status = StructureStatus.ARCHIVED
    module.deleted_at = timezone.now()
    module.position = _next_position_excluding(
        CourseModule,
        exclude_id=module.id,
        course=module.course,
    )
    module.save(update_fields=["status", "position", "deleted_at", "updated_at"])
    invalidate_catalog_cache()
    return module


def reorder_modules(*, course: Course, module_ids: list) -> list[CourseModule]:
    with _redis_structure_lock("course", course.id):
        modules = list(CourseModule.objects.filter(course=course, deleted_at__isnull=True))
        ordered = _ordered_by_ids(items=modules, ordered_ids=module_ids, field_name="module_ids")
        with transaction.atomic():
            temp_base = _max_position(CourseModule, course=course)
            _assign_ordered_positions(ordered, temp_base=temp_base)
    invalidate_catalog_cache()
    return ordered


def create_lesson(*, module: CourseModule, validated_data: dict[str, Any]) -> Lesson:
    position = validated_data.get("position") or _next_position(Lesson, module=module)
    _ensure_position_available(
        Lesson.objects.filter(module=module),
        position,
        "position",
    )
    published_at = (
        timezone.now() if validated_data.get("status") == StructureStatus.PUBLISHED else None
    )
    lesson = Lesson.objects.create(
        course=module.course,
        module=module,
        title=validated_data["title"],
        summary=validated_data.get("summary"),
        position=position,
        status=validated_data.get("status", StructureStatus.DRAFT),
        content_asset_id=validated_data.get("content_asset_id"),
        published_at=published_at,
    )
    invalidate_catalog_cache()
    return lesson


def update_lesson(*, lesson: Lesson, validated_data: dict[str, Any]) -> Lesson:
    target_module = lesson.module
    if module_id := validated_data.pop("module_id", None):
        try:
            target_module = CourseModule.objects.get(id=module_id, deleted_at__isnull=True)
        except CourseModule.DoesNotExist as exc:
            raise ValidationError({"module_id": "Module was not found."}) from exc
        if target_module.course_id != lesson.course_id:
            raise ValidationError(
                {"module_id": "Lesson cannot move to a module in another course."}
            )
        if "position" not in validated_data:
            validated_data["position"] = _next_position(Lesson, module=target_module)

    if "position" in validated_data or target_module.id != lesson.module_id:
        _ensure_position_available(
            Lesson.objects.filter(module=target_module),
            validated_data.get("position", lesson.position),
            "position",
            exclude_id=lesson.id,
        )

    if validated_data.get("status") == StructureStatus.PUBLISHED and lesson.published_at is None:
        lesson.published_at = timezone.now()
    lesson.module = target_module
    lesson.course = target_module.course
    for field in ["title", "summary", "position", "status", "content_asset_id"]:
        if field in validated_data:
            setattr(lesson, field, validated_data[field])
    lesson.save()
    invalidate_catalog_cache()
    return lesson


def publish_lesson(*, lesson: Lesson, correlation_id: str | None = None) -> Lesson:
    lesson.status = StructureStatus.PUBLISHED
    lesson.deleted_at = None
    if lesson.published_at is None:
        lesson.published_at = timezone.now()
    lesson.save(update_fields=["status", "deleted_at", "published_at", "updated_at"])
    invalidate_catalog_cache()
    publish_course_event(
        event_type="LessonPublished",
        aggregate_id=lesson.id,
        correlation_id=correlation_id,
        payload={
            "course_id": str(lesson.course_id),
            "module_id": str(lesson.module_id),
            "institution_id": str(lesson.course.institution_id),
            "status": lesson.status,
        },
    )
    return lesson


def archive_lesson(*, lesson: Lesson) -> Lesson:
    lesson.status = StructureStatus.ARCHIVED
    lesson.deleted_at = timezone.now()
    lesson.position = _next_position_excluding(Lesson, exclude_id=lesson.id, module=lesson.module)
    lesson.save(update_fields=["status", "position", "deleted_at", "updated_at"])
    invalidate_catalog_cache()
    return lesson


def reorder_lessons(*, module: CourseModule, lesson_ids: list) -> list[Lesson]:
    with _redis_structure_lock("module", module.id):
        lessons = list(Lesson.objects.filter(module=module, deleted_at__isnull=True))
        ordered = _ordered_by_ids(items=lessons, ordered_ids=lesson_ids, field_name="lesson_ids")
        with transaction.atomic():
            temp_base = _max_position(Lesson, module=module)
            _assign_ordered_positions(ordered, temp_base=temp_base)
    invalidate_catalog_cache()
    return ordered


def create_topic(*, lesson: Lesson, validated_data: dict[str, Any]) -> Topic:
    position = validated_data.get("position") or _next_position(Topic, lesson=lesson)
    _ensure_position_available(
        Topic.objects.filter(lesson=lesson),
        position,
        "position",
    )
    topic = Topic.objects.create(
        lesson=lesson,
        title=validated_data["title"],
        position=position,
        content_asset_id=validated_data.get("content_asset_id"),
    )
    invalidate_catalog_cache()
    return topic


def update_topic(*, topic: Topic, validated_data: dict[str, Any]) -> Topic:
    if "position" in validated_data:
        _ensure_position_available(
            Topic.objects.filter(lesson=topic.lesson),
            validated_data["position"],
            "position",
            exclude_id=topic.id,
        )
    for field in ["title", "position", "content_asset_id"]:
        if field in validated_data:
            setattr(topic, field, validated_data[field])
    topic.save()
    invalidate_catalog_cache()
    return topic


def delete_topic(*, topic: Topic) -> None:
    topic.delete()
    invalidate_catalog_cache()


def reorder_topics(*, lesson: Lesson, topic_ids: list) -> list[Topic]:
    with _redis_structure_lock("lesson", lesson.id):
        topics = list(Topic.objects.filter(lesson=lesson))
        ordered = _ordered_by_ids(items=topics, ordered_ids=topic_ids, field_name="topic_ids")
        with transaction.atomic():
            temp_base = _max_position(Topic, lesson=lesson)
            _assign_ordered_positions(ordered, temp_base=temp_base)
    invalidate_catalog_cache()
    return ordered


def create_course_revision(*, course: Course, created_by_profile_id) -> CourseRevision:
    version_number = (
        CourseRevision.objects.filter(course=course).aggregate(max_version=Max("version_number"))[
            "max_version"
        ]
        or 0
    ) + 1
    revision = CourseRevision.objects.create(
        course=course,
        version_number=version_number,
        created_by_profile_id=created_by_profile_id,
        snapshot=course_structure_snapshot(course),
    )
    return revision


def course_structure_snapshot(course: Course) -> dict[str, Any]:
    modules = (
        CourseModule.objects.filter(course=course, deleted_at__isnull=True)
        .prefetch_related("lessons__topics")
        .order_by("position", "id")
    )
    return {
        "course": {
            "id": str(course.id),
            "institution_id": str(course.institution_id),
            "owner_profile_id": str(course.owner_profile_id),
            "title": course.title,
            "slug": course.slug,
            "status": course.status,
            "published_at": course.published_at.isoformat() if course.published_at else None,
        },
        "modules": [
            {
                "id": str(module.id),
                "title": module.title,
                "description": module.description,
                "position": module.position,
                "status": module.status,
                "lessons": [
                    {
                        "id": str(lesson.id),
                        "title": lesson.title,
                        "summary": lesson.summary,
                        "position": lesson.position,
                        "status": lesson.status,
                        "content_asset_id": (
                            str(lesson.content_asset_id) if lesson.content_asset_id else None
                        ),
                        "published_at": (
                            lesson.published_at.isoformat() if lesson.published_at else None
                        ),
                        "topics": [
                            {
                                "id": str(topic.id),
                                "title": topic.title,
                                "position": topic.position,
                                "content_asset_id": (
                                    str(topic.content_asset_id) if topic.content_asset_id else None
                                ),
                            }
                            for topic in lesson.topics.all().order_by("position", "id")
                        ],
                    }
                    for lesson in module.lessons.filter(deleted_at__isnull=True).order_by(
                        "position",
                        "id",
                    )
                ],
            }
            for module in modules
        ],
    }


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
    return get_json_cache(_redis_client(), key)


def set_catalog_cache(key: str, value: Any) -> None:
    set_json_cache(_redis_client(), key, value, settings.COURSE_CATALOG_CACHE_TTL_SECONDS)


def catalog_cache_key(kind: str, params: dict[str, Any]) -> str:
    return _key_builder().key("cache", "catalog", [kind, digest_json(params)])


def invalidate_catalog_cache() -> None:
    try:
        client = _redis_client()
        for key in client.scan_iter(f"{_key_builder().prefix_for('cache', 'catalog')}*"):
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
    event = publish_kafka_event(
        event_type=event_type,
        aggregate_id=aggregate_id,
        producer_service=settings.SERVICE_NAME,
        correlation_id=correlation_id,
        payload=payload,
    )
    logger.info("course_event %s", json.dumps(event, sort_keys=True))
    return event


def _redis_client():
    return redis_client(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT_SECONDS,
        socket_timeout=settings.REDIS_SOCKET_TIMEOUT_SECONDS,
        sentinel_urls=settings.REDIS_SENTINEL_URLS,
        sentinel_master_name=settings.REDIS_SENTINEL_MASTER_NAME,
        sentinel_password=settings.REDIS_SENTINEL_PASSWORD,
        password=settings.REDIS_PASSWORD,
    )


def _key_builder() -> RedisKeyBuilder:
    return RedisKeyBuilder(service=settings.SERVICE_NAME, env=settings.REDIS_ENV)


@contextmanager
def _redis_structure_lock(kind: str, object_id):
    key = _key_builder().key("lock", f"{kind}-structure", str(object_id))
    try:
        with redis_lock(_redis_client(), key, settings.REDIS_LOCK_TTL_SECONDS):
            yield
    except RedisLockNotAcquired as exc:
        raise CourseStructureLockUnavailable() from exc


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
        raise ValidationError(
            {"prerequisite_course_ids": "One or more prerequisite courses were not found."}
        )
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


def _next_position(model, **filters) -> int:
    return _max_position(model, **filters) + 1


def _next_position_excluding(model, *, exclude_id, **filters) -> int:
    return (
        model.objects.filter(**filters)
        .exclude(id=exclude_id)
        .aggregate(max_position=Max("position"))["max_position"]
        or 0
    ) + 1


def _max_position(model, **filters) -> int:
    return (
        model.objects.filter(**filters).aggregate(max_position=Max("position"))["max_position"] or 0
    )


def _ensure_position_available(queryset, position: int, field_name: str, exclude_id=None) -> None:
    if position is None:
        return
    if exclude_id:
        queryset = queryset.exclude(id=exclude_id)
    if queryset.filter(position=position).exists():
        raise ValidationError({field_name: "Position is already used in this scope."})


def _ordered_by_ids(*, items: list, ordered_ids: list, field_name: str) -> list:
    normalized_ids = _unique_ids(ordered_ids)
    if len(normalized_ids) != len(ordered_ids):
        raise ValidationError({field_name: "Duplicate IDs are not allowed."})
    item_map = {item.id: item for item in items}
    expected_ids = set(item_map)
    received_ids = set(normalized_ids)
    if received_ids != expected_ids:
        raise ValidationError({field_name: "IDs must match the current active structure records."})
    return [item_map[item_id] for item_id in normalized_ids]


def _assign_ordered_positions(items: list, *, temp_base: int) -> None:
    for offset, item in enumerate(items, start=1):
        item.position = temp_base + offset
        item.save(update_fields=["position", "updated_at"])
    for position, item in enumerate(items, start=1):
        item.position = position
        item.save(update_fields=["position", "updated_at"])
