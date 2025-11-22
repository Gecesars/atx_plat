"""add project settings column

Revision ID: a52f5abf3e5d
Revises: fd0aa8e4b52b
Create Date: 2025-02-14 23:05:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a52f5abf3e5d"
down_revision = "fd0aa8e4b52b"
branch_labels = None
depends_on = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return column_name in {col["name"] for col in inspector.get_columns(table_name)}


def upgrade() -> None:
    if not _has_column("projects", "settings"):
        with op.batch_alter_table("projects") as batch_op:
            batch_op.add_column(sa.Column("settings", sa.JSON(), nullable=True))


def downgrade() -> None:
    if _has_column("projects", "settings"):
        with op.batch_alter_table("projects") as batch_op:
            batch_op.drop_column("settings")
