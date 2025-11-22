"""empty message

Revision ID: b9c63a12ffc1
Revises: b7658b871358
Create Date: 2024-05-02 13:16:47.876092

"""
from alembic import op
import sqlalchemy as sa


def _column_names(table_name: str):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {col['name'] for col in inspector.get_columns(table_name)}


# revision identifiers, used by Alembic.
revision = 'b9c63a12ffc1'
down_revision = 'b7658b871358'
branch_labels = None
depends_on = None


def upgrade():
    if 'antenna_pattern' in _column_names('users'):
        with op.batch_alter_table('users', schema=None) as batch_op:
            batch_op.alter_column(
                'antenna_pattern',
                existing_type=sa.TEXT(),
                type_=sa.LargeBinary(),
                existing_nullable=True,
                postgresql_using='antenna_pattern::bytea',
            )


def downgrade():
    if 'antenna_pattern' in _column_names('users'):
        with op.batch_alter_table('users', schema=None) as batch_op:
            batch_op.alter_column(
                'antenna_pattern',
                existing_type=sa.LargeBinary(),
                type_=sa.TEXT(),
                existing_nullable=True,
                postgresql_using='antenna_pattern::text',
            )
