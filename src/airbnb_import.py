#Adapted from the AirBnB CHch base workflow.ipynb

#Imports
import yaml
from pathlib import Path
import pandas as pd

#Loading in config.yaml
config_path = Path(__file__).resolve().parent.parent / "config.yaml"
with open(config_path, "r") as f:
    config = yaml.safe_load(f)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / config["paths"]["data"]
OUTPUTS_DIR = PROJECT_ROOT / config["paths"]["outputs"]
LOOKUP_FILE = DATA_PATH / "AirBnB_date_lookup.csv"
OUTPUTS_CSV = OUTPUTS_DIR/ "AirBnB_all_chch.csv"
CITY_FILTER = "Christchurch City"

#Load lookup table
if not LOOKUP_FILE.exists():
    raise FileNotFoundError(f"Lookup file not found: {LOOKUP_FILE}")

lookup = pd.read_csv(LOOKUP_FILE)

required_cols = {"name", "year_month"}
missing_cols = required_cols - set(lookup.columns)
if missing_cols:
    raise ValueError(f"Lookup table missing columns: {missing_cols}")

#process monthly files
merged_data = []

for row in lookup.itertuples(index=False):
    file_path = DATA_PATH / row.name

    if not file_path.exists():
        raise FileNotFoundError(f"Expected monthly file not found: {file_path}")

    df = pd.read_csv(file_path)

    # Filter to Christchurch
    df = df[df["neighbourhood_group"] == CITY_FILTER]

    # Add year_month tag
    df["year_month"] = row.year_month

    merged_data.append(df)

#Merging all months
if len(merged_data) == 0:
    raise ValueError("No Christchurch listings found in any monthly file.")

merged_df = pd.concat(merged_data, ignore_index=True)

#Export to outputs
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
merged_df.to_csv(OUTPUTS_CSV, index=False)

