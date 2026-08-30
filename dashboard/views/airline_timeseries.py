import altair as alt
import pandas as pd
import streamlit as st

from dashboard.views.airline_charts import COLORS, get_color_range


def period_axis(df):
    periods = sorted(df["period"].dropna().unique())

    if len(periods) > 9:
        periods = [
            p for p in periods
            if pd.Timestamp(p).month in [1, 4, 7, 10]
        ]

    return alt.Axis(
        format="%Y-%m",
        values=[
            pd.Timestamp(p).to_pydatetime()
            for p in periods
        ],
    )


def color_encoding(color_domain):
    return alt.Color(
        "airline_name:N",
        title="Airline",
        scale=alt.Scale(
            domain=color_domain,
            range=get_color_range(color_domain),
        ),
        legend=alt.Legend(
            orient="right",
            labelLimit=220,
        ),
    )


def kpi_chart(df, column, title, color_domain):
    return (
        alt.Chart(df)
        .mark_line(
            point=True,
            strokeDash=[6, 4],
        )
        .encode(
            x=alt.X(
                "period:T",
                title=None,
                axis=period_axis(df),
            ),
            y=alt.Y(
                f"{column}:Q",
                title=title,
                axis=alt.Axis(orient="right"),
                scale=alt.Scale(zero=False),
            ),
            color=color_encoding(color_domain),
            tooltip=[
                alt.Tooltip("airline_name:N", title="Airline"),
                alt.Tooltip(
                    "period:T",
                    title="Month",
                    format="%Y-%m",
                ),
                alt.Tooltip(
                    f"{column}:Q",
                    title=title,
                    format=".2f",
                ),
            ],
        )
    )


def flights_chart(df, color_domain):
    flights_df = df[
        df["airline_name"] != "All Airlines"
    ]

    return (
        alt.Chart(flights_df)
        .mark_line(point=True)
        .encode(
            x=alt.X(
                "period:T",
                title=None,
                axis=period_axis(df),
            ),
            y=alt.Y(
                "flights:Q",
                title="Flights",
                axis=alt.Axis(orient="left"),
            ),
            color=color_encoding(color_domain),
            tooltip=[
                alt.Tooltip("airline_name:N", title="Airline"),
                alt.Tooltip(
                    "period:T",
                    title="Month",
                    format="%Y-%m",
                ),
                alt.Tooltip(
                    "flights:Q",
                    title="Flights",
                    format=",.0f",
                ),
            ],
        )
    )


def combined_chart(kpi, flights):
    return (
        alt.layer(flights, kpi)
        .resolve_scale(y="independent")
        .properties(height=520)
    )


def show_timeseries(df, color_domain):
    if df.empty:
        st.info("No data available for the selected period.")
        return

    df = df.copy()
    df["period"] = pd.to_datetime(
        dict(
            year=df["year"],
            month=df["month"],
            day=1,
        )
    )
    df["cancel_diversion_rate_pct"] = (
        df["cancellation_rate_pct"]
        + df["diversion_rate_pct"]
    )

    df = df.sort_values(
        ["period", "airline_name"]
    )

    tabs = st.tabs([
        "On-Time",
        "Departure Delay",
        "Cancellation & Diversion",
    ])

    charts = [
        (
            "on_time_rate_pct",
            "On-Time Rate (%)",
        ),
        (
            "avg_dep_delay_minutes",
            "Avg. Departure Delay (Min)",
        ),
        (
            "cancel_diversion_rate_pct",
            "Cancellation & Diversion Rate (%)",
        ),
    ]

    flights = flights_chart(
        df,
        color_domain,
    )

    for tab, (column, title) in zip(tabs, charts):
        with tab:
            st.caption(
                "Solid line = Flights · Dashed line = KPI"
            )
            st.altair_chart(
                combined_chart(
                    kpi_chart(
                        df,
                        column,
                        title,
                        color_domain,
                    ),
                    flights,
                ),
                width="stretch",
            )
            