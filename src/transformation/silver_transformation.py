import argparse

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from datetime import datetime
from zoneinfo import ZoneInfo

from config.paths import (
    BRONZE_FLIGHTS,
    SILVER_FLIGHTS,
    SILVER_FLIGHT_REPORTS,
)


REQUIRED_COLUMNS = [
    "Year", "Quarter", "Month", "DayofMonth", "DayOfWeek", "FlightDate", "DOT_ID_Reporting_Airline", "Flight_Number_Reporting_Airline", "OriginAirportID",
    "Origin", "OriginCityName", "OriginStateName", "DestAirportID", "Dest", "DestCityName", "DestStateName", "CRSDepTime", "DepTime", "DepDelay", "DepDelayMinutes",
    "DepDel15", "DepartureDelayGroups", "DepTimeBlk", "TaxiOut", "WheelsOff", "WheelsOn", "TaxiIn", "CRSArrTime", "ArrTime", "ArrDelay", "ArrDelayMinutes",
    "ArrDel15", "ArrivalDelayGroups", "ArrTimeBlk", "Cancelled", "CancellationCode", "Diverted", "CRSElapsedTime", "ActualElapsedTime",
    "AirTime", "Distance", "DistanceGroup", "CarrierDelay", "WeatherDelay", "NASDelay", "SecurityDelay", "LateAircraftDelay",]


def create_spark_session() -> SparkSession:
    return (
        SparkSession.builder
        .appName("airline-silver-transformation")
        .master("local[2]")
        .config("spark.driver.memory", "2g")
        .getOrCreate()
    )


def validate_schema(df) -> None:
    """
    Checking for miss of most interesting / important columns
    """

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Following mandatory columns are missing: {missing_columns}"
        )

# ---------------------------------------------------------
# Set validation Flags
# ---------------------------------------------------------

