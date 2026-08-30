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
def load_gold_data(dataset, periods):
    if dataset not in GOLD_TABLES:
        raise ValueError(f"Unknown Gold dataset: {dataset}")

    table_name = GOLD_TABLES[dataset]

    conditions = []
    params = {}

    for i, (year, month) in enumerate(periods):
        conditions.append(
            f"(year = :year_{i} AND month = :month_{i})"
        )
        params[f"year_{i}"] = year
        params[f"month_{i}"] = month

    query = text(f"""
        SELECT *
        FROM analytics.{table_name}
        WHERE {" OR ".join(conditions)}
    """)

    return pd.read_sql_query(
        query,
        get_engine(),
        params=params,
    )
