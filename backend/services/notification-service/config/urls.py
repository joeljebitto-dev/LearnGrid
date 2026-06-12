from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from learngrid_observability.health import health, liveness, readiness


urlpatterns = [
    path("health/", health, name="health"),
    path("health/live/", liveness, name="health-live"),
    path("health/ready/", readiness, name="health-ready"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("", include("django_prometheus.urls")),
    path("api/notifications/", include("apps.notifications.urls")),
]
