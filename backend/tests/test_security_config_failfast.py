"""Tests for security configuration fail-fast - A4.

Verifies that:
1. Production mode fails startup on security configuration errors
2. Debug mode bypasses strict validation
"""
import pytest
from unittest.mock import patch


class TestSecurityConfigFailFast:
    """Test security configuration validation."""

    def test_production_rejects_weak_jwt_secret(self, monkeypatch):
        """In production, JWT_SECRET_KEY < 32 chars should be an error."""
        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("JWT_SECRET_KEY", "short_key")
        monkeypatch.setenv("CORS_ORIGINS", "https://example.com")

        import importlib
        from app.core import config
        importlib.reload(config)

        settings = config.Settings()
        warnings, errors = settings._validate_security_config()

        assert len(errors) > 0
        assert any("JWT_SECRET_KEY" in e and "32 characters" in e for e in errors)

    def test_production_rejects_wildcard_cors(self, monkeypatch):
        """In production, CORS_ORIGINS='*' should be an error."""
        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("JWT_SECRET_KEY", "a" * 32)  # Valid length
        monkeypatch.setenv("CORS_ORIGINS", "*")

        import importlib
        from app.core import config
        importlib.reload(config)

        settings = config.Settings()
        warnings, errors = settings._validate_security_config()

        assert len(errors) > 0
        assert any("CORS_ORIGINS='*'" in e for e in errors)

    def test_production_warns_missing_frontend_url(self, monkeypatch):
        """In production, missing FRONTEND_URL should be a warning."""
        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("JWT_SECRET_KEY", "a" * 32)
        monkeypatch.setenv("CORS_ORIGINS", "https://example.com")
        monkeypatch.delenv("FRONTEND_URL", raising=False)
        monkeypatch.delenv("ALLOWED_WS_ORIGINS", raising=False)

        import importlib
        from app.core import config
        importlib.reload(config)

        settings = config.Settings()
        warnings, errors = settings._validate_security_config()

        assert any("FRONTEND_URL" in w or "ALLOWED_WS_ORIGINS" in w for w in warnings)

    def test_debug_mode_skips_validation(self, monkeypatch):
        """In debug mode, strict validation should be skipped."""
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("JWT_SECRET_KEY", "short")  # Would fail in production
        monkeypatch.setenv("CORS_ORIGINS", "*")  # Would fail in production

        import importlib
        from app.core import config
        importlib.reload(config)

        settings = config.Settings()
        warnings, errors = settings._validate_security_config()

        # Both should be empty in debug mode
        assert len(warnings) == 0
        assert len(errors) == 0

    def test_valid_production_config_passes(self, monkeypatch):
        """Valid production configuration should pass."""
        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("JWT_SECRET_KEY", "a" * 32)
        monkeypatch.setenv("CORS_ORIGINS", "https://example.com")
        monkeypatch.setenv("FRONTEND_URL", "https://example.com")

        import importlib
        from app.core import config
        importlib.reload(config)

        settings = config.Settings()
        warnings, errors = settings._validate_security_config()

        assert len(errors) == 0

    def test_multiple_errors_reported(self, monkeypatch):
        """Multiple security issues should all be reported."""
        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("JWT_SECRET_KEY", "short")
        monkeypatch.setenv("CORS_ORIGINS", "*")

        import importlib
        from app.core import config
        importlib.reload(config)

        settings = config.Settings()
        warnings, errors = settings._validate_security_config()

        # Should have at least 2 errors (JWT and CORS)
        assert len(errors) >= 2
