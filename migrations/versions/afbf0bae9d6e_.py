"""empty message

Revision ID: afbf0bae9d6e
Revises: 4d5065a12a57
Create Date: 2024-05-14 13:05:24.362354

"""
from alembic import op
import sqlalchemy as sa


def _column_names(table_name: str):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {col['name'] for col in inspector.get_columns(table_name)}


# revision identifiers, used by Alembic.
revision = 'afbf0bae9d6e'
down_revision = '4d5065a12a57'
branch_labels = None
depends_on = None


def upgrade():
    column_names = _column_names('users')
    with op.batch_alter_table('users', schema=None) as batch_op:
        if 'antenna_pattern_img_dia_H' not in column_names:
            batch_op.add_column(sa.Column('antenna_pattern_img_dia_H', sa.LargeBinary(), nullable=True))
        if 'antenna_pattern_img_dia_V' not in column_names:
            batch_op.add_column(sa.Column('antenna_pattern_img_dia_V', sa.LargeBinary(), nullable=True))
        if 'cobertura_img_' not in column_names:
            batch_op.add_column(sa.Column('cobertura_img_', sa.LargeBinary(), nullable=True))
        if 'perfil_img' not in column_names:
            batch_op.add_column(sa.Column('perfil_img', sa.LargeBinary(), nullable=True))


def downgrade():
    column_names = _column_names('users')
    with op.batch_alter_table('users', schema=None) as batch_op:
        if 'perfil_img' in column_names:
            batch_op.drop_column('perfil_img')
        if 'cobertura_img_' in column_names:
            batch_op.drop_column('cobertura_img_')
        if 'antenna_pattern_img_dia_V' in column_names:
            batch_op.drop_column('antenna_pattern_img_dia_V')
        if 'antenna_pattern_img_dia_H' in column_names:
            batch_op.drop_column('antenna_pattern_img_dia_H')
