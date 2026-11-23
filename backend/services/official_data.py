"""Validated loaders for the official PLFS and NCS CSV files."""
from __future__ import annotations

from pathlib import Path
import pandas as pd

BACKEND_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BACKEND_DIR / "data" / "raw"
PLFS_DIR = RAW_DIR / "plfs"
NCS_DIR = RAW_DIR / "ncs"


def _read_csv(path: Path, required: list[str]) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required source data file not found: {path}")
    df = pd.read_csv(path, encoding="utf-8-sig")
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(f"{path.name} is missing required columns: {missing}")
    if df.empty:
        raise ValueError(f"Source data file is empty: {path}")
    return df


def _validate_nonnegative(df: pd.DataFrame, columns: list[str], label: str) -> pd.DataFrame:
    result = df.copy()
    for column in columns:
        result[column] = pd.to_numeric(result[column], errors="coerce")
        if result[column].isna().any() or (result[column] < 0).any():
            raise ValueError(f"{label}: invalid values in '{column}'.")
    return result


def load_plfs_state_wpr() -> pd.DataFrame:
    required = [
        "state_ut", "survey_period", "age_group", "status_approach",
        "rural_person_wpr_pct", "urban_person_wpr_pct",
        "rural_urban_person_wpr_pct",
    ]
    df = _read_csv(PLFS_DIR / "plfs_state_wpr_2025.csv", required)
    if df["state_ut"].astype(str).str.strip().duplicated().any():
        raise ValueError("PLFS state WPR file contains duplicate state/UT names.")
    for column in required[-3:]:
        values = pd.to_numeric(df[column], errors="coerce").dropna()
        if not values.between(0, 100).all():
            raise ValueError(f"PLFS state WPR '{column}' must be between 0 and 100.")
    return df


def load_plfs_state_wpr_2023_24() -> pd.DataFrame:
    return _read_csv(
        PLFS_DIR / "plfs_state_wpr_2023_24.csv",
        ["state_ut"],
    )


def load_plfs_industry_distribution() -> pd.DataFrame:
    required = [
        "survey_period", "industry_broad_division_nic08",
        "rural_urban_person_pct", "source_url",
    ]
    df = _read_csv(PLFS_DIR / "plfs_all_india_industry_distribution_2021_24.csv", required)
    df = _validate_nonnegative(df, ["rural_urban_person_pct"], "PLFS industry distribution")
    if not df["rural_urban_person_pct"].between(0, 100).all():
        raise ValueError("PLFS industry employment shares must be between 0 and 100.")
    return df


def load_plfs_monthly_cws_wpr() -> pd.DataFrame:
    required = [
        "reference_month", "age_group", "status_approach",
        "rural_person_wpr_pct", "urban_person_wpr_pct",
        "rural_urban_person_wpr_pct", "source_document", "source_url",
    ]
    df = _read_csv(PLFS_DIR / "plfs_monthly_cws_wpr_2025_2026.csv", required)
    df = df.copy()
    df["parsed_month"] = pd.to_datetime(
        df["reference_month"].astype(str), format="%Y-%m", errors="coerce"
    )
    if df["parsed_month"].isna().any():
        raise ValueError("Monthly PLFS reference_month must use YYYY-MM.")
    if df["parsed_month"].duplicated().any():
        raise ValueError("Monthly PLFS data contains duplicate months.")
    for column in ["rural_person_wpr_pct", "urban_person_wpr_pct", "rural_urban_person_wpr_pct"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
        if df[column].isna().any() or not df[column].between(0, 100).all():
            raise ValueError(f"Monthly PLFS '{column}' must be numeric percentages from 0 to 100.")
    df = df.sort_values("parsed_month").reset_index(drop=True)
    periods = pd.PeriodIndex(df["parsed_month"], freq="M")
    expected = pd.period_range(periods.min(), periods.max(), freq="M")
    if not periods.equals(expected):
        raise ValueError("Monthly PLFS CWS WPR has missing months.")
    return df.drop(columns=["parsed_month"])


def load_ncs_sector_vacancies() -> pd.DataFrame:
    required = [
        "ncs_sector_as_published", "vacancies_fy2022_23",
        "vacancies_fy2023_24", "source_report", "source_url",
    ]
    df = _read_csv(NCS_DIR / "ncs_sector_vacancies_fy2022_23_fy2023_24.csv", required)
    return _validate_nonnegative(df, ["vacancies_fy2022_23", "vacancies_fy2023_24"], "NCS sector vacancies")


def load_ncs_qualification_vacancies() -> pd.DataFrame:
    required = [
        "qualification_as_published", "vacancies_fy2022_23",
        "vacancies_fy2023_24", "source_report", "source_url",
    ]
    df = _read_csv(NCS_DIR / "ncs_qualification_vacancies_fy2022_23_fy2023_24.csv", required)
    return _validate_nonnegative(df, ["vacancies_fy2022_23", "vacancies_fy2023_24"], "NCS qualification vacancies")


def load_ncs_summary() -> pd.DataFrame:
    required = [
        "metric_as_published", "value_fy2022_23",
        "value_fy2023_24", "source_report", "source_url",
    ]
    df = _read_csv(NCS_DIR / "ncs_summary_statistics_fy2022_23_fy2023_24.csv", required)
    return _validate_nonnegative(df, ["value_fy2022_23", "value_fy2023_24"], "NCS summary")
