"""empty message

Revision ID: 4f65fed2f5a5
Revises: caf3c010faf5
Create Date: 2024-05-21 18:38:31.134980

"""
from alembic import op
import sqlalchemy as sa


def _column_names(table_name: str):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {col['name'] for col in inspector.get_columns(table_name)}


# revision identifiers, used by Alembic.
revision = '4f65fed2f5a5'
down_revision = 'caf3c010faf5'
branch_labels = None
depends_on = None


def upgrade():
    column_names = _column_names('users')
    with op.batch_alter_table('users', schema=None) as batch_op:
        if 'antenna_pattern_data_h' not in column_names:
            batch_op.add_column(sa.Column('antenna_pattern_data_h', sa.Text(), nullable=True))
        if 'antenna_pattern_data_v' not in column_names:
            batch_op.add_column(sa.Column('antenna_pattern_data_v', sa.Text(), nullable=True))
        if 'antenna_pattern_data_h_modified' not in column_names:
            batch_op.add_column(sa.Column('antenna_pattern_data_h_modified', sa.Text(), nullable=True))
        if 'antenna_pattern_data_v_modified' not in column_names:
            batch_op.add_column(sa.Column('antenna_pattern_data_v_modified', sa.Text(), nullable=True))


def downgrade():
    column_names = _column_names('users')
    with op.batch_alter_table('users', schema=None) as batch_op:
        if 'antenna_pattern_data_v_modified' in column_names:
            batch_op.drop_column('antenna_pattern_data_v_modified')
        if 'antenna_pattern_data_h_modified' in column_names:
            batch_op.drop_column('antenna_pattern_data_h_modified')
        if 'antenna_pattern_data_v' in column_names:
            batch_op.drop_column('antenna_pattern_data_v')
        if 'antenna_pattern_data_h' in column_names:
            batch_op.drop_column('antenna_pattern_data_h')
