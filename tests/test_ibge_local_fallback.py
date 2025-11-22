import types

import pytest

from app_core.integrations import ibge as ibge_api


class DummyResponse:
    def raise_for_status(self):
        raise RuntimeError("network unavailable")


def test_resolve_municipality_code_uses_local_dataset(monkeypatch):
    monkeypatch.setattr(ibge_api.requests, "get", lambda *args, **kwargs: DummyResponse())
    code = ibge_api.resolve_municipality_code("São Paulo", "SP")
    assert code == "3550308"


def test_fetch_demographics_by_code_local(monkeypatch):
    monkeypatch.setattr(ibge_api.requests, "get", lambda *args, **kwargs: DummyResponse())
    data = ibge_api.fetch_demographics_by_code("3550308")
    assert data is not None
    assert data["total"] > 0


def test_fetch_demographics_by_city_local(monkeypatch):
    monkeypatch.setattr(ibge_api.requests, "get", lambda *args, **kwargs: DummyResponse())
    data = ibge_api.fetch_demographics_by_city("Rio de Janeiro", "RJ")
    assert data is not None
    assert data["total"] > 0
