import pandas as pd
import streamlit as st
from sqlalchemy import text

from dashboard.db import get_engine


GOLD_TABLES = {
    "airlines": "gold_airline_reliability",
    "airports": "gold_airport_reliability",
    "routes": "gold_route_reliability",
    "flights": "gold_flight_reliability",
}


@st.cache_data
def load_periods():
    query = text("""
        SELECT DISTINCT
            year,
            month
        FROM analytics.gold_airline_reliability
        ORDER BY year DESC, month DESC
    """)

    return pd.read_sql_query(
        query,
        get_engine(),
    )


@st.cache_data
def load_gold_data(dataset, year, month):
    if dataset not in GOLD_TABLES:
        raise ValueError(f"Unknown Gold dataset: {dataset}")

    table_name = GOLD_TABLES[dataset]

    query = text(f"""
        SELECT *
        FROM analytics.{table_name}
        WHERE year = :year
          AND month = :month
    """)

    return pd.read_sql_query(
        query,
        get_engine(),
        params={
            "year": year,
            "month": month,
        },
    )
