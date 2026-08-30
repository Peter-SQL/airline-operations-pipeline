import altair as alt
import pandas as pd
import pydeck as pdk
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
        selected = st.session_state.get("airport_selected", [])

        if not selected:
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
    selected = st.session_state.get("airport_selected", [])

    if specific_mode and selected:
        map_df = map_df[
            map_df["airport_code"].isin(selected)
        ].copy()

    if map_df.empty:
        st.info("No airport coordinates available.")
        return

    def reliability_color(value):
        red = [220, 60, 60, 210]
        yellow = [240, 190, 40, 210]
        green = [60, 170, 70, 210]

        if metric == "On-Time":
            return green if value >= 80 else yellow if value >= 70 else red
        if metric == "Avg. Delay":
            return green if value <= 15 else yellow if value <= 25 else red
        if metric == "Cancellation":
            return green if value <= 1 else yellow if value <= 3 else red
        if metric == "Diversion":
            return green if value <= 0.5 else yellow if value <= 1 else red

        return yellow

    map_df["map_color"] = map_df[column].apply(
        reliability_color
    )

    max_flights = map_df["flights"].max()

    map_df["radius"] = (
        map_df["flights"] / max_flights * 40000 + 5000
        if max_flights > 0 else 5000
    )

    map_df["flights_display"] = map_df["flights"].map(
        lambda x: f"{x:,.0f}"
    )

    map_df["on_time_display"] = map_df[
        "on_time_rate_pct"
    ].map(
        lambda x: f"{x:.2f}"
    )

    map_df["delay_display"] = map_df[
        "avg_delay_minutes"
    ].map(
        lambda x: f"{x:.2f}"
    )

    reset = st.button(
        "↺ Reset map",
        key="airport_map_center",
    )

    latitude, longitude, zoom = 39.5, -98.35, 3

    if specific_mode and selected and not reset:
        latitude = map_df["latitude"].mean()
        longitude = map_df["longitude"].mean()

        span = max(
            map_df["latitude"].max() - map_df["latitude"].min(),
            map_df["longitude"].max() - map_df["longitude"].min(),
        )

        if span < 3:
            zoom = 7
        elif span < 7:
            zoom = 6
        elif span < 15:
            zoom = 5
        elif span < 30:
            zoom = 4

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position="[longitude, latitude]",
        get_radius="radius",
        get_fill_color="map_color",
        pickable=True,
        auto_highlight=True,
    )

    tooltip = {
        "html": (
            "<b>{city} ({airport_code})</b><br/>"
            "{airport_name}<br/>"
            "{state_code}<br/>"
            "Flights: {flights_display}<br/>"
            "On-Time: {on_time_display}%<br/>"
            "Avg. Delay: {delay_display} min"
        )
    }

    if reset:
        st.session_state["airport_map_reset"] = (
            st.session_state.get("airport_map_reset", 0) + 1
        )

    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=pdk.ViewState(
            latitude=latitude,
            longitude=longitude,
            zoom=zoom,
        ),
        map_style="light",
        tooltip=tooltip,
    )

    st.pydeck_chart(
        deck,
        width="stretch",
        key=f"airport_map_{st.session_state.get('airport_map_reset', 0)}",
    )