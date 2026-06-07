from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import BinaryIO
from urllib.parse import urlparse

from django.conf import settings
from minio import Minio
from minio.error import S3Error
from rest_framework.exceptions import APIException, ValidationError


class ObjectStorageError(APIException):
    status_code = 503
    default_detail = "Object storage is unavailable."
    default_code = "object_storage_unavailable"


@dataclass(frozen=True)
class StoredObject:
    size: int
    content_type: str | None
    metadata: dict


def storage_provider() -> str:
    return "minio"


def storage_bucket() -> str:
    return settings.CONTENT_STORAGE_BUCKET


def storage_client() -> Minio:
    parsed = urlparse(settings.CONTENT_MINIO_ENDPOINT_URL)
    endpoint = parsed.netloc or parsed.path
    secure = settings.CONTENT_MINIO_SECURE
    if parsed.scheme:
        secure = parsed.scheme == "https"
    return Minio(
        endpoint,
        access_key=settings.CONTENT_MINIO_ACCESS_KEY,
        secret_key=settings.CONTENT_MINIO_SECRET_KEY,
        secure=secure,
    )


def stat_storage_object(object_key: str) -> StoredObject:
    try:
        stat = storage_client().stat_object(storage_bucket(), object_key)
    except S3Error as exc:
        if exc.code in {"NoSuchBucket", "NoSuchKey", "NoSuchObject"}:
            raise ValidationError({"file": "Object does not exist in MinIO."}) from exc
        raise ObjectStorageError("Could not inspect object storage metadata.") from exc
    except OSError as exc:
        raise ObjectStorageError("Could not connect to object storage.") from exc
    return StoredObject(
        size=stat.size,
        content_type=getattr(stat, "content_type", None),
        metadata=getattr(stat, "metadata", {}) or {},
    )


def upload_storage_object(
    *,
    object_key: str,
    data: BinaryIO,
    length: int,
    content_type: str,
    metadata: dict[str, str] | None = None,
) -> None:
    try:
        storage_client().put_object(
            storage_bucket(),
            object_key,
            data,
            length,
            content_type=content_type,
            metadata=metadata,
        )
    except S3Error as exc:
        raise ObjectStorageError("Could not upload object to MinIO.") from exc
    except OSError as exc:
        raise ObjectStorageError("Could not connect to object storage.") from exc


def generate_presigned_upload_url(*, object_key: str) -> str:
    try:
        return storage_client().presigned_put_object(
            storage_bucket(),
            object_key,
            expires=timedelta(seconds=settings.CONTENT_PRESIGNED_UPLOAD_TTL_SECONDS),
        )
    except S3Error as exc:
        raise ObjectStorageError("Could not create a MinIO upload URL.") from exc
    except OSError as exc:
        raise ObjectStorageError("Could not connect to object storage.") from exc


def generate_presigned_download_url(*, object_key: str) -> str:
    try:
        return storage_client().presigned_get_object(
            storage_bucket(),
            object_key,
            expires=timedelta(seconds=settings.CONTENT_PRESIGNED_DOWNLOAD_TTL_SECONDS),
        )
    except S3Error as exc:
        raise ObjectStorageError("Could not create a MinIO download URL.") from exc
    except OSError as exc:
        raise ObjectStorageError("Could not connect to object storage.") from exc
