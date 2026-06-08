from __future__ import annotations

from rest_framework import serializers

from .models import (
    Assessment,
    AssessmentStatus,
    AssessmentType,
    Assignment,
    Question,
    QuestionBank,
    QuestionStatus,
    QuestionType,
    Quiz,
    QuizAnswer,
    QuizAttempt,
    QuizQuestion,
)


QUESTION_SORT_CHOICES = ["created_at", "-created_at", "updated_at", "-updated_at", "points", "-points"]
ASSESSMENT_SORT_CHOICES = ["created_at", "-created_at", "available_from", "-available_from", "title", "-title"]


def _choice_ids(choices) -> set[str]:
    if not isinstance(choices, list):
        return set()
    return {str(choice.get("id")) for choice in choices if isinstance(choice, dict) and choice.get("id")}


def _normalize_bool_answer(value):
    if isinstance(value, dict):
        value = value.get("value")
    if isinstance(value, bool):
        return value
    raise serializers.ValidationError("True/false correct_answer must be a boolean or {'value': boolean}.")


def validate_question_payload(attrs: dict) -> dict:
    question_type = attrs.get("question_type")
    choices = attrs.get("choices")
    correct_answer = attrs.get("correct_answer")

    if question_type == QuestionType.CODING:
        raise serializers.ValidationError({"question_type": "Coding questions are reserved for a future release."})

    if question_type in {QuestionType.MULTIPLE_CHOICE, QuestionType.MULTIPLE_SELECT}:
        ids = _choice_ids(choices)
        if not ids:
            raise serializers.ValidationError({"choices": "Objective questions require choices with stable ids."})

        if question_type == QuestionType.MULTIPLE_CHOICE:
            correct_id = correct_answer.get("choice_id") if isinstance(correct_answer, dict) else correct_answer
            if not correct_id or str(correct_id) not in ids:
                raise serializers.ValidationError({"correct_answer": "Correct choice_id must exist in choices."})
        else:
            correct_ids = correct_answer.get("choice_ids") if isinstance(correct_answer, dict) else correct_answer
            if not isinstance(correct_ids, list) or not correct_ids:
                raise serializers.ValidationError({"correct_answer": "Correct choice_ids must be a non-empty list."})
            unknown = {str(choice_id) for choice_id in correct_ids} - ids
            if unknown:
                raise serializers.ValidationError({"correct_answer": "All correct choice_ids must exist in choices."})

    if question_type == QuestionType.TRUE_FALSE:
        attrs["correct_answer"] = {"value": _normalize_bool_answer(correct_answer)}

    if question_type in {QuestionType.ESSAY, QuestionType.FILE_UPLOAD}:
        attrs["correct_answer"] = correct_answer or None
        attrs["choices"] = choices or None

    return attrs


class QuestionBankSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionBank
        fields = [
            "id",
            "institution_id",
            "owner_profile_id",
            "title",
            "description",
            "created_at",
            "updated_at",
            "deleted_at",
        ]


class QuestionBankCreateSerializer(serializers.Serializer):
    institution_id = serializers.UUIDField()
    owner_profile_id = serializers.UUIDField()
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class QuestionBankUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class QuestionBankSearchSerializer(serializers.Serializer):
    institution_id = serializers.UUIDField(required=False)
    owner_profile_id = serializers.UUIDField(required=False)
    q = serializers.CharField(required=False, allow_blank=True, max_length=255)
    sort = serializers.ChoiceField(choices=QUESTION_SORT_CHOICES, default="-created_at", required=False)


class QuestionSerializer(serializers.ModelSerializer):
    question_bank_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = Question
        fields = [
            "id",
            "question_bank_id",
            "question_type",
            "prompt",
            "choices",
            "correct_answer",
            "points",
            "status",
            "created_at",
            "updated_at",
            "deleted_at",
        ]


class StudentQuestionSerializer(serializers.ModelSerializer):
    points = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ["id", "question_type", "prompt", "choices", "points"]

    def get_points(self, question: Question):
        points_by_question = self.context.get("points_by_question", {})
        return str(points_by_question.get(question.id, question.points))


