import pytest

import src.loading.load_postgres as load_postgres


def test_flight_path():
    path = load_postgres.flight_path(2026, 6)

    assert path == (
        load_postgres.SILVER_FLIGHTS
        / "year=2026"
        / "month=06"
    )


def test_reference_path():
    path = load_postgres.reference_path(
        2026,
        6,
        "airlines",
    )

    assert path == (
        load_postgres.SILVER_REFERENCE
        / "year=2026"
        / "month=06"
        / "airlines"
    )


def test_get_connection_without_password(monkeypatch):
    monkeypatch.setattr(
        load_postgres,
        "POSTGRES_PASSWORD",
        None,
    )

    with pytest.raises(
        ValueError,
        match="POSTGRES_PASSWORD is not set",
    ):
        load_postgres.get_connection()


def test_load_dim_airline_missing_path(monkeypatch):
    missing_path = load_postgres.SILVER_REFERENCE / "missing"

    monkeypatch.setattr(
        load_postgres,
        "reference_path",
        lambda year, month, name: missing_path,
    )

    with pytest.raises(
        FileNotFoundError,
        match="Silver airlines not found",
    ):
        load_postgres.load_dim_airline(
            spark=None,
            year=2026,
            month=6,
        )


def test_load_fact_flight_missing_path(monkeypatch):
    missing_path = load_postgres.SILVER_FLIGHTS / "missing"

    monkeypatch.setattr(
        load_postgres,
        "flight_path",
        lambda year, month: missing_path,
    )

    with pytest.raises(
        FileNotFoundError,
        match="Silver flights not found",
    ):
        load_postgres.load_fact_flight(
            spark=None,
            year=2026,
            month=6,
        )