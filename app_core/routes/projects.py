from __future__ import annotations

import io
import json
import math
from functools import lru_cache
from pathlib import Path

from flask import (
    Blueprint,
    abort,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
    flash,
)
from flask_login import current_user, login_required
from sqlalchemy.exc import SQLAlchemyError
from PIL import Image

from extensions import db
from app_core.models import Project, Asset, AssetType, CoverageJob, Report, DatasetSource
from app_core.storage import ensure_storage_structure, remove_project_storage, storage_root
from app_core.utils import (
    ensure_unique_slug,
    project_by_slug_or_404,
    project_to_dict,
    projects_to_dict,
    slugify,
)
from app_core.data_acquisition import download_srtm_tile, download_mapbiomas_tile
from app_core.models import CoverageEngine


bp = Blueprint("projects", __name__, url_prefix="/projects")
api_bp = Blueprint("projects_api", __name__, url_prefix="/api/projects")


# ---------------------------------------------------------------------------#
# UI routes                                                                  #
# ---------------------------------------------------------------------------#


@bp.route("/", methods=["GET"])
@login_required
def list_projects():
    projects = (
        current_user.projects.order_by(Project.created_at.desc()).all()
        if hasattr(current_user, "projects")
        else []
    )
    return render_template("projects/index.html", projects=projects)


@bp.route("/new", methods=["GET", "POST"])
@login_required
def new_project():
    error = None
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip() or None
        crs = request.form.get("crs", "EPSG:4326").strip() or "EPSG:4326"
        aoi_raw = request.form.get("aoi_geojson", "").strip()
        aoi_geojson = None

        if not name:
            error = "Informe um nome para o projeto."
        else:
            if aoi_raw:
                try:
                    aoi_geojson = json.loads(aoi_raw)
                except json.JSONDecodeError:
                    error = "GeoJSON inválido. Corrija o conteúdo informado."

        if error is None:
            slug_candidate = slugify(name)
            slug = ensure_unique_slug(current_user.uuid, slug_candidate)
            project = Project(
                user_uuid=current_user.uuid,
                name=name,
                slug=slug,
                description=description,
                aoi_geojson=aoi_geojson,
                crs=crs,
            )
            db.session.add(project)
            try:
                db.session.commit()
            except SQLAlchemyError as exc:
                db.session.rollback()
                error = f"Erro ao criar projeto: {exc}"
            else:
                ensure_storage_structure(str(current_user.uuid), slug)
                flash("Projeto criado com sucesso!", "success")
                return redirect(url_for("projects.view_project", slug=slug))

    return render_template("projects/new.html", error=error)


@bp.route("/<slug>", methods=["GET"])
@login_required
def view_project(slug):
    project = project_by_slug_or_404(slug, current_user.uuid)
    assets = project.assets
    jobs = project.coverage_jobs
    reports = project.reports
    dataset_sources = project.dataset_sources
    return render_template(
        "projects/detail.html",
        project=project,
        assets=assets,
        jobs=jobs,
        reports=reports,
        dataset_sources=dataset_sources,
    )


@bp.route("/<slug>/assets/<asset_id>/preview", methods=["GET"])
@login_required
def asset_preview(slug, asset_id):
    project = project_by_slug_or_404(slug, current_user.uuid)
    asset = Asset.query.filter_by(id=asset_id, project_id=project.id).first()
    if asset is None:
        abort(404)
    file_path = storage_root() / asset.path
    if not file_path.exists():
        abort(404)
    return send_file(file_path, mimetype=asset.mime_type or 'application/octet-stream')


TILE_SIZE = 256


@lru_cache(maxsize=1)
def _empty_tile_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new('RGBA', (TILE_SIZE, TILE_SIZE), (0, 0, 0, 0)).save(buffer, format='PNG')
    return buffer.getvalue()


@lru_cache(maxsize=128)
def _load_heatmap_bytes(path_str: str) -> bytes:
    return Path(path_str).read_bytes()


@lru_cache(maxsize=128)
def _load_summary_payload(path_str: str) -> dict:
    with open(path_str, 'r', encoding='utf-8') as handle:
        return json.load(handle)


