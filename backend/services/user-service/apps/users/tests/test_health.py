def test_health_endpoint(client):
    response = client.get("/health/")

    assert response.status_code == 200
    assert response.json() == {"service": "user-service", "status": "ok"}
