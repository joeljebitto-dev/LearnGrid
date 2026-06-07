from __future__ import annotations

import uuid

from django.db import models
from django.db.models import Q


class CourseStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"
    ARCHIVED = "archived", "Archived"
    DELETED = "deleted", "Deleted"


class CourseDifficulty(models.TextChoices):
    BEGINNER = "beginner", "Beginner"
    INTERMEDIATE = "intermediate", "Intermediate"
    ADVANCED = "advanced", "Advanced"


class Course(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    institution_id = models.UUIDField()
    owner_profile_id = models.UUIDField()
    title = models.CharField(max_length=255)
    slug = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    difficulty_level = models.CharField(
        max_length=32,
        choices=CourseDifficulty.choices,
        null=True,
        blank=True,
    )
    thumbnail_asset_id = models.UUIDField(null=True, blank=True)
    status = models.CharField(
        max_length=24,
        choices=CourseStatus.choices,
        default=CourseStatus.DRAFT,
    )
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "courses"
        constraints = [
            models.UniqueConstraint(
                fields=["institution_id", "slug"],
                name="uq_courses_institution_slug",
            ),
        ]
        indexes = [
            models.Index(fields=["institution_id", "status"], name="idx_courses_inst_status"),
            models.Index(fields=["owner_profile_id"], name="idx_courses_owner_profile"),
        ]

    def __str__(self) -> str:
        return self.title


class CourseCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    institution_id = models.UUIDField(null=True, blank=True)
    name = models.CharField(max_length=128)
    slug = models.CharField(max_length=128)
    parent_category = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="child_categories",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "course_categories"
        constraints = [
            models.UniqueConstraint(
                fields=["institution_id", "slug"],
                condition=Q(institution_id__isnull=False),
                name="uq_course_cat_inst_slug",
            ),
            models.UniqueConstraint(
                fields=["slug"],
                condition=Q(institution_id__isnull=True),
                name="uq_course_cat_global_slug",
            ),
        ]
        indexes = [
            models.Index(fields=["parent_category"], name="idx_course_cat_parent"),
            models.Index(fields=["institution_id", "slug"], name="idx_course_cat_scope_slug"),
        ]

    def __str__(self) -> str:
        return self.name


class CourseTag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    institution_id = models.UUIDField(null=True, blank=True)
    name = models.CharField(max_length=128)
    slug = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "course_tags"
        constraints = [
            models.UniqueConstraint(
                fields=["institution_id", "slug"],
                condition=Q(institution_id__isnull=False),
                name="uq_course_tags_inst_slug",
            ),
            models.UniqueConstraint(
                fields=["slug"],
                condition=Q(institution_id__isnull=True),
                name="uq_course_tags_global_slug",
            ),
        ]
        indexes = [
            models.Index(fields=["institution_id", "slug"], name="idx_course_tags_scope_slug"),
        ]

    def __str__(self) -> str:
        return self.name


class CourseCategoryLink(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="category_links",
    )
    category = models.ForeignKey(
        CourseCategory,
        on_delete=models.CASCADE,
        related_name="course_links",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "course_category_links"
        constraints = [
            models.UniqueConstraint(
                fields=["course", "category"],
                name="uq_course_category_links_course_category",
            ),
        ]
        indexes = [
            models.Index(fields=["category"], name="idx_course_cat_links_cat"),
        ]


class CourseTagLink(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="tag_links",
    )
    tag = models.ForeignKey(
        CourseTag,
        on_delete=models.CASCADE,
        related_name="course_links",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "course_tag_links"
        constraints = [
            models.UniqueConstraint(
                fields=["course", "tag"],
                name="uq_course_tag_links_course_tag",
            ),
        ]
        indexes = [
            models.Index(fields=["tag"], name="idx_course_tag_links_tag"),
        ]


class CoursePrerequisite(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="prerequisites",
    )
    prerequisite_course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="required_by_courses",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "course_prerequisites"
        constraints = [
            models.UniqueConstraint(
                fields=["course", "prerequisite_course"],
                name="uq_course_prereq_course_prereq",
            ),
        ]
        indexes = [
            models.Index(fields=["prerequisite_course"], name="idx_course_prereq_prereq"),
        ]


class LearningOutcome(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="learning_outcomes",
    )
    description = models.TextField()
    position = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "learning_outcomes"
        constraints = [
            models.UniqueConstraint(
                fields=["course", "position"],
                name="uq_learning_outcomes_course_position",
            ),
        ]
        indexes = [
            models.Index(fields=["course"], name="idx_learning_outcomes_course"),
        ]
        ordering = ["position", "id"]

    def __str__(self) -> str:
        return self.description
