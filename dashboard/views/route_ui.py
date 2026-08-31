# dashboard/views/route_ui.py

import pandas as pd
import streamlit as st


WEIGHTED_COLUMNS = [
    "avg_dep_delay_minutes",
    "avg_arr_delay_minutes",
    "on_time_rate_pct",
    "cancellation_rate_pct",
    "diversion_rate_pct",
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
        "origin_airport_id": None,
        "origin_airport_code": None,
        "origin_airport_name": None,
        "origin_city": "All Routes",
        "origin_state_code": None,
        "origin_state": None,
        "dest_airport_id": None,
        "dest_airport_code": None,
        "dest_airport_name": None,
        "dest_city": "All Routes",
        "dest_state_code": None,
        "dest_state": None,
        "route": "All Routes",
        "flights": flights,
    }

    for column in [
        "dep_delay_flights",
        "dep_delay_sum_minutes",
        "arr_delay_flights",
        "arr_delay_sum_minutes",
    ]:
        if column in df.columns:
            total[column] = df[column].sum()

    if (
        "dep_delay_flights" in df.columns
        and "dep_delay_sum_minutes" in df.columns
    ):
        dep_delay_flights = total["dep_delay_flights"]
        total["avg_dep_delay_minutes"] = (
            total["dep_delay_sum_minutes"] / dep_delay_flights
            if dep_delay_flights
            else 0
        )

    if (
        "arr_delay_flights" in df.columns
        and "arr_delay_sum_minutes" in df.columns
    ):
        arr_delay_flights = total["arr_delay_flights"]
        total["avg_arr_delay_minutes"] = (
            total["arr_delay_sum_minutes"] / arr_delay_flights
            if arr_delay_flights
            else 0
        )

    for col in [
        "on_time_rate_pct",
        "cancellation_rate_pct",
        "diversion_rate_pct",
    ]:
        total[col] = (
            (df[col] * df["flights"]).sum() / flights
            if flights
            else 0
        )

    return pd.concat(
        [pd.DataFrame([total]), df],
        ignore_index=True,
    )


def show_kpis(values, route_count):
    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Flights",
        f"{values['flights']:,.0f}",
    )

    c2.metric(
        "On-Time Rate",
        f"{values['on_time_rate_pct']:.2f} %",
    )

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


def filter_route_set(df, route_set, period_count):
    if route_set == "> 0.1% of all flights":
        min_flights = df["flights"].sum() * 0.001
    elif route_set == "> 100 flights p.m.":
        min_flights = 100 * period_count
    else:
        min_flights = None

    if min_flights is None:
        return df.copy(), None

    return (
        df[df["flights"] > min_flights].copy(),
        min_flights,
    )


