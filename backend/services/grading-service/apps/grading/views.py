from __future__ import annotations

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import has_grade_permission, require_grade_permission
from .selectors import (
    certificate_eligibility_queryset,
    certificate_queryset,
    grade_record_queryset,
    grading_rule_queryset,
    manual_review_queryset,
    published_result_queryset,
    search_certificate_eligibility,
    search_certificates,
    search_grade_records,
    search_grading_rules,
    search_published_results,
)
from .serializers import (
    CertificateAssetUpdateSerializer,
    CertificateEligibilityEvaluateSerializer,
    CertificateEligibilitySearchSerializer,
    CertificateEligibilitySerializer,
    CertificateSearchSerializer,
    CertificateSerializer,
    GradeCalculateSerializer,
    GradeOverrideSerializer,
    GradePublishSerializer,
    GradeRecordSearchSerializer,
    GradeRecordSerializer,
    GradingRuleCreateSerializer,
    GradingRuleSearchSerializer,
    GradingRuleSerializer,
    GradingRuleUpdateSerializer,
    ManualReviewCompleteSerializer,
    ManualReviewCreateSerializer,
    ManualReviewSerializer,
    PublishedResultSearchSerializer,
    PublishedResultSerializer,
)
from .services import (
    auth_token,
    calculate_grade_from_quiz,
    complete_manual_review,
    create_grading_rule,
    create_manual_review,
    current_profile,
    evaluate_certificate_eligibility,
    fetch_grading_source,
    get_course_context,
    override_grade,
    publish_grade,
    revoke_certificate,
    update_grading_rule,
    update_certificate_asset,
)


class GradingPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


def _correlation_id(request) -> str | None:
    return request.headers.get("X-Correlation-ID")


def _course_for_request(request, course_id):
    return get_course_context(token=auth_token(request), course_id=course_id)


def _require_grade_scope(request, permission: str, course_id) -> dict:
    course = _course_for_request(request, course_id)
    require_grade_permission(
        request,
        permission,
        course_id=course_id,
        institution_id=course["institution_id"],
    )
    return course


def _has_certificate_view_scope(request, course_id) -> bool:
    course = _course_for_request(request, course_id)
    return has_grade_permission(
        request,
        "grade.view",
        course_id=course_id,
        institution_id=course["institution_id"],
    )


class GradingRuleListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = GradingPagination

    def get(self, request):
        serializer = GradingRuleSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        course_id = serializer.validated_data.get("course_id")
        if course_id:
            _require_grade_scope(request, "grade.view", course_id)
        else:
            require_grade_permission(request, "grade.view")
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(
            search_grading_rules(serializer.validated_data),
            request,
            view=self,
        )
        return paginator.get_paginated_response(GradingRuleSerializer(page, many=True).data)

    def post(self, request):
        serializer = GradingRuleCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        _require_grade_scope(request, "grade.manage", serializer.validated_data["course_id"])
        rule = create_grading_rule(validated_data=serializer.validated_data)
        return Response(GradingRuleSerializer(rule).data, status=status.HTTP_201_CREATED)


class GradingRuleDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, rule_id):
        rule = get_object_or_404(grading_rule_queryset(), id=rule_id)
        _require_grade_scope(request, "grade.view", rule.course_id)
        return Response(GradingRuleSerializer(rule).data)

    def patch(self, request, rule_id):
        rule = get_object_or_404(grading_rule_queryset(), id=rule_id)
        _require_grade_scope(request, "grade.manage", rule.course_id)
        serializer = GradingRuleUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        rule = update_grading_rule(rule=rule, validated_data=serializer.validated_data)
        return Response(GradingRuleSerializer(rule).data)


class GradeRecordListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = GradingPagination

    def get(self, request):
        serializer = GradeRecordSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        course_id = serializer.validated_data.get("course_id")
        if course_id:
            _require_grade_scope(request, "grade.view", course_id)
        else:
            require_grade_permission(request, "grade.view")
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(
            search_grade_records(serializer.validated_data),
            request,
            view=self,
        )
        return paginator.get_paginated_response(GradeRecordSerializer(page, many=True).data)


class GradeRecordDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, grade_record_id):
        grade_record = get_object_or_404(grade_record_queryset(), id=grade_record_id)
        _require_grade_scope(request, "grade.view", grade_record.course_id)
        return Response(GradeRecordSerializer(grade_record).data)


class GradeCalculateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = GradeCalculateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = auth_token(request)
        source = fetch_grading_source(
            token=token,
            submission_type=serializer.validated_data["submission_type"],
            submission_id=serializer.validated_data["submission_id"],
        )
        _require_grade_scope(request, "grade.manage", source["course_id"])
        profile = current_profile(token=token)
        grade_record = calculate_grade_from_quiz(
            source=source,
            changed_by_profile_id=profile.get("id"),
            correlation_id=_correlation_id(request),
        )
        return Response(GradeRecordSerializer(grade_record).data, status=status.HTTP_201_CREATED)


class ManualReviewCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ManualReviewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = auth_token(request)
        source = fetch_grading_source(
            token=token,
            submission_type=serializer.validated_data["submission_type"],
            submission_id=serializer.validated_data["submission_id"],
        )
        _require_grade_scope(request, "grade.manage", source["course_id"])
        profile = current_profile(token=token)
        reviewer_profile_id = serializer.validated_data.get("reviewer_profile_id") or profile.get("id")
        review = create_manual_review(source=source, reviewer_profile_id=reviewer_profile_id)
        return Response(ManualReviewSerializer(review).data, status=status.HTTP_201_CREATED)


class ManualReviewCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, review_id):
        review = get_object_or_404(manual_review_queryset(), id=review_id)
        _require_grade_scope(request, "grade.manage", review.grade_record.course_id)
        serializer = ManualReviewCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        grade_record = complete_manual_review(
            review=review,
            score=serializer.validated_data["score"],
            feedback=serializer.validated_data.get("feedback"),
        )
        return Response(GradeRecordSerializer(grade_record).data)


class GradeOverrideView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, grade_record_id):
        grade_record = get_object_or_404(grade_record_queryset(), id=grade_record_id)
        _require_grade_scope(request, "grade.manage", grade_record.course_id)
        serializer = GradeOverrideSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = current_profile(token=auth_token(request))
        grade_record = override_grade(
            grade_record=grade_record,
            score=serializer.validated_data["score"],
            max_score=serializer.validated_data.get("max_score"),
            changed_by_profile_id=profile.get("id"),
            reason=serializer.validated_data["change_reason"],
        )
        return Response(GradeRecordSerializer(grade_record).data)


class GradePublishView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, grade_record_id):
        grade_record = get_object_or_404(grade_record_queryset(), id=grade_record_id)
        _require_grade_scope(request, "grade.manage", grade_record.course_id)
        serializer = GradePublishSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = current_profile(token=auth_token(request))
        result = publish_grade(
            grade_record=grade_record,
            published_by_profile_id=profile.get("id"),
            feedback=serializer.validated_data.get("published_feedback"),
            token=auth_token(request),
            correlation_id=_correlation_id(request),
        )
        return Response(PublishedResultSerializer(result).data)


class PublishedResultListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = GradingPagination

    def get(self, request):
        serializer = PublishedResultSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        filters = serializer.validated_data
        profile = current_profile(token=auth_token(request))
        course_id = filters.get("course_id")
        manager = has_grade_permission(request, "grade.view", course_id=course_id) if course_id else has_grade_permission(request, "grade.view")
        if not manager:
            filters["student_profile_id"] = profile.get("id")
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(
            search_published_results(filters),
            request,
            view=self,
        )
        return paginator.get_paginated_response(PublishedResultSerializer(page, many=True).data)


class PublishedResultDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, result_id):
        result = get_object_or_404(published_result_queryset(), id=result_id)
        manager = has_grade_permission(request, "grade.view", course_id=result.course_id)
        if not manager:
            profile = current_profile(token=auth_token(request))
            if str(profile.get("id")) != str(result.student_profile_id):
                from rest_framework.exceptions import PermissionDenied

                raise PermissionDenied("Result belongs to another profile.")
        return Response(PublishedResultSerializer(result).data)


class CertificateEligibilityListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = GradingPagination

    def get(self, request):
        serializer = CertificateEligibilitySearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        course_id = serializer.validated_data.get("course_id")
        if course_id:
            _require_grade_scope(request, "grade.view", course_id)
        else:
            require_grade_permission(request, "grade.view")
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(
            search_certificate_eligibility(serializer.validated_data),
            request,
            view=self,
        )
        return paginator.get_paginated_response(CertificateEligibilitySerializer(page, many=True).data)


class CertificateEligibilityDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, eligibility_id):
        eligibility = get_object_or_404(certificate_eligibility_queryset(), id=eligibility_id)
        _require_grade_scope(request, "grade.view", eligibility.course_id)
        return Response(CertificateEligibilitySerializer(eligibility).data)


class CertificateEligibilityEvaluateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CertificateEligibilityEvaluateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        _require_grade_scope(request, "grade.manage", serializer.validated_data["course_id"])
        result = evaluate_certificate_eligibility(
            token=auth_token(request),
            student_profile_id=serializer.validated_data["student_profile_id"],
            course_id=serializer.validated_data["course_id"],
            certificate_asset_id=serializer.validated_data.get("certificate_asset_id"),
            correlation_id=_correlation_id(request),
        )
        return Response(
            {
                "eligibility": CertificateEligibilitySerializer(result["eligibility"]).data,
                "certificate": (
                    CertificateSerializer(result["certificate"]).data
                    if result["certificate"] is not None
                    else None
                ),
                "grade_percent": result["grade_percent"],
                "threshold_percent": result["threshold_percent"],
            },
            status=status.HTTP_200_OK,
        )


class CertificateListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = GradingPagination

    def get(self, request):
        serializer = CertificateSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        filters = serializer.validated_data
        profile = current_profile(token=auth_token(request))
        if profile.get("profile_type") == "student":
            filters["student_profile_id"] = profile.get("id")
            filters["include_revoked"] = False
        else:
            course_id = filters.get("course_id")
            manager = (
                _has_certificate_view_scope(request, course_id)
                if course_id
                else has_grade_permission(request, "grade.view")
            )
            if not manager:
                filters["student_profile_id"] = profile.get("id")
                filters["include_revoked"] = False
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(
            search_certificates(filters),
            request,
            view=self,
        )
        return paginator.get_paginated_response(CertificateSerializer(page, many=True).data)


class CertificateDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, certificate_id):
        certificate = get_object_or_404(certificate_queryset(), id=certificate_id)
        profile = current_profile(token=auth_token(request))
        if str(profile.get("id")) == str(certificate.student_profile_id) and certificate.revoked_at is None:
            return Response(CertificateSerializer(certificate).data)
        manager = _has_certificate_view_scope(request, certificate.course_id)
        if not manager:
            raise PermissionDenied("Certificate is not visible to this profile.")
        return Response(CertificateSerializer(certificate).data)

    def patch(self, request, certificate_id):
        certificate = get_object_or_404(certificate_queryset(), id=certificate_id)
        _require_grade_scope(request, "grade.manage", certificate.course_id)
        serializer = CertificateAssetUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        certificate = update_certificate_asset(
            token=auth_token(request),
            certificate=certificate,
            certificate_asset_id=serializer.validated_data.get("certificate_asset_id"),
        )
        return Response(CertificateSerializer(certificate).data)


class CertificateRevokeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, certificate_id):
        certificate = get_object_or_404(certificate_queryset(), id=certificate_id)
        _require_grade_scope(request, "grade.manage", certificate.course_id)
        certificate = revoke_certificate(certificate=certificate)
        return Response(CertificateSerializer(certificate).data)
