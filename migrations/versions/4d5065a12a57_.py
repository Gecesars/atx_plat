"""empty message

Revision ID: 4d5065a12a57
Revises: b9c63a12ffc1
Create Date: 2024-05-08 12:16:56.710801

"""
from alembic import op
import sqlalchemy as sa


def _column_names(table_name: str):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {col['name'] for col in inspector.get_columns(table_name)}


# revision identifiers, used by Alembic.
revision = '4d5065a12a57'
down_revision = 'b9c63a12ffc1'
branch_labels = None
depends_on = None


def upgrade():
    column_names = _column_names('users')
    with op.batch_alter_table('users', schema=None) as batch_op:
        if 'antenna_direction' not in column_names:
            batch_op.add_column(sa.Column('antenna_direction', sa.Float(), nullable=True))
        if 'antenna_tilt' not in column_names:
            batch_op.add_column(sa.Column('antenna_tilt', sa.Float(), nullable=True))


def downgrade():
    column_names = _column_names('users')
    with op.batch_alter_table('users', schema=None) as batch_op:
        if 'antenna_tilt' in column_names:
            batch_op.drop_column('antenna_tilt')
        if 'antenna_direction' in column_names:
            batch_op.drop_column('antenna_direction')
