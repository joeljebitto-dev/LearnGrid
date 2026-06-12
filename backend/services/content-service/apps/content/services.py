from __future__ import annotations

import hashlib
import hmac
import logging
import os
import re
import secrets
import shlex
import subprocess
import tempfile
import uuid
from datetime import timedelta
from io import BytesIO
from pathlib import PurePath
from typing import Any

from django.conf import settings
from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from learngrid_events import publish_event as publish_kafka_event
from rest_framework.exceptions import PermissionDenied, ValidationError

from .models import (
    ContentAsset,
    ContentAssetStatus,
    ContentPermission,
    ContentPermissionValue,
    ContentVersion,
    FileMetadata,
    SignedAccessRecord,
)
from .storage import (
    generate_presigned_download_url,
    generate_presigned_upload_url,
    stat_storage_object,
    storage_bucket,
    storage_provider,
    upload_storage_object,
)


logger = logging.getLogger(__name__)
UPLOAD_STATUS_COMPLETE = "complete"
UPLOAD_STATUS_PENDING = "pending"


def validate_file_metadata(
    *,
    mime_type: str,
    file_size_bytes: int,
    file_name: str | None = None,
    object_key: str | None = None,
) -> None:
    if mime_type not in settings.CONTENT_ALLOWED_MIME_TYPES:
        raise ValidationError({"mime_type": "File type is not allowed."})
    if file_size_bytes <= 0:
        raise ValidationError({"file_size_bytes": "File size must be greater than zero."})
    if file_size_bytes > settings.CONTENT_MAX_UPLOAD_SIZE_BYTES:
        raise ValidationError({"file_size_bytes": "File size exceeds the configured limit."})
    if file_name:
        validate_file_name(file_name)
    if object_key:
        validate_object_key(object_key)


def create_asset(
    *, validated_data: dict[str, Any], correlation_id: str | None = None
) -> ContentAsset:
    file_data = validated_data.pop("file", None)
    if file_data:
        provider = validate_minio_provider(file_data)
        validate_file_metadata(
            mime_type=file_data["mime_type"],
            file_size_bytes=file_data["file_size_bytes"],
            file_name=file_data["file_name"],
            object_key=file_data["object_key"],
        )
        verify_storage_object_matches(file_data)
        scan_stored_object(file_data)
    with transaction.atomic():
        metadata = with_upload_metadata(
            validated_data.get("metadata"),
            status=UPLOAD_STATUS_COMPLETE if file_data else None,
            flow="metadata-registration" if file_data else None,
        )
        asset = ContentAsset.objects.create(**{**validated_data, "metadata": metadata})
        if file_data:
            FileMetadata.objects.create(
                content_asset=asset,
                storage_provider=provider,
                bucket_name=file_data.get("bucket_name") or storage_bucket(),
                object_key=file_data["object_key"],
                file_name=file_data["file_name"],
                mime_type=file_data["mime_type"],
                file_size_bytes=file_data["file_size_bytes"],
                checksum_sha256=file_data.get("checksum_sha256"),
            )
            create_content_version(
                asset=asset,
                created_by_profile_id=asset.owner_profile_id,
                change_note="Initial upload",
            )
    publish_content_event(
        event_type="ContentUploaded",
        aggregate_id=asset.id,
        correlation_id=correlation_id,
        payload={"institution_id": str(asset.institution_id), "status": asset.status},
    )
    return asset


