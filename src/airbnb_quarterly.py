# Aggregates the SA2-augmented AirBnB data to one row per listing per quarter
# and joins it to the Tenancy Services bond data
# Inputs:  outputs/sa_aug_cleaned_chch_airbnb.csv (from the Koordinates SA lookup script)
#          outputs/tenancy_services_chch_only.csv (from bond_import.py)
# Output:  outputs/airbnb_tenancy_joined.csv

# Imports
import yaml
import warnings
from pathlib import Path
import pandas as pd

# Loading in config.yaml
config_path = Path(__file__).resolve().parent.parent / "config.yaml"
with open(config_path, "r") as f:
    config = yaml.safe_load(f)

# Setting paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = PROJECT_ROOT / config["paths"]["outputs"]
AIRBNB_CSV = OUTPUTS_DIR / "sa_aug_cleaned_chch_airbnb.csv"
TENANCY_CSV = OUTPUTS_DIR / "tenancy_services_chch_only.csv"
OUTPUT_CSV = OUTPUTS_DIR / "airbnb_tenancy_joined.csv"

# Parameters
UNMATCHED_WARN_PERCENT = 20  # warn if more than this % of listing-quarters get no tenancy data

# Loading in both datasets, stopping with a clear message if an earlier step hasn't run
for path, step in [(AIRBNB_CSV, "the Koordinates SA lookup script"), (TENANCY_CSV, "bond_import.py")]:
    if not path.exists():
        raise FileNotFoundError(f"{path} not found. Run {step} first.")

df = pd.read_csv(AIRBNB_CSV)
df = df.drop(columns = ["Unnamed: 0"], errors = "ignore")  # old pandas index column, if present
ts = pd.read_csv(TENANCY_CSV)

# Sorting so "first" below really is the first month in each quarter
df["year_month"] = pd.to_datetime(df["year_month"])
df = df.sort_values(["id", "year_month"])

# Check: listings whose SA2 changes within a quarter (host moved the map pin)
# The first month's SA2 is kept (see Spatial Assignment decision in data_cleaning.md)
sa2_per_quarter = df.groupby(["id", "quarter"])["SA22019_V1_00"].nunique()
n_moved = (sa2_per_quarter > 1).sum()
if n_moved > 0:
    warnings.warn(
        f"{n_moved} listing-quarters have more than one SA2 code. "
        f"The SA2 from the first month in the quarter was used."
    )

# Aggregating to one row per listing per quarter
df_quarterly = df.groupby(["id", "quarter"]).agg(
    year_month = ("year_month", "first"),
    price = ("price", "mean"),
    number_of_reviews = ("number_of_reviews", "max"),
    minimum_nights = ("minimum_nights", "mean"),
    host_id = ("host_id", "first"),
    host_name = ("host_name", "first"),
    latitude = ("latitude", "first"),
    longitude = ("longitude", "first"),
    room_type = ("room_type", "first"),
    SA22019_V1_00 = ("SA22019_V1_00", "first")
).reset_index()
df_quarterly["SA22019_V1_00"] = df_quarterly["SA22019_V1_00"].astype("Int64")

# Converting the tenancy timeframe to the same quarter format (e.g. 2026Q1)
ts["quarter"] = pd.to_datetime(ts["TimeFrame"]).dt.to_period("Q").astype(str)

# Keeping the all-dwellings, all-bedrooms rows so there is one row per area per quarter
ts_all = ts[(ts["Dwelling Type"] == "ALL") & (ts["Number Of Beds"] == "ALL")].copy()
ts_all["Location Id"] = ts_all["Location Id"].astype("Int64")
ts_all = ts_all.dropna(subset = ["Location Id"])

# Joining the tenancy and quarterly datasets
airbnb_tenancy_joined = df_quarterly.merge(
    ts_all,
    left_on = ["SA22019_V1_00", "quarter"],
    right_on = ["Location Id", "quarter"],
    how = "left"
)

# Check: the join didn't duplicate any listing-quarters
if len(airbnb_tenancy_joined) != len(df_quarterly):
    raise ValueError(
        f"Join changed the row count from {len(df_quarterly)} to {len(airbnb_tenancy_joined)}. "
        f"Tenancy data has more than one row per area per quarter."
    )

# Check: how many listing-quarters found no tenancy data
unmatched_percent = airbnb_tenancy_joined["Median Rent"].isna().mean() * 100
if unmatched_percent > UNMATCHED_WARN_PERCENT:
    warnings.warn(f"{unmatched_percent:.1f}% of listing-quarters have no matching tenancy data.")

# Exporting
airbnb_tenancy_joined.to_csv(OUTPUT_CSV, index = False)
print(f"Saved {len(airbnb_tenancy_joined)} listing-quarters to {OUTPUT_CSV} ({unmatched_percent:.1f}% unmatched)")
