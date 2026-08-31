import numpy as np
import plotly.graph_objects as go
import streamlit as st


def show_route_map(
    df,
    period_count,
):
    st.subheader("Route Map")
    color_by = st.radio(
        "Color by",
        ["Flights", "On-Time", "Avg. Delay"],
        horizontal=True,
        key="route_map_color",
    )

    routes = df.copy()

    route_limit = st.session_state.get(
        "route_limit",
        "Top 20",
    )

    # -------------------------------------------------
    # Use exactly the routes selected by Route Comparison
    # -------------------------------------------------

    if route_limit == "Specific":
        selected = st.session_state.get(
            "route_selected",
            [],
        )
    else:
        selected = st.session_state.get(
            "route_comparison_selection",
            [],
        )

    if selected:
        routes = routes[
            routes["route"].isin(selected)
        ].copy()
    else:
        st.info(
            "No routes selected for the map."
        )
        return

    # -------------------------------------------------
    # Coordinates
    # -------------------------------------------------

    routes = routes.dropna(
        subset=[
            "origin_latitude",
            "origin_longitude",
            "dest_latitude",
            "dest_longitude",
        ]
    ).copy()

    if routes.empty:
        st.info(
            "No route coordinates available "
            "for the current selection."
        )
        return

    # -------------------------------------------------
    # Line width according to number of flights
    #
    # sqrt prevents the largest routes from completely
    # dominating the map.
    # -------------------------------------------------

    min_flights = routes["flights"].min()
    max_flights = routes["flights"].max()

    if max_flights == min_flights:
        routes["line_width"] = 3.0
    else:
        min_sqrt = np.sqrt(min_flights)
        max_sqrt = np.sqrt(max_flights)

        routes["line_width"] = (
            1.0
            + (
                np.sqrt(routes["flights"])
                - min_sqrt
            )
            / (
                max_sqrt
                - min_sqrt
            )
            * 3.0
        )   

    # -------------------------------------------------
    # Map
    # With 20 / 50 / Specific routes one trace per route
    # is fine and gives us proper hover information.
    # -------------------------------------------------

    fig = go.Figure()

    def route_color(row):
        if color_by == "On-Time":
            return (
                "green"
                if row.on_time_rate_pct >= 80
                else "gold"
                if row.on_time_rate_pct >= 70
                else "red"
            )

        if color_by == "Avg. Delay":
            return (
                "green"
                if row.avg_arr_delay_minutes <= 15
                else "gold"
                if row.avg_arr_delay_minutes <= 25
                else "red"
            )

        return "rgba(31, 119, 180, 0.65)"




    for row in routes.itertuples():

        route_label = (
            f"{row.origin_airport_name} "
            f"({row.origin_airport_code}) → "
            f"{row.dest_airport_name} "
            f"({row.dest_airport_code})"
        )

        hover_text = (
            f"<b>{route_label}</b><br>"
            f"Flights: {row.flights:,.0f}<br>"
            f"On-Time: {row.on_time_rate_pct:.2f}%<br>"
            f"Avg. Arrival Delay: "
            f"{row.avg_arr_delay_minutes:.2f} min"
        )

        fig.add_trace(
            go.Scattermap(
                lat=[
                    row.origin_latitude,
                    row.dest_latitude,
                ],
                lon=[
                    row.origin_longitude,
                    row.dest_longitude,
                ],
                mode="lines",
                line={
                    "width": row.line_width,
                    "color": route_color(row),
                },
                text=[
                    hover_text,
                    hover_text,
                ],
                hovertemplate=(
                    "%{text}"
                    "<extra></extra>"
                ),
                showlegend=False,
            )
        )

    # -------------------------------------------------
    # Airport markers
    # -------------------------------------------------

    airport_rows = []

    for row in routes.itertuples():
        airport_rows.append(
            {
                "code": row.origin_airport_code,
                "name": row.origin_airport_name,
                "lat": row.origin_latitude,
                "lon": row.origin_longitude,
            }
        )

        airport_rows.append(
            {
                "code": row.dest_airport_code,
                "name": row.dest_airport_name,
                "lat": row.dest_latitude,
                "lon": row.dest_longitude,
            }
        )

    # remove duplicate airports
    airports = {
        row["code"]: row
        for row in airport_rows
    }

    fig.add_trace(
        go.Scattermap(
            lat=[
                row["lat"]
                for row in airports.values()
            ],
            lon=[
                row["lon"]
                for row in airports.values()
            ],
            mode="markers",
            text=[
                f"{row['name']} ({row['code']})"
                for row in airports.values()
            ],
            marker={
                "size": 6,
                "color": "#D62728",
                "opacity": 0.8,
            },
            hovertemplate=(
                "<b>%{text}</b>"
                "<extra></extra>"
            ),
            showlegend=False,
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
        width="stretch",
        config={
            "scrollZoom": False,
            "displaylogo": False,
        },
    )

    st.caption(
        f"{len(routes):,} routes shown · "
        "Line width represents number of flights"
    )