WITH params AS (
    SELECT
        %s::integer AS year,
        %s::integer AS month
)

-- 1. Pflichtfelder
SELECT
    'invalid_required_fields' AS check_name,
    COUNT(*)::bigint AS error_count
FROM analytics.fact_flight f
CROSS JOIN params p
WHERE EXTRACT(YEAR FROM f.flight_date) = p.year
  AND EXTRACT(MONTH FROM f.flight_date) = p.month
  AND (
       f.flight_date IS NULL
       OR f.airline_id IS NULL
       OR f.flight_number IS NULL
       OR f.origin_airport_id IS NULL
       OR f.dest_airport_id IS NULL
       OR f.cancelled IS NULL
       OR f.diverted IS NULL
  )

UNION ALL

-- 2. Cancelled / Diverted
SELECT
    'invalid_flags',
    COUNT(*)::bigint
FROM analytics.fact_flight f
CROSS JOIN params p
WHERE EXTRACT(YEAR FROM f.flight_date) = p.year
  AND EXTRACT(MONTH FROM f.flight_date) = p.month
  AND (
      f.cancelled NOT IN (0, 1)
      OR f.diverted NOT IN (0, 1)
  )

UNION ALL

-- 3. Airline muss in Dimension existieren
SELECT
    'unknown_airlines',
    COUNT(*)::bigint
FROM analytics.fact_flight f
CROSS JOIN params p
LEFT JOIN analytics.dim_airline a
    ON f.airline_id = a.airline_id
WHERE EXTRACT(YEAR FROM f.flight_date) = p.year
  AND EXTRACT(MONTH FROM f.flight_date) = p.month
  AND a.airline_id IS NULL

UNION ALL

-- 4. Origin Airport muss existieren
SELECT
    'unknown_origin_airports',
    COUNT(*)::bigint
FROM analytics.fact_flight f
CROSS JOIN params p
LEFT JOIN analytics.dim_airport a
    ON f.origin_airport_id = a.airport_id
WHERE EXTRACT(YEAR FROM f.flight_date) = p.year
  AND EXTRACT(MONTH FROM f.flight_date) = p.month
  AND a.airport_id IS NULL

UNION ALL

-- 5. Destination Airport muss existieren
SELECT
    'unknown_dest_airports',
    COUNT(*)::bigint
FROM analytics.fact_flight f
CROSS JOIN params p
LEFT JOIN analytics.dim_airport a
    ON f.dest_airport_id = a.airport_id
WHERE EXTRACT(YEAR FROM f.flight_date) = p.year
  AND EXTRACT(MONTH FROM f.flight_date) = p.month
  AND a.airport_id IS NULL

UNION ALL

-- 6. Fachliche Dubletten
SELECT
    'duplicate_flights',
    COUNT(*)::bigint
FROM (
    SELECT
        f.flight_date,
        f.airline_id,
        f.flight_number,
        f.origin_airport_id,
        f.dest_airport_id
    FROM analytics.fact_flight f
    CROSS JOIN params p
    WHERE EXTRACT(YEAR FROM f.flight_date) = p.year
      AND EXTRACT(MONTH FROM f.flight_date) = p.month
    GROUP BY
        f.flight_date,
        f.airline_id,
        f.flight_number,
        f.origin_airport_id,
        f.dest_airport_id
    HAVING COUNT(*) > 1
) d

UNION ALL

-- 7. Airline Gold KPI Wertebereiche
SELECT
    'invalid_airline_kpis',
    COUNT(*)::bigint
FROM analytics.gold_airline_reliability g
CROSS JOIN params p
WHERE g.year = p.year
  AND g.month = p.month
  AND (
      g.flights < 0
      OR g.on_time_rate_pct NOT BETWEEN 0 AND 100
      OR g.cancellation_rate_pct NOT BETWEEN 0 AND 100
      OR g.diversion_rate_pct NOT BETWEEN 0 AND 100
  )

UNION ALL

-- 8. Airport Gold KPI Wertebereiche
SELECT
    'invalid_airport_kpis',
    COUNT(*)::bigint
FROM analytics.gold_airport_reliability g
CROSS JOIN params p
WHERE g.year = p.year
  AND g.month = p.month
  AND (
      g.flights < 0
      OR g.on_time_rate_pct NOT BETWEEN 0 AND 100
      OR g.cancellation_rate_pct NOT BETWEEN 0 AND 100
      OR g.diversion_rate_pct NOT BETWEEN 0 AND 100
  )

UNION ALL

-- 9. Route Gold KPI Wertebereiche
SELECT
    'invalid_route_kpis',
    COUNT(*)::bigint
FROM analytics.gold_route_reliability g
CROSS JOIN params p
WHERE g.year = p.year
  AND g.month = p.month
  AND (
      g.flights < 0
      OR g.on_time_rate_pct NOT BETWEEN 0 AND 100
      OR g.cancellation_rate_pct NOT BETWEEN 0 AND 100
      OR g.diversion_rate_pct NOT BETWEEN 0 AND 100
  )

UNION ALL

-- 10. Fact und Airline-Gold müssen dieselbe Fluganzahl enthalten
SELECT
    'fact_vs_airline_gold',
    ABS(
        (
            SELECT COUNT(*)
            FROM analytics.fact_flight f
            CROSS JOIN params p
            WHERE EXTRACT(YEAR FROM f.flight_date) = p.year
              AND EXTRACT(MONTH FROM f.flight_date) = p.month
        )
        -
        (
            SELECT COALESCE(SUM(g.flights), 0)
            FROM analytics.gold_airline_reliability g
            CROSS JOIN params p
            WHERE g.year = p.year
              AND g.month = p.month
        )
    )::bigint;