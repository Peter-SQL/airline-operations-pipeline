import pandas as pd
import streamlit as st

from dashboard.data import load_gold_data, load_periods
from dashboard.helpers import add_total_row, aggregate_periods
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


def select_trend_period(available_periods, selected_periods):
    available = sorted([
        (int(year), int(month))
        for year, month in available_periods[["year", "month"]].values
    ])
    labels = [f"{year}-{month:02d}" for year, month in available]

    selected_periods = sorted(selected_periods)
    start_default = selected_periods[0] if selected_periods else available[0]
    end_default = selected_periods[-1] if selected_periods else available[-1]

    with st.sidebar:
        with st.container(border=True):
            st.subheader("KPI Development")
            st.caption("Independent period selection")

            start = st.selectbox(
                "Start",
                labels,
                index=available.index(start_default),
                key="kpi_start",
            )
            end = st.selectbox(
                "End",
                labels,
                index=available.index(end_default),
                key="kpi_end",
            )

    start_key = int(start.replace("-", ""))
    end_key = int(end.replace("-", ""))

    return [
        period
        for period in available
        if start_key <= period[0] * 100 + period[1] <= end_key
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
    show_comparison(all_df, df, color_domain)

    selected_airlines = show_airline_details(all_df, df)

    st.subheader("KPI Development")

    trend_periods = select_trend_period(
        load_periods(),
        periods,
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