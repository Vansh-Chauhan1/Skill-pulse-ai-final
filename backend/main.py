"""FastAPI application for SkillPulse AI.

Run from the backend directory:
    uvicorn main:app --reload

This file keeps the existing API paths for backward compatibility and adds
routes for the compact official-data pipeline and NCS sector-demand analysis.
"""

from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from ml.predictor import predict_skill_gap
from services.official_data import (
    load_ncs_qualification_vacancies,
    load_ncs_sector_vacancies,
    load_ncs_summary,
    load_plfs_industry_distribution,
    load_plfs_monthly_cws_wpr,
    load_plfs_state_wpr,
)
from services.skill_gap import (
    calculate_skill_gaps,
    identify_shortages,
    identify_surpluses,
    industry_wise_analysis,
    most_demanded_skills,
    state_wise_analysis,
)

# The two modules below must be saved in backend/services/.
from services.compact_market_data import (
    load_compact_market_data_report,
    load_compact_market_indicators,
)
from services.sector_demand_engine import (
    build_sector_demand_summary,
    load_sector_demand_trends,
)
from services.intelligence_engine import build_market_intelligence_overview
from routers.ai import router as ai_router

load_dotenv()


app = FastAPI(
    title="SkillPulse AI",
    description=(
        "Indian employment indicators, NCS platform vacancy analytics, "
        "and exploratory labour-market forecasting."
    ),
    version="1.1.0",
)


# ---------------------------------------------------------------------------
# FRONTEND CONNECTION
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://localhost:5176",
        "http://127.0.0.1:5176",
        *[
            origin.strip().rstrip("/")
            for origin in os.getenv("FRONTEND_ORIGINS", "").split(",")
            if origin.strip()
        ],
    ],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1):517\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ai_router)
# ---------------------------------------------------------------------------
# SHARED RESPONSE HELPERS
# ---------------------------------------------------------------------------


def dataframe_to_records(df) -> list[dict[str, Any]]:
    """Convert a pandas DataFrame to JSON-safe records (NaN becomes null)."""
    return json.loads(df.to_json(orient="records"))


def _raise_data_error(error: Exception) -> None:
    """Translate expected data-pipeline errors into useful HTTP responses."""
    if isinstance(error, FileNotFoundError):
        raise HTTPException(status_code=404, detail=str(error))
    if isinstance(error, ValueError):
        raise HTTPException(status_code=400, detail=str(error))
    raise HTTPException(status_code=500, detail="Unexpected data-processing error.")


# ---------------------------------------------------------------------------
# BASIC / HEALTH ENDPOINTS
# ---------------------------------------------------------------------------


@app.get("/")
def home():
    return {
        "project": "SkillPulse AI",
        "status": "Operational",
        "docs": "/docs",
    }


@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "backend": "connected",
        "project": "SkillPulse AI",
    }


# ---------------------------------------------------------------------------
# LEGACY SKILL-GAP ENDPOINTS
# ---------------------------------------------------------------------------
# NOTE: These endpoints still use backend/data/employment_data.csv, which
# currently contains illustrative sample rows. Keep them for compatibility,
# but do not describe their results as official national skill-gap estimates
# or use this tiny sample file to train an ML model.


@app.get("/api/skill-gaps")
def get_skill_gaps():
    try:
        return dataframe_to_records(calculate_skill_gaps())
    except (FileNotFoundError, ValueError) as error:
        _raise_data_error(error)


@app.get("/api/states")
def get_states():
    try:
        return dataframe_to_records(state_wise_analysis())
    except (FileNotFoundError, ValueError) as error:
        _raise_data_error(error)


@app.get("/api/industries")
def get_industries():
    try:
        return dataframe_to_records(industry_wise_analysis())
    except (FileNotFoundError, ValueError) as error:
        _raise_data_error(error)


@app.get("/api/skills")
def get_skills():
    try:
        result = most_demanded_skills().reset_index()
        result.columns = ["skill", "total_demand"]
        return dataframe_to_records(result)
    except (FileNotFoundError, ValueError) as error:
        _raise_data_error(error)


@app.get("/api/shortages")
def get_shortages():
    try:
        return dataframe_to_records(identify_shortages())
    except (FileNotFoundError, ValueError) as error:
        _raise_data_error(error)


@app.get("/api/surpluses")
def get_surpluses():
    try:
        return dataframe_to_records(identify_surpluses())
    except (FileNotFoundError, ValueError) as error:
        _raise_data_error(error)