def _resolve_summary_path(image_path: Path):
    if image_path.name.endswith('_field.png'):
        candidate = image_path.with_name(image_path.name.replace('_field.png', '_summary.json'))
        if candidate.exists():
            return candidate
    candidate = image_path.with_suffix('.json')
    if candidate.exists():
        return candidate
    stem = image_path.stem.replace('_field', '')
    for option in image_path.parent.glob(f"{stem}*_summary.json"):
        return option
    return None


def _normalize_bounds(bounds):
    if not bounds:
        return None
    try:
        north = float(bounds.get('north'))
        south = float(bounds.get('south'))
        east = float(bounds.get('east'))
        west = float(bounds.get('west'))
    except (TypeError, ValueError, AttributeError):
        return None
    if north < south:
        north, south = south, north
    if east < west:
        east, west = west, east
    if math.isclose(north, south) or math.isclose(east, west):
        return None
    return north, south, east, west


def _tile_bounds(zoom: int, x: int, y: int):
    scale = 2 ** zoom
    lon_left = x / scale * 360.0 - 180.0
    lon_right = (x + 1) / scale * 360.0 - 180.0
    lat_rad_top = math.atan(math.sinh(math.pi * (1 - 2 * y / scale)))
    lat_rad_bottom = math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / scale)))
    lat_top = math.degrees(lat_rad_top)
    lat_bottom = math.degrees(lat_rad_bottom)
    if lat_top < lat_bottom:
        lat_top, lat_bottom = lat_bottom, lat_top
    return {
        'north': lat_top,
        'south': lat_bottom,
        'west': lon_left,
        'east': lon_right,
    }


def _compose_tile_bytes(image_bytes: bytes, coverage_bounds, tile_bounds) -> bytes:
    coverage = _normalize_bounds(coverage_bounds)
    tile = _normalize_bounds(tile_bounds)
    if not coverage or not tile:
        return _empty_tile_bytes()

    cov_north, cov_south, cov_east, cov_west = coverage
    tile_north, tile_south, tile_east, tile_west = tile

    lat_top = min(cov_north, tile_north)
    lat_bottom = max(cov_south, tile_south)
    lon_left = max(cov_west, tile_west)
    lon_right = min(cov_east, tile_east)

    if lat_top <= lat_bottom or lon_left >= lon_right:
        return _empty_tile_bytes()

    lon_span = cov_east - cov_west
    lat_span = cov_north - cov_south
    if lon_span <= 0 or lat_span <= 0:
        return _empty_tile_bytes()

    with Image.open(io.BytesIO(image_bytes)) as img:
        img = img.convert('RGBA')
        width, height = img.size
        x0 = (lon_left - cov_west) / lon_span * width
        x1 = (lon_right - cov_west) / lon_span * width
        y0 = (cov_north - lat_top) / lat_span * height
        y1 = (cov_north - lat_bottom) / lat_span * height

        x0 = max(0.0, min(width, x0))
        x1 = max(0.0, min(width, x1))
        y0 = max(0.0, min(height, y0))
        y1 = max(0.0, min(height, y1))

        if x1 <= x0 or y1 <= y0:
            return _empty_tile_bytes()

        patch = img.crop((x0, y0, x1, y1))

    tile_lon_span = tile_east - tile_west
    tile_lat_span = tile_north - tile_south
    if tile_lon_span <= 0 or tile_lat_span <= 0:
        return _empty_tile_bytes()

    tile_x0 = (lon_left - tile_west) / tile_lon_span * TILE_SIZE
    tile_x1 = (lon_right - tile_west) / tile_lon_span * TILE_SIZE
    tile_y0 = (tile_north - lat_top) / tile_lat_span * TILE_SIZE
    tile_y1 = (tile_north - lat_bottom) / tile_lat_span * TILE_SIZE

    tile_x0 = max(0.0, min(TILE_SIZE, tile_x0))
    tile_x1 = max(0.0, min(TILE_SIZE, tile_x1))
    tile_y0 = max(0.0, min(TILE_SIZE, tile_y0))
    tile_y1 = max(0.0, min(TILE_SIZE, tile_y1))

    tile_x0_int = max(0, min(TILE_SIZE - 1, int(math.floor(tile_x0))))
    tile_y0_int = max(0, min(TILE_SIZE - 1, int(math.floor(tile_y0))))
    tile_x1_int = max(tile_x0_int + 1, min(TILE_SIZE, int(math.ceil(tile_x1))))
    tile_y1_int = max(tile_y0_int + 1, min(TILE_SIZE, int(math.ceil(tile_y1))))

    dest_w = tile_x1_int - tile_x0_int
    dest_h = tile_y1_int - tile_y0_int
    if dest_w <= 0 or dest_h <= 0:
        return _empty_tile_bytes()

    patch = patch.resize((dest_w, dest_h), resample=Image.BILINEAR)
    tile_img = Image.new('RGBA', (TILE_SIZE, TILE_SIZE), (0, 0, 0, 0))
    tile_img.paste(patch, (tile_x0_int, tile_y0_int), mask=patch)
    output = io.BytesIO()
    tile_img.save(output, format='PNG')
    return output.getvalue()


