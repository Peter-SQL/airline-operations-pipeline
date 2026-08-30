import altair as alt
import pandas as pd
import streamlit as st

from dashboard.views.airport_charts import color_range


def period_axis(df):
    periods = sorted(df["period"].dropna().unique())

    if len(periods) > 9:
        periods = [
            p for p in periods
            if pd.Timestamp(p).month in [1, 4, 7, 10]
        ]

    return alt.Axis(
        format="%Y-%m",
        values=[pd.Timestamp(p).to_pydatetime() for p in periods],
    )


def color_encoding(domain, colors):
    return alt.Color(
        "display_airport:N",
        title="Airport",
        scale=alt.Scale(domain=domain, range=colors),
        legend=alt.Legend(orient="right", labelLimit=260),
    )


def kpi_chart(df, column, title, domain, colors):
    return (
        alt.Chart(df)
        .mark_line(point=True, strokeDash=[6, 4])
        .encode(
            x=alt.X("period:T", title=None, axis=period_axis(df)),
            y=alt.Y(
                f"{column}:Q",
                title=title,
                axis=alt.Axis(orient="right"),
                scale=alt.Scale(zero=False),
            ),
            color=color_encoding(domain, colors),
            tooltip=[
                alt.Tooltip("display_airport:N", title="Airport"),
                alt.Tooltip("period:T", title="Month", format="%Y-%m"),
                alt.Tooltip(f"{column}:Q", title=title, format=".2f"),
            ],
        )
    )


def flights_chart(df, domain, colors):
    flights_df = df[df["airport_code"] != "All Airports"]

    return (
        alt.Chart(flights_df)
        .mark_line(point=True)
        .encode(
            x=alt.X("period:T", title=None, axis=period_axis(df)),
            y=alt.Y(
                "flights:Q",
                title="Flights",
                axis=alt.Axis(orient="left"),
            ),
            color=color_encoding(domain, colors),
            tooltip=[
                alt.Tooltip("display_airport:N", title="Airport"),
                alt.Tooltip("period:T", title="Month", format="%Y-%m"),
                alt.Tooltip("flights:Q", title="Flights", format=",.0f"),
            ],
        )
    )


def show_timeseries(df, color_domain, operation):
    if df.empty:
        st.info("No data available for the selected period.")
        return

    df = df.copy()

    df["period"] = pd.to_datetime(
        dict(year=df["year"], month=df["month"], day=1)
    )

    df["display_airport"] = df["airport_code"]

    mask = df["airport_code"] != "All Airports"

    df.loc[mask, "display_airport"] = (
        df.loc[mask, "city"].fillna("")
        + " ("
        + df.loc[mask, "airport_code"]
        + ")"
    )

    code_labels = (
        df[["airport_code", "display_airport"]]
        .drop_duplicates()
        .set_index("airport_code")["display_airport"]
        .to_dict()
    )

    color_lookup = dict(
        zip(color_domain, color_range(color_domain))
    )

    present_codes = [
        code for code in color_domain
        if code in code_labels
    ]

    display_domain = [
        code_labels[code] for code in present_codes
    ]

    display_colors = [
        color_lookup[code] for code in present_codes
    ]

    charts = [
        ("On-Time", "on_time_rate_pct", "On-Time Rate (%)"),
        ("Avg. Delay", "avg_delay_minutes", "Avg. Delay (Min)"),
    ]

    if not str(operation).lower().startswith("arr"):
        df["cancel_diversion_rate_pct"] = (
            df["cancellation_rate_pct"]
            + df["diversion_rate_pct"]
        )

        charts.append(
            (
                "Cancellation & Diversion",
                "cancel_diversion_rate_pct",
                "Cancellation & Diversion Rate (%)",
            )
        )

    df = df.sort_values(["period", "display_airport"])

    flights = flights_chart(
        df,
        display_domain,
        display_colors,
    )

    tabs = st.tabs([name for name, _, _ in charts])

    for tab, (_, column, title) in zip(tabs, charts):
        with tab:
            st.caption(
                "Solid line = Flights · Dashed line = KPI"
            )

            chart = (
                alt.layer(
                    flights,
                    kpi_chart(
                        df,
                        column,
                        title,
                        display_domain,
                        display_colors,
                    ),
                )
                .resolve_scale(y="independent")
                .properties(height=520)
            )

            st.altair_chart(chart, width="stretch")