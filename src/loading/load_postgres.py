import argparse
import os

from dotenv import load_dotenv
import psycopg
from pyspark.sql import SparkSession, functions as F

from config.paths import SILVER_FLIGHTS, SILVER_REFERENCE

load_dotenv()

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "airline_reliability")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

JDBC_URL = f"jdbc:postgresql://{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
JDBC_PROPERTIES = {
    "user": POSTGRES_USER,
    "password": POSTGRES_PASSWORD or "",
    "driver": "org.postgresql.Driver",
}


def create_spark_session():
    return (
        SparkSession.builder
        .appName("airline-postgres-load")
        .config("spark.jars.packages", "org.postgresql:postgresql:42.7.7")
        .getOrCreate()
    )


def get_connection():
    if not POSTGRES_PASSWORD:
        raise ValueError("POSTGRES_PASSWORD is not set.")

    return psycopg.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )


def flight_path(year, month):
    return SILVER_FLIGHTS / f"year={year}" / f"month={month:02d}"


def reference_path(year, month, name):
    return (
        SILVER_REFERENCE
        / f"year={year}"
        / f"month={month:02d}"
        / name
    )


def create_tables():
    ddl = """
    CREATE SCHEMA IF NOT EXISTS analytics;

    CREATE TABLE IF NOT EXISTS analytics.dim_airline (
        airline_id INTEGER PRIMARY KEY,
        airline_name TEXT NOT NULL,
        airline_code VARCHAR(10)
    );

    CREATE TABLE IF NOT EXISTS analytics.dim_airport (
        airport_id INTEGER PRIMARY KEY,
        airport_code VARCHAR(10),
        city TEXT,
        state TEXT,
        airport_name TEXT
    );

    CREATE TABLE IF NOT EXISTS analytics.fact_flight (
        flight_id BIGSERIAL PRIMARY KEY,
        flight_date DATE NOT NULL,
        airline_id INTEGER NOT NULL,
        flight_number INTEGER NOT NULL,
        origin_airport_id INTEGER NOT NULL,
        dest_airport_id INTEGER NOT NULL,
        day_of_week INTEGER,
        dep_time_block VARCHAR(20),
        dep_delay_minutes INTEGER,
        arr_delay_minutes INTEGER,
        cancelled INTEGER NOT NULL,
        diverted INTEGER NOT NULL,
        carrier_delay INTEGER,
        weather_delay INTEGER,
        nas_delay INTEGER,
        security_delay INTEGER,
        late_aircraft_delay INTEGER
    );

    CREATE INDEX IF NOT EXISTS idx_fact_flight_date
        ON analytics.fact_flight (flight_date);
    CREATE INDEX IF NOT EXISTS idx_fact_flight_airline
        ON analytics.fact_flight (airline_id);
    CREATE INDEX IF NOT EXISTS idx_fact_flight_origin
        ON analytics.fact_flight (origin_airport_id);
    CREATE INDEX IF NOT EXISTS idx_fact_flight_dest
        ON analytics.fact_flight (dest_airport_id);
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(ddl)
        conn.commit()

    print("Database tables ready")


def load_dim_airline(spark, year, month):
    path = reference_path(year, month, "airlines")
    if not path.exists():
        raise FileNotFoundError(f"Silver airlines not found: {path}")

    df = spark.read.parquet(str(path))
    pattern = r"^(.*):\s*([^:]*)$"

    dim_df = (
        df.select(
            F.col("AirlineID").cast("integer").alias("airline_id"),

            F.trim(
                F.regexp_extract(
                    F.col("AirlineName"),
                    r"^(.*?):",
                    1,
                )
            ).alias("airline_name"),

            F.upper(
                F.regexp_extract(
                    F.col("AirlineName"),
                    r":\s*([A-Za-z0-9]+)",
                    1,
                )
            ).alias("airline_code"),
        )
        .filter(F.col("airline_id").isNotNull())
        .filter(F.col("airline_name") != "")
        .dropDuplicates(["airline_id"])
    )

    rows = [tuple(row) for row in dim_df.collect()]

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO analytics.dim_airline
                    (airline_id, airline_name, airline_code)
                VALUES (%s, %s, %s)
                ON CONFLICT (airline_id) DO UPDATE SET
                    airline_name = EXCLUDED.airline_name,
                    airline_code = EXCLUDED.airline_code;
                """,
                rows,
            )
        conn.commit()

    print(f"dim_airline loaded: {len(rows)} rows")


