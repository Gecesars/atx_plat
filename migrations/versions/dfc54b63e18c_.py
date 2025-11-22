"""empty message

Revision ID: dfc54b63e18c
Revises: b1f7caa0b9a0
Create Date: 2024-05-02 12:25:50.325297

"""
from alembic import op
import sqlalchemy as sa


def _column_names(table_name: str):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {col['name'] for col in inspector.get_columns(table_name)}


# revision identifiers, used by Alembic.
revision = 'dfc54b63e18c'
down_revision = 'b1f7caa0b9a0'
branch_labels = None
depends_on = None


def upgrade():
    column_names = _column_names('users')
    if 'antenna_pattern' not in column_names:
        with op.batch_alter_table('users', schema=None) as batch_op:
            batch_op.add_column(sa.Column('antenna_pattern', sa.LargeBinary(), nullable=True))


def downgrade():
    column_names = _column_names('users')
    if 'antenna_pattern' in column_names:
        with op.batch_alter_table('users', schema=None) as batch_op:
            batch_op.drop_column('antenna_pattern')
