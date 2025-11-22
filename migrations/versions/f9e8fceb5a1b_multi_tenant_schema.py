"""multi-tenant schema

Revision ID: f9e8fceb5a1b
Revises: cc3d3ad4f9a1
Create Date: 2025-02-14 17:25:00.000000

"""
from __future__ import annotations

import re
import unicodedata
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy import exc as sa_exc
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import table, column


# revision identifiers, used by Alembic.
revision = "f9e8fceb5a1b"
down_revision = "cc3d3ad4f9a1"
branch_labels = None
depends_on = None


def _table_exists(bind, table_name: str) -> bool:
    inspector = sa.inspect(bind)
    try:
        return inspector.has_table(table_name)
    except AttributeError:
        return table_name in inspector.get_table_names()


def _index_exists(bind, table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(bind)
    try:
        indexes = inspector.get_indexes(table_name)
    except sa_exc.NoSuchTableError:
        return False
    return any(idx["name"] == index_name for idx in indexes)


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    is_postgres = dialect == "postgresql"
    inspector = sa.inspect(bind)
    user_columns = {col["name"] for col in inspector.get_columns("users")}

    json_type = postgresql.JSONB() if is_postgres else sa.JSON()
    time_range_type = postgresql.DATERANGE() if is_postgres else sa.String(length=255)

    if "uuid" not in user_columns:
        op.add_column(
            "users",
            sa.Column("uuid", sa.String(length=36), nullable=True),
        )
    if "is_active" not in user_columns:
        op.add_column(
            "users",
            sa.Column(
                "is_active",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            ),
        )
    if "is_email_confirmed" not in user_columns:
        op.add_column(
            "users",
            sa.Column(
                "is_email_confirmed",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
        )
    if "created_at" not in user_columns:
        op.add_column(
            "users",
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )
    if "updated_at" not in user_columns:
        op.add_column(
            "users",
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )

    users_table = table(
        "users",
        column("id", sa.Integer),
        column("uuid", sa.String(length=36)),
    )
    rows = list(bind.execute(sa.select(users_table.c.id, users_table.c.uuid)))
    for row in rows:
        if row.uuid:
            continue
        bind.execute(
            users_table.update()
            .where(users_table.c.id == row.id)
            .values(uuid=str(uuid.uuid4()))
        )

    if "uuid" in (user_columns | {"uuid"}):
        op.alter_column("users", "uuid", nullable=False)

    inspector = sa.inspect(bind)
    existing_uniques = {uc["name"] for uc in inspector.get_unique_constraints("users")}
    if "uq_users_uuid" not in existing_uniques:
        op.create_unique_constraint("uq_users_uuid", "users", ["uuid"])

    existing_indexes = {idx["name"] for idx in inspector.get_indexes("users")}
    if "ix_users_uuid" not in existing_indexes:
        op.create_index("ix_users_uuid", "users", ["uuid"], unique=False)

    if is_postgres:
        asset_type_enum = postgresql.ENUM(
            "dem",
            "lulc",
            "building_footprints",
            "mesh3d",
            "heatmap",
            "pdf",
            "csv",
            "png",
            "json",
            "other",
            name="asset_type",
            create_type=False,
        )
        coverage_engine_enum = postgresql.ENUM(
            "p1546", "itm", "pycraf", "rt3d", name="coverage_engine", create_type=False
        )
        coverage_status_enum = postgresql.ENUM(
            "queued",
            "running",
            "succeeded",
            "failed",
            "canceled",
            name="coverage_job_status",
            create_type=False,
        )
        dataset_source_kind_enum = postgresql.ENUM(
            "SRTM",
            "TOPODATA",
            "CGLS_LC100",
            "MAPBIOMAS",
            "OSM",
            "CADASTRE",
            "GEE",
            "CUSTOM",
            name="dataset_source_kind",
            create_type=False,
        )
    else:
        asset_type_enum = sa.Enum(
            "dem",
            "lulc",
            "building_footprints",
            "mesh3d",
            "heatmap",
            "pdf",
            "csv",
            "png",
            "json",
            "other",
            name="asset_type",
        )
        coverage_engine_enum = sa.Enum(
            "p1546", "itm", "pycraf", "rt3d", name="coverage_engine"
        )
        coverage_status_enum = sa.Enum(
            "queued",
            "running",
            "succeeded",
            "failed",
            "canceled",
            name="coverage_job_status",
        )
        dataset_source_kind_enum = sa.Enum(
            "SRTM",
            "TOPODATA",
            "CGLS_LC100",
            "MAPBIOMAS",
            "OSM",
            "CADASTRE",
            "GEE",
            "CUSTOM",
            name="dataset_source_kind",
        )

    if is_postgres:
        for enum_type in (
            asset_type_enum,
            coverage_engine_enum,
            coverage_status_enum,
            dataset_source_kind_enum,
        ):
            enum_type.create(bind, checkfirst=True)

    created_projects_table = False
    if not _table_exists(bind, "projects"):
        op.create_table(
            "projects",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("user_uuid", sa.String(length=36), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("slug", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("aoi_geojson", json_type, nullable=True),
            sa.Column(
                "crs",
                sa.String(length=32),
                nullable=False,
                server_default=sa.text("'EPSG:4326'"),
            ),
            sa.Column("settings", json_type, nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.ForeignKeyConstraint(
                ["user_uuid"],
                ["users.uuid"],
                name="fk_projects_user_uuid_users",
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_uuid", "slug", name="uq_projects_user_slug"),
        )
        created_projects_table = True
    if created_projects_table or not _index_exists(bind, "projects", "ix_projects_user_uuid"):
        op.create_index("ix_projects_user_uuid", "projects", ["user_uuid"])

    created_assets_table = False
    if not _table_exists(bind, "assets"):
        op.create_table(
            "assets",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("project_id", sa.String(length=36), nullable=False),
            sa.Column("type", asset_type_enum, nullable=False),
            sa.Column("path", sa.String(length=512), nullable=False),
            sa.Column("mime_type", sa.String(length=128), nullable=True),
            sa.Column("byte_size", sa.BigInteger(), nullable=True),
            sa.Column("checksum_sha256", sa.String(length=64), nullable=True),
            sa.Column("meta", json_type, nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.ForeignKeyConstraint(
                ["project_id"],
                ["projects.id"],
                name="fk_assets_project_id_projects",
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        created_assets_table = True
    if created_assets_table or not _index_exists(bind, "assets", "ix_assets_project_id"):
        op.create_index("ix_assets_project_id", "assets", ["project_id"])

    created_coverage_jobs_table = False
    if not _table_exists(bind, "coverage_jobs"):
        op.create_table(
            "coverage_jobs",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("project_id", sa.String(length=36), nullable=False),
            sa.Column(
                "status",
                coverage_status_enum,
                nullable=False,
                server_default="queued",
            ),
            sa.Column("engine", coverage_engine_enum, nullable=False),
            sa.Column("inputs", json_type, nullable=False),
            sa.Column("metrics", json_type, nullable=True),
            sa.Column("outputs_asset_id", sa.String(length=36), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.ForeignKeyConstraint(
                ["outputs_asset_id"],
                ["assets.id"],
                name="fk_coverage_jobs_outputs_asset_id_assets",
                ondelete="SET NULL",
            ),
            sa.ForeignKeyConstraint(
                ["project_id"],
                ["projects.id"],
                name="fk_coverage_jobs_project_id_projects",
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        created_coverage_jobs_table = True
    if created_coverage_jobs_table or not _index_exists(bind, "coverage_jobs", "ix_coverage_jobs_project_id"):
        op.create_index(
            "ix_coverage_jobs_project_id", "coverage_jobs", ["project_id"]
        )
    if created_coverage_jobs_table or not _index_exists(bind, "coverage_jobs", "ix_coverage_jobs_outputs_asset_id"):
        op.create_index(
            "ix_coverage_jobs_outputs_asset_id",
            "coverage_jobs",
            ["outputs_asset_id"],
        )

    created_reports_table = False
    if not _table_exists(bind, "reports"):
        op.create_table(
            "reports",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("project_id", sa.String(length=36), nullable=False),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("template_name", sa.String(length=255), nullable=False),
            sa.Column("json_payload", json_type, nullable=False),
            sa.Column("pdf_asset_id", sa.String(length=36), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.ForeignKeyConstraint(
                ["pdf_asset_id"],
                ["assets.id"],
                name="fk_reports_pdf_asset_id_assets",
                ondelete="SET NULL",
            ),
            sa.ForeignKeyConstraint(
                ["project_id"],
                ["projects.id"],
                name="fk_reports_project_id_projects",
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        created_reports_table = True
    if created_reports_table or not _index_exists(bind, "reports", "ix_reports_project_id"):
        op.create_index("ix_reports_project_id", "reports", ["project_id"])
    if created_reports_table or not _index_exists(bind, "reports", "ix_reports_pdf_asset_id"):
        op.create_index("ix_reports_pdf_asset_id", "reports", ["pdf_asset_id"])

    created_dataset_sources_table = False
    if not _table_exists(bind, "dataset_sources"):
        op.create_table(
            "dataset_sources",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("project_id", sa.String(length=36), nullable=False),
            sa.Column("kind", dataset_source_kind_enum, nullable=False),
            sa.Column("locator", json_type, nullable=True),
            sa.Column("time_range", time_range_type, nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.ForeignKeyConstraint(
                ["project_id"],
                ["projects.id"],
                name="fk_dataset_sources_project_id_projects",
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        created_dataset_sources_table = True
    if created_dataset_sources_table or not _index_exists(bind, "dataset_sources", "ix_dataset_sources_project_id"):
        op.create_index("ix_dataset_sources_project_id", "dataset_sources", ["project_id"])

    if created_projects_table:
        users_full = table(
            "users",
            column("uuid", sa.String(length=36)),
            column("username", sa.String()),
            column("email", sa.String()),
        )
        projects_table = table(
            "projects",
            column("id", sa.String(length=36)),
            column("user_uuid", sa.String(length=36)),
            column("name", sa.String(length=255)),
            column("slug", sa.String(length=255)),
            column("description", sa.Text()),
        )

        def _slugify(value: str) -> str:
            if not value:
                return ""
            value = (
                unicodedata.normalize("NFKD", value)
                .encode("ascii", "ignore")
                .decode("ascii")
            )
            value = re.sub(r"[^\w\s-]", "", value).strip().lower()
            value = re.sub(r"[-\s]+", "-", value)
            return value

        user_slugs: dict[str, set[str]] = {}
        for row in bind.execute(sa.select(users_full.c.uuid, users_full.c.username, users_full.c.email)):
            user_uuid = row.uuid
            base_label = row.username or (row.email.split("@")[0] if row.email else "projeto-atx")
            slug_candidate = _slugify(base_label) or f"project-{uuid.uuid4().hex[:8]}"
            per_user = user_slugs.setdefault(user_uuid, set())
            slug = slug_candidate
            counter = 2
            while slug in per_user:
                slug = f"{slug_candidate}-{counter}"
                counter += 1
            per_user.add(slug)
            bind.execute(
                projects_table.insert().values(
                    id=str(uuid.uuid4()),
                    user_uuid=user_uuid,
                    name=f"Projeto de {base_label}",
                    slug=slug,
                    description="Projeto padrão criado automaticamente.",
                )
            )


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    is_postgres = dialect == "postgresql"
    inspector = sa.inspect(bind)
    user_columns = {col["name"] for col in inspector.get_columns("users")}
    unique_names = {uc["name"] for uc in inspector.get_unique_constraints("users")}
    index_names = {idx["name"] for idx in inspector.get_indexes("users")}

    if _index_exists(bind, "dataset_sources", "ix_dataset_sources_project_id"):
        op.drop_index("ix_dataset_sources_project_id", table_name="dataset_sources")
    if _table_exists(bind, "dataset_sources"):
        op.drop_table("dataset_sources")

    if _index_exists(bind, "reports", "ix_reports_pdf_asset_id"):
        op.drop_index("ix_reports_pdf_asset_id", table_name="reports")
    if _index_exists(bind, "reports", "ix_reports_project_id"):
        op.drop_index("ix_reports_project_id", table_name="reports")
    if _table_exists(bind, "reports"):
        op.drop_table("reports")

    if _index_exists(bind, "coverage_jobs", "ix_coverage_jobs_outputs_asset_id"):
        op.drop_index(
            "ix_coverage_jobs_outputs_asset_id", table_name="coverage_jobs"
        )
    if _index_exists(bind, "coverage_jobs", "ix_coverage_jobs_project_id"):
        op.drop_index("ix_coverage_jobs_project_id", table_name="coverage_jobs")
    if _table_exists(bind, "coverage_jobs"):
        op.drop_table("coverage_jobs")

    if _index_exists(bind, "assets", "ix_assets_project_id"):
        op.drop_index("ix_assets_project_id", table_name="assets")
    if _table_exists(bind, "assets"):
        op.drop_table("assets")

    if _index_exists(bind, "projects", "ix_projects_user_uuid"):
        op.drop_index("ix_projects_user_uuid", table_name="projects")
    if _table_exists(bind, "projects"):
        op.drop_table("projects")

    if is_postgres:
        dataset_source_kind_enum = postgresql.ENUM(
            "SRTM",
            "TOPODATA",
            "CGLS_LC100",
            "MAPBIOMAS",
            "OSM",
            "CADASTRE",
            "GEE",
            "CUSTOM",
            name="dataset_source_kind",
            create_type=False,
        )
        coverage_status_enum = postgresql.ENUM(
            "queued",
            "running",
            "succeeded",
            "failed",
            "canceled",
            name="coverage_job_status",
            create_type=False,
        )
        coverage_engine_enum = postgresql.ENUM(
            "p1546", "itm", "pycraf", "rt3d", name="coverage_engine", create_type=False
        )
        asset_type_enum = postgresql.ENUM(
            "dem",
            "lulc",
            "building_footprints",
            "mesh3d",
            "heatmap",
            "pdf",
            "csv",
            "png",
            "json",
            "other",
            name="asset_type",
            create_type=False,
        )

        dataset_source_kind_enum.drop(bind, checkfirst=True)
        coverage_status_enum.drop(bind, checkfirst=True)
        coverage_engine_enum.drop(bind, checkfirst=True)
        asset_type_enum.drop(bind, checkfirst=True)

    if "uq_users_uuid" in unique_names:
        op.drop_constraint("uq_users_uuid", "users", type_="unique")
    if "ix_users_uuid" in index_names:
        op.drop_index("ix_users_uuid", table_name="users")
    if "updated_at" in user_columns:
        op.drop_column("users", "updated_at")
    if "created_at" in user_columns:
        op.drop_column("users", "created_at")
    if "is_email_confirmed" in user_columns:
        op.drop_column("users", "is_email_confirmed")
    if "is_active" in user_columns:
        op.drop_column("users", "is_active")
    if "uuid" in user_columns:
        op.drop_column("users", "uuid")
