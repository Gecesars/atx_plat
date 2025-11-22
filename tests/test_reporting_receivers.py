from app_core.reporting import service


def test_collect_receiver_entries_refreshes_demographics(monkeypatch):
    snapshot = {
        "receivers": [
            {
                "label": "RX 1",
                "municipality": "Viana, Maranhão, Brasil",
                "state": "MA",
                "distance_km": 42.5,
                "field_dbuv_m": 68.0,
                "location": {
                    "municipality": "Viana",
                    "state_code": "MA",
                },
                "ibge": {
                    "code": "2100055",
                    "name": "Viana",
                    "state": "MA",
                    "demographics": {
                        "code": "2100055",
                        "total": 106550,
                        "period": 2022,
                    },
                },
            }
        ]
    }

    resolved_code = "2112803"
    refreshed_payload = {"code": resolved_code, "total": 51442, "period": 2022}

    monkeypatch.setattr(
        service.ibge_api,
        "resolve_municipality_code",
        lambda city, state=None: resolved_code,
    )
    monkeypatch.setattr(
        service.ibge_api,
        "fetch_demographics_by_code",
        lambda code: refreshed_payload if code == resolved_code else None,
    )
    monkeypatch.setattr(
        service.ibge_api,
        "fetch_demographics_by_city",
        lambda city, state=None: None,
    )

    entries = service._collect_receiver_entries(snapshot, limit=None)

    assert entries
    entry = entries[0]
    assert entry["population"] == refreshed_payload["total"]
    assert entry["ibge_code"] == resolved_code
    assert entry["demographics"] == refreshed_payload


def test_estimate_population_impact_uses_preprocessed_entries():
    snapshot = {"receivers": []}
    receivers = [
        {
            "label": "RX 1",
            "municipality": "Cidade A",
            "state": "MA",
            "field_dbuv_m": 42.0,
            "population": 123,
            "population_year": 2022,
            "demographics": {"total": 123, "period": 2022},
        }
    ]

    summary, total = service._estimate_population_impact(
        snapshot,
        allow_remote_lookup=False,
        receivers_preprocessed=receivers,
    )

    assert total == 123
    assert summary and summary[0]["population"] == 123
