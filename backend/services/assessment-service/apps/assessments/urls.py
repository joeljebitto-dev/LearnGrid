from django.urls import path

from .views import (
    AssessmentCloseView,
    AssessmentDetailView,
    AssessmentListCreateView,
    AssessmentPublishView,
    AssessmentQuestionReplaceView,
    QuestionBankDetailView,
    QuestionBankListCreateView,
    QuestionDetailView,
    QuestionListCreateView,
    QuizAttemptAnswersView,
    QuizAttemptAutoSubmitView,
    QuizAttemptDetailView,
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
