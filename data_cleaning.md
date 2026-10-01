## Christchurch Airbnb Cleaning Dataset Description:

### Overview:
This document records the major data-cleaning investigations, assumptions, and decisions made during preprocessing of the Christchurch Airbnb dataset. The goal is to maintain a reproducaible record of how potential data-quality issues were identified and handled


### Missing Price Data:
An initial investigation of price showed that there were no price observations for December, January, or February. As a result, no listing contains price observations for all nine months represented in the dataset. This in an indication of MAR. 

#### Decision: 
Observations with missing price values were retained. If price is later selected as the response variable for modeling, observations without a recorded price need to be removed at that stage. Remvoing these observations before knowing the oObjective could unnecessarily discard information useful for other analyses. 

### Row Completeness and Missingness:
The completeness of individaul observations was assesed by calculating the proportion of missing values within each row. 

At a missingness threshold of 50%, no observations were flagged. Observations only began to be flagged when the threshold was reduced to 20% (1,087 rows; none are flagged at 25% or above). The threshold used in the code is the `MISSINGNESS_THRESHOLD` variable in `Chch_dataset_clean.ipynb`, set to 50% to match this document.

#### Decision: 
No observations were remvoed based soley on overal missingness. The investigation did not idenitfy rows that were sufficiently incomplete to justify removal at this stage. 

### Duplicate Investigation
Potential duplicate Airbnb listings were investigated to determine whether listings appearing across different months represented the same underlying property. 

host_id was used during the initial investigation because it provided an integer that would avoid issues that come with comparing text fileds, such as whitespace and captilization differences. 

Potential matches were investigated using combinations of:
- host_id
- listin_id
- listing name similarity 
- latitude
- longitude
- month/time period 

An inner join was also used to compare possible matches with existing records. 

The investigation identified hosts associated with multiple listing IDs that had identical coordinates and similar listing names. But, identical coordinates were not considered sufficient evidence that two listing represented the same physical property. Multiple Airbnb units may exist within the same bulding, and the provided latitude and longitude may represent approximate rather than exact propertly location. 

Temporal patterns were also examined to determine whether a new listing ID appeared to replace an older ID. In several cases, potentially matching listing IDs were active during the same months. This provided additional evidence that the listings could represent distinct properties rather than the same property recieving a new ID. 

No duplicate listing sequences were identified that exceed the nine-month period represented by the dataset. 

#### Decision:
Potential matches were not automatically merged. Listings with similar names, the same host, and identical or similar coordinates are retained as separate entities unless there is sufficient evidence to establish that they represent the same property. Ambiguous cases are not flagged in the dataset: no `possible_duplicate` column exists, and the possible matches are only listed in `Chch_dataset_clean.ipynb` for inspection. 

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

Boxplots and individual values were examine to determine whether the flagged observations appeared to represent data errors or plausible extreme values. The relativley large number of IQR-flagged observations suggests that several Airbnb variables have skewed distribution. Being classified as an outlier does not garuntee that they are erroneous values. 

#### Decision
Observations were retained when there was insuffienct evidence that the reported values represented errors. No observations were removed soleyl because they were flagged by the IQR method. Hence, all outliers were retained in the dataset in order to avoid accidentally removing meaninful data. 


### Spatial Assignment (Statistical Area 2):
Each listing is assigned an SA2 code by querying the Koordinates service with its latitude and longitude (`Koordinates SA lookup.ipynb`). Failed lookups are left as missing (NA) rather than stopping the run, and each unique coordinate pair is queried once.

37 listings have more than one SA2 code across the nine months, because the host moved the listing's map pin (up to three distinct coordinate pairs per listing). Within a single quarter this affects 36 of 10,355 listing-quarters.

#### Decision:
When monthly rows are combined into one row per listing per quarter, the SA2 is taken from the listing's **first month in that quarter**. Listings are not otherwise reconciled, because the number affected is small (0.3% of listing-quarters).
