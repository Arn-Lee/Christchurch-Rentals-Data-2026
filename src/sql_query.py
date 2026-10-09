# Companion py script to generate an automated notebook from a template
# Based on deliv_5_analysis.ipynb

# Imports
import sqlite3
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import geopandas as gpd
import papermill
import yaml
from pathlib import Path
import subprocess

# Loading in config.yaml
config_path = Path(__file__).resolve().parent.parent / "config.yaml"
with open(config_path, "r") as f:
    config = yaml.safe_load(f)

# Setting paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = PROJECT_ROOT / config["paths"]["outputs"]
DB_PATH = PROJECT_ROOT / config["paths"]["sql_db"]
DATA_PATH = PROJECT_ROOT / config["paths"]["data"]
SRC_PATH = PROJECT_ROOT / config["paths"]["src"]

#Connecting to existing SQLite database
con = sqlite3.connect(DB_PATH)

# Loading up the SA2 polygons (also useful for SA2 code name lookup)
sa_areas = gpd.read_file(DATA_PATH / "statsnz-statistical-area/statistical-area-2-2019-generalised.shp")

# Coverting CRS to NZGD2000 (EPSG:2193), if not already
sa_areas = sa_areas.to_crs(2193)

# Recasting SA22019_V1 to int for join
sa_areas["SA22019_V1"] = sa_areas["SA22019_V1"].astype(int)

# Performing join and saving out the head of the table for display in the notebook
joined = pd.read_sql_query("SELECT * FROM joined_quarterly;", con)
joined_head = joined.head()
joined_head.to_csv(OUTPUTS_DIR / "joined_sql_table.csv", index = False)

# Calculating median price for Chch central
median_chch_central = joined.loc[
    joined["SA22019_V1_00"] == 326600, "price"
].median()

#Calculating the gap bet airbnb prices and long term rental

#Convert weekly to per night rent
joined["long_term_price_per_night"] = joined["median_rent"] / 7

#Working out price gap
joined["price_gap"] = joined["price"] - joined["long_term_price_per_night"]
joined[["SA22019_V1_00", "price", "long_term_price_per_night", "price_gap"]].head()

#Finding the maximum gap
gap_by_sa2 = (
    joined.groupby("SA22019_V1_00")["price_gap"]
    .median()
    .sort_values(ascending=False)
)
top_gap_area = gap_by_sa2.index[0] # extracting top SA2 code
top_gap_price = gap_by_sa2.iloc[0] # extracting top price
top_gap_name = sa_areas.loc[ # getting human readable name from geographic data above
    sa_areas["SA22019_V1"] == top_gap_area,
    "SA22019__1"
].iloc[0]

# Generating plot
gap_valid = joined.dropna(subset=["median_rent"])

gap_by_sa2 = (
    gap_valid.groupby("SA22019_V1_00")["price_gap"]
    .median()
    .reset_index()
)

top_sa2 = gap_by_sa2.sort_values("price_gap", ascending=False).head(10)

plt.figure(figsize=(12,6))
sns.barplot(
    data=top_sa2,
    x="SA22019_V1_00",
    y="price_gap",
    order=top_sa2["SA22019_V1_00"]
)

plt.title("Top SA2 Areas with Largest Airbnb vs Long-Term Rent Gaps")
plt.ylabel("Median Price Gap ($)")
plt.xlabel("SA2 Code")
plt.tight_layout()
plt.savefig(OUTPUTS_DIR / "top_sa2_gaps.png",
            dpi=300,
            bbox_inches="tight")
plt.close()

# Comparing AirBnbs and rentals in each location
counts_sql = """
WITH airbnb_counts AS (
    SELECT SA22019_V1_00 AS sa2, quarter, COUNT(DISTINCT id) AS airbnb_listings
    FROM airbnb_listing_month
    GROUP BY SA22019_V1_00, quarter
),
rental_counts AS (
    SELECT location_id AS sa2,
            strftime('%Y', timeframe) || 'Q' ||
                ((CAST(strftime('%m', timeframe) AS INTEGER) + 2) / 3) AS quarter,
            active_bonds AS rental_properties
    FROM tenancy_bond
    WHERE dwelling_type = 'ALL' AND number_of_beds = 'ALL'
)
SELECT a.sa2 AS SA22019_V1_00, a.quarter, a.airbnb_listings, r.rental_properties
FROM airbnb_counts a
LEFT JOIN rental_counts r ON a.sa2 = r.sa2 AND a.quarter = r.quarter
"""
counts_quarterly = pd.read_sql_query(counts_sql, con)

print("area-quarters:", len(counts_quarterly),
      "| duplicates:", counts_quarterly.duplicated(["SA22019_V1_00","quarter"]).sum())
print("areas missing rental data in at least one quarter:",
      counts_quarterly.loc[counts_quarterly["rental_properties"].isna(),"SA22019_V1_00"].nunique())

compare_location = (
    counts_quarterly.groupby("SA22019_V1_00")[["airbnb_listings", "rental_properties"]]
    .mean()
    .reset_index()
)
compare_location["airbnb_to_longterm_ratio"] = (
    compare_location["airbnb_listings"] / compare_location["rental_properties"]
)

#sorting..
compare_location_head = compare_location.sort_values("airbnb_to_longterm_ratio", ascending=False).head(10)

# Writing back out to output for inclusion in report
compare_location_head.to_csv(OUTPUTS_DIR / "compare_location_head.csv", index = False)

# Joining the polygon data to the prepped data in preparation for map below
sa_joined = sa_areas.merge(compare_location,
                           left_on = "SA22019_V1",
                           right_on = "SA22019_V1_00",
                           how = "left")

# Preparing choropleth map
fig, ax = plt.subplots(figsize = (8,8))

sa_joined.plot(
    column = "airbnb_to_longterm_ratio",
    cmap = "viridis",
    legend = True,
    vmax = 1,
    ax = ax,
    missing_kwds = {"color" : "lightgrey", "label": "No data"}
)

# Setting axis limits
ax.set_xlim(1540000, 1595000)
ax.set_ylim(5160000, 5200000)

ax.set_title("AirBnB to long-term rental ratio")
ax.axis("off") # don't need the distance axes

plt.savefig(OUTPUTS_DIR / "airbnb_to_longterm_choropleth.png",
            dpi=300,
            bbox_inches="tight")
plt.close()

# Generating automated report via papermill
papermill.execute_notebook(
    SRC_PATH / "sql_query_notebook_template.ipynb",
    OUTPUTS_DIR / "sql_query_notebook_generated.ipynb",
    cwd = SRC_PATH,
    parameters = {
        "median_chch_central": float(median_chch_central),
        "top_gap_area": int(top_gap_area),
        "top_gap_price": float(top_gap_price),
        "top_gap_name": str(top_gap_name)
    }
)

# Converting generated report to clean HTML
subprocess.run(
    [
        "jupyter",
        "nbconvert",
        str(OUTPUTS_DIR / "sql_query_notebook_generated.ipynb"),
        "--to",
        "html",
        "--no-input"
    ],
    check = True
)