"""Central place for file locations, so every script uses the same relative paths.

All paths are relative to the project root (the folder containing this repo's
README), so the pipeline runs on any machine without editing paths.
Folder convention: raw downloads and prepared tenancy data live in lowercase `data/`
(git-ignored); prepared Airbnb CSVs live in `workflows/`.
"""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
WORKFLOWS_DIR = PROJECT_ROOT / "workflows"

AIRBNB_CSV = WORKFLOWS_DIR / "sa_aug_cleaned_chch_airbnb.csv"
TENANCY_CSV = DATA_DIR / "tenancy_services_chch_only.csv"
DB_PATH = PROJECT_ROOT / "rentals.db"   # git-ignored
