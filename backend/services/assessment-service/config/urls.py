from django.conf import settings
from django.urls import include, path
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def health(_request):
    return Response({"service": settings.SERVICE_NAME, "status": "ok"})


urlpatterns = [
    path("health/", health, name="health"),
    path("api/assessments/", include("apps.assessments.urls")),
]
