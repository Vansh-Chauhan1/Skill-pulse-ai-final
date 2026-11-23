"""Integrated labour-market intelligence response for SkillPulse AI.

This combines existing official PLFS and NCS analytical outputs in one
backend response. It deliberately does not calculate a cross-source skill
gap because current PLFS and NCS tables have incompatible measures.
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from services.official_data import (
    load_ncs_qualification_vacancies,
    load_ncs_summary,
    load_plfs_industry_distribution,
    load_plfs_monthly_cws_wpr,
    load_plfs_state_wpr,
)
from services.sector_demand_engine import (
    build_sector_demand_summary,
    load_sector_demand_trends,
)


def _number(value: Any) -> float | None:
    parsed = pd.to_numeric(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return float(parsed)


def _find_all_india(df: pd.DataFrame) -> pd.Series | None:
    if "state_ut" not in df.columns:
        return None
    mask = (
        df["state_ut"].astype(str).str.strip().str.casefold()
        .isin({"all india", "india", "all india total"})
    )
    if not mask.any():
        return None
    return df.loc[mask].iloc[0]


def _build_monthly_wpr_summary(df: pd.DataFrame) -> dict:
    required = ["reference_month", "rural_urban_person_wpr_pct"]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(f"Monthly PLFS data is missing columns: {missing}")

    work = df.copy()
    work["month"] = pd.to_datetime(work["reference_month"], format="%Y-%m", errors="coerce")
    work["wpr"] = pd.to_numeric(work["rural_urban_person_wpr_pct"], errors="coerce")
    work = work.dropna(subset=["month", "wpr"]).sort_values("month")
    if work.empty:
        raise ValueError("Monthly PLFS WPR has no valid observations.")

    latest = work.iloc[-1]
    previous = work.iloc[-2] if len(work) >= 2 else None
    change = None if previous is None else float(latest["wpr"] - previous["wpr"])

    return {
        "latest_month": latest["month"].strftime("%Y-%m"),
        "latest_wpr_pct": round(float(latest["wpr"]), 2),
        "previous_month": None if previous is None else previous["month"].strftime("%Y-%m"),
        "month_on_month_change_percentage_points": None if change is None else round(change, 2),
        "observation_count": int(len(work)),
        "population_scope": str(latest.get("age_group", "As published")),
        "status_approach": str(latest.get("status_approach", "As published")),
    }


def _build_industry_changes(df: pd.DataFrame) -> list[dict]:
    required = ["survey_period", "industry_broad_division_nic08", "rural_urban_person_pct"]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(f"PLFS industry data is missing columns: {missing}")

    work = df[required].copy()
    work["value"] = pd.to_numeric(work["rural_urban_person_pct"], errors="coerce")
    if work["value"].isna().any():
        raise ValueError("PLFS industry distribution contains missing values.")

    periods = sorted(work["survey_period"].astype(str).unique())
    if len(periods) < 2:
        return []
    previous_period, latest_period = periods[-2], periods[-1]

    previous = work[work["survey_period"].astype(str) == previous_period].set_index(
        "industry_broad_division_nic08"
    )["value"]
    latest = work[work["survey_period"].astype(str) == latest_period].set_index(
        "industry_broad_division_nic08"
    )["value"]

    records: list[dict] = []
    for industry in sorted(set(previous.index).intersection(latest.index)):
        old = float(previous.loc[industry])
        new = float(latest.loc[industry])
        records.append({
            "industry": str(industry),
            "previous_period": previous_period,
            "latest_period": latest_period,
            "previous_employment_share_pct": round(old, 2),
            "latest_employment_share_pct": round(new, 2),
            "change_percentage_points": round(new - old, 2),
            "interpretation": "Change in share of workers, not change in vacancies or absolute worker count.",
        })

    return sorted(records, key=lambda row: row["change_percentage_points"], reverse=True)


def _build_qualification_demand(df: pd.DataFrame) -> list[dict]:
    required = [
        "qualification_as_published",
        "vacancies_fy2022_23",
        "vacancies_fy2023_24",
    ]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(f"NCS qualification data is missing columns: {missing}")

    work = df.copy()
    for column in ("vacancies_fy2022_23", "vacancies_fy2023_24"):
        work[column] = pd.to_numeric(work[column], errors="coerce")
        if work[column].isna().any() or (work[column] < 0).any():
            raise ValueError(f"Invalid counts in NCS column {column}.")

    records: list[dict] = []
    for _, row in work.iterrows():
        old = float(row["vacancies_fy2022_23"])
        new = float(row["vacancies_fy2023_24"])
        change_pct = None if old == 0 else ((new - old) / old) * 100
        records.append({
            "qualification": str(row["qualification_as_published"]),
            "vacancies_fy2022_23": int(old),
            "vacancies_fy2023_24": int(new),
            "absolute_change": int(new - old),
            "calculated_change_pct": None if change_pct is None else round(change_pct, 2),
            "source_scope": "Vacancies mobilised through NCS; not all vacancies in India.",
        })

    return sorted(records, key=lambda row: row["vacancies_fy2023_24"], reverse=True)


def build_market_intelligence_overview(horizon: int = 1) -> dict:
    """Build the integrated current-market intelligence summary.

    The WPR forecast is optional. If the separate forecasting file is not
    installed or its input data is unavailable, the other analytics remain
    usable and a forecast status explains why it was omitted.
    """
    if not 1 <= horizon <= 3:
        raise ValueError("Forecast horizon must be between 1 and 3 months.")

    state_df = load_plfs_state_wpr()
    monthly_df = load_plfs_monthly_cws_wpr()
    industry_df = load_plfs_industry_distribution()
    ncs_summary_df = load_ncs_summary()
    qualification_df = load_ncs_qualification_vacancies()
    sector_df = load_sector_demand_trends()

    all_india = _find_all_india(state_df)
    annual_wpr = None
    if all_india is not None:
        annual_wpr = {
            "survey_period": str(all_india.get("survey_period", "")),
            "age_group": str(all_india.get("age_group", "")),
            "status_approach": str(all_india.get("status_approach", "")),
            "combined_wpr_pct": _number(all_india.get("rural_urban_person_wpr_pct")),
            "rural_wpr_pct": _number(all_india.get("rural_person_wpr_pct")),
            "urban_wpr_pct": _number(all_india.get("urban_person_wpr_pct")),
            "interpretation": "Annual usual-status WPR; do not compare directly with monthly CWS WPR.",
        }

    ncs_summary = []
    for _, row in ncs_summary_df.iterrows():
        ncs_summary.append({
            "metric": str(row["metric_as_published"]),
            "fy2022_23": _number(row["value_fy2022_23"]),
            "fy2023_24": _number(row["value_fy2023_24"]),
            "reported_change_pct": _number(row.get("reported_percent_change")),
            "scope": "NCS platform activity; not a census of India's labour market.",
        })

    forecast_status: dict
    try:
        from ml.plfs_forecasting import build_plfs_wpr_forecast
        forecast = build_plfs_wpr_forecast(horizon=horizon)
        forecast_status = {"available": True, "result": forecast}
    except (ImportError, FileNotFoundError, ValueError) as error:
        forecast_status = {"available": False, "reason": str(error)}

    return {
        "project": "SkillPulse AI",
        "generated_for": "Exploratory labour-market intelligence",
        "employment_indicators": {
            "annual_all_india_wpr": annual_wpr,
            "latest_monthly_wpr": _build_monthly_wpr_summary(monthly_df),
            "industry_share_changes": _build_industry_changes(industry_df),
        },
        "ncs_demand_indicators": {
            "sector_trends": sector_df.to_dict(orient="records"),
            "sector_trend_summary": build_sector_demand_summary(sector_df),
            "qualification_vacancies": _build_qualification_demand(qualification_df),
            "platform_summary": ncs_summary,
        },
        "wpr_forecast": forecast_status,
        "limitations": [
            "PLFS WPR is an employment indicator, not a direct measure of vacancies or skill shortage.",
            "PLFS industry shares and NCS vacancy counts have different units, populations, and coverage; they are not subtracted.",
            "NCS sector and qualification files currently contain only FY 2022-23 and FY 2023-24; trend labels are descriptive, not ML forecasts.",
            "A genuine skill-gap model requires supply and demand observations aligned to the same occupation or skill categories, geography, period, and unit.",
        ],
    }
