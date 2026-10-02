# Week 9 Coding Practices Review:

**AI used:** Claude Sonnet 5.5 (Anthropic), via claude.ai. The AI read the repository, compared the documentation with the code, wrote the fixes and the sanity check, and drafted the design document. The team made the decisions (see section 4) and applied the changes through a pull request.


## 1. Summary

We reviewed the pipeline against good coding practice and found that the code, the documentation and the committed outputs disagreed in 13 places. Two exports wrote the wrong table, a key column was never created in the notebook that was supposed to make it, the pipeline script only ran on one person's machine, and several documents described behaviour the code did not have. We fixed these in 11 small commits, added automatic checks to the join step, wrote an independent sanity check, and updated the design principles document so it matches the code.

## 2. What we changed and why

| Area | What changed (high level) | Practice | Why |
|---|---|---|---|
| Wrong outputs | Two notebooks exported the monthly table instead of the quarterly/joined table. Both now export the right one. | Output matches intent | `airbnb_tenancy_joined.csv` had no rent columns, so it was not a join at all. |
| Missing column | `quarter` is now created before `cleaned_chch_airbnb.csv` is exported. | Reproducible data lineage | Downstream files used `quarter`, but the code that made it was not in the repo. |
| One threshold | The missingness cut-off is a single variable, `MISSINGNESS_THRESHOLD = 50`, used everywhere. | No magic numbers, one source of truth | The code mixed 50 and 60, and the documentation said 60. |
| API lookup | Each unique coordinate is queried once, and a failed lookup returns NA instead of crashing the run. | DRY, defensive programming | 28,795 API calls became 3,957 (about 86% fewer), and the NA check can now detect failures. |
| Pipeline script | `src/sql_prep.py` was split into functions, reads paths from a new `src/config.py`, and does nothing on import. | Modularity, config separate from code, testability | It used absolute `/outputs/...` paths, so it could not run on a teammate's machine. |
| Built-in checks | `sql_prep.py` now asserts row counts and column types after each load, and that no listing-quarter is lost or duplicated by the join. | Automated checks | These checks existed in a notebook but were dropped when it became a script. |
| Folder names | The notebooks consistently use lowercase `data/`. | Portability, consistent naming | `Data/` and `data/` mixed breaks on case-sensitive systems and the `.gitignore` only covers `data/`. |
| Documentation | README (data files, how to run, assumptions), `data_cleaning.md` (threshold, duplicate handling, SA2 rule), and a new `DESIGN_PRINCIPLES.md`. | Documentation matches code | Several documents described behaviour the code did not have. |
| Housekeeping | Removed `.DS_Store`, Orange swap files and `test.md` from git, and fixed the `listing-X.csv` / `listings-X.csv` naming. | Version control hygiene | Tracked junk files and an inconsistent naming convention. |

## 3. Sanity check example

**Step checked:** the join in `sql_prep.py`, which turns monthly Airbnb rows into one row per listing per quarter and adds the area's median rent. Silent failures here would give plausible-looking but wrong results.

**Script:** `sanity_check_join.py`, run with `python sanity_check_join.py rentals.db`. It checks that:

1. the output has exactly one row per distinct `(id, quarter)` in the source, so no rows are lost;
2. no `(id, quarter)` appears twice, so the join has not duplicated rows;
3. one listing's quarterly mean price matches a separate pandas calculation done by hand;
4. one `median_rent` value matches the raw tenancy table;
5. the share of listing-quarters with no rent is reported, with a warning above 20%.

**Results:**
- It passed on a database built by the pipeline's own SQL: 10,355 rows, no duplicates, spot checks matched, and 7.2% of listing-quarters had no median rent.
- **Negative test.** We deliberately removed the `ALL`/`ALL` filter from the SQL. The check failed with "joined has 19,967 rows, but source has 10,355". This shows the check catches the exact fan-out error the pipeline comments warn about.
- **Limitation.** The real Tenancy Services file is not in the repo, so these runs used a synthetic tenancy file covering the real SA2 codes. It should be run on the real database before you claim a real-data result.

## 4. Documentation versus code

**Process.** The AI compared every claim in the README, `data_cleaning.md` and the notebook text against the code and the committed data, then listed each mismatch. Section 5 of `DESIGN_PRINCIPLES.md` has the full table of 13, each with its resolution. Highlights:

- Wrong dataframe exported (two places), and `quarter` not reproducible: code fixed.
- README described one `listings.csv` from 19 June, but the pipeline reads nine monthly files: README fixed.
- Threshold 50 versus 60: code and docs aligned to 50%.
- Facts confirmed correct: no prices exist for December, January and February (9,427 rows), and the join loses and duplicates nothing.

**Team decisions** (these were choices for the team, not the AI):
- Missingness threshold of **50%**. No rows are flagged at 50% or above. Rows only appear at 20% (1,087 rows).
- **No duplicate-flag column.** Possible duplicates are listed in the notebook for inspection and not flagged in the data.
- A listing's SA2 comes from its **first month in the quarter**. 37 listings change SA2 across months because the host moved the pin, and this affects 36 of 10,355 listing-quarters (0.3%).

## 5. How we did it

1. Gave the AI the public repository and asked it to review the code against good practice.
2. It cloned the repo, read the notebooks, scripts and data, and compared them with the documentation.
3. It wrote the fixes as a series of small patches, each one commit with a clear message.
4. It tested the changes: ran the refactored script from a different directory, ran the sanity check, and tried a deliberately broken join. The Koordinates change was tested with a mocked API.
5. The team chose the open decisions in section 4, applied the patches on a branch (`fixes`), and opened a pull request.
6. We resolved merge conflicts where teammates had changed the same files on `main`.



## 8. Limitations and next steps

- The sanity check and refactored script are tested on synthetic tenancy data only. Run them on the real data.
- Two committed CSVs still hold the old output until regenerated: `cleaned_chch_airbnb.csv` has no `quarter` column, and `airbnb_tenancy_joined.csv` still holds the monthly data.
- Quarterly aggregation still exists twice (pandas in one notebook, SQL in `sql_prep.py`), and the collation step is repeated in two notebooks. Both break the "don't repeat yourself" rule.
- There is no automated test suite yet. Next step: run `sanity_check_join.py` as a `pytest` test.