def load_dim_airport(spark, year, month):
    flights_path = flight_path(year, month)
    ref_path = reference_path(year, month, "airport_ids")

    if not flights_path.exists():
        raise FileNotFoundError(f"Silver flights not found: {flights_path}")
    if not ref_path.exists():
        raise FileNotFoundError(f"Silver airport IDs not found: {ref_path}")

    flights = spark.read.parquet(str(flights_path))
    airport_ref = spark.read.parquet(str(ref_path))

    origin = flights.select(
        F.col("OriginAirportID").cast("integer").alias("airport_id"),
        F.col("Origin").alias("airport_code"),
        F.col("OriginCityName").alias("city"),
        F.col("OriginStateName").alias("state"),
    )

    destination = flights.select(
        F.col("DestAirportID").cast("integer").alias("airport_id"),
        F.col("Dest").alias("airport_code"),
        F.col("DestCityName").alias("city"),
        F.col("DestStateName").alias("state"),
    )

    base = (
        origin.unionByName(destination)
        .filter(F.col("airport_id").isNotNull())
        .dropDuplicates(["airport_id"])
    )

    names = (
        airport_ref.select(
            F.col("AirportID").cast("integer").alias("airport_id"),
            F.trim(
                F.regexp_extract(
                    F.col("AirportName"),
                    r"^(.+),\s*([^:]+):\s*(.+)$",
                    3,
                )
            ).alias("airport_name"),
        )
        .dropDuplicates(["airport_id"])
    )

    dim_df = base.join(names, "airport_id", "left")
    rows = [tuple(row) for row in dim_df.collect()]

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO analytics.dim_airport
                    (airport_id, airport_code, city, state, airport_name)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (airport_id) DO UPDATE SET
                    airport_code = EXCLUDED.airport_code,
                    city = EXCLUDED.city,
                    state = EXCLUDED.state,
                    airport_name = EXCLUDED.airport_name;
                """,
                rows,
            )
        conn.commit()

    print(f"dim_airport loaded: {len(rows)} rows")


def load_fact_flight(spark, year, month):
    path = flight_path(year, month)
    if not path.exists():
        raise FileNotFoundError(f"Silver flights not found: {path}")

    df = spark.read.parquet(str(path))

    fact_df = df.select(
        F.col("FlightDate").alias("flight_date"),
        F.col("DOT_ID_Reporting_Airline").cast("integer").alias("airline_id"),
        F.col("Flight_Number_Reporting_Airline").cast("integer").alias("flight_number"),
        F.col("OriginAirportID").cast("integer").alias("origin_airport_id"),
        F.col("DestAirportID").cast("integer").alias("dest_airport_id"),
        F.col("DayOfWeek").cast("integer").alias("day_of_week"),
        F.col("DepTimeBlk").alias("dep_time_block"),
        F.col("DepDelayMinutes").cast("integer").alias("dep_delay_minutes"),
        F.col("ArrDelayMinutes").cast("integer").alias("arr_delay_minutes"),
        F.col("Cancelled").cast("integer").alias("cancelled"),
        F.col("Diverted").cast("integer").alias("diverted"),
        F.col("CarrierDelay").cast("integer").alias("carrier_delay"),
        F.col("WeatherDelay").cast("integer").alias("weather_delay"),
        F.col("NASDelay").cast("integer").alias("nas_delay"),
        F.col("SecurityDelay").cast("integer").alias("security_delay"),
        F.col("LateAircraftDelay").cast("integer").alias("late_aircraft_delay"),
    )

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM analytics.fact_flight
                WHERE flight_date >= make_date(%s, %s, 1)
                  AND flight_date < make_date(%s, %s, 1) + INTERVAL '1 month';
                """,
                (year, month, year, month),
            )
        conn.commit()

    (
        fact_df.write
        .mode("append")
        .jdbc(
            url=JDBC_URL,
            table="analytics.fact_flight",
            properties=JDBC_PROPERTIES,
        )
    )

    print(f"fact_flight loaded: {fact_df.count()} rows")


def run_check(year, month):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM analytics.fact_flight
                WHERE flight_date >= make_date(%s, %s, 1)
                  AND flight_date < make_date(%s, %s, 1) + INTERVAL '1 month';
                """,
                (year, month, year, month),
            )
            count = cur.fetchone()[0]

    print(f"Post-load check - fact rows: {count}")


def load_postgres(year, month):
    spark = create_spark_session()

    try:
        print("=" * 60)
        print(f"POSTGRES LOAD - {year}-{month:02d}")
        print("=" * 60)

        create_tables()
        load_dim_airline(spark, year, month)
        load_dim_airport(spark, year, month)
        load_fact_flight(spark, year, month)
        run_check(year, month)

        print("POSTGRESQL LOAD COMPLETED SUCCESSFULLY")

    finally:
        spark.stop()


def main():
    parser = argparse.ArgumentParser(
        description="Load Silver airline data into PostgreSQL."
    )
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--month", type=int, required=True)
    args = parser.parse_args()

    if not 1 <= args.month <= 12:
        parser.error("Month must be between 1 and 12.")

    load_postgres(args.year, args.month)


if __name__ == "__main__":
    main()
