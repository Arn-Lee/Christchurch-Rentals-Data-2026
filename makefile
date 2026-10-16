# Runs the whole Christchurch rentals pipeline
#   make        builds anything that is missing or out of date
#   make clean  deletes all outputs, so the next make reruns every step
# Each rule reads as  output: inputs  followed by the command that builds the output.
# Make only reruns a step when one of its inputs is newer than its output.

# setting up the virtual env
.venv:
	python -m venv .venv
	.venv/Scripts/pip install -r requirements.txt

PYTHON = .venv/Scripts/python.exe
OUT = outputs
# Every script reads config.yaml, so changing a setting reruns the steps after it
CONFIG = config.yaml

# Marian's scripts
AIRBNB_IMPORT = src/airbnb_import.py
KOORD_LOOKUP  = src/koordinates_lookup.py

LOOKUP   = data/AirBnB_date_lookup.csv
LISTINGS = $(wildcard data/listings-*.csv)

.PHONY: all clean

all: $(OUT)/sql_query_notebook_generated.html $(OUT)/airbnb_tenancy_joined.csv $(OUT)/leland_reports.done

# Creates the outputs folder if it doesn't exist yet (used after the | below)
$(OUT):
	mkdir -p $(OUT)

# 1. Tenancy Services bonds, filtered to Christchurch SA2s (Arnold)
$(OUT)/tenancy_services_chch_only.csv: src/bond_import.py $(CONFIG) | $(OUT)
	$(PYTHON) src/bond_import.py

# 2. All monthly listings files combined, Christchurch only (Marian)
$(OUT)/AirBnB_all_chch.csv: $(AIRBNB_IMPORT) $(CONFIG) $(LOOKUP) $(LISTINGS) | $(OUT)
	$(PYTHON) $(AIRBNB_IMPORT)

# 3. Checks, dates and quarter column (Ollie)
$(OUT)/cleaned_chch_airbnb.csv: src/airbnb_clean.py $(CONFIG) $(OUT)/AirBnB_all_chch.csv
	$(PYTHON) src/airbnb_clean.py

# 4. SA2 code for each listing from the Koordinates API (Marian)
$(OUT)/sa_aug_cleaned_chch_airbnb.csv: $(KOORD_LOOKUP) $(CONFIG) $(OUT)/cleaned_chch_airbnb.csv
	$(PYTHON) $(KOORD_LOOKUP)

# 5. One row per listing per quarter, joined to tenancy data (Ollie)
$(OUT)/airbnb_tenancy_joined.csv: src/airbnb_quarterly.py $(CONFIG) $(OUT)/sa_aug_cleaned_chch_airbnb.csv $(OUT)/tenancy_services_chch_only.csv
	$(PYTHON) src/airbnb_quarterly.py

# 6. SQLite database (Arnold)
$(OUT)/rentals.db: src/sql_prep.py $(CONFIG) $(OUT)/sa_aug_cleaned_chch_airbnb.csv $(OUT)/tenancy_services_chch_only.csv
	$(PYTHON) src/sql_prep.py

# 7. Deliverable 5 report (Arnold)
$(OUT)/sql_query_notebook_generated.html: src/sql_query.py $(CONFIG) src/sql_query_notebook_template.ipynb $(OUT)/rentals.db
	$(PYTHON) src/sql_query.py

# 8. Leland's reports go here once they are scripts, and get added to "all" above
$(OUT)/leland_reports.done: src/leland_reports.py $(CONFIG) $(OUT)/AirBnB_all_chch.csv
	$(PYTHON) src/leland_reports.py

clean:
	rm -rf $(OUT)
