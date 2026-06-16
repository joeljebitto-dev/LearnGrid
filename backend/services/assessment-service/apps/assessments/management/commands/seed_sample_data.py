from __future__ import annotations

import sys
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

ROOT = Path(__file__).resolve().parents[7]
sys.path.append(str(ROOT / "scripts" / "sample_data"))

from seed_helpers import (  # noqa: E402
    add_seed_arguments,
    course_id,
    days_from_now,
    decimal_value,
    load_manifest,
    now,
    planned,
    profile_id,
    uuid_value,
)

from apps.assessments.models import (  # noqa: E402
    Assessment,
    AssessmentStatus,
    AssessmentType,
    Assignment,
    AssignmentSubmission,
    AssignmentSubmissionStatus,
    Question,
    QuestionBank,
    QuestionStatus,
    QuestionType,
    Quiz,
    QuizAnswer,
    QuizAttempt,
    QuizAttemptStatus,
    QuizQuestion,
    SubmissionAuditLog,
    SubmissionType,
)


class Command(BaseCommand):
    help = "Seed LearnGrid demo sample data for assessment-service."

    def add_arguments(self, parser) -> None:
        add_seed_arguments(parser, __file__)

    def handle(self, *args, **options) -> None:
        manifest = load_manifest(options["manifest"])
        records = [
            "question_banks",
            "questions",
            "quiz_assessments",
            "quiz_attempts",
            "assignment_submissions",
            "submission_audit_logs",
        ]
        if options["dry_run"]:
            planned(self, "assessment-service", manifest, records)
            return
        with transaction.atomic():
            if options["reset_sample_data"]:
                self.reset(manifest)
            self.seed(manifest)
        self.stdout.write(self.style.SUCCESS("Seeded assessment-service sample data."))

    def reset(self, manifest: dict) -> None:
        data = manifest["assessment"]
        SubmissionAuditLog.objects.filter(id=uuid_value(data["submission_audit_id"])).delete()
        AssignmentSubmission.objects.filter(
            id=uuid_value(data["assignment_submission_id"])
        ).delete()
        Assignment.objects.filter(id=uuid_value(data["assignment_id"])).delete()
        QuizAnswer.objects.filter(
            id__in=[uuid_value(data["quiz_answer_one_id"]), uuid_value(data["quiz_answer_two_id"])]
        ).delete()
        QuizAttempt.objects.filter(id=uuid_value(data["quiz_attempt_id"])).delete()
        QuizQuestion.objects.filter(
            id__in=[
                uuid_value(data["quiz_question_one_id"]),
                uuid_value(data["quiz_question_two_id"]),
            ]
        ).delete()
        Quiz.objects.filter(id=uuid_value(data["quiz_id"])).delete()
        Assessment.objects.filter(
            id__in=[
                uuid_value(data["quiz_assessment_id"]),
                uuid_value(data["assignment_assessment_id"]),
            ]
        ).delete()
        Question.objects.filter(
            id__in=[uuid_value(data["question_one_id"]), uuid_value(data["question_two_id"])]
        ).delete()
        QuestionBank.objects.filter(id=uuid_value(data["question_bank_id"])).delete()

    def seed(self, manifest: dict) -> None:
        data = manifest["assessment"]
        current_time = now()
        bank, _created = QuestionBank.objects.update_or_create(
            id=uuid_value(data["question_bank_id"]),
            defaults={
                "institution_id": uuid_value(manifest["institution"]["id"]),
                "owner_profile_id": profile_id(manifest, "instructor"),
                "title": "Demo Question Bank",
                "description": "Seeded question bank for local quiz authoring.",
                "deleted_at": None,
            },
        )
        question_one, _created = Question.objects.update_or_create(
            id=uuid_value(data["question_one_id"]),
            defaults={
                "question_bank": bank,
                "question_type": QuestionType.MULTIPLE_CHOICE,
                "prompt": "What does LearnGrid organize for learners?",
                "choices": [
                    {"id": "A", "text": "Courses, lessons, and assessments"},
                    {"id": "B", "text": "Only invoices"},
                    {"id": "C", "text": "Only calendar events"},
                ],
                "correct_answer": {"choice_id": "A"},
                "points": decimal_value("50.00"),
                "status": QuestionStatus.PUBLISHED,
                "deleted_at": None,
            },
        )
        question_two, _created = Question.objects.update_or_create(
            id=uuid_value(data["question_two_id"]),
            defaults={
                "question_bank": bank,
                "question_type": QuestionType.TRUE_FALSE,
                "prompt": "Published lessons can appear in the learning portal.",
                "choices": [{"id": "true", "text": "True"}, {"id": "false", "text": "False"}],
                "correct_answer": {"choice_id": "true"},
                "points": decimal_value("50.00"),
                "status": QuestionStatus.PUBLISHED,
                "deleted_at": None,
            },
        )
        quiz_assessment, _created = Assessment.objects.update_or_create(
            id=uuid_value(data["quiz_assessment_id"]),
            defaults={
                "course_id": course_id(manifest),
                "lesson_id": uuid_value(manifest["courses"]["main"]["lesson_id"]),
                "created_by_profile_id": profile_id(manifest, "instructor"),
                "assessment_type": AssessmentType.QUIZ,
                "title": "Demo Knowledge Check",
                "description": "Objective seeded quiz.",
                "status": AssessmentStatus.PUBLISHED,
                "available_from": current_time,
                "available_until": days_from_now(30),
                "deleted_at": None,
            },
        )
        quiz, _created = Quiz.objects.update_or_create(
            id=uuid_value(data["quiz_id"]),
            defaults={
                "assessment": quiz_assessment,
                "time_limit_seconds": 900,
                "max_attempts": 3,
                "randomize_questions": False,
                "auto_submit": True,
                "grading_policy": {
                    "seed_namespace": manifest["seed_namespace"],
                    "mode": "objective",
                },
            },
        )
        QuizQuestion.objects.update_or_create(
            id=uuid_value(data["quiz_question_one_id"]),
            defaults={
                "quiz": quiz,
                "question": question_one,
                "position": 1,
                "points_override": None,
            },
        )
        QuizQuestion.objects.update_or_create(
            id=uuid_value(data["quiz_question_two_id"]),
            defaults={
                "quiz": quiz,
                "question": question_two,
                "position": 2,
                "points_override": None,
            },
        )
        attempt, _created = QuizAttempt.objects.update_or_create(
            id=uuid_value(data["quiz_attempt_id"]),
            defaults={
                "quiz": quiz,
                "student_profile_id": profile_id(manifest, "student"),
                "attempt_number": 1,
                "status": QuizAttemptStatus.GRADED,
                "submitted_at": current_time,
                "score": decimal_value("90.00"),
            },
        )
        QuizAnswer.objects.update_or_create(
            id=uuid_value(data["quiz_answer_one_id"]),
            defaults={
                "quiz_attempt": attempt,
                "question": question_one,
                "answer_payload": {"choice_id": "A"},
                "score": decimal_value("50.00"),
                "graded_at": current_time,
            },
        )
        QuizAnswer.objects.update_or_create(
            id=uuid_value(data["quiz_answer_two_id"]),
            defaults={
                "quiz_attempt": attempt,
                "question": question_two,
                "answer_payload": {"choice_id": "false"},
                "score": decimal_value("40.00"),
                "graded_at": current_time,
            },
        )

        assignment_assessment, _created = Assessment.objects.update_or_create(
            id=uuid_value(data["assignment_assessment_id"]),
            defaults={
                "course_id": course_id(manifest),
                "lesson_id": uuid_value(manifest["courses"]["main"]["lesson_id"]),
                "created_by_profile_id": profile_id(manifest, "instructor"),
                "assessment_type": AssessmentType.ASSIGNMENT,
                "title": "Demo Reflection Assignment",
                "description": "Short seeded assignment submission.",
                "status": AssessmentStatus.PUBLISHED,
                "available_from": current_time,
                "available_until": days_from_now(30),
                "deleted_at": None,
            },
        )
        assignment, _created = Assignment.objects.update_or_create(
            id=uuid_value(data["assignment_id"]),
            defaults={
                "assessment": assignment_assessment,
                "due_at": days_from_now(14),
                "allow_late_submission": True,
                "max_points": decimal_value("100.00"),
                "resource_asset_id": uuid_value(manifest["content"]["lesson_document"]["id"]),
            },
        )
        submission, _created = AssignmentSubmission.objects.update_or_create(
            id=uuid_value(data["assignment_submission_id"]),
            defaults={
                "assignment": assignment,
                "student_profile_id": profile_id(manifest, "student"),
                "submission_text": "This is a seeded reflection for local grading demos.",
                "attachment_asset_id": uuid_value(manifest["content"]["lesson_document"]["id"]),
                "status": AssignmentSubmissionStatus.GRADED,
                "submitted_at": current_time,
            },
        )
        SubmissionAuditLog.objects.update_or_create(
            id=uuid_value(data["submission_audit_id"]),
            defaults={
                "submission_type": SubmissionType.ASSIGNMENT_SUBMISSION,
                "submission_id": submission.id,
                "event_type": "submitted",
                "actor_profile_id": profile_id(manifest, "student"),
                "metadata": {"seed_namespace": manifest["seed_namespace"]},
            },
        )
