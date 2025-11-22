"""Merge multiple heads into a single lineage.

Revision ID: d4c8f2fe73f8
Revises: 1e4fa8cd5acb, 098cfb467e49, 5b2d5bb1c4b3, cc3d3ad4f9a1
Create Date: 2025-11-21 19:53:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = 'd4c8f2fe73f8'
down_revision = ('1e4fa8cd5acb', '5b2d5bb1c4b3')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
