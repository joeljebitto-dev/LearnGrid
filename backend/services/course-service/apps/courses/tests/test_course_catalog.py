from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import jwt
import pytest
import redis
from django.conf import settings
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIClient

from apps.courses import permissions, services, views
from apps.courses.models import (
    Course,
    CourseCategory,
    CourseCategoryLink,
    CourseDifficulty,
    CoursePrerequisite,
    CourseStatus,
    CourseTag,
    CourseTagLink,
    LearningOutcome,
)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def access_token():
    now = timezone.now()
    return jwt.encode(
        {
            "iss": settings.AUTH_JWT_ISSUER,
            "sub": str(uuid4()),
            "typ": "access",
            "jti": str(uuid4()),
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=5)).timestamp()),
        },
        settings.AUTH_JWT_SIGNING_KEY,
        algorithm=settings.AUTH_JWT_ALGORITHM,
    )


@pytest.fixture(autouse=True)
def disable_external_redis(monkeypatch):
    monkeypatch.setattr(services, "_redis_client", lambda: BrokenRedis())


def auth_headers(token: str) -> dict[str, str]:
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def allow_course_manage(monkeypatch, institution_id):
    monkeypatch.setattr(
        permissions,
        "remote_authorization_check",
        lambda **kwargs: (
            kwargs["permission"] == "course.manage"
            and kwargs["scope_type"] == "institution"
            and kwargs["scope_id"] == str(institution_id)
        ),
    )


def allow_course_view(monkeypatch, institution_id):
    monkeypatch.setattr(
        permissions,
        "remote_authorization_check",
        lambda **kwargs: (
            kwargs["permission"] == "course.view"
            and kwargs["scope_type"] == "institution"
            and kwargs["scope_id"] == str(institution_id)
        ),
    )


def allow_course_manage_and_view(monkeypatch, institution_id):
    monkeypatch.setattr(
        permissions,
        "remote_authorization_check",
        lambda **kwargs: (
            kwargs["permission"] in {"course.manage", "course.view"}
            and kwargs["scope_type"] == "institution"
            and kwargs["scope_id"] == str(institution_id)
        ),
    )


def allow_platform_course_manage_and_view(monkeypatch):
    monkeypatch.setattr(
        permissions,
        "remote_authorization_check",
        lambda **kwargs: (
            kwargs["permission"] in {"course.manage", "course.view"}
            and kwargs["scope_type"] == "platform"
            and kwargs["scope_id"] is None
        ),
    )


def create_course(institution_id, **overrides) -> Course:
    defaults = {
        "institution_id": institution_id,
        "owner_profile_id": uuid4(),
        "title": f"Course {uuid4()}",
        "slug": f"course-{uuid4()}",
        "status": CourseStatus.DRAFT,
    }
    defaults.update(overrides)
    return Course.objects.create(**defaults)


class FakeRedis:
    def __init__(self):
        self.data: dict[str, str] = {}
        self.set_count = 0
        self.delete_count = 0

    def get(self, key):
        return self.data.get(key)

    def setex(self, key, _ttl, value):
        self.set_count += 1
        self.data[key] = value

    def scan_iter(self, pattern):
        prefix = pattern.removesuffix("*")
        return [key for key in self.data if key.startswith(prefix)]

    def delete(self, key):
        self.delete_count += 1
        self.data.pop(key, None)


class BrokenRedis:
    def get(self, _key):
        raise redis.RedisError("redis unavailable")

    def setex(self, *_args):
        raise redis.RedisError("redis unavailable")

    def scan_iter(self, _pattern):
        raise redis.RedisError("redis unavailable")


