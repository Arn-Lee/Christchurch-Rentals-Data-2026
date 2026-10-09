# Koordinates lookup

import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import yaml
from dotenv import load_dotenv
import os

# Loding config
PROJECT_ROOT = Path(__file__).resolve().parent.parent

config_path = PROJECT_ROOT / "config.yaml"
with open(config_path, "r") as f:
    config = yaml.safe_load(f)

DATA_PATH = PROJECT_ROOT / config["paths"]["data"]
OUTPUTS_PATH = PROJECT_ROOT / config["paths"]["outputs"]

INPUT_FILE = OUTPUTS_PATH / "cleaned_chch_airbnb.csv"
OUTPUT_FILE = OUTPUTS_PATH / "sa_aug_cleaned_chch_airbnb.csv"

# Koordinates settings
SA2_LAYER_ID = 98970
KOORDINATES_URL = "https://koordinates.com/services/query/v1/vector.json"
NUM_WORKERS = 8

# Loading api
load_dotenv()
api_key = os.getenv("api_key")

#Koordinates query
def koord_query(lat, lon):
    params = {
        "key": api_key,
        "layer": SA2_LAYER_ID,
        "x": lon,
        "y": lat
    }

    try:
        response = requests.get(KOORDINATES_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        return data["vectorQuery"]["layers"][str(SA2_LAYER_ID)]["features"][0]["properties"]["SA22019_V1_00"]

    except (requests.RequestException, KeyError, IndexError, ValueError):
        return None

# main worfklow
def main():
    print(">>> MAIN() STARTED <<<")

    # Load Airbnb data
    airbnb_data = pd.read_csv(INPUT_FILE)

    # Unique coordinates
    unique_coords = airbnb_data[["latitude", "longitude"]].drop_duplicates()
    coords = list(zip(unique_coords["latitude"], unique_coords["longitude"]))

    print(f">>> Querying {len(coords)} unique coordinates <<<")

    # Parallel Koordinates lookup
    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        results = list(executor.map(lambda xy: koord_query(xy[0], xy[1]), coords))

    unique_coords["SA22019_V1_00"] = results

    # Merge back
    airbnb_data = airbnb_data.merge(unique_coords, on=["latitude", "longitude"], how="left")

    # Check failures
    n_failed = airbnb_data["SA22019_V1_00"].isna().sum()
    if n_failed > 0:
        raise ValueError(f"{n_failed} rows have no SA2 code")

    # Save output
    airbnb_data.to_csv(OUTPUT_FILE, index=False)
    print(f">>> Saved SA2‑augmented Airbnb dataset to {OUTPUT_FILE} <<<")

# -----------------------------
# RUN SCRIPT
# -----------------------------
if __name__ == "__main__":
    main()
