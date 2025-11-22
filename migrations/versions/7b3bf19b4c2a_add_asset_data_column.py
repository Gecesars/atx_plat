"""Add inline data storage for assets.

Revision ID: 7b3bf19b4c2a
Revises: d4c8f2fe73f8
Create Date: 2025-11-21 23:25:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7b3bf19b4c2a'
down_revision = 'd4c8f2fe73f8'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('assets', sa.Column('data', sa.LargeBinary(), nullable=True))


def downgrade():
    op.drop_column('assets', 'data')
