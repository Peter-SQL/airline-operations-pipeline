import pandas as pd
import streamlit as st


def weighted_average(df, column):
    flights = df["flights"].sum()

    if flights == 0:
        return 0

    return (df[column] * df["flights"]).sum() / flights


def aggregate_periods(df, group_columns, weighted_columns):
    weighted = df.copy()

    for column in weighted_columns:
        weighted[f"_{column}"] = (
            weighted[column] * weighted["flights"]
        )

    aggregations = {
        "flights": "sum",
        **{
            f"_{column}": "sum"
            for column in weighted_columns
        },
    }

    result = weighted.groupby(
        group_columns,
        as_index=False,
        dropna=False,
    ).agg(aggregations)

    for column in weighted_columns:
        result[column] = (
            result[f"_{column}"] / result["flights"]
        ).fillna(0)

        result.drop(
            columns=f"_{column}",
            inplace=True,
        )

    return result


def add_total_row(df, name_column, code_column):
    total = {
        code_column: "n/a",
        name_column: "All Airlines",
        "flights": df["flights"].sum(),
    }

    for column in [
        "on_time_rate_pct",
        "avg_dep_delay_minutes",
        "avg_arr_delay_minutes",
        "cancellation_rate_pct",
        "diversion_rate_pct",
    ]:
        total[column] = weighted_average(df, column)

    return pd.concat(
        [pd.DataFrame([total]), df],
        ignore_index=True,
    )


def highlight_total(row):
    if row.get("airline_name") == "All Airlines":
        return ["color: blue"] * len(row)

    return [""] * len(row)


def number_column(label):
    return {
        "label": label,
        "format": "%.2f",
    }


def select_periods(periods):
    options = [
        tuple(x)
        for x in periods[["year", "month"]].astype(int).values
    ]

    def set_selection(items, value):
        for year, month in items:
            st.session_state[f"period_{year}_{month}"] = value

    for i, (year, month) in enumerate(options):
        st.session_state.setdefault(
            f"period_{year}_{month}",
            i == 0,
        )

    selected = []

    with st.sidebar:
        with st.container(border=True):
            st.subheader("Periods")

            c1, c2 = st.columns(2)

            c1.button(
                "All on",
                on_click=set_selection,
                args=(options, True),
            )

            c2.button(
                "All off",
                on_click=set_selection,
                args=(options, False),
            )

            for year in sorted(
                {year for year, _ in options},
                reverse=True,
            ):
                year_options = sorted(
                    [p for p in options if p[0] == year],
                    key=lambda p: p[1],
                )

                st.markdown(f"**{year}**")

                c1, c2 = st.columns(2)

                c1.button(
                    "On",
                    key=f"on_{year}",
                    on_click=set_selection,
                    args=(year_options, True),
                )

                c2.button(
                    "Off",
                    key=f"off_{year}",
                    on_click=set_selection,
                    args=(year_options, False),
                )

                cols = st.columns(3)

                for i, (year, month) in enumerate(year_options):
                    if cols[i % 3].checkbox(
                        f"{month:02d}",
                        key=f"period_{year}_{month}",
                    ):
                        selected.append((year, month))

    return selected