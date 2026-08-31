import pandas as pd
import streamlit as st


WEIGHTED_COLUMNS = [
    "avg_dep_delay_minutes", "avg_arr_delay_minutes",
    "on_time_rate_pct", "cancellation_rate_pct", "diversion_rate_pct",
]

DETAIL_FORMAT = {
    "on_time_rate_pct": "{:.2f}",
    "avg_dep_delay_minutes": "{:.2f}",
    "avg_arr_delay_minutes": "{:.2f}",
    "cancellation_rate_pct": "{:.2f}",
    "diversion_rate_pct": "{:.2f}",
}

DETAIL_LABELS = {
    "route": "Route",
    "origin_city": "Origin City",
    "origin_state_code": "Origin State",
    "dest_city": "Destination City",
    "dest_state_code": "Destination State",
    "flights": "Flights",
    "on_time_rate_pct": "On-Time %",
    "avg_dep_delay_minutes": "Avg. Dep. Delay",
    "avg_arr_delay_minutes": "Avg. Arr. Delay",
    "cancellation_rate_pct": "Cancellation %",
    "diversion_rate_pct": "Diversion %",
}


def add_all_routes(df):
    flights = df["flights"].sum()

    total = {
        "origin_airport_id": None, "origin_airport_code": None,
        "origin_city": "All Routes", "origin_state_code": None,
        "origin_state": None,
        "dest_airport_id": None, "dest_airport_code": None,
        "dest_city": "All Routes", "dest_state_code": None,
        "dest_state": None,
        "route": "All Routes", "flights": flights,
    }

    for col in WEIGHTED_COLUMNS:
        total[col] = (
            (df[col] * df["flights"]).sum() / flights
            if flights else 0
        )

    return pd.concat([pd.DataFrame([total]), df], ignore_index=True)


def show_kpis(values, route_count):
    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Flights", f"{values['flights']:,.0f}")
    c2.metric("On-Time Rate", f"{values['on_time_rate_pct']:.2f} %")
    c3.metric(
        "Avg. Departure Delay",
        f"{values['avg_dep_delay_minutes']:.2f} min",
    )

    cancel_diversion = (
        values["cancellation_rate_pct"]
        + values["diversion_rate_pct"]
    )

    c4.metric(
        "Cancellation & Diversion Rate",
        f"{cancel_diversion:.2f} %",
    )


def show_route_details(all_df, df):
    st.write("Routes")

    sort_mode = st.radio(
        "Route list",
        ["Origin City", "Flights", "Route", "Destination City"],
        horizontal=True,
        key="route_selection_sort",
    )

    routes = df.copy()

    if sort_mode == "Origin City":
        routes = routes.sort_values([
            "origin_city", "dest_city",
            "origin_airport_code", "dest_airport_code",
        ])
    elif sort_mode == "Flights":
        routes = routes.sort_values(
            ["flights", "route"], ascending=[False, True]
        )
    elif sort_mode == "Route":
        routes = routes.sort_values("route")
    else:
        routes = routes.sort_values([
            "dest_city", "origin_city",
            "dest_airport_code", "origin_airport_code",
        ])

    route_codes = routes["route"].tolist()
    labels = {}

    for row in routes.itertuples(index=False):
        display = (
            f"{row.origin_city} ({row.origin_airport_code}) → "
            f"{row.dest_city} ({row.dest_airport_code})"
        )

        if sort_mode == "Flights":
            labels[row.route] = f"{row.flights:,.0f} · {display}"
        elif sort_mode == "Route":
            labels[row.route] = (
                f"{row.route} · {row.origin_city} → {row.dest_city}"
            )
        elif sort_mode == "Destination City":
            labels[row.route] = (
                f"{row.dest_city} ({row.dest_airport_code}) · "
                f"from {row.origin_city} ({row.origin_airport_code})"
            )
        else:
            labels[row.route] = display

    specific_mode = (
        st.session_state.get("route_limit", "Top 20") == "Specific"
    )

    previous = st.session_state.get("route_selected", [])
    previous = [route for route in previous if route in route_codes]

    widget_key = "_route_specific_selection"

    if widget_key not in st.session_state:
        st.session_state[widget_key] = previous

    def save_routes():
        st.session_state["route_selected"] = st.session_state[widget_key]

    selected = st.multiselect(
        "Select routes",
        options=route_codes,
        format_func=lambda route: labels[route],
        key=widget_key,
        on_change=save_routes,
        disabled=not specific_mode,
    )

    st.session_state["route_selected"] = selected

    if specific_mode:
        st.caption(
            f"{len(selected)} route"
            f"{'' if len(selected) == 1 else 's'} selected"
        )
    else:
        st.caption(
            "Select 'Specific' in Route Comparison "
            "to activate this selection."
        )

    detail_routes = (
        selected if specific_mode
        else st.session_state.get("route_comparison_selection", [])
    )

    mask = all_df["route"].isin(detail_routes)

    columns = [
        "route", "origin_city", "origin_state_code",
        "dest_city", "dest_state_code", "flights",
        "on_time_rate_pct", "avg_dep_delay_minutes",
        "avg_arr_delay_minutes", "cancellation_rate_pct",
        "diversion_rate_pct",
    ]

    st.subheader("Route Details")

    st.dataframe(
        all_df.loc[mask, columns].style.format(DETAIL_FORMAT),
        width="stretch",
        hide_index=True,
        height=int(min(37 + max(int(mask.sum()), 1) * 35, 1000)),
        column_config=DETAIL_LABELS,
    )

    return selected