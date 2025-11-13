"""add regulatory module tables

Revision ID: 1e4fa8cd5acb
Revises: 098cfb467e49, cc3d3ad4f9a1
Create Date: 2025-11-08 06:05:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = '1e4fa8cd5acb'
down_revision = ('098cfb467e49', 'cc3d3ad4f9a1')
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'regulatory_reports',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('status', sa.Enum('draft', 'pending', 'validated', 'failed', 'generated', name='reg_report_status', native_enum=False), nullable=False, server_default='draft'),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('validation_summary', sa.JSON(), nullable=True),
        sa.Column('output_pdf_path', sa.String(length=512), nullable=True),
        sa.Column('output_zip_path', sa.String(length=512), nullable=True),
        sa.Column('logs', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'slug', name='uq_reg_reports_project_slug')
    )
    op.create_index('ix_reg_reports_project_id', 'regulatory_reports', ['project_id'])

    op.create_table(
        'regulatory_attachments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('report_id', sa.String(length=36), nullable=False),
        sa.Column('type', sa.Enum(
            'art_profissional',
            'decea_protocolo',
            'rni_relatorio',
            'homologacao',
            'hrp_vrp',
            'laudo_vistoria',
            'custom',
            name='reg_attachment_type',
            native_enum=False,
        ), nullable=False),
        sa.Column('path', sa.String(length=512), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('mime_type', sa.String(length=128), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['report_id'], ['regulatory_reports.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_reg_attachments_report_id', 'regulatory_attachments', ['report_id'])

    op.create_table(
        'regulatory_validations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('report_id', sa.String(length=36), nullable=False),
        sa.Column('pillar', sa.Enum('decea', 'rni', 'servico', 'sarc', name='reg_pillar', native_enum=False), nullable=False),
        sa.Column('status', sa.Enum('approved', 'attention', 'blocked', name='reg_validation_status', native_enum=False), nullable=False),
        sa.Column('messages', sa.JSON(), nullable=False),
        sa.Column('metrics', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['report_id'], ['regulatory_reports.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_reg_validations_report_id', 'regulatory_validations', ['report_id'])


def downgrade():
    op.drop_index('ix_reg_validations_report_id', table_name='regulatory_validations')
    op.drop_table('regulatory_validations')

    op.drop_index('ix_reg_attachments_report_id', table_name='regulatory_attachments')
    op.drop_table('regulatory_attachments')

    op.drop_index('ix_reg_reports_project_id', table_name='regulatory_reports')
    op.drop_table('regulatory_reports')
