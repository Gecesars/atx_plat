import pytest
import requests

from app_core.analytics.ibge_catalog import (
    _create_sidra_session,
    discover_population_age_sex_classifications,
    get_population_by_sex_for_min_age,
)


@pytest.fixture(scope="module")
def sidra_session():
    return _create_sidra_session()


def _skip_on_connection_error(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except requests.RequestException as exc:
        pytest.skip(f"SIDRA indisponível ou sem conectividade ({exc}).")


def test_metadata_exposes_simple_age_categories(sidra_session):
    meta = _skip_on_connection_error(
        lambda session: session.get(
            "https://servicodados.ibge.gov.br/api/v3/agregados/6579/metadados",
            timeout=30,
        ).json(),
        sidra_session,
    )
    print("Classificações disponíveis:", [cls["nome"] for cls in meta.get("classificacoes", [])])
    classes_payload = _skip_on_connection_error(
        lambda session: session.get(
            "https://servicodados.ibge.gov.br/api/v3/agregados/6579/classificacoes",
            timeout=30,
        ).json(),
        sidra_session,
    )
    print("Resposta /classificacoes:", classes_payload)

    info = discover_population_age_sex_classifications(session=sidra_session)

    sex_names = {name.lower() for name in info["sex"]["categories"].keys()}
    assert {"homens", "mulheres"}.issubset(sex_names)

    ages = [item["age"] for item in info["age"]["categories"]]
    assert any(age == 18 for age in ages)
    assert max(ages) >= 90


def test_population_over_18_by_sex_returns_values(sidra_session):
    result = _skip_on_connection_error(
        get_population_by_sex_for_min_age,
        "3550308",  # São Paulo (SP)
        session=sidra_session,
    )

    assert result["municipality"] == "3550308"
    assert result["period"]

    totals = result["sex_totals"]
    assert "Homens" in totals and "Mulheres" in totals
    assert totals["Homens"] > 100_000
    assert totals["Mulheres"] > 100_000
    assert result["age_category_count"] >= 50

