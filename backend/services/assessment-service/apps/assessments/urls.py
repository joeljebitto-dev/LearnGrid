from django.urls import path

from .views import (
    AssessmentCloseView,
    AssessmentDetailView,
    AssessmentListCreateView,
    AssessmentPublishView,
    AssessmentQuestionReplaceView,
    AssignmentSubmissionDetailView,
    AssignmentSubmissionGradingSourceView,
    AssignmentSubmissionListCreateView,
    AssignmentSubmissionMarkGradedView,
    AssignmentSubmissionSubmitView,
    QuestionBankDetailView,
    QuestionBankListCreateView,
    QuestionDetailView,
    QuestionListCreateView,
    QuizAttemptAnswersView,
    QuizAttemptAutoSubmitView,
    QuizAttemptDetailView,
    QuizAttemptGradingSourceView,
    QuizAttemptStartView,
    QuizAttemptSubmitView,
)


urlpatterns = [
    path("question-banks/", QuestionBankListCreateView.as_view(), name="question-bank-list-create"),
    path("question-banks/<uuid:question_bank_id>/", QuestionBankDetailView.as_view(), name="question-bank-detail"),
    path(
        "question-banks/<uuid:question_bank_id>/questions/",
        QuestionListCreateView.as_view(),
        name="question-list-create",
    ),
    path("questions/<uuid:question_id>/", QuestionDetailView.as_view(), name="question-detail"),
    path(
        "assignments/<uuid:assignment_id>/submissions/",
        AssignmentSubmissionListCreateView.as_view(),
        name="assignment-submission-list-create",
    ),
    path("submissions/<uuid:submission_id>/", AssignmentSubmissionDetailView.as_view(), name="assignment-submission-detail"),
    path(
        "submissions/<uuid:submission_id>/submit/",
        AssignmentSubmissionSubmitView.as_view(),
        name="assignment-submission-submit",
    ),
    path(
        "submissions/<uuid:submission_id>/mark-graded/",
        AssignmentSubmissionMarkGradedView.as_view(),
        name="assignment-submission-mark-graded",
    ),
    path(
        "grading/quiz-attempts/<uuid:attempt_id>/",
        QuizAttemptGradingSourceView.as_view(),
        name="quiz-attempt-grading-source",
    ),
    path(
        "grading/assignment-submissions/<uuid:submission_id>/",
        AssignmentSubmissionGradingSourceView.as_view(),
        name="assignment-submission-grading-source",
    ),
    path("", AssessmentListCreateView.as_view(), name="assessment-list-create"),
    path("<uuid:assessment_id>/", AssessmentDetailView.as_view(), name="assessment-detail"),
    path("<uuid:assessment_id>/questions/", AssessmentQuestionReplaceView.as_view(), name="assessment-questions"),
    path("<uuid:assessment_id>/publish/", AssessmentPublishView.as_view(), name="assessment-publish"),
    path("<uuid:assessment_id>/close/", AssessmentCloseView.as_view(), name="assessment-close"),
    path("<uuid:assessment_id>/attempts/start/", QuizAttemptStartView.as_view(), name="quiz-attempt-start"),
    path("attempts/<uuid:attempt_id>/", QuizAttemptDetailView.as_view(), name="quiz-attempt-detail"),
    path("attempts/<uuid:attempt_id>/answers/", QuizAttemptAnswersView.as_view(), name="quiz-attempt-answers"),
    path("attempts/<uuid:attempt_id>/submit/", QuizAttemptSubmitView.as_view(), name="quiz-attempt-submit"),
    path(
        "attempts/<uuid:attempt_id>/auto-submit/",
        QuizAttemptAutoSubmitView.as_view(),
        name="quiz-attempt-auto-submit",
    ),
]
