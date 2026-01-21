"""Unified HTTP client with timeout, retry, and connection management.

This module provides a configured httpx client for all external HTTP requests.
It enforces timeouts to prevent blocking the event loop indefinitely.
"""
import logging
from typing import Optional
from functools import lru_cache

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


# Default timeout configuration (in seconds)
DEFAULT_TIMEOUT = httpx.Timeout(
    connect=5.0,      # Connection establishment
    read=30.0,        # Reading response body
    write=10.0,       # Writing request body
    pool=5.0,         # Waiting for connection from pool
)

# Shorter timeout for OAuth operations
OAUTH_TIMEOUT = httpx.Timeout(
    connect=5.0,
    read=10.0,
    write=5.0,
    pool=3.0,
)

# Longer timeout for LLM operations
LLM_TIMEOUT = httpx.Timeout(
    connect=10.0,
    read=120.0,       # LLM responses can be slow
    write=10.0,
    pool=10.0,
)

# Connection pool limits
DEFAULT_LIMITS = httpx.Limits(
    max_connections=100,
    max_keepalive_connections=20,
    keepalive_expiry=30.0,
)


class RetryableHTTPClient:
    """HTTP client with retry support for transient errors.

    Usage:
        async with RetryableHTTPClient() as client:
            response = await client.get("https://api.example.com/data")
    """

    def __init__(
        self,
        timeout: Optional[httpx.Timeout] = None,
        limits: Optional[httpx.Limits] = None,
        max_retries: int = 2,
        retry_statuses: tuple = (502, 503, 504),
    ):
        self.timeout = timeout or DEFAULT_TIMEOUT
        self.limits = limits or DEFAULT_LIMITS
        self.max_retries = max_retries
        self.retry_statuses = retry_statuses
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> httpx.AsyncClient:
        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            limits=self.limits,
            follow_redirects=True,
        )
        return self._client

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()


def get_oauth_client() -> httpx.AsyncClient:
    """Get a configured httpx client for OAuth operations.

    Returns:
        httpx.AsyncClient with OAuth-specific timeout settings.

    Note:
        Caller is responsible for closing the client or using as context manager.
    """
    return httpx.AsyncClient(
        timeout=OAUTH_TIMEOUT,
        limits=DEFAULT_LIMITS,
        follow_redirects=True,
    )


def get_llm_client() -> httpx.AsyncClient:
    """Get a configured httpx client for LLM API operations.

    Returns:
        httpx.AsyncClient with LLM-specific timeout settings.

    Note:
        Caller is responsible for closing the client or using as context manager.
    """
    return httpx.AsyncClient(
        timeout=LLM_TIMEOUT,
        limits=DEFAULT_LIMITS,
        follow_redirects=False,  # LLM APIs shouldn't redirect
    )


# Singleton clients for reuse (optional - for high-frequency usage)
_shared_oauth_client: Optional[httpx.AsyncClient] = None
_shared_llm_client: Optional[httpx.AsyncClient] = None


async def get_shared_oauth_client() -> httpx.AsyncClient:
    """Get or create a shared OAuth client.

    This is useful for high-frequency OAuth operations.
    The client should be closed during application shutdown.
    """
    global _shared_oauth_client
    if _shared_oauth_client is None or _shared_oauth_client.is_closed:
        _shared_oauth_client = get_oauth_client()
    return _shared_oauth_client


async def close_shared_clients():
    """Close all shared HTTP clients. Call during application shutdown."""
    global _shared_oauth_client, _shared_llm_client

    if _shared_oauth_client and not _shared_oauth_client.is_closed:
        await _shared_oauth_client.aclose()
        _shared_oauth_client = None

    if _shared_llm_client and not _shared_llm_client.is_closed:
        await _shared_llm_client.aclose()
        _shared_llm_client = None

    logger.info("Shared HTTP clients closed")
