from __future__ import annotations

from rest_framework import serializers

from .models import (
    Certificate,
    CertificateEligibility,
    GradeHistory,
    GradeRecord,
    GradeRecordStatus,
    GradingRule,
    GradingRuleType,
    ManualReview,
    PublishedResult,
)


GRADE_SORT_CHOICES = ["created_at", "-created_at", "updated_at", "-updated_at", "score", "-score"]


class GradingRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = GradingRule
        fields = [
            "id",
            "course_id",
            "assessment_id",
            "rule_type",
            "configuration",
            "created_by_profile_id",
            "created_at",
            "updated_at",
        ]


class GradingRuleCreateSerializer(serializers.Serializer):
    course_id = serializers.UUIDField()
    assessment_id = serializers.UUIDField(required=False, allow_null=True)
    rule_type = serializers.ChoiceField(choices=GradingRuleType.choices)
    configuration = serializers.JSONField(required=False)
    created_by_profile_id = serializers.UUIDField()

    def validate(self, attrs):
        attrs["configuration"] = attrs.get("configuration") or {}
        return attrs


class GradingRuleUpdateSerializer(serializers.Serializer):
    assessment_id = serializers.UUIDField(required=False, allow_null=True)
    rule_type = serializers.ChoiceField(choices=GradingRuleType.choices, required=False)
    configuration = serializers.JSONField(required=False)


class GradingRuleSearchSerializer(serializers.Serializer):
    course_id = serializers.UUIDField(required=False)
    assessment_id = serializers.UUIDField(required=False)
    rule_type = serializers.ChoiceField(choices=GradingRuleType.choices, required=False)


class GradeHistorySerializer(serializers.ModelSerializer):
    grade_record_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = GradeHistory
        fields = [
            "id",
            "grade_record_id",
            "previous_score",
            "new_score",
            "changed_by_profile_id",
            "change_reason",
            "created_at",
        ]


class ManualReviewSerializer(serializers.ModelSerializer):
    grade_record_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = ManualReview
        fields = [
            "id",
            "grade_record_id",
            "reviewer_profile_id",
            "status",
            "feedback",
            "reviewed_at",
            "created_at",
            "updated_at",
        ]


class GradeRecordSerializer(serializers.ModelSerializer):
    history = GradeHistorySerializer(many=True, read_only=True)
    manual_reviews = ManualReviewSerializer(many=True, read_only=True)

    class Meta:
        model = GradeRecord
        fields = [
            "id",
            "student_profile_id",
            "course_id",
            "assessment_id",
            "submission_id",
            "score",
            "max_score",
            "status",
            "published_at",
            "history",
            "manual_reviews",
            "created_at",
            "updated_at",
        ]


class GradeRecordSearchSerializer(serializers.Serializer):
    student_profile_id = serializers.UUIDField(required=False)
    course_id = serializers.UUIDField(required=False)
    assessment_id = serializers.UUIDField(required=False)
    submission_id = serializers.UUIDField(required=False)
    status = serializers.ChoiceField(choices=GradeRecordStatus.choices, required=False)
    sort = serializers.ChoiceField(choices=GRADE_SORT_CHOICES, default="-updated_at", required=False)


class GradeCalculateSerializer(serializers.Serializer):
    submission_type = serializers.ChoiceField(choices=["quiz_attempt"])
    submission_id = serializers.UUIDField()
    rule_id = serializers.UUIDField(required=False, allow_null=True)


class ManualReviewCreateSerializer(serializers.Serializer):
    submission_type = serializers.ChoiceField(choices=["quiz_attempt", "assignment_submission"])
    submission_id = serializers.UUIDField()
    reviewer_profile_id = serializers.UUIDField(required=False, allow_null=True)


class ManualReviewCompleteSerializer(serializers.Serializer):
    score = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=0)
    feedback = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class GradeOverrideSerializer(serializers.Serializer):
    score = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=0)
    max_score = serializers.DecimalField(max_digits=8, decimal_places=2, required=False, min_value=0)
    change_reason = serializers.CharField(allow_blank=False)


class GradePublishSerializer(serializers.Serializer):
    published_feedback = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class PublishedResultSerializer(serializers.ModelSerializer):
    grade_record_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = PublishedResult
        fields = [
            "id",
            "grade_record_id",
            "student_profile_id",
            "course_id",
            "published_score",
            "published_feedback",
            "published_by_profile_id",
            "published_at",
        ]


class PublishedResultSearchSerializer(serializers.Serializer):
    student_profile_id = serializers.UUIDField(required=False)
    course_id = serializers.UUIDField(required=False)


class CertificateEligibilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = CertificateEligibility
        fields = [
            "id",
            "student_profile_id",
            "course_id",
            "eligible",
            "reason",
            "evaluated_at",
            "created_at",
            "updated_at",
        ]


class CertificateSerializer(serializers.ModelSerializer):
    certificate_eligibility_id = serializers.UUIDField(read_only=True)
    valid = serializers.SerializerMethodField()

    class Meta:
        model = Certificate
        fields = [
            "id",
            "certificate_eligibility_id",
            "student_profile_id",
            "course_id",
            "certificate_number",
            "certificate_asset_id",
            "issued_at",
            "revoked_at",
            "valid",
        ]

    def get_valid(self, certificate: Certificate) -> bool:
        return certificate.revoked_at is None


class CertificateEligibilitySearchSerializer(serializers.Serializer):
    student_profile_id = serializers.UUIDField(required=False)
    course_id = serializers.UUIDField(required=False)
    eligible = serializers.BooleanField(required=False)


class CertificateEligibilityEvaluateSerializer(serializers.Serializer):
    student_profile_id = serializers.UUIDField()
    course_id = serializers.UUIDField()
    certificate_asset_id = serializers.UUIDField(required=False, allow_null=True)


class CertificateSearchSerializer(serializers.Serializer):
    student_profile_id = serializers.UUIDField(required=False)
    course_id = serializers.UUIDField(required=False)
    include_revoked = serializers.BooleanField(required=False, default=False)


class CertificateAssetUpdateSerializer(serializers.Serializer):
    certificate_asset_id = serializers.UUIDField(required=False, allow_null=True)
