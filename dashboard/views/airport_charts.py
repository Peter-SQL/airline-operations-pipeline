import altair as alt
import pandas as pd
import pydeck as pdk
import streamlit as st


COLORS = [
    "#FFD700", "#1F77B4", "#D62728", "#2CA02C", "#FF7F0E",
    "#9467BD", "#17BECF", "#8C564B", "#E377C2", "#7F7F7F",
    "#BCBD22", "#393B79", "#E6550D", "#31A354", "#756BB1",
    "#636363", "#6BAED6", "#FD8D3C", "#74C476", "#9E9AC8",
]


METRICS = {
    "On-Time": "on_time_rate_pct",
    "Flights": "flights",
    "Avg. Delay": "avg_delay_minutes",
    "Cancellation": "cancellation_rate_pct",
    "Diversion": "diversion_rate_pct",
}


Y_LABELS = {
    "On-Time": "On-Time Rate (%)",
    "Flights": "Flights",
    "Avg. Delay": "Avg. Delay (Min)",
    "Cancellation": "Cancellation Rate (%)",
    "Diversion": "Diversion Rate (%)",
}


def color_range(domain):
    return [
        COLORS[i % len(COLORS)]
        for i in range(len(domain))
    ]


def show_comparison(all_df, df, color_domain):
    st.subheader("Airport Comparison")

    metric = st.radio(
        "Choose metric",
        METRICS,
        horizontal=True,
        key="airport_metric",
    )

    c1, c2 = st.columns(2)

    sort_by = c1.radio(
        "Sort by",
        ["Metric", "Airport code"],
        horizontal=True,
        key="airport_sort",
    )

    limit = c2.radio(
        "Show",
        ["Top 20", "Top 50", "All"],
        horizontal=True,
        key="airport_limit",
    )

    column = METRICS[metric]
    chart_df = all_df.copy()

    if st.session_state.get(
        "airport_comparison_filter",
        False,
    ):
        selected = [
            airport
            for airport in df["airport_code"].dropna()
            if st.session_state.get(
                f"airport_{airport}",
                True,
            )
        ]

        chart_df = chart_df[
            chart_df["airport_code"].isin(selected)
            | (chart_df["airport_code"] == "n/a")
        ]

    all_row = chart_df[
        chart_df["airport_code"] == "n/a"
    ]

    airports = chart_df[
        chart_df["airport_code"] != "n/a"
    ].copy()

    if sort_by == "Airport code":
        airports = airports.sort_values(
            "airport_code"
        )
    else:
        airports = airports.sort_values(
            column,
            ascending=False,
        )

    if limit == "Top 20":
        airports = airports.head(20)

    elif limit == "Top 50":
        airports = airports.head(50)

    if metric == "Flights":
        chart_df = airports
    else:
        chart_df = pd.concat(
            [all_row, airports],
            ignore_index=True,
        )

    chart_df["display_code"] = chart_df[
        "airport_code"
    ].replace(
        {"n/a": "All Airports"}
    )

    chart_order = chart_df[
        "display_code"
    ].tolist()

    bars = (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            x=alt.X(
                "display_code:N",
                title="Airports",
                sort=chart_order,
                axis=alt.Axis(
                    labelAngle=-45,
                    labelOverlap=False,
                    labelLimit=100,
                ),
            ),
            y=alt.Y(
                f"{column}:Q",
                title=Y_LABELS[metric],
            ),
            color=alt.Color(
                "display_code:N",
                title="Airport",
                scale=alt.Scale(
                    domain=color_domain,
                    range=color_range(color_domain),
                ),
                legend=None,
            ),
            stroke=alt.condition(
                alt.datum.display_code
                == "All Airports",
                alt.value("#000000"),
                alt.value(None),
            ),
            strokeWidth=alt.condition(
                alt.datum.display_code
                == "All Airports",
                alt.value(6),
                alt.value(0),
            ),
            tooltip=[
                alt.Tooltip(
                    "display_code:N",
                    title="Airport",
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
        chart_df["display_code"]
        == "All Airports"
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
                "display_code:N",
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


def show_map(df):
    st.subheader("Airport Map")

    metric = st.radio(
        "Map color",
        [
            "On-Time",
            "Avg. Delay",
            "Cancellation",
            "Diversion",
        ],
        horizontal=True,
        key="airport_map_metric",
    )

    column = METRICS[metric]

    map_df = df[
        df["latitude"].notna()
        & df["longitude"].notna()
    ].copy()

    if map_df.empty:
        st.info(
            "No airport coordinates available."
        )
        return

    values = map_df[column]
    minimum = values.min()
    maximum = values.max()

    if maximum == minimum:
        normalized = pd.Series(
            0.5,
            index=map_df.index,
        )
    else:
        normalized = (
            values - minimum
        ) / (
            maximum - minimum
        )

    map_df["map_color"] = normalized.apply(
        lambda x: [
            int(230 * (1 - x)),
            int(80 + 120 * x),
            int(230 * x),
            190,
        ]
    )

    max_flights = map_df["flights"].max()

    if max_flights > 0:
        map_df["radius"] = (
            map_df["flights"]
            / max_flights
            * 40000
            + 5000
        )
    else:
        map_df["radius"] = 5000

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position="[longitude, latitude]",
        get_radius="radius",
        get_fill_color="map_color",
        pickable=True,
        auto_highlight=True,
    )

    view = pdk.ViewState(
        latitude=39.5,
        longitude=-98.35,
        zoom=3,
    )

    tooltip = {
        "html": (
            "<b>{airport_code}</b><br/>"
            "{airport_name}<br/>"
            "{city}, {state_code}<br/>"
            "Flights: {flights}<br/>"
            "On-Time: {on_time_rate_pct}%<br/>"
            "Avg. Delay: {avg_delay_minutes} min<br/>"
            "Cancellation: {cancellation_rate_pct}%<br/>"
            "Diversion: {diversion_rate_pct}%"
        )
    }

    st.pydeck_chart(
        pdk.Deck(
            layers=[layer],
            initial_view_state=view,
            tooltip=tooltip,
        ),
        width="stretch",
    )