def create_presigned_upload(
    *,
    validated_data: dict[str, Any],
    correlation_id: str | None = None,
) -> dict[str, Any]:
    validate_file_metadata(
        mime_type=validated_data["mime_type"],
        file_size_bytes=validated_data["file_size_bytes"],
        file_name=validated_data["file_name"],
    )
    asset_id = uuid.uuid4()
    object_key = build_object_key(
        institution_id=validated_data["institution_id"],
        asset_id=asset_id,
        file_name=validated_data["file_name"],
    )
    upload_url = generate_presigned_upload_url(object_key=object_key)
    expires_at = timezone.now() + timedelta(seconds=settings.CONTENT_PRESIGNED_UPLOAD_TTL_SECONDS)
    metadata = with_upload_metadata(
        validated_data.get("metadata"),
        status=UPLOAD_STATUS_PENDING,
        flow="presigned",
        correlation_id=correlation_id,
    )
    with transaction.atomic():
        asset = ContentAsset.objects.create(
            id=asset_id,
            institution_id=validated_data["institution_id"],
            owner_profile_id=validated_data["owner_profile_id"],
            asset_type=validated_data["asset_type"],
            title=validated_data["title"],
            metadata=metadata,
        )
        FileMetadata.objects.create(
            content_asset=asset,
            storage_provider=storage_provider(),
            bucket_name=storage_bucket(),
            object_key=object_key,
            file_name=validated_data["file_name"],
            mime_type=validated_data["mime_type"],
            file_size_bytes=validated_data["file_size_bytes"],
            checksum_sha256=validated_data.get("checksum_sha256"),
        )
    return {
        "asset": asset,
        "object_key": object_key,
        "upload_url": upload_url,
        "upload_headers": build_upload_headers(
            mime_type=validated_data["mime_type"],
            checksum_sha256=validated_data.get("checksum_sha256"),
        ),
        "expires_at": expires_at.isoformat(),
    }


def complete_presigned_upload(
    *,
    asset: ContentAsset,
    checksum_sha256: str | None = None,
    correlation_id: str | None = None,
) -> ContentAsset:
    file_metadata = require_file_metadata(asset)
    expected = {
        "object_key": file_metadata.object_key,
        "mime_type": file_metadata.mime_type,
        "file_size_bytes": file_metadata.file_size_bytes,
    }
    verify_storage_object_matches(expected)
    scan_stored_object(
        {
            **expected,
            "bucket_name": file_metadata.bucket_name,
            "file_name": file_metadata.file_name,
        }
    )
    if checksum_sha256:
        file_metadata.checksum_sha256 = checksum_sha256
        file_metadata.save(update_fields=["checksum_sha256"])
    asset.metadata = with_upload_metadata(
        asset.metadata,
        status=UPLOAD_STATUS_COMPLETE,
        flow="presigned",
        correlation_id=correlation_id,
    )
    asset.save(update_fields=["metadata", "updated_at"])
    if not ContentVersion.objects.filter(content_asset=asset).exists():
        create_content_version(
            asset=asset,
            created_by_profile_id=asset.owner_profile_id,
            change_note="Initial upload",
        )
    publish_content_event(
        event_type="ContentUploaded",
        aggregate_id=asset.id,
        correlation_id=correlation_id,
        payload={"institution_id": str(asset.institution_id), "status": asset.status},
    )
    return asset


def proxy_upload_asset(
    *,
    validated_data: dict[str, Any],
    correlation_id: str | None = None,
) -> ContentAsset:
    uploaded_file = validated_data.pop("file")
    file_size = uploaded_file.size
    mime_type = uploaded_file.content_type or "application/octet-stream"
    validate_file_metadata(
        mime_type=mime_type,
        file_size_bytes=file_size,
        file_name=uploaded_file.name,
    )
    asset_id = uuid.uuid4()
    object_key = build_object_key(
        institution_id=validated_data["institution_id"],
        asset_id=asset_id,
        file_name=uploaded_file.name,
    )
    data, checksum_sha256 = read_uploaded_file(uploaded_file)
    scan_uploaded_file_data(
        data,
        metadata={
            "object_key": object_key,
            "file_name": uploaded_file.name,
            "mime_type": mime_type,
            "file_size_bytes": file_size,
            "bucket_name": storage_bucket(),
        },
    )
    upload_storage_object(
        object_key=object_key,
        data=data,
        length=file_size,
        content_type=mime_type,
        metadata={"checksum-sha256": checksum_sha256},
    )
    metadata = with_upload_metadata(
        validated_data.get("metadata"),
        status=UPLOAD_STATUS_COMPLETE,
        flow="proxy",
        correlation_id=correlation_id,
    )
    with transaction.atomic():
        asset = ContentAsset.objects.create(
            id=asset_id,
            institution_id=validated_data["institution_id"],
            owner_profile_id=validated_data["owner_profile_id"],
            asset_type=validated_data["asset_type"],
            title=validated_data["title"],
            metadata=metadata,
        )
        FileMetadata.objects.create(
            content_asset=asset,
            storage_provider=storage_provider(),
            bucket_name=storage_bucket(),
            object_key=object_key,
            file_name=uploaded_file.name,
            mime_type=mime_type,
            file_size_bytes=file_size,
            checksum_sha256=checksum_sha256,
        )
        create_content_version(
            asset=asset,
            created_by_profile_id=asset.owner_profile_id,
            change_note="Initial upload",
        )
    publish_content_event(
        event_type="ContentUploaded",
        aggregate_id=asset.id,
        correlation_id=correlation_id,
        payload={"institution_id": str(asset.institution_id), "status": asset.status},
    )
    return asset


