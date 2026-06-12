from django.urls import path

from .views import (
    ContentAssetDetailView,
    ContentAssetListCreateView,
    ContentAssetPublishView,
    ContentPermissionListCreateView,
    ContentVersionListCreateView,
    PresignedUploadCompleteView,
    PresignedUploadCreateView,
    ProxyUploadCreateView,
    SignedAccessCreateView,
    SignedDownloadView,
)


urlpatterns = [
    path("assets/", ContentAssetListCreateView.as_view(), name="content-asset-list-create"),
    path(
        "assets/uploads/presigned/",
        PresignedUploadCreateView.as_view(),
        name="presigned-upload-create",
    ),
    path(
        "assets/uploads/proxy/",
        ProxyUploadCreateView.as_view(),
        name="proxy-upload-create",
    ),
    path("assets/<uuid:asset_id>/", ContentAssetDetailView.as_view(), name="content-asset-detail"),
    path(
        "assets/<uuid:asset_id>/uploads/complete/",
        PresignedUploadCompleteView.as_view(),
        name="presigned-upload-complete",
    ),
    path(
        "assets/<uuid:asset_id>/publish/",
        ContentAssetPublishView.as_view(),
        name="content-asset-publish",
    ),
    path(
        "assets/<uuid:asset_id>/permissions/",
        ContentPermissionListCreateView.as_view(),
        name="content-permission-list-create",
    ),
    path(
        "assets/<uuid:asset_id>/access/",
        SignedAccessCreateView.as_view(),
        name="signed-access-create",
    ),
    path(
        "assets/<uuid:asset_id>/versions/",
        ContentVersionListCreateView.as_view(),
        name="content-version-list-create",
    ),
    path("download/<uuid:access_id>/", SignedDownloadView.as_view(), name="signed-download"),
]
