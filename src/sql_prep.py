"""Builds the SQLite database (rentals.db) from the prepared Airbnb and Tenancy Services data.

Adapted from deliv_5_sql.ipynb. Run from anywhere with:  python src/sql_prep.py
Paths come from src/config.py; nothing runs on import, so the functions can be tested.

Tables created:
    airbnb_listing_month  one row per listing per month
    tenancy_bond          Tenancy Services bond statistics per SA2 per quarter
    joined_quarterly      one row per listing per quarter, with the area's median rent
"""
import sqlite3
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config

AIRBNB_SCHEMA = """
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
"""

TENANCY_SCHEMA = """
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
"""

# Groups monthly Airbnb rows into one row per listing per quarter (the SA2 comes from
# the listing's first month in that quarter), filters tenancy to the single
# "all dwellings, all bedrooms" rent per area per quarter (without this filter the join
# would create copies of each listing, one per dwelling type), then LEFT JOINs on SA2
# and quarter so no listing-quarter is lost or duplicated.
JOIN_SQL = """
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


def load_airbnb(con, csv_path):
    """Creates airbnb_listing_month and loads the prepared Airbnb CSV into it."""
    con.execute("DROP TABLE IF EXISTS airbnb_listing_month;")
    con.execute(AIRBNB_SCHEMA)
    df = pd.read_csv(csv_path)
    df = df.drop(columns="Unnamed: 0", errors="ignore")  # old pandas index column, if present
    df.to_sql("airbnb_listing_month", con, if_exists="append", index=False)
    con.commit()
    return len(df)


def load_tenancy(con, csv_path):
    """Creates tenancy_bond and loads the Tenancy Services CSV (columns renamed for SQL)."""
    con.execute("DROP TABLE IF EXISTS tenancy_bond;")
    con.execute(TENANCY_SCHEMA)
    ts = pd.read_csv(csv_path)
    ts.columns = ts.columns.str.lower().str.replace(" ", "_")
    ts.to_sql("tenancy_bond", con, if_exists="append", index=False)
    con.commit()
    return len(ts)


def build_joined_quarterly(con):
    """Runs the quarterly aggregation and join and stores the result as joined_quarterly."""
    joined = pd.read_sql_query(JOIN_SQL, con)
    joined.to_sql("joined_quarterly", con, if_exists="replace", index=False)
    con.commit()
    return joined


def check_loads(con, n_airbnb_expected, n_tenancy_expected):
    """Load checks (previously only in deliv_5_sql.ipynb). Raises AssertionError if any fail."""
    n_airbnb = con.execute("SELECT COUNT(*) FROM airbnb_listing_month").fetchone()[0]
    n_tenancy = con.execute("SELECT COUNT(*) FROM tenancy_bond").fetchone()[0]
    assert n_airbnb == n_airbnb_expected, f"airbnb rows: table has {n_airbnb}, file had {n_airbnb_expected}"
    assert n_tenancy == n_tenancy_expected, f"tenancy rows: table has {n_tenancy}, file had {n_tenancy_expected}"

    sa_type, q_type = con.execute(
        "SELECT typeof(SA22019_V1_00), typeof(quarter) FROM airbnb_listing_month WHERE SA22019_V1_00 IS NOT NULL LIMIT 1"
    ).fetchone()
    assert (sa_type, q_type) == ("integer", "text"), f"join column types are {sa_type}/{q_type}, expected integer/text"

    loc_type = con.execute("SELECT typeof(location_id) FROM tenancy_bond LIMIT 1").fetchone()[0]
    assert loc_type == "integer", f"tenancy location_id type is {loc_type}, expected integer"


def check_join(con, joined):
    """Join checks: no listing-quarter lost or duplicated. Raises AssertionError if any fail."""
    n_expected = con.execute(
        "SELECT COUNT(*) FROM (SELECT DISTINCT id, quarter FROM airbnb_listing_month)"
    ).fetchone()[0]
    assert len(joined) == n_expected, f"joined has {len(joined)} rows, expected {n_expected} listing-quarters"
    n_dupes = int(joined.duplicated(["id", "quarter"]).sum())
    assert n_dupes == 0, f"{n_dupes} duplicated listing-quarters after the join"


def main(airbnb_csv=config.AIRBNB_CSV, tenancy_csv=config.TENANCY_CSV, db_path=config.DB_PATH):
    con = sqlite3.connect(db_path)
    try:
        n_airbnb = load_airbnb(con, airbnb_csv)
        n_tenancy = load_tenancy(con, tenancy_csv)
        check_loads(con, n_airbnb, n_tenancy)
        joined = build_joined_quarterly(con)
        check_join(con, joined)
    finally:
        con.close()

    n_matched = int(joined["median_rent"].notna().sum())
    print(f"Built {db_path}")
    print(f"  airbnb_listing_month: {n_airbnb} rows | tenancy_bond: {n_tenancy} rows")
    print(f"  joined_quarterly: {len(joined)} rows, {n_matched} with a median rent, {len(joined) - n_matched} without")


if __name__ == "__main__":
    main()
