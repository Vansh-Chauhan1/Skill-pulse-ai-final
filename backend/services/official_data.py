from pathlib import Path
import pandas as pd

BACKEND_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BACKEND_DIR / "data" / "raw"


def load_plfs_state_wpr():
    """
    Load the latest state-wise PLFS 2025 WPR data.
    """

    path = RAW_DIR / "plfs" / "plfs_state_wpr_2025.csv"

    if not path.exists():
        raise FileNotFoundError(
            f"PLFS 2025 dataset not found: {path}"
        )

    df = pd.read_csv(path)

    required_columns = [
        "state_ut",
        "survey_period",
        "age_group",
        "rural_person_wpr_pct",
        "urban_person_wpr_pct",
        "rural_urban_person_wpr_pct",
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing PLFS columns: {missing}"
        )

    return df


def load_plfs_state_wpr_2023_24():
    """
    Retain the older PLFS dataset for historical reference.
    """

    path = RAW_DIR / "plfs" / "plfs_state_wpr_2023_24.csv"
    return pd.read_csv(path)


def load_plfs_industry_distribution():

    path = (
        RAW_DIR
        / "plfs"
        / "plfs_all_india_industry_distribution_2021_24.csv"
    )

    return pd.read_csv(path)


def load_ncs_sector_vacancies():

    path = (
        RAW_DIR
        / "ncs"
        / "ncs_sector_vacancies_fy2022_23_fy2023_24.csv"
    )

    return pd.read_csv(path)


def load_ncs_qualification_vacancies():

    path = (
        RAW_DIR
        / "ncs"
        / "ncs_qualification_vacancies_fy2022_23_fy2023_24.csv"
    )

    return pd.read_csv(path)


def load_ncs_summary():

    path = (
        RAW_DIR
        / "ncs"
        / "ncs_summary_statistics_fy2022_23_fy2023_24.csv"
    )

    return pd.read_csv(path)
def load_plfs_monthly_cws_wpr():

    path = (
        RAW_DIR
        / "plfs"
        / "plfs_monthly_cws_wpr_2025_2026.csv"
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Monthly PLFS dataset not found: {path}"
        )

    df = pd.read_csv(path)

    required_columns = [
        "reference_month",
        "age_group",
        "status_approach",
        "rural_person_wpr_pct",
        "urban_person_wpr_pct",
        "rural_urban_person_wpr_pct",
    ]

    missing = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing columns: {missing}"
        )

    # Validate monthly dates
    df["parsed_month"] = pd.to_datetime(
        df["reference_month"],
        format="%Y-%m",
        errors="raise"
    )

    # Prevent duplicate months
    if df["reference_month"].duplicated().any():
        raise ValueError(
            "Duplicate monthly observations found."
        )

    # Validate numeric features
    numeric_columns = [
        "rural_person_wpr_pct",
        "urban_person_wpr_pct",
        "rural_urban_person_wpr_pct",
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(
            df[col],
            errors="raise"
        )

        if not df[col].between(0, 100).all():
            raise ValueError(
                f"Invalid percentage values in {col}"
            )

    df = df.sort_values("parsed_month")

    df = df.drop(columns=["parsed_month"])

    return df