"""Compact NCS sector-demand trend engine for SkillPulse AI.

This module calculates transparent descriptive trend signals from the two
financial years published in the project's NCS sector-vacancy CSV.

It is deliberately NOT an ML forecast: two annual observations per sector
are insufficient for robust model training or independent validation.

Run from backend/:
    python -m services.sector_demand_engine
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

BACKEND_DIR = Path(__file__).resolve().parents[1]
SOURCE_FILE = (
    BACKEND_DIR
    / "data"
    / "raw"
    / "ncs"
    / "ncs_sector_vacancies_fy2022_23_fy2023_24.csv"
)

REQUIRED_COLUMNS = [
    "ncs_sector_as_published",
    "vacancies_fy2022_23",
    "vacancies_fy2023_24",
]

OUTPUT_COLUMNS = [
    "sector",
    "vacancies_fy2022_23",
    "vacancies_fy2023_24",
    "absolute_change",
    "calculated_change_pct",
    "reported_change_pct",
    "trend_signal",
    "low_base_warning",
    "interpretation",
    "source_report",
    "source_url",
]


def classify_sector_trend(
    previous: float,
    current: float,
    *,
    stable_band_pct: float = 5.0,
    rapid_growth_pct: float = 100.0,
) -> tuple[str, bool, str]:
    """Return a transparent trend label, low-base flag and explanation."""
    if previous < 0 or current < 0:
        raise ValueError("Vacancy counts cannot be negative.")

    if previous == 0:
        if current == 0:
            return (
                "no_reported_vacancies",
                False,
                "No vacancies were reported in either comparison year.",
            )
        return (
            "new_or_zero_baseline",
            True,
            "Current vacancies are positive but the prior-year baseline is zero; percentage growth is undefined.",
        )

    change_pct = ((current - previous) / previous) * 100
    low_base_warning = previous < 10_000 and change_pct >= rapid_growth_pct

    if change_pct >= rapid_growth_pct:
        signal = "rapid_growth"
        interpretation = "NCS-reported vacancies rose by at least 100%; check the small-base effect before interpreting the increase."
    elif change_pct > stable_band_pct:
        signal = "growth"
        interpretation = "NCS-reported vacancies increased by more than the stability band."
    elif change_pct >= -stable_band_pct:
        signal = "stable"
        interpretation = "NCS-reported vacancies stayed within the plus/minus 5% stability band."
    else:
        signal = "decline"
        interpretation = "NCS-reported vacancies decreased by more than the stability band."

    if low_base_warning:
        interpretation += " The prior-year count was below 10,000, so the percentage change is especially sensitive to the base."

    return signal, low_base_warning, interpretation


def calculate_sector_demand_trends(source_df: pd.DataFrame) -> pd.DataFrame:
    """Validate NCS sector data and calculate comparable two-year trend signals."""
    missing = [column for column in REQUIRED_COLUMNS if column not in source_df.columns]
    if missing:
        raise ValueError(f"NCS sector file is missing required columns: {missing}")
    if source_df.empty:
        raise ValueError("NCS sector vacancy file contains no rows.")

    df = source_df.copy()
    df["ncs_sector_as_published"] = (
        df["ncs_sector_as_published"].astype(str).str.strip()
    )

    if df["ncs_sector_as_published"].eq("").any():
        raise ValueError("NCS sector names cannot be blank.")
    if df["ncs_sector_as_published"].duplicated().any():
        raise ValueError("Duplicate NCS sector names found.")

    for column in ["vacancies_fy2022_23", "vacancies_fy2023_24"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
        values = df[column].to_numpy(dtype=float)
        if not np.isfinite(values).all():
            raise ValueError(f"NCS column '{column}' has missing or non-finite values.")
        if (df[column] < 0).any():
            raise ValueError(f"NCS column '{column}' contains negative vacancy counts.")

    if "reported_percent_change" in df.columns:
        reported = pd.to_numeric(df["reported_percent_change"], errors="coerce")
    else:
        reported = pd.Series(np.nan, index=df.index, dtype=float)

    source_report = (
        df["source_report"].fillna("").astype(str)
        if "source_report" in df.columns
        else pd.Series([""] * len(df), index=df.index)
    )
    source_url = (
        df["source_url"].fillna("").astype(str)
        if "source_url" in df.columns
        else pd.Series([""] * len(df), index=df.index)
    )

    records: list[dict] = []
    for idx, row in df.iterrows():
        previous = float(row["vacancies_fy2022_23"])
        current = float(row["vacancies_fy2023_24"])
        absolute_change = current - previous

        if previous == 0:
            calculated_change_pct = np.nan
        else:
            calculated_change_pct = (absolute_change / previous) * 100

        signal, low_base_warning, interpretation = classify_sector_trend(
            previous, current
        )

        records.append(
            {
                "sector": row["ncs_sector_as_published"],
                "vacancies_fy2022_23": int(round(previous)),
                "vacancies_fy2023_24": int(round(current)),
                "absolute_change": int(round(absolute_change)),
                "calculated_change_pct": (
                    round(float(calculated_change_pct), 2)
                    if np.isfinite(calculated_change_pct)
                    else None
                ),
                "reported_change_pct": (
                    round(float(reported.loc[idx]), 2)
                    if pd.notna(reported.loc[idx])
                    else None
                ),
                "trend_signal": signal,
                "low_base_warning": bool(low_base_warning),
                "interpretation": interpretation,
                "source_report": source_report.loc[idx],
                "source_url": source_url.loc[idx],
            }
        )

    result = pd.DataFrame(records, columns=OUTPUT_COLUMNS)
    result = result.sort_values(
        "vacancies_fy2023_24", ascending=False
    ).reset_index(drop=True)
    return result


def load_sector_demand_trends() -> pd.DataFrame:
    """Load the project's published NCS sector file and calculate signals."""
    if not SOURCE_FILE.exists():
        raise FileNotFoundError(f"NCS sector vacancy source file not found: {SOURCE_FILE}")

    source_df = pd.read_csv(SOURCE_FILE, encoding="utf-8-sig")
    return calculate_sector_demand_trends(source_df)


def build_sector_demand_summary(trends: pd.DataFrame | None = None) -> dict:
    """Return simple counts by signal; do not sum categories as national totals."""
    if trends is None:
        trends = load_sector_demand_trends()

    counts = (
        trends["trend_signal"].value_counts().to_dict()
        if not trends.empty
        else {}
    )

    return {
        "source": "National Career Service (NCS)",
        "comparison_period": ["FY 2022-23", "FY 2023-24"],
        "sector_count": int(len(trends)),
        "trend_signal_counts": {str(key): int(value) for key, value in counts.items()},
        "method": "Two-year descriptive comparison with a +/-5% stability band and a 100% rapid-growth threshold.",
        "forecast_ready": False,
        "limitation": (
            "Only two annual observations are available. These signals describe changes in NCS-platform vacancies; "
            "they are not a validated forecast and do not represent total national labour demand."
        ),
    }


def main() -> None:
    trends = load_sector_demand_trends()
    summary = build_sector_demand_summary(trends)
    print("\n===== NCS SECTOR DEMAND TREND ANALYSIS =====")
    print(trends.to_string(index=False))
    print("\n===== SUMMARY =====")
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
