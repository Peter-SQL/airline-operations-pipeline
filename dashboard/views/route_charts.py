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
    "Dep. Delay": "Avg. Departure Delay (Min)",
    "Arr. Delay": "Avg. Arrival Delay (Min)",
    "Cancellation": "Cancellation Rate (%)",
    "Diversion": "Diversion Rate (%)",
    "Flights": "Flights",
}


def color_range(domain):
    colors = []
    route_index = 0

    for value in domain:
        if value == "All Routes":
            colors.append(COLORS[0])
        else:
            colors.append(COLORS[1 + route_index % (len(COLORS) - 1)])
            route_index += 1

    return colors


def show_comparison(all_df, df, color_domain):
    st.subheader("Route Comparison")

    metrics = [
        "On-Time", "Dep. Delay", "Arr. Delay",
        "Cancellation", "Diversion", "Flights",
    ]

    metric = st.radio(
        "Choose metric", metrics, index=len(metrics) - 1,
        horizontal=True, key="route_metric",
    )

    c1, c2 = st.columns(2)

    sort_by = c1.radio(
        "Sort by", ["Metric", "Route"],
        horizontal=True, key="route_sort",
    )

    show = c2.radio(
        "Show", ["Top 20", "Top 50", "Specific"],
        horizontal=True, key="route_limit",
    )

    specific_mode = show == "Specific"

    route_set = st.radio(
        "Route set", ["All routes", "> 1% of all flights"],
        horizontal=True, key="route_set",
        disabled=specific_mode,
    )

    column = METRICS[metric]
    routes = df.copy()

    if specific_mode:
        selected = st.session_state.get("route_selected", [])

        if not selected:
            st.session_state["route_comparison_selection"] = []
            st.info("Select one or more routes below.")
            return

        routes = routes[routes["route"].isin(selected)].copy()

    elif route_set == "> 1% of all flights":
        min_flights = df["flights"].sum() * 0.01
        routes = routes[routes["flights"] > min_flights].copy()
        st.caption(
            f"Minimum: {min_flights:,.0f} flights · "
            f"{len(routes)} routes"
        )

    routes["display_route"] = routes["route"]
    routes["color_route"] = routes["route"]

    if not specific_mode:
        limit = 20 if show == "Top 20" else 50
        routes = routes.sort_values(column, ascending=False).head(limit)

    if sort_by == "Route":
        routes = routes.sort_values("route")
    else:
        routes = routes.sort_values(column, ascending=False)

    st.session_state["route_comparison_selection"] = (
        routes["route"].tolist()
    )

    if metric != "Flights":
        all_row = all_df[all_df["route"] == "All Routes"].copy()
        all_row["display_route"] = "All Routes"
        all_row["color_route"] = "All Routes"

        if sort_by == "Route":
            all_row_end = all_row.copy()
            all_row_end["display_route"] = "All Routes "
            routes = pd.concat(
                [all_row, routes, all_row_end],
                ignore_index=True,
            )

        elif route_set == "> 1% of all flights" or specific_mode:
            routes = pd.concat(
                [routes, all_row], ignore_index=True
            ).sort_values(column, ascending=False)

        else:
            routes = pd.concat(
                [all_row, routes], ignore_index=True
            )

    chart_order = routes["display_route"].tolist()

    bars = alt.Chart(routes).mark_bar().encode(
        x=alt.X(
            "display_route:N",
            title="Route",
            sort=chart_order,
            axis=alt.Axis(
                labelAngle=-45,
                labelOverlap=False,
                labelLimit=170,
            ),
        ),
        y=alt.Y(f"{column}:Q", title=Y_LABELS[metric]),
        color=alt.condition(
            alt.datum.color_route == "All Routes",
            alt.value("#FFD700"),
            alt.Color(
                "color_route:N",
                scale=alt.Scale(
                    domain=color_domain,
                    range=color_range(color_domain),
                ),
                legend=None,
            ),
        ),
        stroke=alt.condition(
            alt.datum.color_route == "All Routes",
            alt.value("#000000"),
            alt.value(None),
        ),
        strokeWidth=alt.condition(
            alt.datum.color_route == "All Routes",
            alt.value(6),
            alt.value(0),
        ),
        tooltip=[
            alt.Tooltip("display_route:N", title="Route"),
            alt.Tooltip("flights:Q", title="Flights", format=",.0f"),
            alt.Tooltip(
                f"{column}:Q",
                title=Y_LABELS[metric],
                format=".2f",
            ),
        ],
    )

    marker = (
        alt.Chart(routes[routes["color_route"] == "All Routes"])
        .mark_text(
            text="▼",
            fontSize=20,
            fontWeight="bold",
            dy=-13,
            color="black",
        )
        .encode(
            x=alt.X("display_route:N", sort=chart_order),
            y=f"{column}:Q",
        )
    )

    chart = alt.layer(bars, marker).properties(height=400)
    st.altair_chart(chart, width="stretch")