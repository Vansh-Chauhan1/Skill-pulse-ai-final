"""
Compact official labour-market data pipeline for SkillPulse AI.

This module normalises the project's existing official PLFS and NCS CSVs
into one compact, long-format indicator table. It deliberately preserves
the meaning, unit, population, period, and coverage of each source instead
of combining incompatible measures into a fabricated "skill gap".

Run from the backend directory:
    python -m services.compact_market_data
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


BACKEND_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BACKEND_DIR / "data" / "raw"
PLFS_DIR = RAW_DIR / "plfs"
NCS_DIR = RAW_DIR / "ncs"
PROCESSED_DIR = BACKEND_DIR / "data" / "processed"

OUTPUT_CSV = PROCESSED_DIR / "compact_market_indicators.csv"
OUTPUT_REPORT = PROCESSED_DIR / "compact_market_data_report.json"

# Canonical schema shared by every input source.
OUTPUT_COLUMNS = [
    "dataset",
    "source",
    "indicator",
    "category_type",
    "category",
    "breakdown",
    "reference_period",
    "frequency",
    "geography",
    "population",
    "status_approach",
    "value",
    "unit",
    "source_document",
    "source_url",
    "interpretation_note",
]


def _read_csv(path: Path, required: Iterable[str]) -> pd.DataFrame:
    """Read one source CSV and check its required fields."""
    if not path.exists():
        raise FileNotFoundError(f"Required source file is missing: {path}")

    df = pd.read_csv(path, encoding="utf-8-sig")

    missing = sorted(set(required) - set(df.columns))
    if missing:
        raise ValueError(
            f"{path.name} is missing required columns: {missing}"
        )

    if df.empty:
        raise ValueError(f"Source file is empty: {path}")

    return df


def _numeric(df: pd.DataFrame, columns: Iterable[str], label: str) -> None:
    """Convert numeric columns and reject null, non-finite, or invalid values."""
    for column in columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

        values = df[column].to_numpy(dtype=float)
        if not np.isfinite(values).all():
            raise ValueError(
                f"{label}: column '{column}' contains missing or non-finite values."
            )


def _append_long_rows(
    rows: list[dict],
    *,
    dataset: str,
    source: str,
    indicator: str,
    category_type: str,
    category: str,
    breakdown: str,
    reference_period: str,
    frequency: str,
    geography: str,
    population: str,
    status_approach: str,
    value: float,
    unit: str,
    source_document: str,
    source_url: str,
    interpretation_note: str,
) -> None:
    """Append a single normalised observation."""
    rows.append(
        {
            "dataset": dataset,
            "source": source,
            "indicator": indicator,
            "category_type": category_type,
            "category": str(category),
            "breakdown": breakdown,
            "reference_period": str(reference_period),
            "frequency": frequency,
            "geography": geography,
            "population": population,
            "status_approach": status_approach,
            "value": float(value),
            "unit": unit,
            "source_document": source_document,
            "source_url": source_url,
            "interpretation_note": interpretation_note,
        }
    )


def _build_monthly_plfs(rows: list[dict]) -> int:
    """Normalise All-India monthly CWS WPR: rural, urban and combined."""
    path = PLFS_DIR / "plfs_monthly_cws_wpr_2025_2026.csv"
    df = _read_csv(
        path,
        [
            "reference_month",
            "age_group",
            "status_approach",
            "rural_person_wpr_pct",
            "urban_person_wpr_pct",
            "rural_urban_person_wpr_pct",
            "source_document",
            "source_url",
        ],
    )

    df["parsed_month"] = pd.to_datetime(
        df["reference_month"], format="%Y-%m", errors="coerce"
    )
    if df["parsed_month"].isna().any():
        raise ValueError("Monthly PLFS data contains invalid YYYY-MM periods.")
    if df["parsed_month"].duplicated().any():
        raise ValueError("Monthly PLFS data contains duplicate months.")

    df = df.sort_values("parsed_month").reset_index(drop=True)

    observed = pd.PeriodIndex(df["parsed_month"], freq="M")
    expected = pd.period_range(observed.min(), observed.max(), freq="M")
    if not observed.equals(expected):
        raise ValueError("Monthly PLFS WPR series has one or more missing months.")

    metric_columns = [
        "rural_person_wpr_pct",
        "urban_person_wpr_pct",
        "rural_urban_person_wpr_pct",
    ]
    _numeric(df, metric_columns, "Monthly PLFS WPR")

    for column in metric_columns:
        if not df[column].between(0, 100).all():
            raise ValueError(f"Monthly PLFS WPR '{column}' must be between 0 and 100.")

    breakdown_map = {
        "rural_person_wpr_pct": "Rural",
        "urban_person_wpr_pct": "Urban",
        "rural_urban_person_wpr_pct": "Rural + Urban",
    }

    start_count = len(rows)
    for _, record in df.iterrows():
        for column, breakdown in breakdown_map.items():
            _append_long_rows(
                rows,
                dataset="plfs_monthly_wpr",
                source="PLFS / MoSPI",
                indicator="worker_population_ratio",
                category_type="geography",
                category="All India",
                breakdown=breakdown,
                reference_period=record["reference_month"],
                frequency="Monthly",
                geography="All India",
                population=str(record["age_group"]),
                status_approach=str(record["status_approach"]),
                value=record[column],
                unit="percent",
                source_document=str(record["source_document"]),
                source_url=str(record["source_url"]),
                interpretation_note=(
                    "Monthly CWS WPR; keep separate from annual usual-status WPR."
                ),
            )

    return len(rows) - start_count


def _build_annual_state_plfs(rows: list[dict]) -> int:
    """Normalise state/UT annual usual-status WPR without mixing it with CWS."""
    path = PLFS_DIR / "plfs_state_wpr_2025.csv"
    df = _read_csv(
        path,
        [
            "state_ut",
            "survey_period",
            "age_group",
            "status_approach",
            "rural_person_wpr_pct",
            "urban_person_wpr_pct",
            "rural_urban_person_wpr_pct",
            "source_page",
            "source_url",
        ],
    )

    if df["state_ut"].astype(str).duplicated().any():
        raise ValueError("Annual PLFS state WPR file contains duplicate regions.")

    metric_columns = [
        "rural_person_wpr_pct",
        "urban_person_wpr_pct",
        "rural_urban_person_wpr_pct",
    ]
    for column in metric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")
        valid = df[column].dropna()
        if not np.isfinite(valid.to_numpy(dtype=float)).all():
            raise ValueError(f"Annual PLFS state WPR '{column}' has non-finite values.")
        if not valid.between(0, 100).all():
            raise ValueError(f"Annual PLFS state WPR '{column}' must be between 0 and 100.")

    breakdown_map = {
        "rural_person_wpr_pct": "Rural",
        "urban_person_wpr_pct": "Urban",
        "rural_urban_person_wpr_pct": "Rural + Urban",
    }

    start_count = len(rows)
    for _, record in df.iterrows():
        for column, breakdown in breakdown_map.items():
            value = record[column]
            if pd.isna(value):
                continue

            _append_long_rows(
                rows,
                dataset="plfs_annual_state_wpr",
                source="PLFS / MoSPI",
                indicator="worker_population_ratio",
                category_type="state_ut",
                category=str(record["state_ut"]),
                breakdown=breakdown,
                reference_period=str(record["survey_period"]),
                frequency="Annual",
                geography=str(record["state_ut"]),
                population=str(record["age_group"]),
                status_approach=str(record["status_approach"]),
                value=value,
                unit="percent",
                source_document="PLFS Annual Report 2025, Appendix A, Table 17.0",
                source_url=str(record["source_url"]),
                interpretation_note=(
                    "Annual usual-status (ps+ss) WPR; not comparable to monthly CWS WPR."
                ),
            )

    if not df["state_ut"].astype(str).str.casefold().eq("all india").any():
        raise ValueError("Annual PLFS state file must contain an All India row.")

    return len(rows) - start_count


def _build_plfs_industry(rows: list[dict]) -> int:
    """Normalise only the combined rural+urban employment-share series."""
    path = PLFS_DIR / "plfs_all_india_industry_distribution_2021_24.csv"
    df = _read_csv(
        path,
        [
            "survey_period",
            "industry_broad_division_nic08",
            "rural_urban_person_pct",
            "indicator",
            "source_statement",
            "source_url",
        ],
    )

    _numeric(df, ["rural_urban_person_pct"], "PLFS industry distribution")
    if not df["rural_urban_person_pct"].between(0, 100).all():
        raise ValueError("PLFS industry employment shares must be between 0 and 100.")

    start_count = len(rows)
    for _, record in df.iterrows():
        _append_long_rows(
            rows,
            dataset="plfs_industry_distribution",
            source="PLFS / MoSPI",
            indicator="employment_distribution_by_industry",
            category_type="industry",
            category=str(record["industry_broad_division_nic08"]),
            breakdown="Rural + Urban",
            reference_period=str(record["survey_period"]),
            frequency="Annual",
            geography="All India",
            population="Workers in usual status (ps+ss)",
            status_approach="Usual status (ps+ss)",
            value=record["rural_urban_person_pct"],
            unit="percent_of_workers",
            source_document=str(record["source_statement"]),
            source_url=str(record["source_url"]),
            interpretation_note=(
                "Share of workers by broad industry division; not vacancy demand."
            ),
        )

    return len(rows) - start_count


def _build_ncs_wide_to_long(
    rows: list[dict],
    *,
    filename: str,
    category_column: str,
    dataset: str,
    indicator: str,
    category_type: str,
    population: str,
    note: str,
) -> int:
    """Convert the two published NCS financial-year columns into long format."""
    path = NCS_DIR / filename
    df = _read_csv(
        path,
        [
            category_column,
            "vacancies_fy2022_23",
            "vacancies_fy2023_24",
            "source_report",
            "source_url",
        ],
    )
    _numeric(
        df,
        ["vacancies_fy2022_23", "vacancies_fy2023_24"],
        f"NCS {dataset}",
    )

    for column in ["vacancies_fy2022_23", "vacancies_fy2023_24"]:
        if (df[column] < 0).any():
            raise ValueError(f"NCS {dataset} contains negative vacancy values.")

    if df[category_column].astype(str).duplicated().any():
        raise ValueError(f"NCS {dataset} contains duplicate categories.")

    period_columns = {
        "vacancies_fy2022_23": "FY 2022-23",
        "vacancies_fy2023_24": "FY 2023-24",
    }

    start_count = len(rows)
    for _, record in df.iterrows():
        for column, period in period_columns.items():
            _append_long_rows(
                rows,
                dataset=dataset,
                source="National Career Service (NCS)",
                indicator=indicator,
                category_type=category_type,
                category=str(record[category_column]),
                breakdown="As published",
                reference_period=period,
                frequency="Financial year",
                geography="India",
                population=population,
                status_approach="NCS platform reporting",
                value=record[column],
                unit="vacancies",
                source_document=str(record["source_report"]),
                source_url=str(record["source_url"]),
                interpretation_note=note,
            )

    return len(rows) - start_count


def _build_ncs_summary(rows: list[dict]) -> int:
    """Normalise the NCS platform summary indicators."""
    path = NCS_DIR / "ncs_summary_statistics_fy2022_23_fy2023_24.csv"
    df = _read_csv(
        path,
        [
            "metric_as_published",
            "value_fy2022_23",
            "value_fy2023_24",
            "source_report",
            "source_url",
        ],
    )

    _numeric(
        df,
        ["value_fy2022_23", "value_fy2023_24"],
        "NCS summary statistics",
    )
    if (df[["value_fy2022_23", "value_fy2023_24"]] < 0).any().any():
        raise ValueError("NCS summary statistics contain negative values.")

    if df["metric_as_published"].astype(str).duplicated().any():
        raise ValueError("NCS summary contains duplicate metrics.")

    period_columns = {
        "value_fy2022_23": "FY 2022-23",
        "value_fy2023_24": "FY 2023-24",
    }

    start_count = len(rows)
    for _, record in df.iterrows():
        metric = str(record["metric_as_published"])
        for column, period in period_columns.items():
            _append_long_rows(
                rows,
                dataset="ncs_platform_summary",
                source="National Career Service (NCS)",
                indicator="ncs_platform_metric",
                category_type="platform_metric",
                category=metric,
                breakdown="As published",
                reference_period=period,
                frequency="Financial year",
                geography="India",
                population="NCS platform activity",
                status_approach="NCS platform reporting",
                value=record[column],
                unit="count",
                source_document=str(record["source_report"]),
                source_url=str(record["source_url"]),
                interpretation_note=(
                    "Platform activity metric; not a census of the Indian labour market."
                ),
            )

    return len(rows) - start_count


def build_compact_market_dataset() -> tuple[pd.DataFrame, dict]:
    """
    Build a compact unified indicator table and a machine-readable quality report.

    The result is unified structurally, not mathematically: each source keeps
    its own indicator, unit, population, time frequency, and coverage.
    """
    rows: list[dict] = []
    dataset_counts = {}

    builders = [
        ("plfs_monthly_wpr", _build_monthly_plfs),
        ("plfs_annual_state_wpr", _build_annual_state_plfs),
        ("plfs_industry_distribution", _build_plfs_industry),
        (
            "ncs_sector_vacancies",
            lambda out: _build_ncs_wide_to_long(
                out,
                filename="ncs_sector_vacancies_fy2022_23_fy2023_24.csv",
                category_column="ncs_sector_as_published",
                dataset="ncs_sector_vacancies",
                indicator="ncs_vacancies_by_sector",
                category_type="sector",
                population="Vacancies mobilised through NCS",
                note=(
                    "NCS platform vacancies by published sector; not total national demand."
                ),
            ),
        ),
        (
            "ncs_qualification_vacancies",
            lambda out: _build_ncs_wide_to_long(
                out,
                filename="ncs_qualification_vacancies_fy2022_23_fy2023_24.csv",
                category_column="qualification_as_published",
                dataset="ncs_qualification_vacancies",
                indicator="ncs_vacancies_by_qualification",
                category_type="qualification",
                population="Vacancies mobilised through NCS",
                note=(
                    "NCS vacancy counts grouped by source qualification categories; "
                    "not occupation-level worker supply."
                ),
            ),
        ),
        ("ncs_platform_summary", _build_ncs_summary),
    ]

    for name, builder in builders:
        before = len(rows)
        builder(rows)
        dataset_counts[name] = len(rows) - before

    result = pd.DataFrame(rows, columns=OUTPUT_COLUMNS)

    if result.empty:
        raise ValueError("The compact market dataset contains no observations.")

    if result[OUTPUT_COLUMNS].isna().any().any():
        # All schema columns are required; blank provenance or values are not accepted.
        null_columns = result.columns[result.isna().any()].tolist()
        raise ValueError(f"Compact dataset contains null required fields: {null_columns}")

    if not np.isfinite(result["value"].to_numpy(dtype=float)).all():
        raise ValueError("Compact dataset contains non-finite numeric values.")

    duplicate_key = [
        "dataset",
        "indicator",
        "category_type",
        "category",
        "breakdown",
        "reference_period",
    ]
    if result.duplicated(duplicate_key).any():
        raise ValueError("Duplicate observations found in compact market dataset.")

    result = result.sort_values(
        ["dataset", "reference_period", "category_type", "category", "breakdown"]
    ).reset_index(drop=True)

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "record_count": int(len(result)),
        "dataset_record_counts": dataset_counts,
        "source_files": [
            "plfs/plfs_monthly_cws_wpr_2025_2026.csv",
            "plfs/plfs_state_wpr_2025.csv",
            "plfs/plfs_all_india_industry_distribution_2021_24.csv",
            "ncs/ncs_sector_vacancies_fy2022_23_fy2023_24.csv",
            "ncs/ncs_qualification_vacancies_fy2022_23_fy2023_24.csv",
            "ncs/ncs_summary_statistics_fy2022_23_fy2023_24.csv",
        ],
        "quality_checks": {
            "all_required_source_columns_present": True,
            "monthly_wpr_has_contiguous_months": True,
            "wpr_percentages_within_0_and_100": True,
            "ncs_counts_non_negative": True,
            "duplicate_observations_absent": True,
            "all_records_have_source_provenance": True,
            "incompatible_units_and_populations_kept_separate": True,
        },
        "methodology": (
            "Long-format consolidation only. PLFS WPR percentages, PLFS worker "
            "industry shares, NCS vacancy counts, and NCS platform activity "
            "remain separate indicators. No PLFS-NCS subtraction or synthetic "
            "skill-gap target is created."
        ),
        "forecasting_readiness": {
            "monthly_plfs_wpr": (
                "Suitable for the existing short-horizon exploratory baseline "
                "forecast only; current history is short."
            ),
            "plfs_industry_distribution": (
                "Three annual points; descriptive trend only, insufficient "
                "for a reliable ML forecast."
            ),
            "ncs_sector_and_qualification_vacancies": (
                "Two annual observations; descriptive comparison only, "
                "insufficient for ML forecasting."
            ),
            "genuine_skill_gap": (
                "Not model-ready until occupation/skill-level labour supply "
                "and demand are available in compatible units and periods."
            ),
        },
    }

    return result, report



def load_compact_market_indicators(
    *,
    dataset: str = "",
    indicator: str = "",
    category_type: str = "",
    category: str = "",
    limit: int = 1000,
) -> pd.DataFrame:
    """Load processed observations with optional exact/substring filters."""
    if not OUTPUT_CSV.exists():
        raise FileNotFoundError(
            f"Processed data not found: {OUTPUT_CSV}. "
            "Run `python -m services.compact_market_data` from backend first."
        )

    if limit < 1 or limit > 5000:
        raise ValueError("limit must be between 1 and 5000.")

    df = pd.read_csv(OUTPUT_CSV, encoding="utf-8-sig")

    filters = {
        "dataset": dataset,
        "indicator": indicator,
        "category_type": category_type,
        "category": category,
    }

    for column, term in filters.items():
        if term:
            df = df[
                df[column].astype(str).str.contains(
                    term, case=False, regex=False, na=False
                )
            ]

    return df.head(limit)


def load_compact_market_data_report() -> dict:
    """Load the JSON quality report generated alongside the compact CSV."""
    if not OUTPUT_REPORT.exists():
        raise FileNotFoundError(
            f"Data quality report not found: {OUTPUT_REPORT}. "
            "Run `python -m services.compact_market_data` from backend first."
        )

    with OUTPUT_REPORT.open("r", encoding="utf-8") as file:
        return json.load(file)

def main() -> None:
    """Build the processed CSV and quality report."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    compact_df, report = build_compact_market_dataset()

    compact_df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    with OUTPUT_REPORT.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)

    print("\n===== SKILLPULSE COMPACT DATA PIPELINE =====")
    print(f"Output CSV: {OUTPUT_CSV}")
    print(f"Quality report: {OUTPUT_REPORT}")
    print(f"Total observations: {report['record_count']}")
    print("\nRecords by dataset:")
    for name, count in report["dataset_record_counts"].items():
        print(f"  {name}: {count}")
    print("\nAll validation checks passed.")
    print(
        "\nReminder: the consolidated table preserves source units and "
        "does not calculate a cross-source skill gap."
    )


if __name__ == "__main__":
    main()
