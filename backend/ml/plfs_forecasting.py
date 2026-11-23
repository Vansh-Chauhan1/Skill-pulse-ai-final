"""PLFS monthly WPR forecasting with a validated baseline and a dynamic trend scenario.

The module keeps two outputs deliberately separate:
- forecast: the lowest-error model from rolling-origin validation (may be flat).
- trend_forecast: a damped Holt trend projection that can vary by month.

With a short and volatile series, the flat naive baseline can legitimately win.
The trend projection is shown as an alternative scenario and is NOT described as
more accurate when validation says otherwise.

Run from backend/: python -m ml.plfs_forecasting
"""
from __future__ import annotations

from itertools import product
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

BACKEND_DIR = Path(__file__).resolve().parents[1]
DATA_FILE = BACKEND_DIR / "data" / "raw" / "plfs" / "plfs_monthly_cws_wpr_2025_2026.csv"
TARGET_COLUMN = "rural_urban_person_wpr_pct"
MIN_TRAIN_SIZE = 8
HOLT_MIN_INNER_TRAIN = 5


def load_wpr_series(path: Path = DATA_FILE) -> pd.DataFrame:
    """Load and validate one continuous All-India monthly CWS WPR series."""
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
        df["reference_month"].astype(str), format="%Y-%m", errors="coerce"
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
            f"At least {MIN_TRAIN_SIZE + 1} observations are required; found {len(df)}."
        )

    ages = set(df["age_group"].dropna().astype(str).str.strip().unique())
    statuses = set(df["status_approach"].dropna().astype(str).str.strip().unique())
    if len(ages) != 1 or len(statuses) != 1:
        raise ValueError("Monthly WPR input mixes age groups or status approaches.")
    return df


def naive_forecast(train: Iterable[float], horizon: int = 1) -> list[float]:
    values = np.asarray(list(train), dtype=float)
    if values.size < 1 or horizon < 1:
        raise ValueError("Naive forecast requires data and a positive horizon.")
    return [float(np.clip(values[-1], 0, 100))] * horizon


def drift_forecast(train: Iterable[float], horizon: int = 1) -> list[float]:
    values = np.asarray(list(train), dtype=float)
    if values.size < 2 or horizon < 1:
        raise ValueError("Drift forecast requires at least two observations and a positive horizon.")
    slope = (values[-1] - values[0]) / (values.size - 1)
    return [float(np.clip(values[-1] + step * slope, 0, 100)) for step in range(1, horizon + 1)]


def linear_trend_forecast(train: Iterable[float], horizon: int = 1, window: int = 6) -> list[float]:
    """Fit a simple least-squares line to the most recent `window` observations."""
    values = np.asarray(list(train), dtype=float)
    if values.size < 2 or horizon < 1:
        raise ValueError("Linear trend requires at least two observations and a positive horizon.")
    values = values[-min(window, values.size):]
    x = np.arange(values.size, dtype=float)
    slope, intercept = np.polyfit(x, values, deg=1)
    future_x = np.arange(values.size, values.size + horizon, dtype=float)
    return [float(np.clip(value, 0, 100)) for value in intercept + slope * future_x]


def holt_damped_forecast(
    train: Iterable[float], horizon: int = 1,
    alpha: float = 0.6, beta: float = 0.2, phi: float = 0.90,
) -> list[float]:
    """Holt's additive trend with damping; estimates a changing, fading trend."""
    values = np.asarray(list(train), dtype=float)
    if values.size < 2 or horizon < 1:
        raise ValueError("Holt forecasting requires two observations and a positive horizon.")
    if not (0 < alpha <= 1 and 0 <= beta <= 1 and 0 < phi <= 1):
        raise ValueError("Invalid Holt smoothing parameters.")

    level = float(values[0])
    trend = float(values[1] - values[0])
    for observation in values[1:]:
        previous_level = level
        level = alpha * float(observation) + (1 - alpha) * (level + phi * trend)
        trend = beta * (level - previous_level) + (1 - beta) * phi * trend

    forecasts = []
    damped_trend_sum = 0.0
    for step in range(1, horizon + 1):
        damped_trend_sum += phi ** step
        forecasts.append(float(np.clip(level + damped_trend_sum * trend, 0, 100)))
    return forecasts


