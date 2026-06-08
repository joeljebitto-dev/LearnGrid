from __future__ import annotations

import uuid

from django.db import models


class QuestionType(models.TextChoices):
    MULTIPLE_CHOICE = "multiple_choice", "Multiple choice"
    MULTIPLE_SELECT = "multiple_select", "Multiple select"
    TRUE_FALSE = "true_false", "True/false"
    SHORT_ANSWER = "short_answer", "Short answer"
    ESSAY = "essay", "Essay"
    FILE_UPLOAD = "file_upload", "File upload"
    CODING = "coding", "Coding"


class QuestionStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"
    ARCHIVED = "archived", "Archived"


class AssessmentType(models.TextChoices):
    QUIZ = "quiz", "Quiz"
    EXAM = "exam", "Exam"
    ASSIGNMENT = "assignment", "Assignment"


class AssessmentStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"
    CLOSED = "closed", "Closed"
    ARCHIVED = "archived", "Archived"


class QuizAttemptStatus(models.TextChoices):
    STARTED = "started", "Started"
    SUBMITTED = "submitted", "Submitted"
    AUTO_SUBMITTED = "auto_submitted", "Auto submitted"
    CANCELLED = "cancelled", "Cancelled"
    GRADED = "graded", "Graded"


class SubmissionType(models.TextChoices):
    QUIZ_ATTEMPT = "quiz_attempt", "Quiz attempt"
    ASSIGNMENT_SUBMISSION = "assignment_submission", "Assignment submission"


class AssignmentSubmissionStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    SUBMITTED = "submitted", "Submitted"
    LATE = "late", "Late"
    WITHDRAWN = "withdrawn", "Withdrawn"
    GRADED = "graded", "Graded"


