"""
Sanity check for the Airbnb x Tenancy Services join step (src/sql_prep.py).

Usage:  python sanity_check_join.py path/to/rentals.db

The step under test turns monthly Airbnb rows into one row per listing per
quarter and left-joins the area's median rent onto it. What can go wrong
silently is (a) rows being lost, (b) rows being duplicated by a fan-out
join, or (c) the wrong number landing in the wrong row. Each check below
targets one of those, and fails loudly with a message saying what broke.
"""
import sqlite3
import sys

import pandas as pd


def run_checks(db_path: str) -> None:
    con = sqlite3.connect(db_path)
    monthly = pd.read_sql_query("SELECT * FROM airbnb_listing_month", con)
    tenancy = pd.read_sql_query("SELECT * FROM tenancy_bond", con)
    joined = pd.read_sql_query("SELECT * FROM joined_quarterly", con)

    # 1. Row conservation: one output row per (listing, quarter), none lost.
    expected = monthly.groupby(["id", "quarter"]).ngroups
    assert len(joined) == expected, (
        f"Row count mismatch: joined has {len(joined)} rows, "
        f"but source has {expected} distinct (id, quarter) pairs")

    # 2. No fan-out: the join key must stay unique.
    dupes = joined.duplicated(["id", "quarter"]).sum()
    assert dupes == 0, f"{dupes} duplicated (id, quarter) rows after join"

    # 3. Hand-computed case: independent pandas calculation vs the SQL result.
    priced = monthly.dropna(subset=["price"])
    counts = priced.groupby(["id", "quarter"]).size()
    id_, q = counts[counts >= 2].index[0]          # a listing with 2+ priced months
    by_hand = priced[(priced.id == id_) & (priced.quarter == q)]["price"].mean()
    from_sql = joined[(joined.id == id_) & (joined.quarter == q)]["price"].iloc[0]
    assert abs(by_hand - from_sql) < 1e-9, (
        f"Listing {id_} in {q}: hand-computed mean price {by_hand} "
        f"!= pipeline value {from_sql}")

    # 4. Right rent on the right row: compare against the raw tenancy table.
    row = joined.dropna(subset=["median_rent"]).iloc[0]
    t = tenancy.assign(
        quarter=lambda d: pd.PeriodIndex(pd.to_datetime(d.timeframe), freq="Q").astype(str))
    t = t[(t.dwelling_type == "ALL") & (t.number_of_beds == "ALL")
          & (t.location_id == row.SA22019_V1_00) & (t.quarter == row.quarter)]
    assert len(t) == 1 and t.median_rent.iloc[0] == row.median_rent, (
        f"median_rent for SA2 {row.SA22019_V1_00} in {row.quarter} "
        f"does not match tenancy_bond")

    # 5. Plausibility (warning only): how many rows failed to get a rent?
    unmatched = joined.median_rent.isna().mean()
    print(f"OK: {len(joined)} rows, no duplicates, spot checks match. "
          f"{unmatched:.1%} of listing-quarters have no median_rent.")
    if unmatched > 0.2:
        print("WARNING: >20% unmatched. Check SA2 code types and quarter formats.")


if __name__ == "__main__":
    run_checks(sys.argv[1] if len(sys.argv) > 1 else "rentals.db")
