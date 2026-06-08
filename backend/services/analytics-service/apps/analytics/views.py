from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError

from .models import DashboardScopeType
from .selectors import dashboard_payload, platform_dashboard_payload, report_snapshots
from .serializers import (
    EventFactSerializer,
    EventIngestSerializer,
    ReportSnapshotCreateSerializer,
    ReportSnapshotSearchSerializer,
    ReportSnapshotSerializer,
)
from .services import (
    auth_token,
    create_report_snapshot,
    current_profile,
    dashboard_scope_for_profile,
    ingest_event,
    require_analytics_view,
    require_instructor_profile,
    require_profile_view,
    require_student_profile,
)


class AnalyticsPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class StudentDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        token = auth_token(request)
        profile = current_profile(token=token)
        require_student_profile(profile)
        require_profile_view(token=token, institution_id=profile.get("institution_id"))
        scope_type, scope_id = dashboard_scope_for_profile(profile)
        return Response(
            dashboard_payload(
                portal="student",
                scope_type=scope_type,
                scope_id=scope_id,
                profile=profile,
                institution_id=profile.get("institution_id"),
            )
        )


class InstructorDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        token = auth_token(request)
        profile = current_profile(token=token)
        require_instructor_profile(profile)
        require_analytics_view(token=token, institution_id=profile.get("institution_id"))
        scope_type, scope_id = dashboard_scope_for_profile(profile)
        return Response(
            dashboard_payload(
                portal="instructor",
                scope_type=scope_type,
                scope_id=scope_id,
                profile=profile,
                institution_id=profile.get("institution_id"),
            )
        )


class AdminInstitutionDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        institution_id = request.query_params.get("institution_id")
        if not institution_id:
            raise ValidationError({"institution_id": "institution_id query parameter is required."})
        require_analytics_view(token=auth_token(request), institution_id=institution_id)
        return Response(
            dashboard_payload(
                portal="admin",
                scope_type=DashboardScopeType.INSTITUTION,
                scope_id=institution_id,
                institution_id=institution_id,
            )
        )


class AdminSystemDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        token = auth_token(request)
        require_analytics_view(token=token, platform=True)
        try:
            profile = current_profile(token=token)
        except Exception:
            profile = None
        return Response(platform_dashboard_payload(profile=profile))


class EventIngestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = EventIngestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        institution_id = serializer.validated_data.get("institution_id")
        require_analytics_view(
            token=auth_token(request),
            institution_id=str(institution_id) if institution_id else None,
            platform=institution_id is None,
        )
        event, created = ingest_event(serializer.validated_data)
        return Response(
            {"created": created, "event": EventFactSerializer(event).data},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class ReportSnapshotListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = AnalyticsPagination

    def get(self, request):
        serializer = ReportSnapshotSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        institution_id = serializer.validated_data.get("institution_id")
        require_analytics_view(
            token=auth_token(request),
            institution_id=str(institution_id) if institution_id else None,
            platform=institution_id is None,
        )
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(
            report_snapshots(serializer.validated_data),
            request,
            view=self,
        )
        return paginator.get_paginated_response(ReportSnapshotSerializer(page, many=True).data)

    def post(self, request):
        serializer = ReportSnapshotCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        institution_id = serializer.validated_data.get("institution_id")
        token = auth_token(request)
        require_analytics_view(
            token=token,
            institution_id=str(institution_id) if institution_id else None,
            platform=institution_id is None,
        )
        profile = current_profile(token=token)
        snapshot = create_report_snapshot(
            validated_data=serializer.validated_data,
            generated_by_profile_id=profile.get("id"),
        )
        return Response(ReportSnapshotSerializer(snapshot).data, status=status.HTTP_201_CREATED)
