"""empty message

Revision ID: caf3c010faf5
Revises: 67cb50b43a83
Create Date: 2024-05-20 13:10:27.692648

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'caf3c010faf5'
down_revision = '67cb50b43a83'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    column_names = {col['name'] for col in inspector.get_columns('users')}

    if 'rx_gain' not in column_names:
        with op.batch_alter_table('users', schema=None) as batch_op:
            batch_op.add_column(sa.Column('rx_gain', sa.Float(), nullable=True))


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    column_names = {col['name'] for col in inspector.get_columns('users')}

    if 'rx_gain' in column_names:
        with op.batch_alter_table('users', schema=None) as batch_op:
            batch_op.drop_column('rx_gain')
