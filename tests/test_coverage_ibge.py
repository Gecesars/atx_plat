from app_core.analytics.coverage_ibge import (
    MunicipalityCoverage,
    _enrich_municipalities_with_ibge,
    summarize_coverage_demographics,
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

    def fake_lookup(code):
        value = pop_values.get(code)
        if value is None:
            return None
        return {
            "code": code,
            "name": f"City {code}",
            "state": "SP",
            "state_code": "35",
            "population": value,
            "population_year": 2022,
        }

    monkeypatch.setattr(
        "app_core.analytics.coverage_ibge.ibge_api.get_local_municipality_entry",
        fake_lookup,
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

    def fake_lookup(code):
        mapping = {
            "400": {
                "code": "400",
                "name": "City 400",
                "state": "RJ",
                "state_code": "33",
                "population": 111111,
                "population_year": 2022,
                "income_per_capita": 3200.0,
                "income_year": 2021,
            },
            "500": {
                "code": "500",
                "name": "City 500",
                "state": "PR",
                "state_code": "41",
                "population": 222222,
                "population_year": 2022,
                "income_per_capita": 4100.0,
                "income_year": 2020,
            },
        }
        return mapping.get(code)

    monkeypatch.setattr(
        "app_core.analytics.coverage_ibge.ibge_api.get_local_municipality_entry",
        fake_lookup,
    )

    _enrich_municipalities_with_ibge(municipalities)

    assert municipalities["400"].income_per_capita == 3200.0
    assert municipalities["400"].income_year == 2021
    assert municipalities["500"].income_per_capita == 4100.0
    assert municipalities["500"].income_year == 2020


def test_summarize_coverage_prefers_tile_stats(monkeypatch):
    summary_payload = {
        "tile_stats": {
            "10": {
                "100/200": 30.5,
                "101/200": 20.0,
            }
        }
    }

    monkeypatch.setattr(
        "app_core.analytics.coverage_ibge._enrich_municipalities_with_ibge",
        lambda municipalities: None,
    )

    def fake_resolve(lat, lon):
        return {
            "ibge_code": "9999999",
            "municipality": "Cidade Teste",
            "state": "SP",
            "state_id": "35",
        }

    monkeypatch.setattr(
        "app_core.analytics.coverage_ibge._resolve_municipality",
        fake_resolve,
    )

    result = summarize_coverage_demographics(summary_payload=summary_payload, min_field_dbuvm=25.0)

    assert result["sample_source"] == "tiles"
    assert result["tiles_total"] == 2
    assert result["tiles_covered"] == 1
    assert result["municipality_count"] == 1
    assert result["municipalities"][0]["tile_hits"] == 1


def test_summarize_coverage_fallback_to_signal_dict(monkeypatch):
    summary_payload = {
        "tile_stats": {"8": {"10/10": 15.0}},
        "signal_level_dict": {"(-23.0,-46.0)": 32.0},
    }

    monkeypatch.setattr(
        "app_core.analytics.coverage_ibge._enrich_municipalities_with_ibge",
        lambda municipalities: None,
    )

    def fake_resolve(lat, lon):
        return {
            "ibge_code": "8888888",
            "municipality": "Fallback",
            "state": "RJ",
            "state_id": "33",
        }

    monkeypatch.setattr(
        "app_core.analytics.coverage_ibge._resolve_municipality",
        fake_resolve,
    )

    result = summarize_coverage_demographics(summary_payload=summary_payload, min_field_dbuvm=25.0)

    assert result["sample_source"] == "signal_dict"
    assert result["tiles_total"] == 1
    assert result["tiles_covered"] == 0
    assert result["municipality_count"] == 1
