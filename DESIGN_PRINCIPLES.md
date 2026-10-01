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
| `cleaned_chch_airbnb.csv` | Christchurch City listings, all nine months stacked (28,795 rows), `year_month` added |
| `sa_aug_cleaned_chch_airbnb.csv` | As above plus `quarter` and the SA2 code `SA22019_V1_00` |
| `tenancy_services_chch_only.csv` | Tenancy rows for SA2s that are at least 50% inside Christchurch City |
| `rentals.db` (SQLite) | Tables `airbnb_listing_month`, `tenancy_bond`, and `joined_quarterly` (one row per listing per quarter with the area's median rent; 10,355 rows) |
| Analysis results | Median Airbnb price in Christchurch Central, short- vs long-term price gap by SA2, Airbnb-to-rental ratio choropleth, histograms |

## 3. Main steps

1. **Collate.** Loop over the lookup table, read each monthly file, keep `neighbourhood_group == "Christchurch City"`, tag with `year_month`, concatenate (`AirBnB Chch base workflow.ipynb`, repeated inline in `Chch_dataset_clean.ipynb`).
2. **Clean and investigate.** Examine missing prices, row completeness, possible duplicate listings and IQR outliers. Decisions are recorded in `data_cleaning.md`; the general rule is *retain unless there is evidence of error*.
3. **Augment with SA2.** For each listing coordinate, query Koordinates in parallel (`ThreadPoolExecutor`, 8 workers) to get the SA2 code (`Koordinates SA lookup.ipynb`).
4. **Prepare tenancy data.** Dissolve the Christchurch City neighbourhood polygons, keep SA2s with more than 50% area coverage, filter the tenancy file to those SA2s (`Tenancy_Services_bond_cleanup.ipynb`).
5. **Load and join.** Create typed SQLite tables, load both datasets, aggregate Airbnb to listing × quarter (mean price, mean minimum nights, max reviews, SA2 from the first month), filter tenancy to `Dwelling Type = ALL` and `Beds = ALL`, and `LEFT JOIN` on SA2 and quarter (`src/sql_prep.py`, `deliv_5_sql.ipynb`).
6. **Analyse and visualise.** Queries and plots over `joined_quarterly` (`deliv_5_analysis.ipynb` and the smaller notebooks).

## 4. Software strategies

Practices the project **already uses**:

- **Version control with pull requests.** Work is merged through PRs (e.g. #19, #21, #22), and data and secrets are excluded via `.gitignore`.
- **Separating config and secrets from code.** The API key lives in `.env` and is loaded with `python-dotenv`. File paths and worker count sit in a config cell at the top of each notebook. Collation is driven by a lookup table rather than hard-coded file names.
- **Reproducible environment.** `requirements.txt` pins exact package versions.
- **Explicit schemas.** The SQLite tables declare column types and a primary key `(id, year_month)`, so type problems are caught at load time.
- **Sanity checks inside the pipeline.** Examples: plotting the dissolved Christchurch polygon against the selected SA2s, row-count and type checks after each SQL load, and a duplicate `(id, quarter)` check after the join.
- **Documenting decisions.** `data_cleaning.md` records what was investigated and why each choice was made.

Practices the project **should adopt next** (this is the refactor target):

- **Don't repeat yourself.** Collation exists in two notebooks, and quarterly aggregation exists twice (pandas in `augmented_quarterly_chch_airbnb.ipynb`, SQL in `sql_prep.py`) with different column sets. Each should live in one function.
- **Functions and automated tests.** `sql_prep.py` runs everything at import time, so it can't be tested. Wrap it in functions and run `sanity_check_join.py` (below) as a test.
- **Relative paths from one config.** See discrepancy 7.

> **[CHECK]** I don't have your lecture notes. If the lectures named specific best practices (for example modularity, defensive programming, testing, or naming conventions), rename the bullets above to match the lecture terms.

### Worked sanity check

`sanity_check_join.py` checks the join step of `sql_prep.py` and fails loudly with an explanation. It verifies:

1. the output has exactly one row per distinct `(id, quarter)` in the source (no rows lost);
2. no `(id, quarter)` is duplicated (no fan-out);
3. one listing's quarterly mean price matches an independent pandas calculation;
4. one `median_rent` matches the raw `tenancy_bond` row;
5. the unmatched share is reported, with a warning above 20%.

When I ran it against a database built by the repo's own SQL, it passed (10,355 rows, 7.2% unmatched). The real Tenancy Services file is not in the repo, so I used a synthetic tenancy file covering the real SA2 codes; run it against your real `rentals.db` for a true result. I also removed the `ALL`/`ALL` filter from the SQL on purpose, and the check failed with *"joined has 19,967 rows, but source has 10,355"*, which is the exact failure the pipeline comments warn about.

## 5. Where the document and the code disagree

These are the places where the repo's description, the code, or the committed output don't match. For each, decide whether the code or the document reflects your intention, then fix one.

| # | What the docs/intent say | What the code/data actually shows | Suggested fix |
|---|---|---|---|
| 1 | README: uses `listings.csv` for NZ "from 19 June 2026" | The pipeline reads **nine** monthly files (Oct 2025 to Jun 2026) via the lookup table | Update README |
| 2 | `airbnb_tenancy_joined.csv` should be the Airbnb × tenancy join | The last cell of `augmented_quarterly_chch_airbnb.ipynb` writes `df` (the monthly table), not `airbnb_tenancy_joined`. The committed file has 28,795 rows × 22 columns and **no rent columns** | **Code bug**: export `airbnb_tenancy_joined` |
| 3 | `cleaned_chch_airbnb_quarterly.csv` should be quarterly | `Chch_dataset_clean.ipynb` exports `df` (monthly) instead of `df_quarterly` | **Code bug**: export `df_quarterly` |
| 4 | The Koordinates notebook reads `cleaned_chch_airbnb.csv`, and the downstream data uses `quarter` | `cleaned_chch_airbnb.csv` has **no `quarter` column** (19 columns); in the cleaning notebook `quarter` is only created after that export. `sa_aug_cleaned_chch_airbnb.csv` does have it, so the step that created it is not in the repo | Add `quarter` before export and re-run so the chain reproduces |
| 5 | `data_cleaning.md`: "missingness threshold of 60%", with flagging beginning at 20% | The code filters at `>= 50` but only fills `percent_missing` for rows `>= 60`, and no 20% run is saved | Make the code and text use one threshold, held in a variable |
| 6 | `data_cleaning.md`: ambiguous duplicates "may be flagged as potential matches" | No flag column or output exists | Add a `possible_duplicate` flag or reword to "not flagged" |
| 7 | Notebooks use `../data/` and `../Data/` (different case, which breaks on Linux and macOS case-sensitive setups). `.gitignore` ignores `data/` | `src/sql_prep.py` uses absolute `/outputs/...` paths, so it can't run on any teammate's machine. The notebook writes the tenancy CSV to `../Data/` but the script reads `/outputs/` | One `config.py` with relative paths, and one folder name |
| 8 | `deliv_5_sql.ipynb` verifies loads (row counts 28,795 and 21,828, types, duplicate listing-quarters) | These checks were **dropped** when the notebook became `sql_prep.py` | Reinstate them, or call `sanity_check_join.py` |
| 9 | Koordinates notebook: "check for number of failed attempts" via `isna().sum()` | `koord_query` raises on any HTTP error or empty result, so failures stop the run rather than producing NaN, and the NA check can't detect them. Each coordinate is also queried once per month (about 28.8k calls for about 4.0k unique coordinates) | Catch errors and return NaN, and de-duplicate coordinates before querying |
| 10 | Not documented | 37 listings have different SA2s in different months; both quarterly aggregations silently take the first month's value | **[CHECK]** Document this assumption or choose a rule |
| 11 | Not documented | The price gap divides weekly median rent by 7 to compare with nightly price, and "rental properties" means `active_bonds` | Document these assumptions in the README |
| 12 | `.gitignore` lists `.DS_Store`; `test.md` says "delete during refactor week" | `.DS_Store`, `.swp.p` files and `test.md` are still tracked | `git rm` them |

Confirmed as correct: the claim in `data_cleaning.md` that there are no price observations for Dec, Jan or Feb (all 9,427 rows for those months have a missing price), and the claim that the SQL join loses and duplicates no rows (checked by `sanity_check_join.py`).
