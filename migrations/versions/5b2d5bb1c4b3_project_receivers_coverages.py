"""Persist receivers and coverage snapshots in dedicated tables.

Revision ID: 5b2d5bb1c4b3
Revises: 41084a944409
Create Date: 2025-02-14 15:20:00.000000

"""
from __future__ import annotations

import json
import uuid
from datetime import datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '5b2d5bb1c4b3'
down_revision = '41084a944409'
branch_labels = None
depends_on = None


project_table = sa.table(
    'projects',
    sa.column('id', sa.String(length=36)),
    sa.column('settings', postgresql.JSON(astext_type=sa.Text())),
)

receivers_table = sa.table(
    'project_receivers',
    sa.column('project_id', sa.String(length=36)),
    sa.column('legacy_id', sa.String(128)),
    sa.column('label', sa.String(255)),
    sa.column('latitude', sa.Float),
    sa.column('longitude', sa.Float),
    sa.column('municipality', sa.String(255)),
    sa.column('state', sa.String(64)),
    sa.column('summary', postgresql.JSON(astext_type=sa.Text())),
    sa.column('ibge_code', sa.String(16)),
    sa.column('population', sa.Integer),
    sa.column('population_year', sa.Integer),
    sa.column('profile_asset_id', sa.String(length=36)),
    sa.column('created_at', sa.DateTime(timezone=True)),
    sa.column('updated_at', sa.DateTime(timezone=True)),
)

coverage_table = sa.table(
    'project_coverages',
    sa.column('id', sa.String(length=36)),
    sa.column('project_id', sa.String(length=36)),
    sa.column('engine', sa.String(32)),
    sa.column('generated_at', sa.DateTime(timezone=True)),
    sa.column('payload', postgresql.JSON(astext_type=sa.Text())),
    sa.column('heatmap_asset_id', sa.String(length=36)),
    sa.column('colorbar_asset_id', sa.String(length=36)),
    sa.column('map_snapshot_asset_id', sa.String(length=36)),
    sa.column('summary_asset_id', sa.String(length=36)),
    sa.column('created_at', sa.DateTime(timezone=True)),
    sa.column('updated_at', sa.DateTime(timezone=True)),
)


def _coerce_asset_id(value):
    if not value:
        return None
    try:
        return str(uuid.UUID(str(value)))
    except (ValueError, AttributeError, TypeError):
        return None


def _coerce_datetime(value):
    if not value:
        return datetime.utcnow()
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return datetime.utcnow()


def upgrade():
    op.create_table(
        'project_receivers',
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('legacy_id', sa.String(length=128), nullable=False),
        sa.Column('label', sa.String(length=255), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('municipality', sa.String(length=255), nullable=True),
        sa.Column('state', sa.String(length=64), nullable=True),
        sa.Column('summary', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('ibge_code', sa.String(length=16), nullable=True),
        sa.Column('population', sa.Integer(), nullable=True),
        sa.Column('population_year', sa.Integer(), nullable=True),
        sa.Column('profile_asset_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['profile_asset_id'], ['assets.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('project_id', 'legacy_id')
    )
    op.create_table(
        'project_coverages',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('engine', sa.String(length=32), nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('payload', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('heatmap_asset_id', sa.String(length=36), nullable=True),
        sa.Column('colorbar_asset_id', sa.String(length=36), nullable=True),
        sa.Column('map_snapshot_asset_id', sa.String(length=36), nullable=True),
        sa.Column('summary_asset_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['colorbar_asset_id'], ['assets.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['heatmap_asset_id'], ['assets.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['map_snapshot_asset_id'], ['assets.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['summary_asset_id'], ['assets.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    bind = op.get_bind()
    projects = list(bind.execute(sa.select(project_table.c.id, project_table.c.settings)))

    for project_id, settings in projects:
        if not settings:
            continue
        project_id_str = str(project_id)
        updated_settings = dict(settings)
        receiver_entries = updated_settings.pop('receiverBookmarks', None)
        last_coverage = updated_settings.pop('lastCoverage', None)

        if receiver_entries and isinstance(receiver_entries, list):
            for entry in receiver_entries:
                legacy_id = str(entry.get('id') or uuid.uuid4())
                location = entry.get('location') or {}
                lat = entry.get('lat') or location.get('lat') or location.get('latitude')
                lon = entry.get('lng') or entry.get('lon') or location.get('lng') or location.get('longitude')
                try:
                    lat = float(lat) if lat is not None else None
                except (TypeError, ValueError):
                    lat = None
                try:
                    lon = float(lon) if lon is not None else None
                except (TypeError, ValueError):
                    lon = None
                profile_asset_id = _coerce_asset_id(entry.get('profile_asset_id'))
                bind.execute(
                    receivers_table.insert().values(
                        project_id=project_id_str,
                        legacy_id=legacy_id,
                        label=entry.get('label'),
                        latitude=lat,
                        longitude=lon,
                        municipality=entry.get('municipality') or location.get('municipality'),
                        state=entry.get('state') or location.get('state'),
                        summary=json.loads(json.dumps(entry)),
                        ibge_code=(entry.get('ibge') or {}).get('code'),
                        population=entry.get('population'),
                        population_year=entry.get('population_year'),
                        profile_asset_id=profile_asset_id,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                )

        if last_coverage and isinstance(last_coverage, dict):
            payload = json.loads(json.dumps(last_coverage))
            generated_at = _coerce_datetime(last_coverage.get('generated_at'))
            bind.execute(
                coverage_table.insert().values(
                    id=str(uuid.uuid4()),
                    project_id=project_id_str,
                    engine=last_coverage.get('engine'),
                    generated_at=generated_at,
                    payload=payload,
                    heatmap_asset_id=_coerce_asset_id(last_coverage.get('asset_id')),
                    colorbar_asset_id=_coerce_asset_id(last_coverage.get('colorbar_asset_id')),
                    map_snapshot_asset_id=_coerce_asset_id(last_coverage.get('map_snapshot_asset_id')),
                    summary_asset_id=_coerce_asset_id(last_coverage.get('json_asset_id')),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
            )

        if receiver_entries or last_coverage:
            bind.execute(
                project_table.update()
                .where(project_table.c.id == project_id)
                .values(settings=updated_settings)
            )


def downgrade():
    bind = op.get_bind()
    projects = list(bind.execute(sa.select(project_table.c.id, project_table.c.settings)))

    for project_id, settings in projects:
        updated_settings = dict(settings or {})

        receiver_rows = list(
            bind.execute(
                sa.select(receivers_table.c.legacy_id, receivers_table.c.summary)
                .where(receivers_table.c.project_id == project_id)
            )
        )
        if receiver_rows:
            updated_settings['receiverBookmarks'] = [row.summary for row in receiver_rows if row.summary]
        else:
            updated_settings.pop('receiverBookmarks', None)

        coverage_row = bind.execute(
            sa.select(coverage_table.c.payload)
            .where(coverage_table.c.project_id == project_id)
            .order_by(coverage_table.c.generated_at.desc().nullslast(), coverage_table.c.created_at.desc().nullslast())
            .limit(1)
        ).fetchone()
        if coverage_row and coverage_row.payload:
            updated_settings['lastCoverage'] = coverage_row.payload
        else:
            updated_settings.pop('lastCoverage', None)

        bind.execute(
            project_table.update()
            .where(project_table.c.id == project_id)
            .values(settings=updated_settings)
        )

    op.drop_table('project_coverages')
    op.drop_table('project_receivers')