def add_validation_flags (df, year: int, month: int):
    return (

        df

        # Airport Codes
        .withColumn("valid_origin_code", F.col("Origin").rlike("^[A-Z]{3}$"))
        .withColumn("valid_dest_code", F.col("Dest").rlike("^[A-Z]{3}$"))

        # Route
        .withColumn("valid_route", (F.col("Origin") != F.col("Dest")) | (F.col("Cancelled") == 1) | (F.col("Diverted") == 1))

        # Flags
        .withColumn("valid_cancelled", F.col("Cancelled").isin(0, 1))
        .withColumn("valid_diverted", F.col("Diverted").isin(0, 1))
        .withColumn("valid_depdel15", F.col("DepDel15").isNull() | F.col("DepDel15").isin(0, 1))
        .withColumn("valid_arrdel15", F.col("ArrDel15").isNull() | F.col("ArrDel15").isin(0, 1))

        # Partition / Datum
        .withColumn("valid_partition_date", (F.year("FlightDate") == year) & (F.month("FlightDate") == month))
        .withColumn("valid_year", F.col("Year") == year)
        .withColumn("valid_month", F.col("Month") == month)
        .withColumn("valid_quarter", F.col("Quarter").between(1, 4))
        .withColumn("valid_day_of_month", F.col("DayofMonth").between(1, 31))
        .withColumn("valid_day_of_week", F.col("DayOfWeek").between(1, 7))

        # Delay Minutes
        .withColumn("valid_dep_delay_minutes", F.col("DepDelayMinutes").isNull() | (F.col("DepDelayMinutes") >= 0))
        .withColumn("valid_arr_delay_minutes", F.col("ArrDelayMinutes").isNull() | (F.col("ArrDelayMinutes") >= 0))

        # Taxi-  / flight times
        .withColumn("valid_taxi_out", F.col("TaxiOut").isNull() | (F.col("TaxiOut") >= 0))
        .withColumn("valid_taxi_in", F.col("TaxiIn").isNull() | (F.col("TaxiIn") >= 0))
        .withColumn("valid_crs_elapsed_time", F.col("CRSElapsedTime").isNull() | (F.col("CRSElapsedTime") >= 0))
        .withColumn("valid_actual_elapsed_time", F.col("ActualElapsedTime").isNull() | (F.col("ActualElapsedTime") >= 0))
        .withColumn("valid_air_time", F.col("AirTime").isNull() | (F.col("AirTime") >= 0))

        # Distance
        .withColumn("valid_distance", F.col("Distance").isNull() | (F.col("Distance") > 0))

        # Delay-reasons
        .withColumn("valid_carrier_delay", F.col("CarrierDelay").isNull() | (F.col("CarrierDelay") >= 0))
        .withColumn("valid_weather_delay", F.col("WeatherDelay").isNull() | (F.col("WeatherDelay") >= 0))
        .withColumn("valid_nas_delay", F.col("NASDelay").isNull() | (F.col("NASDelay") >= 0))
        .withColumn("valid_security_delay", F.col("SecurityDelay").isNull() | (F.col("SecurityDelay") >= 0))
        .withColumn("valid_late_aircraft_delay", F.col("LateAircraftDelay").isNull() | (F.col("LateAircraftDelay") >= 0))
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


        ## Loading, counting, schema check bronze data 
        df = (
            spark.read
            .option("header", True)
            .option("inferSchema", True)
            .csv([str(file) for file in csv_files])            
        )

        bronze_count = df.count()
        print("Bronze rows:", bronze_count)

        df.printSchema()

        validate_schema(df)


        ## Create silver df, convert to "correct" data type and do all the checks
        silver_df = (
            df.select(*REQUIRED_COLUMNS)

        # Date
        .withColumn("FlightDate", F.to_date(F.col("FlightDate")))
        
        # Date's parts
        .withColumn("Year", F.col("Year").cast("integer"))
        .withColumn("Quarter", F.col("Quarter").cast("integer"))
        .withColumn("Month", F.col("Month").cast("integer"))
        .withColumn("DayofMonth", F.col("DayofMonth").cast("integer"))
        .withColumn("DayOfWeek", F.col("DayOfWeek").cast("integer"))

        # IDs
        .withColumn("DOT_ID_Reporting_Airline", F.col("DOT_ID_Reporting_Airline").cast("integer")        )
        .withColumn("Flight_Number_Reporting_Airline", F.col("Flight_Number_Reporting_Airline").cast("integer")        )
        .withColumn("OriginAirportID", F.col("OriginAirportID").cast("integer"))
        .withColumn("DestAirportID", F.col("DestAirportID").cast("integer"))

        # Times as integer as hhmm
        .withColumn("CRSDepTime", F.col("CRSDepTime").cast("integer"))
        .withColumn("DepTime", F.col("DepTime").cast("integer"))
        .withColumn("WheelsOff", F.col("WheelsOff").cast("integer"))
        .withColumn("WheelsOn", F.col("WheelsOn").cast("integer"))
        .withColumn("CRSArrTime", F.col("CRSArrTime").cast("integer"))
        .withColumn("ArrTime", F.col("ArrTime").cast("integer"))

        # Flags
        .withColumn("DepDel15", F.col("DepDel15").cast("integer"))
        .withColumn("ArrDel15", F.col("ArrDel15").cast("integer"))
        .withColumn("Cancelled", F.col("Cancelled").cast("integer"))
        .withColumn("Diverted", F.col("Diverted").cast("integer"))

        # Groups      
        .withColumn("DepartureDelayGroups", F.col("DepartureDelayGroups").cast("integer"))
        .withColumn("ArrivalDelayGroups", F.col("ArrivalDelayGroups").cast("integer"))
        .withColumn("DistanceGroup", F.col("DistanceGroup").cast("integer"))

        # Delay / Time as integer in minutes
        .withColumn("DepDelay", F.col("DepDelay").cast("integer"))
        .withColumn("DepDelayMinutes", F.col("DepDelayMinutes").cast("integer"))
        .withColumn("TaxiOut", F.col("TaxiOut").cast("integer"))
        .withColumn("TaxiIn", F.col("TaxiIn").cast("integer"))
        .withColumn("ArrDelay", F.col("ArrDelay").cast("integer"))
        .withColumn("ArrDelayMinutes", F.col("ArrDelayMinutes").cast("integer"))
        .withColumn("CRSElapsedTime", F.col("CRSElapsedTime").cast("integer"))
        .withColumn("ActualElapsedTime", F.col("ActualElapsedTime").cast("integer"))
        .withColumn("AirTime", F.col("AirTime").cast("integer"))

        # Distance
        .withColumn("Distance", F.col("Distance").cast("integer"))

        # Various Reasons for Delay in minutes
        .withColumn("CarrierDelay", F.col("CarrierDelay").cast("integer"))
        .withColumn("WeatherDelay", F.col("WeatherDelay").cast("integer"))
        .withColumn("NASDelay", F.col("NASDelay").cast("integer"))
        .withColumn("SecurityDelay", F.col("SecurityDelay").cast("integer"))
        .withColumn("LateAircraftDelay",F.col("LateAircraftDelay").cast("integer"))

        # Formatting Text
        .withColumn("Origin", F.upper(F.trim(F.col("Origin"))))
        .withColumn("OriginCityName", F.trim(F.col("OriginCityName")))
        .withColumn("OriginStateName", F.trim(F.col("OriginStateName")))
        .withColumn("Dest", F.upper(F.trim(F.col("Dest"))))
        .withColumn("DestCityName", F.trim(F.col("DestCityName")))
        .withColumn("DestStateName", F.trim(F.col("DestStateName")))
        .withColumn("CancellationCode", F.upper(F.trim(F.col("CancellationCode"))))
        .withColumn("DepTimeBlk", F.trim(F.col("DepTimeBlk")))
        .withColumn("ArrTimeBlk", F.trim(F.col("ArrTimeBlk")))
        )


        silver_df = add_validation_flags(
            silver_df,
            year,
            month,
        )



        # ---------------------------------------------------------
        # Hard Validation
        # ---------------------------------------------------------


        # # find reasons for not perfect data
        # hard_invalid_df = silver_df.filter(
        #     F.col("FlightDate").isNull()
        #     | F.col("DOT_ID_Reporting_Airline").isNull()
        #     | F.col("Flight_Number_Reporting_Airline").isNull()
        #     | F.col("OriginAirportID").isNull()
        #     | F.col("Origin").isNull()
        #     | F.col("DestAirportID").isNull()
        #     | F.col("Dest").isNull()
        #     | (F.col("valid_origin_code") != True)
        #     | (F.col("valid_dest_code") != True)
        #     | (F.col("valid_route") != True)
        #     | (F.col("valid_cancelled") != True)
        #     | (F.col("valid_diverted") != True)
        #     | (F.col("valid_partition_date") != True)
        #     | (F.col("valid_year") != True)
        #     | (F.col("valid_month") != True)
        #     | (F.col("valid_quarter") != True)
        #     | (F.col("valid_day_of_month") != True)
        #     | (F.col("valid_day_of_week") != True)
        # )
        # hard_invalid_df.show(truncate=False)
        # hard_invalid_df.select(
        #     "FlightDate",
        #     "DOT_ID_Reporting_Airline",
        #     "Flight_Number_Reporting_Airline",
        #     "OriginAirportID",
        #     "Origin",
        #     "DestAirportID",
        #     "Dest",
        #     "Cancelled",
        #     "Diverted",
        #     "Year",
        #     "Month",
        #     "Quarter",
        #     "DayofMonth",
        #     "DayOfWeek",
        #     "valid_origin_code",
        #     "valid_dest_code",
        #     "valid_route",
        #     "valid_cancelled",
        #     "valid_diverted",
        #     "valid_partition_date",
        #     "valid_year",
        #     "valid_month",
        #     "valid_quarter",
        #     "valid_day_of_month",
        #     "valid_day_of_week",
        # ).show(truncate=False)


        valid_df = (
            silver_df
            .filter(F.col("FlightDate").isNotNull())
            .filter(F.col("DOT_ID_Reporting_Airline").isNotNull())
            .filter(F.col("Flight_Number_Reporting_Airline").isNotNull())
            .filter(F.col("OriginAirportID").isNotNull())
            .filter(F.col("Origin").isNotNull())
            .filter(F.col("DestAirportID").isNotNull())
            .filter(F.col("Dest").isNotNull())

            .filter(F.col("valid_origin_code"))
            .filter(F.col("valid_dest_code"))
            .filter(F.col("valid_route"))

            .filter(F.col("valid_cancelled"))
            .filter(F.col("valid_diverted"))

            .filter(F.col("valid_partition_date"))
            .filter(F.col("valid_year"))
            .filter(F.col("valid_month"))
            .filter(F.col("valid_quarter"))
            .filter(F.col("valid_day_of_month"))
            .filter(F.col("valid_day_of_week"))
        )


        # ---------------------------------------------------------
        # Validation
        # ---------------------------------------------------------

        validation_report = silver_df.agg(

            # Mandatory fields
            F.sum(F.when(F.col("FlightDate").isNull(), 1).otherwise(0)).alias("missing_flight_date"),
            F.sum(F.when(F.col("DOT_ID_Reporting_Airline").isNull(), 1).otherwise(0)).alias("missing_airline_id"),
            F.sum(F.when(F.col("Flight_Number_Reporting_Airline").isNull(), 1).otherwise(0)).alias("missing_flight_number"),
            F.sum(F.when(F.col("OriginAirportID").isNull(), 1).otherwise(0)).alias("missing_origin_airport_id"),
            F.sum(F.when(F.col("Origin").isNull(), 1).otherwise(0)).alias("missing_origin"),
            F.sum(F.when(F.col("DestAirportID").isNull(), 1).otherwise(0)).alias("missing_dest_airport_id"),
            F.sum(F.when(F.col("Dest").isNull(), 1).otherwise(0)).alias("missing_dest"),

            # Airport codes
            F.sum(F.when(F.col("Origin").isNotNull() & ~F.col("valid_origin_code"), 1).otherwise(0)).alias("invalid_origin_code"),
            F.sum(F.when(F.col("Dest").isNotNull() & ~F.col("valid_dest_code"), 1).otherwise(0)).alias("invalid_dest_code"),

            # Route
            F.sum(F.when(F.col("Origin").isNotNull() & F.col("Dest").isNotNull() & ~F.col("valid_route"), 1).otherwise(0)).alias("invalid_route"),

            # Flags
            F.sum(F.when(~F.col("valid_cancelled"), 1).otherwise(0)).alias("invalid_cancelled"),
            F.sum(F.when(~F.col("valid_diverted"), 1).otherwise(0)).alias("invalid_diverted"),
            F.sum(F.when(~F.col("valid_depdel15"), 1).otherwise(0)).alias("invalid_depdel15"), 
            F.sum(F.when(~F.col("valid_arrdel15"), 1).otherwise(0)).alias("invalid_arrdel15"),

            # Date / partition
            F.sum(F.when(~F.col("valid_partition_date"), 1).otherwise(0)).alias("invalid_partition_date"),
            F.sum(F.when(~F.col("valid_year"), 1).otherwise(0)).alias("invalid_year"),
            F.sum(F.when(~F.col("valid_month"), 1).otherwise(0)).alias("invalid_month"),
            F.sum(F.when(~F.col("valid_quarter"), 1).otherwise(0)).alias("invalid_quarter"),
            F.sum(F.when(~F.col("valid_day_of_month"), 1).otherwise(0)).alias("invalid_day_of_month"),
            F.sum(F.when(~F.col("valid_day_of_week"), 1).otherwise(0)).alias("invalid_day_of_week"),

            # Delay minutes
            F.sum(F.when(~F.col("valid_dep_delay_minutes"), 1).otherwise(0)).alias("invalid_dep_delay_minutes"),
            F.sum(F.when(~F.col("valid_arr_delay_minutes"), 1).otherwise(0)).alias("invalid_arr_delay_minutes"),

            # Taxi / elapsed / airtime
            F.sum(F.when(~F.col("valid_taxi_out"), 1).otherwise(0)).alias("invalid_taxi_out"),
            F.sum(F.when(~F.col("valid_taxi_in"), 1).otherwise(0)).alias("invalid_taxi_in"),
            F.sum(F.when(~F.col("valid_crs_elapsed_time"), 1).otherwise(0)).alias("invalid_crs_elapsed_time"),
            F.sum(F.when(~F.col("valid_actual_elapsed_time"), 1).otherwise(0)).alias("invalid_actual_elapsed_time"),
            F.sum(F.when(~F.col("valid_air_time"), 1).otherwise(0)).alias("invalid_air_time"),

            # Distance
            F.sum(F.when(~F.col("valid_distance"), 1).otherwise(0)).alias("invalid_distance"),

            # Delay reasons
            F.sum(F.when(~F.col("valid_carrier_delay"), 1).otherwise(0)).alias("invalid_carrier_delay"),
            F.sum(F.when(~F.col("valid_weather_delay"), 1).otherwise(0)).alias("invalid_weather_delay"),
            F.sum(F.when(~F.col("valid_nas_delay"), 1).otherwise(0)).alias("invalid_nas_delay"),
            F.sum(F.when(~F.col("valid_security_delay"), 1).otherwise(0)).alias("invalid_security_delay"),
            F.sum(F.when(~F.col("valid_late_aircraft_delay"), 1).otherwise(0)).alias("invalid_late_aircraft_delay"),

        ).first().asDict()


        # find reasons for not perfect data
        # print("\nInvalid ActualElapsedTime:")
        # silver_df.filter(
        #     ~F.col("valid_actual_elapsed_time")
        # ).select(
        #     "FlightDate",
        #     "Flight_Number_Reporting_Airline",
        #     "Origin",
        #     "Dest",
        #     "CRSElapsedTime",
        #     "ActualElapsedTime",
        #     "AirTime",
        #     "Cancelled",
        #     "Diverted"
        # ).show(truncate=False)

        # print("\nInvalid Distance:")
        # silver_df.filter(
        #     ~F.col("valid_distance")
        # ).select(
        #     "FlightDate",
        #     "Flight_Number_Reporting_Airline",
        #     "Origin",
        #     "Dest",
        #     "Distance",
        #     "DistanceGroup",
        #     "Cancelled",
        #     "Diverted"
        # ).show(truncate=False)

        # print("\nIvalid_elapsed time:")
        # silver_df.filter(
        #     ~F.col("valid_crs_elapsed_time")
        # ).select(
        #     "FlightDate",
        #     "Flight_Number_Reporting_Airline",
        #     "Origin",
        #     "Dest",
        #     "CRSDepTime",
        #     "CRSArrTime",
        #     "CRSElapsedTime",
        #     "Cancelled",
        #     "Diverted"
        # ).show(truncate=False)




        # # ---------------------------------------------------------
        # # Look for duplicates to be removed
        # # ---------------------------------------------------------
        count_before_duplicates = valid_df.count()

        valid_df = valid_df.dropDuplicates(
            ["FlightDate", "DOT_ID_Reporting_Airline", "Flight_Number_Reporting_Airline", "Origin", "Dest",]
        )

        count_after_duplicates = valid_df.count()

        duplicate_count = count_before_duplicates - count_after_duplicates


        # ---------------------------------------------------------
        # Remove aux columns
        # ---------------------------------------------------------

        valid_df = valid_df.drop(
            "valid_origin_code",
            "valid_dest_code",
            "valid_route",
            "valid_cancelled",
            "valid_diverted",
            "valid_depdel15",
            "valid_arrdel15",
            "valid_partition_date",
            "valid_year",
            "valid_month",
            "valid_quarter",
            "valid_day_of_month",
            "valid_day_of_week",
            "valid_dep_delay_minutes",
            "valid_arr_delay_minutes",
            "valid_taxi_out",
            "valid_taxi_in",
            "valid_crs_elapsed_time",
            "valid_actual_elapsed_time",
            "valid_air_time",
            "valid_distance",
            "valid_carrier_delay",
            "valid_weather_delay",
            "valid_nas_delay",
            "valid_security_delay",
            "valid_late_aircraft_delay",
        
        )


        # ---------------------------------------------------------
        # Final counts
        # ---------------------------------------------------------

        silver_count = valid_df.count()

        rejected_by_validation = (
            bronze_count
            - count_before_duplicates
        )

        rejected_total = (
            bronze_count
            - silver_count
        )


        # ---------------------------------------------------------
        # Write Silver
        # ---------------------------------------------------------

        (
            valid_df
            .write
            .mode("overwrite")
            .parquet(str(output_path))
        )

        print(f"Silver written to: {output_path}")



        # ---------------------------------------------------------
        # Validation Results
        # ---------------------------------------------------------

        report_dir = (
            SILVER_FLIGHT_REPORTS
            / f"year={year}"
            / f"month={month:02d}"
        )

        report_dir.mkdir(parents=True, exist_ok=True)

        report_path = report_dir / "validation_report.txt"

        run_timestamp = datetime.now(ZoneInfo("Europe/Berlin")).strftime("%Y-%m-%d %H:%M:%S")

        report_lines = [
            "",
            "=" * 70,
            f"VALIDATION REPORT - {year}-{month:02d}",
            f"Run timestamp: {run_timestamp}",
            "=" * 70,
            f"{'Bronze rows':<45} {bronze_count:>10}",
            "-" * 70,
            "HARD VALIDATION",
            "-" * 70,
            f"{'Missing FlightDate':<45} {validation_report['missing_flight_date']:>10}",
            f"{'Missing Airline ID':<45} {validation_report['missing_airline_id']:>10}",
            f"{'Missing Flight Number':<45} {validation_report['missing_flight_number']:>10}",
            f"{'Missing OriginAirportID':<45} {validation_report['missing_origin_airport_id']:>10}",
            f"{'Missing Origin':<45} {validation_report['missing_origin']:>10}",
            f"{'Missing DestAirportID':<45} {validation_report['missing_dest_airport_id']:>10}",
            f"{'Missing Dest':<45} {validation_report['missing_dest']:>10}",
            f"{'Invalid Origin Code':<45} {validation_report['invalid_origin_code']:>10}",
            f"{'Invalid Dest Code':<45} {validation_report['invalid_dest_code']:>10}",
            f"{'Origin equals Destination':<45} {validation_report['invalid_route']:>10}",
            f"{'Invalid Cancelled':<45} {validation_report['invalid_cancelled']:>10}",
            f"{'Invalid Diverted':<45} {validation_report['invalid_diverted']:>10}",
            f"{'Wrong FlightDate partition':<45} {validation_report['invalid_partition_date']:>10}",
            f"{'Wrong Year':<45} {validation_report['invalid_year']:>10}",
            f"{'Wrong Month':<45} {validation_report['invalid_month']:>10}",
            f"{'Invalid Quarter':<45} {validation_report['invalid_quarter']:>10}",
            f"{'Invalid DayOfMonth':<45} {validation_report['invalid_day_of_month']:>10}",
            f"{'Invalid DayOfWeek':<45} {validation_report['invalid_day_of_week']:>10}",
            "-" * 70,
            "SOFT VALIDATION",
            "-" * 70,
            f"{'Invalid DepDel15':<45} {validation_report['invalid_depdel15']:>10}",
            f"{'Invalid ArrDel15':<45} {validation_report['invalid_arrdel15']:>10}",
            f"{'Negative DepDelayMinutes':<45} {validation_report['invalid_dep_delay_minutes']:>10}",
            f"{'Negative ArrDelayMinutes':<45} {validation_report['invalid_arr_delay_minutes']:>10}",
            f"{'Invalid TaxiOut':<45} {validation_report['invalid_taxi_out']:>10}",
            f"{'Invalid TaxiIn':<45} {validation_report['invalid_taxi_in']:>10}",
            f"{'Invalid CRSElapsedTime':<45} {validation_report['invalid_crs_elapsed_time']:>10}",
            f"{'Invalid ActualElapsedTime':<45} {validation_report['invalid_actual_elapsed_time']:>10}",
            f"{'Invalid AirTime':<45} {validation_report['invalid_air_time']:>10}",
            f"{'Invalid Distance':<45} {validation_report['invalid_distance']:>10}",
            f"{'Invalid CarrierDelay':<45} {validation_report['invalid_carrier_delay']:>10}",
            f"{'Invalid WeatherDelay':<45} {validation_report['invalid_weather_delay']:>10}",
            f"{'Invalid NASDelay':<45} {validation_report['invalid_nas_delay']:>10}",
            f"{'Invalid SecurityDelay':<45} {validation_report['invalid_security_delay']:>10}",
            f"{'Invalid LateAircraftDelay':<45} {validation_report['invalid_late_aircraft_delay']:>10}",
            "-" * 70,
            "RESULT",
            "-" * 70,
            f"{'Rejected by hard validation':<45} {rejected_by_validation:>10}",
            f"{'Duplicates removed':<45} {duplicate_count:>10}",
            f"{'Total rejected':<45} {rejected_total:>10}",
            f"{'Silver rows':<45} {silver_count:>10}",
            "=" * 70,
        ]


        report_text = "\n".join(report_lines)
        print(report_text)

        report_path.write_text(
            report_text,
            encoding="utf-8"
        )

        print(f"Validation report written to: {report_path}")


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

