import altair as alt
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


COLORS = [
    "#FFD700", "#1F77B4", "#D62728", "#2CA02C", "#FF7F0E",
    "#9467BD", "#17BECF", "#8C564B", "#E377C2", "#7F7F7F",
    "#BCBD22", "#393B79", "#E6550D", "#31A354", "#756BB1",
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
    return [COLORS[i % len(COLORS)] for i in range(len(domain))]


def show_comparison(all_df, df, color_domain, operation):
    st.subheader("Airport Comparison")

    metrics = ["On-Time", "Flights", "Avg. Delay"]

    if not str(operation).lower().startswith("arr"):
        metrics += ["Cancellation", "Diversion"]

    metric = st.radio(
        "Choose metric", metrics,
        horizontal=True, key="airport_metric",
    )

    c1, c2 = st.columns(2)

    sort_by = c1.radio(
        "Sort by", ["Metric", "Airport"],
        horizontal=True, key="airport_sort",
    )

    show = c2.radio(
        "Show", ["Top 20", "Top 50", "Specific"],
        horizontal=True, key="airport_limit",
    )

    specific_mode = show == "Specific"

    airport_set = st.radio(
        "Airport set",
        ["All airports", "> 1% of all flights"],
        horizontal=True,
        key="airport_set",
        disabled=specific_mode,
    )

    column = METRICS[metric]
    airports = df.copy()

    if specific_mode:
        selected = st.session_state.get(
            "airport_specific_selection",
            st.session_state.get("airport_selected", []),
        )

        if not selected:
            st.session_state["airport_comparison_selection"] = []
            st.info("Select one or more airports below.")
            return

        airports = airports[
            airports["airport_code"].isin(selected)
        ].copy()

    else:
        if airport_set == "> 1% of all flights":
            min_flights = df["flights"].sum() * 0.01

            airports = airports[
                airports["flights"] > min_flights
            ].copy()

            st.caption(
                f"Minimum: {min_flights:,.0f} flights · "
                f"{len(airports)} airports"
            )

    airports["display_code"] = (
        airports["city"].fillna("")
        + " (" + airports["airport_code"] + ")"
    )

    airports["color_code"] = airports["airport_code"]

    if sort_by == "Airport":
        airports = airports.sort_values(
            ["city", "airport_code"]
        )
    else:
        airports = airports.sort_values(
            column,
            ascending=False,
        )

    if not specific_mode:
        airports = airports.head(
            20 if show == "Top 20" else 50
        )

    st.session_state["airport_comparison_selection"] = (
        airports["airport_code"].tolist()
    )

    if metric != "Flights":
        all_row = all_df[
            all_df["airport_code"] == "n/a"
        ].copy()

        all_row["display_code"] = "All Airports"
        all_row["color_code"] = "All Airports"

        airports = pd.concat(
            [all_row, airports],
            ignore_index=True,
        )

    chart_order = airports["display_code"].tolist()

    bars = alt.Chart(airports).mark_bar().encode(
        x=alt.X(
            "display_code:N",
            title="Airport",
            sort=chart_order,
            axis=alt.Axis(
                labelAngle=-45,
                labelOverlap=False,
                labelLimit=170,
            ),
        ),
        y=alt.Y(
            f"{column}:Q",
            title=Y_LABELS[metric],
        ),
        color=alt.condition(
            alt.datum.display_code == "All Airports",
            alt.value("#FFD700"),
            alt.Color(
                "color_code:N",
                scale=alt.Scale(
                    range=COLORS[1:]
                ),
                legend=None,
            ),
        ),
        stroke=alt.condition(
            alt.datum.display_code == "All Airports",
            alt.value("#000000"),
            alt.value(None),
        ),
        strokeWidth=alt.condition(
            alt.datum.display_code == "All Airports",
            alt.value(6),
            alt.value(0),
        ),
        tooltip=[
            alt.Tooltip(
                "display_code:N",
                title="Airport",
            ),
            alt.Tooltip(
                "flights:Q",
                title="Flights",
                format=",.0f",
            ),
            alt.Tooltip(
                f"{column}:Q",
                title=Y_LABELS[metric],
                format=".2f",
            ),
        ],
    )

    marker = (
        alt.Chart(
            airports[
                airports["display_code"] == "All Airports"
            ]
        )
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
            y=f"{column}:Q",
        )
    )

    st.altair_chart(
        alt.layer(
            bars,
            marker,
        ).properties(height=400),
        width="stretch",
    )


def show_map(df, operation):
    st.subheader("Airport Map")

    metrics = ["On-Time", "Avg. Delay"]

    if not str(operation).lower().startswith("arr"):
        metrics += ["Cancellation", "Diversion"]

    metric = st.radio(
        "Map color", metrics,
        horizontal=True, key="airport_map_metric",
    )

    column = METRICS[metric]

    map_df = df[
        df["latitude"].notna()
        & df["longitude"].notna()
    ].copy()

    specific_mode = (
        st.session_state.get("airport_limit") == "Specific"
    )

    selected = st.session_state.get(
        "airport_specific_selection",
        st.session_state.get("airport_selected", []),
    )

    if specific_mode and selected:
        map_df = map_df[
            map_df["airport_code"].isin(selected)
        ].copy()

    if map_df.empty:
        st.info("No airport coordinates available.")
        return

    def reliability_color(value):
        if metric == "On-Time":
            return (
                "green" if value >= 80
                else "gold" if value >= 70
                else "red"
            )

        if metric == "Avg. Delay":
            return (
                "green" if value <= 15
                else "gold" if value <= 25
                else "red"
            )

        if metric == "Cancellation":
            return (
                "green" if value <= 1
                else "gold" if value <= 3
                else "red"
            )

        if metric == "Diversion":
            return (
                "green" if value <= 0.5
                else "gold" if value <= 1
                else "red"
            )

        return "gold"

    map_df["map_color"] = map_df[column].apply(
        reliability_color
    )

    max_flights = map_df["flights"].max()

    map_df["marker_size"] = (
        map_df["flights"] / max_flights * 30 + 8
        if max_flights > 0 else 8
    )

    map_df["display_airport"] = (
        map_df["city"].fillna("")
        + " (" + map_df["airport_code"] + ")"
    )

    customdata = map_df[
        [
            "airport_name",
            "state_code",
            "flights",
            "on_time_rate_pct",
            "avg_delay_minutes",
        ]
    ].to_numpy()

    fig = go.Figure(
        go.Scattermap(
            lat=map_df["latitude"],
            lon=map_df["longitude"],
            mode="markers",
            text=map_df["display_airport"],
            customdata=customdata,
            marker={
                "size": map_df["marker_size"],
                "color": map_df["map_color"],
                "opacity": 0.75,
            },
            hovertemplate=(
                "<b>%{text}</b><br>"
                "%{customdata[0]}<br>"
                "%{customdata[1]}<br>"
                "Flights: %{customdata[2]:,.0f}<br>"
                "On-Time: %{customdata[3]:.2f}%<br>"
                "Avg. Delay: %{customdata[4]:.2f} min"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        map={
            "style": "open-street-map",
            "center": {
                "lat": 39.5,
                "lon": -98.35,
            },
            "zoom": 2.8,
        },
        height=600,
        margin={
            "l": 0,
            "r": 0,
            "t": 0,
            "b": 0,
        },
        showlegend=False,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "scrollZoom": False,
            "displaylogo": False,
        },
    )