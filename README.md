# Christchurch-Rentals-Data-2026

This project was prepared as a part of the Data Wrangling course at the University of Canterbury. It is intended to prepare and briefly analyse data for short-term (AirBnBs) and long-term (bonds lodged with Tenancy Services) rentals in Chrichchurch, New Zealand sourced from Inside AirBnB and Tenancy Services.

The pipeline will prepare a SQLite database that brings together AirBnB and Tenancy Services bond data, such as those relating to price and volume per Statistical Area.
Additionally, an automated report will present some aspects of the dataset (eg, a choropleth map of AirBnB hotspots)

In brief, the pipeline will prepare the data by:
1. Assigning months and years to the AirBnB data (as specified by a lookup table), filtering for observations in Christchurch City only and bring them into a single dataset instead of separate csv files
2. As the AirBnB data include latitude and longitude for each observation, these coordinates are queried via the Koordinates API to return the corresponding Statistical Area 2 (SA2) code for joining the Tenancy Services bond dataset later
3. The Tenancy Services bond dataset is filtered specifically to areas in Christchurch City (and corresponds to the areas used for the AirBnB dataset) via spatial operations
4. The AirBnB data are aggregated to quarters (instead of monthly) to match the quarterly Tenancy Services bond data
5. The two datasets are joined (via left join of the AirBnB dataset with the Tenancy Services data). This means the date range of the AirBnB dataset decides the date range of the output database!
6. SQL queries are used to generate an automated report

## Data sources

AirBnB data is available at Inside Airbnb (https://insideairbnb.com/get-the-data/) and includes scraped data relating to AirBnB listings.

Bond lodgement data from Tenancy Services includes summary statistics related to bonds lodged with Tenancy Services per SA2 statistical area.
It is available at https://www.tenancy.govt.nz/about-tenancy-services/data-and-statistics/rental-bond-data/

## Running the pipeline

You will need Python 3 (3.12.3 or later) installed to run this pipeline. Additionally, you'll need a Koordinates API key.
Visit https://koordinates.com/ to register and obtain a key.

**NOTE:** For Windows users, please ensure that Python is correctly added to PATH and Git Bash is strongly recommended.

To run the pipeline, first, prepare all input files as indicated in the section below.
After the files are ready, run the makefile located in the project root (via `make all` in the terminal).
For Windows users, Git Bash is recommended instead of Powershell.
All outputs (SQLite DB, reports etc.) will be prepared within `/outputs`.

**NOTE:** As stated above, the date range of the AirBnB dataset will determine the date range of the resulting database!

## Inputs

The following should be saved within a directory named `/data` on the project root unless mentioned otherwise.

1. AirBnB data for New Zealand as `listings-X.csv`, one for each scraped timepoint. Replace X with a sequentially increasing number with 0 being the first and newest scrape
2. `AirBnB_date_lookup.csv` is a lookup table that needs to be prepared as formatted below as an example:

| name           | year_month |
|----------------|------------|
| listings-0.csv | 2026-6     |
| listings-1.csv | 2026-5     |

3. `neighbourhoods.geojson` for New Zealand from Inside Airbnb that has geographic data that corresponds to neghbourhoods for the NZ data
4. Stats NZ Statistical Area 2 (2019, generalised) shapefile contained within a subdirectory `data/statsnz-statistical-area`. This can be downloaded from Koordinates
**NOTE: Do not forget to include all components of the shapefile! (ie, not just the shp)**
5. Tenancy Services detailed quarterly bond data (eg, `Detailed-Quarterly-Tenancy-Q1-2020-Q3-2026.csv`)
6. Koordinates API key in .env located at the project root as `api_key` = KEY

## Outputs/ Data Dictionary

A key output for this project is a SQLite database containing three tables:
1. Christchurch AirBnB data which are augmented with SA2 area codes and aggregates to quarters
2. Tenancy Services data filtered to Christchurch areas
3. A joined table of tables 1 and 2 above

An automated report will present some basic analyses (eg, presenting potential AirBnB hotspots).
Some basic information regarding the dataset (eg, price distribution) is also present in `/outputs` as loose files.

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
