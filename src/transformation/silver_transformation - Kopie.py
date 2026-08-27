import argparse

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from config.paths import BRONZE_FLIGHTS, SILVER_FLIGHTS


def create_spark_session() -> SparkSession:
    return (
        SparkSession.builder
        .appName("airline-silver-transformation")
        .getOrCreate()
    )


def transformation_silver(year: int, month: int) -> None:
    spark = create_spark_session()

    try:
        input_path = (
            BRONZE_FLIGHTS
            / f"year={year}"
            / f"month={month:02d}"
        )

        if not input_path.exists():
            raise FileNotFoundError(
                f"Bronze directory not found: {input_path}"
            )

        csv_files = list(input_path.glob("*.csv"))

        if not csv_files:
            raise FileNotFoundError(
                f"No CSV file found in: {input_path}"
            )


        output_path = (
            SILVER_FLIGHTS
            / f"year={year}"
            / f"month={month:02d}"
        )

        df = (
            spark.read
            .option("header", True)
            .option("inferSchema", True)
            .csv(str(input_path / "*.csv"))
        )

        print("Bronze rows:", df.count())
        df.printSchema()

        silver_df = (
            df
            .select(
                "Year",
                "Quarter",
                "Month",
                "DayofMonth",
                "DayOfWeek",
                "FlightDate",
                "DOT_ID_Reporting_Airline",
                "Flight_Number_Reporting_Airline",
                "OriginAirportID",
                "Origin",
                "OriginCityName",
                "OriginStateName",
                "DestAirportID",
                "Dest",
                "DestCityName",
                "DestStateName",
                "CRSDepTime",
                "DepTime",
                "DepDelay",
                "DepDelayMinutes",
                "DepDel15",
                "DepartureDelayGroups",
                "DepTimeBlk",
                "TaxiOut",
                "WheelsOff",
                "WheelsOn",
                "TaxiIn",
                "CRSArrTime",
                "ArrTime",
                "ArrDelay",
                "ArrDelayMinutes",
                "ArrDel15",
                "ArrivalDelayGroups",
                "ArrTimeBlk",
                "Cancelled",
                "CancellationCode",
                "Diverted",
                "CRSElapsedTime",
                "ActualElapsedTime",
                "AirTime",
                "Distance",
                "DistanceGroup",
                "CarrierDelay",
                "WeatherDelay",
                "NASDelay",
                "SecurityDelay",
                "LateAircraftDelay",
            )
           .withColumn(
                "FlightDate",
                F.to_date(F.col("FlightDate"))
            )
            .withColumn(
                "Cancelled",
                F.col("Cancelled").cast("integer")
            )
            .withColumn(
                "Diverted",
                F.col("Diverted").cast("integer")
            )
            .withColumn(
                "DepDel15",
                F.col("DepDel15").cast("integer")
            )
            .withColumn(
                "ArrDel15",
                F.col("ArrDel15").cast("integer")
            )
            .filter(F.col("OriginAirportID").isNotNull())
            .filter(F.col("DestAirportID").isNotNull())
            .dropDuplicates()
        )

        print("Silver rows:", silver_df.count())

        (
            silver_df.write
            .mode("overwrite")
            .parquet(str(output_path))
        )
    
    finally:
        spark.stop()


def main():
    parser = argparse.ArgumentParser(
        description="Transformation Bronze -> Silver"
    )

    parser.add_argument("--year", type=int)
    parser.add_argument("--month", type=int)
  
    args = parser.parse_args()

    if args.year and args.month:
        year, month = args.year, args.month

    else:
        parser.error("Use --year YEAR --month MONTH.")

    if not 1 <= month <= 12:
        parser.error("Month must be between 1 and 12.")

    transformation_silver(year, month)

if __name__ == "__main__":
    main()

