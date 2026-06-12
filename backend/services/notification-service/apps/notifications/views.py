from __future__ import annotations

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import has_notification_permission, require_notification_permission
from .selectors import (
    delivery_attempt_queryset,
    notification_queryset,
    notification_template_queryset,
    search_delivery_attempts,
    search_notification_templates,
    search_notifications,
    search_user_notification_preferences,
)
from .serializers import (
    DeliveryAttemptSearchSerializer,
    DeliveryAttemptSerializer,
    NotificationEventIngestSerializer,
    NotificationSearchSerializer,
    NotificationSerializer,
    NotificationTemplateCreateSerializer,
    NotificationTemplateSearchSerializer,
    NotificationTemplateSerializer,
    NotificationTemplateUpdateSerializer,
    UserNotificationPreferenceSearchSerializer,
    UserNotificationPreferenceSerializer,
    UserNotificationPreferenceUpsertSerializer,
)
from .services import (
    auth_token,
    create_notification_template,
    current_profile,
    ingest_notification_event,
    mark_all_notifications_read,
    mark_notification_read,
    mark_notification_unread,
    update_notification_template,
    upsert_user_notification_preference,
)


class NotificationPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


def _current_profile(request) -> dict:
    return current_profile(token=auth_token(request))


def _can_manage_notifications(request) -> bool:
    return has_notification_permission(request, "notification.manage")


def _can_view_notifications(request) -> bool:
    return has_notification_permission(request, "notification.view")


def _require_owner_or_view(request, recipient_profile_id) -> None:
    profile = _current_profile(request)
    if str(profile.get("id")) == str(recipient_profile_id):
        return
    if not _can_view_notifications(request):
        raise PermissionDenied("Notification belongs to another profile.")


class NotificationTemplateListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = NotificationPagination

    def get(self, request):
        require_notification_permission(request, "notification.view")
        serializer = NotificationTemplateSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(
            search_notification_templates(serializer.validated_data),
            request,
            view=self,
        )
        return paginator.get_paginated_response(
            NotificationTemplateSerializer(page, many=True).data
        )

    def post(self, request):
        require_notification_permission(request, "notification.manage")
        serializer = NotificationTemplateCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        template = create_notification_template(validated_data=serializer.validated_data)
        return Response(
            NotificationTemplateSerializer(template).data, status=status.HTTP_201_CREATED
        )


class NotificationTemplateDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, template_id):
        require_notification_permission(request, "notification.view")
        template = get_object_or_404(notification_template_queryset(), id=template_id)
        return Response(NotificationTemplateSerializer(template).data)

    def patch(self, request, template_id):
        require_notification_permission(request, "notification.manage")
        template = get_object_or_404(notification_template_queryset(), id=template_id)
        serializer = NotificationTemplateUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        template = update_notification_template(
            template=template, validated_data=serializer.validated_data
        )
        return Response(NotificationTemplateSerializer(template).data)


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = NotificationPagination

    def get(self, request):
        serializer = NotificationSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        filters = serializer.validated_data
        profile = _current_profile(request)
        if filters.get("recipient_profile_id"):
            _require_owner_or_view(request, filters["recipient_profile_id"])
        elif not _can_view_notifications(request):
            filters["recipient_profile_id"] = profile.get("id")
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(
            search_notifications(filters),
            request,
            view=self,
        )
        return paginator.get_paginated_response(NotificationSerializer(page, many=True).data)


class NotificationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, notification_id):
        notification = get_object_or_404(
            notification_queryset(), id=notification_id, deleted_at__isnull=True
        )
        _require_owner_or_view(request, notification.recipient_profile_id)
        return Response(NotificationSerializer(notification).data)


class NotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, notification_id):
        notification = get_object_or_404(
            notification_queryset(), id=notification_id, deleted_at__isnull=True
        )
        _require_owner_or_view(request, notification.recipient_profile_id)
        notification = mark_notification_read(notification=notification)
        return Response(NotificationSerializer(notification).data)


class NotificationUnreadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, notification_id):
        notification = get_object_or_404(
            notification_queryset(), id=notification_id, deleted_at__isnull=True
        )
        _require_owner_or_view(request, notification.recipient_profile_id)
        notification = mark_notification_unread(notification=notification)
        return Response(NotificationSerializer(notification).data)


class NotificationReadAllView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile = _current_profile(request)
        updated_count = mark_all_notifications_read(recipient_profile_id=profile["id"])
        return Response({"updated_count": updated_count})


class NotificationPreferenceListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = NotificationPagination

    def get(self, request):
        serializer = UserNotificationPreferenceSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        filters = serializer.validated_data
        profile = _current_profile(request)
        if filters.get("profile_id"):
            if str(filters["profile_id"]) != str(
                profile.get("id")
            ) and not _can_manage_notifications(request):
                raise PermissionDenied("Preference belongs to another profile.")
        else:
            filters["profile_id"] = profile.get("id")
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(
            search_user_notification_preferences(filters),
            request,
            view=self,
        )
        return paginator.get_paginated_response(
            UserNotificationPreferenceSerializer(page, many=True).data
        )

    def post(self, request):
        serializer = UserNotificationPreferenceUpsertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = _current_profile(request)
        data = dict(serializer.validated_data)
        if data.get("profile_id"):
            if str(data["profile_id"]) != str(profile.get("id")) and not _can_manage_notifications(
                request
            ):
                raise PermissionDenied("Preference belongs to another profile.")
        else:
            data["profile_id"] = profile.get("id")
        preference = upsert_user_notification_preference(validated_data=data)
        return Response(
            UserNotificationPreferenceSerializer(preference).data, status=status.HTTP_200_OK
        )


class DeliveryAttemptListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = NotificationPagination

    def get(self, request):
        require_notification_permission(request, "notification.view")
        serializer = DeliveryAttemptSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(
            search_delivery_attempts(serializer.validated_data),
            request,
            view=self,
        )
        return paginator.get_paginated_response(DeliveryAttemptSerializer(page, many=True).data)


class DeliveryAttemptDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, attempt_id):
        require_notification_permission(request, "notification.view")
        attempt = get_object_or_404(delivery_attempt_queryset(), id=attempt_id)
        return Response(DeliveryAttemptSerializer(attempt).data)


class NotificationEventIngestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        require_notification_permission(request, "notification.manage")
        serializer = NotificationEventIngestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = ingest_notification_event(event=serializer.validated_data)
        return Response(
            {
                "status": result["status"],
                "notifications": NotificationSerializer(result["notifications"], many=True).data,
                "skipped_count": result["skipped_count"],
                "duplicate_count": result["duplicate_count"],
            },
            status=status.HTTP_200_OK,
        )
