import argparse
from datetime import datetime

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from zoneinfo import ZoneInfo

from config.paths import (
    BRONZE_REFERENCE,
    SILVER_REFERENCE,
    SILVER_REFERENCE_REPORTS,
)


REFERENCE_FILES = {
    "airlines": {
        "filename": "L_Airline_ID.csv",
        "code_type": "integer",
        "code_name": "AirlineID",
        "description_name": "AirlineName",
    },
    "airports": {
        "filename": "L_Airport.csv",
        "code_type": "string",
        "code_name": "AirportCode",
        "description_name": "AirportName",
    },
    "airport_ids": {
        "filename": "L_Airport-ID.csv",
        "code_type": "integer",
        "code_name": "AirportID",
        "description_name": "AirportName",
    },
}

EXPECTED_COLUMNS = {"Code", "Description"}


def create_spark_session() -> SparkSession:
    return (
        SparkSession.builder
        .appName("airline-silver-reference-transformation")
        .getOrCreate()
    )


def validate_schema(df, name: str) -> None:
    missing_columns = [
        column
        for column in EXPECTED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"{name}: mandatory columns missing: {missing_columns}"
        )


def transform_reference(
    spark: SparkSession,
    name: str,
    config: dict,
    year: int,
    month: int,
) -> None:
    filename = config["filename"]
    code_type = config["code_type"]
    code_name = config["code_name"]
    description_name = config["description_name"]

    input_path = (
        BRONZE_REFERENCE
        / f"year={year}"
        / f"month={month:02d}"
        / name
        / filename
    )

    output_path = (
        SILVER_REFERENCE
        / f"year={year}"
        / f"month={month:02d}"
        / name
    )

    if not input_path.exists():
        raise FileNotFoundError(
            f"Bronze reference file not found: {input_path}"
        )

    df = (
        spark.read
        .option("header", True)
        .option("inferSchema", False)
        .csv(str(input_path))
    )

    bronze_count = df.count()
    validate_schema(df, name)

    silver_df = (
        df
        .select("Code", "Description")
        .withColumn("Code", F.trim(F.col("Code")))
        .withColumn("Description", F.trim(F.col("Description")))
    )

    if code_type == "integer":
        silver_df = silver_df.withColumn(
            "Code",
            F.col("Code").cast("integer")
        )
    else:
        silver_df = silver_df.withColumn(
            "Code",
            F.upper(F.col("Code"))
        )

    validation_report = (
        silver_df
        .agg(
            F.sum(
                F.when(F.col("Code").isNull(), 1).otherwise(0)
            ).alias("missing_code"),
            F.sum(
                F.when(
                    F.col("Description").isNull()
                    | (F.col("Description") == ""),
                    1
                ).otherwise(0)
            ).alias("missing_description"),
        )
        .first()
        .asDict()
    )

    duplicate_count = (
        silver_df
        .groupBy("Code")
        .count()
        .filter(
            F.col("Code").isNotNull()
            & (F.col("count") > 1)
        )
        .count()
    )

    valid_df = (
        silver_df
        .filter(F.col("Code").isNotNull())
        .filter(F.col("Description").isNotNull())
        .filter(F.col("Description") != "")
        .dropDuplicates(["Code"])
        .withColumnRenamed("Code", code_name)
        .withColumnRenamed("Description", description_name)
    )

    silver_count = valid_df.count()
    rejected_total = bronze_count - silver_count

    (
        valid_df
        .write
        .mode("overwrite")
        .parquet(str(output_path))
    )

    print(f"Silver reference written to: {output_path}")

    run_timestamp = datetime.now(ZoneInfo("Europe/Berlin")).strftime("%Y-%m-%d %H:%M:%S")

    report_lines = [
        "",
        "=" * 70,
        f"VALIDATION REPORT - {name.upper()} - {year}-{month:02d}",
        f"Run timestamp: {run_timestamp}",
        "=" * 70,
        f"{'Bronze rows':<45} {bronze_count:>10}",
        "-" * 70,
        "VALIDATION",
        "-" * 70,
        f"{'Missing Code':<45} "
        f"{validation_report['missing_code']:>10}",
        f"{'Missing Description':<45} "
        f"{validation_report['missing_description']:>10}",
        f"{'Duplicate Codes':<45} "
        f"{duplicate_count:>10}",
        "-" * 70,
        "RESULT",
        "-" * 70,
        f"{'Total rejected':<45} {rejected_total:>10}",
        f"{'Silver rows':<45} {silver_count:>10}",
        "=" * 70,
    ]

    report_text = "\n".join(report_lines)

    print(report_text)

    report_dir = (
        SILVER_REFERENCE_REPORTS
        / f"year={year}"
        / f"month={month:02d}"
        / name
    )

    report_dir.mkdir(parents=True, exist_ok=True)

    report_path = report_dir / "validation_report.txt"
    report_path.write_text(
        report_text,
        encoding="utf-8"
    )

    print(f"Validation report written to: {report_path}")


def transformation_silver_references(
    year: int,
    month: int,
) -> None:
    spark = create_spark_session()

    try:
        for name, config in REFERENCE_FILES.items():
            transform_reference(
                spark=spark,
                name=name,
                config=config,
                year=year,
                month=month,
            )
    finally:
        spark.stop()


def main():
    parser = argparse.ArgumentParser(
        description="Transformation Bronze Reference -> Silver Reference"
    )

    parser.add_argument(
        "--year",
        type=int,
        required=True,
    )

    parser.add_argument(
        "--month",
        type=int,
        required=True,
    )

    args = parser.parse_args()

    if not 1 <= args.month <= 12:
        parser.error("Month must be between 1 and 12.")

    transformation_silver_references(
        args.year,
        args.month,
    )


if __name__ == "__main__":
    main()
