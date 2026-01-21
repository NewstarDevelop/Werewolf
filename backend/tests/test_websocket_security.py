"""WebSocket authentication and security tests."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import WebSocket

from app.services.websocket_auth import (
    extract_token,
    validate_origin,
    authenticate_websocket,
    WebSocketAuthError,
)


class TestExtractToken:
    """Tests for token extraction from WebSocket."""

    @pytest.mark.asyncio
    async def test_extract_from_subprotocol(self):
        """Test token extraction from Sec-WebSocket-Protocol."""
        websocket = MagicMock(spec=WebSocket)
        websocket.scope = {"subprotocols": ["auth", "test-token-123"]}
        websocket.cookies = {}
        websocket.query_params = {}

        token, source = await extract_token(websocket)

        assert token == "test-token-123"
        assert source == "protocol"

    @pytest.mark.asyncio
    async def test_extract_from_cookie(self):
        """Test token extraction from cookie."""
        websocket = MagicMock(spec=WebSocket)
        websocket.scope = {"subprotocols": []}
        websocket.cookies = {"user_access_token": "cookie-token-456"}
        websocket.query_params = {}

        token, source = await extract_token(websocket)

        assert token == "cookie-token-456"
        assert source == "cookie"

    @pytest.mark.asyncio
    async def test_extract_from_query_when_allowed(self):
        """Test token extraction from query string when allowed."""
        websocket = MagicMock(spec=WebSocket)
        websocket.scope = {"subprotocols": []}
        websocket.cookies = {}
        websocket.query_params = {"token": "query-token-789"}

        token, source = await extract_token(websocket, allow_query_token=True)

        assert token == "query-token-789"
        assert source == "query"

    @pytest.mark.asyncio
    async def test_no_token_found(self):
        """Test when no token is available."""
        websocket = MagicMock(spec=WebSocket)
        websocket.scope = {"subprotocols": []}
        websocket.cookies = {}
        websocket.query_params = {}

        token, source = await extract_token(websocket)

        assert token is None
        assert source == "none"

    @pytest.mark.asyncio
    async def test_query_token_ignored_when_not_allowed(self):
        """Test that query token is ignored when not allowed."""
        websocket = MagicMock(spec=WebSocket)
        websocket.scope = {"subprotocols": []}
        websocket.cookies = {}
        websocket.query_params = {"token": "query-token-789"}

        token, source = await extract_token(websocket, allow_query_token=False)

        assert token is None
        assert source == "none"


class TestValidateOrigin:
    """Tests for WebSocket origin validation."""

    def test_valid_origin(self):
        """Test valid origin is accepted."""
        websocket = MagicMock(spec=WebSocket)
        websocket.headers = {"origin": "https://example.com"}

        with patch("app.services.websocket_auth.settings") as mock_settings:
            mock_settings.ALLOWED_WS_ORIGINS = ["https://example.com"]
            mock_settings.DEBUG = False

            is_valid, origin = validate_origin(websocket)

            assert is_valid is True
            assert origin == "https://example.com"

    def test_invalid_origin(self):
        """Test invalid origin is rejected."""
        websocket = MagicMock(spec=WebSocket)
        websocket.headers = {"origin": "https://evil.com"}

        with patch("app.services.websocket_auth.settings") as mock_settings:
            mock_settings.ALLOWED_WS_ORIGINS = ["https://example.com"]
            mock_settings.DEBUG = False

            is_valid, origin = validate_origin(websocket)

            assert is_valid is False
            assert origin == "https://evil.com"

    def test_localhost_allowed_in_debug(self):
        """Test localhost origins allowed in debug mode."""
        websocket = MagicMock(spec=WebSocket)
        websocket.headers = {"origin": "http://localhost:3000", "host": "localhost:8000"}

        with patch("app.services.websocket_auth.settings") as mock_settings:
            mock_settings.ALLOWED_WS_ORIGINS = []
            mock_settings.DEBUG = True

            is_valid, origin = validate_origin(websocket)

            assert is_valid is True

    def test_same_origin_accepted(self):
        """Test same-origin requests are accepted."""
        websocket = MagicMock(spec=WebSocket)
        websocket.headers = {"origin": "https://api.example.com", "host": "api.example.com"}

        with patch("app.services.websocket_auth.settings") as mock_settings:
            mock_settings.ALLOWED_WS_ORIGINS = []
            mock_settings.DEBUG = False

            is_valid, origin = validate_origin(websocket)

            assert is_valid is True


class TestLoginRateLimiter:
    """Tests for login rate limiting."""

    def test_allows_initial_attempts(self):
        """Test that initial attempts are allowed."""
        from app.services.login_rate_limiter import LoginRateLimiter

        limiter = LoginRateLimiter(max_attempts=3)

        is_allowed, retry_after = limiter.check_rate_limit("192.168.1.1")

        assert is_allowed is True
        assert retry_after is None

    def test_blocks_after_max_attempts(self):
        """Test that attempts are blocked after max attempts."""
        from app.services.login_rate_limiter import LoginRateLimiter

        limiter = LoginRateLimiter(max_attempts=3, lockout_seconds=60)

        # Record failed attempts
        for _ in range(3):
            limiter.record_attempt("192.168.1.2", success=False)

        is_allowed, retry_after = limiter.check_rate_limit("192.168.1.2")

        assert is_allowed is False
        assert retry_after is not None
        assert retry_after > 0

    def test_successful_login_resets_attempts(self):
        """Test that successful login resets attempt counter."""
        from app.services.login_rate_limiter import LoginRateLimiter

        limiter = LoginRateLimiter(max_attempts=3)

        # Record some failed attempts
        limiter.record_attempt("192.168.1.3", success=False)
        limiter.record_attempt("192.168.1.3", success=False)

        # Successful login
        limiter.record_attempt("192.168.1.3", success=True)

        # Should be allowed again
        is_allowed, _ = limiter.check_rate_limit("192.168.1.3")
        assert is_allowed is True

    def test_reset_clears_all_state(self):
        """Test that reset clears all limiting state."""
        from app.services.login_rate_limiter import LoginRateLimiter

        limiter = LoginRateLimiter(max_attempts=3, lockout_seconds=60)

        # Lock out the IP
        for _ in range(3):
            limiter.record_attempt("192.168.1.4", success=False)

        is_allowed, _ = limiter.check_rate_limit("192.168.1.4")
        assert is_allowed is False

        # Reset
        limiter.reset("192.168.1.4")

        is_allowed, _ = limiter.check_rate_limit("192.168.1.4")
        assert is_allowed is True
