from django.urls import path

from .views import (
    AssessmentProgressUpdateView,
    CourseProgressDetailView,
    CourseProgressListView,
    LessonProgressUpdateView,
    ProgressEventIngestView,
    VideoProgressUpdateView,
)


urlpatterns = [
    path("lessons/", LessonProgressUpdateView.as_view(), name="lesson-progress-update"),
    path("videos/", VideoProgressUpdateView.as_view(), name="video-progress-update"),
    path("assessments/", AssessmentProgressUpdateView.as_view(), name="assessment-progress-update"),
    path("courses/", CourseProgressListView.as_view(), name="course-progress-list"),
    path("courses/<uuid:progress_id>/", CourseProgressDetailView.as_view(), name="course-progress-detail"),
    path("events/", ProgressEventIngestView.as_view(), name="progress-event-ingest"),
]
