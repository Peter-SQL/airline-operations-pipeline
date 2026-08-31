# dashboard/views/routes.py

import pandas as pd
import streamlit as st

from dashboard.data import load_gold_data, load_periods
from dashboard.helpers import aggregate_periods, select_kpi_period
from dashboard.views.route_charts import show_comparison
from dashboard.views.route_timeseries import show_timeseries
from dashboard.views.route_map import show_route_map
from dashboard.views.route_charts import show_comparison
from dashboard.views.route_map import show_route_map
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
    "origin_airport_name",
    "origin_city",
    "origin_state_code",
    "origin_state",
    "origin_latitude",
    "origin_longitude",
    "dest_airport_id",
    "dest_airport_code",
    "dest_airport_name",
    "dest_city",
    "dest_state_code",
    "dest_state",
    "dest_latitude",
    "dest_longitude",
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
        len(periods),
    )

    show_route_map(
        df,
        len(periods),
    )

    show_route_details(
        all_df,
        df,
        len(periods),
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

    specific_mode = (
        st.session_state.get(
            "route_limit",
            "Top 20",
        )
        == "Specific"
    )

    if specific_mode:
        if st.session_state.get(
            "route_selection_cleared",
            False,
        ):
            selected = []
        else:
            selected = (
                st.session_state.get(
                    "route_selected",
                    [],
                )
                or st.session_state.get(
                    "route_comparison_selection",
                    [],
                )
            )
    else:
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
    all_routes["origin_airport_name"] = "All Routes"
    all_routes["origin_city"] = "All Routes"
    all_routes["origin_airport_code"] = None
    all_routes["dest_airport_name"] = "All Routes"
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