def _tile_response(tile_bytes: bytes):
    buffer = io.BytesIO(tile_bytes)
    buffer.seek(0)
    response = send_file(buffer, mimetype='image/png')
    response.headers['Cache-Control'] = 'public, max-age=86400'
    return response


@bp.route("/<slug>/assets/<asset_id>/tiles/<int:z>/<int:x>/<int:y>.png", methods=["GET"])
@login_required
def coverage_tile(slug, asset_id, z, x, y):
    if z < 0 or z > 22:
        abort(404)

    project = project_by_slug_or_404(slug, current_user.uuid)
    asset = (
        Asset.query.filter_by(
            id=asset_id,
            project_id=project.id,
            type=AssetType.heatmap,
        )
        .first()
    )
    if asset is None:
        abort(404)

    image_path = storage_root() / asset.path
    if not image_path.exists():
        abort(404)

    scale = 1 << z
    wrapped_x = x % scale
    if y < 0 or y >= scale:
        return _tile_response(_empty_tile_bytes())

    summary_path = _resolve_summary_path(image_path)
    coverage_bounds = None
    if summary_path and summary_path.exists():
        try:
            summary_payload = _load_summary_payload(str(summary_path))
            coverage_bounds = summary_payload.get('bounds')
        except (OSError, json.JSONDecodeError):
            coverage_bounds = None

    tile_bounds = _tile_bounds(z, wrapped_x, y)
    try:
        image_bytes = _load_heatmap_bytes(str(image_path))
        tile_bytes = _compose_tile_bytes(image_bytes, coverage_bounds, tile_bounds)
    except OSError:
        tile_bytes = _empty_tile_bytes()

    return _tile_response(tile_bytes)


@bp.route("/<slug>/coverage", methods=["GET"])
@login_required
def project_coverage_redirect(slug):
    project_by_slug_or_404(slug, current_user.uuid)
    return redirect(url_for("ui.calcular_cobertura", project=slug))


@bp.route("/<slug>/update", methods=["POST"])
@login_required
def update_project(slug):
    project = project_by_slug_or_404(slug, current_user.uuid)
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip() or None
    crs = request.form.get("crs", "").strip() or project.crs
    aoi_raw = request.form.get("aoi_geojson", "").strip()

    if name:
        if name != project.name:
            candidate = slugify(name)
            if candidate != project.slug:
                project.slug = ensure_unique_slug(project.user_uuid, candidate)
        project.name = name
    project.description = description
    project.crs = crs
    if aoi_raw:
        try:
            project.aoi_geojson = json.loads(aoi_raw)
        except json.JSONDecodeError:
            flash("GeoJSON inválido. Mantendo valor anterior.", "warning")
    else:
        project.aoi_geojson = None

    try:
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        flash(f"Erro ao atualizar projeto: {exc}", "error")
    else:
        ensure_storage_structure(str(project.user_uuid), project.slug)
        flash("Projeto atualizado com sucesso!", "success")
    return redirect(url_for("projects.view_project", slug=project.slug))


