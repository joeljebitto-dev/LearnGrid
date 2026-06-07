from rest_framework import serializers

from .models import (
    ContentAsset,
    ContentAssetStatus,
    ContentAssetType,
    ContentPermission,
    ContentPermissionGranteeType,
    ContentPermissionValue,
    ContentVersion,
    FileMetadata,
)


ASSET_SORT_CHOICES = [
    "title",
    "-title",
    "asset_type",
    "-asset_type",
    "status",
    "-status",
    "created_at",
    "-created_at",
    "updated_at",
    "-updated_at",
]


class FileMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileMetadata
        fields = [
            "id",
            "storage_provider",
            "bucket_name",
            "object_key",
            "file_name",
            "mime_type",
            "file_size_bytes",
            "checksum_sha256",
            "created_at",
        ]


class ContentAssetSerializer(serializers.ModelSerializer):
    file_metadata = FileMetadataSerializer(read_only=True)

    class Meta:
        model = ContentAsset
        fields = [
            "id",
            "institution_id",
            "owner_profile_id",
            "asset_type",
            "title",
            "status",
            "metadata",
            "file_metadata",
            "created_at",
            "updated_at",
            "deleted_at",
        ]


class FileMetadataPayloadSerializer(serializers.Serializer):
    storage_provider = serializers.CharField(required=False, allow_blank=True, max_length=32)
    bucket_name = serializers.CharField(required=False, allow_blank=True, max_length=255)
    object_key = serializers.CharField()
    file_name = serializers.CharField(max_length=255)
    mime_type = serializers.CharField(max_length=128)
    file_size_bytes = serializers.IntegerField(min_value=1)
    checksum_sha256 = serializers.RegexField(
        regex=r"^[0-9a-fA-F]{64}$",
        required=False,
        allow_null=True,
    )


class ContentAssetCreateSerializer(serializers.Serializer):
    institution_id = serializers.UUIDField()
    owner_profile_id = serializers.UUIDField()
    asset_type = serializers.ChoiceField(choices=ContentAssetType.choices)
    title = serializers.CharField(max_length=255)
    metadata = serializers.JSONField(required=False)
    file = FileMetadataPayloadSerializer(required=False)

    def validate(self, attrs):
        attrs["metadata"] = attrs.get("metadata") or {}
        if attrs["asset_type"] != ContentAssetType.LINK and "file" not in attrs:
            raise serializers.ValidationError({"file": "File metadata is required for uploaded assets."})
        return attrs


class PresignedUploadCreateSerializer(serializers.Serializer):
    institution_id = serializers.UUIDField()
    owner_profile_id = serializers.UUIDField()
    asset_type = serializers.ChoiceField(choices=ContentAssetType.choices)
    title = serializers.CharField(max_length=255)
    metadata = serializers.JSONField(required=False)
    file_name = serializers.CharField(max_length=255)
    mime_type = serializers.CharField(max_length=128)
    file_size_bytes = serializers.IntegerField(min_value=1)
    checksum_sha256 = serializers.RegexField(
        regex=r"^[0-9a-fA-F]{64}$",
        required=False,
        allow_null=True,
    )

    def validate(self, attrs):
        if attrs["asset_type"] == ContentAssetType.LINK:
            raise serializers.ValidationError({"asset_type": "Link assets do not use object uploads."})
        attrs["metadata"] = attrs.get("metadata") or {}
        return attrs


class PresignedUploadCompleteSerializer(serializers.Serializer):
    checksum_sha256 = serializers.RegexField(
        regex=r"^[0-9a-fA-F]{64}$",
        required=False,
        allow_null=True,
    )


class ProxyUploadCreateSerializer(serializers.Serializer):
    institution_id = serializers.UUIDField()
    owner_profile_id = serializers.UUIDField()
    asset_type = serializers.ChoiceField(choices=ContentAssetType.choices)
    title = serializers.CharField(max_length=255)
    metadata = serializers.JSONField(required=False)
    file = serializers.FileField()

    def validate(self, attrs):
        if attrs["asset_type"] == ContentAssetType.LINK:
            raise serializers.ValidationError({"asset_type": "Link assets do not use object uploads."})
        attrs["metadata"] = attrs.get("metadata") or {}
        return attrs


class ContentAssetUpdateSerializer(serializers.Serializer):
    asset_type = serializers.ChoiceField(choices=ContentAssetType.choices, required=False)
    title = serializers.CharField(required=False, max_length=255)
    metadata = serializers.JSONField(required=False)


class ContentAssetSearchSerializer(serializers.Serializer):
    institution_id = serializers.UUIDField(required=False)
    owner_profile_id = serializers.UUIDField(required=False)
    asset_type = serializers.ChoiceField(choices=ContentAssetType.choices, required=False)
    status = serializers.ChoiceField(choices=ContentAssetStatus.choices, required=False)
    q = serializers.CharField(required=False, allow_blank=True, max_length=255)
    sort = serializers.ChoiceField(choices=ASSET_SORT_CHOICES, default="-created_at", required=False)


class ContentPermissionSerializer(serializers.ModelSerializer):
    content_asset_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = ContentPermission
        fields = [
            "id",
            "content_asset_id",
            "grantee_type",
            "grantee_id",
            "permission",
            "expires_at",
            "created_at",
        ]


class ContentPermissionCreateSerializer(serializers.Serializer):
    grantee_type = serializers.ChoiceField(choices=ContentPermissionGranteeType.choices)
    grantee_id = serializers.UUIDField()
    permission = serializers.ChoiceField(
        choices=ContentPermissionValue.choices,
        default=ContentPermissionValue.VIEW,
        required=False,
    )
    expires_at = serializers.DateTimeField(required=False, allow_null=True)


class SignedAccessCreateSerializer(serializers.Serializer):
    requested_by_profile_id = serializers.UUIDField()


class ContentVersionSerializer(serializers.ModelSerializer):
    content_asset_id = serializers.UUIDField(read_only=True)
    file_metadata_id = serializers.UUIDField(read_only=True, allow_null=True)

    class Meta:
        model = ContentVersion
        fields = [
            "id",
            "content_asset_id",
            "version_number",
            "file_metadata_id",
            "change_note",
            "created_by_profile_id",
            "created_at",
        ]


class ContentVersionCreateSerializer(serializers.Serializer):
    created_by_profile_id = serializers.UUIDField()
    change_note = serializers.CharField(required=False, allow_blank=True, allow_null=True)
