import streamlit as st

from dashboard.data import load_periods
from dashboard.views.airlines import show_airlines
from dashboard.views.airports import show_airports
from dashboard.views.routes import show_routes
from dashboard.views.flights import show_flights


st.set_page_config(
    page_title="Airline Reliability Dashboard",
    page_icon="✈️",
    layout="wide",
)

st.title("✈️ Airline Reliability Dashboard")

periods = load_periods()

if periods.empty:
    st.warning("No Gold data available.")
    st.stop()

years = sorted(
    periods["year"].astype(int).unique(),
    reverse=True,
)

selected_year = st.sidebar.selectbox(
    "Year",
    years,
)

months = sorted(
    periods.loc[
        periods["year"] == selected_year,
        "month",
    ]
    .astype(int)
    .unique(),
    reverse=True,
)

selected_month = st.sidebar.selectbox(
    "Month",
    months,
)

st.sidebar.markdown("---")
st.sidebar.write(
    f"Selected period: "
    f"**{selected_year}-{selected_month:02d}**"
)

tab_airlines, tab_airports, tab_routes, tab_flights = st.tabs(
    [
        "Airlines",
        "Airports",
        "Routes",
        "Flights",
    ]
)

with tab_airlines:
    show_airlines(
        selected_year,
        selected_month,
    )

with tab_airports:
    show_airports(
        selected_year,
        selected_month,
    )

with tab_routes:
    show_routes(
        selected_year,
        selected_month,
    )

with tab_flights:
    show_flights(
        selected_year,
        selected_month,
    )