def update_asset(*, asset: ContentAsset, validated_data: dict[str, Any]) -> ContentAsset:
    for field in ["title", "asset_type", "metadata"]:
        if field in validated_data:
            setattr(asset, field, validated_data[field])
    asset.save()
    return asset


def publish_asset(*, asset: ContentAsset, correlation_id: str | None = None) -> ContentAsset:
    asset.status = ContentAssetStatus.PUBLISHED
    asset.deleted_at = None
    asset.save(update_fields=["status", "deleted_at", "updated_at"])
    publish_content_event(
        event_type="ContentPublished",
        aggregate_id=asset.id,
        correlation_id=correlation_id,
        payload={"institution_id": str(asset.institution_id), "status": asset.status},
    )
    return asset


def delete_asset(*, asset: ContentAsset, correlation_id: str | None = None) -> ContentAsset:
    asset.status = ContentAssetStatus.DELETED
    asset.deleted_at = timezone.now()
    asset.save(update_fields=["status", "deleted_at", "updated_at"])
    publish_content_event(
        event_type="ContentDeleted",
        aggregate_id=asset.id,
        correlation_id=correlation_id,
        payload={"institution_id": str(asset.institution_id), "status": asset.status},
    )
    return asset


def create_permission(*, asset: ContentAsset, validated_data: dict[str, Any]) -> ContentPermission:
    return ContentPermission.objects.create(content_asset=asset, **validated_data)


def create_content_version(
    *,
    asset: ContentAsset,
    created_by_profile_id,
    change_note: str | None = None,
) -> ContentVersion:
    version_number = (
        ContentVersion.objects.filter(content_asset=asset).aggregate(
            max_version=Max("version_number")
        )["max_version"]
        or 0
    ) + 1
    return ContentVersion.objects.create(
        content_asset=asset,
        file_metadata=_asset_file_metadata(asset),
        version_number=version_number,
        created_by_profile_id=created_by_profile_id,
        change_note=change_note,
    )


def grant_signed_access(*, asset: ContentAsset, requested_by_profile_id, request) -> dict[str, Any]:
    if asset.status == ContentAssetStatus.DELETED or not asset_is_uploaded(asset):
        raise PermissionDenied("Content is not available for download.")
    if not has_asset_grant(
        asset=asset, profile_id=requested_by_profile_id, required_permission="download"
    ):
        if str(asset.owner_profile_id) != str(requested_by_profile_id):
            raise PermissionDenied("Content download is not allowed.")
    token = secrets.token_urlsafe(32)
    record = SignedAccessRecord.objects.create(
        content_asset=asset,
        requested_by_profile_id=requested_by_profile_id,
        access_token_hash=hash_access_token(token),
        expires_at=timezone.now() + timedelta(seconds=settings.CONTENT_SIGNED_ACCESS_TTL_SECONDS),
    )
    download_url = f"/api/content/download/{record.id}/?token={token}"
    return {
        "access_id": str(record.id),
        "access_token": token,
        "expires_at": record.expires_at.isoformat(),
        "download_url": download_url,
        "access_url": download_url,
    }


