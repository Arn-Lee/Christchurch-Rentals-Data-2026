# Christchurch-Rentals-Data-2026

# NOTE: this project is currently under development

This project is intended to prepare and analyse data for short-term and long-term rentals in Chrichchurch, New Zealand sourced from AirBnB and Tenancy Services.

AirBnB data is provided by Inside Airbnb (https://insideairbnb.com/get-the-data/). This project uses nine monthly `listings.csv` files for New Zealand (October 2025 to June 2026), saved as `listings-0.csv` (newest, June 2026) to `listings-8.csv` (oldest, October 2025); `workflows/AirBnB_date_lookup.csv` maps each file to its month.
These data are available under public domain.
Downloaded data (.csv) should be saved within a subdirectory named 'data', these have been excluded from this repo.

The data dictionary for the AirBnB data is also available at Inside Airbnb. For convenience, this is available below:

| FIELD                          | TYPE     | CALCULATED | DESCRIPTION                                                                                                                                                                                       |
|--------------------------------|----------|------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| id                             | integer  |            | Airbnb's unique identifier for the listing                                                                                                                                                        |
| name                           | string   |            |                                                                                                                                                                                                   |
| host_id                        | integer  |            |                                                                                                                                                                                                   |
| host_name                      | string   |            |                                                                                                                                                                                                   |
| neighbourhood_group            | text     | y          | The neighbourhood group as geocoded using the latitude and longitude against neighborhoods as defined by open or public digital shapefiles.                                                       |
| neighbourhood                  | text     | y          | The neighbourhood as geocoded using the latitude and longitude against neighborhoods as defined by open or public digital shapefiles.                                                             |
| latitude                       | numeric  |            | Uses the World Geodetic System (WGS84) projection for latitude and longitude.                                                                                                                     |
| longitude                      |          |            | Uses the World Geodetic System (WGS84) projection for latitude and longitude.                                                                                                                     |
| room_type                      | string   |            |                                                                                                                                                                                                   |
| price                          | currency |            | daily price in local currency. Note, $ sign may be used despite locale                                                                                                                            |
| minimum_nights                 | integer  |            | minimum number of night stay for the listing (calendar rules may be different)                                                                                                                    |
| number_of_reviews              | integer  |            | The number of reviews the listing has                                                                                                                                                             |
| last_review                    | date     | y          | The date of the last/newest review                                                                                                                                                                |
| calculated_host_listings_count | integer  | y          | The number of listings the host has in the current scrape, in the city/region geography.                                                                                                          |
| availability_365               | integer  | y          | avaliability_x. The availability of the listing x days in the future as determined by the calendar. Note a listing may be available because it has been booked by a guest or blocked by the host. |
| number_of_reviews_ltm          | integer  | y          | The number of reviews the listing has (in the last 12 months)                                                                                                                                     |
| license                        | string   |            |                                                                                                                                                                                                   |

Bond lodgement data from Tenancy Services includes summary statistics related to bonds lodged with Tenancy Services per statistical area. 

It is available at https://www.tenancy.govt.nz/about-tenancy-services/data-and-statistics/rental-bond-data/

As a data dictionary was not provided, the following descriptions are assumed:


TODO note: we'll need to update this towards the end of the course (during refactor week) with a more accurate and descriptive readme.

TODO note 2: Need to clean up the table since we'll be culling some of the cols

TODO note 3: Actually, we'll need to clean up this whole readme to describe the contents of the files and how/why to run them.

## How to run the pipeline

See [DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md) for the inputs, outputs and design of the pipeline. Create the environment with `pip install -r requirements.txt`, put the raw downloads in a folder named `data/` at the project root (git-ignored), and run these in order (notebooks from within `workflows/`):

1. `workflows/Chch_dataset_clean.ipynb` collates the monthly files, investigates data quality (decisions in [data_cleaning.md](data_cleaning.md)) and writes `workflows/cleaned_chch_airbnb.csv`.
2. `workflows/Koordinates SA lookup.ipynb` adds the Statistical Area 2 code and writes `workflows/sa_aug_cleaned_chch_airbnb.csv`. It needs a Koordinates API key in a `.env` file at the project root (`api_key = YOUR_KEY`) and is slow, so rerun it sparingly.
3. `workflows/Tenancy_Services_bond_cleanup.ipynb` filters the Tenancy Services data to Christchurch and writes `data/tenancy_services_chch_only.csv`. It needs `data/neighbourhoods.geojson`, the Stats NZ SA2 shapefile in `data/statsnz-statistical-area/`, and the Tenancy Services CSV in `data/`.
4. `python src/sql_prep.py` builds `rentals.db` (tables `airbnb_listing_month`, `tenancy_bond`, `joined_quarterly`). Paths are set in `src/config.py`. It stops with an error if the load or join checks fail.
5. `python sanity_check_join.py rentals.db` runs the extra checks on the joined table.
6. `workflows/deliv_5_analysis.ipynb` and the smaller analysis notebooks produce the results. The exploratory notebooks (histogram, top 10% reviews, days since review) read `data/AirBnB_all_chch.csv`, which is written by `workflows/AirBnB Chch base workflow.ipynb`.

## Assumptions in the analysis

- Prices are only available for some months: no listing has a price in December, January or February (see [data_cleaning.md](data_cleaning.md)). Quarterly prices are the mean of the months that have a price.
- Tenancy Services median rent is **weekly**, so it is divided by 7 to compare with the Airbnb **nightly** price.
- "Rental properties" in an area means its `active_bonds` count for all dwelling types and all bedroom counts.
- A listing's SA2 comes from its first month in each quarter (see data_cleaning.md).
