import html

import altair as alt
import pandas as pd
import streamlit as st

from dashboard.views.route_charts import color_range


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
        "display_route:N",
        scale=alt.Scale(domain=domain, range=colors),
        legend=None,
    )


def show_legend(domain, colors):
    items = "".join(
        f"""
        <div style="display:flex;align-items:center;gap:8px;margin:4px 0;">
            <span style="width:12px;height:12px;background:{color};
                         display:inline-block;flex:0 0 12px;"></span>
            <span>{html.escape(str(label))}</span>
        </div>
        """
        for label, color in zip(domain, colors)
    )

    st.markdown(
        f"""
        <div style="max-height:520px;overflow-y:auto;padding-right:8px;">
            <b>Route</b>
            {items}
        </div>
        """,
        unsafe_allow_html=True,
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
                alt.Tooltip("display_route:N", title="Route"),
                alt.Tooltip("period:T", title="Month", format="%Y-%m"),
                alt.Tooltip(f"{column}:Q", title=title, format=".2f"),
            ],
        )
    )


def flights_chart(df, domain, colors):
    flights_df = df[df["route"] != "All Routes"]

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
                alt.Tooltip("display_route:N", title="Route"),
                alt.Tooltip("period:T", title="Month", format="%Y-%m"),
                alt.Tooltip("flights:Q", title="Flights", format=",.0f"),
            ],
        )
    )


def show_timeseries(df, color_domain):
    if df.empty:
        st.info("No data available for the selected period.")
        return

    df = df.copy()
    df["period"] = pd.to_datetime(
        dict(year=df["year"], month=df["month"], day=1)
    )

    df["display_route"] = df["route"]
    mask = df["route"] != "All Routes"

    df.loc[mask, "display_route"] = (
        df.loc[mask, "origin_city"].fillna("")
        + " (" + df.loc[mask, "origin_airport_code"] + ") → "
        + df.loc[mask, "dest_city"].fillna("")
        + " (" + df.loc[mask, "dest_airport_code"] + ")"
    )

    route_labels = (
        df[["route", "display_route"]]
        .drop_duplicates()
        .set_index("route")["display_route"]
        .to_dict()
    )

    color_lookup = dict(
        zip(color_domain, color_range(color_domain))
    )

    selected = st.session_state.get(
        "route_comparison_selection", []
    )

    present_routes = [
        "All Routes",
        *[route for route in selected if route in route_labels],
    ]

    display_domain = [
        route_labels[route] for route in present_routes
    ]
    display_colors = [
        color_lookup[route] for route in present_routes
    ]

    df["cancel_diversion_rate_pct"] = (
        df["cancellation_rate_pct"]
        + df["diversion_rate_pct"]
    )

    charts = [
        ("On-Time", "on_time_rate_pct", "On-Time Rate (%)"),
        ("Dep. Delay", "avg_dep_delay_minutes", "Avg. Departure Delay (Min)"),
        ("Arr. Delay", "avg_arr_delay_minutes", "Avg. Arrival Delay (Min)"),
        (
            "Cancellation & Diversion",
            "cancel_diversion_rate_pct",
            "Cancellation & Diversion Rate (%)",
        ),
    ]

    df = df.sort_values(["period", "display_route"])
    flights = flights_chart(df, display_domain, display_colors)
    tabs = st.tabs([name for name, _, _ in charts])

    for tab, (_, column, title) in zip(tabs, charts):
        with tab:
            st.caption("Solid line = Flights · Dashed line = KPI")

            chart = (
                alt.layer(
                    flights,
                    kpi_chart(
                        df, column, title,
                        display_domain, display_colors,
                    ),
                )
                .resolve_scale(y="independent")
                .properties(height=520)
            )

            chart_col, legend_col = st.columns([4, 1])

            with chart_col:
                st.altair_chart(chart, width="stretch")

            with legend_col:
                show_legend(display_domain, display_colors)