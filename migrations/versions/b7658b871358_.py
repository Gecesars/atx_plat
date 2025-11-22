"""empty message

Revision ID: b7658b871358
Revises: dfc54b63e18c
Create Date: 2024-05-02 12:40:16.053073

"""
from alembic import op
import sqlalchemy as sa


def _column_names(table_name: str):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {col['name'] for col in inspector.get_columns(table_name)}


# revision identifiers, used by Alembic.
revision = 'b7658b871358'
down_revision = 'dfc54b63e18c'
branch_labels = None
depends_on = None


def upgrade():
    if 'antenna_pattern' in _column_names('users'):
        with op.batch_alter_table('users', schema=None) as batch_op:
            batch_op.alter_column('antenna_pattern',
                   existing_type=sa.BLOB(),
                   type_=sa.Text(),
                   existing_nullable=True)


def downgrade():
    if 'antenna_pattern' in _column_names('users'):
        with op.batch_alter_table('users', schema=None) as batch_op:
            batch_op.alter_column('antenna_pattern',
                   existing_type=sa.Text(),
                   type_=sa.BLOB(),
                   existing_nullable=True)
