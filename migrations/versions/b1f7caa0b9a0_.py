"""empty message

Revision ID: b1f7caa0b9a0
Revises: a0e2b314ab99
Create Date: 2024-04-28 18:35:02.707090

"""
from alembic import op
import sqlalchemy as sa


def _column_names(table_name: str):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {col['name'] for col in inspector.get_columns(table_name)}


# revision identifiers, used by Alembic.
revision = 'b1f7caa0b9a0'
down_revision = 'a0e2b314ab99'
branch_labels = None
depends_on = None


def upgrade():
    column_names = _column_names('users')
    with op.batch_alter_table('users', schema=None) as batch_op:
        if 'total_loss' not in column_names:
            batch_op.add_column(sa.Column('total_loss', sa.Float(), nullable=True))
        if 'cable_type' in column_names:
            batch_op.drop_column('cable_type')


def downgrade():
    column_names = _column_names('users')
    with op.batch_alter_table('users', schema=None) as batch_op:
        if 'cable_type' not in column_names:
            batch_op.add_column(sa.Column('cable_type', sa.VARCHAR(), nullable=True))
        if 'total_loss' in column_names:
            batch_op.drop_column('total_loss')
