import pandas as pd
import streamlit as st

from dashboard.data import load_gold_data, load_periods
from dashboard.helpers import aggregate_periods, select_kpi_period
from dashboard.views.airport_charts import show_comparison, show_map
from dashboard.views.airport_timeseries import show_timeseries
from dashboard.views.airport_ui import (
    WEIGHTED_COLUMNS,
    add_all_airports,
    show_airport_details,
    show_kpis,
)


GROUP_COLUMNS = [
    "airport_id", "airport_code", "airport_name", "city",
    "state_code", "state", "latitude", "longitude",
]


def show_airports(periods):
    monthly_df = load_gold_data("airports", periods)

    if monthly_df.empty:
        st.info("No airport data available.")
        return

    operation = st.session_state.get("airport_operation", "DEP")

    monthly_df = monthly_df[
        monthly_df["operation"] == operation
    ].copy()

    df = aggregate_periods(
        monthly_df,
        GROUP_COLUMNS,
        WEIGHTED_COLUMNS,
    )

    airport_count = df["airport_id"].nunique()

    st.header(
        "Airport Reliability in total for selected "
        + ("period" if len(periods) == 1 else "periods")
        + f" - {airport_count:,} airports"
    )

    all_df = add_all_airports(df)

    color_domain = [
        "All Airports",
        *sorted(df["airport_code"].dropna().unique()),
    ]

    show_kpis(
        all_df.iloc[0],
        df["airport_id"].nunique(),
        operation,
    )

    show_comparison(
        all_df,
        df,
        color_domain,
        operation,
    )

    show_map(
        df,
        operation,
    )

    show_airport_details(
        all_df,
        df,
        operation,
    )

    st.subheader("KPI Development")

    trend_periods = select_kpi_period(
        load_periods(),
        periods,
        "airport",
        "Airport KPI Development",
    )

    if not trend_periods:
        st.warning("End must not be before Start.")
        return

    monthly_trend = load_gold_data(
        "airports",
        trend_periods,
    )

    monthly_trend = monthly_trend[
        monthly_trend["operation"] == operation
    ].copy()

    selected = st.session_state.get(
        "airport_comparison_selection",
        [],
    )

    trend_df = monthly_trend[
        monthly_trend["airport_code"].isin(selected)
    ].copy()

    all_airports = aggregate_periods(
        monthly_trend,
        ["year", "month"],
        WEIGHTED_COLUMNS,
    )

    all_airports["airport_code"] = "All Airports"
    all_airports["city"] = "All Airports"

    trend_df = pd.concat(
        [all_airports, trend_df],
        ignore_index=True,
    )

    show_timeseries(
        trend_df,
        color_domain,
        operation,
    )