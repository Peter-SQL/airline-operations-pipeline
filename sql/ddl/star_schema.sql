-- analytics.dim_airline definition

-- Drop table

-- DROP TABLE analytics.dim_airline;

CREATE TABLE analytics.dim_airline (
	dot_id_reporting_airline int4 NOT NULL,
	airline_name text NULL,
	airline_code varchar(10) NULL,
	CONSTRAINT dim_airline_pkey PRIMARY KEY (dot_id_reporting_airline)
);


-- analytics.dim_airport definition

-- Drop table

-- DROP TABLE analytics.dim_airport;

CREATE TABLE analytics.dim_airport (
	airport_code varchar(10) NOT NULL,
	ac_city text NULL,
	ac_state text NULL,
	ac_airport text NULL,
	CONSTRAINT dim_airport_code_pkey PRIMARY KEY (airport_code)
);


-- analytics.dim_airport_id definition

-- Drop table

-- DROP TABLE analytics.dim_airport_id;

CREATE TABLE analytics.dim_airport_id (
	airport_id int4 NOT NULL,
	an_city text NULL,
	an_state text NULL,
	an_airport text NULL,
	CONSTRAINT dim_airport_num_pkey PRIMARY KEY (airport_id)
);


-- analytics.dim_cancel_reason definition

-- Drop table

-- DROP TABLE analytics.dim_cancel_reason;

CREATE TABLE analytics.dim_cancel_reason (
	cancel_code varchar(1) NOT NULL,
	cancel_reason varchar(50) NOT NULL,
	CONSTRAINT dim_cancel_reason_pkey PRIMARY KEY (cancel_code)
);


-- analytics.dim_date definition

-- Drop table

-- DROP TABLE analytics.dim_date;

CREATE TABLE analytics.dim_date (
	full_date date NOT NULL,
	"year" int4 NOT NULL,
	quarter int4 NOT NULL,
	"month" int4 NOT NULL,
	day_of_month int4 NOT NULL,
	day_of_week int4 NOT NULL,
	CONSTRAINT dim_date_pkey PRIMARY KEY (full_date)
);


-- analytics.fact_flight definition

-- Drop table

-- DROP TABLE analytics.fact_flight;

CREATE TABLE analytics.fact_flight (
	flight_id int8 GENERATED ALWAYS AS IDENTITY( INCREMENT BY 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1 NO CYCLE) NOT NULL,
	flightdate date NOT NULL,
	dot_id_reporting_airline int4 NULL,
	flight_number_reporting_airline int4 NULL,
	originairportid int4 NULL,
	destairportid int4 NULL,
	departuredelaygroups int4 NOT NULL,
	deptimeblk varchar(10) NOT NULL,
	taxiin int4 NOT NULL,
	taxiout int4 NOT NULL,
	arrivaldelaygroups int4 NOT NULL,
	cancelled bool NOT NULL,
	diverted bool NOT NULL,
	distance int4 NOT NULL,
	carrierdelay int4 NOT NULL,
	weatherdelay int4 NOT NULL,
	nasdelay int4 NOT NULL,
	securitydelay int4 NOT NULL,
	lateaircraftdelay int4 NOT NULL,
	CONSTRAINT fact_flight_pkey PRIMARY KEY (flight_id),
	CONSTRAINT fact_flight_destairportid_fkey FOREIGN KEY (destairportid) REFERENCES analytics.dim_airport_id(airport_id),
	CONSTRAINT fact_flight_dot_id_reporting_airline_fkey FOREIGN KEY (dot_id_reporting_airline) REFERENCES analytics.dim_airline(dot_id_reporting_airline),
	CONSTRAINT fact_flight_flightdate_fkey FOREIGN KEY (flightdate) REFERENCES analytics.dim_date(full_date),
	CONSTRAINT fact_flight_originairportid_fkey FOREIGN KEY (originairportid) REFERENCES analytics.dim_airport_id(airport_id)
);
CREATE INDEX idx_fact_flight_airline ON analytics.fact_flight USING btree (dot_id_reporting_airline);
CREATE INDEX idx_fact_flight_date ON analytics.fact_flight USING btree (flightdate);
CREATE INDEX idx_fact_flight_dest ON analytics.fact_flight USING btree (destairportid);
CREATE INDEX idx_fact_flight_origin ON analytics.fact_flight USING btree (originairportid);