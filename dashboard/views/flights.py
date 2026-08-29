import streamlit as st

from dashboard.data import load_gold_data


def show_flights(year, month):
    df = load_gold_data(
        "flights",
        year,
        month,
    )

    st.header("Flight Reliability")

    if df.empty:
        st.info("No flight data available.")
        return

    airlines = sorted(
        df["airline_name"]
        .dropna()
        .unique()
    )

    selected_airline = st.selectbox(
        "Airline",
        airlines,
        key="flight_airline",
    )

    filtered = df[
        df["airline_name"] == selected_airline
    ].copy()

    filtered["route"] = (
        filtered["origin_airport_code"]
        + " → "
        + filtered["dest_airport_code"]
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Flight numbers",
        filtered["flight_number"].nunique(),
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
    )

    col3.metric(
        "Overall On-Time Rate",
        f"{weighted_on_time:.1f} %",
    )

    st.subheader("Flight Data")

    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True,
    )