import pandas as pd
import streamlit as st


DELAY_AGGREGATIONS = {
    "avg_dep_delay_minutes": (
        "dep_delay_sum_minutes",
        "dep_delay_flights",
    ),
    "avg_arr_delay_minutes": (
        "arr_delay_sum_minutes",
        "arr_delay_flights",
    ),
    "avg_delay_minutes": (
        "delay_sum_minutes",
        "delay_flights",
    ),
}


def weighted_average(df, column):
    if column in DELAY_AGGREGATIONS:
        sum_column, count_column = DELAY_AGGREGATIONS[column]

        if (
            sum_column in df.columns
            and count_column in df.columns
        ):
            count = df[count_column].sum()

            if count == 0:
                return 0

            return df[sum_column].sum() / count

    valid = df[column].notna()

    flights = df.loc[valid, "flights"].sum()

    if flights == 0:
        return pd.NA

    return (
        df.loc[valid, column]
        * df.loc[valid, "flights"]
    ).sum() / flights


def aggregate_periods(
    df,
    group_columns,
    weighted_columns,
):
    weighted = df.copy()

    aggregations = {
        "flights": "sum",
    }

    delay_columns = {}

    for column in weighted_columns:
        if column in DELAY_AGGREGATIONS:
            sum_column, count_column = (
                DELAY_AGGREGATIONS[column]
            )

            if (
                sum_column in weighted.columns
                and count_column in weighted.columns
            ):
                aggregations[sum_column] = "sum"
                aggregations[count_column] = "sum"

                delay_columns[column] = (
                    sum_column,
                    count_column,
                )

                continue

        numerator = f"_{column}_numerator"
        denominator = f"_{column}_denominator"

        valid = weighted[column].notna()

        weighted[numerator] = (
            weighted[column]
            * weighted["flights"]
        ).where(valid)

        weighted[denominator] = (
            weighted["flights"]
            .where(valid, 0)
        )

        aggregations[numerator] = "sum"
        aggregations[denominator] = "sum"

    result = (
        weighted
        .groupby(
            group_columns,
            as_index=False,
            dropna=False,
        )
        .agg(aggregations)
    )

    for column in weighted_columns:
        if column in delay_columns:
            sum_column, count_column = (
                delay_columns[column]
            )

            result[column] = (
                result[sum_column]
                / result[count_column]
            ).where(
                result[count_column] != 0
            )

            continue

        numerator = f"_{column}_numerator"
        denominator = f"_{column}_denominator"

        result[column] = (
            result[numerator]
            / result[denominator]
        ).where(
            result[denominator] != 0
        )

        result.drop(
            columns=[
                numerator,
                denominator,
            ],
            inplace=True,
        )

    return result


def add_total_row(
    df,
    name_column,
    code_column,
):
    total = {
        code_column: "n/a",
        name_column: "All Airlines",
        "flights": df["flights"].sum(),
    }

    for column in [
        "dep_delay_flights",
        "dep_delay_sum_minutes",
        "arr_delay_flights",
        "arr_delay_sum_minutes",
    ]:
        if column in df.columns:
            total[column] = df[column].sum()

    for column in [
        "on_time_rate_pct",
        "avg_dep_delay_minutes",
        "avg_arr_delay_minutes",
        "cancellation_rate_pct",
        "diversion_rate_pct",
    ]:
        total[column] = weighted_average(
            df,
            column,
        )

    return pd.concat(
        [
            pd.DataFrame([total]),
            df,
        ],
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
        for x in periods[
            ["year", "month"]
        ].astype(int).values
    ]

    def set_selection(items, value):
        for year, month in items:
            st.session_state[
                f"period_{year}_{month}"
            ] = value

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
                {
                    year
                    for year, _ in options
                },
                reverse=True,
            ):
                year_options = sorted(
                    [
                        p
                        for p in options
                        if p[0] == year
                    ],
                    key=lambda p: p[1],
                )

                st.markdown(
                    f"**{year}**"
                )

                c1, c2 = st.columns(2)

                c1.button(
                    "On",
                    key=f"on_{year}",
                    on_click=set_selection,
                    args=(
                        year_options,
                        True,
                    ),
                )

                c2.button(
                    "Off",
                    key=f"off_{year}",
                    on_click=set_selection,
                    args=(
                        year_options,
                        False,
                    ),
                )

                cols = st.columns(3)

                for i, (
                    year,
                    month,
                ) in enumerate(
                    year_options
                ):
                    if cols[
                        i % 3
                    ].checkbox(
                        f"{month:02d}",
                        key=(
                            f"period_"
                            f"{year}_"
                            f"{month}"
                        ),
                    ):
                        selected.append(
                            (
                                year,
                                month,
                            )
                        )

    return selected


def select_kpi_period(
    periods,
    selected_periods,
    prefix,
    title,
):
    available = sorted(
        (int(y), int(m))
        for y, m in periods[
            ["year", "month"]
        ].values
    )

    if not available:
        return []

    selected = sorted(
        (int(y), int(m))
        for y, m in selected_periods
    )

    start_default = (
        selected[0]
        if (
            selected
            and selected[0] in available
        )
        else available[0]
    )

    end_default = (
        selected[-1]
        if (
            selected
            and selected[-1] in available
        )
        else available[-1]
    )

    labels = [
        f"{y}-{m:02d}"
        for y, m in available
    ]

    start_key = (
        f"{prefix}_kpi_start"
    )
    end_key = (
        f"{prefix}_kpi_end"
    )

    widget_start = (
        f"_{start_key}"
    )
    widget_end = (
        f"_{end_key}"
    )

    if (
        start_key
        not in st.session_state
        or st.session_state[
            start_key
        ] not in labels
    ):
        st.session_state[
            start_key
        ] = (
            f"{start_default[0]}-"
            f"{start_default[1]:02d}"
        )

    if (
        end_key
        not in st.session_state
        or st.session_state[
            end_key
        ] not in labels
    ):
        st.session_state[
            end_key
        ] = (
            f"{end_default[0]}-"
            f"{end_default[1]:02d}"
        )

    st.session_state[
        widget_start
    ] = st.session_state[
        start_key
    ]

    st.session_state[
        widget_end
    ] = st.session_state[
        end_key
    ]

    def save_period():
        st.session_state[
            start_key
        ] = st.session_state[
            widget_start
        ]

        st.session_state[
            end_key
        ] = st.session_state[
            widget_end
        ]

    with st.sidebar:
        with st.container(
            border=True
        ):
            st.subheader(title)

            st.caption(
                "Independent period selection"
            )

            start = st.selectbox(
                "Start",
                labels,
                key=widget_start,
                on_change=save_period,
            )

            end = st.selectbox(
                "End",
                labels,
                key=widget_end,
                on_change=save_period,
            )

    start = int(
        start.replace("-", "")
    )

    end = int(
        end.replace("-", "")
    )

    return [
        p
        for p in available
        if (
            start
            <= p[0] * 100 + p[1]
            <= end
        )
    ]
