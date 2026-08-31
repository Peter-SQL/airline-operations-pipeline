-- Incremental Gold build for one year/month.
-- Existing historical Gold rows remain unchanged.


CREATE TABLE IF NOT EXISTS analytics.gold_airline_reliability AS
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
                THEN 1 ELSE 0
            END
        ) / COUNT(*),
        2
    ) AS on_time_rate_pct,
    ROUND(AVG(f.dep_delay_minutes)::numeric, 2) AS avg_dep_delay_minutes,
    ROUND(AVG(f.arr_delay_minutes)::numeric, 2) AS avg_arr_delay_minutes,
    ROUND(100.0 * AVG(f.cancelled::numeric), 2) AS cancellation_rate_pct,
    ROUND(100.0 * AVG(f.diverted::numeric), 2) AS diversion_rate_pct,
    ROUND(SUM(COALESCE(f.carrier_delay, 0))::numeric / COUNT(*), 2)
        AS avg_carrier_delay_minutes,
    ROUND(SUM(COALESCE(f.weather_delay, 0))::numeric / COUNT(*), 2)
        AS avg_weather_delay_minutes,
    ROUND(SUM(COALESCE(f.nas_delay, 0))::numeric / COUNT(*), 2)
        AS avg_nas_delay_minutes,
    ROUND(SUM(COALESCE(f.security_delay, 0))::numeric / COUNT(*), 2)
        AS avg_security_delay_minutes,
    ROUND(SUM(COALESCE(f.late_aircraft_delay, 0))::numeric / COUNT(*), 2)
        AS avg_late_aircraft_delay_minutes,
    COUNT(f.dep_delay_minutes) AS dep_delay_flights,
    SUM(f.dep_delay_minutes)::numeric AS dep_delay_sum_minutes,
    COUNT(f.arr_delay_minutes) AS arr_delay_flights,
    SUM(f.arr_delay_minutes)::numeric AS arr_delay_sum_minutes
FROM analytics.fact_flight f
JOIN analytics.dim_airline a
    ON f.airline_id = a.airline_id
WHERE FALSE
GROUP BY
    EXTRACT(YEAR FROM f.flight_date),
    EXTRACT(MONTH FROM f.flight_date),
    f.airline_id,
    a.airline_name,
    a.airline_code;


ALTER TABLE analytics.gold_airline_reliability
    ADD COLUMN IF NOT EXISTS dep_delay_flights bigint,
    ADD COLUMN IF NOT EXISTS dep_delay_sum_minutes numeric,
    ADD COLUMN IF NOT EXISTS arr_delay_flights bigint,
    ADD COLUMN IF NOT EXISTS arr_delay_sum_minutes numeric;


DELETE FROM analytics.gold_airline_reliability
WHERE year = %(year)s
  AND month = %(month)s;


INSERT INTO analytics.gold_airline_reliability (
    year,
    month,
    airline_id,
    airline_name,
    airline_code,
    flights,
    on_time_rate_pct,
    avg_dep_delay_minutes,
    avg_arr_delay_minutes,
    cancellation_rate_pct,
    diversion_rate_pct,
    avg_carrier_delay_minutes,
    avg_weather_delay_minutes,
    avg_nas_delay_minutes,
    avg_security_delay_minutes,
    avg_late_aircraft_delay_minutes,
    dep_delay_flights,
    dep_delay_sum_minutes,
    arr_delay_flights,
    arr_delay_sum_minutes
)
SELECT
    EXTRACT(YEAR FROM f.flight_date)::integer,
    EXTRACT(MONTH FROM f.flight_date)::integer,
    f.airline_id,
    a.airline_name,
    a.airline_code,
    COUNT(*),
    ROUND(
        100.0 * SUM(
            CASE
                WHEN f.cancelled = 0
                 AND f.diverted = 0
                 AND f.arr_delay_minutes < 15
                THEN 1 ELSE 0
            END
        ) / COUNT(*),
        2
    ),
    ROUND(AVG(f.dep_delay_minutes)::numeric, 2),
    ROUND(AVG(f.arr_delay_minutes)::numeric, 2),
    ROUND(100.0 * AVG(f.cancelled::numeric), 2),
    ROUND(100.0 * AVG(f.diverted::numeric), 2),
    ROUND(SUM(COALESCE(f.carrier_delay, 0))::numeric / COUNT(*), 2),
    ROUND(SUM(COALESCE(f.weather_delay, 0))::numeric / COUNT(*), 2),
    ROUND(SUM(COALESCE(f.nas_delay, 0))::numeric / COUNT(*), 2),
    ROUND(SUM(COALESCE(f.security_delay, 0))::numeric / COUNT(*), 2),
    ROUND(SUM(COALESCE(f.late_aircraft_delay, 0))::numeric / COUNT(*), 2),
    COUNT(f.dep_delay_minutes),
    SUM(f.dep_delay_minutes)::numeric,
    COUNT(f.arr_delay_minutes),
    SUM(f.arr_delay_minutes)::numeric
