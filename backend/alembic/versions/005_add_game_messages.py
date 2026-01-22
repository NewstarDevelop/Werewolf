"""add game_messages table for replay (MVP: messages only)

Revision ID: 005
Revises: 004
Create Date: 2026-01-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    insp = inspect(bind)
    return table_name in insp.get_table_names()


def upgrade() -> None:
    """Create game_messages table."""
    if _table_exists("game_messages"):
        return

    op.create_table(
        "game_messages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "game_id",
            sa.String(36),
            sa.ForeignKey("game_sessions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("seq", sa.Integer(), nullable=False),
        sa.Column("day", sa.Integer(), nullable=False, index=True),
        sa.Column("seat_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("msg_type", sa.String(32), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("game_id", "seq", name="uq_game_messages_game_seq"),
    )

    op.create_index(
        "idx_game_messages_game_seq",
        "game_messages",
        ["game_id", "seq"],
    )
    op.create_index(
        "idx_game_messages_game_day",
        "game_messages",
        ["game_id", "day"],
    )


def downgrade() -> None:
    """Drop game_messages table."""
    op.drop_index("idx_game_messages_game_day", table_name="game_messages")
    op.drop_index("idx_game_messages_game_seq", table_name="game_messages")
    op.drop_table("game_messages")
