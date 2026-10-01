# Christchurch-Rentals-Data-2026

# NOTE: this project is currently under development

This project is intended to prepare and analyse data for short-term and long-term rentals in Chrichchurch, New Zealand sourced from AirBnB and Tenancy Services.


**NOTE: currently copy-pasted from generated Design Principles doc; to be updated prior to final release (once the automated pipeline is prepped)**

1. **Collate.** Loop over the lookup table, read each monthly file, keep `neighbourhood_group == "Christchurch City"`, tag with `year_month`, concatenate (`AirBnB Chch base workflow.ipynb`, repeated inline in `Chch_dataset_clean.ipynb`).
2. **Clean and investigate.** Examine missing prices, row completeness, possible duplicate listings and IQR outliers. Decisions are recorded in `data_cleaning.md`; the general rule is *retain unless there is evidence of error*.
3. **Augment with SA2.** For each listing coordinate, query Koordinates in parallel (`ThreadPoolExecutor`, 8 workers) to get the SA2 code (`Koordinates SA lookup.ipynb`).
4. **Prepare tenancy data.** Dissolve the Christchurch City neighbourhood polygons, keep SA2s with more than 50% area coverage, filter the tenancy file to those SA2s (`Tenancy_Services_bond_cleanup.ipynb`).
5. **Load and join.** Create typed SQLite tables, load both datasets, aggregate Airbnb to listing × quarter (mean price, mean minimum nights, max reviews, SA2 from the first month), filter tenancy to `Dwelling Type = ALL` and `Beds = ALL`, and `LEFT JOIN` on SA2 and quarter (`src/sql_prep.py`, `deliv_5_sql.ipynb`).
6. **Analyse and visualise.** Queries and plots over `joined_quarterly` (`deliv_5_analysis.ipynb` and the smaller notebooks).

## Data sources

