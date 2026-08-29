import pytest

from datetime import date

from src.transformation.silver_transformation import (
    REQUIRED_COLUMNS,
    validate_schema,
    add_validation_flags,
)


class FakeDataFrame:
    def __init__(self, columns):
        self.columns = columns


def test_validate_schema_complete():
    df = FakeDataFrame(REQUIRED_COLUMNS)

    validate_schema(df)


def test_validate_schema_missing_column():
    columns = [
        column
        for column in REQUIRED_COLUMNS
        if column != "FlightDate"
    ]

    df = FakeDataFrame(columns)

    with pytest.raises(ValueError, match="FlightDate"):
        validate_schema(df)

def test_add_validation_flags(spark):

    data = [
        {
            "Origin": "JFK",
            "Dest": "LAX",
            "Cancelled": 0,
            "Diverted": 0,
            "DepDel15": 0,
            "ArrDel15": 1,
            "FlightDate": date(2026, 6, 15),
            "Year": 2026,
            "Month": 6,
            "Quarter": 2,
            "DayofMonth": 15,
            "DayOfWeek": 1,
            "DepDelayMinutes": 10,
            "ArrDelayMinutes": 20,
            "TaxiOut": 15,
            "TaxiIn": 10,
            "CRSElapsedTime": 360,
            "ActualElapsedTime": 355,
            "AirTime": 320,
            "Distance": 2475,
            "CarrierDelay": 10,
            "WeatherDelay": 0,
            "NASDelay": 5,
            "SecurityDelay": 0,
            "LateAircraftDelay": 5,
        },
        {
            "Origin": "XX",
            "Dest": "LAX",
            "Cancelled": 2,
            "Diverted": 0,
            "DepDel15": 3,
            "ArrDel15": 0,
            "FlightDate": date(2026, 5, 15),
            "Year": 2025,
            "Month": 5,
            "Quarter": 5,
            "DayofMonth": 32,
            "DayOfWeek": 8,
            "DepDelayMinutes": -1,
            "ArrDelayMinutes": -5,
            "TaxiOut": -1,
            "TaxiIn": -1,
            "CRSElapsedTime": -10,
            "ActualElapsedTime": -10,
            "AirTime": -10,
            "Distance": 0,
            "CarrierDelay": -1,
            "WeatherDelay": -1,
            "NASDelay": -1,
            "SecurityDelay": -1,
            "LateAircraftDelay": -1,
        },
    ]

    df = spark.createDataFrame(data)

    result = add_validation_flags(
        df,
        year=2026,
        month=6,
    ).collect()

    valid = result[0]
    invalid = result[1]

    # Valid row
    assert valid.valid_origin_code is True
    assert valid.valid_dest_code is True
    assert valid.valid_route is True
    assert valid.valid_cancelled is True
    assert valid.valid_diverted is True
    assert valid.valid_partition_date is True
    assert valid.valid_year is True
    assert valid.valid_month is True
    assert valid.valid_distance is True

    # Invalid row
    assert invalid.valid_origin_code is False
    assert invalid.valid_cancelled is False
    assert invalid.valid_depdel15 is False
    assert invalid.valid_partition_date is False
    assert invalid.valid_year is False
    assert invalid.valid_month is False
    assert invalid.valid_quarter is False
    assert invalid.valid_day_of_month is False
    assert invalid.valid_day_of_week is False
    assert invalid.valid_dep_delay_minutes is False
    assert invalid.valid_arr_delay_minutes is False
    assert invalid.valid_taxi_out is False
    assert invalid.valid_taxi_in is False
    assert invalid.valid_crs_elapsed_time is False
    assert invalid.valid_actual_elapsed_time is False
    assert invalid.valid_air_time is False
    assert invalid.valid_distance is False
    assert invalid.valid_carrier_delay is False
    assert invalid.valid_weather_delay is False
    assert invalid.valid_nas_delay is False
    assert invalid.valid_security_delay is False
    assert invalid.valid_late_aircraft_delay is False


def test_route_invalid_when_origin_equals_dest(spark):

    data = [{
        "Origin": "JFK",
        "Dest": "JFK",
        "Cancelled": 0,
        "Diverted": 0,
        "DepDel15": 0,
        "ArrDel15": 0,
        "FlightDate": date(2026, 6, 15),
        "Year": 2026,
        "Month": 6,
        "Quarter": 2,
        "DayofMonth": 15,
        "DayOfWeek": 1,
        "DepDelayMinutes": 0,
        "ArrDelayMinutes": 0,
        "TaxiOut": 10,
        "TaxiIn": 10,
        "CRSElapsedTime": 100,
        "ActualElapsedTime": 90,
        "AirTime": 70,
        "Distance": 500,
        "CarrierDelay": 0,
        "WeatherDelay": 0,
        "NASDelay": 0,
        "SecurityDelay": 0,
        "LateAircraftDelay": 0,
    }]

    df = spark.createDataFrame(data)

    result = add_validation_flags(
        df,
        year=2026,
        month=6,
    ).first()

    assert result.valid_route is False



def test_route_valid_when_origin_equals_dest_but_cancelled(spark):

    data = [{
        "Origin": "JFK",
        "Dest": "JFK",
        "Cancelled": 1,
        "Diverted": 0,
        "DepDel15": 0,
        "ArrDel15": 0,
        "FlightDate": date(2026, 6, 15),
        "Year": 2026,
        "Month": 6,
        "Quarter": 2,
        "DayofMonth": 15,
        "DayOfWeek": 1,
        "DepDelayMinutes": 0,
        "ArrDelayMinutes": 0,
        "TaxiOut": 10,
        "TaxiIn": 10,
        "CRSElapsedTime": 100,
        "ActualElapsedTime": 90,
        "AirTime": 70,
        "Distance": 500,
        "CarrierDelay": 0,
        "WeatherDelay": 0,
        "NASDelay": 0,
        "SecurityDelay": 0,
        "LateAircraftDelay": 0,
    }]

    df = spark.createDataFrame(data)

    result = add_validation_flags(
        df,
        year=2026,
        month=6,
    ).first()

    assert result.valid_route is True
