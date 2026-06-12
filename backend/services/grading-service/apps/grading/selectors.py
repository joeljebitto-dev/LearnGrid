from __future__ import annotations

from .models import (
    Certificate,
    CertificateEligibility,
    GradeRecord,
    GradingRule,
    ManualReview,
    PublishedResult,
)


def grading_rule_queryset():
    return GradingRule.objects.all()


def grade_record_queryset():
    return GradeRecord.objects.prefetch_related("history", "manual_reviews")


def manual_review_queryset():
    return ManualReview.objects.select_related("grade_record")


def published_result_queryset():
    return PublishedResult.objects.select_related("grade_record")


def certificate_eligibility_queryset():
    return CertificateEligibility.objects.all()


def certificate_queryset():
    return Certificate.objects.select_related("certificate_eligibility")


def search_grading_rules(filters: dict):
    queryset = grading_rule_queryset()
    if course_id := filters.get("course_id"):
        queryset = queryset.filter(course_id=course_id)
    if assessment_id := filters.get("assessment_id"):
        queryset = queryset.filter(assessment_id=assessment_id)
    if rule_type := filters.get("rule_type"):
        queryset = queryset.filter(rule_type=rule_type)
    return queryset.order_by("-updated_at", "id")


def search_grade_records(filters: dict):
    queryset = grade_record_queryset()
    for field in ["student_profile_id", "course_id", "assessment_id", "submission_id", "status"]:
        if value := filters.get(field):
            queryset = queryset.filter(**{field: value})
    return queryset.order_by(filters.get("sort") or "-updated_at", "id")


def search_published_results(filters: dict):
    queryset = published_result_queryset()
    if student_profile_id := filters.get("student_profile_id"):
        queryset = queryset.filter(student_profile_id=student_profile_id)
    if course_id := filters.get("course_id"):
        queryset = queryset.filter(course_id=course_id)
    return queryset.order_by("-published_at", "id")


def search_certificate_eligibility(filters: dict):
    queryset = certificate_eligibility_queryset()
    for field in ["student_profile_id", "course_id", "eligible"]:
        if field in filters:
            queryset = queryset.filter(**{field: filters[field]})
    return queryset.order_by("-evaluated_at", "id")


def search_certificates(filters: dict):
    queryset = certificate_queryset()
    if student_profile_id := filters.get("student_profile_id"):
        queryset = queryset.filter(student_profile_id=student_profile_id)
    if course_id := filters.get("course_id"):
        queryset = queryset.filter(course_id=course_id)
    if not filters.get("include_revoked"):
        queryset = queryset.filter(revoked_at__isnull=True)
    return queryset.order_by("-issued_at", "id")
