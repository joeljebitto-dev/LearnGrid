from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import require_progress_permission
from .selectors import course_progress_queryset, progress_event_queryset
from .serializers import (
    AssessmentProgressSerializer,
    AssessmentProgressUpdateSerializer,
    CourseProgressSearchSerializer,
    CourseProgressSerializer,
    LessonProgressSerializer,
    LessonProgressUpdateSerializer,
    ProgressEventIngestSerializer,
    ProgressEventSerializer,
    VideoProgressSerializer,
    VideoProgressUpdateSerializer,
)
from .services import (
    process_progress_event,
    update_assessment_progress,
    update_lesson_progress,
    update_video_progress,
)


class LessonProgressUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LessonProgressUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        require_progress_permission(
            request, "progress.manage", serializer.validated_data["course_id"]
        )
        progress = update_lesson_progress(validated_data=serializer.validated_data)
        return Response(LessonProgressSerializer(progress).data, status=status.HTTP_200_OK)


class VideoProgressUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = VideoProgressUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        require_progress_permission(
            request, "progress.manage", serializer.validated_data["course_id"]
        )
        progress = update_video_progress(validated_data=serializer.validated_data)
        return Response(VideoProgressSerializer(progress).data, status=status.HTTP_200_OK)


class AssessmentProgressUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AssessmentProgressUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        require_progress_permission(
            request, "progress.manage", serializer.validated_data["course_id"]
        )
        progress = update_assessment_progress(validated_data=serializer.validated_data)
        return Response(AssessmentProgressSerializer(progress).data, status=status.HTTP_200_OK)


class CourseProgressListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = CourseProgressSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        course_id = serializer.validated_data.get("course_id")
        require_progress_permission(request, "progress.view", course_id)
        queryset = course_progress_queryset()
        for field in ["student_profile_id", "course_id", "status"]:
            if value := serializer.validated_data.get(field):
                queryset = queryset.filter(**{field: value})
        return Response(
            CourseProgressSerializer(queryset.order_by("-updated_at", "id"), many=True).data
        )


class CourseProgressDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, progress_id):
        progress = get_object_or_404(course_progress_queryset(), id=progress_id)
        require_progress_permission(request, "progress.view", progress.course_id)
        return Response(CourseProgressSerializer(progress).data)


class ProgressEventIngestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ProgressEventIngestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data["payload"]
        require_progress_permission(request, "progress.manage", payload.get("course_id"))
        result = process_progress_event(**serializer.validated_data)
        return Response(result, status=status.HTTP_200_OK)

    def get(self, request):
        require_progress_permission(request, "progress.view")
        return Response(ProgressEventSerializer(progress_event_queryset(), many=True).data)
