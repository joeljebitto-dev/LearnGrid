from __future__ import annotations

from rest_framework import serializers

from .models import (
    Course,
    CourseCategory,
    CourseDifficulty,
    CourseModule,
    CourseRevision,
    CourseStatus,
    CourseTag,
    LearningOutcome,
    Lesson,
    StructureStatus,
    Topic,
)
from .services import normalize_slug


COURSE_SORT_CHOICES = [
    "title",
    "-title",
    "status",
    "-status",
    "difficulty_level",
    "-difficulty_level",
    "published_at",
    "-published_at",
    "created_at",
    "-created_at",
    "updated_at",
    "-updated_at",
]
CATEGORY_TAG_SORT_CHOICES = ["name", "-name", "slug", "-slug", "created_at", "-created_at"]


class CourseCategorySerializer(serializers.ModelSerializer):
    parent_category_id = serializers.UUIDField(read_only=True, allow_null=True)

    class Meta:
        model = CourseCategory
        fields = [
            "id",
            "institution_id",
            "name",
            "slug",
            "parent_category_id",
            "created_at",
            "updated_at",
        ]


class CourseTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseTag
        fields = ["id", "institution_id", "name", "slug", "created_at"]


class LearningOutcomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningOutcome
        fields = ["id", "description", "position", "created_at", "updated_at"]


class TopicSerializer(serializers.ModelSerializer):
    lesson_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = Topic
        fields = [
            "id",
            "lesson_id",
            "title",
            "position",
            "content_asset_id",
            "created_at",
            "updated_at",
        ]


class LessonSerializer(serializers.ModelSerializer):
    course_id = serializers.UUIDField(read_only=True)
    module_id = serializers.UUIDField(read_only=True)
    topics = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = [
            "id",
            "course_id",
            "module_id",
            "title",
            "summary",
            "position",
            "status",
            "content_asset_id",
            "published_at",
            "topics",
            "created_at",
            "updated_at",
            "deleted_at",
        ]

    def get_topics(self, obj: Lesson) -> list[dict]:
        topics = getattr(obj, "prefetched_topics", None)
        if topics is None:
            topics = obj.topics.order_by("position", "id")
        return [TopicSerializer(topic).data for topic in topics]


class CourseModuleSerializer(serializers.ModelSerializer):
    course_id = serializers.UUIDField(read_only=True)
    lessons = serializers.SerializerMethodField()

    class Meta:
        model = CourseModule
        fields = [
            "id",
            "course_id",
            "title",
            "description",
            "position",
            "status",
            "lessons",
            "created_at",
            "updated_at",
            "deleted_at",
        ]

    def get_lessons(self, obj: CourseModule) -> list[dict]:
        lessons = getattr(obj, "prefetched_lessons", None)
        if lessons is None:
            lessons = obj.lessons.order_by("position", "id")
        return [LessonSerializer(lesson).data for lesson in lessons]


class CourseStructureSerializer(serializers.ModelSerializer):
    modules = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            "id",
            "institution_id",
            "title",
            "slug",
            "status",
            "modules",
        ]

    def get_modules(self, obj: Course) -> list[dict]:
        modules = getattr(obj, "prefetched_modules", None)
        if modules is None:
            modules = obj.modules.order_by("position", "id")
        return [CourseModuleSerializer(module).data for module in modules]


class CourseSerializer(serializers.ModelSerializer):
    categories = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    prerequisite_course_ids = serializers.SerializerMethodField()
    learning_outcomes = LearningOutcomeSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = [
            "id",
            "institution_id",
            "owner_profile_id",
            "title",
            "slug",
            "description",
            "difficulty_level",
            "thumbnail_asset_id",
            "status",
            "published_at",
            "categories",
            "tags",
            "prerequisite_course_ids",
            "learning_outcomes",
            "created_at",
            "updated_at",
            "deleted_at",
        ]

    def get_categories(self, obj: Course) -> list[dict]:
        links = getattr(obj, "prefetched_category_links", None)
        if links is None:
            links = obj.category_links.select_related("category").all()
        return [CourseCategorySerializer(link.category).data for link in links]

    def get_tags(self, obj: Course) -> list[dict]:
        links = getattr(obj, "prefetched_tag_links", None)
        if links is None:
            links = obj.tag_links.select_related("tag").all()
        return [CourseTagSerializer(link.tag).data for link in links]

    def get_prerequisite_course_ids(self, obj: Course) -> list[str]:
        prerequisites = getattr(obj, "prefetched_prerequisites", None)
        if prerequisites is None:
            prerequisites = obj.prerequisites.select_related("prerequisite_course").all()
        return [str(prerequisite.prerequisite_course_id) for prerequisite in prerequisites]


class LearningOutcomePayloadSerializer(serializers.Serializer):
    description = serializers.CharField(allow_blank=False)
    position = serializers.IntegerField(required=False, min_value=1)


