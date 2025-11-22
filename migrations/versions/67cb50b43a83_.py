"""empty message

Revision ID: 67cb50b43a83
Revises: 01f8c716dd29
Create Date: 2024-05-20 12:37:32.194808

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '67cb50b43a83'
down_revision = '01f8c716dd29'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    column_names = {col['name'] for col in inspector.get_columns('users')}

    if 'rx_height' not in column_names:
        with op.batch_alter_table('users', schema=None) as batch_op:
            batch_op.add_column(sa.Column('rx_height', sa.Float(), nullable=True))


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    column_names = {col['name'] for col in inspector.get_columns('users')}

    if 'rx_height' in column_names:
        with op.batch_alter_table('users', schema=None) as batch_op:
            batch_op.drop_column('rx_height')
