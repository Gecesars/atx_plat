from __future__ import annotations

from pathlib import Path

from flask import current_app

from extensions import db
from app_core.storage import inline_asset_path


def legacy_storage_root() -> Path | None:
    """
    Returns the legacy storage root (if configured and present on disk).
    """
    root = current_app.config.get('LEGACY_STORAGE_ROOT')
    if root:
        path = Path(root)
    else:
        default_path = Path(current_app.root_path).parent / 'storage'
        path = default_path if default_path.exists() else None
    if path is None:
        return None
    if not path.exists():
        return None
    return path


def rehydrate_asset_data(asset, *, kind: str = 'legacy') -> bytes | None:
    """
    Loads legacy data from the filesystem into the provided Asset row, storing it inline.
    Returns the raw bytes when rehydration succeeds.
    """
    if not asset or getattr(asset, 'data', None):
        return None
    legacy_path = getattr(asset, 'path', None)
    if not legacy_path or str(legacy_path).startswith('inline://'):
        return None
    root = legacy_storage_root()
    if not root:
        return None
    file_path = root / legacy_path
    if not file_path.exists():
        return None
    try:
        payload = file_path.read_bytes()
    except OSError:
        return None

    suffix = Path(legacy_path).suffix or '.bin'
    asset.data = payload
    asset.byte_size = len(payload)
    asset.path = inline_asset_path(kind, suffix)
    meta = dict(getattr(asset, 'meta', {}) or {})
    meta.setdefault('legacy_path', str(legacy_path))
    asset.meta = meta
    db.session.add(asset)
    db.session.commit()

    try:
        file_path.unlink()
    except OSError:
        pass
    return payload
