from rest_framework import serializers

from .models import (
    AssessmentProgress,
    AssessmentProgressStatus,
    CourseProgress,
    LessonProgress,
    LessonProgressStatus,
    ProgressEvent,
    VideoProgress,
)


class LessonProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonProgress
        fields = [
            "id",
            "student_profile_id",
            "course_id",
            "lesson_id",
            "status",
            "view_count",
            "first_viewed_at",
            "completed_at",
            "updated_at",
        ]


class LessonProgressUpdateSerializer(serializers.Serializer):
    student_profile_id = serializers.UUIDField()
    course_id = serializers.UUIDField()
    lesson_id = serializers.UUIDField()
    status = serializers.ChoiceField(choices=LessonProgressStatus.choices, required=False)
    view_increment = serializers.IntegerField(required=False, min_value=0, default=1)
    total_lessons = serializers.IntegerField(required=False, min_value=0)
    total_assessments = serializers.IntegerField(required=False, min_value=0)


class VideoProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoProgress
        fields = [
            "id",
            "student_profile_id",
            "content_asset_id",
            "course_id",
            "last_position_seconds",
            "duration_seconds",
            "percent_complete",
            "completed_at",
            "updated_at",
        ]


class VideoProgressUpdateSerializer(serializers.Serializer):
    student_profile_id = serializers.UUIDField()
    content_asset_id = serializers.UUIDField()
    course_id = serializers.UUIDField()
    last_position_seconds = serializers.IntegerField(required=False, min_value=0, default=0)
    duration_seconds = serializers.IntegerField(required=False, min_value=1)
    percent_complete = serializers.DecimalField(required=False, max_digits=5, decimal_places=2, min_value=0, max_value=100)
    total_lessons = serializers.IntegerField(required=False, min_value=0)
    total_assessments = serializers.IntegerField(required=False, min_value=0)


class AssessmentProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentProgress
        fields = [
            "id",
            "student_profile_id",
            "assessment_id",
            "course_id",
            "status",
            "attempt_count",
            "last_submitted_at",
            "updated_at",
        ]


class AssessmentProgressUpdateSerializer(serializers.Serializer):
    student_profile_id = serializers.UUIDField()
    assessment_id = serializers.UUIDField()
    course_id = serializers.UUIDField()
    status = serializers.ChoiceField(choices=AssessmentProgressStatus.choices, required=False)
    attempt_increment = serializers.IntegerField(required=False, min_value=0, default=1)
    total_lessons = serializers.IntegerField(required=False, min_value=0)
    total_assessments = serializers.IntegerField(required=False, min_value=0)


class CourseProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseProgress
        fields = [
            "id",
            "student_profile_id",
            "course_id",
            "completion_percent",
            "lessons_completed",
            "assessments_completed",
            "status",
            "completed_at",
            "updated_at",
        ]


class CourseProgressSearchSerializer(serializers.Serializer):
    student_profile_id = serializers.UUIDField(required=False)
    course_id = serializers.UUIDField(required=False)
    status = serializers.CharField(required=False)


class ProgressEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgressEvent
        fields = ["id", "event_id", "event_type", "aggregate_id", "payload", "processed_at"]


class ProgressEventIngestSerializer(serializers.Serializer):
    event_id = serializers.UUIDField()
    event_type = serializers.ChoiceField(
        choices=["LessonViewed", "VideoCompleted", "QuizSubmitted", "AssignmentSubmitted"]
    )
    aggregate_id = serializers.UUIDField()
    payload = serializers.JSONField()
