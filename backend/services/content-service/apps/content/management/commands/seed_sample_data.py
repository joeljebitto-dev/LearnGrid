from __future__ import annotations

import os
import sys
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

ROOT = Path(__file__).resolve().parents[7]
sys.path.append(str(ROOT / "scripts" / "sample_data"))

from seed_helpers import (  # noqa: E402
    add_seed_arguments,
    institution_id,
    load_manifest,
    planned,
    profile_id,
    seed_metadata,
    uuid_value,
)

from apps.content.models import (  # noqa: E402
    ContentAsset,
    ContentAssetStatus,
    ContentPermission,
    ContentPermissionGranteeType,
    ContentPermissionValue,
    ContentVersion,
    FileMetadata,
)


class Command(BaseCommand):
    help = "Seed LearnGrid demo sample data for content-service."

    def add_arguments(self, parser) -> None:
        add_seed_arguments(parser, __file__)

    def handle(self, *args, **options) -> None:
        manifest = load_manifest(options["manifest"])
        records = ["content_assets", "file_metadata", "content_versions", "content_permissions"]
        if options["dry_run"]:
            planned(self, "content-service", manifest, records)
            return
        with transaction.atomic():
            if options["reset_sample_data"]:
                self.reset(manifest)
            self.seed(manifest)
        self.stdout.write(self.style.SUCCESS("Seeded content-service sample data."))

    def reset(self, manifest: dict) -> None:
        asset_ids = [uuid_value(data["id"]) for data in manifest["content"].values()]
        ContentAsset.objects.filter(id__in=asset_ids).delete()
        ContentAsset.objects.filter(metadata__seed_namespace=manifest["seed_namespace"]).delete()

    def seed(self, manifest: dict) -> None:
        bucket = os.getenv("CONTENT_STORAGE_BUCKET", "learngrid-content")
        for key, data in manifest["content"].items():
            asset, _created = ContentAsset.objects.update_or_create(
                id=uuid_value(data["id"]),
                defaults={
                    "institution_id": institution_id(manifest),
                    "owner_profile_id": profile_id(manifest, "instructor"),
                    "asset_type": data["asset_type"],
                    "title": data["title"],
                    "status": ContentAssetStatus.PUBLISHED,
                    "metadata": seed_metadata(key, upload_status="complete"),
                    "deleted_at": None,
                },
            )
            file_metadata, _created = FileMetadata.objects.update_or_create(
                content_asset=asset,
                defaults={
                    "id": uuid_value(data["file_metadata_id"]),
                    "storage_provider": "minio",
                    "bucket_name": bucket,
                    "object_key": data["object_key"],
                    "file_name": data["file_name"],
                    "mime_type": data["mime_type"],
                    "file_size_bytes": data["file_size_bytes"],
                    "checksum_sha256": "0" * 64,
                },
            )
            ContentVersion.objects.update_or_create(
                content_asset=asset,
                version_number=1,
                defaults={
                    "id": uuid_value(data["version_id"]),
                    "file_metadata": file_metadata,
                    "change_note": "Demo seed version.",
                    "created_by_profile_id": profile_id(manifest, "instructor"),
                },
            )
            ContentPermission.objects.update_or_create(
                content_asset=asset,
                grantee_type=ContentPermissionGranteeType.INSTITUTION,
                grantee_id=institution_id(manifest),
                permission=ContentPermissionValue.VIEW,
                defaults={"expires_at": None},
            )
