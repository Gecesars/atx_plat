"""empty message

Revision ID: 41084a944409
Revises: afbf0bae9d6e
Create Date: 2024-05-14 13:44:31.965339

"""
from alembic import op
import sqlalchemy as sa


def _column_names(table_name: str):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {col['name'] for col in inspector.get_columns(table_name)}


# revision identifiers, used by Alembic.
revision = '41084a944409'
down_revision = 'afbf0bae9d6e'
branch_labels = None
depends_on = None


def upgrade():
    column_names = _column_names('users')
    with op.batch_alter_table('users', schema=None) as batch_op:
        if 'cobertura_img' not in column_names:
            batch_op.add_column(sa.Column('cobertura_img', sa.LargeBinary(), nullable=True))
        if 'cobertura_img_' in column_names:
            batch_op.drop_column('cobertura_img_')


def downgrade():
    column_names = _column_names('users')
    with op.batch_alter_table('users', schema=None) as batch_op:
        if 'cobertura_img_' not in column_names:
            batch_op.add_column(sa.Column('cobertura_img_', sa.BLOB(), nullable=True))
        if 'cobertura_img' in column_names:
            batch_op.drop_column('cobertura_img')