class CourseCreateSerializer(serializers.Serializer):
    institution_id = serializers.UUIDField()
    owner_profile_id = serializers.UUIDField()
    title = serializers.CharField(max_length=255)
    slug = serializers.CharField(required=False, allow_blank=True, max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    difficulty_level = serializers.ChoiceField(
        choices=CourseDifficulty.choices,
        required=False,
        allow_null=True,
    )
    thumbnail_asset_id = serializers.UUIDField(required=False, allow_null=True)
    category_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True,
    )
    tag_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True,
    )
    prerequisite_course_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True,
    )
    learning_outcomes = LearningOutcomePayloadSerializer(
        many=True,
        required=False,
        allow_empty=True,
    )

    def validate(self, attrs):
        attrs["slug"] = normalize_slug(attrs.get("slug") or attrs["title"])
        if Course.objects.filter(
            institution_id=attrs["institution_id"],
            slug=attrs["slug"],
        ).exists():
            raise serializers.ValidationError(
                {"slug": "Course slug already exists for this institution."}
            )
        return _validate_learning_outcome_positions(attrs)


class CourseUpdateSerializer(serializers.Serializer):
    institution_id = serializers.UUIDField(required=False)
    owner_profile_id = serializers.UUIDField(required=False)
    title = serializers.CharField(required=False, max_length=255)
    slug = serializers.CharField(required=False, allow_blank=True, max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    difficulty_level = serializers.ChoiceField(
        choices=CourseDifficulty.choices,
        required=False,
        allow_null=True,
    )
    thumbnail_asset_id = serializers.UUIDField(required=False, allow_null=True)
    category_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True,
    )
    tag_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True,
    )
    prerequisite_course_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True,
    )
    learning_outcomes = LearningOutcomePayloadSerializer(
        many=True,
        required=False,
        allow_empty=True,
    )

    def validate(self, attrs):
        course = self.context["course"]
        if "slug" in attrs or ("title" in attrs and not course.slug):
            attrs["slug"] = normalize_slug(attrs.get("slug") or attrs.get("title") or course.title)
        institution_id = attrs.get("institution_id", course.institution_id)
        slug = attrs.get("slug", course.slug)
        if (
            Course.objects.filter(institution_id=institution_id, slug=slug)
            .exclude(id=course.id)
            .exists()
        ):
            raise serializers.ValidationError(
                {"slug": "Course slug already exists for this institution."}
            )
        return _validate_learning_outcome_positions(attrs)


class CourseSearchSerializer(serializers.Serializer):
    institution_id = serializers.UUIDField(required=False)
    owner_profile_id = serializers.UUIDField(required=False)
    status = serializers.ChoiceField(choices=CourseStatus.choices, required=False)
    difficulty_level = serializers.ChoiceField(choices=CourseDifficulty.choices, required=False)
    category_id = serializers.UUIDField(required=False)
    tag_id = serializers.UUIDField(required=False)
    q = serializers.CharField(required=False, allow_blank=True, max_length=255)
    sort = serializers.ChoiceField(
        choices=COURSE_SORT_CHOICES, default="-created_at", required=False
    )


class ModuleCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    position = serializers.IntegerField(required=False, min_value=1)
    status = serializers.ChoiceField(
        choices=StructureStatus.choices,
        default=StructureStatus.DRAFT,
        required=False,
    )


class ModuleUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    position = serializers.IntegerField(required=False, min_value=1)
    status = serializers.ChoiceField(choices=StructureStatus.choices, required=False)


class LessonCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    summary = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    position = serializers.IntegerField(required=False, min_value=1)
    status = serializers.ChoiceField(
        choices=StructureStatus.choices,
        default=StructureStatus.DRAFT,
        required=False,
    )
    content_asset_id = serializers.UUIDField(required=False, allow_null=True)


class LessonUpdateSerializer(serializers.Serializer):
    module_id = serializers.UUIDField(required=False)
    title = serializers.CharField(required=False, max_length=255)
    summary = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    position = serializers.IntegerField(required=False, min_value=1)
    status = serializers.ChoiceField(choices=StructureStatus.choices, required=False)
    content_asset_id = serializers.UUIDField(required=False, allow_null=True)


class TopicCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    position = serializers.IntegerField(required=False, min_value=1)
    content_asset_id = serializers.UUIDField(required=False, allow_null=True)


class TopicUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, max_length=255)
    position = serializers.IntegerField(required=False, min_value=1)
    content_asset_id = serializers.UUIDField(required=False, allow_null=True)


class ModuleReorderSerializer(serializers.Serializer):
    module_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False,
    )


class LessonReorderSerializer(serializers.Serializer):
    lesson_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False,
    )


class TopicReorderSerializer(serializers.Serializer):
    topic_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False,
    )