def tune_holt_parameters(train: Iterable[float]) -> dict[str, float]:
    """Tune Holt parameters using only earlier observations inside the training fold."""
    values = np.asarray(list(train), dtype=float)
    if values.size < HOLT_MIN_INNER_TRAIN + 1:
        return {"alpha": 0.6, "beta": 0.2, "phi": 0.90}

    alpha_grid = (0.3, 0.5, 0.7, 0.9)
    beta_grid = (0.1, 0.2, 0.4)
    phi_grid = (0.85, 0.90, 0.95, 1.0)
    best: tuple[float, float, float, float] | None = None

    for alpha, beta, phi in product(alpha_grid, beta_grid, phi_grid):
        errors = []
        for validation_index in range(HOLT_MIN_INNER_TRAIN, len(values)):
            fit_values = values[:validation_index]
            actual = values[validation_index]
            prediction = holt_damped_forecast(
                fit_values, horizon=1, alpha=alpha, beta=beta, phi=phi
            )[0]
            errors.append((actual - prediction) ** 2)
        score = float(np.mean(errors)) if errors else float("inf")
        candidate = (score, alpha, beta, phi)
        if best is None or candidate < best:
            best = candidate

    assert best is not None
    return {"alpha": best[1], "beta": best[2], "phi": best[3]}


def calculate_metrics(actual: Iterable[float], predicted: Iterable[float]) -> dict[str, float]:
    actual_values = np.asarray(list(actual), dtype=float)
    predicted_values = np.asarray(list(predicted), dtype=float)
    if actual_values.size == 0 or actual_values.size != predicted_values.size:
        raise ValueError("Actual and predicted values must have equal, non-zero lengths.")
    if not np.isfinite(actual_values).all() or not np.isfinite(predicted_values).all():
        raise ValueError("Metric inputs must be finite.")

    errors = actual_values - predicted_values
    denominator = np.abs(actual_values) + np.abs(predicted_values)
    smape_terms = np.divide(
        2 * np.abs(errors), denominator,
        out=np.zeros_like(errors), where=denominator != 0,
    )
    return {
        "mae": round(float(np.mean(np.abs(errors))), 4),
        "rmse": round(float(np.sqrt(np.mean(errors ** 2))), 4),
        "smape_pct": round(float(np.mean(smape_terms) * 100), 4),
    }


def _predict_model(train: np.ndarray, model: str, horizon: int = 1) -> list[float]:
    if model == "naive":
        return naive_forecast(train, horizon)
    if model == "drift":
        return drift_forecast(train, horizon)
    if model == "linear_recent6":
        return linear_trend_forecast(train, horizon, window=6)
    if model == "holt_damped_trend":
        params = tune_holt_parameters(train)
        return holt_damped_forecast(train, horizon, **params)
    raise ValueError(f"Unknown forecasting model: {model}")


def rolling_origin_validation(df: pd.DataFrame) -> dict:
    """Expanding-window one-step-ahead evaluation for all candidate methods."""
    values = df[TARGET_COLUMN].to_numpy(dtype=float)
    months = pd.PeriodIndex(df["parsed_month"], freq="M")
    if len(values) <= MIN_TRAIN_SIZE:
        raise ValueError("Not enough observations for rolling-origin validation.")

    model_names = ["naive", "drift", "linear_recent6", "holt_damped_trend"]
    actuals: list[float] = []
    predictions: dict[str, list[float]] = {name: [] for name in model_names}
    records: list[dict] = []

    for test_index in range(MIN_TRAIN_SIZE, len(values)):
        train = values[:test_index]
        actual = float(values[test_index])
        row = {"reference_month": str(months[test_index]), "actual_wpr_pct": round(actual, 3)}
        actuals.append(actual)
        for model in model_names:
            prediction = _predict_model(train, model, horizon=1)[0]
            predictions[model].append(prediction)
            row[f"{model}_prediction_pct"] = round(prediction, 3)
        records.append(row)

    comparison = [
        {"model": model, **calculate_metrics(actuals, predictions[model])}
        for model in model_names
    ]
    comparison.sort(key=lambda item: (item["mae"], item["rmse"]))
    best_model = comparison[0]["model"]
    return {
        "validation_method": "Expanding-window rolling-origin, one-month-ahead",
        "initial_training_observations": MIN_TRAIN_SIZE,
        "backtest_observations": len(actuals),
        "model_comparison": comparison,
        "best_validated_model": best_model,
        "selected_model": best_model,  # Backward-compatible field for the dashboard.
        "backtest_predictions": records,
    }


