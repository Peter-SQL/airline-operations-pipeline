import streamlit as st

from dashboard.helpers import highlight_total

DETAIL_COLUMNS = [
    "airline_code",
    "airline_name",
    "flights",
    "on_time_rate_pct",
    "avg_dep_delay_minutes",
    "avg_arr_delay_minutes",
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
    "airline_code": "Code",
    "airline_name": "Airline",
    "flights": "Flights",
    "on_time_rate_pct": "On-Time %",
    "avg_dep_delay_minutes": "Avg. Dep. Delay",
    "avg_arr_delay_minutes": "Avg. Arr. Delay",
    "cancellation_rate_pct": "Cancellation %",
    "diversion_rate_pct": "Diversion %",
}


def set_all_airlines(airlines, value):
    for airline in airlines:
        st.session_state[f"airline_{airline}"] = value
    st.session_state["airline_all"] = value


def show_kpis(values):
    cancel_diversion = (
        values["cancellation_rate_pct"]
        + values["diversion_rate_pct"]
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Flights", f"{values['flights']:,.0f}")
    c2.metric("On-Time Rate", f"{values['on_time_rate_pct']:.2f} %")
    c3.metric(
        "Avg. Departure Delay",
        f"{values['avg_dep_delay_minutes']:.2f} min",
    )
    c4.metric(
        "Cancellation & Diversion Rate",
        f"{cancel_diversion:.2f} %",
    )


def show_airline_details(all_df, df):
    airlines = sorted(df["airline_name"].dropna().tolist())

    st.write("Airlines")
    cols = st.columns(5)

    selected = [
        airline
        for i, airline in enumerate(airlines)
        if cols[i % 5].checkbox(
            airline,
            value=True,
            key=f"airline_{airline}",
        )
    ]

    c1, c2, c3, _ = st.columns([1.4, 1, 1, 4])

    if c1.checkbox(
        "All Airlines",
        value=False,
        key="airline_all",
    ):
        selected.append("All Airlines")

    c2.button(
        "Check all",
        on_click=set_all_airlines,
        args=(airlines, True),
    )

    c3.button(
        "Uncheck all",
        on_click=set_all_airlines,
        args=(airlines, False),
    )

    st.toggle(
        "Use filter inside airline comparison",
        value=False,
        key="comparison_filter",
    )

    details = all_df[
        all_df["airline_name"].isin(selected)
    ][DETAIL_COLUMNS]

    st.subheader("Airline Details")

    st.dataframe(
        details.style
        .apply(highlight_total, axis=1)
        .format(DETAIL_FORMAT),
        width="stretch",
        hide_index=True,
        height=min(37 + len(details) * 35, 1000),
        column_config=DETAIL_LABELS,
    )

    return selected