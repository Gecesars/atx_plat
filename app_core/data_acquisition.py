
import os
import math
from datetime import datetime
from pathlib import Path

import requests
from astropy import units as u
from flask import current_app
from pycraf import pathprof

from .models import db, Asset, DatasetSource, DatasetSourceKind
from .storage import get_project_asset_path, ensure_project_path_exists, storage_root

MAPBIOMAS_AVAILABLE_YEARS = list(range(1985, 2024))
_MAPBIOMAS_DEFAULT_YEAR = MAPBIOMAS_AVAILABLE_YEARS[-1]
MAPBIOMAS_BASE_URL = "https://storage.googleapis.com/mapbiomas-public/initiatives/brasil/collection_10/lulc/coverage"


def _normalize_mapbiomas_year(year):
    if not MAPBIOMAS_AVAILABLE_YEARS:
        return None
    if year is None:
        return _MAPBIOMAS_DEFAULT_YEAR
    try:
        year = int(year)
    except (TypeError, ValueError):
        return _MAPBIOMAS_DEFAULT_YEAR
    min_year = MAPBIOMAS_AVAILABLE_YEARS[0]
    max_year = MAPBIOMAS_AVAILABLE_YEARS[-1]
    if year < min_year:
        return min_year
    if year > max_year:
        return max_year
    return year


def global_srtm_dir() -> Path:
    """
    Returns the shared SRTM directory (../SRTM relative to the project root).
    """
    base = Path(current_app.root_path).parent / "SRTM"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _rehydrate_asset(
    project,
    asset_type,
    filename,
    source_kind,
    notes,
    meta,
    size=None,
    locator=None,
    mime_type='application/octet-stream',
):
    """Cria registros de Source/Asset quando o arquivo já existe localmente."""
    try:
        source = DatasetSource(
            project_id=project.id,
            kind=source_kind,
            locator=locator or {},
            notes=notes,
        )
        db.session.add(source)
        db.session.flush()
    except Exception:
        db.session.rollback()
        current_app.logger.warning("Não foi possível registrar fonte %s para %s", source_kind, filename)
        return None

    rel_path = get_project_asset_path(project, asset_type, filename)
    asset = Asset(
        project_id=project.id,
        type=asset_type,
        path=rel_path,
        mime_type=mime_type,
        byte_size=size,
        meta=meta,
        source_id=source.id,
    )
    db.session.add(asset)
    db.session.commit()
    return asset


def _hgt_tile_name(lat: float, lon: float) -> str:
    lat_floor = math.floor(lat)
    lon_floor = math.floor(lon)
    ns = "N" if lat_floor >= 0 else "S"
    ew = "E" if lon_floor >= 0 else "W"
    return f"{ns}{abs(lat_floor):02d}{ew}{abs(lon_floor):03d}"


def download_srtm_tile(project, lat, lon):
    """
    Garante a presença do tile SRTM1 (.hgt) baixado via viewpano (servidor usado pelo pycraf).
    """
    tile_name = _hgt_tile_name(lat, lon)
    global_dir = global_srtm_dir()
    tile_pattern = f"{tile_name}.hgt"

    try:
        matches = list(global_dir.rglob(tile_pattern))
        if not matches:
            with pathprof.SrtmConf.set(srtm_dir=str(global_dir), download='missing', server='viewpano'):
                pathprof.srtm_height_map(
                    lon * u.deg,
                    lat * u.deg,
                    0.02 * u.deg,
                    0.02 * u.deg,
                    map_resolution=1 * u.arcsec,
                )
            matches = list(global_dir.rglob(tile_pattern))
    except Exception as exc:
        current_app.logger.error("Falha ao baixar SRTM via viewpano: %s", exc)
        return None

    if not matches:
        current_app.logger.error("Tile %s não foi encontrado em %s após o download.", tile_name, global_dir)
        return None

    local_path = matches[0]
    rel_path = os.path.relpath(local_path, storage_root())

    existing = Asset.query.filter_by(project_id=project.id, path=rel_path).order_by(Asset.created_at.desc()).first()
    if existing:
        return existing

    file_size = os.path.getsize(local_path)
    source = DatasetSource(
        project_id=project.id,
        kind=DatasetSourceKind.SRTM,
        locator={'server': 'viewpano'},
        notes=f"SRTM1 (1\") tile {tile_name} obtido do viewpano.",
    )
    db.session.add(source)
    db.session.flush()

    asset = Asset(
        project_id=project.id,
        type='dem',
        path=rel_path,
        mime_type='application/octet-stream',
        byte_size=file_size,
        meta={'source': 'SRTM1 viewpano', 'tile': tile_name, 'resolution': '1 arc-second'},
        source_id=source.id,
    )
    db.session.add(asset)
    db.session.commit()
    return asset