@pytest.mark.django_db
def test_manage_user_can_create_draft_course_with_metadata(
    api_client,
    access_token,
    monkeypatch,
):
    institution_id = uuid4()
    category = CourseCategory.objects.create(
        institution_id=institution_id,
        name="Programming",
        slug="programming",
    )
    tag = CourseTag.objects.create(institution_id=institution_id, name="Python", slug="python")
    prerequisite = create_course(
        institution_id,
        title="Computer Basics",
        slug="computer-basics",
        status=CourseStatus.PUBLISHED,
    )
    allow_course_manage(monkeypatch, institution_id)
    events = []
    monkeypatch.setattr(
        services,
        "publish_course_event",
        lambda **kwargs: events.append(kwargs) or {"event_id": "evt"},
    )

    response = api_client.post(
        "/api/courses/",
        {
            "institution_id": str(institution_id),
            "owner_profile_id": str(uuid4()),
            "title": "Intro To Python",
            "description": "Foundational Python course.",
            "difficulty_level": CourseDifficulty.BEGINNER,
            "category_ids": [str(category.id)],
            "tag_ids": [str(tag.id)],
            "prerequisite_course_ids": [str(prerequisite.id)],
            "learning_outcomes": [
                {"description": "Write simple scripts."},
                {"description": "Use Python collections."},
            ],
        },
        **auth_headers(access_token),
        format="json",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == CourseStatus.DRAFT
    assert body["slug"] == "intro-to-python"
    assert body["categories"][0]["id"] == str(category.id)
    assert body["tags"][0]["id"] == str(tag.id)
    assert body["prerequisite_course_ids"] == [str(prerequisite.id)]
    assert [outcome["position"] for outcome in body["learning_outcomes"]] == [1, 2]
    assert events[0]["event_type"] == "CourseCreated"


@pytest.mark.django_db
def test_unauthorized_user_cannot_manage_courses(api_client, access_token, monkeypatch):
    institution_id = uuid4()
    course = create_course(institution_id)
    monkeypatch.setattr(permissions, "remote_authorization_check", lambda **_kwargs: False)

    response = api_client.post(
        "/api/courses/",
        {
            "institution_id": str(institution_id),
            "owner_profile_id": str(uuid4()),
            "title": "Blocked Course",
        },
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 403

    for method, path in [
        ("patch", f"/api/courses/{course.id}/"),
        ("post", f"/api/courses/{course.id}/publish/"),
        ("post", f"/api/courses/{course.id}/archive/"),
        ("delete", f"/api/courses/{course.id}/"),
    ]:
        response = getattr(api_client, method)(
            path,
            {"title": "Blocked Update"} if method == "patch" else {},
            **auth_headers(access_token),
            format="json",
        )
        assert response.status_code == 403


@pytest.mark.django_db
def test_catalog_visibility_follows_lifecycle_and_permission(
    api_client,
    access_token,
    monkeypatch,
):
    institution_id = uuid4()
    published = create_course(
        institution_id,
        title="Published",
        slug="published",
        status=CourseStatus.PUBLISHED,
        published_at=timezone.now(),
    )
    draft = create_course(institution_id, title="Draft", slug="draft")
    archived = create_course(
        institution_id,
        title="Archived",
        slug="archived",
        status=CourseStatus.ARCHIVED,
    )
    deleted = create_course(
        institution_id,
        title="Deleted",
        slug="deleted",
        status=CourseStatus.DELETED,
        deleted_at=timezone.now(),
    )

    allow_course_view(monkeypatch, institution_id)
    response = api_client.get(
        "/api/courses/",
        {"institution_id": str(institution_id), "page_size": "10"},
        **auth_headers(access_token),
    )
    assert response.status_code == 200
    assert [course["id"] for course in response.json()["results"]] == [str(published.id)]

    response = api_client.get(f"/api/courses/{draft.id}/", **auth_headers(access_token))
    assert response.status_code == 403

    allow_course_manage_and_view(monkeypatch, institution_id)
    for course in [published, draft, archived, deleted]:
        response = api_client.get(f"/api/courses/{course.id}/", **auth_headers(access_token))
        assert response.status_code == 200

    response = api_client.get(
        "/api/courses/",
        {"institution_id": str(institution_id), "status": CourseStatus.ARCHIVED},
        **auth_headers(access_token),
    )
    assert response.status_code == 200
    assert response.json()["results"][0]["id"] == str(archived.id)


@pytest.mark.django_db
def test_publish_archive_and_delete_update_visibility_and_emit_events(
    api_client,
    access_token,
    monkeypatch,
):
    institution_id = uuid4()
    course = create_course(institution_id)
    allow_course_manage_and_view(monkeypatch, institution_id)
    events = []
    monkeypatch.setattr(
        services,
        "publish_course_event",
        lambda **kwargs: events.append(kwargs) or {"event_id": "evt"},
    )

    response = api_client.post(
        f"/api/courses/{course.id}/publish/",
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["status"] == CourseStatus.PUBLISHED
    assert events[-1]["event_type"] == "CoursePublished"

    response = api_client.post(
        f"/api/courses/{course.id}/archive/",
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["status"] == CourseStatus.ARCHIVED
    assert events[-1]["event_type"] == "CourseArchived"

    response = api_client.delete(f"/api/courses/{course.id}/", **auth_headers(access_token))
    assert response.status_code == 200
    assert response.json()["status"] == CourseStatus.DELETED
    assert Course.objects.get(id=course.id).deleted_at is not None


@pytest.mark.django_db
def test_course_update_replaces_metadata_and_validates_prerequisites(
    api_client,
    access_token,
    monkeypatch,
):
    institution_id = uuid4()
    other_institution_id = uuid4()
    course = create_course(institution_id)
    old_category = CourseCategory.objects.create(
        institution_id=institution_id,
        name="Old Category",
        slug="old-category",
    )
    new_category = CourseCategory.objects.create(
        institution_id=institution_id,
        name="New Category",
        slug="new-category",
    )
    old_tag = CourseTag.objects.create(institution_id=institution_id, name="Old Tag", slug="old-tag")
    new_tag = CourseTag.objects.create(institution_id=institution_id, name="New Tag", slug="new-tag")
    old_prerequisite = create_course(institution_id, title="Old Prereq", slug="old-prereq")
    new_prerequisite = create_course(institution_id, title="New Prereq", slug="new-prereq")
    other_prerequisite = create_course(
        other_institution_id,
        title="Other Prereq",
        slug="other-prereq",
    )
    CourseCategoryLink.objects.create(course=course, category=old_category)
    CourseTagLink.objects.create(course=course, tag=old_tag)
    CoursePrerequisite.objects.create(course=course, prerequisite_course=old_prerequisite)
    LearningOutcome.objects.create(course=course, description="Old outcome", position=1)
    allow_course_manage(monkeypatch, institution_id)

    response = api_client.patch(
        f"/api/courses/{course.id}/",
        {
            "title": "Updated Course",
            "category_ids": [str(new_category.id)],
            "tag_ids": [str(new_tag.id)],
            "prerequisite_course_ids": [str(new_prerequisite.id)],
            "learning_outcomes": [{"description": "New outcome", "position": 3}],
        },
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Updated Course"
    assert body["categories"][0]["id"] == str(new_category.id)
    assert body["tags"][0]["id"] == str(new_tag.id)
    assert body["prerequisite_course_ids"] == [str(new_prerequisite.id)]
    assert body["learning_outcomes"][0]["position"] == 3

    response = api_client.patch(
        f"/api/courses/{course.id}/",
        {"prerequisite_course_ids": [str(course.id)]},
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 400

    response = api_client.patch(
        f"/api/courses/{course.id}/",
        {"prerequisite_course_ids": [str(other_prerequisite.id)]},
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_category_and_tag_crud_search_normalizes_slugs(api_client, access_token, monkeypatch):
    institution_id = uuid4()
    allow_course_manage_and_view(monkeypatch, institution_id)

    response = api_client.post(
        "/api/courses/categories/",
        {"institution_id": str(institution_id), "name": "Data Science", "slug": " Data Science "},
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 201
    category_id = response.json()["id"]
    assert response.json()["slug"] == "data-science"

    response = api_client.get(
        "/api/courses/categories/",
        {"institution_id": str(institution_id), "q": "data"},
        **auth_headers(access_token),
    )
    assert response.status_code == 200
    assert response.json()["count"] == 1

    response = api_client.patch(
        f"/api/courses/categories/{category_id}/",
        {"name": "Analytics"},
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Analytics"

    response = api_client.post(
        "/api/courses/tags/",
        {"institution_id": str(institution_id), "name": "Machine Learning"},
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 201
    tag_id = response.json()["id"]
    assert response.json()["slug"] == "machine-learning"

    response = api_client.get(
        "/api/courses/tags/",
        {"institution_id": str(institution_id), "q": "machine"},
        **auth_headers(access_token),
    )
    assert response.status_code == 200
    assert response.json()["count"] == 1

    response = api_client.delete(
        f"/api/courses/tags/{tag_id}/",
        **auth_headers(access_token),
    )
    assert response.status_code == 204
    assert not CourseTag.objects.filter(id=tag_id).exists()


@pytest.mark.django_db
def test_published_catalog_reads_use_cache_and_writes_invalidate_it(
    api_client,
    access_token,
    monkeypatch,
):
    institution_id = uuid4()
    create_course(
        institution_id,
        title="Cached Course",
        slug="cached-course",
        status=CourseStatus.PUBLISHED,
        published_at=timezone.now(),
    )
    fake_redis = FakeRedis()
    monkeypatch.setattr(services, "_redis_client", lambda: fake_redis)
    allow_course_view(monkeypatch, institution_id)

    response = api_client.get(
        "/api/courses/",
        {"institution_id": str(institution_id)},
        **auth_headers(access_token),
    )
    assert response.status_code == 200
    assert fake_redis.set_count == 1

    monkeypatch.setattr(
        views,
        "search_courses",
        lambda *_args, **_kwargs: pytest.fail("catalog cache was not used"),
    )
    response = api_client.get(
        "/api/courses/",
        {"institution_id": str(institution_id)},
        **auth_headers(access_token),
    )
    assert response.status_code == 200

    allow_course_manage(monkeypatch, institution_id)
    course = Course.objects.get(slug="cached-course")
    response = api_client.patch(
        f"/api/courses/{course.id}/",
        {"title": "Cache Invalidated"},
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 200
    assert fake_redis.delete_count >= 1


@pytest.mark.django_db
def test_redis_failure_falls_back_to_database(api_client, access_token, monkeypatch):
    institution_id = uuid4()
    create_course(
        institution_id,
        title="Database Course",
        slug="database-course",
        status=CourseStatus.PUBLISHED,
        published_at=timezone.now(),
    )
    monkeypatch.setattr(services, "_redis_client", lambda: BrokenRedis())
    allow_course_view(monkeypatch, institution_id)

    response = api_client.get(
        "/api/courses/",
        {"institution_id": str(institution_id)},
        **auth_headers(access_token),
    )

    assert response.status_code == 200
    assert response.json()["count"] == 1


@pytest.mark.django_db
def test_course_list_prefetches_metadata(api_client, access_token, monkeypatch):
    institution_id = uuid4()
    category = CourseCategory.objects.create(
        institution_id=institution_id,
        name="Category",
        slug="category",
    )
    tag = CourseTag.objects.create(institution_id=institution_id, name="Tag", slug="tag")
    prerequisite = create_course(
        institution_id,
        title="Prerequisite",
        slug="prerequisite",
        status=CourseStatus.PUBLISHED,
        published_at=timezone.now(),
    )
    for index in range(3):
        course = create_course(
            institution_id,
            title=f"Published {index}",
            slug=f"published-{index}",
            status=CourseStatus.PUBLISHED,
            published_at=timezone.now(),
        )
        CourseCategoryLink.objects.create(course=course, category=category)
        CourseTagLink.objects.create(course=course, tag=tag)
        CoursePrerequisite.objects.create(course=course, prerequisite_course=prerequisite)
        LearningOutcome.objects.create(course=course, description=f"Outcome {index}", position=1)
    allow_course_view(monkeypatch, institution_id)

    with CaptureQueriesContext(connection) as queries:
        response = api_client.get(
            "/api/courses/",
            {"institution_id": str(institution_id), "page_size": "10"},
            **auth_headers(access_token),
        )

    assert response.status_code == 200
    assert response.json()["count"] == 4
    assert len(queries) <= 8
