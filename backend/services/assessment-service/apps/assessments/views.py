from __future__ import annotations

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AssessmentStatus
from .permissions import has_assessment_permission, require_assessment_permission
from .selectors import (
    assessment_queryset,
    question_bank_queryset,
    question_queryset,
    quiz_attempt_queryset,
    search_assessments,
    search_question_banks,
    search_questions,
)
from .serializers import (
    AssessmentCreateSerializer,
    AssessmentSearchSerializer,
    AssessmentSerializer,
    AssessmentUpdateSerializer,
    QuestionBankCreateSerializer,
    QuestionBankSearchSerializer,
    QuestionBankSerializer,
    QuestionBankUpdateSerializer,
    QuestionCreateSerializer,
    QuestionSearchSerializer,
    QuestionSerializer,
    QuestionUpdateSerializer,
    QuizAnswersUpsertSerializer,
    QuizAttemptSerializer,
    QuizQuestionReplaceSerializer,
    StudentQuestionSerializer,
)
from .services import (
    archive_assessment,
    archive_question,
    archive_question_bank,
    attempt_deadline,
    auth_token,
    close_assessment,
    create_assessment,
    create_question,
    create_question_bank,
    current_profile,
    get_course_context,
    has_enrollment_access,
    ordered_attempt_questions,
    points_by_question,
    publish_assessment,
    replace_quiz_questions,
    save_attempt_answers,
    start_quiz_attempt,
    submit_attempt,
    update_assessment,
    update_question,
    update_question_bank,
)


class AssessmentPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


def _correlation_id(request) -> str | None:
    return request.headers.get("X-Correlation-ID")


def _course_context_for_request(request, course_id):
    return get_course_context(token=auth_token(request), course_id=course_id)


def _can_manage_assessment(request, assessment) -> tuple[bool, dict]:
    course = _course_context_for_request(request, assessment.course_id)
    return (
        has_assessment_permission(
            request,
            "assessment.manage",
            course_id=assessment.course_id,
            institution_id=course["institution_id"],
        ),
        course,
    )


def _require_assessment_manage(request, assessment) -> dict:
    course = _course_context_for_request(request, assessment.course_id)
    require_assessment_permission(
        request,
        "assessment.manage",
        course_id=assessment.course_id,
        institution_id=course["institution_id"],
    )
    return course


def _require_published_student_access(request, assessment, course: dict) -> None:
    require_assessment_permission(
        request,
        "assessment.view",
        course_id=assessment.course_id,
        institution_id=course["institution_id"],
    )
    profile = current_profile(token=auth_token(request))
    if profile.get("profile_type") == "student" and not has_enrollment_access(
        token=auth_token(request),
        student_profile_id=profile["id"],
        course_id=assessment.course_id,
    ):
        from rest_framework.exceptions import PermissionDenied

        raise PermissionDenied("Student does not have active access to this course.")


def _assessment_attempt_payload(attempt):
    questions = ordered_attempt_questions(attempt)
    return {
        "attempt": QuizAttemptSerializer(attempt).data,
        "questions": StudentQuestionSerializer(
            questions,
            many=True,
            context={"points_by_question": points_by_question(attempt)},
        ).data,
        "deadline_at": attempt_deadline(attempt),
    }


class QuestionBankListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = AssessmentPagination

    def get(self, request):
        serializer = QuestionBankSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        institution_id = serializer.validated_data.get("institution_id")
        require_assessment_permission(request, "assessment.view", institution_id=institution_id)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(
            search_question_banks(serializer.validated_data),
            request,
            view=self,
        )
        return paginator.get_paginated_response(QuestionBankSerializer(page, many=True).data)

    def post(self, request):
        serializer = QuestionBankCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        require_assessment_permission(
            request,
            "assessment.manage",
            institution_id=serializer.validated_data["institution_id"],
        )
        question_bank = create_question_bank(validated_data=serializer.validated_data)
        return Response(QuestionBankSerializer(question_bank).data, status=status.HTTP_201_CREATED)


class QuestionBankDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, question_bank_id):
        question_bank = get_object_or_404(question_bank_queryset(), id=question_bank_id)
        require_assessment_permission(request, "assessment.view", institution_id=question_bank.institution_id)
        return Response(QuestionBankSerializer(question_bank).data)

    def patch(self, request, question_bank_id):
        question_bank = get_object_or_404(question_bank_queryset(), id=question_bank_id)
        require_assessment_permission(request, "assessment.manage", institution_id=question_bank.institution_id)
        serializer = QuestionBankUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        question_bank = update_question_bank(question_bank=question_bank, validated_data=serializer.validated_data)
        return Response(QuestionBankSerializer(question_bank).data)

    def delete(self, request, question_bank_id):
        question_bank = get_object_or_404(question_bank_queryset(), id=question_bank_id)
        require_assessment_permission(request, "assessment.manage", institution_id=question_bank.institution_id)
        question_bank = archive_question_bank(question_bank=question_bank)
        return Response(QuestionBankSerializer(question_bank).data)


class QuestionListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = AssessmentPagination

    def get(self, request, question_bank_id):
        question_bank = get_object_or_404(question_bank_queryset(), id=question_bank_id)
        require_assessment_permission(request, "assessment.view", institution_id=question_bank.institution_id)
        serializer = QuestionSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(
            search_questions(question_bank, serializer.validated_data),
            request,
            view=self,
        )
        return paginator.get_paginated_response(QuestionSerializer(page, many=True).data)

    def post(self, request, question_bank_id):
        question_bank = get_object_or_404(question_bank_queryset(), id=question_bank_id)
        require_assessment_permission(request, "assessment.manage", institution_id=question_bank.institution_id)
        serializer = QuestionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = create_question(question_bank=question_bank, validated_data=serializer.validated_data)
        return Response(QuestionSerializer(question).data, status=status.HTTP_201_CREATED)


class QuestionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, question_id):
        question = get_object_or_404(question_queryset(), id=question_id)
        require_assessment_permission(request, "assessment.view", institution_id=question.question_bank.institution_id)
        return Response(QuestionSerializer(question).data)

    def patch(self, request, question_id):
        question = get_object_or_404(question_queryset(), id=question_id)
        require_assessment_permission(request, "assessment.manage", institution_id=question.question_bank.institution_id)
        serializer = QuestionUpdateSerializer(
            data=request.data,
            partial=True,
            context={"question": question},
        )
        serializer.is_valid(raise_exception=True)
        question = update_question(question=question, validated_data=serializer.validated_data)
        return Response(QuestionSerializer(question).data)

    def delete(self, request, question_id):
        question = get_object_or_404(question_queryset(), id=question_id)
        require_assessment_permission(request, "assessment.manage", institution_id=question.question_bank.institution_id)
        question = archive_question(question=question)
        return Response(QuestionSerializer(question).data)


class AssessmentListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = AssessmentPagination

    def get(self, request):
        serializer = AssessmentSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        filters = serializer.validated_data
        course_id = filters.get("course_id")
        if course_id:
            course = _course_context_for_request(request, course_id)
            management = has_assessment_permission(
                request,
                "assessment.manage",
                course_id=course_id,
                institution_id=course["institution_id"],
            )
            if not management:
                require_assessment_permission(
                    request,
                    "assessment.view",
                    course_id=course_id,
                    institution_id=course["institution_id"],
                )
                profile = current_profile(token=auth_token(request))
                if profile.get("profile_type") == "student" and not has_enrollment_access(
                    token=auth_token(request),
                    student_profile_id=profile["id"],
                    course_id=course_id,
                ):
                    from rest_framework.exceptions import PermissionDenied

                    raise PermissionDenied("Student does not have active access to this course.")
        else:
            management = has_assessment_permission(request, "assessment.manage")
            if not management:
                require_assessment_permission(request, "assessment.view")

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(
            search_assessments(filters, management=management),
            request,
            view=self,
        )
        return paginator.get_paginated_response(AssessmentSerializer(page, many=True).data)

    def post(self, request):
        serializer = AssessmentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        course = _course_context_for_request(request, serializer.validated_data["course_id"])
        require_assessment_permission(
            request,
            "assessment.manage",
            course_id=serializer.validated_data["course_id"],
            institution_id=course["institution_id"],
        )
        assessment = create_assessment(validated_data=serializer.validated_data)
        return Response(AssessmentSerializer(assessment).data, status=status.HTTP_201_CREATED)


class AssessmentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, assessment_id):
        assessment = get_object_or_404(assessment_queryset(include_deleted=True), id=assessment_id)
        management, course = _can_manage_assessment(request, assessment)
        if assessment.status == AssessmentStatus.PUBLISHED and assessment.deleted_at is None:
            if not management:
                _require_published_student_access(request, assessment, course)
        elif not management:
            require_assessment_permission(
                request,
                "assessment.manage",
                course_id=assessment.course_id,
                institution_id=course["institution_id"],
            )
        return Response(AssessmentSerializer(assessment).data)

    def patch(self, request, assessment_id):
        assessment = get_object_or_404(assessment_queryset(), id=assessment_id)
        _require_assessment_manage(request, assessment)
        serializer = AssessmentUpdateSerializer(
            data=request.data,
            partial=True,
            context={"assessment": assessment},
        )
        serializer.is_valid(raise_exception=True)
        if "course_id" in serializer.validated_data:
            course = _course_context_for_request(request, serializer.validated_data["course_id"])
            require_assessment_permission(
                request,
                "assessment.manage",
                course_id=serializer.validated_data["course_id"],
                institution_id=course["institution_id"],
            )
        assessment = update_assessment(assessment=assessment, validated_data=serializer.validated_data)
        return Response(AssessmentSerializer(assessment).data)

    def delete(self, request, assessment_id):
        assessment = get_object_or_404(assessment_queryset(), id=assessment_id)
        _require_assessment_manage(request, assessment)
        assessment = archive_assessment(assessment=assessment)
        return Response(AssessmentSerializer(assessment).data)


