"""add updated_at columns to asset-related tables

Revision ID: fd0aa8e4b52b
Revises: f9e8fceb5a1b
Create Date: 2025-02-14 22:15:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "fd0aa8e4b52b"
down_revision = "f9e8fceb5a1b"
branch_labels = None
depends_on = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return column_name in {col["name"] for col in inspector.get_columns(table_name)}


def _add_column_with_default(table_name: str) -> None:
    if _has_column(table_name, "updated_at"):
        return
    with op.batch_alter_table(table_name) as batch_op:
        batch_op.add_column(
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            )
        )


def upgrade() -> None:
    for table in ("assets", "coverage_jobs", "reports", "dataset_sources"):
        _add_column_with_default(table)


def downgrade() -> None:
    for table in ("assets", "coverage_jobs", "reports", "dataset_sources"):
        if _has_column(table, "updated_at"):
            with op.batch_alter_table(table) as batch_op:
                batch_op.drop_column("updated_at")
