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
    course_structure_queryset,
    lesson_queryset,
    module_queryset,
    revision_queryset,
    search_categories,
    search_courses,
    search_tags,
    tag_queryset,
    topic_queryset,
)
from .serializers import (
    CategoryCreateSerializer,
    CategoryTagSearchSerializer,
    CategoryUpdateSerializer,
    CourseCategorySerializer,
    CourseCreateSerializer,
    CourseModuleSerializer,
    CourseRevisionCreateSerializer,
    CourseRevisionSerializer,
    CourseSearchSerializer,
    CourseSerializer,
    CourseStructureSerializer,
    CourseTagSerializer,
    CourseUpdateSerializer,
    LessonCreateSerializer,
    LessonReorderSerializer,
    LessonSerializer,
    LessonUpdateSerializer,
    ModuleCreateSerializer,
    ModuleReorderSerializer,
    ModuleUpdateSerializer,
    TagCreateSerializer,
    TagUpdateSerializer,
    TopicCreateSerializer,
    TopicReorderSerializer,
    TopicSerializer,
    TopicUpdateSerializer,
)
from .services import (
    archive_course,
    archive_lesson,
    archive_module,
    catalog_cache_key,
    create_category,
    create_course,
    create_course_revision,
    create_lesson,
    create_module,
    create_tag,
    create_topic,
    delete_category,
    delete_course,
    delete_tag,
    delete_topic,
    get_catalog_cache,
    publish_lesson,
    publish_course,
    reorder_lessons,
    reorder_modules,
    reorder_topics,
    set_catalog_cache,
    update_category,
    update_course,
    update_lesson,
    update_module,
    update_tag,
    update_topic,
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


def _require_structure_read(request, course) -> bool:
    management = has_course_permission(request, "course.manage", course.institution_id)
    if management:
        return True
    if course.status != CourseStatus.PUBLISHED or course.deleted_at is not None:
        require_course_permission(request, "course.manage", course.institution_id)
    require_course_permission(request, "course.view", course.institution_id)
    return False


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


class CourseStructureView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):
        base_course = get_object_or_404(course_queryset(include_deleted=True), id=course_id)
        management = _require_structure_read(request, base_course)
        if not management:
            cache_key = catalog_cache_key("course-structure", {"course_id": str(base_course.id)})
            cached = get_catalog_cache(cache_key)
            if cached is not None:
                return Response(cached)

        course = get_object_or_404(
            course_structure_queryset(management=management),
            id=course_id,
        )
        data = CourseStructureSerializer(course).data
        if not management:
            set_catalog_cache(cache_key, data)
        return Response(data)


class ModuleListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):
        course = get_object_or_404(course_queryset(include_deleted=True), id=course_id)
        management = _require_structure_read(request, course)
        queryset = module_queryset().filter(course=course)
        if not management:
            queryset = queryset.filter(status="published")
        return Response(CourseModuleSerializer(queryset.order_by("position", "id"), many=True).data)

    def post(self, request, course_id):
        course = get_object_or_404(course_queryset(), id=course_id)
        require_course_permission(request, "course.manage", course.institution_id)
        serializer = ModuleCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        module = create_module(course=course, validated_data=serializer.validated_data)
        return Response(CourseModuleSerializer(module).data, status=status.HTTP_201_CREATED)


class ModuleDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, module_id):
        module = get_object_or_404(module_queryset(), id=module_id)
        management = _require_structure_read(request, module.course)
        if not management and module.status != "published":
            require_course_permission(request, "course.manage", module.course.institution_id)
        return Response(CourseModuleSerializer(module).data)

    def patch(self, request, module_id):
        module = get_object_or_404(module_queryset(), id=module_id)
        require_course_permission(request, "course.manage", module.course.institution_id)
        serializer = ModuleUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        module = update_module(module=module, validated_data=serializer.validated_data)
        return Response(CourseModuleSerializer(module).data)

    def delete(self, request, module_id):
        module = get_object_or_404(module_queryset(), id=module_id)
        require_course_permission(request, "course.manage", module.course.institution_id)
        module = archive_module(module=module)
        return Response(CourseModuleSerializer(module).data)


class ModuleReorderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, course_id):
        course = get_object_or_404(course_queryset(), id=course_id)
        require_course_permission(request, "course.manage", course.institution_id)
        serializer = ModuleReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        modules = reorder_modules(course=course, module_ids=serializer.validated_data["module_ids"])
        return Response(CourseModuleSerializer(modules, many=True).data)


class LessonListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, module_id):
        module = get_object_or_404(module_queryset(), id=module_id)
        management = _require_structure_read(request, module.course)
        queryset = lesson_queryset().filter(module=module)
        if not management:
            if module.status != "published":
                require_course_permission(request, "course.manage", module.course.institution_id)
            queryset = queryset.filter(status="published")
        return Response(LessonSerializer(queryset.order_by("position", "id"), many=True).data)

    def post(self, request, module_id):
        module = get_object_or_404(module_queryset(), id=module_id)
        require_course_permission(request, "course.manage", module.course.institution_id)
        serializer = LessonCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lesson = create_lesson(module=module, validated_data=serializer.validated_data)
        return Response(LessonSerializer(lesson).data, status=status.HTTP_201_CREATED)


class LessonDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, lesson_id):
        lesson = get_object_or_404(lesson_queryset(), id=lesson_id)
        management = _require_structure_read(request, lesson.course)
        if not management and (lesson.status != "published" or lesson.module.status != "published"):
            require_course_permission(request, "course.manage", lesson.course.institution_id)
        return Response(LessonSerializer(lesson).data)

    def patch(self, request, lesson_id):
        lesson = get_object_or_404(lesson_queryset(), id=lesson_id)
        require_course_permission(request, "course.manage", lesson.course.institution_id)
        serializer = LessonUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        lesson = update_lesson(lesson=lesson, validated_data=serializer.validated_data)
        return Response(LessonSerializer(lesson).data)

    def delete(self, request, lesson_id):
        lesson = get_object_or_404(lesson_queryset(), id=lesson_id)
        require_course_permission(request, "course.manage", lesson.course.institution_id)
        lesson = archive_lesson(lesson=lesson)
        return Response(LessonSerializer(lesson).data)


class LessonPublishView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, lesson_id):
        lesson = get_object_or_404(lesson_queryset(), id=lesson_id)
        require_course_permission(request, "course.manage", lesson.course.institution_id)
        lesson = publish_lesson(lesson=lesson, correlation_id=_correlation_id(request))
        return Response(LessonSerializer(lesson).data)


class LessonReorderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, module_id):
        module = get_object_or_404(module_queryset(), id=module_id)
        require_course_permission(request, "course.manage", module.course.institution_id)
        serializer = LessonReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lessons = reorder_lessons(module=module, lesson_ids=serializer.validated_data["lesson_ids"])
        return Response(LessonSerializer(lessons, many=True).data)


class TopicListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, lesson_id):
        lesson = get_object_or_404(lesson_queryset(), id=lesson_id)
        management = _require_structure_read(request, lesson.course)
        if not management and (lesson.status != "published" or lesson.module.status != "published"):
            require_course_permission(request, "course.manage", lesson.course.institution_id)
        topics = topic_queryset().filter(lesson=lesson).order_by("position", "id")
        return Response(TopicSerializer(topics, many=True).data)

    def post(self, request, lesson_id):
        lesson = get_object_or_404(lesson_queryset(), id=lesson_id)
        require_course_permission(request, "course.manage", lesson.course.institution_id)
        serializer = TopicCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        topic = create_topic(lesson=lesson, validated_data=serializer.validated_data)
        return Response(TopicSerializer(topic).data, status=status.HTTP_201_CREATED)


class TopicDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, topic_id):
        topic = get_object_or_404(topic_queryset(), id=topic_id)
        management = _require_structure_read(request, topic.lesson.course)
        if not management and (
            topic.lesson.status != "published" or topic.lesson.module.status != "published"
        ):
            require_course_permission(request, "course.manage", topic.lesson.course.institution_id)
        return Response(TopicSerializer(topic).data)

    def patch(self, request, topic_id):
        topic = get_object_or_404(topic_queryset(), id=topic_id)
        require_course_permission(request, "course.manage", topic.lesson.course.institution_id)
        serializer = TopicUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        topic = update_topic(topic=topic, validated_data=serializer.validated_data)
        return Response(TopicSerializer(topic).data)

    def delete(self, request, topic_id):
        topic = get_object_or_404(topic_queryset(), id=topic_id)
        require_course_permission(request, "course.manage", topic.lesson.course.institution_id)
        delete_topic(topic=topic)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TopicReorderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, lesson_id):
        lesson = get_object_or_404(lesson_queryset(), id=lesson_id)
        require_course_permission(request, "course.manage", lesson.course.institution_id)
        serializer = TopicReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        topics = reorder_topics(lesson=lesson, topic_ids=serializer.validated_data["topic_ids"])
        return Response(TopicSerializer(topics, many=True).data)


class CourseRevisionListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):
        course = get_object_or_404(course_queryset(include_deleted=True), id=course_id)
        require_course_permission(request, "course.manage", course.institution_id)
        revisions = revision_queryset().filter(course=course).order_by("-version_number", "id")
        return Response(CourseRevisionSerializer(revisions, many=True).data)

    def post(self, request, course_id):
        course = get_object_or_404(course_queryset(), id=course_id)
        require_course_permission(request, "course.manage", course.institution_id)
        serializer = CourseRevisionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        revision = create_course_revision(
            course=course,
            created_by_profile_id=serializer.validated_data.get("created_by_profile_id")
            or request.user.id,
        )
        return Response(CourseRevisionSerializer(revision).data, status=status.HTTP_201_CREATED)


class CourseRevisionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, revision_id):
        revision = get_object_or_404(revision_queryset(), id=revision_id)
        require_course_permission(request, "course.manage", revision.course.institution_id)
        return Response(CourseRevisionSerializer(revision).data)


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
