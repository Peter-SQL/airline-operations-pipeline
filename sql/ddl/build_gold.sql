DROP TABLE IF EXISTS analytics.gold_airline_reliability;

CREATE TABLE analytics.gold_airline_reliability AS
SELECT
    EXTRACT(YEAR FROM f.flight_date)::integer AS year,
    EXTRACT(MONTH FROM f.flight_date)::integer AS month,
    f.airline_id,
    a.airline_name,
    a.airline_code,
    COUNT(*) AS flights,
    ROUND(
        100.0 * SUM(
            CASE
                WHEN f.cancelled = 0
                 AND f.diverted = 0
                 AND f.arr_delay_minutes < 15
                THEN 1
                ELSE 0
            END
        ) / COUNT(*),
        2
    ) AS on_time_rate_pct,
    ROUND(AVG(f.dep_delay_minutes)::numeric, 2)
        AS avg_dep_delay_minutes,
    ROUND(AVG(f.arr_delay_minutes)::numeric, 2)
        AS avg_arr_delay_minutes,
    ROUND(
        100.0 * AVG(f.cancelled::numeric),
        2
    ) AS cancellation_rate_pct,
    ROUND(
        100.0 * AVG(f.diverted::numeric),
        2
    ) AS diversion_rate_pct,
ROUND(    SUM(COALESCE(f.carrier_delay, 0))::numeric / COUNT(*),    2) AS avg_carrier_delay_minutes,
ROUND(    SUM(COALESCE(f.weather_delay, 0))::numeric / COUNT(*),    2) AS avg_weather_delay_minutes,
ROUND(    SUM(COALESCE(f.nas_delay, 0))::numeric / COUNT(*),    2) AS avg_nas_delay_minutes,
ROUND(    SUM(COALESCE(f.security_delay, 0))::numeric / COUNT(*),    2) AS avg_security_delay_minutes,
ROUND(    SUM(COALESCE(f.late_aircraft_delay, 0))::numeric / COUNT(*),    2) AS avg_late_aircraft_delay_minutes
FROM analytics.fact_flight f
JOIN analytics.dim_airline a
    ON f.airline_id = a.airline_id
GROUP BY
    EXTRACT(YEAR FROM f.flight_date),
    EXTRACT(MONTH FROM f.flight_date),
    f.airline_id,
    a.airline_name,
    a.airline_code;


DROP TABLE IF EXISTS analytics.gold_airport_reliability;


CREATE TABLE analytics.gold_airport_reliability AS
-- Departures
SELECT
    EXTRACT(YEAR FROM f.flight_date)::integer AS year,
    EXTRACT(MONTH FROM f.flight_date)::integer AS month,
    f.origin_airport_id AS airport_id,
    a.airport_code,
    a.airport_name,
    a.city,
    a.state_code,
    a.state,
    'DEP' AS operation,
    COUNT(*) AS flights,
    ROUND(
        AVG(f.dep_delay_minutes)::numeric,
        2
    ) AS avg_delay_minutes,
    ROUND(
        100.0 * SUM(
            CASE
                WHEN f.cancelled = 0
                 AND f.diverted = 0
                 AND f.dep_delay_minutes < 15
                THEN 1
                ELSE 0
            END
        ) / COUNT(*),
        2
    ) AS on_time_rate_pct,
    ROUND(
        100.0 * AVG(f.cancelled::numeric),
        2
    ) AS cancellation_rate_pct,
    ROUND(
        100.0 * AVG(f.diverted::numeric),
        2
    ) AS diversion_rate_pct
FROM analytics.fact_flight f
JOIN analytics.dim_airport a
    ON f.origin_airport_id = a.airport_id
GROUP BY
    EXTRACT(YEAR FROM f.flight_date),
    EXTRACT(MONTH FROM f.flight_date),
    f.origin_airport_id,
    a.airport_code,
    a.airport_name,
    a.city,
    a.state_code,
    a.state
UNION ALL
-- Arrivals
SELECT
    EXTRACT(YEAR FROM f.flight_date)::integer AS year,
    EXTRACT(MONTH FROM f.flight_date)::integer AS month,
    f.dest_airport_id AS airport_id,
    a.airport_code,
    a.airport_name,
    a.city,
    a.state_code,
    a.state,
    'ARR' AS operation,
    COUNT(*) FILTER (
    WHERE f.cancelled = 0
      AND f.diverted = 0
	) AS flights,
    ROUND(
    AVG(f.arr_delay_minutes) FILTER (
        WHERE f.cancelled = 0
          AND f.diverted = 0
    )::numeric,
    2
) AS avg_delay_minutes,
      ROUND(
    100.0 * SUM(
        CASE
            WHEN f.cancelled = 0
             AND f.diverted = 0
             AND f.arr_delay_minutes < 15
            THEN 1
            ELSE 0
        END
    )
    /
    NULLIF(
        COUNT(*) FILTER (
            WHERE f.cancelled = 0
              AND f.diverted = 0
        ),
        0
    ),
    2
) AS on_time_rate_pct,
    NULL::numeric AS cancellation_rate_pct,
    NULL::numeric AS diversion_rate_pct
FROM analytics.fact_flight f
JOIN analytics.dim_airport a
    ON f.dest_airport_id = a.airport_id
