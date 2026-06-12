from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from django.conf import settings
from django.utils import timezone
from learngrid_events import DuplicateEvent
from learngrid_events import publish_event as publish_kafka_event

from .models import (
    AssessmentProgress,
    AssessmentProgressStatus,
    CourseProgress,
    CourseProgressStatus,
    LessonProgress,
    LessonProgressStatus,
    ProgressEvent,
    VideoProgress,
)


logger = logging.getLogger(__name__)


def update_lesson_progress(*, validated_data: dict[str, Any]) -> LessonProgress:
    completed = validated_data.get("status") == LessonProgressStatus.COMPLETED
    progress, _created = LessonProgress.objects.get_or_create(
        student_profile_id=validated_data["student_profile_id"],
        lesson_id=validated_data["lesson_id"],
        defaults={
            "course_id": validated_data["course_id"],
            "status": LessonProgressStatus.NOT_STARTED,
        },
    )
    progress.course_id = validated_data["course_id"]
    progress.view_count += validated_data.get("view_increment", 1)
    progress.first_viewed_at = progress.first_viewed_at or timezone.now()
    progress.status = validated_data.get("status") or LessonProgressStatus.IN_PROGRESS
    if completed and progress.completed_at is None:
        progress.completed_at = timezone.now()
    progress.save()
    recalculate_course_progress(
        student_profile_id=progress.student_profile_id,
        course_id=progress.course_id,
        total_lessons=validated_data.get("total_lessons"),
        total_assessments=validated_data.get("total_assessments"),
    )
    return progress


def update_video_progress(*, validated_data: dict[str, Any]) -> VideoProgress:
    duration = validated_data.get("duration_seconds")
    position = validated_data.get("last_position_seconds", 0)
    percent = validated_data.get("percent_complete")
    if percent is None and duration:
        percent = min(Decimal("100.00"), Decimal(position * 100) / Decimal(duration))
    percent = Decimal(str(percent or 0)).quantize(Decimal("0.01"))
    progress, _created = VideoProgress.objects.get_or_create(
        student_profile_id=validated_data["student_profile_id"],
        content_asset_id=validated_data["content_asset_id"],
        defaults={"course_id": validated_data["course_id"]},
    )
    progress.course_id = validated_data["course_id"]
    progress.last_position_seconds = max(progress.last_position_seconds, position)
    progress.duration_seconds = duration or progress.duration_seconds
    progress.percent_complete = max(progress.percent_complete, percent)
    if progress.percent_complete >= Decimal("100.00") and progress.completed_at is None:
        progress.completed_at = timezone.now()
    progress.save()
    recalculate_course_progress(
        student_profile_id=progress.student_profile_id,
        course_id=progress.course_id,
        total_lessons=validated_data.get("total_lessons"),
        total_assessments=validated_data.get("total_assessments"),
    )
    return progress


def update_assessment_progress(*, validated_data: dict[str, Any]) -> AssessmentProgress:
    progress, _created = AssessmentProgress.objects.get_or_create(
        student_profile_id=validated_data["student_profile_id"],
        assessment_id=validated_data["assessment_id"],
        defaults={"course_id": validated_data["course_id"]},
    )
    progress.course_id = validated_data["course_id"]
    progress.status = validated_data.get("status") or AssessmentProgressStatus.SUBMITTED
    progress.attempt_count += validated_data.get("attempt_increment", 1)
    if progress.status in {AssessmentProgressStatus.SUBMITTED, AssessmentProgressStatus.GRADED}:
        progress.last_submitted_at = timezone.now()
    progress.save()
    recalculate_course_progress(
        student_profile_id=progress.student_profile_id,
        course_id=progress.course_id,
        total_lessons=validated_data.get("total_lessons"),
        total_assessments=validated_data.get("total_assessments"),
    )
    return progress


def recalculate_course_progress(*, student_profile_id, course_id, total_lessons=None, total_assessments=None) -> CourseProgress:
    lessons_completed = LessonProgress.objects.filter(
        student_profile_id=student_profile_id,
        course_id=course_id,
        status=LessonProgressStatus.COMPLETED,
    ).count()
    assessments_completed = AssessmentProgress.objects.filter(
        student_profile_id=student_profile_id,
        course_id=course_id,
        status__in=[AssessmentProgressStatus.SUBMITTED, AssessmentProgressStatus.GRADED],
    ).count()
    lesson_total = max(total_lessons or 0, lessons_completed)
    assessment_total = max(total_assessments or 0, assessments_completed)
    total_items = lesson_total + assessment_total
    completed_items = lessons_completed + assessments_completed
    percent = Decimal("0.00")
    if total_items:
        percent = (Decimal(completed_items * 100) / Decimal(total_items)).quantize(Decimal("0.01"))
    progress, _created = CourseProgress.objects.get_or_create(
        student_profile_id=student_profile_id,
        course_id=course_id,
    )
    previous_status = progress.status
    progress.lessons_completed = lessons_completed
    progress.assessments_completed = assessments_completed
    progress.completion_percent = percent
    if percent >= Decimal("100.00") and total_items > 0:
        progress.status = CourseProgressStatus.COMPLETED
        progress.completed_at = progress.completed_at or timezone.now()
    elif completed_items == 0:
        progress.status = CourseProgressStatus.NOT_STARTED
        progress.completed_at = None
    else:
        progress.status = CourseProgressStatus.IN_PROGRESS
        progress.completed_at = None
    progress.save()
    publish_progress_event(
        event_type="CourseCompleted" if progress.status == CourseProgressStatus.COMPLETED and previous_status != CourseProgressStatus.COMPLETED else "CourseProgressUpdated",
        aggregate_id=progress.id,
        payload={
            "student_profile_id": str(student_profile_id),
            "course_id": str(course_id),
            "completion_percent": str(progress.completion_percent),
            "status": progress.status,
        },
    )
    return progress


def process_progress_event(*, event_id, event_type: str, aggregate_id, payload: dict[str, Any]) -> dict[str, Any]:
    if ProgressEvent.objects.filter(event_id=event_id).exists():
        return {"status": "duplicate", "event_id": str(event_id)}
    ProgressEvent.objects.create(
        event_id=event_id,
        event_type=event_type,
        aggregate_id=aggregate_id,
        payload=payload,
    )
    if event_type == "LessonViewed":
        update_lesson_progress(validated_data={**payload, "status": LessonProgressStatus.IN_PROGRESS})
    elif event_type == "VideoCompleted":
        update_video_progress(validated_data={**payload, "percent_complete": 100})
    elif event_type in {"QuizSubmitted", "AssignmentSubmitted"}:
        update_assessment_progress(validated_data={**payload, "status": AssessmentProgressStatus.SUBMITTED})
    return {"status": "processed", "event_id": str(event_id)}


def publish_progress_event(*, event_type: str, aggregate_id, payload: dict[str, Any]) -> dict[str, Any]:
    event = publish_kafka_event(
        event_type=event_type,
        aggregate_id=aggregate_id,
        producer_service=settings.SERVICE_NAME,
        payload=payload,
    )
    logger.info("progress_event %s", event)
    return event


def handle_kafka_progress_event(event: dict[str, Any]) -> dict[str, Any]:
    if event["event_type"] not in {"LessonViewed", "VideoCompleted", "QuizSubmitted", "AssignmentSubmitted"}:
        return {"status": "skipped", "event_id": event["event_id"]}
    result = process_progress_event(
        event_id=event["event_id"],
        event_type=event["event_type"],
        aggregate_id=event["aggregate_id"],
        payload=event["payload"],
    )
    if result["status"] == "duplicate":
        raise DuplicateEvent()
    return result
