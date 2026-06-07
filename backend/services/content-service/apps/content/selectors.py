from django.db.models import Q, QuerySet

from .models import ContentAsset, ContentAssetStatus, ContentPermission, ContentVersion


def asset_queryset(*, include_deleted: bool = False) -> QuerySet[ContentAsset]:
    queryset = ContentAsset.objects.select_related("file_metadata")
    if not include_deleted:
        queryset = queryset.exclude(status=ContentAssetStatus.DELETED).filter(deleted_at__isnull=True)
    return queryset


def search_assets(filters: dict, *, management: bool = False) -> QuerySet[ContentAsset]:
    queryset = asset_queryset(include_deleted=management and filters.get("status") == ContentAssetStatus.DELETED)
    if institution_id := filters.get("institution_id"):
        queryset = queryset.filter(institution_id=institution_id)
    if owner_profile_id := filters.get("owner_profile_id"):
        queryset = queryset.filter(owner_profile_id=owner_profile_id)
    if asset_type := filters.get("asset_type"):
        queryset = queryset.filter(asset_type=asset_type)
    if status := filters.get("status"):
        queryset = queryset.filter(status=status)
    elif not management:
        queryset = queryset.filter(status=ContentAssetStatus.PUBLISHED)
    if q := (filters.get("q") or "").strip():
        queryset = queryset.filter(Q(title__icontains=q) | Q(file_metadata__file_name__icontains=q))
    return queryset.order_by(filters.get("sort") or "-created_at", "id")


def permission_queryset() -> QuerySet[ContentPermission]:
    return ContentPermission.objects.select_related("content_asset")


def version_queryset() -> QuerySet[ContentVersion]:
    return ContentVersion.objects.select_related("content_asset", "file_metadata")
