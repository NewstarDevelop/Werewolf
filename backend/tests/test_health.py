"""Health check endpoint tests."""
import pytest


class TestHealthEndpoints:
    """Test health check and root endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns 200 and status ok."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "message" in data

    def test_health_endpoint(self, client):
        """Test /health endpoint returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_api_docs_available_in_debug(self, client):
        """Test that API docs are available in debug mode."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "swagger" in response.text.lower() or "openapi" in response.text.lower()

    def test_openapi_schema(self, client):
        """Test OpenAPI schema is accessible."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert data["info"]["title"] == "Werewolf AI Game API"
