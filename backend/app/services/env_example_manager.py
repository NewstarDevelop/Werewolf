"""Read-only utilities for parsing required env vars from .env.example.

This module is intentionally read-only:
- It never writes to .env.example
- It does not attempt to validate runtime values

It exists to support admin UI by exposing which variables are required,
while still keeping .env as the source of truth for actual configured values.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from app.core import config as config_module

logger = logging.getLogger(__name__)


class EnvExampleError(Exception):
    """Base error for .env.example operations."""


class EnvExampleNotFoundError(EnvExampleError):
    """Raised when .env.example cannot be resolved."""


class EnvExamplePermissionError(EnvExampleError):
    """Raised on filesystem permission issues."""


class EnvExampleDecodeError(EnvExampleError):
    """Raised when .env.example cannot be decoded as UTF-8."""


class EnvExampleManager:
    """Parse required keys from .env.example.

    Required keys are identified by comment tags:
    - [必需] -> required
    - [Docker 部署必需] -> docker_required
    """

    _key_pattern = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

    _tag_required = "[必需]"
    _tag_docker_required = "[Docker 部署必需]"

    def resolve_env_example_path(self) -> Path:
        """Resolve .env.example path with simple, predictable rules."""
        current_file = Path(config_module.__file__).resolve()
        possible_paths = [
            # Docker environment: /app/.env.example (same level as backend/)
            current_file.parent.parent.parent / ".env.example",
            # Local development: project_root/.env.example
            current_file.parent.parent.parent.parent / ".env.example",
            # Fallback: current working directory
            Path.cwd() / ".env.example",
        ]

        for p in possible_paths:
            if p.exists():
                try:
                    resolved = p.resolve(strict=True)
                except OSError as e:
                    raise EnvExampleError(f"Path resolution failed: {e}") from e
                if not resolved.is_file():
                    raise EnvExampleError(".env.example must be a regular file")
                return resolved

        raise EnvExampleNotFoundError("No .env.example file found")

    def read_required_keys(self) -> tuple[Path, dict[str, str]]:
        """Read required keys mapping from .env.example.

        Returns:
            (path, key -> required_reason)
        """
        path = self.resolve_env_example_path()
        try:
            text = path.read_text(encoding="utf-8")
        except FileNotFoundError as e:
            raise EnvExampleNotFoundError("Resolved .env.example file does not exist") from e
        except PermissionError as e:
            raise EnvExamplePermissionError("Permission denied reading .env.example") from e
        except UnicodeDecodeError as e:
            raise EnvExampleDecodeError("Failed to decode .env.example (expected UTF-8)") from e

        return path, self._parse_required_keys(text)

    def _parse_required_keys(self, text: str) -> dict[str, str]:
        """Extract required keys by scanning tag comment lines and next KEY= line."""
        required_by_key: dict[str, str] = {}
        pending_reason: str | None = None

        for raw in text.splitlines():
            stripped = raw.strip()
            if stripped == "":
                pending_reason = None
                continue

            # Detect tag markers (Chinese template conventions)
            if self._tag_docker_required in stripped:
                pending_reason = "docker_required"
            elif self._tag_required in stripped:
                pending_reason = "required"

            # Extract KEY= from either active lines or commented example lines
            key = self._extract_key_from_line(raw)
            if key and pending_reason:
                required_by_key.setdefault(key, pending_reason)
                pending_reason = None

        return required_by_key

    def _extract_key_from_line(self, raw: str) -> str | None:
        """Extract env key from a line like:
        - KEY=value
        - export KEY=value
        - # KEY=value
        - # export KEY=value
        """
        candidate = raw.lstrip()
        if candidate.startswith("#"):
            candidate = candidate[1:].lstrip()

        if candidate.startswith("export "):
            candidate = candidate[len("export ") :]

        if "=" not in candidate:
            return None

        left, _ = candidate.split("=", 1)
        key = left.strip()
        if not self._key_pattern.fullmatch(key):
            return None
        return key
