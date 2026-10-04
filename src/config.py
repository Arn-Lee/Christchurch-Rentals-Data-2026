"""Central place for file locations, so every script uses the same relative paths.

All paths are relative to the project root (the folder containing this repo's
README), so the pipeline runs on any machine without editing paths.
Folder convention: RAW data lives in /data, PREPARED data lives in /outputs
Workflow folder is being depreciated
"""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

AIRBNB_CSV = OUTPUTS_DIR / "sa_aug_cleaned_chch_airbnb.csv"
TENANCY_CSV = OUTPUTS_DIR / "tenancy_services_chch_only.csv"
DB_PATH = OUTPUTS_DIR / "rentals.db"   # git-ignored
