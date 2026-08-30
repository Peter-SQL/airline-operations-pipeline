import pandas as pd
import streamlit as st


WEIGHTED_COLUMNS = [
    "avg_delay_minutes", "on_time_rate_pct",
    "cancellation_rate_pct", "diversion_rate_pct",
]

DETAIL_COLUMNS = [
    "airport_code", "airport_name", "city", "state_code", "flights",
    "on_time_rate_pct", "avg_delay_minutes",
    "cancellation_rate_pct", "diversion_rate_pct",
]

DETAIL_FORMAT = {
    "on_time_rate_pct": "{:.2f}",
    "avg_delay_minutes": "{:.2f}",
    "cancellation_rate_pct": "{:.2f}",
    "diversion_rate_pct": "{:.2f}",
}

DETAIL_LABELS = {
    "airport_code": "Code", "airport_name": "Airport",
    "city": "City", "state_code": "State", "flights": "Flights",
    "on_time_rate_pct": "On-Time %",
    "avg_delay_minutes": "Avg. Delay",
    "cancellation_rate_pct": "Cancellation %",
    "diversion_rate_pct": "Diversion %",
}


def add_all_airports(df):
    flights = df["flights"].sum()
    total = {
        "airport_id": None, "airport_code": "n/a",
        "airport_name": "All Airports", "city": None,
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


def show_kpis(values, airport_count):
    cancel_diversion = (
        values["cancellation_rate_pct"]
        + values["diversion_rate_pct"]
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Flights", f"{values['flights']:,.0f}")
    c2.metric("On-Time Rate", f"{values['on_time_rate_pct']:.2f} %")
    c3.metric("Avg. Delay", f"{values['avg_delay_minutes']:.2f} min")
    c4.metric("Cancellation & Diversion Rate", f"{cancel_diversion:.2f} %")
    st.caption(f"{airport_count:,} airports")


def show_airport_details(all_df, df):
    airports = sorted(df["airport_code"].dropna().unique())
    st.write("Airports")

    cols = st.columns(5)
    selected = [
        airport for i, airport in enumerate(airports)
        if cols[i % 5].checkbox(
            airport, value=True, key=f"airport_{airport}"
        )
    ]

    c1, c2, c3, _ = st.columns([1.4, 1, 1, 4])

    if c1.checkbox("All Airports", value=False, key="airport_all"):
        selected.append("All Airports")

    c2.button(
        "Check all",
        on_click=set_all_airports,
        args=(airports, True),
    )
    c3.button(
        "Uncheck all",
        on_click=set_all_airports,
        args=(airports, False),
    )

    st.toggle(
        "Use filter inside Airport Comparison",
        value=False,
        key="airport_comparison_filter",
    )

    mask = all_df["airport_code"].isin(selected)
    if "All Airports" in selected:
        mask |= all_df["airport_code"].eq("n/a")

    details = all_df.loc[mask, DETAIL_COLUMNS]

    st.subheader("Airport Details")
    st.dataframe(
        details.style.format(DETAIL_FORMAT),
        width="stretch",
        hide_index=True,
        height=min(37 + len(details) * 35, 1000),
        column_config=DETAIL_LABELS,
    )

    return selected


def select_airport_trend_period(periods, selected_periods):
    available = sorted(
        (int(y), int(m))
        for y, m in periods[["year", "month"]].values
    )

    if not available:
        return []

    selected = sorted(
        (int(y), int(m))
        for y, m in selected_periods
    )

    start_default = (
        selected[0] if selected and selected[0] in available
        else available[0]
    )
    end_default = (
        selected[-1] if selected and selected[-1] in available
        else available[-1]
    )

    labels = [f"{y}-{m:02d}" for y, m in available]

    with st.sidebar:
        with st.container(border=True):
            st.subheader("Airport KPI Development")
            start = st.selectbox(
                "Start", labels,
                index=available.index(start_default),
                key="airport_kpi_start",
            )
            end = st.selectbox(
                "End", labels,
                index=available.index(end_default),
                key="airport_kpi_end",
            )

    start = int(start.replace("-", ""))
    end = int(end.replace("-", ""))

    return [
        p for p in available
        if start <= p[0] * 100 + p[1] <= end
    ]