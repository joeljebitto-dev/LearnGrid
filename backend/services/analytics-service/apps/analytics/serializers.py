from rest_framework import serializers

from .models import EventFact, ReportSnapshot, ReportType


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
