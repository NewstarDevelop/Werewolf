"""Client IP extraction utilities with trusted proxy support.

A5-FIX: Implements TRUSTED_PROXIES-driven real client IP extraction.
Only trust X-Forwarded-For when the request comes from a trusted proxy.
"""
import ipaddress
import logging
from typing import Optional

from fastapi import Request

from app.core.config import settings

logger = logging.getLogger(__name__)

# Cache parsed CIDR networks for performance
_trusted_networks: Optional[list[ipaddress.IPv4Network | ipaddress.IPv6Network]] = None


def _get_trusted_networks() -> list[ipaddress.IPv4Network | ipaddress.IPv6Network]:
    """Parse and cache trusted proxy networks from settings."""
    global _trusted_networks
    if _trusted_networks is not None:
        return _trusted_networks

    _trusted_networks = []
    for proxy in settings.TRUSTED_PROXIES:
        try:
            # Try parsing as network (CIDR)
            if "/" in proxy:
                network = ipaddress.ip_network(proxy, strict=False)
                _trusted_networks.append(network)
            else:
                # Single IP - convert to /32 or /128 network
                ip = ipaddress.ip_address(proxy)
                if isinstance(ip, ipaddress.IPv4Address):
                    network = ipaddress.IPv4Network(f"{proxy}/32")
                else:
                    network = ipaddress.IPv6Network(f"{proxy}/128")
                _trusted_networks.append(network)
        except ValueError as e:
            logger.warning(f"Invalid TRUSTED_PROXIES entry '{proxy}': {e}")

    return _trusted_networks


def _is_trusted_proxy(ip: str) -> bool:
    """Check if an IP address is a trusted proxy."""
    try:
        addr = ipaddress.ip_address(ip)
        for network in _get_trusted_networks():
            if addr in network:
                return True
        return False
    except ValueError:
        return False


def get_client_ip(request: Request) -> str:
    """Get the real client IP address from a request.

    If the request comes from a trusted proxy (as configured in TRUSTED_PROXIES),
    extracts the original client IP from X-Forwarded-For header.
    Otherwise, returns the direct connection IP.

    This prevents IP spoofing attacks where untrusted clients send fake
    X-Forwarded-For headers to bypass rate limiting or IP-based security.

    Args:
        request: FastAPI Request object

    Returns:
        Client IP address string
    """
    # Get direct connection IP
    peer_ip = request.client.host if request.client else "unknown"

    # If no trusted proxies configured, always use peer IP
    if not settings.TRUSTED_PROXIES:
        return peer_ip

    # Check if request comes from a trusted proxy
    if not _is_trusted_proxy(peer_ip):
        # Not from trusted proxy - don't trust X-Forwarded-For
        return peer_ip

    # Request is from trusted proxy - extract client IP from X-Forwarded-For
    xff = request.headers.get("x-forwarded-for", "")
    if not xff:
        return peer_ip

    # X-Forwarded-For format: client, proxy1, proxy2, ...
    # Take the leftmost (original client) IP
    ips = [ip.strip() for ip in xff.split(",")]
    if not ips:
        return peer_ip

    client_ip = ips[0]

    # Validate the extracted IP
    try:
        ipaddress.ip_address(client_ip)
        return client_ip
    except ValueError:
        logger.warning(f"Invalid IP in X-Forwarded-For: {client_ip}, using peer IP")
        return peer_ip


def get_client_ip_for_logging(request: Request) -> str:
    """Get client IP with additional context for logging.

    Returns a string like "1.2.3.4" or "1.2.3.4 (via proxy 10.0.0.1)"
    """
    peer_ip = request.client.host if request.client else "unknown"
    client_ip = get_client_ip(request)

    if client_ip != peer_ip:
        return f"{client_ip} (via proxy {peer_ip})"
    return client_ip
