from django.urls import path

from .views import (
    CertificateDetailView,
    CertificateEligibilityDetailView,
    CertificateEligibilityEvaluateView,
    CertificateEligibilityListView,
    CertificateListView,
    CertificateRevokeView,
    GradeCalculateView,
    GradeOverrideView,
    GradePublishView,
    GradeRecordDetailView,
    GradeRecordListView,
    GradingRuleDetailView,
    GradingRuleListCreateView,
    ManualReviewCompleteView,
    ManualReviewCreateView,
    PublishedResultDetailView,
    PublishedResultListView,
)


urlpatterns = [
    path("rules/", GradingRuleListCreateView.as_view(), name="grading-rule-list-create"),
    path("rules/<uuid:rule_id>/", GradingRuleDetailView.as_view(), name="grading-rule-detail"),
    path("records/", GradeRecordListView.as_view(), name="grade-record-list"),
    path("records/calculate/", GradeCalculateView.as_view(), name="grade-record-calculate"),
    path("records/manual-reviews/", ManualReviewCreateView.as_view(), name="manual-review-create"),
    path("records/<uuid:grade_record_id>/", GradeRecordDetailView.as_view(), name="grade-record-detail"),
    path("records/<uuid:grade_record_id>/override/", GradeOverrideView.as_view(), name="grade-record-override"),
    path("records/<uuid:grade_record_id>/publish/", GradePublishView.as_view(), name="grade-record-publish"),
    path("manual-reviews/<uuid:review_id>/complete/", ManualReviewCompleteView.as_view(), name="manual-review-complete"),
    path("results/", PublishedResultListView.as_view(), name="published-result-list"),
    path("results/<uuid:result_id>/", PublishedResultDetailView.as_view(), name="published-result-detail"),
    path(
        "certificates/eligibility/",
        CertificateEligibilityListView.as_view(),
        name="certificate-eligibility-list",
    ),
    path(
        "certificates/eligibility/evaluate/",
        CertificateEligibilityEvaluateView.as_view(),
        name="certificate-eligibility-evaluate",
    ),
    path(
        "certificates/eligibility/<uuid:eligibility_id>/",
        CertificateEligibilityDetailView.as_view(),
        name="certificate-eligibility-detail",
    ),
    path("certificates/", CertificateListView.as_view(), name="certificate-list"),
    path("certificates/<uuid:certificate_id>/", CertificateDetailView.as_view(), name="certificate-detail"),
    path("certificates/<uuid:certificate_id>/revoke/", CertificateRevokeView.as_view(), name="certificate-revoke"),
]
