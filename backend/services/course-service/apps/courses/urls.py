from django.urls import path

from .views import (
    CategoryDetailView,
    CategoryListCreateView,
    CourseArchiveView,
    CourseDetailView,
    CourseListCreateView,
    CoursePublishView,
    TagDetailView,
    TagListCreateView,
)


urlpatterns = [
    path("", CourseListCreateView.as_view(), name="course-list-create"),
    path("<uuid:course_id>/", CourseDetailView.as_view(), name="course-detail"),
    path("<uuid:course_id>/publish/", CoursePublishView.as_view(), name="course-publish"),
    path("<uuid:course_id>/archive/", CourseArchiveView.as_view(), name="course-archive"),
    path("categories/", CategoryListCreateView.as_view(), name="course-category-list-create"),
    path("categories/<uuid:category_id>/", CategoryDetailView.as_view(), name="course-category-detail"),
    path("tags/", TagListCreateView.as_view(), name="course-tag-list-create"),
    path("tags/<uuid:tag_id>/", TagDetailView.as_view(), name="course-tag-detail"),
]
