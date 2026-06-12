from __future__ import annotations

import uuid

from django.db import models


class ContentAssetType(models.TextChoices):
    VIDEO = "video", "Video"
    PDF = "pdf", "PDF"
    DOCUMENT = "document", "Document"
    IMAGE = "image", "Image"
    LINK = "link", "Link"
    ASSIGNMENT_RESOURCE = "assignment_resource", "Assignment Resource"


class ContentAssetStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"
    DELETED = "deleted", "Deleted"
    QUARANTINED = "quarantined", "Quarantined"


class ContentPermissionGranteeType(models.TextChoices):
    PROFILE = "profile", "Profile"
    COURSE = "course", "Course"
    INSTITUTION = "institution", "Institution"
    ROLE = "role", "Role"


class ContentPermissionValue(models.TextChoices):
    VIEW = "view", "View"
    DOWNLOAD = "download", "Download"
    MANAGE = "manage", "Manage"


class ContentAsset(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    institution_id = models.UUIDField()
    owner_profile_id = models.UUIDField()
    asset_type = models.CharField(max_length=32, choices=ContentAssetType.choices)
    title = models.CharField(max_length=255)
    status = models.CharField(
        max_length=24,
        choices=ContentAssetStatus.choices,
        default=ContentAssetStatus.DRAFT,
    )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "content_assets"
        indexes = [
            models.Index(
                fields=["institution_id", "status"], name="idx_content_assets_inst_status"
            ),
            models.Index(fields=["owner_profile_id"], name="idx_content_assets_owner"),
            models.Index(fields=["asset_type"], name="idx_content_assets_asset_type"),
        ]

    def __str__(self) -> str:
        return self.title


class FileMetadata(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content_asset = models.OneToOneField(
        ContentAsset,
        on_delete=models.CASCADE,
        related_name="file_metadata",
    )
    storage_provider = models.CharField(max_length=32)
    bucket_name = models.CharField(max_length=255)
    object_key = models.TextField()
    file_name = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=128)
    file_size_bytes = models.BigIntegerField()
    checksum_sha256 = models.CharField(max_length=64, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "file_metadata"
        indexes = [
            models.Index(fields=["mime_type"], name="idx_file_metadata_mime_type"),
            models.Index(fields=["object_key"], name="idx_file_metadata_object_key"),
        ]

    def __str__(self) -> str:
        return self.file_name


class ContentPermission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content_asset = models.ForeignKey(
        ContentAsset,
        on_delete=models.CASCADE,
        related_name="permissions",
    )
    grantee_type = models.CharField(max_length=32, choices=ContentPermissionGranteeType.choices)
    grantee_id = models.UUIDField()
    permission = models.CharField(
        max_length=32,
        choices=ContentPermissionValue.choices,
        default=ContentPermissionValue.VIEW,
    )
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "content_permissions"
        constraints = [
            models.UniqueConstraint(
                fields=["content_asset", "grantee_type", "grantee_id", "permission"],
                name="uq_content_permissions_grant",
            ),
        ]
        indexes = [
            models.Index(fields=["content_asset"], name="idx_content_permissions_asset"),
            models.Index(fields=["grantee_type", "grantee_id"], name="idx_content_perms_grantee"),
        ]


class SignedAccessRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content_asset = models.ForeignKey(
        ContentAsset,
        on_delete=models.CASCADE,
        related_name="signed_access_records",
    )
    requested_by_profile_id = models.UUIDField()
    access_token_hash = models.TextField()
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "signed_access_records"
        indexes = [
            models.Index(fields=["content_asset"], name="idx_signed_access_asset"),
            models.Index(fields=["requested_by_profile_id"], name="idx_signed_access_profile"),
            models.Index(fields=["expires_at"], name="idx_signed_access_expires"),
        ]


class ContentVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content_asset = models.ForeignKey(
        ContentAsset,
        on_delete=models.CASCADE,
        related_name="versions",
    )
    version_number = models.PositiveIntegerField()
    file_metadata = models.ForeignKey(
        FileMetadata,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="content_versions",
    )
    change_note = models.TextField(null=True, blank=True)
    created_by_profile_id = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "content_versions"
        constraints = [
            models.UniqueConstraint(
                fields=["content_asset", "version_number"],
                name="uq_content_versions_asset_version",
            ),
        ]
        indexes = [
            models.Index(fields=["content_asset"], name="idx_content_versions_asset"),
        ]
        ordering = ["-version_number", "id"]
