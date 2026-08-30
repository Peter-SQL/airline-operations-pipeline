import streamlit as st

from dashboard.data import load_periods
from dashboard.helpers import select_periods
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

selected_periods = select_periods(periods)

if not selected_periods:
    st.warning("Select at least one period.")
    st.stop()

for key in [
    "airline_kpi_start", "airline_kpi_end",
    "airport_kpi_start", "airport_kpi_end",
]:
    saved = f"saved_{key}"
    if key in st.session_state:
        st.session_state[saved] = st.session_state[key]
    elif saved in st.session_state:
        st.session_state[key] = st.session_state[saved]

view = st.segmented_control(
    "View",
    ["Airlines", "Airports", "Routes", "Flights"],
    default="Airlines",
    key="dashboard_view",
    label_visibility="collapsed",
)

if view == "Airlines":
    show_airlines(selected_periods)
elif view == "Airports":
    show_airports(selected_periods)
elif view == "Routes":
    show_routes(selected_periods)
else:
    show_flights(selected_periods)