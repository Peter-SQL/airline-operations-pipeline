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
        raise ValueError(
            f"Unknown Gold dataset: {dataset}"
        )

    table_name = GOLD_TABLES[dataset]

    conditions = []
    params = {}

    for i, (year, month) in enumerate(periods):
        conditions.append(
            f"(g.year = :year_{i} AND g.month = :month_{i})"
        )

        params[f"year_{i}"] = year
        params[f"month_{i}"] = month

    if dataset == "airports":
        query = text(f"""
            SELECT
                g.*,
                d.latitude,
                d.longitude
            FROM analytics.{table_name} g
            LEFT JOIN analytics.dim_airport d
                ON g.airport_id = d.airport_id
            WHERE {" OR ".join(conditions)}
        """)

    elif dataset == "routes":
        query = text(f"""
            SELECT
                g.*,
                origin.latitude AS origin_latitude,
                origin.longitude AS origin_longitude,
                dest.latitude AS dest_latitude,
                dest.longitude AS dest_longitude
            FROM analytics.{table_name} g
            LEFT JOIN analytics.dim_airport origin
                ON g.origin_airport_id = origin.airport_id
            LEFT JOIN analytics.dim_airport dest
                ON g.dest_airport_id = dest.airport_id
            WHERE {" OR ".join(conditions)}
        """)

    else:
        query = text(f"""
            SELECT g.*
            FROM analytics.{table_name} g
            WHERE {" OR ".join(conditions)}
        """)

    return pd.read_sql_query(
        query,
        get_engine(),
        params=params,
    )