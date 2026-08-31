import pandas as pd
import streamlit as st

from dashboard.data import load_gold_data, load_periods
from dashboard.helpers import aggregate_periods, select_kpi_period
from dashboard.views.route_charts import show_comparison
from dashboard.views.route_timeseries import show_timeseries
from dashboard.views.route_ui import (
    WEIGHTED_COLUMNS,
    add_all_routes,
    show_kpis,
    show_route_details,
)


GROUP_COLUMNS = [
    "origin_airport_id",
    "origin_airport_code",
    "origin_city",
    "origin_state_code",
    "origin_state",
    "dest_airport_id",
    "dest_airport_code",
    "dest_city",
    "dest_state_code",
    "dest_state",
]


def show_routes(periods):
    monthly_df = load_gold_data("routes", periods)

    if monthly_df.empty:
        st.info("No route data available.")
        return

    df = aggregate_periods(
        monthly_df,
        GROUP_COLUMNS,
        WEIGHTED_COLUMNS,
    )

    df["route"] = (
        df["origin_airport_code"]
        + " → "
        + df["dest_airport_code"]
    )

    route_count = len(df)

    st.header(
        "Route Reliability in total for selected "
        + ("period" if len(periods) == 1 else "periods")
        + f" - {route_count:,} routes"
    )    

    all_df = add_all_routes(df)

    color_domain = [
        "All Routes",
        *sorted(df["route"].dropna().unique()),
    ]

    show_kpis(
        all_df.iloc[0],
        len(df),
    )

    show_comparison(
        all_df,
        df,
        color_domain,
    )

    show_route_details(
        all_df,
        df,
    )

    st.subheader("KPI Development")

    trend_periods = select_kpi_period(
        load_periods(),
        periods,
        "route",
        "Route KPI Development",
    )

    if not trend_periods:
        st.warning("End must not be before Start.")
        return

    monthly_trend = load_gold_data(
        "routes",
        trend_periods,
    )

    trend_df = aggregate_periods(
        monthly_trend,
        ["year", "month"] + GROUP_COLUMNS,
        WEIGHTED_COLUMNS,
    )

    trend_df["route"] = (
        trend_df["origin_airport_code"]
        + " → "
        + trend_df["dest_airport_code"]
    )

    selected = st.session_state.get(
        "route_comparison_selection",
        [],
    )

    trend_df = trend_df[
        trend_df["route"].isin(selected)
    ].copy()

    all_routes = aggregate_periods(
        monthly_trend,
        ["year", "month"],
        WEIGHTED_COLUMNS,
    )

    all_routes["route"] = "All Routes"
    all_routes["origin_city"] = "All Routes"
    all_routes["origin_airport_code"] = None
    all_routes["dest_city"] = "All Routes"
    all_routes["dest_airport_code"] = None

    trend_df = pd.concat(
        [all_routes, trend_df],
        ignore_index=True,
    )

    show_timeseries(
        trend_df,
        color_domain,
    )