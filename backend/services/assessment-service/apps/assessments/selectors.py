from __future__ import annotations

from django.db.models import Prefetch, Q

from .models import (
    Assessment,
    AssessmentStatus,
    AssignmentSubmission,
    Question,
    QuestionBank,
    QuizAttempt,
    QuizQuestion,
)


def question_bank_queryset(*, include_deleted: bool = False):
    queryset = QuestionBank.objects.all()
    if not include_deleted:
        queryset = queryset.filter(deleted_at__isnull=True)
    return queryset


def question_queryset(*, include_deleted: bool = False):
    queryset = Question.objects.select_related("question_bank")
    if not include_deleted:
        queryset = queryset.filter(deleted_at__isnull=True, question_bank__deleted_at__isnull=True)
    return queryset


def assessment_queryset(*, include_deleted: bool = False, include_metadata: bool = True):
    queryset = Assessment.objects.all()
    if include_metadata:
        queryset = queryset.select_related("quiz", "assignment").prefetch_related(
            Prefetch(
                "quiz__question_links",
                queryset=QuizQuestion.objects.select_related("question", "question__question_bank").order_by(
                    "position",
                    "id",
                ),
            )
        )
    if not include_deleted:
        queryset = queryset.filter(deleted_at__isnull=True)
    return queryset


def quiz_attempt_queryset():
    return QuizAttempt.objects.select_related("quiz", "quiz__assessment").prefetch_related(
        "answers",
        Prefetch(
            "quiz__question_links",
            queryset=QuizQuestion.objects.select_related("question").order_by("position", "id"),
        ),
    )


def assignment_submission_queryset():
    return AssignmentSubmission.objects.select_related(
        "assignment",
        "assignment__assessment",
    )


def search_question_banks(filters: dict):
    queryset = question_bank_queryset()
    if institution_id := filters.get("institution_id"):
        queryset = queryset.filter(institution_id=institution_id)
    if owner_profile_id := filters.get("owner_profile_id"):
        queryset = queryset.filter(owner_profile_id=owner_profile_id)
    if q := filters.get("q"):
        queryset = queryset.filter(Q(title__icontains=q) | Q(description__icontains=q))
    return queryset.order_by(filters.get("sort") or "-created_at", "id")


def search_questions(question_bank: QuestionBank, filters: dict):
    queryset = question_queryset().filter(question_bank=question_bank)
    if question_type := filters.get("question_type"):
        queryset = queryset.filter(question_type=question_type)
    if status := filters.get("status"):
        queryset = queryset.filter(status=status)
    if q := filters.get("q"):
        queryset = queryset.filter(prompt__icontains=q)
    return queryset.order_by(filters.get("sort") or "-created_at", "id")


def search_assessments(filters: dict, *, management: bool):
    queryset = assessment_queryset()
    if course_id := filters.get("course_id"):
        queryset = queryset.filter(course_id=course_id)
    if lesson_id := filters.get("lesson_id"):
        queryset = queryset.filter(lesson_id=lesson_id)
    if assessment_type := filters.get("assessment_type"):
        queryset = queryset.filter(assessment_type=assessment_type)
    if status := filters.get("status"):
        queryset = queryset.filter(status=status)
    if q := filters.get("q"):
        queryset = queryset.filter(Q(title__icontains=q) | Q(description__icontains=q))
    if not management:
        queryset = queryset.filter(status=AssessmentStatus.PUBLISHED)
    return queryset.order_by(filters.get("sort") or "-created_at", "id")


def search_assignment_submissions(assignment, filters: dict):
    queryset = assignment_submission_queryset().filter(assignment=assignment)
    if student_profile_id := filters.get("student_profile_id"):
        queryset = queryset.filter(student_profile_id=student_profile_id)
    if status := filters.get("status"):
        queryset = queryset.filter(status=status)
    return queryset.order_by("-updated_at", "id")
