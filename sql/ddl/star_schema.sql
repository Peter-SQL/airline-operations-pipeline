-- analytics.dim_airline definition

-- Drop table

-- DROP TABLE analytics.dim_airline;

CREATE TABLE analytics.dim_airline (
	airline_id int4 NOT NULL,
	airline_name text NOT NULL,
	airline_code varchar(10) NULL,
	CONSTRAINT dim_airline_pkey PRIMARY KEY (airline_id)
);


-- analytics.dim_airport definition

-- Drop table

-- DROP TABLE analytics.dim_airport;

CREATE TABLE analytics.dim_airport (
	airport_id int4 NOT NULL,
	airport_code varchar(10) NULL,
	city text NULL,
	state text NULL,
	airport_name text NULL,
	state_code varchar(2) NULL,
	CONSTRAINT dim_airport_pkey PRIMARY KEY (airport_id)
);


-- analytics.fact_flight definition

-- Drop table

-- DROP TABLE analytics.fact_flight;

CREATE TABLE analytics.fact_flight (
	flight_id bigserial NOT NULL,
	flight_date date NOT NULL,
	airline_id int4 NOT NULL,
	flight_number int4 NOT NULL,
	origin_airport_id int4 NOT NULL,
	dest_airport_id int4 NOT NULL,
	day_of_week int4 NULL,
	dep_time_block varchar(20) NULL,
	dep_delay_minutes int4 NULL,
	arr_delay_minutes int4 NULL,
	cancelled int4 NOT NULL,
	diverted int4 NOT NULL,
	carrier_delay int4 NULL,
	weather_delay int4 NULL,
	nas_delay int4 NULL,
	security_delay int4 NULL,
	late_aircraft_delay int4 NULL,
	CONSTRAINT fact_flight_pkey PRIMARY KEY (flight_id)
);
CREATE INDEX idx_fact_flight_airline ON analytics.fact_flight USING btree (airline_id);
CREATE INDEX idx_fact_flight_date ON analytics.fact_flight USING btree (flight_date);
CREATE INDEX idx_fact_flight_dest ON analytics.fact_flight USING btree (dest_airport_id);
CREATE INDEX idx_fact_flight_origin ON analytics.fact_flight USING btree (origin_airport_id);


