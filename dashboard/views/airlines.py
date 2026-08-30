import pandas as pd
import streamlit as st

from dashboard.data import load_gold_data, load_periods
from dashboard.helpers import (
    add_total_row,
    aggregate_periods,
    select_kpi_period,
)
from dashboard.views.airline_charts import show_comparison
from dashboard.views.airline_timeseries import show_timeseries
from dashboard.views.airline_ui import show_airline_details, show_kpis


WEIGHTED_COLUMNS = [
    "on_time_rate_pct",
    "avg_dep_delay_minutes",
    "avg_arr_delay_minutes",
    "cancellation_rate_pct",
    "diversion_rate_pct",
]


def show_airlines(periods):
    monthly_df = load_gold_data("airlines", periods)

    df = aggregate_periods(
        monthly_df,
        ["airline_id", "airline_name", "airline_code"],
        WEIGHTED_COLUMNS,
    )

    period_label = "period" if len(periods) == 1 else "periods"

    st.header(
        f"Airline Reliability in total for selected {period_label}"
    )

    if df.empty:
        st.info("No airline data available.")
        return

    all_df = add_total_row(
        df,
        "airline_name",
        "airline_code",
    )

    color_domain = ["All Airlines"] + sorted(
        df["airline_name"].dropna().unique().tolist()
    )

    show_kpis(all_df.iloc[0])

    show_comparison(
        all_df,
        df,
        color_domain,
    )

    selected_airlines = show_airline_details(
        all_df,
        df,
    )

    st.subheader("KPI Development")

    trend_periods = select_kpi_period(
        load_periods(),
        periods,
        "airline",
        "KPI Development",
    )

    if not trend_periods:
        st.warning("End must not be before Start.")
        return

    trend_airlines = [
        airline
        for airline in selected_airlines
        if airline != "All Airlines"
    ]

    monthly_trend = load_gold_data(
        "airlines",
        trend_periods,
    )

    all_airlines = aggregate_periods(
        monthly_trend,
        ["year", "month"],
        WEIGHTED_COLUMNS,
    )

    all_airlines["airline_name"] = "All Airlines"

    trend_df = monthly_trend[
        monthly_trend["airline_name"].isin(trend_airlines)
    ].copy()

    trend_df = pd.concat(
        [all_airlines, trend_df],
        ignore_index=True,
    )

    show_timeseries(
        trend_df,
        color_domain,
    )