def resolve_signed_access(*, access_id, token: str) -> dict[str, Any]:
    try:
        record = SignedAccessRecord.objects.select_related(
            "content_asset",
            "content_asset__file_metadata",
        ).get(id=access_id)
    except SignedAccessRecord.DoesNotExist as exc:
        raise PermissionDenied("Access record was not found.") from exc
    if record.expires_at <= timezone.now():
        raise PermissionDenied("Access token has expired.")
    if record.used_at is not None:
        raise PermissionDenied("Access token has already been used.")
    if not hmac.compare_digest(record.access_token_hash, hash_access_token(token)):
        raise PermissionDenied("Access token is invalid.")
    record.used_at = timezone.now()
    record.save(update_fields=["used_at"])
    file_metadata = _asset_file_metadata(record.content_asset)
    if not file_metadata:
        raise PermissionDenied("Content file metadata is unavailable.")
    minio_download_url = generate_presigned_download_url(object_key=file_metadata.object_key)
    return {
        "asset_id": str(record.content_asset_id),
        "content_asset_id": str(record.content_asset_id),
        "title": record.content_asset.title,
        "storage_provider": file_metadata.storage_provider if file_metadata else None,
        "bucket_name": file_metadata.bucket_name if file_metadata else None,
        "object_key": file_metadata.object_key if file_metadata else None,
        "file_name": file_metadata.file_name if file_metadata else None,
        "mime_type": file_metadata.mime_type if file_metadata else None,
        "download_url": minio_download_url,
        "expires_at": (
            timezone.now() + timedelta(seconds=settings.CONTENT_PRESIGNED_DOWNLOAD_TTL_SECONDS)
        ).isoformat(),
    }


def has_asset_grant(*, asset: ContentAsset, profile_id, required_permission: str) -> bool:
    allowed = [ContentPermissionValue.MANAGE]
    if required_permission == "view":
        allowed.extend([ContentPermissionValue.VIEW, ContentPermissionValue.DOWNLOAD])
    if required_permission == "download":
        allowed.append(ContentPermissionValue.DOWNLOAD)
    now = timezone.now()
    return (
        ContentPermission.objects.filter(
            content_asset=asset,
            grantee_type="profile",
            grantee_id=profile_id,
            permission__in=allowed,
        )
        .filter(expires_at__isnull=True)
        .exists()
        or ContentPermission.objects.filter(
            content_asset=asset,
            grantee_type="profile",
            grantee_id=profile_id,
            permission__in=allowed,
            expires_at__gt=now,
        ).exists()
    )


def _asset_file_metadata(asset: ContentAsset) -> FileMetadata | None:
    try:
        return asset.file_metadata
    except FileMetadata.DoesNotExist:
        return None


def require_file_metadata(asset: ContentAsset) -> FileMetadata:
    file_metadata = _asset_file_metadata(asset)
    if not file_metadata:
        raise ValidationError({"file": "File metadata is required."})
    return file_metadata


def validate_minio_provider(file_data: dict[str, Any]) -> str:
    provider = file_data.get("storage_provider") or settings.CONTENT_STORAGE_PROVIDER
    if provider != storage_provider():
        raise ValidationError({"storage_provider": "Only MinIO object storage is supported."})
    return provider


def verify_storage_object_matches(file_data: dict[str, Any]) -> None:
    validate_object_key(file_data["object_key"])
    stat = stat_storage_object(file_data["object_key"])
    if stat.size != file_data["file_size_bytes"]:
        raise ValidationError({"file_size_bytes": "Stored object size does not match metadata."})
    if stat.content_type and stat.content_type != file_data["mime_type"]:
        raise ValidationError({"mime_type": "Stored object content type does not match metadata."})


def with_upload_metadata(
    metadata: dict | None,
    *,
    status: str | None,
    flow: str | None,
    correlation_id: str | None = None,
) -> dict:
    next_metadata = dict(metadata or {})
    if status:
        next_metadata["upload_status"] = status
    if flow:
        next_metadata["upload_flow"] = flow
    if correlation_id:
        next_metadata["upload_correlation_id"] = correlation_id
    return next_metadata


def asset_is_uploaded(asset: ContentAsset) -> bool:
    return asset.metadata.get("upload_status") == UPLOAD_STATUS_COMPLETE


def build_upload_headers(*, mime_type: str, checksum_sha256: str | None = None) -> dict[str, str]:
    headers = {"Content-Type": mime_type}
    if checksum_sha256:
        headers["x-amz-meta-checksum-sha256"] = checksum_sha256
    return headers


def validate_file_name(file_name: str) -> None:
    if not file_name or "\x00" in file_name or "/" in file_name or "\\" in file_name:
        raise ValidationError({"file_name": "File name is invalid."})
    extension = PurePath(file_name).suffix.lower()
    if not extension or extension not in allowed_file_extensions():
        raise ValidationError({"file_name": "File extension is not allowed."})