@bp.route("/<slug>/delete", methods=["POST"])
@login_required
def delete_project(slug):
    project = project_by_slug_or_404(slug, current_user.uuid)
    remove_project_storage(str(project.user_uuid), project.slug)
    db.session.delete(project)
    try:
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        flash(f"Erro ao remover projeto: {exc}", "error")
        return redirect(url_for("projects.view_project", slug=slug))
    flash("Projeto removido.", "success")
    return redirect(url_for("projects.list_projects"))


# ---------------------------------------------------------------------------#
# API routes                                                                 #
# ---------------------------------------------------------------------------#


@api_bp.route("/", methods=["GET"])
@login_required
def api_list_projects():
    projects = (
        current_user.projects.order_by(Project.created_at.desc()).all()
        if hasattr(current_user, "projects")
        else []
    )
    return jsonify({"projects": projects_to_dict(projects)})


@api_bp.route("/", methods=["POST"])
@login_required
def api_create_project():
    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Campo 'name' é obrigatório."}), 400

    description = (payload.get("description") or "").strip() or None
    crs = (payload.get("crs") or "EPSG:4326").strip() or "EPSG:4326"
    aoi_geojson = payload.get("aoi_geojson")

    slug_candidate = slugify(name)
    slug = ensure_unique_slug(current_user.uuid, slug_candidate)

    project = Project(
        user_uuid=current_user.uuid,
        name=name,
        slug=slug,
        description=description,
        aoi_geojson=aoi_geojson,
        crs=crs,
    )
    db.session.add(project)
    try:
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        return jsonify({"error": f"Não foi possível criar o projeto: {exc}"}), 500

    ensure_storage_structure(str(current_user.uuid), slug)
    response = jsonify({"project": project_to_dict(project)})
    response.status_code = 201
    response.headers["Location"] = url_for("projects_api.api_get_project", slug=slug)
    return response


def _asset_to_dict(asset: Asset) -> dict:
    return {
        "id": str(asset.id),
        "type": asset.type.value if asset.type else None,
        "path": asset.path,
        "mime_type": asset.mime_type,
        "byte_size": asset.byte_size,
        "checksum_sha256": asset.checksum_sha256,
        "meta": asset.meta,
        "created_at": asset.created_at.isoformat() if asset.created_at else None,
    }


def _job_to_dict(job: CoverageJob) -> dict:
    return {
        "id": str(job.id),
        "engine": job.engine.value if job.engine else None,
        "status": job.status.value if job.status else None,
        "inputs": job.inputs,
        "metrics": job.metrics,
        "outputs_asset_id": str(job.outputs_asset_id) if job.outputs_asset_id else None,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
        "created_at": job.created_at.isoformat() if job.created_at else None,
    }


def _report_to_dict(report: Report) -> dict:
    return {
        "id": str(report.id),
        "title": report.title,
        "description": report.description,
        "template_name": report.template_name,
        "json_payload": report.json_payload,
        "pdf_asset_id": str(report.pdf_asset_id) if report.pdf_asset_id else None,
        "created_at": report.created_at.isoformat() if report.created_at else None,
    }


def _dataset_source_to_dict(dataset: DatasetSource) -> dict:
    return {
        "id": str(dataset.id),
        "kind": dataset.kind.value if dataset.kind else None,
        "locator": dataset.locator,
        "time_range": dataset.time_range,
        "notes": dataset.notes,
        "created_at": dataset.created_at.isoformat() if dataset.created_at else None,
    }


@api_bp.route("/<slug>", methods=["GET"])
@login_required
def api_get_project(slug):
    project = project_by_slug_or_404(slug, current_user.uuid)
    data = project_to_dict(project)
    data["assets"] = [_asset_to_dict(asset) for asset in project.assets]
    data["coverage_jobs"] = [_job_to_dict(job) for job in project.coverage_jobs]
    data["reports"] = [_report_to_dict(report) for report in project.reports]
    data["dataset_sources"] = [
        _dataset_source_to_dict(ds) for ds in project.dataset_sources
    ]
    return jsonify({"project": data})


