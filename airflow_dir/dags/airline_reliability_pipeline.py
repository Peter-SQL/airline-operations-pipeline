from airflow.decorators import dag, task
from airflow.models.param import Param
from airflow.providers.smtp.notifications.smtp import send_smtp_notification

from pathlib import Path

import os
import pendulum
import psycopg
import subprocess
import sys


def run_module(module: str, year: int, month: int, extra_args=None):
    command = [
        sys.executable,
        "-m",
        module,
        "--year",
        str(year),
        "--month",
        str(month),
    ]

    if extra_args:
        command.extend(extra_args)

    subprocess.run(command, check=True)


default_date = pendulum.now("UTC").subtract(months=2)


# ---------------------------------------------------------
# DEMO
# ---------------------------------------------------------

DEMO_MODE = pendulum.now("Europe/Berlin").date() in {
    #pendulum.date(2026, 8, 29),
    pendulum.date(2026, 9, 2),
    pendulum.date(2026, 9, 4),
}

# Silver:
# Demo   -> 1 Retry nach 1 Minute
# Normal -> 2 Retries nach 5 Minuten
SILVER_RETRIES = 1 if DEMO_MODE else 2

SILVER_RETRY_DELAY = (
    pendulum.duration(minutes=1)
    if DEMO_MODE
    else pendulum.duration(minutes=5)
)

# Gold:
# Demo   -> 2 Retries nach je 10 Sekunden
# Normal -> 2 Retries nach 5 Minuten
GOLD_RETRY_DELAY = (
    pendulum.duration(seconds=10)
    if DEMO_MODE
    else pendulum.duration(minutes=5)
)


