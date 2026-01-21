"""Authentication endpoint smoke tests."""
import pytest
from unittest.mock import patch


class TestAuthSmoke:
    """Basic authentication flow smoke tests."""

    def test_register_endpoint_exists(self, client):
        """Test that registration endpoint exists and accepts POST."""
        # Send minimal data - we expect validation error, not 404
        response = client.post("/api/auth/register", json={})
        assert response.status_code != 404
        # Should be 422 (validation error) or 400 (bad request)
        assert response.status_code in [400, 422]

    def test_login_endpoint_exists(self, client):
        """Test that login endpoint exists and accepts POST."""
        response = client.post("/api/auth/login", json={})
        assert response.status_code != 404
        assert response.status_code in [400, 401, 422]

    def test_logout_endpoint_exists(self, client):
        """Test that logout endpoint exists."""
        response = client.post("/api/auth/logout")
        # Without auth, should return 401 or similar
        assert response.status_code in [200, 401, 403]

    def test_me_endpoint_requires_auth(self, client):
        """Test that /users/me requires authentication."""
        response = client.get("/api/users/me")
        assert response.status_code == 401

    def test_admin_login_exists(self, client, test_admin_password):
        """Test that admin login endpoint exists."""
        response = client.post(
            "/api/auth/admin-login",
            json={"password": "wrong-password"}
        )
        # Endpoint contract:
        # - 401/403 when configured but password invalid
        # - 503 when admin password auth is not configured (ADMIN_PASSWORD missing)
        assert response.status_code in [401, 403, 503]


class TestAuthRegistration:
    """User registration tests."""

    def test_register_missing_fields(self, client):
        """Test registration fails with missing fields."""
        response = client.post("/api/auth/register", json={
            "username": "test"
            # Missing password
        })
        assert response.status_code == 422

    def test_register_invalid_email(self, client):
        """Test registration fails with invalid email."""
        response = client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "not-an-email",
            "password": "ValidPassword123!"
        })
        # Should fail email validation
        assert response.status_code in [400, 422]


class TestAuthLogin:
    """User login tests."""

    def test_login_wrong_credentials(self, client):
        """Test login fails with wrong credentials."""
        response = client.post("/api/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code in [401, 404]

    def test_login_missing_password(self, client):
        """Test login fails without password."""
        response = client.post("/api/auth/login", json={
            "email": "testuser@example.com"
        })
        assert response.status_code == 422