AirBnB data is available at Inside Airbnb (https://insideairbnb.com/get-the-data/) and includes scraped data relating to AirBnB listings.

Bond lodgement data from Tenancy Services includes summary statistics related to bonds lodged with Tenancy Services per statistical area.
It is available at https://www.tenancy.govt.nz/about-tenancy-services/data-and-statistics/rental-bond-data/

## Inputs

The following should be saved within a subdirectory named 'data' unless mentioned otherwise.

1. AirBnB data as listings-X.csv, one for each scraped timepoint. Replace X with a sequentially increasing number with 0 being the first and newest scrape
2. AirBnB_date_lookup.csv is a lookup table as formatted below as an example:

| name           | year_month |
|----------------|------------|
| listings-0.csv | 2026-6     |
| listings-1.csv | 2026-5     |

3. neighbourhoods.geojson from Inside Airbnb that has geographic data that corresponds to neghbourhoods for the NZ data
4. Stats NZ Statistical Area 2 (2019, generalised) shapefile contained within a subdirectory /statsnz-statistical-area
5. Tenancy Services detailed quarterly bond data (eg, Detailed-Quarterly-Tenancy-Q1-2020-Q3-2026.csv)
6. Koordinates API key in .env located at the project root as `api_key` = KEY

## Outputs/ Data Dictionary

A key output for this project is a SQLite database containing three tables:
1. Christchurch AirBnB data which are augmented with SA2 area codes and aggregates to quarters
2. Tenancy Services data filtered to Christchurch areas
3. A joined table of tables 1 and 2 above

The data dictionary is available below:

| Field                          | Type             | Description                                                                                                                                                                                 |
|--------------------------------|------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| AirBnBs                        |                  |                                                                                                                                                                                             |
| id                             | INTEGER NOT NULL | Airbnb's unique identifier for the listing                                                                                                                                                  |
| name                           | TEXT             | Name of the listing                                                                                                                                                                         |
| host_id                        | REAL             | Airbnb's unique identifier for the host/user                                                                                                                                                |
| host_name                      | TEXT             | Name of the host. Usually just the first name(s)                                                                                                                                            |
| neighbourhood_group            | TEXT             | The neighbourhood group as geocoded using the latitude and longitude   against neighborhoods as defined by open or public digital shapefiles.                                               |
| neighbourhood                  | TEXT             | The neighbourhood as geocoded using the latitude and longitude against   neighborhoods as defined by open or public digital shapefiles.                                                     |
| latitude                       | REAL             | Uses the World Geodetic System (WGS84) projection for latitude and   longitude.                                                                                                             |
| longitude                      | REAL             | Uses the World Geodetic System (WGS84) projection for latitude and   longitude.                                                                                                             |
| room_type                      | TEXT             | All homes are grouped into the   following three room types: Entire place, Private room, Shared room                                                                                        |
| price                          | REAL             | Daily price in local currency.                                                                                                                                                              |
| minimum_nights                 | REAL             | Minimum number of night stay for the listing (calendar rules may be   different)                                                                                                            |
| number_of_reviews              | INTEGER          | The number of reviews the listing has                                                                                                                                                       |
| last_review                    | TEXT             | The date of the last/newest review                                                                                                                                                          |
| reviews_per_month              | REAL             | The average number of reviews per month the listing has over the lifetime   of the listing.                                                                                                 |
| calculated_host_listings_count | REAL             | The number of listings the host has in the current scrape, in the   city/region geography.                                                                                                  |
| availability_365               | INTEGER          | The availability of the listing 365 days in the future as determined by   the calendar. Note a listing may not be available because it has been booked   by a guest or blocked by the host. |
| number_of_reviews_ltm          | INTEGER          | The number of reviews the listing has (in the last 12 months)                                                                                                                               |
| license                        | TEXT             | The licence/permit/registration number                                                                                                                                                      |
| year_month                     | TEXT NOT NULL    | The year and month the data was scraped by Inside AirBnB                                                                                                                                    |
| quarter                        | TEXT NOT NULL    | Aggregates the year_month to quarters                                                                                                                                                       |
| SA22019_V1_00                  | INTEGER          | SA2 area code associated with the lat/long coordinates                                                                                                                                      |
| PRIMARY KEY                    | KEY              | A primary key generated for this DB using id and year_month                                                                                                                                 |
| Tenancy Services Bonds         |                  |                                                                                                                                                                                             |
| timeframe                      | TEXT NOT NULL    | Starting date for each quarter the observation is associated with                                                                                                                           |
| location_id                    | INTEGER NOT NULL | SA2 area code associated with the observation                                                                                                                                               |
| dwelling_type                  | TEXT NOT NULL    | Permissible dwelling types are ALL, Apartment, Boarding House, Flat,   House, Room                                                                                                          |
| number_of_beds                 | TEXT             | Indicates the number of bedrooms for each observation                                                                                                                                       |
| total_bonds                    | INTEGER          | Total amount of newly lodged bonds for each observation                                                                                                                                     |
| active_bonds                   | INTEGER          | Total amount of active bonds for each observation                                                                                                                                           |
| closed_bonds                   | INTEGER          | Total amount of closed lodged bonds for each observation                                                                                                                                    |
| median_rent                    | REAL             | Median rent for each observation                                                                                                                                                            |
| geometric_mean_rent            | REAL             | Geometric mean rent for each observation, defined as sqrt(product of   rents)                                                                                                               |
| upper_quartile_rent            | REAL             | Upper quartile of rents per the geometric mean for each observation                                                                                                                         |
| lower_quartile_rent            | REAL             | Lower quartile of rents per the geometric mean for each observation                                                                                                                         |
| log_std_dev_weekly_rent        | REAL             | log(standard deviation) of the geometric mean rent for each observation                                                                                                                     |

## Decisions and Assumptions

**NOTE: most copy-pasted from data_cleaning.md (albeit touched up + some extra info added), pending final pipeline**

### Missing Price Data:
An initial investigation of price showed that there were no price observations for December, January, or February. As a result, no listing contains price observations for all nine months represented in the dataset. This in an indication of MAR. 

#### Decision: 
Observations with missing price values were retained. If price is later selected as the response variable for modeling, observations without a recorded price need to be removed at that stage. Removing these observations before knowing the oObjective could unnecessarily discard information useful for other analyses. 

### Row Completeness and Missingness:
The completeness of individual observations was assessed by calculating the proportion of missing values within each row. 

At a missingness threshold of 50%, no observations were flagged. Observations only began to be flagged whe the threshold was reduced to 20%.

#### Decision: 
No observations were removed based solely on overall missingness. The investigation did not identify rows that were sufficiently incomplete to justify removal at this stage. 

### Duplicate Investigation
Potential duplicate Airbnb listings were investigated to determine whether listings appearing across different months represented the same underlying property. 

host_id was used during the initial investigation because it provided an integer that would avoid issues that come with comparing text files, such as whitespace and capitalization differences. 

Potential matches were investigated using combinations of:
- host_id
- listing_id
- listing name similarity 
- latitude
- longitude
- month/time period 

An inner join was also used to compare possible matches with existing records. 

The investigation identified hosts associated with multiple listing IDs that had identical coordinates and similar listing names. But, identical coordinates were not considered sufficient evidence that two listing represented the same physical property. Multiple Airbnb units may exist within the same bulding, and the provided latitude and longitude may represent approximate rather than exact propertly location. 

Temporal patterns were also examined to determine whether a new listing ID appeared to replace an older ID. In several cases, potentially matching listing IDs were active during the same months. This provided additional evidence that the listings could represent distinct properties rather than the same property receiving a new ID. 

No duplicate listing sequences were identified that exceed the nine-month period represented by the dataset. 

#### Decision:
Potential matches were not automatically merged. Listings with similar names, the same host, and identical or similar coordinates are retained as separate entities unless there is sufficient evidence to establish that they represent the same property. Ambiguous cases may instead be flagged as potential matches. 

### Outlier Investigation:
Potential outliers in numeric variables were initially identified using the IQR method: 

Variable	Potential Outliers
price	947
minimum_nights	1,076
number_of_reviews	2,373
reviews_per_month	1,063
calculated_host_listings_count	4,928
availability_365	0
number_of_reviews_ltm	1,727

Boxplots and individual values were examine to determine whether the flagged observations appeared to represent data errors or plausible extreme values. The relatively large number of IQR-flagged observations suggests that several Airbnb variables have skewed distribution. Being classified as an outlier does not garuntee that they are erroneous values. 

#### Decision
Observations were retained when there was insufficient evidence that the reported values represented errors. No observations were removed solely because they were flagged by the IQR method. Hence, all outliers were retained in the dataset in order to avoid accidentally removing meaningful data. 

### Quarterly vs monthly data
The AirBnB data are available monthly while the Tenancy Services bond dataset includes quarterly observations

#### Decision
The AirBnB data were aggregated to quarters to match the Tenancy Services dataset

### Comparing median rents to nightly prices
The median rent from the bond dataset is weekly whereas the AirBnB dataset includes nightly prices.

#### Decision
To make a reasonable comparison between the two datasets, the nightly rent was calculated as `rent / 7`

### Discrepancies in SA2 codes between months
As identified by Claude: 37 listings have different SA2s in different months; both quarterly aggregations silently take the first month's value

#### Decision
Given the small number of affected listings (potentially due to incorrect coordinates during scraping), a warning was added to the pipeline if this is detected, but otherwise the current methodology was retained. When listings are aggregated to quarters, the SA2 from the listing's first month in the quarter is used.

### Meaning of "rental properties"
"Rental properties" in an area means its `active_bonds` count for all dwelling types and all bedroom counts.

## How to run the pipeline

See [DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md) for the inputs, outputs and design of the pipeline. Create the environment with `pip install -r requirements.txt`, put the raw downloads in a folder named `data/` at the project root (git-ignored), and run these in order (notebooks from within `workflows/`):

1. `workflows/Chch_dataset_clean.ipynb` collates the monthly files, investigates data quality (decisions in [data_cleaning.md](data_cleaning.md)) and writes `workflows/cleaned_chch_airbnb.csv`.
2. `workflows/Koordinates SA lookup.ipynb` adds the Statistical Area 2 code and writes `workflows/sa_aug_cleaned_chch_airbnb.csv`. It needs a Koordinates API key in a `.env` file at the project root (`api_key = YOUR_KEY`) and is slow, so rerun it sparingly.
3. `workflows/Tenancy_Services_bond_cleanup.ipynb` filters the Tenancy Services data to Christchurch and writes `data/tenancy_services_chch_only.csv`. It needs `data/neighbourhoods.geojson`, the Stats NZ SA2 shapefile in `data/statsnz-statistical-area/`, and the Tenancy Services CSV in `data/`.
4. `python src/sql_prep.py` builds `rentals.db` (tables `airbnb_listing_month`, `tenancy_bond`, `joined_quarterly`). Paths are set in `src/config.py`. It stops with an error if the load or join checks fail.
5. `python sanity_check_join.py rentals.db` runs the extra checks on the joined table.
6. `workflows/deliv_5_analysis.ipynb` and the smaller analysis notebooks produce the results. The exploratory notebooks (histogram, top 10% reviews, days since review) read `data/AirBnB_all_chch.csv`, which is written by `workflows/AirBnB Chch base workflow.ipynb`.