GROUP BY
    EXTRACT(YEAR FROM f.flight_date),
    EXTRACT(MONTH FROM f.flight_date),
    f.dest_airport_id,
    a.airport_code,
    a.airport_name,
    a.city,
    a.state_code,
	a.state;



DROP TABLE IF EXISTS analytics.gold_route_reliability;
 

CREATE TABLE analytics.gold_route_reliability AS
SELECT
    EXTRACT(YEAR FROM f.flight_date)::integer AS year,
    EXTRACT(MONTH FROM f.flight_date)::integer AS month,
    -- Origin
    f.origin_airport_id,
    origin.airport_code AS origin_airport_code,
    origin.city AS origin_city,
    origin.state_code AS origin_state_code,
    origin.state AS origin_state,
    -- Destination
    f.dest_airport_id,
    dest.airport_code AS dest_airport_code,
    dest.city AS dest_city,
    dest.state_code AS dest_state_code,
    dest.state AS dest_state,
    f.airline_id,
airline.airline_name,
airline.airline_code,
    f.day_of_week,
    CASE f.day_of_week
    WHEN 1 THEN 'Monday'
    WHEN 2 THEN 'Tuesday'
    WHEN 3 THEN 'Wednesday'
    WHEN 4 THEN 'Thursday'
    WHEN 5 THEN 'Friday'
    WHEN 6 THEN 'Saturday'
    WHEN 7 THEN 'Sunday'
END AS day_of_week_name,
    COUNT(*) AS flights,
    ROUND(
        AVG(f.dep_delay_minutes)::numeric,
        2
    ) AS avg_dep_delay_minutes,
    ROUND(
        AVG(f.arr_delay_minutes)::numeric,
        2
    ) AS avg_arr_delay_minutes,
    ROUND(
        100.0 * SUM(
            CASE
                WHEN f.cancelled = 0
                 AND f.diverted = 0
                 AND f.arr_delay_minutes < 15
                THEN 1
                ELSE 0
            END
        ) / COUNT(*),
        2
    ) AS on_time_rate_pct,
    ROUND(
        100.0 * AVG(f.cancelled::numeric),
        2
    ) AS cancellation_rate_pct,
    ROUND(
        100.0 * AVG(f.diverted::numeric),
        2
    ) AS diversion_rate_pct
FROM analytics.fact_flight f
JOIN analytics.dim_airline airline
    ON f.airline_id = airline.airline_id
JOIN analytics.dim_airport origin
    ON f.origin_airport_id = origin.airport_id
JOIN analytics.dim_airport dest
    ON f.dest_airport_id = dest.airport_id
GROUP BY
    EXTRACT(YEAR FROM f.flight_date),
    EXTRACT(MONTH FROM f.flight_date),
    f.origin_airport_id,
    origin.airport_code,
    origin.city,
    origin.state_code,
    origin.state,
    f.dest_airport_id,
    dest.airport_code,
    dest.city,
    dest.state_code,
    dest.state,
f.airline_id,
f.day_of_week,
airline.airline_name,
airline.airline_code;


DROP TABLE IF EXISTS analytics.gold_flight_reliability;

CREATE TABLE analytics.gold_flight_reliability AS
SELECT
    EXTRACT(YEAR FROM f.flight_date)::integer AS year,
    EXTRACT(MONTH FROM f.flight_date)::integer AS month,
    f.airline_id,
    airline.airline_name,
    airline.airline_code,
    f.flight_number,
    f.origin_airport_id,
    origin.airport_code AS origin_airport_code,
    origin.city AS origin_city,
    origin.state_code AS origin_state_code,
    origin.state AS origin_state,
    f.dest_airport_id,
    dest.airport_code AS dest_airport_code,
    dest.city AS dest_city,
    dest.state_code AS dest_state_code,
    dest.state AS dest_state,
    COUNT(*) AS flights,
    ROUND(
        AVG(f.dep_delay_minutes)::numeric,
        2
    ) AS avg_dep_delay_minutes,
    ROUND(
        AVG(f.arr_delay_minutes)::numeric,
        2
    ) AS avg_arr_delay_minutes,
    ROUND(
        100.0 * SUM(
            CASE
                WHEN f.cancelled = 0
                 AND f.diverted = 0
                 AND f.arr_delay_minutes < 15
                THEN 1
                ELSE 0
            END
        ) / COUNT(*),
        2
    ) AS on_time_rate_pct,
    ROUND(
        100.0 * AVG(f.cancelled::numeric),
        2
    ) AS cancellation_rate_pct,
    ROUND(
        100.0 * AVG(f.diverted::numeric),
        2
    ) AS diversion_rate_pct
FROM analytics.fact_flight f
JOIN analytics.dim_airline airline
    ON f.airline_id = airline.airline_id
JOIN analytics.dim_airport origin
    ON f.origin_airport_id = origin.airport_id
JOIN analytics.dim_airport dest
    ON f.dest_airport_id = dest.airport_id
GROUP BY
    EXTRACT(YEAR FROM f.flight_date),
    EXTRACT(MONTH FROM f.flight_date),
    f.airline_id,
    airline.airline_name,
    airline.airline_code,
    f.flight_number,
    f.origin_airport_id,
    origin.airport_code,
    origin.city,
    origin.state_code,
    origin.state,
    f.dest_airport_id,
    dest.airport_code,
    dest.city,
    dest.state_code,
    dest.state;
