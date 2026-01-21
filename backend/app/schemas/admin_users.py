"""Admin user management schemas."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class UserStatusFilter(str, Enum):
    """Filter for user active status."""

    ACTIVE = "active"
    BANNED = "banned"
    ALL = "all"


class AdminFlagFilter(str, Enum):
    """Filter for admin flag."""

    YES = "yes"
    NO = "no"
    ALL = "all"


class UserSort(str, Enum):
    """Sort options for user list."""

    CREATED_AT_DESC = "created_at_desc"
    LAST_LOGIN_AT_DESC = "last_login_at_desc"
    ID_ASC = "id_asc"


class AdminUserBatchAction(str, Enum):
    """Batch action types."""

    BAN = "ban"
    UNBAN = "unban"
    DELETE = "delete"  # Soft delete, equivalent to ban


# Response schemas
class UserListItem(BaseModel):
    """User item for list response."""

    id: str
    nickname: str
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool
    is_admin: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Paginated user list response."""

    items: list[UserListItem]
    total: int
    page: int
    page_size: int


class UserDetailResponse(BaseModel):
    """Detailed user response."""

    id: str
    nickname: str
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    is_active: bool
    is_email_verified: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None
    preferences: dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


# Request schemas
class AdminUpdateUserProfileRequest(BaseModel):
    """Request to update user profile."""

    nickname: Optional[str] = Field(None, min_length=2, max_length=50)
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = Field(None, max_length=512)


class AdminSetUserActiveRequest(BaseModel):
    """Request to set user active status."""

    is_active: bool


class AdminSetUserAdminRequest(BaseModel):
    """Request to set user admin flag."""

    is_admin: bool


class AdminUserBatchRequest(BaseModel):
    """Request for batch user operations."""

    action: AdminUserBatchAction
    ids: list[str] = Field(..., min_length=1, max_length=100)


class AdminUserBatchResponse(BaseModel):
    """Response for batch user operations."""

    accepted: int
    updated: int
    failed: list[str] = Field(default_factory=list)
