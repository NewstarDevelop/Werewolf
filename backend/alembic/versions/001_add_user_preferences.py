"""add user preferences

Revision ID: 001
Revises:
Create Date: 2026-01-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add preferences column to users table"""
    # 兼容"旧库已存在部分 schema / 手工修复"的场景,升级过程保持幂等
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("users")}
    if "preferences" in columns:
        return

    # SQLite: Add JSON column with default empty object
    op.add_column(
        "users",
        sa.Column("preferences", sa.JSON(), nullable=False, server_default="{}"),
    )


def downgrade() -> None:
    """Remove preferences column from users table"""
    # Note: SQLite does not support DROP COLUMN easily
    # This downgrade requires table rebuild, which is complex
    # For production, consider this migration as irreversible
    op.drop_column("users", "preferences")