FROM analytics.fact_flight f
JOIN analytics.dim_airline a
    ON f.airline_id = a.airline_id
WHERE f.flight_date >= make_date(%(year)s, %(month)s, 1)
  AND f.flight_date < make_date(%(year)s, %(month)s, 1) + INTERVAL '1 month'
GROUP BY
    EXTRACT(YEAR FROM f.flight_date),
    EXTRACT(MONTH FROM f.flight_date),
    f.airline_id,
    a.airline_name,
    a.airline_code;



CREATE TABLE IF NOT EXISTS analytics.gold_airport_reliability AS
SELECT
    EXTRACT(YEAR FROM f.flight_date)::integer AS year,
    EXTRACT(MONTH FROM f.flight_date)::integer AS month,
    f.origin_airport_id AS airport_id,
    a.airport_code,
    a.airport_name,
    a.city,
    a.state_code,
    a.state,
    'DEP'::text AS operation,
    COUNT(*) AS flights,
    ROUND(AVG(f.dep_delay_minutes)::numeric, 2) AS avg_delay_minutes,
    ROUND(
        100.0 * SUM(
            CASE
                WHEN f.cancelled = 0
                 AND f.diverted = 0
                 AND f.dep_delay_minutes < 15
                THEN 1 ELSE 0
            END
        ) / COUNT(*),
        2
    ) AS on_time_rate_pct,
    ROUND(100.0 * AVG(f.cancelled::numeric), 2) AS cancellation_rate_pct,
    ROUND(100.0 * AVG(f.diverted::numeric), 2) AS diversion_rate_pct,
    COUNT(f.dep_delay_minutes) AS delay_flights,
    SUM(f.dep_delay_minutes)::numeric AS delay_sum_minutes
FROM analytics.fact_flight f
JOIN analytics.dim_airport a
    ON f.origin_airport_id = a.airport_id
WHERE FALSE
GROUP BY
    EXTRACT(YEAR FROM f.flight_date),
    EXTRACT(MONTH FROM f.flight_date),
    f.origin_airport_id,
    a.airport_code,
    a.airport_name,
    a.city,
    a.state_code,
    a.state;


ALTER TABLE analytics.gold_airport_reliability
    ADD COLUMN IF NOT EXISTS delay_flights bigint,
    ADD COLUMN IF NOT EXISTS delay_sum_minutes numeric;


DELETE FROM analytics.gold_airport_reliability
WHERE year = %(year)s
  AND month = %(month)s;


INSERT INTO analytics.gold_airport_reliability (
    year,
    month,
    airport_id,
    airport_code,
    airport_name,
    city,
    state_code,
    state,
    operation,
    flights,
    avg_delay_minutes,
    on_time_rate_pct,
    cancellation_rate_pct,
    diversion_rate_pct,
    delay_flights,
    delay_sum_minutes
)
SELECT
    EXTRACT(YEAR FROM f.flight_date)::integer,
    EXTRACT(MONTH FROM f.flight_date)::integer,
    f.origin_airport_id,
    a.airport_code,
    a.airport_name,
    a.city,
    a.state_code,
    a.state,
    'DEP',
    COUNT(*),
    ROUND(AVG(f.dep_delay_minutes)::numeric, 2),
    ROUND(
        100.0 * SUM(
            CASE
                WHEN f.cancelled = 0
                 AND f.diverted = 0
                 AND f.dep_delay_minutes < 15
                THEN 1 ELSE 0
            END
        ) / COUNT(*),
        2
    ),
    ROUND(100.0 * AVG(f.cancelled::numeric), 2),
    ROUND(100.0 * AVG(f.diverted::numeric), 2),
    COUNT(f.dep_delay_minutes),
    SUM(f.dep_delay_minutes)::numeric
