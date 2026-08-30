import altair as alt
import pandas as pd
import streamlit as st

from dashboard.views.airport_charts import (
    color_range,
)


def period_axis(df):
    periods = sorted(
        df["period"]
        .dropna()
        .unique()
    )

    if len(periods) > 9:
        periods = [
            period
            for period in periods
            if pd.Timestamp(period).month
            in [1, 4, 7, 10]
        ]

    return alt.Axis(
        format="%Y-%m",
        values=[
            pd.Timestamp(period)
            .to_pydatetime()
            for period in periods
        ],
    )


def color_encoding(color_domain):
    return alt.Color(
        "airport_code:N",
        title="Airport",
        scale=alt.Scale(
            domain=color_domain,
            range=color_range(color_domain),
        ),
        legend=alt.Legend(
            orient="right",
            labelLimit=220,
        ),
    )


def kpi_chart(
    df,
    column,
    title,
    color_domain,
):
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
                axis=alt.Axis(
                    orient="right"
                ),
                scale=alt.Scale(
                    zero=False
                ),
            ),
            color=color_encoding(
                color_domain
            ),
            tooltip=[
                alt.Tooltip(
                    "airport_code:N",
                    title="Airport",
                ),
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


def flights_chart(
    df,
    color_domain,
):
    flights_df = df[
        df["airport_code"]
        != "All Airports"
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
                axis=alt.Axis(
                    orient="left"
                ),
            ),
            color=color_encoding(
                color_domain
            ),
            tooltip=[
                alt.Tooltip(
                    "airport_code:N",
                    title="Airport",
                ),
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
        alt.layer(
            flights,
            kpi,
        )
        .resolve_scale(
            y="independent"
        )
        .properties(height=520)
    )


def show_timeseries(
    df,
    color_domain,
):
    if df.empty:
        st.info(
            "No data available for the selected period."
        )
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
        [
            "period",
            "airport_code",
        ]
    )

    tabs = st.tabs([
        "On-Time",
        "Avg. Delay",
        "Cancellation & Diversion",
    ])

    charts = [
        (
            "on_time_rate_pct",
            "On-Time Rate (%)",
        ),
        (
            "avg_delay_minutes",
            "Avg. Delay (Min)",
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

    for tab, (
        column,
        title,
    ) in zip(tabs, charts):

        with tab:
            st.caption(
                "Solid line = Flights · "
                "Dashed line = KPI"
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