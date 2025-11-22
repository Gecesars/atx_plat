"""add propagation param columns

Revision ID: e3a33b72b1cf
Revises: caf3c010faf5
Create Date: 2025-10-27 14:45:00

"""
from alembic import op
import sqlalchemy as sa


def _column_names(table_name: str):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {col['name'] for col in inspector.get_columns(table_name)}


# revision identifiers, used by Alembic.
revision = 'e3a33b72b1cf'
down_revision = '4f65fed2f5a5'
branch_labels = None
depends_on = None


def upgrade():
    column_names = _column_names('users')
    with op.batch_alter_table('users', schema=None) as batch_op:
        if 'time_percentage' not in column_names:
            batch_op.add_column(sa.Column('time_percentage', sa.Float(), nullable=True))
        if 'polarization' not in column_names:
            batch_op.add_column(sa.Column('polarization', sa.String(), nullable=True))
        if 'temperature_k' not in column_names:
            batch_op.add_column(sa.Column('temperature_k', sa.Float(), nullable=True))
        if 'pressure_hpa' not in column_names:
            batch_op.add_column(sa.Column('pressure_hpa', sa.Float(), nullable=True))
        if 'water_density' not in column_names:
            batch_op.add_column(sa.Column('water_density', sa.Float(), nullable=True))
        if 'p452_version' not in column_names:
            batch_op.add_column(sa.Column('p452_version', sa.Integer(), nullable=True))


def downgrade():
    column_names = _column_names('users')
    with op.batch_alter_table('users', schema=None) as batch_op:
        if 'p452_version' in column_names:
            batch_op.drop_column('p452_version')
        if 'water_density' in column_names:
            batch_op.drop_column('water_density')
        if 'pressure_hpa' in column_names:
            batch_op.drop_column('pressure_hpa')
        if 'temperature_k' in column_names:
            batch_op.drop_column('temperature_k')
        if 'polarization' in column_names:
            batch_op.drop_column('polarization')
        if 'time_percentage' in column_names:
            batch_op.drop_column('time_percentage')
