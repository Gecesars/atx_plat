from __future__ import annotations

import unicodedata
from functools import lru_cache
from typing import Any, Dict

import requests
from flask import current_app


IBGE_LOCATIONS_URL = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
IBGE_DEMOGRAPHICS_URL = "https://servicodados.ibge.gov.br/api/v3/agregados/9514/periodos/2022/variaveis/93?localidades=N6[{code}]"
IBGE_POPULATION_URL = "https://servicodados.ibge.gov.br/api/v3/agregados/6579/periodos/2022/variaveis/9324?localidades=N6[{code}]"

STATE_ALIASES = {
    "acre": "AC",
    "alagoas": "AL",
    "amapa": "AP",
    "amazonas": "AM",
    "bahia": "BA",
    "ceara": "CE",
    "distrito federal": "DF",
    "espirito santo": "ES",
    "goias": "GO",
    "maranhao": "MA",
    "mato grosso": "MT",
    "mato grosso do sul": "MS",
    "minas gerais": "MG",
    "para": "PA",
    "paraiba": "PB",
    "parana": "PR",
    "pernambuco": "PE",
    "piaui": "PI",
    "rio de janeiro": "RJ",
    "rio grande do norte": "RN",
    "rio grande do sul": "RS",
    "rondonia": "RO",
    "roraima": "RR",
    "santa catarina": "SC",
    "sao paulo": "SP",
    "sergipe": "SE",
    "tocantins": "TO",
}


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_text = ascii_text.lower()
    replacements = (
        ("state of ", ""),
        ("estado de ", ""),
    )
    for old, new in replacements:
        ascii_text = ascii_text.replace(old, new)
    ascii_text = ascii_text.replace("-", " ").replace("_", " ")
    ascii_text = " ".join(ascii_text.split())
    return ascii_text


def normalize_state_code(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    if len(value) == 2 and value.isalpha():
        return value.upper()
    slug = _slugify(value)
    return STATE_ALIASES.get(slug, None)


def _safe_parse_numeric(value) -> int | None:
    if value in (None, "", "-", "NA"):
        return None
    try:
        return int(float(str(value).replace(",", ".")))
    except (TypeError, ValueError):
        return None


@lru_cache(maxsize=2048)
def resolve_municipality_code(city: str | None, state: str | None = None) -> str | None:
    if not city:
        return None
    params = {'nome': city}
    try:
        resp = requests.get(IBGE_LOCATIONS_URL, params=params, timeout=10)
        resp.raise_for_status()
        candidates = resp.json()
    except Exception as exc:
        current_app.logger.warning(
            'ibge.lookup_failed',
            extra={'city': city, 'state': state, 'error': str(exc)},
        )
        return None

    if not candidates:
        return None

    normalized_state = normalize_state_code(state) if state else None

    def _candidate_state(item):
        uf_info = (((item.get('microrregiao') or {}).get('mesorregiao') or {}).get('UF') or {})
        sigla = uf_info.get('sigla')
        nome = uf_info.get('nome')
        return normalize_state_code(sigla) or normalize_state_code(nome)

    for item in candidates:
        candidate_state = _candidate_state(item)
        if not normalized_state or candidate_state == normalized_state:
            code = item.get('id')
            if code:
                return str(code)

    code = candidates[0].get('id')
    return str(code) if code else None


@lru_cache(maxsize=4096)
def fetch_demographics_by_code(code: str | None) -> Dict[str, Any] | None:
    if not code:
        return None
    try:
        resp = requests.get(IBGE_DEMOGRAPHICS_URL.format(code=code), timeout=15)
        resp.raise_for_status()
        payload = resp.json()
    except Exception as exc:
        current_app.logger.warning(
            'ibge.demographics_failed',
            extra={'code': code, 'error': str(exc)},
        )
        payload = None

    total = None
    sex_breakdown: dict[str, int] = {}
    age_breakdown: dict[str, int] = {}

    if payload:
        resultados = payload[0].get('resultados', []) if isinstance(payload, list) and payload else []
        for resultado in resultados:
            classificacoes = resultado.get('classificacoes') or []
            classes_meta: dict[str, dict[str, Any]] = {}
            for klass in classificacoes:
                categories = {
                    categoria.get('id'): categoria.get('nome')
                    for categoria in (klass.get('categorias') or [])
                }
                classes_meta[klass.get('id')] = {
                    'name': klass.get('nome', ''),
                    'categories': categories,
                }
            for serie in resultado.get('series') or []:
                serie_values = serie.get('serie') or {}
                value = None
                for raw_value in serie_values.values():
                    value = _safe_parse_numeric(raw_value)
                    if value is not None:
                        break
                if value is None:
                    continue
                serie_classes = serie.get('classificacoes') or []
                if not serie_classes:
                    total = value
                    continue
                for serie_class in serie_classes:
                    class_id = serie_class.get('id')
                    category_id = serie_class.get('categoria')
                    meta = classes_meta.get(class_id) or {}
                    category_label = (meta.get('categories') or {}).get(category_id, category_id)
                    class_name = (meta.get('name') or '').lower()
                    if 'sexo' in class_name:
                        sex_breakdown[category_label] = sex_breakdown.get(category_label, 0) + value
                    elif 'idade' in class_name:
                        age_breakdown[category_label] = age_breakdown.get(category_label, 0) + value

    if total is None:
        legacy_total = fetch_population_legacy(code)
        total = legacy_total

    if payload is None and total is None:
        return None

    return {
        'code': code,
        'total': total,
        'sex': sex_breakdown,
        'age': age_breakdown,
        'raw': payload,
    }


@lru_cache(maxsize=4096)
def fetch_population_legacy(code: str | None) -> int | None:
    if not code:
        return None
    try:
        resp = requests.get(IBGE_POPULATION_URL.format(code=code), timeout=10)
        resp.raise_for_status()
        payload = resp.json()
    except Exception as exc:
        current_app.logger.warning(
            'ibge.population_failed',
            extra={'code': code, 'error': str(exc)},
        )
        return None
    serie = (
        payload[0]
        .get('resultados', [{}])[0]
        .get('series', [{}])[0]
        .get('serie', {})
    )
    values = [
        _safe_parse_numeric(value)
        for value in serie.values()
        if value not in (None, "")
    ]
    values = [value for value in values if value is not None]
    return values[-1] if values else None


def fetch_demographics_by_city(city: str | None, state: str | None = None) -> Dict[str, Any] | None:
    code = resolve_municipality_code(city, state)
    if not code:
        return None
    data = fetch_demographics_by_code(code)
    if data:
        return data
    total = fetch_population_legacy(code)
    if total is None:
        return None
    return {'code': code, 'total': total, 'sex': {}, 'age': {}, 'raw': None}
