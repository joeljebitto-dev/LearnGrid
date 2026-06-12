from django.urls import path

from .views import (
    DeliveryAttemptDetailView,
    DeliveryAttemptListView,
    NotificationDetailView,
    NotificationEventIngestView,
    NotificationListView,
    NotificationPreferenceListCreateView,
    NotificationReadAllView,
    NotificationReadView,
    NotificationTemplateDetailView,
    NotificationTemplateListCreateView,
    NotificationUnreadView,
)


urlpatterns = [
    path(
        "templates/",
        NotificationTemplateListCreateView.as_view(),
        name="notification-template-list-create",
    ),
    path(
        "templates/<uuid:template_id>/",
        NotificationTemplateDetailView.as_view(),
        name="notification-template-detail",
    ),
    path("", NotificationListView.as_view(), name="notification-list"),
    path("<uuid:notification_id>/", NotificationDetailView.as_view(), name="notification-detail"),
    path("<uuid:notification_id>/read/", NotificationReadView.as_view(), name="notification-read"),
    path(
        "<uuid:notification_id>/unread/",
        NotificationUnreadView.as_view(),
        name="notification-unread",
    ),
    path("read-all/", NotificationReadAllView.as_view(), name="notification-read-all"),
    path(
        "preferences/",
        NotificationPreferenceListCreateView.as_view(),
        name="notification-preference-list-create",
    ),
    path("delivery-attempts/", DeliveryAttemptListView.as_view(), name="delivery-attempt-list"),
    path(
        "delivery-attempts/<uuid:attempt_id>/",
        DeliveryAttemptDetailView.as_view(),
        name="delivery-attempt-detail",
    ),
    path("events/ingest/", NotificationEventIngestView.as_view(), name="notification-event-ingest"),
]
