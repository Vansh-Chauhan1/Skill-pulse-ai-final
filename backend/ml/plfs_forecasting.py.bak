"""Exploratory monthly PLFS WPR forecasting baselines.

This module compares naive and drift one-step-ahead forecasts using an
expanding-window backtest. It forecasts only the All-India combined
rural+urban WPR series supplied in the project's monthly PLFS CSV.

It is NOT a skill-gap, vacancy, unemployment, or occupational-demand model.

Run from backend/: python -m ml.plfs_forecasting
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

BACKEND_DIR = Path(__file__).resolve().parents[1]
DATA_FILE = (
    BACKEND_DIR
    / "data"
    / "raw"
    / "plfs"
    / "plfs_monthly_cws_wpr_2025_2026.csv"
)
TARGET_COLUMN = "rural_urban_person_wpr_pct"
MIN_TRAIN_SIZE = 8


def load_wpr_series(path: Path = DATA_FILE) -> pd.DataFrame:
    """Read, validate, sort, and return monthly combined WPR observations."""
    if not path.exists():
        raise FileNotFoundError(f"Monthly PLFS WPR file not found: {path}")

    df = pd.read_csv(path, encoding="utf-8-sig")
    required = ["reference_month", "age_group", "status_approach", TARGET_COLUMN]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(f"Monthly PLFS file is missing columns: {missing}")
    if df.empty:
        raise ValueError("Monthly PLFS WPR file contains no observations.")

    df = df.copy()
    df["parsed_month"] = pd.to_datetime(
        df["reference_month"].astype(str),
        format="%Y-%m",
        errors="coerce",
    )
    if df["parsed_month"].isna().any():
        raise ValueError("reference_month must use YYYY-MM format.")

    df[TARGET_COLUMN] = pd.to_numeric(df[TARGET_COLUMN], errors="coerce")
    values = df[TARGET_COLUMN].to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("Monthly WPR contains missing or non-finite values.")
    if ((values < 0) | (values > 100)).any():
        raise ValueError("WPR percentages must be between 0 and 100.")

    df = df.sort_values("parsed_month").reset_index(drop=True)
    if df["parsed_month"].duplicated().any():
        raise ValueError("Monthly WPR file contains duplicate months.")

    periods = pd.PeriodIndex(df["parsed_month"], freq="M")
    expected = pd.period_range(periods.min(), periods.max(), freq="M")
    if not periods.equals(expected):
        raise ValueError("Monthly WPR series contains missing months.")

    if len(df) <= MIN_TRAIN_SIZE:
        raise ValueError(
            f"At least {MIN_TRAIN_SIZE + 1} monthly observations are required; found {len(df)}."
        )

    # This module assumes one national CWS age-15+ series, not a mixed panel.
    ages = set(df["age_group"].dropna().astype(str).str.strip().unique())
    statuses = set(df["status_approach"].dropna().astype(str).str.strip().unique())
    if len(ages) > 1 or len(statuses) > 1:
        raise ValueError("Monthly WPR input mixes age groups or status approaches.")

    return df


def naive_forecast(train: Iterable[float], horizon: int = 1) -> list[float]:
    values = np.asarray(list(train), dtype=float)
    if values.size < 1:
        raise ValueError("Naive forecast requires at least one observation.")
    if horizon < 1:
        raise ValueError("Forecast horizon must be at least 1.")
    return [float(np.clip(values[-1], 0, 100))] * horizon


def drift_forecast(train: Iterable[float], horizon: int = 1) -> list[float]:
    values = np.asarray(list(train), dtype=float)
    if values.size < 2:
        raise ValueError("Drift forecast requires at least two observations.")
    if horizon < 1:
        raise ValueError("Forecast horizon must be at least 1.")
    average_change = (values[-1] - values[0]) / (values.size - 1)
    return [
        float(np.clip(values[-1] + step * average_change, 0, 100))
        for step in range(1, horizon + 1)
    ]


def calculate_metrics(actual: Iterable[float], predicted: Iterable[float]) -> dict:
    actual_values = np.asarray(list(actual), dtype=float)
    predicted_values = np.asarray(list(predicted), dtype=float)
    if actual_values.size == 0 or actual_values.size != predicted_values.size:
        raise ValueError("Actual and predicted arrays must have equal non-zero lengths.")
    if not np.isfinite(actual_values).all() or not np.isfinite(predicted_values).all():
        raise ValueError("Metric inputs must be finite numbers.")

    errors = actual_values - predicted_values
    denominator = np.abs(actual_values) + np.abs(predicted_values)
    smape_terms = np.divide(
        2 * np.abs(errors),
        denominator,
        out=np.zeros_like(errors),
        where=denominator != 0,
    )
    return {
        "mae": round(float(np.mean(np.abs(errors))), 4),
        "rmse": round(float(np.sqrt(np.mean(errors ** 2))), 4),
        "smape_pct": round(float(np.mean(smape_terms) * 100), 4),
    }


def rolling_origin_validation(df: pd.DataFrame) -> dict:
    """Expanding-window, one-month-ahead backtest for naive and drift baselines."""
    values = df[TARGET_COLUMN].to_numpy(dtype=float)
    months = pd.PeriodIndex(df["parsed_month"], freq="M")
    if len(values) <= MIN_TRAIN_SIZE:
        raise ValueError("Not enough monthly observations for rolling validation.")

    actual_values: list[float] = []
    predictions: dict[str, list[float]] = {"naive": [], "drift": []}
    records: list[dict] = []

    for test_index in range(MIN_TRAIN_SIZE, len(values)):
        train = values[:test_index]
        actual = float(values[test_index])
        naive = naive_forecast(train)[0]
        drift = drift_forecast(train)[0]
        actual_values.append(actual)
        predictions["naive"].append(naive)
        predictions["drift"].append(drift)
        records.append({
            "reference_month": str(months[test_index]),
            "actual_wpr_pct": round(actual, 3),
            "naive_prediction_pct": round(naive, 3),
            "drift_prediction_pct": round(drift, 3),
        })

    comparison = []
    for model_name in ("naive", "drift"):
        comparison.append({
            "model": model_name,
            **calculate_metrics(actual_values, predictions[model_name]),
        })

    selected = min(comparison, key=lambda row: (row["mae"], row["rmse"]))
    return {
        "validation_method": "expanding-window rolling-origin; one-month-ahead",
        "initial_training_observations": MIN_TRAIN_SIZE,
        "backtest_observations": len(actual_values),
        "model_comparison": comparison,
        "selected_model": selected["model"],
        "backtest_predictions": records,
    }


def build_plfs_wpr_forecast(horizon: int = 1) -> dict:
    """Build an exploratory 1-3 month forecast after comparing baseline models."""
    if not 1 <= horizon <= 3:
        raise ValueError("Forecast horizon must be between 1 and 3 months.")

    df = load_wpr_series()
    validation = rolling_origin_validation(df)
    values = df[TARGET_COLUMN].to_numpy(dtype=float)
    selected_model = validation["selected_model"]

    if selected_model == "naive":
        forecasts = naive_forecast(values, horizon)
    else:
        forecasts = drift_forecast(values, horizon)

    latest_period = pd.Period(df["parsed_month"].iloc[-1], freq="M")
    forecast_rows = [
        {
            "reference_month": str(latest_period + step),
            "forecast_wpr_pct": round(float(value), 3),
        }
        for step, value in enumerate(forecasts, start=1)
    ]

    history_rows = [
        {
            "reference_month": str(pd.Period(row.parsed_month, freq="M")),
            "actual_wpr_pct": round(float(getattr(row, TARGET_COLUMN)), 3),
        }
        for row in df.itertuples(index=False)
    ]

    return {
        "indicator": "Worker Population Ratio (WPR)",
        "population_scope": (
            "All India, persons aged 15 years and above, Current Weekly Status, "
            "rural and urban combined"
        ),
        "frequency": "Monthly",
        "unit": "Percent",
        "forecast_origin": str(latest_period),
        "observations": int(len(df)),
        "history_start": str(pd.Period(df["parsed_month"].iloc[0], freq="M")),
        "history_end": str(latest_period),
        "selected_model": selected_model,
        "validation": validation,
        "history": history_rows,
        "forecast": forecast_rows,
        "methodology_warning": (
            "Exploratory WPR forecast only. It is not a skill-gap or vacancy forecast. "
            "The short series does not support strong seasonal or long-horizon claims."
        ),
    }


def main() -> None:
    output = build_plfs_wpr_forecast(horizon=3)
    print("Selected baseline:", output["selected_model"])
    print("Validation:", output["validation"]["model_comparison"])
    print("Forecast:", output["forecast"])


if __name__ == "__main__":
    main()
