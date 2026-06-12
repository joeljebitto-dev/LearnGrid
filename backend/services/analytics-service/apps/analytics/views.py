from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError

from .models import DashboardScopeType, SearchResourceType
from .selectors import (
    dashboard_aggregates,
    report_snapshots,
    search_index_records,
    usage_metrics,
)
from .serializers import (
    DashboardAggregateSearchSerializer,
    DashboardAggregateSerializer,
    DashboardAggregateUpsertSerializer,
    EventFactSerializer,
    EventIngestSerializer,
    ReportGenerateSerializer,
    ReportSnapshotCreateSerializer,
    ReportSnapshotSearchSerializer,
    ReportSnapshotSerializer,
    SearchIndexRecordSerializer,
    SearchIndexRecordUpsertSerializer,
    SearchQuerySerializer,
    UsageMetricCreateSerializer,
    UsageMetricSearchSerializer,
    UsageMetricSerializer,
)
from .services import (
    allowed_search_resource_types,
    auth_token,
    cached_dashboard_payload,
    cached_platform_dashboard_payload,
    create_usage_metric,
    create_report_snapshot,
    current_profile,
    delete_search_index_record,
    dashboard_scope_for_profile,
    generate_report_snapshot,
    ingest_event,
    require_analytics_view,
    require_instructor_profile,
    require_profile_view,
    require_resource_search_view,
    require_student_profile,
    upsert_dashboard_aggregate,
    upsert_search_index_record,
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
            cached_dashboard_payload(
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
            cached_dashboard_payload(
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
            cached_dashboard_payload(
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
        return Response(cached_platform_dashboard_payload(profile=profile))


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


class SearchView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = AnalyticsPagination
    resource_type: str | None = None

    def get(self, request):
        serializer = SearchQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        filters = serializer.validated_data
        token = auth_token(request)
        institution_id = str(filters["institution_id"]) if filters.get("institution_id") else None
        resource_type = self.resource_type or filters.get("resource_type")
        if resource_type:
            require_resource_search_view(
                token=token,
                resource_type=resource_type,
                institution_id=institution_id,
            )
            allowed_resource_types = [resource_type]
        else:
            allowed_resource_types = allowed_search_resource_types(
                token=token,
                institution_id=institution_id,
            )

        queryset = search_index_records(filters, resource_type=resource_type).filter(
            resource_type__in=allowed_resource_types,
        )
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        return paginator.get_paginated_response(SearchIndexRecordSerializer(page, many=True).data)


class CourseSearchView(SearchView):
    resource_type = SearchResourceType.COURSE


class UserSearchView(SearchView):
    resource_type = SearchResourceType.USER


class EnrollmentSearchView(SearchView):
    resource_type = SearchResourceType.ENROLLMENT


class AssessmentSearchView(SearchView):
    resource_type = SearchResourceType.ASSESSMENT


class SubmissionSearchView(SearchView):
    resource_type = SearchResourceType.SUBMISSION


class SearchIndexRecordUpsertView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SearchIndexRecordUpsertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        institution_id = serializer.validated_data.get("institution_id")
        require_analytics_view(
            token=auth_token(request),
            institution_id=str(institution_id) if institution_id else None,
            platform=institution_id is None,
        )
        record, created = upsert_search_index_record(serializer.validated_data)
        return Response(
            {"created": created, "record": SearchIndexRecordSerializer(record).data},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class SearchIndexRecordDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, resource_type, resource_id):
        if resource_type not in SearchResourceType.values:
            raise NotFound("Search index record was not found.")
        require_analytics_view(token=auth_token(request), platform=True)
        if not delete_search_index_record(resource_type=resource_type, resource_id=resource_id):
            raise NotFound("Search index record was not found.")
        return Response(status=status.HTTP_204_NO_CONTENT)


class DashboardAggregateListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = AnalyticsPagination

    def get(self, request):
        serializer = DashboardAggregateSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        institution_id = serializer.validated_data.get("institution_id")
        require_analytics_view(
            token=auth_token(request),
            institution_id=str(institution_id) if institution_id else None,
            platform=institution_id is None,
        )
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(
            dashboard_aggregates(serializer.validated_data),
            request,
            view=self,
        )
        return paginator.get_paginated_response(DashboardAggregateSerializer(page, many=True).data)

    def post(self, request):
        serializer = DashboardAggregateUpsertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        scope_type = serializer.validated_data["scope_type"]
        scope_id = serializer.validated_data.get("scope_id")
        require_analytics_view(
            token=auth_token(request),
            institution_id=str(scope_id) if scope_type == DashboardScopeType.INSTITUTION else None,
            platform=scope_type == DashboardScopeType.PLATFORM,
        )
        if scope_type not in {DashboardScopeType.INSTITUTION, DashboardScopeType.PLATFORM}:
            raise PermissionDenied("Only institution and platform aggregates can be managed here.")
        aggregate, created = upsert_dashboard_aggregate(serializer.validated_data)
        return Response(
            {"created": created, "aggregate": DashboardAggregateSerializer(aggregate).data},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class UsageMetricListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = AnalyticsPagination

    def get(self, request):
        serializer = UsageMetricSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        scope_type = serializer.validated_data.get("scope_type")
        scope_id = serializer.validated_data.get("scope_id")
        require_analytics_view(
            token=auth_token(request),
            institution_id=str(scope_id) if scope_type == DashboardScopeType.INSTITUTION else None,
            platform=scope_type != DashboardScopeType.INSTITUTION,
        )
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(
            usage_metrics(serializer.validated_data),
            request,
            view=self,
        )
        return paginator.get_paginated_response(UsageMetricSerializer(page, many=True).data)

    def post(self, request):
        serializer = UsageMetricCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        scope_type = serializer.validated_data.get("scope_type")
        scope_id = serializer.validated_data.get("scope_id")
        require_analytics_view(
            token=auth_token(request),
            institution_id=str(scope_id) if scope_type == DashboardScopeType.INSTITUTION else None,
            platform=scope_type != DashboardScopeType.INSTITUTION,
        )
        metric = create_usage_metric(serializer.validated_data)
        return Response(UsageMetricSerializer(metric).data, status=status.HTTP_201_CREATED)


class ReportGenerateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ReportGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        institution_id = serializer.validated_data.get("institution_id")
        token = auth_token(request)
        require_analytics_view(
            token=token,
            institution_id=str(institution_id) if institution_id else None,
            platform=institution_id is None,
        )
        profile = current_profile(token=token)
        snapshot = generate_report_snapshot(
            validated_data=serializer.validated_data,
            generated_by_profile_id=profile.get("id"),
        )
        return Response(ReportSnapshotSerializer(snapshot).data, status=status.HTTP_201_CREATED)