def validate_object_key(object_key: str) -> None:
    if (
        not object_key
        or "\x00" in object_key
        or "\\" in object_key
        or object_key.startswith("/")
        or object_key.strip() != object_key
    ):
        raise ValidationError({"object_key": "Object key is invalid."})
    if any(part in {"", ".", ".."} for part in object_key.split("/")):
        raise ValidationError({"object_key": "Object key contains an unsafe path segment."})


def allowed_file_extensions() -> set[str]:
    return {
        extension if extension.startswith(".") else f".{extension}"
        for extension in settings.CONTENT_ALLOWED_FILE_EXTENSIONS
    }


def build_object_key(*, institution_id, asset_id, file_name: str) -> str:
    validate_file_name(file_name)
    base_name = PurePath(file_name).name
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "-", base_name).strip("-") or "upload.bin"
    return f"institutions/{institution_id}/assets/{asset_id}/{uuid.uuid4()}-{safe_name}"


def read_uploaded_file(uploaded_file) -> tuple[BytesIO, str]:
    digest = hashlib.sha256()
    buffer = BytesIO()
    for chunk in uploaded_file.chunks():
        digest.update(chunk)
        buffer.write(chunk)
    buffer.seek(0)
    return buffer, digest.hexdigest()


def scan_uploaded_file_data(data: BytesIO, *, metadata: dict[str, Any]) -> None:
    if not settings.CONTENT_MALWARE_SCAN_ENABLED:
        return
    original_position = data.tell()
    try:
        data.seek(0)
        with tempfile.NamedTemporaryFile(prefix="learngrid-upload-", suffix=".scan") as temporary:
            temporary.write(data.read())
            temporary.flush()
            run_malware_scan(temporary.name, metadata=metadata)
    finally:
        data.seek(original_position)


def scan_stored_object(file_data: dict[str, Any]) -> None:
    if not settings.CONTENT_MALWARE_SCAN_ENABLED:
        return
    run_malware_scan(
        file_data["object_key"],
        metadata={
            "object_key": file_data["object_key"],
            "file_name": file_data.get("file_name"),
            "mime_type": file_data.get("mime_type"),
            "file_size_bytes": file_data.get("file_size_bytes"),
            "bucket_name": file_data.get("bucket_name") or storage_bucket(),
        },
    )


def run_malware_scan(target: str, *, metadata: dict[str, Any]) -> None:
    command = settings.CONTENT_MALWARE_SCANNER_COMMAND.strip()
    if not command:
        raise ValidationError({"file": "Malware scanning is enabled but no scanner is configured."})

    environment = os.environ.copy()
    environment.update(
        {
            "LG_SCAN_TARGET": target,
            "LG_SCAN_OBJECT_KEY": str(metadata.get("object_key") or ""),
            "LG_SCAN_BUCKET": str(metadata.get("bucket_name") or ""),
            "LG_SCAN_FILE_NAME": str(metadata.get("file_name") or ""),
            "LG_SCAN_MIME_TYPE": str(metadata.get("mime_type") or ""),
            "LG_SCAN_FILE_SIZE_BYTES": str(metadata.get("file_size_bytes") or ""),
        }
    )
    try:
        result = subprocess.run(
            [*shlex.split(command), target],
            check=False,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=settings.CONTENT_MALWARE_SCAN_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise ValidationError({"file": "Malware scan timed out."}) from exc
    except (OSError, ValueError) as exc:
        raise ValidationError({"file": "Malware scanner could not be executed."}) from exc

    if result.returncode != 0:
        raise ValidationError({"file": "Uploaded file did not pass malware scanning."})


def hash_access_token(token: str) -> str:
    return hmac.new(
        settings.SECRET_KEY.encode("utf-8"), token.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def publish_content_event(
    *,
    event_type: str,
    aggregate_id,
    payload: dict[str, Any],
    correlation_id: str | None = None,
) -> dict[str, Any]:
    event = publish_kafka_event(
        event_type=event_type,
        aggregate_id=aggregate_id,
        producer_service=settings.SERVICE_NAME,
        correlation_id=correlation_id,
        payload=payload,
    )
    logger.info("content_event %s", event)
    return event
