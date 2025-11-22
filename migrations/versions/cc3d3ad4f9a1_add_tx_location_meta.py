"""add tx location metadata

Revision ID: cc3d3ad4f9a1
Revises: e3a33b72b1cf
Create Date: 2025-10-27 15:40:00

"""
from alembic import op
import sqlalchemy as sa


def _column_names(table_name: str):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {col['name'] for col in inspector.get_columns(table_name)}


# revision identifiers, used by Alembic.
revision = 'cc3d3ad4f9a1'
down_revision = 'e3a33b72b1cf'
branch_labels = None
depends_on = None


def upgrade():
    column_names = _column_names('users')
    with op.batch_alter_table('users', schema=None) as batch_op:
        if 'tx_location_name' not in column_names:
            batch_op.add_column(sa.Column('tx_location_name', sa.String(), nullable=True))
        if 'tx_site_elevation' not in column_names:
            batch_op.add_column(sa.Column('tx_site_elevation', sa.Float(), nullable=True))
        if 'climate_lat' not in column_names:
            batch_op.add_column(sa.Column('climate_lat', sa.Float(), nullable=True))
        if 'climate_lon' not in column_names:
            batch_op.add_column(sa.Column('climate_lon', sa.Float(), nullable=True))
        if 'climate_updated_at' not in column_names:
            batch_op.add_column(sa.Column('climate_updated_at', sa.DateTime(), nullable=True))


def downgrade():
    column_names = _column_names('users')
    with op.batch_alter_table('users', schema=None) as batch_op:
        if 'climate_updated_at' in column_names:
            batch_op.drop_column('climate_updated_at')
        if 'climate_lon' in column_names:
            batch_op.drop_column('climate_lon')
        if 'climate_lat' in column_names:
            batch_op.drop_column('climate_lat')
        if 'tx_site_elevation' in column_names:
            batch_op.drop_column('tx_site_elevation')
        if 'tx_location_name' in column_names:
            batch_op.drop_column('tx_location_name')