class AssessmentQuestionReplaceView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, assessment_id):
        assessment = get_object_or_404(assessment_queryset(), id=assessment_id)
        _require_assessment_manage(request, assessment)
        serializer = QuizQuestionReplaceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        replace_quiz_questions(assessment=assessment, question_payloads=serializer.validated_data["questions"])
        assessment = get_object_or_404(assessment_queryset(), id=assessment_id)
        return Response(AssessmentSerializer(assessment).data)


class AssessmentPublishView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, assessment_id):
        assessment = get_object_or_404(assessment_queryset(), id=assessment_id)
        _require_assessment_manage(request, assessment)
        assessment = publish_assessment(assessment=assessment, correlation_id=_correlation_id(request))
        return Response(AssessmentSerializer(assessment).data)


class AssessmentCloseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, assessment_id):
        assessment = get_object_or_404(assessment_queryset(), id=assessment_id)
        _require_assessment_manage(request, assessment)
        assessment = close_assessment(assessment=assessment, correlation_id=_correlation_id(request))
        return Response(AssessmentSerializer(assessment).data)


class QuizAttemptStartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, assessment_id):
        assessment = get_object_or_404(assessment_queryset(), id=assessment_id)
        course = _course_context_for_request(request, assessment.course_id)
        require_assessment_permission(
            request,
            "assessment.view",
            course_id=assessment.course_id,
            institution_id=course["institution_id"],
        )
        profile = current_profile(token=auth_token(request))
        attempt = start_quiz_attempt(
            assessment=assessment,
            token=auth_token(request),
            profile=profile,
            correlation_id=_correlation_id(request),
        )
        return Response(_assessment_attempt_payload(attempt), status=status.HTTP_201_CREATED)


class QuizAttemptDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, attempt_id):
        attempt = get_object_or_404(quiz_attempt_queryset(), id=attempt_id)
        course = _course_context_for_request(request, attempt.quiz.assessment.course_id)
        management = has_assessment_permission(
            request,
            "assessment.manage",
            course_id=attempt.quiz.assessment.course_id,
            institution_id=course["institution_id"],
        )
        if not management:
            profile = current_profile(token=auth_token(request))
            if str(profile.get("id")) != str(attempt.student_profile_id):
                from rest_framework.exceptions import PermissionDenied

                raise PermissionDenied("Attempt belongs to another profile.")
            require_assessment_permission(
                request,
                "assessment.view",
                course_id=attempt.quiz.assessment.course_id,
                institution_id=course["institution_id"],
            )
        return Response(_assessment_attempt_payload(attempt))


class QuizAttemptAnswersView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, attempt_id):
        attempt = get_object_or_404(quiz_attempt_queryset(), id=attempt_id)
        profile = current_profile(token=auth_token(request))
        if str(profile.get("id")) != str(attempt.student_profile_id):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Attempt belongs to another profile.")
        course = _course_context_for_request(request, attempt.quiz.assessment.course_id)
        require_assessment_permission(
            request,
            "assessment.view",
            course_id=attempt.quiz.assessment.course_id,
            institution_id=course["institution_id"],
        )
        serializer = QuizAnswersUpsertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attempt = save_attempt_answers(attempt=attempt, answers=serializer.validated_data["answers"])
        attempt = get_object_or_404(quiz_attempt_queryset(), id=attempt.id)
        return Response(_assessment_attempt_payload(attempt))


class QuizAttemptSubmitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, attempt_id):
        attempt = get_object_or_404(quiz_attempt_queryset(), id=attempt_id)
        profile = current_profile(token=auth_token(request))
        if str(profile.get("id")) != str(attempt.student_profile_id):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Attempt belongs to another profile.")
        course = _course_context_for_request(request, attempt.quiz.assessment.course_id)
        require_assessment_permission(
            request,
            "assessment.view",
            course_id=attempt.quiz.assessment.course_id,
            institution_id=course["institution_id"],
        )
        attempt = submit_attempt(
            attempt=attempt,
            actor_profile_id=profile["id"],
            auto=False,
            correlation_id=_correlation_id(request),
        )
        return Response(QuizAttemptSerializer(attempt).data)


class QuizAttemptAutoSubmitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, attempt_id):
        attempt = get_object_or_404(quiz_attempt_queryset(), id=attempt_id)
        profile = current_profile(token=auth_token(request))
        if str(profile.get("id")) != str(attempt.student_profile_id):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Attempt belongs to another profile.")
        attempt = submit_attempt(
            attempt=attempt,
            actor_profile_id=profile["id"],
            auto=True,
            correlation_id=_correlation_id(request),
        )
        return Response(QuizAttemptSerializer(attempt).data)
