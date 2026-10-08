# Cleans the combined Christchurch AirBnB data for the automated pipeline
# Input:  outputs/AirBnB_all_chch.csv (all months, Chch only, from the AirBnB base workflow script)
# Output: outputs/cleaned_chch_airbnb.csv (read by the Koordinates SA lookup script)

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
INPUT_CSV = OUTPUTS_DIR / "AirBnB_all_chch.csv"
OUTPUT_CSV = OUTPUTS_DIR / "cleaned_chch_airbnb.csv"

# Parameters
CITY_FILTER = "Christchurch City"
MISSINGNESS_THRESHOLD = 50  # % of a row missing before it gets flagged; must match data_cleaning.md

# Loading in the combined AirBnB data, stopping with a clear message if the previous step hasn't run
if not INPUT_CSV.exists():
    raise FileNotFoundError(
        f"{INPUT_CSV} not found. Run the AirBnB base workflow script first."
    )
df = pd.read_csv(INPUT_CSV)

# Check: only Christchurch listings made it through the filter
assert (df["neighbourhood_group"] == CITY_FILTER).all(), \
    "Non-Christchurch listings detected, filtering step failed."

# Check: each listing appears at most once per month (the SQL table uses id + year_month as its key)
n_dupes = df.duplicated(["id", "year_month"]).sum()
if n_dupes > 0:
    raise ValueError(f"{n_dupes} rows share the same id and year_month. Check the lookup table for a repeated file.")

# Check: rows with a lot of missing values
# These are flagged but not removed (see Row Completeness decision in data_cleaning.md)
row_missing_percent = df.isnull().mean(axis = 1) * 100
n_high_missing = (row_missing_percent >= MISSINGNESS_THRESHOLD).sum()
if n_high_missing > 0:
    warnings.warn(f"{n_high_missing} rows have {MISSINGNESS_THRESHOLD}% or more missing values. They were kept.")

# Setting year_month to a date and sorting on id, then month
df["year_month"] = pd.to_datetime(df["year_month"], format = "%Y-%m")
df = df.sort_values(["id", "year_month"])

# Adding the quarter here so the exported file already has it; the Koordinates
# lookup and the SQL quarterly join rely on this column
df["quarter"] = df["year_month"].dt.to_period("Q")

# Exporting
df.to_csv(OUTPUT_CSV, index = False)
print(f"Saved {len(df)} rows ({df['id'].nunique()} listings) to {OUTPUT_CSV}")
