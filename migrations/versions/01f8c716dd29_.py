"""empty message

Revision ID: 01f8c716dd29
Revises: 41084a944409
Create Date: 2024-05-14 14:34:12.145170

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '01f8c716dd29'
down_revision = '41084a944409'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    column_names = {col['name'] for col in inspector.get_columns('users')}

    if 'notes' not in column_names:
        with op.batch_alter_table('users', schema=None) as batch_op:
            batch_op.add_column(sa.Column('notes', sa.Text(), nullable=True))


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    column_names = {col['name'] for col in inspector.get_columns('users')}

    if 'notes' in column_names:
        with op.batch_alter_table('users', schema=None) as batch_op:
            batch_op.drop_column('notes')
