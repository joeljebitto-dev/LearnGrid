from django.db.models import QuerySet

from .models import AssessmentProgress, CourseProgress, LessonProgress, ProgressEvent, VideoProgress


def lesson_progress_queryset() -> QuerySet[LessonProgress]:
    return LessonProgress.objects.all()


def video_progress_queryset() -> QuerySet[VideoProgress]:
    return VideoProgress.objects.all()


def assessment_progress_queryset() -> QuerySet[AssessmentProgress]:
    return AssessmentProgress.objects.all()


def course_progress_queryset() -> QuerySet[CourseProgress]:
    return CourseProgress.objects.all()


def progress_event_queryset() -> QuerySet[ProgressEvent]:
    return ProgressEvent.objects.all()
