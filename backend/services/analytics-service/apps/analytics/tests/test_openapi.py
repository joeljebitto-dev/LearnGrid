import json
from rest_framework.test import APIClient


def test_openapi_schema_endpoint_exposes_paths():
    response = APIClient().get("/api/schema/?format=json")

    assert response.status_code == 200
    schema = json.loads(response.content)
    assert schema["openapi"].startswith("3.")
    assert schema["info"]["title"].startswith("LearnGrid ")
    assert any(path.startswith("/api/") for path in schema["paths"])


def test_openapi_docs_endpoint_loads():
    response = APIClient().get("/api/docs/")

    assert response.status_code == 200
    assert b"swagger" in response.content.lower()