@app.get("/api/predict")
def predict(demand: float, available_workers: float):
    try:
        return predict_skill_gap(
            demand=demand,
            available_workers=available_workers,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


# ---------------------------------------------------------------------------
# OFFICIAL PLFS AND NCS DATA ENDPOINTS
# ---------------------------------------------------------------------------


@app.get("/api/official/plfs/state-wpr")
def official_plfs_state_wpr():
    try:
        return dataframe_to_records(load_plfs_state_wpr())
    except (FileNotFoundError, ValueError) as error:
        _raise_data_error(error)


@app.get("/api/official/plfs/industry-distribution")
def official_plfs_industry_distribution():
    try:
        return dataframe_to_records(load_plfs_industry_distribution())
    except (FileNotFoundError, ValueError) as error:
        _raise_data_error(error)


@app.get("/api/official/plfs/monthly-cws-wpr")
def official_plfs_monthly_cws_wpr():
    try:
        return dataframe_to_records(load_plfs_monthly_cws_wpr())
    except (FileNotFoundError, ValueError) as error:
        _raise_data_error(error)


@app.get("/api/official/ncs/sector-vacancies")
def official_ncs_sector_vacancies():
    try:
        return dataframe_to_records(load_ncs_sector_vacancies())
    except (FileNotFoundError, ValueError) as error:
        _raise_data_error(error)


@app.get("/api/official/ncs/qualification-vacancies")
def official_ncs_qualification_vacancies():
    try:
        return dataframe_to_records(load_ncs_qualification_vacancies())
    except (FileNotFoundError, ValueError) as error:
        _raise_data_error(error)


@app.get("/api/official/ncs/summary")
def official_ncs_summary():
    try:
        return dataframe_to_records(load_ncs_summary())
    except (FileNotFoundError, ValueError) as error:
        _raise_data_error(error)


# ---------------------------------------------------------------------------
# MONTHLY PLFS WPR FORECAST ENDPOINT
# ---------------------------------------------------------------------------


@app.get("/api/official/plfs/wpr-forecast")
def official_plfs_wpr_forecast(
    horizon: int = Query(default=1, ge=1, le=3),
):
    """Run the optional baseline forecast module if it is installed locally."""
    try:
        # Lazy import means the rest of the API can still start if the forecast
        # file has not yet been added. The endpoint returns a clear 503 then.
        from ml.plfs_forecasting import build_plfs_wpr_forecast
    except ModuleNotFoundError as error:
        raise HTTPException(
            status_code=503,
            detail=(
                "Forecast module is not installed. Add "
                "backend/ml/plfs_forecasting.py before using this endpoint."
            ),
        ) from error

    try:
        return build_plfs_wpr_forecast(horizon=horizon)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


# ---------------------------------------------------------------------------
# COMPACT UNIFIED MARKET-DATA ENDPOINTS
# ---------------------------------------------------------------------------


@app.get("/api/analytics/market-indicators")
def get_compact_market_indicators(
    dataset: str = "",
    indicator: str = "",
    category_type: str = "",
    category: str = "",
    limit: int = Query(default=1000, ge=1, le=5000),
):
    """Return normalized indicators while preserving source units and scope."""
    try:
        df = load_compact_market_indicators(
            dataset=dataset,
            indicator=indicator,
            category_type=category_type,
            category=category,
            limit=limit,
        )
        return dataframe_to_records(df)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.get("/api/analytics/market-indicators/summary")
def get_compact_market_indicators_summary():
    """Return the data-quality report created by the compact pipeline."""
    try:
        return load_compact_market_data_report()
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))


# ---------------------------------------------------------------------------
# NCS SECTOR DEMAND INTELLIGENCE ENDPOINTS
# ---------------------------------------------------------------------------


@app.get("/api/analytics/sector-demand-trends")
def get_sector_demand_trends(signal: str = ""):
    """Return a two-financial-year descriptive comparison of NCS vacancies."""
    try:
        df = load_sector_demand_trends()
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    if signal:
        allowed_signals = {
            "rapid_growth",
            "growth",
            "stable",
            "decline",
            "new_or_zero_baseline",
            "no_reported_vacancies",
        }
        signal_value = signal.strip().lower()
        if signal_value not in allowed_signals:
            raise HTTPException(
                status_code=400,
                detail=(
                    "signal must be one of: "
                    + ", ".join(sorted(allowed_signals))
                ),
            )
        df = df[df["trend_signal"] == signal_value]

    return dataframe_to_records(df)


@app.get("/api/analytics/sector-demand-trends/summary")
def get_sector_demand_trends_summary():
    """Summarize the descriptive NCS sector trend classifications."""
    try:
        return build_sector_demand_summary()
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


# ---------------------------------------------------------------------------
# INTEGRATED MARKET INTELLIGENCE ENDPOINT
# ---------------------------------------------------------------------------


@app.get("/api/intelligence/overview")
def get_market_intelligence_overview(
    horizon: int = Query(default=1, ge=1, le=3),
):
    """Return one consolidated view of existing PLFS/NCS indicators.

    This endpoint does not create a synthetic skill-gap score. It combines
    descriptive employment and NCS vacancy indicators, plus the optional
    exploratory PLFS WPR forecast.
    """
    try:
        return build_market_intelligence_overview(horizon=horizon)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