class QuestionBank(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    institution_id = models.UUIDField()
    owner_profile_id = models.UUIDField()
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "question_banks"
        indexes = [
            models.Index(fields=["institution_id", "owner_profile_id"], name="idx_qbanks_inst_owner"),
            models.Index(fields=["institution_id", "title"], name="idx_qbanks_inst_title"),
        ]

    def __str__(self) -> str:
        return self.title


class Question(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question_bank = models.ForeignKey(
        QuestionBank,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    question_type = models.CharField(max_length=32, choices=QuestionType.choices)
    prompt = models.TextField()
    choices = models.JSONField(null=True, blank=True)
    correct_answer = models.JSONField(null=True, blank=True)
    points = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    status = models.CharField(
        max_length=24,
        choices=QuestionStatus.choices,
        default=QuestionStatus.DRAFT,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "questions"
        indexes = [
            models.Index(fields=["question_bank", "question_type"], name="idx_questions_bank_type"),
            models.Index(fields=["question_bank", "status"], name="idx_questions_bank_status"),
        ]

    def __str__(self) -> str:
        return self.prompt[:80]


class Assessment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course_id = models.UUIDField()
    lesson_id = models.UUIDField(null=True, blank=True)
    created_by_profile_id = models.UUIDField()
    assessment_type = models.CharField(max_length=32, choices=AssessmentType.choices)
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(
        max_length=24,
        choices=AssessmentStatus.choices,
        default=AssessmentStatus.DRAFT,
    )
    available_from = models.DateTimeField(null=True, blank=True)
    available_until = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "assessments"
        indexes = [
            models.Index(fields=["course_id", "status"], name="idx_assess_course_status"),
            models.Index(fields=["created_by_profile_id"], name="idx_assess_created_by"),
            models.Index(fields=["available_from", "available_until"], name="idx_assess_window"),
        ]

    def __str__(self) -> str:
        return self.title


class Quiz(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.OneToOneField(
        Assessment,
        on_delete=models.CASCADE,
        related_name="quiz",
    )
    time_limit_seconds = models.IntegerField(null=True, blank=True)
    max_attempts = models.IntegerField(null=True, blank=True)
    randomize_questions = models.BooleanField(default=False)
    auto_submit = models.BooleanField(default=True)
    grading_policy = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "quizzes"
        constraints = [
            models.UniqueConstraint(fields=["assessment"], name="uq_quizzes_assessment_id"),
        ]

    def __str__(self) -> str:
        return self.assessment.title


class QuizQuestion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="question_links")
    question = models.ForeignKey(Question, on_delete=models.PROTECT, related_name="quiz_links")
    position = models.PositiveIntegerField()
    points_override = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "quiz_questions"
        constraints = [
            models.UniqueConstraint(fields=["quiz", "position"], name="uq_qquestions_quiz_position"),
            models.UniqueConstraint(fields=["quiz", "question"], name="uq_qquestions_quiz_question"),
        ]
        indexes = [
            models.Index(fields=["question"], name="idx_quiz_questions_question"),
        ]
        ordering = ["position", "id"]


class QuizAttempt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    student_profile_id = models.UUIDField()
    attempt_number = models.PositiveIntegerField()
    status = models.CharField(
        max_length=24,
        choices=QuizAttemptStatus.choices,
        default=QuizAttemptStatus.STARTED,
    )
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    score = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "quiz_attempts"
        constraints = [
            models.UniqueConstraint(
                fields=["quiz", "student_profile_id", "attempt_number"],
                name="uq_qattempts_quiz_student_num",
            ),
        ]
        indexes = [
            models.Index(fields=["student_profile_id", "status"], name="idx_qattempts_student_status"),
            models.Index(fields=["quiz", "status"], name="idx_qattempts_quiz_status"),
        ]

    def __str__(self) -> str:
        return f"{self.quiz_id}:{self.student_profile_id}:{self.attempt_number}"


class QuizAnswer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz_attempt = models.ForeignKey(
        QuizAttempt,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    question = models.ForeignKey(Question, on_delete=models.PROTECT, related_name="answers")
    answer_payload = models.JSONField()
    score = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "quiz_answers"
        constraints = [
            models.UniqueConstraint(
                fields=["quiz_attempt", "question"],
                name="uq_qanswers_attempt_question",
            ),
        ]
        indexes = [
            models.Index(fields=["question"], name="idx_quiz_answers_question_id"),
        ]


class Assignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.OneToOneField(
        Assessment,
        on_delete=models.CASCADE,
        related_name="assignment",
    )
    due_at = models.DateTimeField(null=True, blank=True)
    allow_late_submission = models.BooleanField(default=False)
    max_points = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    resource_asset_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "assignments"
        constraints = [
            models.UniqueConstraint(fields=["assessment"], name="uq_assignments_assessment_id"),
        ]
        indexes = [
            models.Index(fields=["due_at"], name="idx_assignments_due_at"),
        ]

    def __str__(self) -> str:
        return self.assessment.title


class AssignmentSubmission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    student_profile_id = models.UUIDField()
    submission_text = models.TextField(null=True, blank=True)
    attachment_asset_id = models.UUIDField(null=True, blank=True)
    status = models.CharField(
        max_length=24,
        choices=AssignmentSubmissionStatus.choices,
        default=AssignmentSubmissionStatus.SUBMITTED,
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "assignment_submissions"
        constraints = [
            models.UniqueConstraint(
                fields=["assignment", "student_profile_id"],
                name="uq_asub_assignment_student",
            ),
        ]
        indexes = [
            models.Index(fields=["status"], name="idx_asub_status"),
            models.Index(fields=["student_profile_id"], name="idx_asub_student_id"),
        ]

    def __str__(self) -> str:
        return f"{self.assignment_id}:{self.student_profile_id}"


class SubmissionAuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission_type = models.CharField(max_length=32, choices=SubmissionType.choices)
    submission_id = models.UUIDField()
    event_type = models.CharField(max_length=64)
    actor_profile_id = models.UUIDField(null=True, blank=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "submission_audit_logs"
        indexes = [
            models.Index(fields=["submission_type", "submission_id"], name="idx_submit_audit_submission"),
            models.Index(fields=["event_type"], name="idx_submit_audit_event"),
        ]
