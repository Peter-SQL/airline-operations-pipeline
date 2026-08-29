import streamlit as st

from dashboard.data import load_gold_data


def show_airlines(year, month):
    df = load_gold_data(
        "airlines",
        year,
        month,
    )

    st.header("Airline Reliability")

    if df.empty:
        st.info("No airline data available.")
        return

    total_flights = df["flights"].sum()

    weighted_on_time = (
        (
            df["on_time_rate_pct"]
            * df["flights"]
        ).sum()
        / total_flights
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Airlines",
        len(df),
    )

    col2.metric(
        "Flights",
        f"{total_flights:,.0f}",
    )

    col3.metric(
        "Overall On-Time Rate",
        f"{weighted_on_time:.1f} %",
    )

    st.subheader("On-Time Rate by Airline")

    chart_df = (
        df[
            [
                "airline_name",
                "on_time_rate_pct",
            ]
        ]
        .sort_values(
            "on_time_rate_pct",
            ascending=False,
        )
        .set_index("airline_name")
    )

    st.bar_chart(chart_df)

    st.subheader("Airline Data")

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )