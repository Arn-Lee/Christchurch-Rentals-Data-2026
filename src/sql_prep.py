# This script is adapted from deliv_5_sql.ipynb
# It's intended to generate the SQL DB from prepared data

# Header for paths/imports
airbnb_input_path = "/outputs/sa_aug_cleaned_chch_airbnb.csv"
tenancy_input_path = "/outputs/tenancy_services_chch_only.csv"
output_path = "/outputs/rentals.db"

import sqlite3
import pandas as pd

# Update if any changes to location of data
AIRBNB_CSV  = airbnb_input_path
TENANCY_CSV = tenancy_input_path

DB_PATH     = output_path

# Opens a connection
con = sqlite3.connect(DB_PATH)

# Defines the AirBnb table with types for each column
con.execute("DROP TABLE IF EXISTS airbnb_listing_month;")
con.execute("""
CREATE TABLE airbnb_listing_month (
    id                              INTEGER NOT NULL,
    name                            TEXT,
    host_id                         REAL,
    host_name                       TEXT,
    neighbourhood_group             TEXT,
    neighbourhood                   TEXT,
    latitude                        REAL,
    longitude                       REAL,
    room_type                       TEXT,
    price                           REAL,
    minimum_nights                  REAL,
    number_of_reviews               INTEGER,
    last_review                     TEXT,
    reviews_per_month               REAL,
    calculated_host_listings_count  REAL,
    availability_365                INTEGER,
    number_of_reviews_ltm           INTEGER,
    license                         TEXT,
    year_month                      TEXT NOT NULL,
    quarter                         TEXT NOT NULL,
    SA22019_V1_00                   INTEGER,
    PRIMARY KEY (id, year_month)
);
""");

# Reads file then removes pandas index column
df = pd.read_csv(AIRBNB_CSV)
df = df.drop(columns="Unnamed: 0")

# loads rows into table then puts prepared dataset into database
df.to_sql("airbnb_listing_month", con, if_exists="append", index=False)
con.commit()

# creates an empty tenancy table with fixed types, read for next dataset
con.execute("DROP TABLE IF EXISTS tenancy_bond;")
con.execute("""
CREATE TABLE tenancy_bond (
    timeframe               TEXT    NOT NULL,
    location_id             INTEGER NOT NULL,
    dwelling_type           TEXT    NOT NULL,
    number_of_beds          TEXT,
    total_bonds             INTEGER,
    active_bonds            INTEGER,
    closed_bonds            INTEGER,
    median_rent             REAL,
    geometric_mean_rent     REAL,
    upper_quartile_rent     REAL,
    lower_quartile_rent     REAL,
    log_std_dev_weekly_rent REAL
);
  """);


# reads tenancy file then converts column names to lowercase with underscores so that it can be used in SQL
# data is then loaded as the second dataset in the database
ts = pd.read_csv(TENANCY_CSV)
ts.columns = ts.columns.str.lower().str.replace(" ", "_")
ts.to_sql("tenancy_bond", con, if_exists="append", index=False)
con.commit()

# SQL query that groups monthly airbnb rows into 1 row per listing per quarter,
# then filtered tenancy to 1 "all dwellings, all bedrooms" rent per area per quarter with correct quarter format - without this it would create copies of listings, all with different rents.
# then left joins them on area code and quarter so every listing-quarter has its area's median rent without any rows being lost or duplicated.
join_sql = """
WITH airbnb_ranked AS (
      SELECT *,
          ROW_NUMBER() OVER (PARTITION BY id, quarter ORDER BY year_month) AS month_order
      FROM airbnb_listing_month
),
airbnb_quarterly AS (
      SELECT
          id,
          quarter,
          MIN(year_month)         AS year_month,
          AVG(price)              AS price,
          AVG(minimum_nights)     AS minimum_nights,
          MAX(number_of_reviews)  AS number_of_reviews,
          MAX(CASE WHEN month_order = 1 THEN SA22019_V1_00 END) AS SA22019_V1_00
      FROM airbnb_ranked
      GROUP BY id, quarter
),
tenancy_quarterly AS (
      SELECT
          location_id,
          strftime('%Y', timeframe) || 'Q' ||
              ((CAST(strftime('%m', timeframe) AS INTEGER) + 2) / 3) AS quarter,
          total_bonds,
          active_bonds,
          median_rent,
          lower_quartile_rent,
          upper_quartile_rent
      FROM tenancy_bond
      WHERE dwelling_type = 'ALL' AND number_of_beds = 'ALL'
)
SELECT
      a.id, a.quarter, a.year_month, a.SA22019_V1_00,
      a.price, a.minimum_nights, a.number_of_reviews,
      t.median_rent, t.lower_quartile_rent, t.upper_quartile_rent,
      t.total_bonds, t.active_bonds
FROM airbnb_quarterly AS a
LEFT JOIN tenancy_quarterly AS t
      ON  a.SA22019_V1_00 = t.location_id
      AND a.quarter       = t.quarter;
"""
joined = pd.read_sql_query(join_sql, con)
joined.to_sql("joined_quarterly", con, if_exists="replace", index=False)
con.commit()