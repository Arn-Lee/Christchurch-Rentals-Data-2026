# Imports and prepares Tenancy Services bond data
# Adapted from Tenancy_Services_bond_cleanup.ipynb

# Imports
import yaml
from pathlib import Path
import pandas as pd
import geopandas as gpd

# Loading in config.yaml
config_path = Path(__file__).resolve().parent.parent / "config.yaml"
with open(config_path, "r") as f:
    config = yaml.safe_load(f)

# Setting paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = PROJECT_ROOT / config["paths"]["outputs"]
DATA_PATH = PROJECT_ROOT / config["paths"]["data"]
SRC_PATH = PROJECT_ROOT / config["paths"]["src"]

# Loading in geospatial data and checking for missing shp accessory files
try:
    sa_areas = gpd.read_file(DATA_PATH / "statsnz-statistical-area/statistical-area-2-2019-generalised.shp")
except Exception as e:
    raise FileNotFoundError(
        f"Failed to load shapefile. Check that all shapefile components "
        f"(.shp, .shx, .dbf, .prj) are present. Original error: {e}"
    ) from e

airbnb_all_area = gpd.read_file(DATA_PATH / "neighbourhoods.geojson")

# Validate and set CRS
if sa_areas.crs is None:
    raise ValueError("SA2 shapefile has no CRS defined.")

if airbnb_all_area.crs is None:
    raise ValueError("GeoJSON has no CRS defined.")

sa_areas = sa_areas.to_crs(2193)
airbnb_all_area = airbnb_all_area.to_crs(2193)

if sa_areas.crs != airbnb_all_area.crs:
    raise ValueError(
        f"Unexpected CRS mismatch between datasets"
    )

# Reading in TS Bond dataset + validation
matches = list(DATA_PATH.glob("Detailed-Quarterly-Tenancy*.csv"))

if len(matches) == 0:
    raise FileNotFoundError(
        "No Detailed-Quarterly-Tenancy CSV found."
    )

if len(matches) > 1:
    raise ValueError(
        f"Expected one file, found {len(matches)}: {matches}"
    )

ts_data = pd.read_csv(matches[0])

# Selecting Chch-only SA2 areas first
airbnb_chch_area = airbnb_all_area[airbnb_all_area["neighbourhood_group"] == "Christchurch City"]
if airbnb_chch_area.empty:
    raise ValueError(
        "No 'Christchurch City' neighbourhood_group found in GeoJSON."
    )

boundary = airbnb_chch_area.geometry.iloc[0]
overlap_area = sa_areas.intersection(boundary).area
total_area = sa_areas.area
coverage = overlap_area / total_area
chch_sa = sa_areas[coverage > 0.5] # Only selecting SAs with at least 50% coverage

# Now to filter the TS dataset (location Id) by the areas identified in chch_sa
chch_codes = chch_sa["SA22019_V1"]
ts_data["Location Id"] = ts_data["Location Id"].astype("Int64")
chch_codes = chch_codes.astype("Int64")
ts_chch = ts_data[ts_data["Location Id"].isin(chch_codes)]

# Exporting back out to Data folder as a csv
OUTPUTS_DIR.mkdir(parents = True, exist_ok = True)
ts_chch.to_csv(OUTPUTS_DIR / "tenancy_services_chch_only.csv", index = False)