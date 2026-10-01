# Design Principles: Christchurch Rentals Pipeline

**AI used to draft this document:** Claude Sonnet 5.5 (Anthropic), via claude.ai. Claude read the public repository (`Arn-Lee/Christchurch-Rentals-Data-2026`, branch `main`, 70 commits) and checked the document's claims against the committed code and data. Items marked **[CHECK]** need the team to confirm the intention.

## 1. Inputs

| Input | Source | Used by |
|---|---|---|
| `listings-0.csv` … `listings-8.csv`: nine monthly Inside Airbnb scrapes for New Zealand, Oct 2025 to Jun 2026 (`listings-0` is the newest) | insideairbnb.com, saved to `data/` (git-ignored) | base workflow / cleaning |
| `AirBnB_date_lookup.csv`: maps each file name to its `year_month` | committed in `workflows/` | collation loop |
| `neighbourhoods.geojson` | Inside Airbnb | tenancy spatial filter |
| Stats NZ Statistical Area 2 (2019, generalised) shapefile | Stats NZ | tenancy spatial filter, choropleth |
| `Detailed-Quarterly-Tenancy-Q1-2020-Q3-2026.csv`: bond lodgement statistics per SA2 | Tenancy Services | tenancy prep, SQL join |
| Koordinates API key (`api_key` in `.env`, git-ignored) and SA2 layer 98970 | Koordinates | SA2 lookup |

## 2. Outputs

