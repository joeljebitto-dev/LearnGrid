from __future__ import annotations

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AssessmentStatus
from .permissions import (
    has_assessment_permission,
    has_scoped_permission,
    require_assessment_permission,
    require_scoped_permission,
)
from .selectors import (
    assignment_submission_queryset,
    assessment_queryset,
    question_bank_queryset,
    question_queryset,
    quiz_attempt_queryset,
    search_assignment_submissions,
    search_assessments,
    search_question_banks,
    search_questions,
)
from .serializers import (
    AssessmentCreateSerializer,
    AssessmentSearchSerializer,
    AssessmentSerializer,
    AssessmentUpdateSerializer,
    AssignmentSubmissionCreateSerializer,
    AssignmentSubmissionGradingSourceSerializer,
    AssignmentSubmissionMarkGradedSerializer,
    AssignmentSubmissionSearchSerializer,
    AssignmentSubmissionSerializer,
    AssignmentSubmissionUpdateSerializer,
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
    QuizAttemptGradingSourceSerializer,
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
    assignment_submission_grading_source,
    mark_assignment_submission_graded,
    ordered_attempt_questions,
    points_by_question,
    publish_assessment,
    replace_quiz_questions,
    save_attempt_answers,
    save_assignment_submission,
    start_quiz_attempt,
    submit_assignment_submission,
    submit_attempt,
    update_assessment,
    update_assignment_submission,
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


def _assignment_submission_manage_allowed(request, assignment) -> tuple[bool, dict]:
    course = _course_context_for_request(request, assignment.assessment.course_id)
    return (
        has_scoped_permission(
            request,
            "submission.manage",
            course_id=assignment.assessment.course_id,
            institution_id=course["institution_id"],
        ),
        course,
    )


def _require_submission_scope(request, permission: str, assignment) -> dict:
    course = _course_context_for_request(request, assignment.assessment.course_id)
    require_scoped_permission(
        request,
        permission,
        course_id=assignment.assessment.course_id,
        institution_id=course["institution_id"],
        message="You do not have permission to access this submission scope.",
    )
    return course


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
        require_assessment_permission(
            request, "assessment.view", institution_id=question_bank.institution_id
        )
        return Response(QuestionBankSerializer(question_bank).data)

    def patch(self, request, question_bank_id):
        question_bank = get_object_or_404(question_bank_queryset(), id=question_bank_id)
        require_assessment_permission(
            request, "assessment.manage", institution_id=question_bank.institution_id
        )
        serializer = QuestionBankUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        question_bank = update_question_bank(
            question_bank=question_bank, validated_data=serializer.validated_data
        )
        return Response(QuestionBankSerializer(question_bank).data)

    def delete(self, request, question_bank_id):
        question_bank = get_object_or_404(question_bank_queryset(), id=question_bank_id)
        require_assessment_permission(
            request, "assessment.manage", institution_id=question_bank.institution_id
        )
        question_bank = archive_question_bank(question_bank=question_bank)
        return Response(QuestionBankSerializer(question_bank).data)


class QuestionListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = AssessmentPagination

    def get(self, request, question_bank_id):
        question_bank = get_object_or_404(question_bank_queryset(), id=question_bank_id)
        require_assessment_permission(
            request, "assessment.view", institution_id=question_bank.institution_id
        )
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
        require_assessment_permission(
            request, "assessment.manage", institution_id=question_bank.institution_id
        )
        serializer = QuestionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = create_question(
            question_bank=question_bank, validated_data=serializer.validated_data
        )
        return Response(QuestionSerializer(question).data, status=status.HTTP_201_CREATED)


class QuestionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, question_id):
        question = get_object_or_404(question_queryset(), id=question_id)
        require_assessment_permission(
            request, "assessment.view", institution_id=question.question_bank.institution_id
        )
        return Response(QuestionSerializer(question).data)

    def patch(self, request, question_id):
        question = get_object_or_404(question_queryset(), id=question_id)
        require_assessment_permission(
            request, "assessment.manage", institution_id=question.question_bank.institution_id
        )
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
        require_assessment_permission(
            request, "assessment.manage", institution_id=question.question_bank.institution_id
        )
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
        assessment = update_assessment(
            assessment=assessment, validated_data=serializer.validated_data
        )
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
        replace_quiz_questions(
            assessment=assessment, question_payloads=serializer.validated_data["questions"]
        )
        assessment = get_object_or_404(assessment_queryset(), id=assessment_id)
        return Response(AssessmentSerializer(assessment).data)


class AssessmentPublishView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, assessment_id):
        assessment = get_object_or_404(assessment_queryset(), id=assessment_id)
        _require_assessment_manage(request, assessment)
        assessment = publish_assessment(
            assessment=assessment, correlation_id=_correlation_id(request)
        )
        return Response(AssessmentSerializer(assessment).data)


class AssessmentCloseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, assessment_id):
        assessment = get_object_or_404(assessment_queryset(), id=assessment_id)
        _require_assessment_manage(request, assessment)
        assessment = close_assessment(
            assessment=assessment, correlation_id=_correlation_id(request)
        )
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
        attempt = save_attempt_answers(
            attempt=attempt, answers=serializer.validated_data["answers"]
        )
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


class AssignmentSubmissionListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = AssessmentPagination

    def get(self, request, assignment_id):
        from .models import Assignment

        assignment = get_object_or_404(
            Assignment.objects.select_related("assessment"), id=assignment_id
        )
        management, course = _assignment_submission_manage_allowed(request, assignment)
        serializer = AssignmentSubmissionSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        filters = serializer.validated_data
        profile = current_profile(token=auth_token(request))
        if profile.get("profile_type") == "student":
            management = False
        if not management:
            require_scoped_permission(
                request,
                "submission.view",
                course_id=assignment.assessment.course_id,
                institution_id=course["institution_id"],
            )
            if profile.get("profile_type") != "student":
                from rest_framework.exceptions import PermissionDenied

                raise PermissionDenied(
                    "Submission list requires a student profile or manager access."
                )
            filters["student_profile_id"] = profile["id"]
            if not has_enrollment_access(
                token=auth_token(request),
                student_profile_id=profile["id"],
                course_id=assignment.assessment.course_id,
            ):
                from rest_framework.exceptions import PermissionDenied

                raise PermissionDenied("Student does not have active access to this course.")
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(
            search_assignment_submissions(assignment, filters),
            request,
            view=self,
        )
        return paginator.get_paginated_response(
            AssignmentSubmissionSerializer(page, many=True).data
        )

    def post(self, request, assignment_id):
        from .models import Assignment

        assignment = get_object_or_404(
            Assignment.objects.select_related("assessment"), id=assignment_id
        )
        _require_submission_scope(request, "submission.manage", assignment)
        profile = current_profile(token=auth_token(request))
        if profile.get("profile_type") != "student":
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Assignment submission requires a student profile.")
        if not has_enrollment_access(
            token=auth_token(request),
            student_profile_id=profile["id"],
            course_id=assignment.assessment.course_id,
        ):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Student does not have active access to this course.")
        serializer = AssignmentSubmissionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        submission = save_assignment_submission(
            assignment=assignment,
            token=auth_token(request),
            profile=profile,
            validated_data=serializer.validated_data,
            submit=serializer.validated_data.get("submit", False),
            correlation_id=_correlation_id(request),
        )
        return Response(
            AssignmentSubmissionSerializer(submission).data, status=status.HTTP_201_CREATED
        )


class AssignmentSubmissionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, submission_id):
        submission = get_object_or_404(assignment_submission_queryset(), id=submission_id)
        management, course = _assignment_submission_manage_allowed(request, submission.assignment)
        profile = current_profile(token=auth_token(request))
        if profile.get("profile_type") == "student":
            management = False
        if not management:
            require_scoped_permission(
                request,
                "submission.view",
                course_id=submission.assignment.assessment.course_id,
                institution_id=course["institution_id"],
            )
            if str(profile.get("id")) != str(submission.student_profile_id):
                from rest_framework.exceptions import PermissionDenied

                raise PermissionDenied("Submission belongs to another profile.")
        return Response(AssignmentSubmissionSerializer(submission).data)

    def patch(self, request, submission_id):
        submission = get_object_or_404(assignment_submission_queryset(), id=submission_id)
        _require_submission_scope(request, "submission.manage", submission.assignment)
        profile = current_profile(token=auth_token(request))
        serializer = AssignmentSubmissionUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        submission = update_assignment_submission(
            submission=submission,
            token=auth_token(request),
            profile=profile,
            validated_data=serializer.validated_data,
        )
        return Response(AssignmentSubmissionSerializer(submission).data)


class AssignmentSubmissionSubmitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, submission_id):
        submission = get_object_or_404(assignment_submission_queryset(), id=submission_id)
        _require_submission_scope(request, "submission.manage", submission.assignment)
        profile = current_profile(token=auth_token(request))
        if str(profile.get("id")) != str(submission.student_profile_id):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Submission belongs to another profile.")
        submission = submit_assignment_submission(
            submission=submission,
            actor_profile_id=profile["id"],
            correlation_id=_correlation_id(request),
        )
        return Response(AssignmentSubmissionSerializer(submission).data)


class AssignmentSubmissionMarkGradedView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, submission_id):
        submission = get_object_or_404(assignment_submission_queryset(), id=submission_id)
        course = _course_context_for_request(request, submission.assignment.assessment.course_id)
        require_scoped_permission(
            request,
            "grade.manage",
            course_id=submission.assignment.assessment.course_id,
            institution_id=course["institution_id"],
            message="You do not have permission to grade this submission.",
        )
        serializer = AssignmentSubmissionMarkGradedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = current_profile(token=auth_token(request))
        submission = mark_assignment_submission_graded(
            submission=submission,
            actor_profile_id=profile.get("id"),
            grade_record_id=serializer.validated_data.get("grade_record_id"),
        )
        return Response(AssignmentSubmissionSerializer(submission).data)


class QuizAttemptGradingSourceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, attempt_id):
        from .services import quiz_attempt_grading_source

        attempt = get_object_or_404(quiz_attempt_queryset(), id=attempt_id)
        course = _course_context_for_request(request, attempt.quiz.assessment.course_id)
        require_scoped_permission(
            request,
            "grade.manage",
            course_id=attempt.quiz.assessment.course_id,
            institution_id=course["institution_id"],
            message="You do not have permission to grade this attempt.",
        )
        return Response(
            QuizAttemptGradingSourceSerializer(quiz_attempt_grading_source(attempt)).data
        )


class AssignmentSubmissionGradingSourceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, submission_id):
        submission = get_object_or_404(assignment_submission_queryset(), id=submission_id)
        course = _course_context_for_request(request, submission.assignment.assessment.course_id)
        require_scoped_permission(
            request,
            "grade.manage",
            course_id=submission.assignment.assessment.course_id,
            institution_id=course["institution_id"],
            message="You do not have permission to grade this submission.",
        )
        return Response(
            AssignmentSubmissionGradingSourceSerializer(
                assignment_submission_grading_source(submission)
            ).data
        )
