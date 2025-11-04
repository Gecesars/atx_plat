
import os
import requests
import math
import urllib.request
from flask import current_app
from .models import db, Asset, DatasetSource
from .storage import get_project_asset_path, ensure_project_path_exists

# Base URL for SRTM 90m data from CGIAR-CSI
SRTM_BASE_URL = "ftp://srtm.csi.cgiar.org/SRTM_v41/SRTM_Data_GeoTiff/"

def download_srtm_tile(project, lat, lon):
    """
    Downloads an SRTM 90m DEM tile for a given latitude and longitude from the CGIAR-CSI FTP server.
    The function determines the correct tile, downloads it, and creates the corresponding
    DatasetSource and Asset records in the database.
    """
    # Determine tile name (e.g., srtm_36_05.zip)
    lon_tile = math.floor((lon + 180) / 5) + 1
    lat_tile = math.floor((60 - lat) / 5) + 1
    tile_name = f"srtm_{lon_tile:02d}_{lat_tile:02d}"
    
    # Construct URL and local file path
    url = f"{SRTM_BASE_URL}{tile_name}.zip"
    asset_filename = f"{tile_name}.zip"
    asset_folder = ensure_project_path_exists(project, 'assets', 'dem')
    local_path = os.path.join(asset_folder, asset_filename)

    # Check if asset already exists
    if os.path.exists(local_path):
        current_app.logger.info(f"SRTM tile {asset_filename} already exists for project {project.slug}.")
        # Optionally, we could return the existing asset here
        return None

    current_app.logger.info(f"Downloading SRTM tile from {url} to {local_path}")

    try:
        with urllib.request.urlopen(url) as response, open(local_path, 'wb') as out_file:
            data = response.read() # read the file contents
            out_file.write(data)
        
        file_size = os.path.getsize(local_path)

        # Create DatasetSource
        source = DatasetSource(
            project_id=project.id,
            kind='SRTM',
            locator={'url': url},
            notes=f"SRTM 90m DEM tile for {tile_name}."
        )
        db.session.add(source)
        db.session.flush() # Flush to get the source.id

        # Create Asset
        asset = Asset(
            project_id=project.id,
            type='dem',
            path=get_project_asset_path(project, 'dem', asset_filename),
            mime_type='application/zip',
            byte_size=file_size,
            meta={'source': 'SRTM 90m', 'tile': tile_name, 'resolution': '90m'},
            source_id=source.id
        )
        db.session.add(asset)
        db.session.commit()

        current_app.logger.info(f"Successfully downloaded and created asset for {asset_filename}.")
        return asset

    except Exception as e:
        current_app.logger.error(f"Failed to download SRTM tile: {e}")
        db.session.rollback()
        return None


MAPBIOMAS_BASE_URL = "https://storage.googleapis.com/mapbiomas-public/initiatives/brasil/collection_10/lulc/coverage"

def download_mapbiomas_tile(project, year):
    """
    Downloads a MapBiomas Collection 10 tile for a given year.
    """
    tile_name = f"brazil_coverage_{year}.tif"
    url = f"{MAPBIOMAS_BASE_URL}/{tile_name}"

    asset_filename = f"mapbiomas_collection10_{year}.tif"
    asset_folder = ensure_project_path_exists(project, 'assets', 'lulc')
    local_path = os.path.join(asset_folder, asset_filename)

    if os.path.exists(local_path):
        current_app.logger.info(f"MapBiomas tile {asset_filename} already exists for project {project.slug}.")
        return None

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
            kind='MAPBIOMAS',
            locator={'url': url},
            notes=f"MapBiomas Collection 10 tile for year {year}."
        )
        db.session.add(source)
        db.session.flush()

        asset = Asset(
            project_id=project.id,
            type='lulc',
            path=get_project_asset_path(project, 'lulc', asset_filename),
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

