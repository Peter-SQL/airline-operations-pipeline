import altair as alt
import pandas as pd
import streamlit as st

COLORS = [
    "#FFD700", "#1F77B4", "#D62728", "#2CA02C", "#FF7F0E",
    "#9467BD", "#17BECF", "#8C564B", "#E377C2", "#7F7F7F",
    "#BCBD22", "#393B79", "#E6550D", "#31A354", "#756BB1",
]

METRICS = {
    "On-Time": "on_time_rate_pct",
    "Dep. Delay": "avg_dep_delay_minutes",
    "Arr. Delay": "avg_arr_delay_minutes",
    "Cancellation": "cancellation_rate_pct",
    "Diversion": "diversion_rate_pct",
    "Flights": "flights",
}

Y_LABELS = {
    "On-Time": "On-Time Rate (%)",
    "Flights": "Flights",
    "Dep. Delay": "Avg. Departure Delay (Min)",
    "Arr. Delay": "Avg. Arrival Delay (Min)",
    "Cancellation": "Cancellation Rate (%)",
    "Diversion": "Diversion Rate (%)",
}


def get_color_range(domain):
    colors = COLORS[:len(domain)].copy()

    american = next(
        (i for i, name in enumerate(domain) if name.startswith("American Airlines")),
        None,
    )

    spirit = next(
        (i for i, name in enumerate(domain) if name.startswith("Spirit Air")),
        None,
    )

    if american is not None and spirit is not None:
        colors[american], colors[spirit] = colors[spirit], colors[american]

    return colors


def show_comparison(all_df, df, color_domain):
    st.subheader("Airline Comparison")

    metric = st.radio(
        "Choose metric",
        list(METRICS),
        index=len(METRICS) - 1,
        horizontal=True,
        key="airline_metric",
    )

    sort_by = st.radio(
        "Sort by",
        ["Metric", "Airline Name"],
        horizontal=True,
        key="airline_sort",
    )

    column = METRICS[metric]

    chart_df = all_df.copy()

    if st.session_state.get("comparison_filter", False):
        selected = [
            airline
            for airline in df["airline_name"].dropna()
            if st.session_state.get(f"airline_{airline}", True)
        ]

        chart_df = chart_df[
            chart_df["airline_name"].isin(selected + ["All Airlines"])
        ]

    if metric == "Flights":
        chart_df = chart_df[
            chart_df["airline_name"] != "All Airlines"
        ]

    if sort_by == "Airline Name":
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

    chart_order = chart_df["airline_name"].tolist()

    colors = get_color_range(color_domain)

    bars = (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            x=alt.X(
                "airline_name:N",
                title="Airlines",
                sort=chart_order,
                axis=alt.Axis(
                    labelAngle=-45,
                    labelOverlap=False,
                    labelLimit=200,
                ),
            ),
            y=alt.Y(
                f"{column}:Q",
                title=Y_LABELS[metric],
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
                alt.value(6),
                alt.value(0),
            ),
            tooltip=[
                alt.Tooltip(
                    "Color:N",
                    title="Airline",
                ),
                alt.Tooltip(
                    f"{column}:Q",
                    title=Y_LABELS[metric],
                    format=".2f",
                ),
            ],
        )
    )

    marker_df = chart_df[
        chart_df["Color"] == "All Airlines"
    ]

    marker = (
        alt.Chart(marker_df)
        .mark_text(
            text="▼",
            fontSize=20,
            fontWeight="bold",
            dy=-13,
            color="black",
        )
        .encode(
            x=alt.X(
                "airline_name:N",
                sort=chart_order,
            ),
            y=alt.Y(f"{column}:Q"),
        )
    )

    st.altair_chart(
        alt.layer(
            bars,
            marker,
        ).properties(height=400),
        width="stretch",
    )