from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import requests
from flask import current_app

from app_core.analytics.ibge_catalog import (
    _create_sidra_session,
    fetch_income_per_capita_by_state,
    get_municipality_metadata,
    get_or_resolve_municipality,
)
from app_core.integrations import ibge as ibge_api

LOGGER = logging.getLogger(__name__)

_GEOCODE_PRECISION = 3  # grau ~ 110m
OSM_REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"


def _round_coord(value: float, precision: int = _GEOCODE_PRECISION) -> float:
    return round(float(value), precision)


@dataclass
class MunicipalityCoverage:
    ibge_code: str
    municipality: str
    state: str
    state_id: Optional[str]
    max_field_dbuvm: float
    sample_lat: float
    sample_lon: float
    points: int = 0
    population: Optional[float] = None
    population_year: Optional[int] = None
    income_per_capita: Optional[float] = None
    income_year: Optional[int] = None


def _parse_signal_dict(signal_dict: Dict[str, float], min_dbuv: float) -> List[Tuple[float, float, float]]:
    points: List[Tuple[float, float, float]] = []
    for key, value in signal_dict.items():
        try:
            val = float(value)
        except (TypeError, ValueError):
            continue
        if val < min_dbuv:
            continue
        lat_str, lon_str = key.strip("()").split(",")
        try:
            lat = float(lat_str)
            lon = float(lon_str)
        except ValueError:
            continue
        points.append((lat, lon, val))
    return points


def _cluster_points(points: List[Tuple[float, float, float]], precision: int = 2, limit: int = 400) -> List[Tuple[float, float, float, int]]:
    clusters: Dict[Tuple[float, float], Dict[str, float]] = {}
    for lat, lon, value in points:
        key = (round(lat, precision), round(lon, precision))
        cluster = clusters.setdefault(key, {"lat": lat, "lon": lon, "value": value, "count": 0})
        cluster["count"] += 1
        if value > cluster["value"]:
            cluster["lat"] = lat
            cluster["lon"] = lon
            cluster["value"] = value
    cluster_list = [
        (info["lat"], info["lon"], info["value"], info["count"]) for info in clusters.values()
    ]
    cluster_list.sort(key=lambda item: item[2], reverse=True)
    if limit and len(cluster_list) > limit:
        return cluster_list[:limit]
    return cluster_list


@lru_cache(maxsize=4096)
def _reverse_geocode_osm_cached(lat_key: float, lon_key: float) -> Optional[Dict[str, str]]:
    lat = float(lat_key)
    lon = float(lon_key)
    params = {
        "lat": lat,
        "lon": lon,
        "format": "jsonv2",
        "accept-language": "pt-BR",
    }
    headers = {"User-Agent": "ATXCoverage/1.0 (+https://atxcoverage)"}
    try:
        resp = requests.get(OSM_REVERSE_URL, params=params, headers=headers, timeout=20)
        resp.raise_for_status()
        address = resp.json().get("address") or {}
        name = address.get("city") or address.get("town") or address.get("village") or address.get("municipality")
        state = address.get("state_code") or address.get("state")
        if not name:
            return None

        return {"name": name, "state": state, "country": address.get("country")}
    except requests.RequestException as exc:
        LOGGER.debug("reverse_geocode_osm_failed", extra={"error": str(exc)})
        return None


def _reverse_geocode_osm(lat: float, lon: float) -> Optional[Dict[str, str]]:
    lat_key = _round_coord(lat)
    lon_key = _round_coord(lon)
    return _reverse_geocode_osm_cached(lat_key, lon_key)


def _resolve_municipality(lat: float, lon: float) -> Optional[Dict[str, str]]:
    detail = _reverse_geocode_osm(lat, lon)
    if not detail:
        return None

    state_hint = ibge_api.normalize_state_code(detail.get("state"))
    code = get_or_resolve_municipality(detail.get("name"), state_hint)
    if not code:
        return None

    meta = get_municipality_metadata(code)
    if not meta:
        return None

    return meta


def _enrich_municipalities_with_ibge(
    municipalities: Dict[str, MunicipalityCoverage],
    population_threshold: float = 25.0,
) -> None:
    if not municipalities:
        return

    session = _create_sidra_session()
    state_codes = {info.state_id for info in municipalities.values() if info.state_id}
    income_data = fetch_income_per_capita_by_state(state_codes, session=session)

    for code, info in municipalities.items():
        pop_value = None
        demographics = ibge_api.fetch_demographics_by_code(code)
        if demographics and demographics.get("total") is not None:
            pop_value = demographics["total"]
            info.population_year = 2022
        else:
            legacy_value = ibge_api.fetch_population_legacy(code)
            if legacy_value is not None:
                pop_value = legacy_value
                info.population_year = 2022
            else:
                info.population_year = None
        info.population = pop_value

        if info.state_id:
            income_entry = income_data.get(info.state_id)
            if income_entry:
                info.income_per_capita = income_entry.get("value")
                info.income_year = income_entry.get("year")


def summarize_coverage_demographics(
    summary_json_path: Path | None = None,
    min_field_dbuvm: float = 25.0,
    cluster_precision: int = 2,
    cluster_limit: int = 400,
    summary_payload: Optional[Dict] = None,
) -> Dict[str, object]:
    if summary_payload is not None:
        summary_data = dict(summary_payload)
    else:
        if summary_json_path is None or not summary_json_path.exists():
            raise FileNotFoundError(f"Coverage summary not found: {summary_json_path}")
        with summary_json_path.open("r", encoding="utf-8") as handle:
            summary_data = json.load(handle)

    signal_dict = summary_data.get("signal_level_dict") or {}
    points = _parse_signal_dict(signal_dict, min_field_dbuvm)
    if not points:
        return {
            "threshold_dbuv": min_field_dbuvm,
            "total_pixels": 0,
            "cluster_count": 0,
            "municipalities": [],
        }

    clusters = _cluster_points(points, precision=cluster_precision, limit=cluster_limit)
    municipalities: Dict[str, MunicipalityCoverage] = {}

    for lat, lon, value, count in clusters:
        meta = _resolve_municipality(lat, lon)
        if not meta:
            continue
        code = meta["ibge_code"]
        municipality = municipalities.get(code)
        if not municipality:
            municipality = MunicipalityCoverage(
                ibge_code=code,
                municipality=meta.get("municipality") or "",
                state=meta.get("state") or "",
                state_id=meta.get("state_id"),
                max_field_dbuvm=value,
                sample_lat=lat,
                sample_lon=lon,
                points=count,
            )
            municipalities[code] = municipality
        else:
            municipality.points += count
            if value > municipality.max_field_dbuvm:
                municipality.max_field_dbuvm = value
                municipality.sample_lat = lat
                municipality.sample_lon = lon

    _enrich_municipalities_with_ibge(municipalities)

    ordered = sorted(
        municipalities.values(),
        key=lambda item: item.max_field_dbuvm,
        reverse=True,
    )

    payload = []
    for info in ordered:
        payload.append(
            {
                "ibge_code": info.ibge_code,
                "municipality": info.municipality,
                "state": info.state,
                "max_field_dbuvm": round(info.max_field_dbuvm, 2),
                "sample_lat": info.sample_lat,
                "sample_lon": info.sample_lon,
                "points": info.points,
                "population": info.population,
                "population_year": info.population_year,
                "income_per_capita": info.income_per_capita,
                "income_year": info.income_year,
            }
        )

    return {
        "threshold_dbuv": min_field_dbuvm,
        "total_pixels": len(points),
        "cluster_count": len(clusters),
        "municipalities": payload,
    }
