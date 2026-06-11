from .selectors import PLATFORM_SCOPE_ID
from rest_framework import serializers

from .models import (
    DashboardAggregate,
    DashboardScopeType,
    EventFact,
    ReportSnapshot,
    ReportType,
    SearchIndexRecord,
    SearchResourceType,
    UsageMetric,
)


class EventIngestSerializer(serializers.Serializer):
    event_id = serializers.UUIDField()
    event_type = serializers.CharField(max_length=80)
    producer_service = serializers.CharField(max_length=80)
    aggregate_id = serializers.UUIDField()
    institution_id = serializers.UUIDField(required=False, allow_null=True)
    occurred_at = serializers.DateTimeField()
    payload = serializers.JSONField(required=False)

    def validate(self, attrs):
        attrs["payload"] = attrs.get("payload") or {}
        return attrs


class EventFactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventFact
        fields = [
            "id",
            "event_id",
            "event_type",
            "producer_service",
            "aggregate_id",
            "institution_id",
            "occurred_at",
            "payload",
            "ingested_at",
        ]


class ReportSnapshotCreateSerializer(serializers.Serializer):
    institution_id = serializers.UUIDField(required=False, allow_null=True)
    report_type = serializers.ChoiceField(choices=ReportType.choices, default=ReportType.DASHBOARD)
    parameters = serializers.JSONField(required=False)
    result_payload = serializers.JSONField(required=False)

    def validate(self, attrs):
        attrs["parameters"] = attrs.get("parameters") or {}
        attrs["result_payload"] = attrs.get("result_payload") or {}
        return attrs


class ReportSnapshotSearchSerializer(serializers.Serializer):
    institution_id = serializers.UUIDField(required=False, allow_null=True)
    report_type = serializers.ChoiceField(choices=ReportType.choices, required=False)


class ReportSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportSnapshot
        fields = [
            "id",
            "institution_id",
            "report_type",
            "parameters",
            "result_payload",
            "generated_by_profile_id",
            "generated_at",
        ]


class SearchQuerySerializer(serializers.Serializer):
    q = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)
    institution_id = serializers.UUIDField(required=False, allow_null=True)
    resource_type = serializers.ChoiceField(choices=SearchResourceType.choices, required=False)
    status = serializers.CharField(required=False, allow_blank=True)
    course_id = serializers.UUIDField(required=False, allow_null=True)
    profile_type = serializers.CharField(required=False, allow_blank=True)
    assessment_type = serializers.CharField(required=False, allow_blank=True)
    submission_status = serializers.CharField(required=False, allow_blank=True)
    sort = serializers.ChoiceField(
        choices=["updated_at", "-updated_at", "resource_type"],
        default="-updated_at",
        required=False,
    )


class SearchIndexRecordUpsertSerializer(serializers.Serializer):
    resource_type = serializers.ChoiceField(choices=SearchResourceType.choices)
    resource_id = serializers.UUIDField()
    institution_id = serializers.UUIDField(required=False, allow_null=True)
    search_text = serializers.CharField(trim_whitespace=True)
    metadata = serializers.JSONField(required=False)

    def validate(self, attrs):
        attrs["metadata"] = attrs.get("metadata") or {}
        return attrs


class SearchIndexRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchIndexRecord
        fields = [
            "id",
            "resource_type",
            "resource_id",
            "institution_id",
            "search_text",
            "metadata",
            "updated_at",
        ]


class DashboardAggregateSearchSerializer(serializers.Serializer):
    scope_type = serializers.ChoiceField(choices=DashboardScopeType.choices, required=False)
    scope_id = serializers.UUIDField(required=False, allow_null=True)
    institution_id = serializers.UUIDField(required=False, allow_null=True)
    metric_date = serializers.DateField(required=False)
    sort = serializers.ChoiceField(
        choices=["metric_date", "-metric_date", "computed_at", "-computed_at"],
        default="-metric_date",
        required=False,
    )


class DashboardAggregateUpsertSerializer(serializers.Serializer):
    scope_type = serializers.ChoiceField(choices=DashboardScopeType.choices)
    scope_id = serializers.UUIDField(required=False, allow_null=True)
    metric_date = serializers.DateField()
    metrics = serializers.JSONField(required=False)

    def validate(self, attrs):
        if attrs["scope_type"] == DashboardScopeType.PLATFORM and not attrs.get("scope_id"):
            attrs["scope_id"] = PLATFORM_SCOPE_ID
        if not attrs.get("scope_id"):
            raise serializers.ValidationError({"scope_id": "This field is required."})
        attrs["metrics"] = attrs.get("metrics") or {}
        return attrs


class DashboardAggregateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardAggregate
        fields = [
            "id",
            "scope_type",
            "scope_id",
            "metric_date",
            "metrics",
            "computed_at",
        ]


class UsageMetricSearchSerializer(serializers.Serializer):
    metric_name = serializers.CharField(required=False, allow_blank=True)
    scope_type = serializers.CharField(required=False, allow_blank=True)
    scope_id = serializers.UUIDField(required=False, allow_null=True)
    bucket_start_at = serializers.DateTimeField(required=False)
    bucket_end_at = serializers.DateTimeField(required=False)
    sort = serializers.ChoiceField(
        choices=["bucket_start_at", "-bucket_start_at", "metric_name"],
        default="-bucket_start_at",
        required=False,
    )


class UsageMetricCreateSerializer(serializers.Serializer):
    metric_name = serializers.CharField(max_length=128)
    metric_value = serializers.DecimalField(max_digits=18, decimal_places=4)
    scope_type = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    scope_id = serializers.UUIDField(required=False, allow_null=True)
    bucket_start_at = serializers.DateTimeField()
    bucket_end_at = serializers.DateTimeField()


class UsageMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsageMetric
        fields = [
            "id",
            "metric_name",
            "metric_value",
            "scope_type",
            "scope_id",
            "bucket_start_at",
            "bucket_end_at",
            "created_at",
        ]


class ReportGenerateSerializer(serializers.Serializer):
    institution_id = serializers.UUIDField(required=False, allow_null=True)
    report_type = serializers.ChoiceField(
        choices=[
            ReportType.ACTIVE_USERS,
            ReportType.ENROLLMENTS,
            ReportType.COMPLETION_RATES,
            ReportType.ASSESSMENT_RESULTS,
            ReportType.SYSTEM_USAGE,
        ]
    )
    parameters = serializers.JSONField(required=False)

    def validate(self, attrs):
        attrs["parameters"] = attrs.get("parameters") or {}
        return attrs
