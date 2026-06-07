from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import jwt
import pytest
import redis
from django.conf import settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.courses import permissions, services
from apps.courses.models import Course, CourseModule, CourseStatus, Lesson, StructureStatus, Topic


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


class BrokenRedis:
    def get(self, _key):
        raise redis.RedisError("redis unavailable")

    def setex(self, *_args):
        raise redis.RedisError("redis unavailable")

    def scan_iter(self, _pattern):
        raise redis.RedisError("redis unavailable")


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


@pytest.mark.django_db
def test_manage_user_can_create_nested_structure_and_reorder(
    api_client,
    access_token,
    monkeypatch,
):
    institution_id = uuid4()
    course = create_course(institution_id)
    allow_course_manage(monkeypatch, institution_id)
    lesson_asset_id = uuid4()
    topic_asset_id = uuid4()

    response = api_client.post(
        f"/api/courses/{course.id}/modules/",
        {"title": "Module One"},
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 201
    module_one_id = response.json()["id"]
    assert response.json()["position"] == 1

    response = api_client.post(
        f"/api/courses/{course.id}/modules/",
        {"title": "Module Two"},
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 201
    module_two_id = response.json()["id"]

    response = api_client.post(
        f"/api/courses/modules/{module_one_id}/lessons/",
        {
            "title": "Lesson One",
            "summary": "Intro lesson",
            "content_asset_id": str(lesson_asset_id),
        },
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 201
    lesson_one_id = response.json()["id"]
    assert response.json()["content_asset_id"] == str(lesson_asset_id)

    response = api_client.post(
        f"/api/courses/modules/{module_one_id}/lessons/",
        {"title": "Lesson Two"},
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 201
    lesson_two_id = response.json()["id"]

    response = api_client.post(
        f"/api/courses/lessons/{lesson_one_id}/topics/",
        {"title": "Topic One", "content_asset_id": str(topic_asset_id)},
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 201
    topic_one_id = response.json()["id"]
    assert response.json()["content_asset_id"] == str(topic_asset_id)

    response = api_client.post(
        f"/api/courses/lessons/{lesson_one_id}/topics/",
        {"title": "Topic Two"},
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 201
    topic_two_id = response.json()["id"]

    response = api_client.post(
        f"/api/courses/{course.id}/modules/reorder/",
        {"module_ids": [module_two_id, module_one_id]},
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 200
    assert [module["id"] for module in response.json()] == [module_two_id, module_one_id]
    assert [module["position"] for module in response.json()] == [1, 2]

    response = api_client.post(
        f"/api/courses/modules/{module_one_id}/lessons/reorder/",
        {"lesson_ids": [lesson_two_id, lesson_one_id]},
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 200
    assert [lesson["id"] for lesson in response.json()] == [lesson_two_id, lesson_one_id]

    response = api_client.post(
        f"/api/courses/lessons/{lesson_one_id}/topics/reorder/",
        {"topic_ids": [topic_two_id, topic_one_id]},
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 200
    assert [topic["id"] for topic in response.json()] == [topic_two_id, topic_one_id]

    response = api_client.get(
        f"/api/courses/{course.id}/structure/",
        **auth_headers(access_token),
    )
    assert response.status_code == 200
    assert [module["id"] for module in response.json()["modules"]] == [module_two_id, module_one_id]


@pytest.mark.django_db
def test_published_structure_hides_draft_lessons_from_view_users(
    api_client,
    access_token,
    monkeypatch,
):
    institution_id = uuid4()
    course = create_course(
        institution_id,
        status=CourseStatus.PUBLISHED,
        published_at=timezone.now(),
    )
    module = CourseModule.objects.create(
        course=course,
        title="Published Module",
        position=1,
        status=StructureStatus.PUBLISHED,
    )
    published_lesson = Lesson.objects.create(
        course=course,
        module=module,
        title="Published Lesson",
        position=1,
        status=StructureStatus.PUBLISHED,
        published_at=timezone.now(),
    )
    Lesson.objects.create(
        course=course,
        module=module,
        title="Draft Lesson",
        position=2,
        status=StructureStatus.DRAFT,
    )
    Topic.objects.create(lesson=published_lesson, title="Visible Topic", position=1)
    allow_course_view(monkeypatch, institution_id)

    response = api_client.get(
        f"/api/courses/{course.id}/structure/",
        **auth_headers(access_token),
    )

    assert response.status_code == 200
    modules = response.json()["modules"]
    assert len(modules) == 1
    assert [lesson["title"] for lesson in modules[0]["lessons"]] == ["Published Lesson"]
    assert modules[0]["lessons"][0]["topics"][0]["title"] == "Visible Topic"


@pytest.mark.django_db
def test_lesson_publish_emits_event_and_makes_lesson_visible(
    api_client,
    access_token,
    monkeypatch,
):
    institution_id = uuid4()
    course = create_course(
        institution_id,
        status=CourseStatus.PUBLISHED,
        published_at=timezone.now(),
    )
    module = CourseModule.objects.create(
        course=course,
        title="Module",
        position=1,
        status=StructureStatus.PUBLISHED,
    )
    lesson = Lesson.objects.create(
        course=course,
        module=module,
        title="Draft Lesson",
        position=1,
    )
    allow_course_manage(monkeypatch, institution_id)
    events = []
    monkeypatch.setattr(
        services,
        "publish_course_event",
        lambda **kwargs: events.append(kwargs) or {"event_id": "evt"},
    )

    response = api_client.post(
        f"/api/courses/lessons/{lesson.id}/publish/",
        **auth_headers(access_token),
        format="json",
    )

    assert response.status_code == 200
    assert response.json()["status"] == StructureStatus.PUBLISHED
    assert response.json()["published_at"] is not None
    assert events[0]["event_type"] == "LessonPublished"

    allow_course_view(monkeypatch, institution_id)
    response = api_client.get(
        f"/api/courses/{course.id}/structure/",
        **auth_headers(access_token),
    )
    assert response.status_code == 200
    assert response.json()["modules"][0]["lessons"][0]["id"] == str(lesson.id)


@pytest.mark.django_db
def test_unauthorized_user_cannot_mutate_structure(api_client, access_token, monkeypatch):
    institution_id = uuid4()
    course = create_course(institution_id)
    module = CourseModule.objects.create(course=course, title="Module", position=1)
    lesson = Lesson.objects.create(course=course, module=module, title="Lesson", position=1)
    monkeypatch.setattr(permissions, "remote_authorization_check", lambda **_kwargs: False)

    requests = [
        api_client.post(
            f"/api/courses/{course.id}/modules/",
            {"title": "Blocked"},
            **auth_headers(access_token),
            format="json",
        ),
        api_client.post(
            f"/api/courses/{course.id}/modules/reorder/",
            {"module_ids": [str(module.id)]},
            **auth_headers(access_token),
            format="json",
        ),
        api_client.post(
            f"/api/courses/lessons/{lesson.id}/publish/",
            **auth_headers(access_token),
            format="json",
        ),
        api_client.delete(
            f"/api/courses/modules/{module.id}/",
            **auth_headers(access_token),
        ),
    ]

    assert [response.status_code for response in requests] == [403, 403, 403, 403]


@pytest.mark.django_db
def test_reorder_validation_is_transactional(api_client, access_token, monkeypatch):
    institution_id = uuid4()
    course = create_course(institution_id)
    first = CourseModule.objects.create(course=course, title="First", position=1)
    second = CourseModule.objects.create(course=course, title="Second", position=2)
    allow_course_manage(monkeypatch, institution_id)

    response = api_client.post(
        f"/api/courses/{course.id}/modules/reorder/",
        {"module_ids": [str(second.id)]},
        **auth_headers(access_token),
        format="json",
    )

    assert response.status_code == 400
    assert list(
        CourseModule.objects.filter(course=course).order_by("position").values_list("id", flat=True)
    ) == [first.id, second.id]


@pytest.mark.django_db
def test_course_revision_snapshots_increment_versions(api_client, access_token, monkeypatch):
    institution_id = uuid4()
    course = create_course(institution_id)
    module = CourseModule.objects.create(course=course, title="Module", position=1)
    lesson = Lesson.objects.create(course=course, module=module, title="Lesson", position=1)
    Topic.objects.create(lesson=lesson, title="Topic", position=1)
    allow_course_manage(monkeypatch, institution_id)
    creator_id = uuid4()

    response = api_client.post(
        f"/api/courses/{course.id}/revisions/",
        {"created_by_profile_id": str(creator_id)},
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 201
    first_revision_id = response.json()["id"]
    assert response.json()["version_number"] == 1
    assert response.json()["created_by_profile_id"] == str(creator_id)
    assert response.json()["snapshot"]["modules"][0]["lessons"][0]["topics"][0]["title"] == "Topic"

    response = api_client.post(
        f"/api/courses/{course.id}/revisions/",
        {"created_by_profile_id": str(creator_id)},
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 201
    assert response.json()["version_number"] == 2

    response = api_client.get(
        f"/api/courses/revisions/{first_revision_id}/",
        **auth_headers(access_token),
    )
    assert response.status_code == 200
    assert response.json()["version_number"] == 1