class CourseRevisionSerializer(serializers.ModelSerializer):
    course_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = CourseRevision
        fields = [
            "id",
            "course_id",
            "version_number",
            "snapshot",
            "created_by_profile_id",
            "created_at",
        ]


class CourseRevisionCreateSerializer(serializers.Serializer):
    created_by_profile_id = serializers.UUIDField(required=False)


class CategoryCreateSerializer(serializers.Serializer):
    institution_id = serializers.UUIDField(required=False, allow_null=True)
    name = serializers.CharField(max_length=128)
    slug = serializers.CharField(required=False, allow_blank=True, max_length=128)
    parent_category_id = serializers.UUIDField(required=False, allow_null=True)

    def validate(self, attrs):
        attrs["institution_id"] = attrs.get("institution_id")
        attrs["slug"] = normalize_slug(attrs.get("slug") or attrs["name"])
        _validate_category_scope(attrs)
        if CourseCategory.objects.filter(
            institution_id=attrs["institution_id"],
            slug=attrs["slug"],
        ).exists():
            raise serializers.ValidationError(
                {"slug": "Category slug already exists for this scope."}
            )
        return attrs


class CategoryUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, max_length=128)
    slug = serializers.CharField(required=False, allow_blank=True, max_length=128)
    parent_category_id = serializers.UUIDField(required=False, allow_null=True)

    def validate(self, attrs):
        category = self.context["category"]
        if "slug" in attrs or ("name" in attrs and not category.slug):
            attrs["slug"] = normalize_slug(attrs.get("slug") or attrs.get("name") or category.name)
        attrs["institution_id"] = category.institution_id
        _validate_category_scope(attrs, category=category)
        slug = attrs.get("slug", category.slug)
        if (
            CourseCategory.objects.filter(
                institution_id=category.institution_id,
                slug=slug,
            )
            .exclude(id=category.id)
            .exists()
        ):
            raise serializers.ValidationError(
                {"slug": "Category slug already exists for this scope."}
            )
        return attrs


class TagCreateSerializer(serializers.Serializer):
    institution_id = serializers.UUIDField(required=False, allow_null=True)
    name = serializers.CharField(max_length=128)
    slug = serializers.CharField(required=False, allow_blank=True, max_length=128)

    def validate(self, attrs):
        attrs["institution_id"] = attrs.get("institution_id")
        attrs["slug"] = normalize_slug(attrs.get("slug") or attrs["name"])
        if CourseTag.objects.filter(
            institution_id=attrs["institution_id"], slug=attrs["slug"]
        ).exists():
            raise serializers.ValidationError({"slug": "Tag slug already exists for this scope."})
        return attrs


class TagUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, max_length=128)
    slug = serializers.CharField(required=False, allow_blank=True, max_length=128)

    def validate(self, attrs):
        tag = self.context["tag"]
        if "slug" in attrs or ("name" in attrs and not tag.slug):
            attrs["slug"] = normalize_slug(attrs.get("slug") or attrs.get("name") or tag.name)
        slug = attrs.get("slug", tag.slug)
        if (
            CourseTag.objects.filter(institution_id=tag.institution_id, slug=slug)
            .exclude(id=tag.id)
            .exists()
        ):
            raise serializers.ValidationError({"slug": "Tag slug already exists for this scope."})
        return attrs


class CategoryTagSearchSerializer(serializers.Serializer):
    institution_id = serializers.UUIDField(required=False)
    q = serializers.CharField(required=False, allow_blank=True, max_length=255)
    sort = serializers.ChoiceField(
        choices=CATEGORY_TAG_SORT_CHOICES,
        default="name",
        required=False,
    )


def _validate_learning_outcome_positions(attrs: dict) -> dict:
    outcomes = attrs.get("learning_outcomes")
    if outcomes is None:
        return attrs
    seen_positions: set[int] = set()
    normalized = []
    for index, outcome in enumerate(outcomes, start=1):
        position = outcome.get("position") or index
        if position in seen_positions:
            raise serializers.ValidationError(
                {"learning_outcomes": "Learning outcome positions must be unique."}
            )
        seen_positions.add(position)
        normalized.append({"description": outcome["description"], "position": position})
    attrs["learning_outcomes"] = normalized
    return attrs


def _validate_category_scope(attrs: dict, category: CourseCategory | None = None) -> None:
    parent_category_id = attrs.get("parent_category_id")
    if not parent_category_id:
        return
    try:
        parent = CourseCategory.objects.get(id=parent_category_id)
    except CourseCategory.DoesNotExist as exc:
        raise serializers.ValidationError(
            {"parent_category_id": "Parent category was not found."}
        ) from exc
    if category and parent.id == category.id:
        raise serializers.ValidationError(
            {"parent_category_id": "Category cannot be its own parent."}
        )
    if parent.institution_id != attrs.get("institution_id"):
        raise serializers.ValidationError(
            {"parent_category_id": "Parent category must be in the same scope."}
        )
