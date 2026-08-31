import pandas as pd
import streamlit as st


WEIGHTED_COLUMNS = [
    "avg_delay_minutes", "on_time_rate_pct",
    "cancellation_rate_pct", "diversion_rate_pct",
]

DETAIL_FORMAT = {
    "on_time_rate_pct": "{:.2f}",
    "avg_delay_minutes": "{:.2f}",
    "cancellation_rate_pct": "{:.2f}",
    "diversion_rate_pct": "{:.2f}",
}

DETAIL_LABELS = {
    "airport_code": "Code",
    "airport_name": "Airport",
    "city": "City",
    "state_code": "State",
    "flights": "Flights",
    "on_time_rate_pct": "On-Time %",
    "avg_delay_minutes": "Avg. Delay",
    "cancellation_rate_pct": "Cancellation %",
    "diversion_rate_pct": "Diversion %",
}


def airport_label(row):
    return f"{row['city']} ({row['airport_code']})"


def add_all_airports(df):
    flights = df["flights"].sum()

    total = {
        "airport_id": None, "airport_code": "n/a",
        "airport_name": "All Airports", "city": "All Airports",
        "state_code": None, "state": None,
        "latitude": None, "longitude": None, "flights": flights,
    }

    for col in WEIGHTED_COLUMNS:
        total[col] = (
            (df[col] * df["flights"]).sum() / flights
            if flights else 0
        )

    return pd.concat([pd.DataFrame([total]), df], ignore_index=True)


def set_all_airports(airports, value):
    for airport in airports:
        st.session_state[f"airport_{airport}"] = value

    st.session_state["airport_all"] = value


def show_kpis(values, airport_count, operation):
    arrival = str(operation).lower().startswith("arr")

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
        "Avg. Delay",
        f"{values['avg_delay_minutes']:.2f} min",
    )

    if arrival:
        c4.metric(
            "Cancellation & Diversion Rate",
            "n/a",
        )
    else:
        cancel_diversion = (
            values["cancellation_rate_pct"]
            + values["diversion_rate_pct"]
        )

        c4.metric(
            "Cancellation & Diversion Rate",
            f"{cancel_diversion:.2f} %",
        )

def show_airport_details(all_df, df, operation):
    st.write("Airports")

    sort_mode = st.radio(
        "Airport list",
        ["City", "Flights", "Code", "State + City"],
        horizontal=True,
        key="airport_selection_sort",
    )

    airports = df.copy()

    if sort_mode == "City":
        airports = airports.sort_values(["city", "airport_code"])

    elif sort_mode == "Flights":
        airports = airports.sort_values(
            ["flights", "city"],
            ascending=[False, True],
        )

    elif sort_mode == "Code":
        airports = airports.sort_values("airport_code")

    else:
        airports = airports.sort_values(
            ["state", "city", "airport_code"]
        )

    codes = airports["airport_code"].tolist()
    labels = {}

    for row in airports.itertuples(index=False):
        if sort_mode == "Flights":
            labels[row.airport_code] = (
                f"{row.flights:,.0f} · "
                f"{row.city} ({row.airport_code}) · "
                f"{row.airport_name}"
            )

        elif sort_mode == "Code":
            labels[row.airport_code] = (
                f"{row.airport_code} · "
                f"{row.city} · "
                f"{row.airport_name}"
            )

        elif sort_mode == "State + City":
            labels[row.airport_code] = (
                f"{row.state_code} · "
                f"{row.city} ({row.airport_code}) · "
                f"{row.airport_name}"
            )

        else:
            labels[row.airport_code] = (
                f"{row.city} ({row.airport_code}) · "
                f"{row.airport_name}"
            )

    specific_mode = (
        st.session_state.get("airport_limit", "Top 20")
        == "Specific"
    )

    previous = st.session_state.get("airport_selected", [])
    previous = [code for code in previous if code in codes]

    widget_key = "_airport_specific_selection"

    if widget_key not in st.session_state:
        st.session_state[widget_key] = previous

    def save_airports():
        st.session_state["airport_selected"] = (
            st.session_state[widget_key]
        )

    selected = st.multiselect(
        "Select airports",
        options=codes,
        format_func=lambda code: labels[code],
        key=widget_key,
        on_change=save_airports,
        disabled=not specific_mode,
    )

    st.session_state["airport_selected"] = selected

    if specific_mode:
        st.caption(
            f"{len(selected)} airport"
            f"{'' if len(selected) == 1 else 's'} selected"
        )
    else:
        st.caption(
            "Select 'Specific' in Airport Comparison "
            "to activate this selection."
        )

    if specific_mode:
        detail_codes = selected
    else:
        detail_codes = st.session_state.get(
            "airport_comparison_selection",
            [],
        )

    mask = all_df["airport_code"].isin(detail_codes)

    columns = [
        "airport_code", "airport_name", "city", "state_code",
        "flights", "on_time_rate_pct", "avg_delay_minutes",
    ]

    if not str(operation).lower().startswith("arr"):
        columns += [
            "cancellation_rate_pct",
            "diversion_rate_pct",
        ]

    st.subheader("Airport Details")

    st.dataframe(
        all_df.loc[mask, columns].style.format(DETAIL_FORMAT),
        width="stretch",
        hide_index=True,
        height=int(min(37 + max(int(mask.sum()), 1) * 35, 1000)),
        column_config=DETAIL_LABELS,
    )

    return selected