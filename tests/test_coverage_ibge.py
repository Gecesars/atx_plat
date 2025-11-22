import types

from app_core.analytics.coverage_ibge import (
    MunicipalityCoverage,
    _enrich_municipalities_with_ibge,
)


def _build_municipality(code: str, state_id: str | None = None) -> MunicipalityCoverage:
    return MunicipalityCoverage(
        ibge_code=code,
        municipality=f"City {code}",
        state="SP",
        state_id=state_id,
        max_field_dbuvm=75.0,
        sample_lat=-23.0,
        sample_lon=-46.0,
        points=5,
    )


def test_enrich_municipalities_uses_legacy_population(monkeypatch):
    municipalities = {
        "100": _build_municipality("100", state_id="35"),
        "200": _build_municipality("200", state_id="35"),
        "300": _build_municipality("300", state_id=None),
    }

    pop_values = {"100": 123456, "200": 654321, "300": None}

    monkeypatch.setattr(
        "app_core.analytics.coverage_ibge._create_sidra_session",
        lambda: types.SimpleNamespace(),
    )

    monkeypatch.setattr(
        "app_core.analytics.coverage_ibge.fetch_income_per_capita_by_state",
        lambda state_codes, session=None: {},
    )

    def fake_demographics(code):
        if pop_values.get(code) is None:
            return None
        return {"total": pop_values[code]}

    monkeypatch.setattr(
        "app_core.analytics.coverage_ibge.ibge_api.fetch_demographics_by_code",
        fake_demographics,
    )

    monkeypatch.setattr(
        "app_core.analytics.coverage_ibge.ibge_api.fetch_population_legacy",
        lambda code: None,
    )

    _enrich_municipalities_with_ibge(municipalities)

    assert municipalities["100"].population == 123456
    assert municipalities["100"].population_year == 2022
    assert municipalities["200"].population == 654321
    assert municipalities["200"].population_year == 2022
    assert municipalities["300"].population is None
    assert municipalities["300"].population_year is None


def test_enrich_municipalities_adds_income(monkeypatch):
    municipalities = {
        "400": _build_municipality("400", state_id="33"),
        "500": _build_municipality("500", state_id="41"),
    }

    monkeypatch.setattr(
        "app_core.analytics.coverage_ibge._create_sidra_session",
        lambda: types.SimpleNamespace(),
    )

    def fake_demographics(code):
        return {"total": 111111} if code == "400" else {"total": 222222}

    monkeypatch.setattr(
        "app_core.analytics.coverage_ibge.ibge_api.fetch_demographics_by_code",
        fake_demographics,
    )

    monkeypatch.setattr(
        "app_core.analytics.coverage_ibge.ibge_api.fetch_population_legacy",
        lambda code: None,
    )

    def fake_income(state_codes, session=None):
        return {
            "33": {"value": 3200.0, "year": 2021},
            "41": {"value": 4100.0, "year": 2020},
        }

    monkeypatch.setattr(
        "app_core.analytics.coverage_ibge.fetch_income_per_capita_by_state",
        fake_income,
    )

    _enrich_municipalities_with_ibge(municipalities)

    assert municipalities["400"].income_per_capita == 3200.0
    assert municipalities["400"].income_year == 2021
    assert municipalities["500"].income_per_capita == 4100.0
    assert municipalities["500"].income_year == 2020
