import streamlit as st

from dashboard.data import load_gold_data
from dashboard.helpers import aggregate_periods


def show_routes(periods):
    df = load_gold_data(
        "routes",
        periods,
    )

    df = aggregate_periods(
        df,
        [
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
            "airline_id",
            "airline_name",
            "airline_code",
            "day_of_week",
            "day_of_week_name",
        ],
        [
            "avg_dep_delay_minutes",
            "avg_arr_delay_minutes",
            "on_time_rate_pct",
            "cancellation_rate_pct",
            "diversion_rate_pct",
        ],
    )

    st.header("Route Reliability")

    if df.empty:
        st.info("No route data available.")
        return

    min_flights = st.number_input(
        "Minimum number of flights",
        min_value=1,
        value=20,
        step=10,
    )

    filtered = df[
        df["flights"] >= min_flights
    ].copy()

    filtered["route"] = (
        filtered["origin_airport_code"]
        + " → "
        + filtered["dest_airport_code"]
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Route records",
        len(filtered),
    )

    col2.metric(
        "Flights",
        f"{filtered['flights'].sum():,.0f}",
    )

    weighted_on_time = (
        (
            filtered["on_time_rate_pct"]
            * filtered["flights"]
        ).sum()
        / filtered["flights"].sum()
        if not filtered.empty
        else 0
    )

    col3.metric(
        "Overall On-Time Rate",
        f"{weighted_on_time:.1f} %",
    )

    st.subheader("Top 20 Routes by On-Time Rate")

    chart_df = (
        filtered[
            [
                "route",
                "on_time_rate_pct",
            ]
        ]
        .sort_values(
            "on_time_rate_pct",
            ascending=False,
        )
        .head(20)
        .set_index("route")
    )

    st.bar_chart(chart_df)

    st.subheader("Route Data")

    st.dataframe(
        filtered,
        width="stretch",
        hide_index=True,
    )
