from __future__ import annotations

from django.conf import settings
from django.db import connections
from django.db.utils import DatabaseError, OperationalError
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def health(_request):
    return Response({"service": settings.SERVICE_NAME, "status": "ok"})


@api_view(["GET"])
def liveness(_request):
    return Response({"service": settings.SERVICE_NAME, "status": "live"})


@api_view(["GET"])
def readiness(_request):
    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1")
    except (DatabaseError, OperationalError):
        return Response(
            {"service": settings.SERVICE_NAME, "status": "unready", "database": "unavailable"},
            status=503,
        )
    return Response({"service": settings.SERVICE_NAME, "status": "ready", "database": "ok"})
