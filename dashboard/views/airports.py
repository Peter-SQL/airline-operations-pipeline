import streamlit as st

from dashboard.data import load_gold_data


def show_airports(year, month):
    df = load_gold_data(
        "airports",
        year,
        month,
    )

    st.header("Airport Reliability")

    if df.empty:
        st.info("No airport data available.")
        return

    operations = sorted(
        df["operation"]
        .dropna()
        .unique()
    )

    selected_operation = st.selectbox(
        "Operation",
        operations,
    )

    filtered = df[
        df["operation"] == selected_operation
    ].copy()

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Airports",
        filtered["airport_id"].nunique(),
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

    st.subheader("Top 20 Airports by On-Time Rate")

    chart_df = (
        filtered[
            [
                "airport_code",
                "on_time_rate_pct",
            ]
        ]
        .sort_values(
            "on_time_rate_pct",
            ascending=False,
        )
        .head(20)
        .set_index("airport_code")
    )

    st.bar_chart(chart_df)

    st.subheader("Airport Data")

    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True,
    )