def build_plfs_wpr_forecast(horizon: int = 1) -> dict:
    """Return best-validated forecast plus a separate dynamic trend scenario."""
    if not 1 <= horizon <= 3:
        raise ValueError("Forecast horizon must be between 1 and 3 months.")

    df = load_wpr_series(DATA_FILE)
    validation = rolling_origin_validation(df)
    values = df[TARGET_COLUMN].to_numpy(dtype=float)
    best_model = validation["best_validated_model"]

    best_predictions = _predict_model(values, best_model, horizon=horizon)
    trend_params = tune_holt_parameters(values)
    trend_predictions = holt_damped_forecast(values, horizon=horizon, **trend_params)

    latest_period = pd.Period(df["parsed_month"].iloc[-1], freq="M")
    best_rows = [
        {"reference_month": str(latest_period + step), "forecast_wpr_pct": round(float(value), 3)}
        for step, value in enumerate(best_predictions, start=1)
    ]
    trend_rows = [
        {"reference_month": str(latest_period + step), "forecast_wpr_pct": round(float(value), 3)}
        for step, value in enumerate(trend_predictions, start=1)
    ]
    history_rows = [
        {
            "reference_month": str(pd.Period(row.parsed_month, freq="M")),
            "actual_wpr_pct": round(float(getattr(row, TARGET_COLUMN)), 3),
        }
        for row in df.itertuples(index=False)
    ]

    trend_metrics = next(
        (row for row in validation["model_comparison"] if row["model"] == "holt_damped_trend"),
        None,
    )
    source_documents = (
        sorted(df["source_document"].dropna().astype(str).unique().tolist())
        if "source_document" in df.columns else []
    )
    source_urls = (
        sorted(df["source_url"].dropna().astype(str).unique().tolist())
        if "source_url" in df.columns else []
    )

    return {
        "indicator": "Worker Population Ratio (WPR)",
        "population_scope": "All India, persons aged 15 years and above, Current Weekly Status (CWS), rural and urban combined",
        "frequency": "Monthly",
        "unit": "Percent",
        "forecast_origin": str(latest_period),
        "observations": int(len(df)),
        "history_start": str(pd.Period(df["parsed_month"].iloc[0], freq="M")),
        "history_end": str(latest_period),
        "selected_model": best_model,
        "best_validated_model": best_model,
        "forecast": best_rows,
        "trend_model": "holt_damped_trend",
        "trend_model_metrics": trend_metrics,
        "trend_model_parameters": trend_params,
        "trend_forecast": trend_rows,
        "validation": validation,
        "history": history_rows,
        "source_documents": source_documents,
        "source_urls": source_urls,
        "methodology_warning": (
            "The primary forecast uses the model with the lowest rolling-origin MAE. "
            "If that is the naive model, its flat forecast is a valid data-driven result. "
            "The separate Holt damped-trend line is a dynamic alternative scenario; "
            "it must not be described as more accurate when its validation error is higher. "
            "This is an exploratory WPR forecast, not a skill-gap or vacancy forecast."
        ),
    }


def main() -> None:
    result = build_plfs_wpr_forecast(horizon=3)
    print("Best validated model:", result["best_validated_model"])
    print("Model comparison:")
    for metric in result["validation"]["model_comparison"]:
        print(metric)
    print("Best validated forecast:", result["forecast"])
    print("Dynamic Holt scenario:", result["trend_forecast"])


if __name__ == "__main__":
    main()
