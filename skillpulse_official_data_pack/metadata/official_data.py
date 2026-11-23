from pathlib import Path
import pandas as pd

# This file belongs at backend/services/official_data.py
BACKEND_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BACKEND_DIR / "data" / "raw"

def load_plfs_state_wpr():
    path = RAW_DIR / "plfs" / "plfs_state_wpr_2023_24.csv"
    return pd.read_csv(path)

def load_plfs_industry_distribution():
    path = RAW_DIR / "plfs" / "plfs_all_india_industry_distribution_2021_24.csv"
    return pd.read_csv(path)

def load_ncs_sector_vacancies():
    path = RAW_DIR / "ncs" / "ncs_sector_vacancies_fy2022_23_fy2023_24.csv"
    return pd.read_csv(path)

def load_ncs_qualification_vacancies():
    path = RAW_DIR / "ncs" / "ncs_qualification_vacancies_fy2022_23_fy2023_24.csv"
    return pd.read_csv(path)

def load_ncs_summary():
    path = RAW_DIR / "ncs" / "ncs_summary_statistics_fy2022_23_fy2023_24.csv"
    return pd.read_csv(path)
