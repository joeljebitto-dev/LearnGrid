from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import require_enrollment_permission
from .selectors import (
    batch_job_queryset,
    cohort_job_queryset,
    enrollment_queryset,
    history_queryset,
    search_enrollments,
)
from .serializers import (
    AccessCheckSerializer,
    BatchEnrollmentCreateSerializer,
    BatchEnrollmentSerializer,
    CohortEnrollmentCreateSerializer,
    CohortEnrollmentSerializer,
    EnrollmentCreateSerializer,
    EnrollmentHistorySerializer,
    EnrollmentSearchSerializer,
    EnrollmentSerializer,
    EnrollmentTransitionSerializer,
)
from .services import (
    create_batch_enrollment_job,
    create_cohort_enrollment_job,
    create_enrollment,
    has_active_access,
    transition_enrollment,
)


class EnrollmentPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


def _correlation_id(request) -> str | None:
    return request.headers.get("X-Correlation-ID")


class EnrollmentListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = EnrollmentPagination

    def get(self, request):
        serializer = EnrollmentSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        require_enrollment_permission(
            request,
            "enrollment.view",
            serializer.validated_data.get("institution_id"),
        )
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(
            search_enrollments(serializer.validated_data),
            request,
            view=self,
        )
        return paginator.get_paginated_response(EnrollmentSerializer(page, many=True).data)

    def post(self, request):
        serializer = EnrollmentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        require_enrollment_permission(request, "enrollment.manage", serializer.validated_data["institution_id"])
        enrollment = create_enrollment(
            validated_data=serializer.validated_data,
            correlation_id=_correlation_id(request),
        )
        return Response(EnrollmentSerializer(enrollment).data, status=status.HTTP_201_CREATED)


class EnrollmentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, enrollment_id):
        enrollment = get_object_or_404(enrollment_queryset(), id=enrollment_id)
        require_enrollment_permission(request, "enrollment.view", enrollment.institution_id)
        return Response(EnrollmentSerializer(enrollment).data)


class EnrollmentTransitionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, enrollment_id):
        enrollment = get_object_or_404(enrollment_queryset(), id=enrollment_id)
        require_enrollment_permission(request, "enrollment.manage", enrollment.institution_id)
        serializer = EnrollmentTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        enrollment = transition_enrollment(
            enrollment=enrollment,
            to_status=serializer.validated_data["status"],
            changed_by_profile_id=serializer.validated_data.get("changed_by_profile_id"),
            reason=serializer.validated_data.get("reason"),
            correlation_id=_correlation_id(request),
        )
        return Response(EnrollmentSerializer(enrollment).data)


class EnrollmentHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, enrollment_id):
        enrollment = get_object_or_404(enrollment_queryset(), id=enrollment_id)
        require_enrollment_permission(request, "enrollment.view", enrollment.institution_id)
        history = history_queryset().filter(enrollment=enrollment).order_by("created_at", "id")
        return Response(EnrollmentHistorySerializer(history, many=True).data)


class AccessCheckView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = AccessCheckSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        require_enrollment_permission(request, "enrollment.view")
        allowed = has_active_access(**serializer.validated_data)
        return Response({"allowed": allowed})


class BatchEnrollmentListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        require_enrollment_permission(request, "enrollment.view")
        return Response(BatchEnrollmentSerializer(batch_job_queryset(), many=True).data)

    def post(self, request):
        serializer = BatchEnrollmentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        require_enrollment_permission(request, "enrollment.manage", serializer.validated_data["institution_id"])
        job = create_batch_enrollment_job(validated_data=serializer.validated_data)
        return Response(BatchEnrollmentSerializer(job).data, status=status.HTTP_201_CREATED)


class CohortEnrollmentListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        require_enrollment_permission(request, "enrollment.view")
        return Response(CohortEnrollmentSerializer(cohort_job_queryset(), many=True).data)

    def post(self, request):
        serializer = CohortEnrollmentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        require_enrollment_permission(request, "enrollment.manage", serializer.validated_data["institution_id"])
        job = create_cohort_enrollment_job(validated_data=serializer.validated_data)
        return Response(CohortEnrollmentSerializer(job).data, status=status.HTTP_201_CREATED)
