from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace
from uuid import uuid4

import jwt
import pytest
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.content import permissions, services
from apps.content.models import (
    ContentAsset,
    ContentAssetStatus,
    ContentPermission,
    ContentVersion,
    FileMetadata,
)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def access_token():
    now = timezone.now()
    return jwt.encode(
        {
            "iss": settings.AUTH_JWT_ISSUER,
            "sub": str(uuid4()),
            "typ": "access",
            "jti": str(uuid4()),
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=5)).timestamp()),
        },
        settings.AUTH_JWT_SIGNING_KEY,
        algorithm=settings.AUTH_JWT_ALGORITHM,
    )


def auth_headers(token: str) -> dict[str, str]:
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def allow_content(monkeypatch, institution_id):
    monkeypatch.setattr(
        permissions,
        "remote_authorization_check",
        lambda **kwargs: (
            kwargs["permission"] in {"content.manage", "content.view"}
            and kwargs["scope_type"] == "institution"
            and kwargs["scope_id"] == str(institution_id)
        )
        or (
            kwargs["permission"] == "content.view"
            and kwargs["scope_type"] == "platform"
            and kwargs["scope_id"] is None
        ),
    )


def stored_object(*, size: int, content_type: str):
    return SimpleNamespace(size=size, content_type=content_type, metadata={})


@pytest.mark.django_db
def test_valid_upload_publish_secure_access_and_delete(api_client, access_token, monkeypatch):
    institution_id = uuid4()
    owner_id = uuid4()
    viewer_id = uuid4()
    allow_content(monkeypatch, institution_id)
    events = []
    monkeypatch.setattr(
        services,
        "publish_content_event",
        lambda **kwargs: events.append(kwargs) or {"event_id": "evt"},
    )
    monkeypatch.setattr(
        services,
        "stat_storage_object",
        lambda _object_key: stored_object(size=2048, content_type="application/pdf"),
    )
    monkeypatch.setattr(
        services,
        "generate_presigned_download_url",
        lambda **_kwargs: "http://127.0.0.1:9000/learngrid-content/presigned-get",
    )

    response = api_client.post(
        "/api/content/assets/",
        {
            "institution_id": str(institution_id),
            "owner_profile_id": str(owner_id),
            "asset_type": "pdf",
            "title": "Syllabus",
            "file": {
                "object_key": "courses/syllabus.pdf",
                "file_name": "syllabus.pdf",
                "mime_type": "application/pdf",
                "file_size_bytes": 2048,
                "checksum_sha256": "a" * 64,
            },
        },
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 201
    asset_id = response.json()["id"]
    assert response.json()["file_metadata"]["storage_provider"] == "minio"
    assert FileMetadata.objects.filter(content_asset_id=asset_id).exists()
    assert ContentVersion.objects.filter(content_asset_id=asset_id).exists()
    assert events[-1]["event_type"] == "ContentUploaded"

    response = api_client.post(
        f"/api/content/assets/{asset_id}/publish/",
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["status"] == ContentAssetStatus.PUBLISHED
    assert events[-1]["event_type"] == "ContentPublished"

    response = api_client.post(
        f"/api/content/assets/{asset_id}/permissions/",
        {"grantee_type": "profile", "grantee_id": str(viewer_id), "permission": "download"},
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 201
    assert ContentPermission.objects.filter(content_asset_id=asset_id).exists()

    response = api_client.post(
        f"/api/content/assets/{asset_id}/access/",
        {"requested_by_profile_id": str(viewer_id)},
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 201
    access = response.json()
    assert access["access_token"]

    response = api_client.get(
        f"/api/content/download/{access['access_id']}/",
        {"token": access["access_token"]},
    )
    assert response.status_code == 200
    assert response.json()["object_key"] == "courses/syllabus.pdf"
    assert response.json()["download_url"].startswith("http://127.0.0.1:9000/")

    response = api_client.get(
        f"/api/content/download/{access['access_id']}/",
        {"token": access["access_token"]},
    )
    assert response.status_code == 403

    response = api_client.delete(
        f"/api/content/assets/{asset_id}/",
        **auth_headers(access_token),
    )
    assert response.status_code == 200
    assert response.json()["status"] == ContentAssetStatus.DELETED
    assert events[-1]["event_type"] == "ContentDeleted"


@pytest.mark.django_db
def test_invalid_upload_and_permission_failure(api_client, access_token, monkeypatch):
    institution_id = uuid4()
    allow_content(monkeypatch, institution_id)

    response = api_client.post(
        "/api/content/assets/",
        {
            "institution_id": str(institution_id),
            "owner_profile_id": str(uuid4()),
            "asset_type": "document",
            "title": "Executable",
            "file": {
                "object_key": "bad.exe",
                "file_name": "bad.exe",
                "mime_type": "application/x-msdownload",
                "file_size_bytes": 200,
            },
        },
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 400
    assert not ContentAsset.objects.filter(title="Executable").exists()

    response = api_client.post(
        "/api/content/assets/",
        {
            "institution_id": str(institution_id),
            "owner_profile_id": str(uuid4()),
            "asset_type": "pdf",
            "title": "Wrong provider",
            "file": {
                "storage_provider": "s3",
                "object_key": "wrong.pdf",
                "file_name": "wrong.pdf",
                "mime_type": "application/pdf",
                "file_size_bytes": 200,
            },
        },
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 400

    monkeypatch.setattr(permissions, "remote_authorization_check", lambda **_kwargs: False)
    response = api_client.post(
        "/api/content/assets/",
        {
            "institution_id": str(institution_id),
            "owner_profile_id": str(uuid4()),
            "asset_type": "pdf",
            "title": "Blocked",
            "file": {
                "object_key": "blocked.pdf",
                "file_name": "blocked.pdf",
                "mime_type": "application/pdf",
                "file_size_bytes": 200,
            },
        },
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 403
    assert not ContentAsset.objects.filter(title="Blocked").exists()


@pytest.mark.django_db
def test_upload_rejects_disallowed_extension_and_unsafe_object_key(
    api_client,
    access_token,
    monkeypatch,
):
    institution_id = uuid4()
    allow_content(monkeypatch, institution_id)

    response = api_client.post(
        "/api/content/assets/",
        {
            "institution_id": str(institution_id),
            "owner_profile_id": str(uuid4()),
            "asset_type": "document",
            "title": "Extension mismatch",
            "file": {
                "object_key": "uploads/notes.exe",
                "file_name": "notes.exe",
                "mime_type": "text/plain",
                "file_size_bytes": 200,
            },
        },
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 400
    assert "file_name" in response.json()

    response = api_client.post(
        "/api/content/assets/",
        {
            "institution_id": str(institution_id),
            "owner_profile_id": str(uuid4()),
            "asset_type": "document",
            "title": "Unsafe key",
            "file": {
                "object_key": "../notes.txt",
                "file_name": "notes.txt",
                "mime_type": "text/plain",
                "file_size_bytes": 200,
            },
        },
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 400
    assert "object_key" in response.json()


@pytest.mark.django_db
def test_presigned_upload_initiation_and_completion(api_client, access_token, monkeypatch):
    institution_id = uuid4()
    allow_content(monkeypatch, institution_id)
    monkeypatch.setattr(
        services,
        "generate_presigned_upload_url",
        lambda **_kwargs: "http://127.0.0.1:9000/learngrid-content/presigned-put",
    )
    monkeypatch.setattr(
        services,
        "stat_storage_object",
        lambda _object_key: stored_object(size=128, content_type="text/plain"),
    )

    response = api_client.post(
        "/api/content/assets/uploads/presigned/",
        {
            "institution_id": str(institution_id),
            "owner_profile_id": str(uuid4()),
            "asset_type": "document",
            "title": "Notes",
            "file_name": "notes.txt",
            "mime_type": "text/plain",
            "file_size_bytes": 128,
            "checksum_sha256": "b" * 64,
        },
        **auth_headers(access_token),
        format="json",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["upload_url"].startswith("http://127.0.0.1:9000/")
    assert body["upload_headers"]["Content-Type"] == "text/plain"
    assert body["asset"]["metadata"]["upload_status"] == "pending"
    assert not ContentVersion.objects.filter(content_asset_id=body["asset"]["id"]).exists()

    response = api_client.post(
        f"/api/content/assets/{body['asset']['id']}/uploads/complete/",
        {"checksum_sha256": "c" * 64},
        **auth_headers(access_token),
        format="json",
    )

    assert response.status_code == 200
    assert response.json()["metadata"]["upload_status"] == "complete"
    assert ContentVersion.objects.filter(content_asset_id=body["asset"]["id"]).exists()


@pytest.mark.django_db
def test_presigned_completion_rejects_mismatched_object(api_client, access_token, monkeypatch):
    institution_id = uuid4()
    allow_content(monkeypatch, institution_id)
    monkeypatch.setattr(
        services, "generate_presigned_upload_url", lambda **_kwargs: "http://upload"
    )
    monkeypatch.setattr(
        services,
        "stat_storage_object",
        lambda _object_key: stored_object(size=1, content_type="text/plain"),
    )

    response = api_client.post(
        "/api/content/assets/uploads/presigned/",
        {
            "institution_id": str(institution_id),
            "owner_profile_id": str(uuid4()),
            "asset_type": "document",
            "title": "Mismatch",
            "file_name": "mismatch.txt",
            "mime_type": "text/plain",
            "file_size_bytes": 128,
        },
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 201

    response = api_client.post(
        f"/api/content/assets/{response.json()['asset']['id']}/uploads/complete/",
        {},
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_proxy_upload_stores_object_and_records_checksum(api_client, access_token, monkeypatch):
    institution_id = uuid4()
    allow_content(monkeypatch, institution_id)
    uploads = []
    monkeypatch.setattr(
        services,
        "upload_storage_object",
        lambda **kwargs: uploads.append(kwargs),
    )

    response = api_client.post(
        "/api/content/assets/uploads/proxy/",
        {
            "institution_id": str(institution_id),
            "owner_profile_id": str(uuid4()),
            "asset_type": "pdf",
            "title": "Proxy PDF",
            "file": SimpleUploadedFile(
                "proxy.pdf",
                b"%PDF-1.4 test",
                content_type="application/pdf",
            ),
        },
        **auth_headers(access_token),
        format="multipart",
    )

    assert response.status_code == 201
    assert uploads
    assert uploads[0]["content_type"] == "application/pdf"
    assert response.json()["metadata"]["upload_flow"] == "proxy"
    metadata = FileMetadata.objects.get(content_asset_id=response.json()["id"])
    assert metadata.storage_provider == "minio"
    assert metadata.checksum_sha256


@pytest.mark.django_db
def test_proxy_upload_runs_malware_scanner_when_enabled(api_client, access_token, monkeypatch):
    institution_id = uuid4()
    allow_content(monkeypatch, institution_id)
    uploads = []
    scans = []
    monkeypatch.setattr(services, "upload_storage_object", lambda **kwargs: uploads.append(kwargs))

    def scanner(command, **_kwargs):
        scans.append(command)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(services.subprocess, "run", scanner)

    with override_settings(
        CONTENT_MALWARE_SCAN_ENABLED=True,
        CONTENT_MALWARE_SCANNER_COMMAND="scanner",
    ):
        response = api_client.post(
            "/api/content/assets/uploads/proxy/",
            {
                "institution_id": str(institution_id),
                "owner_profile_id": str(uuid4()),
                "asset_type": "pdf",
                "title": "Scanned PDF",
                "file": SimpleUploadedFile(
                    "scanned.pdf",
                    b"%PDF-1.4 scanned",
                    content_type="application/pdf",
                ),
            },
            **auth_headers(access_token),
            format="multipart",
        )

    assert response.status_code == 201
    assert scans
    assert scans[0][0] == "scanner"
    assert uploads


@pytest.mark.django_db
def test_malware_scanner_failure_blocks_upload(api_client, access_token, monkeypatch):
    institution_id = uuid4()
    allow_content(monkeypatch, institution_id)
    uploads = []
    monkeypatch.setattr(services, "upload_storage_object", lambda **kwargs: uploads.append(kwargs))
    monkeypatch.setattr(
        services.subprocess, "run", lambda *_args, **_kwargs: SimpleNamespace(returncode=1)
    )

    with override_settings(
        CONTENT_MALWARE_SCAN_ENABLED=True,
        CONTENT_MALWARE_SCANNER_COMMAND="scanner",
    ):
        response = api_client.post(
            "/api/content/assets/uploads/proxy/",
            {
                "institution_id": str(institution_id),
                "owner_profile_id": str(uuid4()),
                "asset_type": "pdf",
                "title": "Blocked PDF",
                "file": SimpleUploadedFile(
                    "blocked.pdf",
                    b"%PDF-1.4 blocked",
                    content_type="application/pdf",
                ),
            },
            **auth_headers(access_token),
            format="multipart",
        )

    assert response.status_code == 400
    assert "file" in response.json()
    assert not uploads
    assert not ContentAsset.objects.filter(title="Blocked PDF").exists()


@pytest.mark.django_db
def test_malware_scanner_outage_blocks_presigned_completion(api_client, access_token, monkeypatch):
    institution_id = uuid4()
    allow_content(monkeypatch, institution_id)
    monkeypatch.setattr(
        services, "generate_presigned_upload_url", lambda **_kwargs: "http://upload"
    )
    monkeypatch.setattr(
        services,
        "stat_storage_object",
        lambda _object_key: stored_object(size=128, content_type="text/plain"),
    )
    monkeypatch.setattr(
        services.subprocess,
        "run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("scanner down")),
    )

    response = api_client.post(
        "/api/content/assets/uploads/presigned/",
        {
            "institution_id": str(institution_id),
            "owner_profile_id": str(uuid4()),
            "asset_type": "document",
            "title": "Scanner outage",
            "file_name": "outage.txt",
            "mime_type": "text/plain",
            "file_size_bytes": 128,
        },
        **auth_headers(access_token),
        format="json",
    )
    assert response.status_code == 201

    with override_settings(
        CONTENT_MALWARE_SCAN_ENABLED=True,
        CONTENT_MALWARE_SCANNER_COMMAND="scanner",
    ):
        response = api_client.post(
            f"/api/content/assets/{response.json()['asset']['id']}/uploads/complete/",
            {},
            **auth_headers(access_token),
            format="json",
        )

    assert response.status_code == 400
    assert "file" in response.json()
