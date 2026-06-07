from rest_framework import serializers

from .models import (
    AccessGrant,
    BatchEnrollment,
    CohortEnrollment,
    Enrollment,
    EnrollmentHistory,
    EnrollmentStatus,
)


ENROLLMENT_SORT_CHOICES = ["created_at", "-created_at", "updated_at", "-updated_at", "status", "-status"]


class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = [
            "id",
            "student_profile_id",
            "course_id",
            "institution_id",
            "status",
            "enrolled_by_profile_id",
            "enrolled_at",
            "completed_at",
            "expires_at",
            "created_at",
            "updated_at",
        ]


class EnrollmentCreateSerializer(serializers.Serializer):
    student_profile_id = serializers.UUIDField()
    course_id = serializers.UUIDField()
    institution_id = serializers.UUIDField()
    enrolled_by_profile_id = serializers.UUIDField(required=False, allow_null=True)
    expires_at = serializers.DateTimeField(required=False, allow_null=True)


class EnrollmentTransitionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=EnrollmentStatus.choices)
    changed_by_profile_id = serializers.UUIDField(required=False, allow_null=True)
    reason = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class EnrollmentSearchSerializer(serializers.Serializer):
    student_profile_id = serializers.UUIDField(required=False)
    course_id = serializers.UUIDField(required=False)
    institution_id = serializers.UUIDField(required=False)
    status = serializers.ChoiceField(choices=EnrollmentStatus.choices, required=False)
    sort = serializers.ChoiceField(choices=ENROLLMENT_SORT_CHOICES, default="-created_at", required=False)


class EnrollmentHistorySerializer(serializers.ModelSerializer):
    enrollment_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = EnrollmentHistory
        fields = [
            "id",
            "enrollment_id",
            "from_status",
            "to_status",
            "changed_by_profile_id",
            "reason",
            "created_at",
        ]


class AccessGrantSerializer(serializers.ModelSerializer):
    enrollment_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = AccessGrant
        fields = [
            "id",
            "enrollment_id",
            "student_profile_id",
            "course_id",
            "access_status",
            "valid_from",
            "valid_until",
            "created_at",
            "updated_at",
        ]


class AccessCheckSerializer(serializers.Serializer):
    student_profile_id = serializers.UUIDField()
    course_id = serializers.UUIDField()


class BatchEnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = BatchEnrollment
        fields = ["id", "batch_id", "course_id", "requested_by_profile_id", "status", "summary", "created_at", "updated_at"]


class CohortEnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CohortEnrollment
        fields = ["id", "cohort_id", "course_id", "requested_by_profile_id", "status", "summary", "created_at", "updated_at"]


class BatchEnrollmentCreateSerializer(serializers.Serializer):
    batch_id = serializers.UUIDField()
    course_id = serializers.UUIDField()
    institution_id = serializers.UUIDField()
    requested_by_profile_id = serializers.UUIDField()
    student_profile_ids = serializers.ListField(child=serializers.UUIDField(), allow_empty=True)


class CohortEnrollmentCreateSerializer(serializers.Serializer):
    cohort_id = serializers.UUIDField()
    course_id = serializers.UUIDField()
    institution_id = serializers.UUIDField()
    requested_by_profile_id = serializers.UUIDField()
    student_profile_ids = serializers.ListField(child=serializers.UUIDField(), allow_empty=True)