@api_bp.route("/<slug>", methods=["PATCH"])
@login_required
def api_update_project(slug):
    project = project_by_slug_or_404(slug, current_user.uuid)
    payload = request.get_json(silent=True) or {}

    if "name" in payload:
        name = (payload.get("name") or "").strip()
        if not name:
            return jsonify({"error": "Campo 'name' não pode ser vazio."}), 400
        if name != project.name:
            candidate = slugify(name)
            if candidate != project.slug:
                project.slug = ensure_unique_slug(project.user_uuid, candidate)
        project.name = name

    if "description" in payload:
        project.description = (payload.get("description") or "").strip() or None

    if "crs" in payload:
        project.crs = (payload.get("crs") or project.crs).strip() or project.crs

    if "aoi_geojson" in payload:
        project.aoi_geojson = payload.get("aoi_geojson")

    try:
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        return jsonify({"error": f"Não foi possível atualizar o projeto: {exc}"}), 500

    ensure_storage_structure(str(project.user_uuid), project.slug)
    return jsonify({"project": project_to_dict(project)})


@api_bp.route("/<slug>", methods=["DELETE"])
@login_required
def api_delete_project(slug):
    project = project_by_slug_or_404(slug, current_user.uuid)
    remove_project_storage(str(project.user_uuid), project.slug)
    db.session.delete(project)
    try:
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        return jsonify({"error": f"Não foi possível remover o projeto: {exc}"}), 500
    return jsonify({"status": "deleted"})


@api_bp.route("/<slug>/data/dem", methods=["POST"])
@login_required
def api_acquire_dem(slug):
    project = project_by_slug_or_404(slug, current_user.uuid)
    payload = request.get_json(silent=True) or {}
    lat = payload.get("lat")
    lon = payload.get("lon")

    if not lat or not lon:
        return jsonify({"error": "Latitude 'lat' and longitude 'lon' are required."}), 400

    try:
        lat = float(lat)
        lon = float(lon)
    except (ValueError, TypeError):
        return jsonify({"error": "Latitude 'lat' and longitude 'lon' must be numbers."}), 400

    asset = download_srtm_tile(project, lat, lon)

    if asset:
        return jsonify({"asset": _asset_to_dict(asset)}), 201
    else:
        return jsonify({"error": "Failed to acquire DEM tile."}), 500


@api_bp.route("/<slug>/data/lulc", methods=["POST"])
@login_required
def api_acquire_lulc(slug):
    project = project_by_slug_or_404(slug, current_user.uuid)
    payload = request.get_json(silent=True) or {}
    year = payload.get("year")

    if not year:
        return jsonify({"error": "Year is required."}), 400

    try:
        year = int(year)
    except (ValueError, TypeError):
        return jsonify({"error": "Year must be a number."}), 400

    asset = download_mapbiomas_tile(project, year)

    if asset:
        return jsonify({"asset": _asset_to_dict(asset)}), 201
    else:
        return jsonify({"error": "Failed to acquire LULC tile."}), 500


@api_bp.route("/<slug>/jobs", methods=["POST"])
@login_required
def api_submit_job(slug):
    project = project_by_slug_or_404(slug, current_user.uuid)
    payload = request.get_json(silent=True) or {}
    engine = payload.get("engine")
    inputs = payload.get("inputs")

    if not engine or not inputs:
        return jsonify({"error": "Engine and inputs are required."}), 400

    try:
        engine_enum = CoverageEngine(engine)
    except ValueError:
        return jsonify({"error": f"Invalid engine. Must be one of: {[e.value for e in CoverageEngine]}"}), 400

    job = CoverageJob(
        project_id=project.id,
        engine=engine_enum,
        inputs=inputs,
    )
    db.session.add(job)
    try:
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        return jsonify({"error": f"Failed to create job: {exc}"}), 500

    # TODO: Trigger background worker here

    response = jsonify({"job": _job_to_dict(job)})
    response.status_code = 202 # Accepted
    response.headers["Location"] = url_for("projects_api.api_get_job", slug=slug, job_id=job.id)
    return response


@api_bp.route("/<slug>/jobs/<job_id>", methods=["GET"])
@login_required
def api_get_job(slug, job_id):
    project = project_by_slug_or_404(slug, current_user.uuid)
    job = CoverageJob.query.filter_by(id=job_id, project_id=project.id).first()
    if not job:
        return jsonify({"error": "Job not found."}), 404

    return jsonify({"job": _job_to_dict(job)})