class QuestionCreateSerializer(serializers.Serializer):
    question_type = serializers.ChoiceField(choices=QuestionType.choices)
    prompt = serializers.CharField()
    choices = serializers.JSONField(required=False, allow_null=True)
    correct_answer = serializers.JSONField(required=False, allow_null=True)
    points = serializers.DecimalField(max_digits=8, decimal_places=2, required=False, min_value=0)
    status = serializers.ChoiceField(choices=QuestionStatus.choices, default=QuestionStatus.DRAFT)

    def validate(self, attrs):
        attrs["points"] = attrs.get("points", 0)
        return validate_question_payload(attrs)


class QuestionUpdateSerializer(serializers.Serializer):
    question_type = serializers.ChoiceField(choices=QuestionType.choices, required=False)
    prompt = serializers.CharField(required=False)
    choices = serializers.JSONField(required=False, allow_null=True)
    correct_answer = serializers.JSONField(required=False, allow_null=True)
    points = serializers.DecimalField(max_digits=8, decimal_places=2, required=False, min_value=0)
    status = serializers.ChoiceField(choices=QuestionStatus.choices, required=False)

    def validate(self, attrs):
        question: Question = self.context["question"]
        merged = {
            "question_type": attrs.get("question_type", question.question_type),
            "choices": attrs.get("choices", question.choices),
            "correct_answer": attrs.get("correct_answer", question.correct_answer),
        }
        validate_question_payload(merged)
        if "correct_answer" in merged and "correct_answer" in attrs:
            attrs["correct_answer"] = merged["correct_answer"]
        return attrs


class QuestionSearchSerializer(serializers.Serializer):
    question_type = serializers.ChoiceField(choices=QuestionType.choices, required=False)
    status = serializers.ChoiceField(choices=QuestionStatus.choices, required=False)
    q = serializers.CharField(required=False, allow_blank=True, max_length=255)
    sort = serializers.ChoiceField(choices=QUESTION_SORT_CHOICES, default="-created_at", required=False)


class QuizConfigSerializer(serializers.Serializer):
    time_limit_seconds = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    max_attempts = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    randomize_questions = serializers.BooleanField(default=False, required=False)
    auto_submit = serializers.BooleanField(default=True, required=False)
    grading_policy = serializers.JSONField(default=dict, required=False)


class AssignmentConfigSerializer(serializers.Serializer):
    due_at = serializers.DateTimeField(required=False, allow_null=True)
    allow_late_submission = serializers.BooleanField(default=False, required=False)
    max_points = serializers.DecimalField(max_digits=8, decimal_places=2, default=0, required=False, min_value=0)
    resource_asset_id = serializers.UUIDField(required=False, allow_null=True)


class QuizQuestionPayloadSerializer(serializers.Serializer):
    question_id = serializers.UUIDField()
    position = serializers.IntegerField(required=False, min_value=1)
    points_override = serializers.DecimalField(
        max_digits=8,
        decimal_places=2,
        required=False,
        allow_null=True,
        min_value=0,
    )


class QuizQuestionSerializer(serializers.ModelSerializer):
    question = QuestionSerializer(read_only=True)

    class Meta:
        model = QuizQuestion
        fields = ["id", "question", "position", "points_override", "created_at"]


class QuizSerializer(serializers.ModelSerializer):
    question_links = QuizQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = [
            "id",
            "time_limit_seconds",
            "max_attempts",
            "randomize_questions",
            "auto_submit",
            "grading_policy",
            "question_links",
            "created_at",
            "updated_at",
        ]


class AssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = [
            "id",
            "due_at",
            "allow_late_submission",
            "max_points",
            "resource_asset_id",
            "created_at",
            "updated_at",
        ]


class AssessmentSerializer(serializers.ModelSerializer):
    quiz = QuizSerializer(read_only=True)
    assignment = AssignmentSerializer(read_only=True)

    class Meta:
        model = Assessment
        fields = [
            "id",
            "course_id",
            "lesson_id",
            "created_by_profile_id",
            "assessment_type",
            "title",
            "description",
            "status",
            "available_from",
            "available_until",
            "quiz",
            "assignment",
            "created_at",
            "updated_at",
            "deleted_at",
        ]


