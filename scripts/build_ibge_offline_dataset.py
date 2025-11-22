#!/usr/bin/env python3
"""
Extrai dados de população (Censo 2022) e renda domiciliar per capita (PNAD)
dos arquivos XLSX locais em /docs e gera um dataset JSON offline.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import re
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
POPULATION_FILE = DOCS_DIR / "CD2022_Populacao_Coletada_Imputada_e_Total_Municipio_e_UF_20231222.xlsx"
INCOME_FILE = DOCS_DIR / "Agregados_por_municipios_renda_responsavel_BR.xlsx"
OUTPUT_FILE = ROOT / "data" / "ibge_population_income.json"

NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def _read_shared_strings(zf: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    strings: list[str] = []
    for si in root.findall("a:si", NS):
        pieces = []
        for node in si.findall(".//a:t", NS):
            pieces.append(node.text or "")
        strings.append("".join(pieces))
    return strings


def _iter_sheet_rows(path: Path):
    with zipfile.ZipFile(path) as zf:
        strings = _read_shared_strings(zf)
        sheet = ET.fromstring(zf.read("xl/worksheets/sheet1.xml"))
        for row in sheet.findall(".//a:row", NS):
            row_map: dict[str, str | None] = {}
            for cell in row.findall("a:c", NS):
                ref = cell.attrib.get("r", "")
                col = "".join(re.findall(r"[A-Z]+", ref))
                t_type = cell.attrib.get("t")
                value_node = cell.find("a:v", NS)
                text_value = value_node.text if value_node is not None else None
                if t_type == "s" and text_value is not None:
                    try:
                        text_value = strings[int(text_value)]
                    except (ValueError, IndexError):
                        text_value = None
                row_map[col] = text_value
            yield row_map


def _to_int(value: str | None) -> int | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        try:
            return int(float(value.replace(".", "").replace(",", ".")))
        except ValueError:
            return None


def _to_float(value: str | None) -> float | None:
    if value is None:
        return None
    value = value.strip().replace(" ", "")
    if not value:
        return None
    try:
        return float(value.replace(".", "").replace(",", "."))
    except ValueError:
        return None


def load_population() -> dict[str, dict[str, object]]:
    dataset: dict[str, dict[str, object]] = {}
    for row in _iter_sheet_rows(POPULATION_FILE):
        header = row.get("B")
        if header == "UF":
            continue
        uf = row.get("B")
        cod_uf = row.get("C")
        cod_munic = row.get("D")
        name = row.get("E")
        population_raw = row.get("H")
        if not (uf and cod_uf and cod_munic and population_raw):
            continue
        try:
            code = f"{int(cod_uf):02d}{int(cod_munic):05d}"
        except ValueError:
            continue
        population = _to_int(population_raw)
        if population is None:
            continue
        dataset[code] = {
            "code": code,
            "name": name,
            "state": uf,
            "population": population,
            "population_year": 2022,
        }
    return dataset


def load_income(dataset: dict[str, dict[str, object]]):
    for row in _iter_sheet_rows(INCOME_FILE):
        if row.get("A") == "CD_MUN":
            continue
        code = row.get("A")
        if not code or code not in dataset:
            continue
        per_capita = _to_float(row.get("F"))
        total_income = _to_float(row.get("G"))
        if per_capita is not None:
            dataset[code]["income_per_capita"] = per_capita
            dataset[code]["income_year"] = 2022
        if total_income is not None:
            dataset[code]["income_total"] = total_income
            dataset[code]["income_total_year"] = 2022


def build_dataset():
    municipalities = load_population()
    load_income(municipalities)
    payload = {
        "source": {
            "population": POPULATION_FILE.name,
            "income": INCOME_FILE.name,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "municipalities": municipalities,
    }
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"Wrote {len(municipalities)} entries to {OUTPUT_FILE}")


if __name__ == "__main__":
    build_dataset()
