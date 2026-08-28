from airflow.decorators import dag, task
from airflow.models.param import Param

import pendulum
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


default_date = pendulum.now("Europe/Berlin").subtract(months=2)


@dag(
    schedule="@monthly",
    start_date=pendulum.datetime(2026, 8, 1, tz="Europe/Berlin"),
    catchup=False,
    tags=["airline-reliability"],
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
        year = context["params"]["year"]
        month = context["params"]["month"]

        run_module(
            "src.ingestion.ingest_bts",
            year,
            month,
            ["--extract"],
        )

    @task
    def ingest_references(**context):
        year = context["params"]["year"]
        month = context["params"]["month"]

        run_module(
            "src.ingestion.ingest_references",
            year,
            month,
        )

    @task
    def silver_flights(**context):
        year = context["params"]["year"]
        month = context["params"]["month"]

        run_module(
            "src.transformation.silver_transformation",
            year,
            month,
        )

    @task
    def silver_references(**context):
        year = context["params"]["year"]
        month = context["params"]["month"]

        run_module(
            "src.transformation.silver_transformation_references",
            year,
            month,
        )

    @task
    def load_postgres(**context):
        year = context["params"]["year"]
        month = context["params"]["month"]

        run_module(
            "src.loading.load_postgres",
            year,
            month,
        )

    @task
    def build_gold(**context):
        year = context["params"]["year"]
        month = context["params"]["month"]

        run_module(
            "src.transformation.build_gold",
            year,
            month,
        )

    ingest_flights_task = ingest_bts()
    ingest_references_task = ingest_references()

    silver_flights_task = silver_flights()
    silver_references_task = silver_references()

    load_postgres_task = load_postgres()
    build_gold_task = build_gold()

    ingest_flights_task >> silver_flights_task
    ingest_references_task >> silver_references_task

    [
        silver_flights_task,
        silver_references_task,
    ] >> load_postgres_task

    load_postgres_task >> build_gold_task


airline_reliability_pipeline()