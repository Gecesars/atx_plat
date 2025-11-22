#!/usr/bin/env python3
"""
Extrai metadados IBGE dos snapshots locais e gera um dataset JSON offline.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]
STORAGE_ROOT = ROOT / "storage"
OUTPUT_PATH = ROOT / "data" / "ibge_demographics.json"


def _safe_float(value) -> float | None:
    if value in (None, "", "-", "..."):
        return None
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return None


def _parse_sex_breakdown(payload: list[Dict[str, Any]] | None) -> Dict[str, int]:
    breakdown: Dict[str, int] = {}
    if not isinstance(payload, list):
        return breakdown
    for block in payload:
        for resultado in block.get("resultados", []):
            classes = resultado.get("classificacoes", [])
            sex_label = None
            for entry in classes:
                if entry.get("nome", "").strip().lower() == "sexo":
                    categories = entry.get("categoria") or {}
                    if categories:
                        sex_label = next(iter(categories.values()))
                    break
            for serie in resultado.get("series", []):
                serie_data = serie.get("serie") or {}
                for raw in serie_data.values():
                    value = _safe_float(raw)
                    if sex_label and value is not None:
                        breakdown[sex_label] = int(round(value))
    return breakdown


def collect_entries() -> Dict[str, Dict[str, Any]]:
    dataset: Dict[str, Dict[str, Any]] = {}
    if not STORAGE_ROOT.exists():
        return dataset
    summary_files = STORAGE_ROOT.rglob("*_summary.json")
    for path in summary_files:
        try:
            data = json.loads(path.read_text())
        except Exception:
            continue
        registry = data.get("ibge_registry") or {}
        for code, payload in registry.items():
            demographics = payload.get("demographics") or {}
            total = demographics.get("total")
            if total is None:
                continue
            entry = dataset.setdefault(
                str(code),
                {
                    "code": str(code),
                    "name": payload.get("name"),
                    "state": payload.get("state"),
                },
            )
            entry["population"] = int(total)
            entry["population_year"] = demographics.get("period") or 2022
            entry["sex_breakdown"] = _parse_sex_breakdown(demographics.get("sex"))
    return dataset


def main():
    entries = collect_entries()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "source": "local_snapshots",
        "municipalities": entries,
    }
    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"Wrote {len(entries)} municipalities to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
