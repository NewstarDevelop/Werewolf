"""
Redis Pub/Sub utilities.

Dependency note:
- This module expects 'redis' (redis-py) with asyncio support:
  pip install redis>=4.2
- The repository currently doesn't list redis in requirements.txt; you must add it
  when enabling multi-instance notification delivery.

Config:
- Reads REDIS_URL from environment (e.g. redis://localhost:6379/0)
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any, Awaitable, Callable, Optional

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None  # type: ignore


def get_redis_url() -> str:
    """Resolve Redis URL from environment."""
    return os.getenv("REDIS_URL", "").strip()


class RedisPublisher:
    """Thin wrapper around Redis publish API."""

    def __init__(self, client: "redis.Redis") -> None:
        self._client = client

    async def publish_json(self, topic: str, payload: dict[str, Any]) -> None:
        """Publish JSON payload to a topic."""
        data = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        await self._client.publish(topic, data)


class RedisSubscriber:
    """Redis Pub/Sub subscriber with reconnect loop."""

    def __init__(self, client: "redis.Redis") -> None:
        self._client = client
        self._stop_event = asyncio.Event()

    def stop(self) -> None:
        """Request subscriber loop to stop."""
        self._stop_event.set()

    async def run(
        self,
        topic: str,
        handler: Callable[[dict[str, Any]], Awaitable[None]],
        *,
        poll_sleep_seconds: float = 1.0,
    ) -> None:
        """
        Subscribe and dispatch messages.

        handler receives decoded JSON dict.
        """
        pubsub = self._client.pubsub()
        await pubsub.subscribe(topic)
        logger.info(f"[redis] subscribed topic={topic}")

        try:
            while not self._stop_event.is_set():
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if not message:
                    await asyncio.sleep(poll_sleep_seconds)
                    continue

                if message.get("type") != "message":
                    continue

                raw = message.get("data")
                if raw is None:
                    continue

                try:
                    if isinstance(raw, (bytes, bytearray)):
                        raw = raw.decode("utf-8")
                    payload = json.loads(raw)
                    if isinstance(payload, dict):
                        await handler(payload)
                except Exception as e:
                    logger.warning(f"[redis] failed to handle message: {e}")
        finally:
            try:
                await pubsub.unsubscribe(topic)
                await pubsub.close()
            except Exception:
                pass


async def create_redis_client() -> Optional["redis.Redis"]:
    """
    Create Redis client if dependency and config are present.

    Returns None when Redis is not configured, allowing graceful dev-mode fallback.
    """
    if redis is None:
        logger.warning("[redis] redis package not installed; pub/sub disabled")
        return None

    url = get_redis_url()
    if not url:
        logger.warning("[redis] REDIS_URL not set; pub/sub disabled")
        return None

    return redis.Redis.from_url(url, decode_responses=False)
