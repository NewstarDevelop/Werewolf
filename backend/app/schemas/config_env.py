"""Schemas for admin .env management endpoints."""

from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


ENV_KEY_PATTERN = r"^[A-Za-z_][A-Za-z0-9_]*$"

RequiredReason = Literal["required", "docker_required"]
EnvVarSource = Literal["env_file", "env_example"]


class EnvVarResponse(BaseModel):
    """Single env var view for UI consumption.

    Security: sensitive keys never return plaintext value.
    """

    name: str = Field(..., pattern=ENV_KEY_PATTERN, description="Environment variable name")
    value: Optional[str] = Field(
        None,
        description="Plaintext value for non-sensitive keys; null for sensitive keys",
    )
    is_sensitive: bool = Field(..., description="Whether this key is treated as sensitive")
    is_set: bool = Field(..., description="Whether the value exists and is non-empty in .env")
    source: Literal["env_file"] = Field("env_file", description="Configuration source")


class EnvVarMergedResponse(BaseModel):
    """Merged env var view from both .env and .env.example (required-only).

    - Sensitive keys never return plaintext value (value=null).
    - Required keys may come from .env.example even if absent in .env.
    """

    name: str = Field(..., pattern=ENV_KEY_PATTERN, description="Environment variable name")
    value: Optional[str] = Field(
        None,
        description="Plaintext value for non-sensitive keys; null for sensitive keys",
    )
    is_sensitive: bool = Field(..., description="Whether this key is treated as sensitive")
    is_set: bool = Field(..., description="Whether the value exists and is non-empty in .env")
    source: EnvVarSource = Field(..., description="Configuration source for this item")

    is_required: bool = Field(..., description="Whether this variable is required by template (.env.example)")
    required_reason: Optional[RequiredReason] = Field(
        None,
        description="Required reason when is_required=true; otherwise null",
    )
    is_editable: bool = Field(..., description="Whether this key is allowed to be edited via admin API")


class EnvUpdateItem(BaseModel):
    """Single env update operation."""

    name: str = Field(..., pattern=ENV_KEY_PATTERN)
    action: Literal["set", "unset"] = Field("set")
    value: Optional[str] = Field(
        None,
        max_length=8192,
        description="Required when action=set; ignored when action=unset",
    )
    confirm_sensitive: bool = Field(
        False,
        description="Required for setting sensitive keys (server enforced)",
    )

    @field_validator("value")
    @classmethod
    def _validate_value(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if "\n" in v or "\r" in v or "\x00" in v:
            raise ValueError("Invalid value: newline or NUL is not allowed")
        return v

    @model_validator(mode="after")
    def _validate_action_value(self) -> "EnvUpdateItem":
        if self.action == "set" and self.value is None:
            raise ValueError("value is required when action=set")
        return self


class EnvUpdateRequest(BaseModel):
    """Batch update request. Applied atomically (all-or-nothing)."""

    updates: list[EnvUpdateItem] = Field(..., min_length=1)

    @model_validator(mode="after")
    def _validate_unique_keys(self) -> "EnvUpdateRequest":
        names = [u.name for u in self.updates]
        if len(set(names)) != len(names):
            raise ValueError("Duplicate key in updates is not allowed")
        return self


class EnvUpdateItemResult(BaseModel):
    """Result for one update item (no secret values)."""

    name: str
    action: Literal["set", "unset"]
    status: Literal["created", "updated", "deleted", "skipped"]
    message: Optional[str] = None


class EnvUpdateResult(BaseModel):
    """Batch update result."""

    success: bool
    results: list[EnvUpdateItemResult]
    restart_required: bool = Field(
        ...,
        description="Whether a server restart is required for changes to fully take effect",
    )
    env_file_path: str = Field(..., description="Resolved .env file path used for this operation")
