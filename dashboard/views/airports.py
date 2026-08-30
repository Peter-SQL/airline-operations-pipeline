import pandas as pd
import streamlit as st

from dashboard.data import load_gold_data, load_periods
from dashboard.helpers import aggregate_periods
from dashboard.views.airport_charts import show_comparison, show_map
from dashboard.views.airport_timeseries import show_timeseries
from dashboard.views.airport_ui import (
    WEIGHTED_COLUMNS,
    add_all_airports,
    select_airport_trend_period,
    show_airport_details,
    show_kpis,
)


GROUP_COLUMNS = [
    "airport_id", "airport_code", "airport_name", "city",
    "state_code", "state", "latitude", "longitude",
]


def show_airports(periods):
    monthly_df = load_gold_data("airports", periods)

    st.header(
        "Airport Reliability in total for selected "
        + ("period" if len(periods) == 1 else "periods")
    )

    if monthly_df.empty:
        st.info("No airport data available.")
        return

    operations = sorted(
        monthly_df["operation"].dropna().unique()
    )

    operation = st.radio(
        "Operation",
        operations,
        horizontal=True,
        key="airport_operation",
    )

    monthly_df = monthly_df[
        monthly_df["operation"] == operation
    ].copy()

    df = aggregate_periods(
        monthly_df,
        GROUP_COLUMNS,
        WEIGHTED_COLUMNS,
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

    selected_airports = show_airport_details(
        all_df,
        df,
        operation,
    )

    st.subheader("KPI Development")

    trend_periods = select_airport_trend_period(
        load_periods(),
        periods,
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

    if st.session_state.get("airport_limit") == "Specific":
        selected = st.session_state.get(
            "airport_specific_selection",
            [],
        )
    else:
        selected = [
            airport
            for airport in selected_airports
            if airport != "All Airports"
        ]

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