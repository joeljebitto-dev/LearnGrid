from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import require_institution_manage_permission, require_profile_permission
from .selectors import (
    batch_queryset,
    department_queryset,
    institution_queryset,
    profile_queryset,
    search_batches,
    search_departments,
    search_institutions,
    search_profiles,
)
from .serializers import (
    BatchCreateSerializer,
    BatchSearchSerializer,
    BatchSerializer,
    BatchUpdateSerializer,
    DepartmentCreateSerializer,
    DepartmentSearchSerializer,
    DepartmentSerializer,
    DepartmentUpdateSerializer,
    InstitutionCreateSerializer,
    InstitutionSearchSerializer,
    InstitutionSerializer,
    InstitutionUpdateSerializer,
    ProfileSearchSerializer,
    UserProfileCreateSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
)
from .services import (
    archive_batch,
    archive_department,
    archive_institution,
    create_batch,
    create_department,
    create_institution,
    create_user_profile,
    deactivate_user_profile,
    update_batch,
    update_department,
    update_institution,
    update_user_profile,
)


class ProfilePagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


def _auth_token(request) -> str:
    return str(request.auth)


def _profile_or_404(profile_id):
    return get_object_or_404(profile_queryset(), id=profile_id, deleted_at__isnull=True)


class InstitutionListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = ProfilePagination

    def get(self, request):
        require_institution_manage_permission(request)
        serializer = InstitutionSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(
            search_institutions(serializer.validated_data),
            request,
            view=self,
        )
        return paginator.get_paginated_response(InstitutionSerializer(page, many=True).data)

    def post(self, request):
        require_institution_manage_permission(request)
        serializer = InstitutionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        institution = create_institution(validated_data=serializer.validated_data)
        return Response(InstitutionSerializer(institution).data, status=status.HTTP_201_CREATED)


class InstitutionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, institution_id):
        require_institution_manage_permission(request)
        institution = get_object_or_404(institution_queryset(), id=institution_id)
        return Response(InstitutionSerializer(institution).data)

    def patch(self, request, institution_id):
        require_institution_manage_permission(request)
        institution = get_object_or_404(institution_queryset(), id=institution_id)
        serializer = InstitutionUpdateSerializer(
            data=request.data,
            partial=True,
            context={"institution": institution},
        )
        serializer.is_valid(raise_exception=True)
        institution = update_institution(
            institution=institution,
            validated_data=serializer.validated_data,
        )
        return Response(InstitutionSerializer(institution).data)

    def delete(self, request, institution_id):
        require_institution_manage_permission(request)
        institution = get_object_or_404(institution_queryset(), id=institution_id)
        institution = archive_institution(institution=institution)
        return Response(InstitutionSerializer(institution).data)


class DepartmentListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = ProfilePagination

    def get(self, request):
        serializer = DepartmentSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        require_institution_manage_permission(
            request,
            serializer.validated_data.get("institution_id"),
        )
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(
            search_departments(serializer.validated_data),
            request,
            view=self,
        )
        return paginator.get_paginated_response(DepartmentSerializer(page, many=True).data)

    def post(self, request):
        serializer = DepartmentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        require_institution_manage_permission(request, serializer.validated_data["institution_id"])
        department = create_department(validated_data=serializer.validated_data)
        return Response(DepartmentSerializer(department).data, status=status.HTTP_201_CREATED)


class DepartmentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, department_id):
        department = get_object_or_404(department_queryset(), id=department_id)
        require_institution_manage_permission(request, department.institution_id)
        return Response(DepartmentSerializer(department).data)

    def patch(self, request, department_id):
        department = get_object_or_404(department_queryset(), id=department_id)
        require_institution_manage_permission(request, department.institution_id)
        serializer = DepartmentUpdateSerializer(
            data=request.data,
            partial=True,
            context={"department": department},
        )
        serializer.is_valid(raise_exception=True)
        department = update_department(
            department=department,
            validated_data=serializer.validated_data,
        )
        return Response(DepartmentSerializer(department).data)

    def delete(self, request, department_id):
        department = get_object_or_404(department_queryset(), id=department_id)
        require_institution_manage_permission(request, department.institution_id)
        department = archive_department(department=department)
        return Response(DepartmentSerializer(department).data)


class BatchListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = ProfilePagination

    def get(self, request):
        serializer = BatchSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        require_institution_manage_permission(
            request,
            serializer.validated_data.get("institution_id"),
        )
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(
            search_batches(serializer.validated_data),
            request,
            view=self,
        )
        return paginator.get_paginated_response(BatchSerializer(page, many=True).data)

    def post(self, request):
        serializer = BatchCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        require_institution_manage_permission(request, serializer.validated_data["institution_id"])
        batch = create_batch(validated_data=serializer.validated_data)
        return Response(BatchSerializer(batch).data, status=status.HTTP_201_CREATED)


class BatchDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, batch_id):
        batch = get_object_or_404(batch_queryset(), id=batch_id)
        require_institution_manage_permission(request, batch.institution_id)
        return Response(BatchSerializer(batch).data)

    def patch(self, request, batch_id):
        batch = get_object_or_404(batch_queryset(), id=batch_id)
        require_institution_manage_permission(request, batch.institution_id)
        serializer = BatchUpdateSerializer(
            data=request.data,
            partial=True,
            context={"batch": batch},
        )
        serializer.is_valid(raise_exception=True)
        batch = update_batch(batch=batch, validated_data=serializer.validated_data)
        return Response(BatchSerializer(batch).data)

    def delete(self, request, batch_id):
        batch = get_object_or_404(batch_queryset(), id=batch_id)
        require_institution_manage_permission(request, batch.institution_id)
        batch = archive_batch(batch=batch)
        return Response(BatchSerializer(batch).data)


class ProfileListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = ProfilePagination

    def get(self, request):
        serializer = ProfileSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        institution_id = serializer.validated_data.get("institution_id")
        require_profile_permission(request, "profile.view", institution_id)

        queryset = search_profiles(serializer.validated_data)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        response_serializer = UserProfileSerializer(page, many=True)
        return paginator.get_paginated_response(response_serializer.data)

    def post(self, request):
        serializer = UserProfileCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        institution_id = serializer.validated_data.get("institution_id")
        require_profile_permission(request, "profile.manage", institution_id)

        profile = create_user_profile(
            validated_data=serializer.validated_data,
            token=_auth_token(request),
        )
        return Response(UserProfileSerializer(profile).data, status=status.HTTP_201_CREATED)


class ProfileDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, profile_id):
        profile = _profile_or_404(profile_id)
        require_profile_permission(request, "profile.view", profile.institution_id)
        return Response(UserProfileSerializer(profile).data)

    def patch(self, request, profile_id):
        profile = _profile_or_404(profile_id)
        require_profile_permission(request, "profile.manage", profile.institution_id)

        serializer = UserProfileUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        profile = update_user_profile(
            profile=profile,
            validated_data=serializer.validated_data,
            token=_auth_token(request),
        )
        return Response(UserProfileSerializer(profile).data)


class ProfileDeactivateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, profile_id):
        profile = _profile_or_404(profile_id)
        require_profile_permission(request, "profile.manage", profile.institution_id)
        profile = deactivate_user_profile(profile=profile, token=_auth_token(request))
        return Response(UserProfileSerializer(profile).data)


class ImportJobPlaceholderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        institution_id = request.data.get("institution_id")
        require_profile_permission(request, "profile.manage", institution_id)
        return Response(
            {
                "code": "not_implemented",
                "detail": "Bulk user imports are reserved for a future release.",
            },
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )
