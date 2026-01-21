"""Tests for client IP extraction - A5: Trusted proxy support.

Verifies that:
1. Direct connection IP is used when no trusted proxies configured
2. X-Forwarded-For is trusted only from configured proxies
3. Invalid IPs in XFF are handled gracefully
"""
import pytest
from unittest.mock import MagicMock


class TestClientIP:
    """Test client IP extraction with trusted proxy support."""

    def test_no_trusted_proxies_uses_peer_ip(self, monkeypatch):
        """When no trusted proxies configured, always use peer IP."""
        monkeypatch.setenv("TRUSTED_PROXIES", "")

        # Reset cached networks
        import importlib
        from app.core import config
        importlib.reload(config)

        from app.core import client_ip
        # Reset the cache
        client_ip._trusted_networks = None
        importlib.reload(client_ip)

        # Create mock request with XFF header
        mock_request = MagicMock()
        mock_request.client.host = "10.0.0.1"
        mock_request.headers = {"x-forwarded-for": "1.2.3.4, 10.0.0.1"}

        # Should return peer IP, not XFF
        result = client_ip.get_client_ip(mock_request)
        assert result == "10.0.0.1"

    def test_trusted_proxy_uses_xff(self, monkeypatch):
        """When request from trusted proxy, use X-Forwarded-For."""
        monkeypatch.setenv("TRUSTED_PROXIES", "10.0.0.1,192.168.0.0/16")

        import importlib
        from app.core import config
        importlib.reload(config)

        from app.core import client_ip
        client_ip._trusted_networks = None
        importlib.reload(client_ip)

        # Create mock request from trusted proxy
        mock_request = MagicMock()
        mock_request.client.host = "10.0.0.1"  # Trusted proxy
        mock_request.headers = {"x-forwarded-for": "203.0.113.50, 10.0.0.1"}

        result = client_ip.get_client_ip(mock_request)
        assert result == "203.0.113.50"  # Original client IP

    def test_untrusted_proxy_ignores_xff(self, monkeypatch):
        """When request from untrusted source, ignore X-Forwarded-For."""
        monkeypatch.setenv("TRUSTED_PROXIES", "10.0.0.1")

        import importlib
        from app.core import config
        importlib.reload(config)

        from app.core import client_ip
        client_ip._trusted_networks = None
        importlib.reload(client_ip)

        # Create mock request from untrusted source
        mock_request = MagicMock()
        mock_request.client.host = "203.0.113.100"  # Not trusted
        mock_request.headers = {"x-forwarded-for": "1.2.3.4"}  # Spoofed

        result = client_ip.get_client_ip(mock_request)
        assert result == "203.0.113.100"  # Peer IP, not spoofed XFF

    def test_cidr_network_trusted(self, monkeypatch):
        """CIDR network ranges should work."""
        monkeypatch.setenv("TRUSTED_PROXIES", "192.168.0.0/16")

        import importlib
        from app.core import config
        importlib.reload(config)

        from app.core import client_ip
        client_ip._trusted_networks = None
        importlib.reload(client_ip)

        # Create mock request from IP within CIDR range
        mock_request = MagicMock()
        mock_request.client.host = "192.168.50.100"  # Within 192.168.0.0/16
        mock_request.headers = {"x-forwarded-for": "8.8.8.8"}

        result = client_ip.get_client_ip(mock_request)
        assert result == "8.8.8.8"

    def test_invalid_xff_fallback_to_peer(self, monkeypatch):
        """Invalid IP in X-Forwarded-For should fallback to peer IP."""
        monkeypatch.setenv("TRUSTED_PROXIES", "10.0.0.1")

        import importlib
        from app.core import config
        importlib.reload(config)

        from app.core import client_ip
        client_ip._trusted_networks = None
        importlib.reload(client_ip)

        # Create mock request with invalid XFF
        mock_request = MagicMock()
        mock_request.client.host = "10.0.0.1"
        mock_request.headers = {"x-forwarded-for": "invalid-ip, 10.0.0.1"}

        result = client_ip.get_client_ip(mock_request)
        assert result == "10.0.0.1"  # Fallback to peer

    def test_empty_xff_uses_peer(self, monkeypatch):
        """Empty X-Forwarded-For should use peer IP."""
        monkeypatch.setenv("TRUSTED_PROXIES", "10.0.0.1")

        import importlib
        from app.core import config
        importlib.reload(config)

        from app.core import client_ip
        client_ip._trusted_networks = None
        importlib.reload(client_ip)

        mock_request = MagicMock()
        mock_request.client.host = "10.0.0.1"
        mock_request.headers = {"x-forwarded-for": ""}

        result = client_ip.get_client_ip(mock_request)
        assert result == "10.0.0.1"

    def test_logging_format(self, monkeypatch):
        """get_client_ip_for_logging should include proxy info."""
        monkeypatch.setenv("TRUSTED_PROXIES", "10.0.0.1")

        import importlib
        from app.core import config
        importlib.reload(config)

        from app.core import client_ip
        client_ip._trusted_networks = None
        importlib.reload(client_ip)

        mock_request = MagicMock()
        mock_request.client.host = "10.0.0.1"
        mock_request.headers = {"x-forwarded-for": "203.0.113.50"}

        result = client_ip.get_client_ip_for_logging(mock_request)
        assert "203.0.113.50" in result
        assert "via proxy" in result
        assert "10.0.0.1" in result