| Output | Description |
|---|---|
| `cleaned_chch_airbnb.csv` | Christchurch City listings, all nine months stacked (28,795 rows), with `year_month` and `quarter` added |
| `sa_aug_cleaned_chch_airbnb.csv` | As above plus the SA2 code `SA22019_V1_00` |
| `tenancy_services_chch_only.csv` | Tenancy rows for SA2s that are at least 50% inside Christchurch City |
| `rentals.db` (SQLite) | Tables `airbnb_listing_month`, `tenancy_bond`, and `joined_quarterly` (one row per listing per quarter with the area's median rent; 10,355 rows) |
| Analysis results | Median Airbnb price in Christchurch Central, short- vs long-term price gap by SA2, Airbnb-to-rental ratio choropleth, histograms |

## 3. Main steps

1. **Collate.** Loop over the lookup table, read each monthly file, keep `neighbourhood_group == "Christchurch City"`, tag with `year_month`, concatenate (`AirBnB Chch base workflow.ipynb`, repeated inline in `Chch_dataset_clean.ipynb`).
2. **Clean and investigate.** Examine missing prices, row completeness, possible duplicate listings and IQR outliers. Decisions are recorded in `data_cleaning.md`; the general rule is *retain unless there is evidence of error*.
3. **Augment with SA2.** For each listing coordinate, query Koordinates in parallel (`ThreadPoolExecutor`, 8 workers, each unique coordinate once, failed lookups left as NA) to get the SA2 code (`Koordinates SA lookup.ipynb`).
4. **Prepare tenancy data.** Dissolve the Christchurch City neighbourhood polygons, keep SA2s with more than 50% area coverage, filter the tenancy file to those SA2s (`Tenancy_Services_bond_cleanup.ipynb`).
5. **Load and join.** Create typed SQLite tables, load both datasets, aggregate Airbnb to listing × quarter (mean price, mean minimum nights, max reviews, SA2 from the first month), filter tenancy to `Dwelling Type = ALL` and `Beds = ALL`, and `LEFT JOIN` on SA2 and quarter (`src/sql_prep.py`, with paths from `src/config.py`; it stops with an error if its load or join checks fail; `deliv_5_sql.ipynb` is the notebook version).
6. **Analyse and visualise.** Queries and plots over `joined_quarterly` (`deliv_5_analysis.ipynb` and the smaller notebooks).

## 4. Software strategies

Practices the project **uses**:

- **Version control with pull requests.** Work is merged through PRs (e.g. #19, #21, #22), and data and secrets are excluded via `.gitignore`.
- **Separating config and secrets from code.** The API key lives in `.env` and is loaded with `python-dotenv`. File locations are defined once in `src/config.py` as paths relative to the project root, and collation is driven by a lookup table rather than hard-coded file names.
- **Reproducible environment.** `requirements.txt` pins exact package versions, and the README gives the order in which to run the pipeline.
- **Explicit schemas.** The SQLite tables declare column types and a primary key `(id, year_month)`, so type problems are caught at load time.
- **Sanity checks built into the pipeline.** `sql_prep.py` asserts row counts and column types after each load and that no listing-quarter is lost or duplicated by the join, and stops if any fail. `sanity_check_join.py` adds independent spot checks (below). The notebooks also plot the selected SA2s for visual checking.
- **Small, testable functions.** `sql_prep.py` is split into load, join and check functions and does nothing on import.
- **Documenting decisions and assumptions.** `data_cleaning.md` records what was investigated and why each choice was made, and the README lists the analysis assumptions.

Practices the project **should adopt next**:

- **Don't repeat yourself.** Collation exists in two notebooks, and quarterly aggregation exists twice (pandas in `augmented_quarterly_chch_airbnb.ipynb`, SQL in `sql_prep.py`) with different column sets. Each should live in one function.
- **Automated tests.** Add a `pytest` suite (for example running `sanity_check_join.py` on a small fixture database) so the checks run on every change.

> **[CHECK]** I don't have your lecture notes. If the lectures named specific best practices (for example modularity, defensive programming, testing, or naming conventions), rename the bullets above to match the lecture terms.

### Worked sanity check

`sanity_check_join.py` checks the join step of `sql_prep.py` and fails loudly with an explanation. It verifies:

1. the output has exactly one row per distinct `(id, quarter)` in the source (no rows lost);
2. no `(id, quarter)` is duplicated (no fan-out);
3. one listing's quarterly mean price matches an independent pandas calculation;
4. one `median_rent` matches the raw `tenancy_bond` row;
5. the unmatched share is reported, with a warning above 20%.

When I ran it against a database built by the repo's own SQL, it passed (10,355 rows, 7.2% unmatched). The real Tenancy Services file is not in the repo, so I used a synthetic tenancy file covering the real SA2 codes; run it against your real `rentals.db` for a true result. I also removed the `ALL`/`ALL` filter from the SQL on purpose, and the check failed with *"joined has 19,967 rows, but source has 10,355"*, which is the exact failure the pipeline comments warn about.

## 5. Where the document and the code disagreed

A review of the repository found the mismatches below between the documentation, the code and the committed outputs. Each is listed with how it was resolved. Items marked **Re-run needed** are fixed in the code, but the CSV committed in the repo was produced by the old code and must be regenerated on a machine that has the data.

| # | What the docs/intent said | What the code/data showed | Status |
|---|---|---|---|
| 1 | README: uses `listings.csv` for NZ "from 19 June 2026" | The pipeline reads **nine** monthly files (Oct 2025 to Jun 2026) via the lookup table | **Resolved**: README updated |
| 2 | `airbnb_tenancy_joined.csv` should be the Airbnb × tenancy join | The last cell of `augmented_quarterly_chch_airbnb.ipynb` wrote `df` (the monthly table). The committed file has 28,795 rows × 22 columns and **no rent columns** | **Code fixed. Re-run needed**: re-run the notebook to regenerate the file |
| 3 | `cleaned_chch_airbnb_quarterly.csv` should be quarterly | `Chch_dataset_clean.ipynb` exported `df` (monthly) instead of `df_quarterly` | **Resolved**: now exports `df_quarterly` |
| 4 | The Koordinates notebook reads `cleaned_chch_airbnb.csv`, and downstream data uses `quarter` | `cleaned_chch_airbnb.csv` had **no `quarter` column**; the cleaning notebook only created it after the export, so how `sa_aug_...csv` got it was not reproducible | **Code fixed. Re-run needed**: `quarter` is now added before export; regenerate `cleaned_chch_airbnb.csv` |
| 5 | `data_cleaning.md`: "missingness threshold of 60%", flagging beginning at 20% | The code filtered at `>= 50` but only filled `percent_missing` for rows `>= 60` | **Resolved**: one `MISSINGNESS_THRESHOLD = 50` variable, and `data_cleaning.md` now says 50% as well (the team chose 50%). Result unchanged: no rows are flagged at 50% or above; 1,087 at 20% |
| 6 | `data_cleaning.md`: ambiguous duplicates "may be flagged as potential matches" | No flag column or output exists | **Resolved**: document reworded to say they are not flagged |
| 7 | Notebooks used `../data/` and `../Data/` (different case); `.gitignore` ignores `data/` | `src/sql_prep.py` used absolute `/outputs/...` paths, so it could not run on a teammate's machine, and read the tenancy file from a different place than the notebook wrote it | **Resolved**: lowercase `data/` everywhere; paths in `src/config.py` |
| 8 | `deliv_5_sql.ipynb` verified loads (row counts, types, duplicate listing-quarters) | These checks were dropped when the notebook became `sql_prep.py` | **Resolved**: reinstated in `sql_prep.py` (they now compare against the source file, not hard-coded counts) |
| 9 | Koordinates notebook: "check for number of failed attempts" via `isna().sum()` | `koord_query` raised on any failure, so the NA check could never detect one; each coordinate was queried once per month (28,795 calls for 3,957 unique coordinates) | **Resolved**: failed lookups return NA, and each unique coordinate is queried once |
| 10 | Not documented | 37 listings have different SA2s in different months (36 listing-quarters differ within a quarter); the first month's value was silently used | **Documented** in `data_cleaning.md` as a decision (first month in the quarter) |
| 11 | Not documented | The price gap divides weekly median rent by 7 to compare with nightly price, and "rental properties" means `active_bonds` | **Documented** in the README |
| 12 | `.gitignore` lists `.DS_Store`; `test.md` says "delete during refactor week" | `.DS_Store`, Orange `.swp.p` files and `test.md` were still tracked | **Resolved**: removed from git; swap files added to `.gitignore` |
| 13 | Found while fixing: the base workflow notebook told users to name files `listing-X.csv` | The lookup table and code use `listings-X.csv` | **Resolved**: notebook instructions corrected |

**Decisions made by the team:** a 50% missingness threshold (item 5), no duplicate-flag column (item 6), and taking a listing's SA2 from its first month in the quarter (item 10).

Confirmed as correct: the claim in `data_cleaning.md` that there are no price observations for Dec, Jan or Feb (all 9,427 rows for those months have a missing price), and the claim that the SQL join loses and duplicates no rows (checked by `sql_prep.py` and `sanity_check_join.py`).