def show_route_details(all_df, df, period_count):
    st.write("Routes")

    specific_mode = (
        st.session_state.get(
            "route_limit",
            "Top 20",
        )
        == "Specific"
    )

    route_set = st.session_state.get(
        "route_specific_route_set",
        st.session_state.get(
            "route_set",
            "> 100 flights p.m.",
        ),
    )

    routes, _ = filter_route_set(
        df,
        route_set,
        period_count,
    )

    sort_mode = st.radio(
        "Sort by",
        ["Flights", "Alphabetical"],
        horizontal=True,
        key="route_selection_sort",
        disabled=not specific_mode,
    )

    origin_df = (
        routes[
            [
                "origin_airport_code",
                "origin_airport_name",
                "origin_city",
                "origin_state_code",
            ]
        ]
        .dropna(subset=["origin_airport_code"])
        .drop_duplicates(subset=["origin_airport_code"])
        .sort_values(
            ["origin_city", "origin_airport_code"]
        )
    )

    dest_df = (
        routes[
            [
                "dest_airport_code",
                "dest_airport_name",
                "dest_city",
                "dest_state_code",
            ]
        ]
        .dropna(subset=["dest_airport_code"])
        .drop_duplicates(subset=["dest_airport_code"])
        .sort_values(
            ["dest_city", "dest_airport_code"]
        )
    )

    origin_labels = {
        row.origin_airport_code: (
            f"{row.origin_airport_name} "
            f"({row.origin_airport_code}) · "
            f"{row.origin_city}, {row.origin_state_code}"
        )
        for row in origin_df.itertuples(index=False)
    }

    dest_labels = {
        row.dest_airport_code: (
            f"{row.dest_airport_name} "
            f"({row.dest_airport_code}) · "
            f"{row.dest_city}, {row.dest_state_code}"
        )
        for row in dest_df.itertuples(index=False)
    }

    c1, c2 = st.columns(2)

    origin_airport = c1.selectbox(
        "Origin airport",
        ["All"] + list(origin_labels),
        format_func=lambda code: (
            "All origin airports"
            if code == "All"
            else origin_labels[code]
        ),
        key="route_origin_airport",
        disabled=not specific_mode,
    )

    dest_airport = c2.selectbox(
        "Destination airport",
        ["All"] + list(dest_labels),
        format_func=lambda code: (
            "All destination airports"
            if code == "All"
            else dest_labels[code]
        ),
        key="route_dest_airport",
        disabled=not specific_mode,
    )

    if specific_mode and origin_airport != "All":
        routes = routes[
            routes["origin_airport_code"] == origin_airport
        ].copy()

    if specific_mode and dest_airport != "All":
        routes = routes[
            routes["dest_airport_code"] == dest_airport
        ].copy()

    if sort_mode == "Flights":
        routes = routes.sort_values(
            [
                "flights",
                "origin_airport_code",
                "dest_airport_code",
            ],
            ascending=[False, True, True],
        )
    else:
        routes = routes.sort_values(
            [
                "origin_city",
                "origin_airport_code",
                "dest_city",
                "dest_airport_code",
            ]
        )

    route_codes = routes["route"].tolist()

    labels = {
        row.route: (
            (
                f"{row.flights:,.0f} · "
                if sort_mode == "Flights"
                else ""
            )
            + (
                f"{row.origin_city} "
                f"({row.origin_airport_code}) → "
                f"{row.dest_city} "
                f"({row.dest_airport_code})"
            )
        )
        for row in routes.itertuples(index=False)
    }

    found_key = "route_found_routes"
    selected_key = "route_selected"
    widget_key = "_route_specific_selection"

    valid_found = [
        route
        for route in st.session_state.get(
            found_key,
            [],
        )
        if route in route_codes
    ]

    st.session_state[found_key] = valid_found

    found_routes = st.multiselect(
        "Found routes",
        options=route_codes,
        format_func=lambda route: labels[route],
        key=found_key,
        disabled=not specific_mode,
    )

    selected_routes = [
        route
        for route in st.session_state.get(
            selected_key,
            [],
        )
        if route in set(df["route"])
    ]

    def add_routes():
        st.session_state[selected_key] = list(
            dict.fromkeys(
                st.session_state.get(
                    selected_key,
                    [],
                )
                + st.session_state.get(
                    found_key,
                    [],
                )
            )
        )
        st.session_state[found_key] = []
        st.session_state[
            "route_selection_cleared"
        ] = False

    def clear_airports():
        st.session_state[
            "route_origin_airport"
        ] = "All"
        st.session_state[
            "route_dest_airport"
        ] = "All"
        st.session_state[found_key] = []

    def clear_selected():
        st.session_state[selected_key] = []
        st.session_state[widget_key] = []
        st.session_state[
            "route_selection_cleared"
        ] = True

    def save_routes():
        st.session_state[selected_key] = (
            st.session_state[widget_key]
        )
        st.session_state[
            "route_selection_cleared"
        ] = False

    add_col, clear_airports_col, clear_selected_col = (
        st.columns(3)
    )

    add_col.button(
        "Add selected routes",
        key="route_add_found",
        on_click=add_routes,
        disabled=(
            not specific_mode
            or not found_routes
        ),
    )

    clear_airports_col.button(
        "Clear selection",
        key="route_clear_selection",
        on_click=clear_airports,
        disabled=not specific_mode,
    )

    clear_selected_col.button(
        "Clear selected routes",
        key="route_clear_selected",
        on_click=clear_selected,
        disabled=(
            not specific_mode
            or not selected_routes
        ),
    )

    selected_routes = st.session_state.get(
        selected_key,
        selected_routes,
    )

    selected_df = df[
        df["route"].isin(selected_routes)
    ]

    selected_labels = {
        row.route: (
            f"{row.origin_city} "
            f"({row.origin_airport_code}) → "
            f"{row.dest_city} "
            f"({row.dest_airport_code})"
        )
        for row in selected_df.itertuples(index=False)
    }

    selected_routes = [
        route
        for route in selected_routes
        if route in selected_labels
    ]

    st.session_state[widget_key] = selected_routes

    selected = st.multiselect(
        "Select routes",
        options=selected_routes,
        format_func=lambda route: selected_labels[route],
        key=widget_key,
        on_change=save_routes,
        disabled=not specific_mode,
    )

    st.session_state[selected_key] = selected

    if specific_mode:
        st.caption(
            f"{len(route_codes)} routes found · "
            f"{len(selected)} selected"
        )
    else:
        st.caption(
            "Select 'Specific' in Route Comparison "
            "to activate route selection."
        )

    if (
        specific_mode
        and st.session_state.get(
            "route_selection_cleared",
            False,
        )
    ):
        detail_routes = []
    elif specific_mode and selected:
        detail_routes = selected
    else:
        detail_routes = st.session_state.get(
            "route_comparison_selection",
            [],
        )

    mask = all_df["route"].isin(detail_routes)

    columns = [
        "route",
        "origin_city",
        "origin_state_code",
        "dest_city",
        "dest_state_code",
        "flights",
        "on_time_rate_pct",
        "avg_dep_delay_minutes",
        "avg_arr_delay_minutes",
        "cancellation_rate_pct",
        "diversion_rate_pct",
    ]

    st.subheader("Route Details")

    st.dataframe(
        all_df.loc[
            mask,
            columns,
        ].style.format(
            DETAIL_FORMAT
        ),
        width="stretch",
        hide_index=True,
        height=int(
            min(
                37
                + max(
                    int(mask.sum()),
                    1,
                )
                * 35,
                1000,
            )
        ),
        column_config=DETAIL_LABELS,
    )

    return selected