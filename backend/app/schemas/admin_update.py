"""Schemas for admin update (方案 B: 更新代理)."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


UpdateJobState = Literal["idle", "queued", "running", "success", "error"]


class AdminUpdateCheckResponse(BaseModel):
    """Response for GET /api/admin/update/check."""

    update_available: bool
    current_revision: Optional[str] = None
    remote_revision: Optional[str] = None

    blocked: bool = False
    blocking_reasons: list[str] = Field(default_factory=list)

    agent_reachable: bool = True
    agent_job_running: bool = False
    agent_job_id: Optional[str] = None
    agent_message: Optional[str] = None


class AdminUpdateRunRequest(BaseModel):
    """Request for POST /api/admin/update/run."""

    force: bool = False
    confirm_phrase: Optional[str] = None


class AdminUpdateRunResponse(BaseModel):
    """Response for POST /api/admin/update/run."""

    status: Literal["accepted"]
    job_id: str
    message: str


class AdminUpdateStatusResponse(BaseModel):
    """Response for GET /api/admin/update/status."""

    job_id: Optional[str] = None
    state: UpdateJobState = "idle"
    message: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    current_revision: Optional[str] = None
    remote_revision: Optional[str] = None
    last_log_lines: list[str] = Field(default_factory=list)