class AssessmentCreateSerializer(serializers.Serializer):
    course_id = serializers.UUIDField()
    lesson_id = serializers.UUIDField(required=False, allow_null=True)
    created_by_profile_id = serializers.UUIDField()
    assessment_type = serializers.ChoiceField(choices=AssessmentType.choices)
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    available_from = serializers.DateTimeField(required=False, allow_null=True)
    available_until = serializers.DateTimeField(required=False, allow_null=True)
    quiz_config = QuizConfigSerializer(required=False)
    assignment_config = AssignmentConfigSerializer(required=False)
    questions = QuizQuestionPayloadSerializer(many=True, required=False)

    def validate(self, attrs):
        _validate_window(attrs)
        assessment_type = attrs["assessment_type"]
        if assessment_type in {AssessmentType.QUIZ, AssessmentType.EXAM}:
            attrs["quiz_config"] = attrs.get("quiz_config") or {}
        if assessment_type == AssessmentType.ASSIGNMENT:
            attrs["assignment_config"] = attrs.get("assignment_config") or {}
            if attrs.get("questions"):
                raise serializers.ValidationError({"questions": "Assignments do not support quiz questions."})
        return attrs


class AssessmentUpdateSerializer(serializers.Serializer):
    course_id = serializers.UUIDField(required=False)
    lesson_id = serializers.UUIDField(required=False, allow_null=True)
    title = serializers.CharField(required=False, max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    available_from = serializers.DateTimeField(required=False, allow_null=True)
    available_until = serializers.DateTimeField(required=False, allow_null=True)
    quiz_config = QuizConfigSerializer(required=False)
    assignment_config = AssignmentConfigSerializer(required=False)
    questions = QuizQuestionPayloadSerializer(many=True, required=False)

    def validate(self, attrs):
        assessment: Assessment = self.context["assessment"]
        window = {
            "available_from": attrs.get("available_from", assessment.available_from),
            "available_until": attrs.get("available_until", assessment.available_until),
        }
        _validate_window(window)
        if assessment.assessment_type == AssessmentType.ASSIGNMENT and attrs.get("questions"):
            raise serializers.ValidationError({"questions": "Assignments do not support quiz questions."})
        return attrs


class AssessmentSearchSerializer(serializers.Serializer):
    course_id = serializers.UUIDField(required=False)
    lesson_id = serializers.UUIDField(required=False)
    status = serializers.ChoiceField(choices=AssessmentStatus.choices, required=False)
    assessment_type = serializers.ChoiceField(choices=AssessmentType.choices, required=False)
    q = serializers.CharField(required=False, allow_blank=True, max_length=255)
    sort = serializers.ChoiceField(choices=ASSESSMENT_SORT_CHOICES, default="-created_at", required=False)


class QuizQuestionReplaceSerializer(serializers.Serializer):
    questions = QuizQuestionPayloadSerializer(many=True)


class QuizAnswerSerializer(serializers.ModelSerializer):
    question_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = QuizAnswer
        fields = ["id", "question_id", "answer_payload", "score", "graded_at", "created_at", "updated_at"]


class QuizAttemptSerializer(serializers.ModelSerializer):
    assessment_id = serializers.UUIDField(source="quiz.assessment_id", read_only=True)
    answers = QuizAnswerSerializer(many=True, read_only=True)

    class Meta:
        model = QuizAttempt
        fields = [
            "id",
            "assessment_id",
            "student_profile_id",
            "attempt_number",
            "status",
            "started_at",
            "submitted_at",
            "score",
            "answers",
            "created_at",
            "updated_at",
        ]


class QuizAttemptStartSerializer(serializers.Serializer):
    pass


class QuizAttemptQuestionSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    question_type = serializers.CharField()
    prompt = serializers.CharField()
    choices = serializers.JSONField(allow_null=True)
    points = serializers.CharField()


class QuizAttemptDetailSerializer(serializers.Serializer):
    attempt = QuizAttemptSerializer()
    questions = QuizAttemptQuestionSerializer(many=True)
    deadline_at = serializers.DateTimeField(allow_null=True)


class QuizAnswerPayloadSerializer(serializers.Serializer):
    question_id = serializers.UUIDField()
    answer_payload = serializers.JSONField()


class QuizAnswersUpsertSerializer(serializers.Serializer):
    answers = QuizAnswerPayloadSerializer(many=True)


def _validate_window(attrs: dict) -> None:
    available_from = attrs.get("available_from")
    available_until = attrs.get("available_until")
    if available_from and available_until and available_until <= available_from:
        raise serializers.ValidationError({"available_until": "End window must be after start window."})
