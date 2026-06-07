from __future__ import annotations

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CourseStatus
from .permissions import has_course_permission, require_course_permission
from .selectors import (
    category_queryset,
    course_queryset,
    search_categories,
    search_courses,
    search_tags,
    tag_queryset,
)
from .serializers import (
    CategoryCreateSerializer,
    CategoryTagSearchSerializer,
    CategoryUpdateSerializer,
    CourseCategorySerializer,
    CourseCreateSerializer,
    CourseSearchSerializer,
    CourseSerializer,
    CourseTagSerializer,
    CourseUpdateSerializer,
    TagCreateSerializer,
    TagUpdateSerializer,
)
from .services import (
    archive_course,
    catalog_cache_key,
    create_category,
    create_course,
    create_tag,
    delete_category,
    delete_course,
    delete_tag,
    get_catalog_cache,
    publish_course,
    set_catalog_cache,
    update_category,
    update_course,
    update_tag,
)


class CoursePagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


def _require_course_read(request, institution_id) -> bool:
    management = has_course_permission(request, "course.manage", institution_id)
    if management:
        return True
    require_course_permission(request, "course.view", institution_id)
    return False


def _require_category_tag_read(request, institution_id) -> None:
    if has_course_permission(request, "course.manage", institution_id):
        return
    require_course_permission(request, "course.view", institution_id)


def _correlation_id(request) -> str | None:
    return request.headers.get("X-Correlation-ID")


class CourseListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CoursePagination

    def get(self, request):
        serializer = CourseSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        filters = serializer.validated_data
        institution_id = filters.get("institution_id")
        management = _require_course_read(request, institution_id)

        if not management:
            cache_key = catalog_cache_key("course-list", dict(request.query_params.lists()))
            cached = get_catalog_cache(cache_key)
            if cached is not None:
                return Response(cached)

        queryset = search_courses(filters, management=management)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        response = paginator.get_paginated_response(CourseSerializer(page, many=True).data)

        if not management:
            set_catalog_cache(cache_key, response.data)
        return response

    def post(self, request):
        serializer = CourseCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        require_course_permission(request, "course.manage", serializer.validated_data["institution_id"])
        course = create_course(
            validated_data=serializer.validated_data,
            correlation_id=_correlation_id(request),
        )
        return Response(CourseSerializer(course).data, status=status.HTTP_201_CREATED)


class CourseDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):
        course = get_object_or_404(course_queryset(include_deleted=True), id=course_id)
        management = has_course_permission(request, "course.manage", course.institution_id)
        if course.status == CourseStatus.PUBLISHED and course.deleted_at is None:
            if not management:
                require_course_permission(request, "course.view", course.institution_id)
                cache_key = catalog_cache_key("course-detail", {"course_id": str(course.id)})
                cached = get_catalog_cache(cache_key)
                if cached is not None:
                    return Response(cached)
                data = CourseSerializer(course).data
                set_catalog_cache(cache_key, data)
                return Response(data)
        elif not management:
            require_course_permission(request, "course.manage", course.institution_id)
        return Response(CourseSerializer(course).data)

    def patch(self, request, course_id):
        course = get_object_or_404(course_queryset(), id=course_id)
        serializer = CourseUpdateSerializer(
            data=request.data,
            partial=True,
            context={"course": course},
        )
        serializer.is_valid(raise_exception=True)
        require_course_permission(request, "course.manage", course.institution_id)
        if "institution_id" in serializer.validated_data:
            require_course_permission(request, "course.manage", serializer.validated_data["institution_id"])
        course = update_course(course=course, validated_data=serializer.validated_data)
        return Response(CourseSerializer(course).data)

    def delete(self, request, course_id):
        course = get_object_or_404(course_queryset(), id=course_id)
        require_course_permission(request, "course.manage", course.institution_id)
        course = delete_course(course=course)
        return Response(CourseSerializer(course).data)


class CoursePublishView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, course_id):
        course = get_object_or_404(course_queryset(), id=course_id)
        require_course_permission(request, "course.manage", course.institution_id)
        course = publish_course(course=course, correlation_id=_correlation_id(request))
        return Response(CourseSerializer(course).data)


class CourseArchiveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, course_id):
        course = get_object_or_404(course_queryset(), id=course_id)
        require_course_permission(request, "course.manage", course.institution_id)
        course = archive_course(course=course, correlation_id=_correlation_id(request))
        return Response(CourseSerializer(course).data)


class CategoryListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CoursePagination

    def get(self, request):
        serializer = CategoryTagSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        _require_category_tag_read(request, serializer.validated_data.get("institution_id"))
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(
            search_categories(serializer.validated_data),
            request,
            view=self,
        )
        return paginator.get_paginated_response(CourseCategorySerializer(page, many=True).data)

    def post(self, request):
        serializer = CategoryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        require_course_permission(request, "course.manage", serializer.validated_data.get("institution_id"))
        category = create_category(validated_data=serializer.validated_data)
        return Response(CourseCategorySerializer(category).data, status=status.HTTP_201_CREATED)


class CategoryDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, category_id):
        category = get_object_or_404(category_queryset(), id=category_id)
        _require_category_tag_read(request, category.institution_id)
        return Response(CourseCategorySerializer(category).data)

    def patch(self, request, category_id):
        category = get_object_or_404(category_queryset(), id=category_id)
        require_course_permission(request, "course.manage", category.institution_id)
        serializer = CategoryUpdateSerializer(
            data=request.data,
            partial=True,
            context={"category": category},
        )
        serializer.is_valid(raise_exception=True)
        category = update_category(category=category, validated_data=serializer.validated_data)
        return Response(CourseCategorySerializer(category).data)

    def delete(self, request, category_id):
        category = get_object_or_404(category_queryset(), id=category_id)
        require_course_permission(request, "course.manage", category.institution_id)
        delete_category(category=category)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CoursePagination

    def get(self, request):
        serializer = CategoryTagSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        _require_category_tag_read(request, serializer.validated_data.get("institution_id"))
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(search_tags(serializer.validated_data), request, view=self)
        return paginator.get_paginated_response(CourseTagSerializer(page, many=True).data)

    def post(self, request):
        serializer = TagCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        require_course_permission(request, "course.manage", serializer.validated_data.get("institution_id"))
        tag = create_tag(validated_data=serializer.validated_data)
        return Response(CourseTagSerializer(tag).data, status=status.HTTP_201_CREATED)


class TagDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, tag_id):
        tag = get_object_or_404(tag_queryset(), id=tag_id)
        _require_category_tag_read(request, tag.institution_id)
        return Response(CourseTagSerializer(tag).data)

    def patch(self, request, tag_id):
        tag = get_object_or_404(tag_queryset(), id=tag_id)
        require_course_permission(request, "course.manage", tag.institution_id)
        serializer = TagUpdateSerializer(data=request.data, partial=True, context={"tag": tag})
        serializer.is_valid(raise_exception=True)
        tag = update_tag(tag=tag, validated_data=serializer.validated_data)
        return Response(CourseTagSerializer(tag).data)

    def delete(self, request, tag_id):
        tag = get_object_or_404(tag_queryset(), id=tag_id)
        require_course_permission(request, "course.manage", tag.institution_id)
        delete_tag(tag=tag)
        return Response(status=status.HTTP_204_NO_CONTENT)
