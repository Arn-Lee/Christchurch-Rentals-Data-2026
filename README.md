# Christchurch-Rentals-Data-2026

# NOTE: this project is currently under development

This project is intended to prepare and analyse data for short-term and long-term rentals in Chrichchurch, New Zealand sourced from AirBnB and Tenancy Services.

AirBnB data is provided by Inside Airbnb (https://insideairbnb.com/get-the-data/). This project uses the listings.csv data for New Zealand from 19 June 2026.
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