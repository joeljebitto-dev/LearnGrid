from __future__ import annotations

import uuid

from django.db import models


class LessonProgressStatus(models.TextChoices):
    NOT_STARTED = "not_started", "Not Started"
    IN_PROGRESS = "in_progress", "In Progress"
    COMPLETED = "completed", "Completed"


class AssessmentProgressStatus(models.TextChoices):
    NOT_STARTED = "not_started", "Not Started"
    STARTED = "started", "Started"
    SUBMITTED = "submitted", "Submitted"
    GRADED = "graded", "Graded"


class CourseProgressStatus(models.TextChoices):
    NOT_STARTED = "not_started", "Not Started"
    IN_PROGRESS = "in_progress", "In Progress"
    COMPLETED = "completed", "Completed"


class LessonProgress(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student_profile_id = models.UUIDField()
    course_id = models.UUIDField()
    lesson_id = models.UUIDField()
    status = models.CharField(
        max_length=24,
        choices=LessonProgressStatus.choices,
        default=LessonProgressStatus.NOT_STARTED,
    )
    view_count = models.PositiveIntegerField(default=0)
    first_viewed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "lesson_progress"
        constraints = [
            models.UniqueConstraint(
                fields=["student_profile_id", "lesson_id"],
                name="uq_lesson_progress_student_lesson",
            ),
        ]
        indexes = [
            models.Index(fields=["course_id", "status"], name="idx_lesson_progress_course"),
            models.Index(fields=["student_profile_id", "course_id"], name="idx_lesson_progress_student"),
        ]


class VideoProgress(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student_profile_id = models.UUIDField()
    content_asset_id = models.UUIDField()
    course_id = models.UUIDField()
    last_position_seconds = models.PositiveIntegerField(default=0)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    percent_complete = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "video_progress"
        constraints = [
            models.UniqueConstraint(
                fields=["student_profile_id", "content_asset_id"],
                name="uq_video_progress_student_asset",
            ),
        ]
        indexes = [
            models.Index(fields=["course_id"], name="idx_video_progress_course"),
        ]


class AssessmentProgress(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student_profile_id = models.UUIDField()
    assessment_id = models.UUIDField()
    course_id = models.UUIDField()
    status = models.CharField(
        max_length=24,
        choices=AssessmentProgressStatus.choices,
        default=AssessmentProgressStatus.NOT_STARTED,
    )
    attempt_count = models.PositiveIntegerField(default=0)
    last_submitted_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "assessment_progress"
        constraints = [
            models.UniqueConstraint(
                fields=["student_profile_id", "assessment_id"],
                name="uq_assess_progress_student_assess",
            ),
        ]
        indexes = [
            models.Index(fields=["course_id", "status"], name="idx_assess_progress_course"),
        ]


class CourseProgress(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student_profile_id = models.UUIDField()
    course_id = models.UUIDField()
    completion_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    lessons_completed = models.PositiveIntegerField(default=0)
    assessments_completed = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=24,
        choices=CourseProgressStatus.choices,
        default=CourseProgressStatus.IN_PROGRESS,
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "course_progress"
        constraints = [
            models.UniqueConstraint(
                fields=["student_profile_id", "course_id"],
                name="uq_course_progress_student_course",
            ),
        ]
        indexes = [
            models.Index(fields=["course_id", "status"], name="idx_course_progress_course"),
            models.Index(fields=["student_profile_id", "status"], name="idx_course_progress_student"),
        ]


class ProgressEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_id = models.UUIDField(unique=True)
    event_type = models.CharField(max_length=80)
    aggregate_id = models.UUIDField()
    payload = models.JSONField()
    processed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "progress_events"
        indexes = [
            models.Index(fields=["event_type"], name="idx_progress_events_event_type"),
        ]