FROM analytics.fact_flight f
JOIN analytics.dim_airport a
    ON f.origin_airport_id = a.airport_id
WHERE f.flight_date >= make_date(%(year)s, %(month)s, 1)
  AND f.flight_date < make_date(%(year)s, %(month)s, 1) + INTERVAL '1 month'
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

SELECT
    EXTRACT(YEAR FROM f.flight_date)::integer,
    EXTRACT(MONTH FROM f.flight_date)::integer,
    f.dest_airport_id,
    a.airport_code,
    a.airport_name,
    a.city,
    a.state_code,
    a.state,
    'ARR',
    COUNT(*) FILTER (
        WHERE f.cancelled = 0
          AND f.diverted = 0
    ),
    ROUND(
        AVG(f.arr_delay_minutes) FILTER (
            WHERE f.cancelled = 0
              AND f.diverted = 0
        )::numeric,
        2
    ),
    ROUND(
        100.0 * SUM(
            CASE
                WHEN f.cancelled = 0
                 AND f.diverted = 0
                 AND f.arr_delay_minutes < 15
                THEN 1 ELSE 0
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
    ),
    NULL::numeric,
    NULL::numeric,
    COUNT(f.arr_delay_minutes) FILTER (
        WHERE f.cancelled = 0
          AND f.diverted = 0
    ),
    SUM(f.arr_delay_minutes) FILTER (
        WHERE f.cancelled = 0
          AND f.diverted = 0
    )::numeric
FROM analytics.fact_flight f
JOIN analytics.dim_airport a
    ON f.dest_airport_id = a.airport_id
WHERE f.flight_date >= make_date(%(year)s, %(month)s, 1)
  AND f.flight_date < make_date(%(year)s, %(month)s, 1) + INTERVAL '1 month'
GROUP BY
    EXTRACT(YEAR FROM f.flight_date),
    EXTRACT(MONTH FROM f.flight_date),
    f.dest_airport_id,
    a.airport_code,
    a.airport_name,
    a.city,
    a.state_code,
    a.state;



CREATE TABLE IF NOT EXISTS analytics.gold_route_reliability AS
SELECT
    EXTRACT(YEAR FROM f.flight_date)::integer AS year,
    EXTRACT(MONTH FROM f.flight_date)::integer AS month,

    f.origin_airport_id,
    origin.airport_code AS origin_airport_code,
    origin.airport_name AS origin_airport_name,
    origin.city AS origin_city,
    origin.state_code AS origin_state_code,
    origin.state AS origin_state,

    f.dest_airport_id,
    dest.airport_code AS dest_airport_code,
    dest.airport_name AS dest_airport_name,
    dest.city AS dest_city,
    dest.state_code AS dest_state_code,
    dest.state AS dest_state,

    COUNT(*) AS flights,
    ROUND(AVG(f.dep_delay_minutes)::numeric, 2) AS avg_dep_delay_minutes,
    ROUND(AVG(f.arr_delay_minutes)::numeric, 2) AS avg_arr_delay_minutes,
    ROUND(
        100.0 * SUM(
            CASE
                WHEN f.cancelled = 0
                 AND f.diverted = 0
                 AND f.arr_delay_minutes < 15
                THEN 1 ELSE 0
            END
        ) / COUNT(*),
        2
    ) AS on_time_rate_pct,
    ROUND(100.0 * AVG(f.cancelled::numeric), 2) AS cancellation_rate_pct,
    ROUND(100.0 * AVG(f.diverted::numeric), 2) AS diversion_rate_pct,
    COUNT(f.dep_delay_minutes) AS dep_delay_flights,
    SUM(f.dep_delay_minutes)::numeric AS dep_delay_sum_minutes,
    COUNT(f.arr_delay_minutes) AS arr_delay_flights,
    SUM(f.arr_delay_minutes)::numeric AS arr_delay_sum_minutes
FROM analytics.fact_flight f
JOIN analytics.dim_airport origin
    ON f.origin_airport_id = origin.airport_id
JOIN analytics.dim_airport dest
    ON f.dest_airport_id = dest.airport_id
WHERE FALSE
GROUP BY
    EXTRACT(YEAR FROM f.flight_date),
    EXTRACT(MONTH FROM f.flight_date),
    f.origin_airport_id,
    origin.airport_code,
    origin.airport_name,
    origin.city,
    origin.state_code,
    origin.state,
    f.dest_airport_id,
    dest.airport_code,
    dest.airport_name,
    dest.city,
    dest.state_code,
    dest.state;


ALTER TABLE analytics.gold_route_reliability
    ADD COLUMN IF NOT EXISTS origin_airport_name text,
    ADD COLUMN IF NOT EXISTS dest_airport_name text,
    ADD COLUMN IF NOT EXISTS dep_delay_flights bigint,
    ADD COLUMN IF NOT EXISTS dep_delay_sum_minutes numeric,
    ADD COLUMN IF NOT EXISTS arr_delay_flights bigint,
    ADD COLUMN IF NOT EXISTS arr_delay_sum_minutes numeric;


DELETE FROM analytics.gold_route_reliability
WHERE year = %(year)s
  AND month = %(month)s;


INSERT INTO analytics.gold_route_reliability (
    year,
    month,
    origin_airport_id,
    origin_airport_code,
    origin_city,
    origin_state_code,
    origin_state,
    dest_airport_id,
    dest_airport_code,
    dest_city,
    dest_state_code,
    dest_state,
    flights,
    avg_dep_delay_minutes,
    avg_arr_delay_minutes,
    on_time_rate_pct,
    cancellation_rate_pct,
    diversion_rate_pct,
    dep_delay_flights,
    dep_delay_sum_minutes,
    arr_delay_flights,
    arr_delay_sum_minutes,
    origin_airport_name,
    dest_airport_name
)
SELECT
    EXTRACT(YEAR FROM f.flight_date)::integer,
    EXTRACT(MONTH FROM f.flight_date)::integer,

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

    COUNT(*),
    ROUND(AVG(f.dep_delay_minutes)::numeric, 2),
    ROUND(AVG(f.arr_delay_minutes)::numeric, 2),
    ROUND(
        100.0 * SUM(
            CASE
                WHEN f.cancelled = 0
                 AND f.diverted = 0
                 AND f.arr_delay_minutes < 15
                THEN 1 ELSE 0
            END
        ) / COUNT(*),
        2
    ),
    ROUND(100.0 * AVG(f.cancelled::numeric), 2),
    ROUND(100.0 * AVG(f.diverted::numeric), 2),
    COUNT(f.dep_delay_minutes),
    SUM(f.dep_delay_minutes)::numeric,
    COUNT(f.arr_delay_minutes),
    SUM(f.arr_delay_minutes)::numeric,

    origin.airport_name,
    dest.airport_name

FROM analytics.fact_flight f
JOIN analytics.dim_airport origin
    ON f.origin_airport_id = origin.airport_id
JOIN analytics.dim_airport dest
    ON f.dest_airport_id = dest.airport_id
WHERE f.flight_date >= make_date(%(year)s, %(month)s, 1)
  AND f.flight_date < make_date(%(year)s, %(month)s, 1) + INTERVAL '1 month'
GROUP BY
    EXTRACT(YEAR FROM f.flight_date),
    EXTRACT(MONTH FROM f.flight_date),
    f.origin_airport_id,
    origin.airport_code,
    origin.airport_name,
    origin.city,
    origin.state_code,
    origin.state,
    f.dest_airport_id,
    dest.airport_code,
    dest.airport_name,
    dest.city,
    dest.state_code,
    dest.state;



CREATE TABLE IF NOT EXISTS analytics.gold_flight_reliability AS
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
    ROUND(AVG(f.dep_delay_minutes)::numeric, 2) AS avg_dep_delay_minutes,
    ROUND(AVG(f.arr_delay_minutes)::numeric, 2) AS avg_arr_delay_minutes,
    ROUND(
        100.0 * SUM(
            CASE
                WHEN f.cancelled = 0
                 AND f.diverted = 0
                 AND f.arr_delay_minutes < 15
                THEN 1 ELSE 0
            END
        ) / COUNT(*),
        2
    ) AS on_time_rate_pct,
    ROUND(100.0 * AVG(f.cancelled::numeric), 2) AS cancellation_rate_pct,
    ROUND(100.0 * AVG(f.diverted::numeric), 2) AS diversion_rate_pct,
    COUNT(f.dep_delay_minutes) AS dep_delay_flights,
    SUM(f.dep_delay_minutes)::numeric AS dep_delay_sum_minutes,
    COUNT(f.arr_delay_minutes) AS arr_delay_flights,
    SUM(f.arr_delay_minutes)::numeric AS arr_delay_sum_minutes
FROM analytics.fact_flight f
JOIN analytics.dim_airline airline
    ON f.airline_id = airline.airline_id
JOIN analytics.dim_airport origin
    ON f.origin_airport_id = origin.airport_id
JOIN analytics.dim_airport dest
    ON f.dest_airport_id = dest.airport_id
WHERE FALSE
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


ALTER TABLE analytics.gold_flight_reliability
    ADD COLUMN IF NOT EXISTS dep_delay_flights bigint,
    ADD COLUMN IF NOT EXISTS dep_delay_sum_minutes numeric,
    ADD COLUMN IF NOT EXISTS arr_delay_flights bigint,
    ADD COLUMN IF NOT EXISTS arr_delay_sum_minutes numeric;


DELETE FROM analytics.gold_flight_reliability
WHERE year = %(year)s
  AND month = %(month)s;


INSERT INTO analytics.gold_flight_reliability (
    year,
    month,
    airline_id,
    airline_name,
    airline_code,
    flight_number,
    origin_airport_id,
    origin_airport_code,
    origin_city,
    origin_state_code,
    origin_state,
    dest_airport_id,
    dest_airport_code,
    dest_city,
    dest_state_code,
    dest_state,
    flights,
    avg_dep_delay_minutes,
    avg_arr_delay_minutes,
    on_time_rate_pct,
    cancellation_rate_pct,
    diversion_rate_pct,
    dep_delay_flights,
    dep_delay_sum_minutes,
    arr_delay_flights,
    arr_delay_sum_minutes
)
SELECT
    EXTRACT(YEAR FROM f.flight_date)::integer,
    EXTRACT(MONTH FROM f.flight_date)::integer,
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
    dest.state,
    COUNT(*),
    ROUND(AVG(f.dep_delay_minutes)::numeric, 2),
    ROUND(AVG(f.arr_delay_minutes)::numeric, 2),
    ROUND(
        100.0 * SUM(
            CASE
                WHEN f.cancelled = 0
                 AND f.diverted = 0
                 AND f.arr_delay_minutes < 15
                THEN 1 ELSE 0
            END
        ) / COUNT(*),
        2
    ),
    ROUND(100.0 * AVG(f.cancelled::numeric), 2),
    ROUND(100.0 * AVG(f.diverted::numeric), 2),
    COUNT(f.dep_delay_minutes),
    SUM(f.dep_delay_minutes)::numeric,
    COUNT(f.arr_delay_minutes),
    SUM(f.arr_delay_minutes)::numeric
FROM analytics.fact_flight f
JOIN analytics.dim_airline airline
    ON f.airline_id = airline.airline_id
JOIN analytics.dim_airport origin
    ON f.origin_airport_id = origin.airport_id
JOIN analytics.dim_airport dest
    ON f.dest_airport_id = dest.airport_id
WHERE f.flight_date >= make_date(%(year)s, %(month)s, 1)
  AND f.flight_date < make_date(%(year)s, %(month)s, 1) + INTERVAL '1 month'
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



CREATE INDEX IF NOT EXISTS idx_gold_airline_year_month
ON analytics.gold_airline_reliability (year, month);

CREATE INDEX IF NOT EXISTS idx_gold_route_year_month
ON analytics.gold_route_reliability (year, month);

CREATE INDEX IF NOT EXISTS idx_gold_flight_year_month
ON analytics.gold_flight_reliability (year, month);

CREATE INDEX IF NOT EXISTS idx_gold_airport_year_month_operation
ON analytics.gold_airport_reliability (year, month, operation);