from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import has_content_permission, require_content_permission
from .selectors import asset_queryset, permission_queryset, search_assets, version_queryset
from .serializers import (
    ContentAssetCreateSerializer,
    ContentAssetSearchSerializer,
    ContentAssetSerializer,
    ContentAssetUpdateSerializer,
    ContentPermissionCreateSerializer,
    ContentPermissionSerializer,
    ContentVersionCreateSerializer,
    ContentVersionSerializer,
    PresignedUploadCompleteSerializer,
    PresignedUploadCreateSerializer,
    ProxyUploadCreateSerializer,
    SignedAccessCreateSerializer,
)
from .services import (
    complete_presigned_upload,
    create_asset,
    create_content_version,
    create_presigned_upload,
    create_permission,
    delete_asset,
    grant_signed_access,
    publish_asset,
    proxy_upload_asset,
    resolve_signed_access,
    update_asset,
)


class ContentPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


def _correlation_id(request) -> str | None:
    return request.headers.get("X-Correlation-ID")


class ContentAssetListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = ContentPagination

    def get(self, request):
        serializer = ContentAssetSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        filters = serializer.validated_data
        institution_id = filters.get("institution_id")
        if has_content_permission(request, "content.manage", institution_id):
            management = True
        else:
            require_content_permission(request, "content.view", institution_id)
            management = False
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(
            search_assets(filters, management=management),
            request,
            view=self,
        )
        return paginator.get_paginated_response(ContentAssetSerializer(page, many=True).data)

    def post(self, request):
        serializer = ContentAssetCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        require_content_permission(request, "content.manage", serializer.validated_data["institution_id"])
        asset = create_asset(
            validated_data=serializer.validated_data,
            correlation_id=_correlation_id(request),
        )
        return Response(ContentAssetSerializer(asset).data, status=status.HTTP_201_CREATED)


class PresignedUploadCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PresignedUploadCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        require_content_permission(request, "content.manage", serializer.validated_data["institution_id"])
        result = create_presigned_upload(
            validated_data=serializer.validated_data,
            correlation_id=_correlation_id(request),
        )
        return Response(
            {
                "asset": ContentAssetSerializer(result["asset"]).data,
                "object_key": result["object_key"],
                "upload_url": result["upload_url"],
                "upload_headers": result["upload_headers"],
                "expires_at": result["expires_at"],
            },
            status=status.HTTP_201_CREATED,
        )


class ProxyUploadCreateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = ProxyUploadCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        require_content_permission(request, "content.manage", serializer.validated_data["institution_id"])
        asset = proxy_upload_asset(
            validated_data=serializer.validated_data,
            correlation_id=_correlation_id(request),
        )
        return Response(ContentAssetSerializer(asset).data, status=status.HTTP_201_CREATED)


class ContentAssetDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, asset_id):
        asset = get_object_or_404(asset_queryset(include_deleted=True), id=asset_id)
        require_content_permission(request, "content.view", asset.institution_id)
        return Response(ContentAssetSerializer(asset).data)

    def patch(self, request, asset_id):
        asset = get_object_or_404(asset_queryset(), id=asset_id)
        require_content_permission(request, "content.manage", asset.institution_id)
        serializer = ContentAssetUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        asset = update_asset(asset=asset, validated_data=serializer.validated_data)
        return Response(ContentAssetSerializer(asset).data)

    def delete(self, request, asset_id):
        asset = get_object_or_404(asset_queryset(), id=asset_id)
        require_content_permission(request, "content.manage", asset.institution_id)
        asset = delete_asset(asset=asset, correlation_id=_correlation_id(request))
        return Response(ContentAssetSerializer(asset).data)


class PresignedUploadCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, asset_id):
        asset = get_object_or_404(asset_queryset(), id=asset_id)
        require_content_permission(request, "content.manage", asset.institution_id)
        serializer = PresignedUploadCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        asset = complete_presigned_upload(
            asset=asset,
            checksum_sha256=serializer.validated_data.get("checksum_sha256"),
            correlation_id=_correlation_id(request),
        )
        return Response(ContentAssetSerializer(asset).data)


class ContentAssetPublishView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, asset_id):
        asset = get_object_or_404(asset_queryset(), id=asset_id)
        require_content_permission(request, "content.manage", asset.institution_id)
        asset = publish_asset(asset=asset, correlation_id=_correlation_id(request))
        return Response(ContentAssetSerializer(asset).data)


class ContentPermissionListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, asset_id):
        asset = get_object_or_404(asset_queryset(include_deleted=True), id=asset_id)
        require_content_permission(request, "content.manage", asset.institution_id)
        permissions = permission_queryset().filter(content_asset=asset)
        return Response(ContentPermissionSerializer(permissions, many=True).data)

    def post(self, request, asset_id):
        asset = get_object_or_404(asset_queryset(), id=asset_id)
        require_content_permission(request, "content.manage", asset.institution_id)
        serializer = ContentPermissionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        content_permission = create_permission(asset=asset, validated_data=serializer.validated_data)
        return Response(ContentPermissionSerializer(content_permission).data, status=status.HTTP_201_CREATED)


class SignedAccessCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, asset_id):
        asset = get_object_or_404(asset_queryset(), id=asset_id)
        require_content_permission(request, "content.view", asset.institution_id)
        serializer = SignedAccessCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(
            grant_signed_access(
                asset=asset,
                requested_by_profile_id=serializer.validated_data["requested_by_profile_id"],
                request=request,
            ),
            status=status.HTTP_201_CREATED,
        )


class SignedDownloadView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, access_id):
        return Response(resolve_signed_access(access_id=access_id, token=request.query_params.get("token", "")))


class ContentVersionListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, asset_id):
        asset = get_object_or_404(asset_queryset(include_deleted=True), id=asset_id)
        require_content_permission(request, "content.manage", asset.institution_id)
        versions = version_queryset().filter(content_asset=asset)
        return Response(ContentVersionSerializer(versions, many=True).data)

    def post(self, request, asset_id):
        asset = get_object_or_404(asset_queryset(), id=asset_id)
        require_content_permission(request, "content.manage", asset.institution_id)
        serializer = ContentVersionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        version = create_content_version(asset=asset, **serializer.validated_data)
        return Response(ContentVersionSerializer(version).data, status=status.HTTP_201_CREATED)