def download_mapbiomas_tile(project, year):
    """
    Downloads a MapBiomas Collection 10 tile for a given year.
    """
    year = _normalize_mapbiomas_year(year)
    if year is None:
        return None
    tile_name = f"brazil_coverage_{year}.tif"
    url = f"{MAPBIOMAS_BASE_URL}/{tile_name}"

    asset_filename = f"mapbiomas_collection10_{year}.tif"
    asset_folder = ensure_project_path_exists(project, 'assets', 'lulc')
    local_path = os.path.join(asset_folder, asset_filename)
    rel_path = get_project_asset_path(project, 'lulc', asset_filename)

    if os.path.exists(local_path):
        current_app.logger.info(f"MapBiomas tile {asset_filename} already exists for project {project.slug}.")
        existing = Asset.query.filter_by(project_id=project.id, path=rel_path).order_by(Asset.created_at.desc()).first()
        if existing:
            return existing
        size = os.path.getsize(local_path)
        meta = {'source': 'MapBiomas Collection 10', 'year': year, 'rehydrated': True}
        return _rehydrate_asset(
            project,
            'lulc',
            asset_filename,
            DatasetSourceKind.MAPBIOMAS,
            f"MapBiomas Collection 10 tile {year} (rehydratado).",
            meta,
            size=size,
            locator={'url': url},
            mime_type='image/tiff',
        )

    current_app.logger.info(f"Downloading MapBiomas tile from {url} to {local_path}")

    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        file_size = os.path.getsize(local_path)

        source = DatasetSource(
            project_id=project.id,
            kind=DatasetSourceKind.MAPBIOMAS,
            locator={'url': url},
            notes=f"MapBiomas Collection 10 tile for year {year}."
        )
        db.session.add(source)
        db.session.flush()

        asset = Asset(
            project_id=project.id,
            type='lulc',
            path=rel_path,
            mime_type='image/tiff',
            byte_size=file_size,
            meta={'source': 'MapBiomas Collection 10', 'year': year},
            source_id=source.id
        )
        db.session.add(asset)
        db.session.commit()

        current_app.logger.info(f"Successfully downloaded and created asset for {asset_filename}.")
        return asset

    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Failed to download MapBiomas tile: {e}")
        db.session.rollback()
        return None


def ensure_geodata_availability(project, latitude=None, longitude=None, lulc_year=None, fetch_lulc=True):
    """
    Garante que os dados básicos (DEM + LULC) estejam disponíveis para o projeto.

    Retorna um dicionário com os assets e metadados utilizados.
    """
    summary = {
        'dem_asset': None,
        'dem_dir': str(global_srtm_dir()),
        'lulc_asset': None,
        'lulc_year': None,
    }
    if project is None:
        return summary

    if latitude is not None and longitude is not None:
        summary['dem_asset'] = download_srtm_tile(project, latitude, longitude)

    if fetch_lulc:
        year = _normalize_mapbiomas_year(lulc_year)
        if year is None:
            current_year = datetime.utcnow().year - 1
            year = _normalize_mapbiomas_year(current_year)
        if year is not None:
            summary['lulc_asset'] = download_mapbiomas_tile(project, year)
            summary['lulc_year'] = year

    return summary