@dag(
    schedule="0 6 2 * *",
    start_date=pendulum.datetime(2026, 8, 5, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    tags=["airline-reliability"],
    on_failure_callback=send_smtp_notification(
        to=os.getenv("AIRFLOW_SMTP_USER"),
        subject="Airline Pipeline fehlgeschlagen",
        html_content="""
        <h3>Airline Reliability Pipeline fehlgeschlagen</h3>
        <p>DAG: {{ dag.dag_id }}</p>
        <p>Task: {{ ti.task_id }}</p>
        <p>Run: {{ run_id }}</p>
        """,
    ),
    default_args={
        "retries": 2,
        "retry_delay": pendulum.duration(minutes=5),

        "email": [os.getenv("AIRFLOW_SMTP_USER")],
        "email_on_failure": True,
        "email_on_retry": False,
    },
    params={
        "year": Param(
            default_date.year,
            type="integer",
            title="Year",
        ),
        "month": Param(
            default_date.month,
            type="integer",
            minimum=1,
            maximum=12,
            title="Month",
        ),
    },
)
def airline_reliability_pipeline():

    @task
    def ingest_bts(**context):
        year = int(context["params"]["year"])
        month = int(context["params"]["month"])

        dag_run = context["dag_run"]
        run_type = getattr(
            dag_run.run_type,
            "value",
            str(dag_run.run_type),
        )

        # Manueller Lauf:
        # genau den eingegebenen Monat verwenden.
        if run_type == "manual":
            run_module(
                "src.ingestion.ingest_bts",
                year,
                month,
                ["--extract"],
            )

            return [year, month]

        # Automatischer Lauf:
        # zunächst zwei Monate zurück.
        target = context["data_interval_end"].subtract(months=2)

        year = target.year
        month = target.month

        try:
            run_module(
                "src.ingestion.ingest_bts",
                year,
                month,
                ["--extract"],
            )

        except subprocess.CalledProcessError:
            # Fallback: einen weiteren Monat zurück.
            fallback = target.subtract(months=1)

            year = fallback.year
            month = fallback.month

            print(
                f"BTS {target.year}-{target.month:02d} "
                f"not available. Trying "
                f"{year}-{month:02d}."
            )

            run_module(
                "src.ingestion.ingest_bts",
                year,
                month,
                ["--extract"],
            )

        return [year, month]

    @task
    def ingest_references(period):
        year, month = period

        run_module(
            "src.ingestion.ingest_references",
            year,
            month,
        )

    @task(
        retries=SILVER_RETRIES,
        retry_delay=SILVER_RETRY_DELAY,
    )
    def silver_flights(period, **context):
        year, month = period

        run_module(
            "src.transformation.silver_transformation",
            year,
            month,
        )

    @task
    def silver_references(period):
        year, month = period

        run_module(
            "src.transformation.silver_transformation_references",
            year,
            month,
        )

    @task
    def load_postgres(period):
        year, month = period

        run_module(
            "src.loading.load_postgres",
            year,
            month,
        )

    @task(
        retries=2,
        retry_delay=GOLD_RETRY_DELAY,
    )
    def build_gold(period, **context):
        year, month = period

        # Demo:
        # Versuche 1, 2 und 3 schlagen fehl.
        # Danach bleibt der Task rot.
        if (
            DEMO_MODE
            and context["ti"].try_number <= 3
        ):
            raise RuntimeError(
                f"DEMO: Gold failure - "
                f"attempt {context['ti'].try_number}."
            )

        run_module(
            "src.transformation.build_gold",
            year,
            month,
        )

    @task(
        retries=2,
        retry_delay=pendulum.duration(seconds=5),
    )
    def data_quality_checks(period, **context):
        year, month = period

        # Demo:
        # Versuch 1 schlägt simuliert fehl.
        # Versuch 2 schlägt simuliert fehl.
        # Versuch 3 führt die echten Data Quality Checks aus.
        if (
            DEMO_MODE
            and context["ti"].try_number <= 2
        ):
            raise RuntimeError(
                f"DEMO: temporary Data Quality failure - "
                f"attempt {context['ti'].try_number}."
            )

        quality_sql_path = Path(
            "/opt/airflow/project/sql/data_quality_checks.sql"
        )

        quality_sql = quality_sql_path.read_text(
            encoding="utf-8"
        )

        with psycopg.connect(
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    quality_sql,
                    (year, month),
                )

                quality_results = cur.fetchall()

                for check_name, error_count in quality_results:
                    if error_count != 0:
                        raise ValueError(
                            f"Data quality check failed: "
                            f"{check_name} = {error_count} "
                            f"for {year}-{month:02d}"
                        )

                    print(
                        f"OK: {check_name} = 0 "
                        f"for {year}-{month:02d}"
                    )


    @task
    def pipeline_check(period):
        year, month = period

        tables = [
            "fact_flight",
            "gold_airline_reliability",
            "gold_airport_reliability",
            "gold_route_reliability",
            "gold_flight_reliability",
        ]

        with psycopg.connect(
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
        ) as conn:

            with conn.cursor() as cur:
                for table in tables:
                    cur.execute(
                        f"""
                        SELECT COUNT(*)
                        FROM analytics.{table}
                        WHERE EXTRACT(YEAR FROM flight_date) = %s
                          AND EXTRACT(MONTH FROM flight_date) = %s
                        """
                        if table == "fact_flight"
                        else f"""
                        SELECT COUNT(*)
                        FROM analytics.{table}
                        WHERE year = %s
                          AND month = %s
                        """,
                        (year, month),
                    )

                    count = cur.fetchone()[0]

                    if count == 0:
                        raise ValueError(
                            f"Pipeline check failed: "
                            f"analytics.{table} contains no data "
                            f"for {year}-{month:02d}"
                        )

                    print(
                        f"OK: analytics.{table} "
                        f"contains {count} rows "
                        f"for {year}-{month:02d}"
                    )


    period = ingest_bts()

    ingest_references_task = ingest_references(period)
    silver_flights_task = silver_flights(period)
    silver_references_task = silver_references(period)
    load_postgres_task = load_postgres(period)
    build_gold_task = build_gold(period)
    data_quality_checks_task = data_quality_checks(period)
    pipeline_check_task = pipeline_check(period)

    ingest_references_task >> silver_references_task

    [
        silver_flights_task,
        silver_references_task,
    ] >> load_postgres_task

    (
        load_postgres_task
        >> build_gold_task
        >> data_quality_checks_task
        >> pipeline_check_task
    )


airline_reliability_pipeline()