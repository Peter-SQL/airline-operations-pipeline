import altair as alt
import pandas as pd
import streamlit as st

from dashboard.data import load_gold_data
from dashboard.helpers import (add_total_row, aggregate_periods, highlight_total, number_column,)

def show_airlines(periods):
    df = load_gold_data("airlines", periods)

    df = aggregate_periods(
        df,
        [
            "airline_id",
            "airline_name",
            "airline_code",
        ],
        [
            "on_time_rate_pct",
            "avg_dep_delay_minutes",
            "avg_arr_delay_minutes",
            "cancellation_rate_pct",
            "diversion_rate_pct",
        ],
    )

    st.header("Airline Reliability")

    if df.empty:
        st.info("No airline data available.")
        return

    all_df = add_total_row(df, "airline_name", "airline_code")
    values = all_df.iloc[0]

    cancel_diversion_rate = (
        values["cancellation_rate_pct"]
        + values["diversion_rate_pct"]
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Flights", f"{values['flights']:,.0f}")
    col2.metric("On-Time Rate", f"{values['on_time_rate_pct']:.2f} %")
    col3.metric("Avg. Departure Delay", f"{values['avg_dep_delay_minutes']:.2f} min",)
    col4.metric("Cancellation & Diversion Rate",f"{cancel_diversion_rate:.2f} %",)

    st.subheader("Airline Comparison")

    metrics = {
        "On-Time": "on_time_rate_pct",
        "Flights": "flights",
        "Dep. Delay": "avg_dep_delay_minutes",
        "Arr. Delay": "avg_arr_delay_minutes",
        "Cancellation": "cancellation_rate_pct",
        "Diversion": "diversion_rate_pct",
    }

    y_labels = {
        "On-Time": "On-Time Rate (%)",
        "Flights": "Flights",
        "Dep. Delay": "Avg. Departure Delay (Min)",
        "Arr. Delay": "Avg. Arrival Delay (Min)",
        "Cancellation": "Cancellation Rate (%)",
        "Diversion": "Diversion Rate (%)",
    }

    metric = st.radio(
        "Choose metric",
        metrics,
        horizontal=True,
    )

    sort_by = st.radio(
        "Sort by",
        ["Metric", "Airline name"],
        horizontal=True,
    )

    column = metrics[metric]
    chart_df = all_df.copy()

    if metric == "Flights":
        chart_df = chart_df[
            chart_df["airline_name"] != "All Airlines"
        ]

    if sort_by == "Airline name":
        all_row = chart_df[
            chart_df["airline_name"] == "All Airlines"
        ]

        chart_df = chart_df[
            chart_df["airline_name"] != "All Airlines"
        ].sort_values("airline_name")

        all_row_end = all_row.copy()
        all_row_end["airline_name"] = "All Airlines "

        chart_df = pd.concat(
            [all_row, chart_df, all_row_end],
            ignore_index=True,
        )

    else:
        chart_df = chart_df.sort_values(
            column,
            ascending=False,
        )

    chart_df["Color"] = chart_df["airline_name"].str.strip()

    colors = [
        "#FFD700",  # All Airlines – Gold

        "#1F77B4",  # American / Blau
        "#D62728",  # Delta / Rot
        "#2CA02C",  # United / Grün
        "#FF7F0E",  # Southwest / Orange
        "#9467BD",  # JetBlue / Violett
        "#17BECF",  # Alaska / Türkis
        "#8C564B",  # Frontier / Braun
        "#E377C2",  # Spirit / Pink
        "#7F7F7F",  # Allegiant / Grau
        "#BCBD22",  # Hawaiian / Oliv
        "#393B79",
        "#E6550D",
        "#31A354",
        "#756BB1",
    ]

    color_domain = ["All Airlines"] + sorted(
        df["airline_name"].dropna().unique().tolist()
    )

    chart_order = chart_df["airline_name"].tolist()
    
    chart = (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            x=alt.X(
                "airline_name:N",
                title="Airlines",
                sort=chart_order,
                axis=alt.Axis(labelAngle=-45,   
                labelOverlap=False, 
                labelLimit=200,                            
                ),                                 
            ),
            y=alt.Y(
                f"{column}:Q",
                title=y_labels[metric],
            ),
            color=alt.Color(
                "Color:N",
                title="Airline",
                scale=alt.Scale(
                    domain=color_domain,
                    range=colors,
                ),
            ),
            stroke=alt.condition(
                alt.datum.Color == "All Airlines",
                alt.value("#000000"),
                alt.value(None),
            ),
            strokeWidth=alt.condition(
                alt.datum.Color == "All Airlines",
                alt.value(4),
                alt.value(0),
            ),
            tooltip=[
                alt.Tooltip(
                    "Color:N",
                    title="Airline",
                ),
                alt.Tooltip(
                    f"{column}:Q",
                    title=y_labels[metric],
                    format=".2f",
                ),
            ],
        )
        .properties(height=400)
    )

    st.altair_chart(
        chart,
        width="stretch",
    )

    airlines = sorted(
        df["airline_name"].dropna().tolist()
    )

    st.write("Airlines")

    cols = st.columns(5)
    selected = []

    for i, airline in enumerate(airlines):
        if cols[i % 5].checkbox(
            airline,
            value=True,
            key=f"airline_{airline}",
        ):
            selected.append(airline)

    if st.checkbox(
        "All Airlines",
        value=False,
        key="airline_all",
    ):
        selected.append("All Airlines")

    selected_df = all_df[
        all_df["airline_name"].isin(selected)
    ]

    st.subheader("Airline Details")

    details = selected_df[
        [
            "airline_code",
            "airline_name",
            "flights",
            "on_time_rate_pct",
            "avg_dep_delay_minutes",
            "avg_arr_delay_minutes",
            "cancellation_rate_pct",
            "diversion_rate_pct",
        ]
    ]

    st.dataframe(
        details.style
        .apply(highlight_total, axis=1)
        .format({
            "on_time_rate_pct": "{:.2f}",
            "avg_dep_delay_minutes": "{:.2f}",
            "avg_arr_delay_minutes": "{:.2f}",
            "cancellation_rate_pct": "{:.2f}",
            "diversion_rate_pct": "{:.2f}",
        }),
        width="stretch",
        hide_index=True,
        height=min(37 + len(details) * 35, 1000),
        column_config={
            "airline_code": "Code",
            "airline_name": "Airline",
            "flights": "Flights",
            "on_time_rate_pct": "On-Time %",
            "avg_dep_delay_minutes": "Avg. Dep. Delay",
            "avg_arr_delay_minutes": "Avg. Arr. Delay",
            "cancellation_rate_pct": "Cancellation %",
            "diversion_rate_pct": "Diversion %",
        },
    )