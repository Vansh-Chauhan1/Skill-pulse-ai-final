from pathlib import Path

import numpy as np
import pandas as pd


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

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

MODEL_NAMES = ["naive", "drift"]


# --------------------------------------------------
# LOAD AND VALIDATE DATA
# --------------------------------------------------

def load_wpr_series():
    """
    Load and validate the official monthly PLFS WPR series.

    Expected population:
    All India, persons aged 15 years and above,
    Current Weekly Status (CWS), rural + urban combined.
    """

    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"PLFS monthly dataset not found: {DATA_FILE}"
        )

    df = pd.read_csv(DATA_FILE)

    required_columns = [
        "reference_month",
        TARGET_COLUMN,
    ]

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    if df.empty:
        raise ValueError("The PLFS dataset is empty.")

    # Validate month format.
    df["parsed_month"] = pd.to_datetime(
        df["reference_month"].astype(str),
        format="%Y-%m",
        errors="coerce"
    )

    if df["parsed_month"].isna().any():
        raise ValueError(
            "Invalid reference_month values. Expected YYYY-MM."
        )

    # Validate numeric WPR values.
    df[TARGET_COLUMN] = pd.to_numeric(
        df[TARGET_COLUMN],
        errors="coerce"
    )

    if df[TARGET_COLUMN].isna().any():
        raise ValueError("WPR contains missing or non-numeric values.")

    values = df[TARGET_COLUMN].to_numpy(dtype=float)

    if not np.isfinite(values).all():
        raise ValueError("WPR contains infinite values.")

    if ((values < 0) | (values > 100)).any():
        raise ValueError("WPR values must be between 0 and 100.")

    # Sort chronologically.
    df = df.sort_values("parsed_month").reset_index(drop=True)

    # Reject duplicate months.
    if df["parsed_month"].duplicated().any():
        raise ValueError("Duplicate months found in PLFS dataset.")

    # Check that no month is missing.
    periods = pd.PeriodIndex(
        df["parsed_month"],
        freq="M"
    )

    expected_periods = pd.period_range(
        start=periods[0],
        end=periods[-1],
        freq="M"
    )

    if not periods.equals(expected_periods):
        raise ValueError(
            "The monthly series contains missing months."
        )

    if len(df) <= MIN_TRAIN_SIZE:
        raise ValueError(
            f"At least {MIN_TRAIN_SIZE + 1} observations are required."
        )

    return df


# --------------------------------------------------
# FORECASTING METHODS
# --------------------------------------------------

def naive_forecast(train_values, horizon=1):
    """
    Predict every future month using the last observed value.
    """

    last_value = float(train_values[-1])

    return [
        float(np.clip(last_value, 0, 100))
        for _ in range(horizon)
    ]


def drift_forecast(train_values, horizon=1):
    """
    Extend the average historical change into the future.
    """

    if len(train_values) < 2:
        raise ValueError(
            "Drift forecasting requires at least two observations."
        )

    average_change = (
        train_values[-1] - train_values[0]
    ) / (len(train_values) - 1)

    predictions = []

    for step in range(1, horizon + 1):
        prediction = (
            train_values[-1]
            + step * average_change
        )

        predictions.append(
            float(np.clip(prediction, 0, 100))
        )

    return predictions


# --------------------------------------------------
# FORECAST DISPATCHER
# --------------------------------------------------

def make_forecast(train_values, model_name, horizon=1):

    if model_name == "naive":
        return naive_forecast(train_values, horizon)

    if model_name == "drift":
        return drift_forecast(train_values, horizon)

    raise ValueError(
        f"Unknown forecasting method: {model_name}"
    )


# --------------------------------------------------
# EVALUATION METRICS
# --------------------------------------------------

def calculate_metrics(actual_values, predicted_values):

    actual = np.asarray(actual_values, dtype=float)
    predicted = np.asarray(predicted_values, dtype=float)

    errors = actual - predicted

    mae = np.mean(np.abs(errors))

    rmse = np.sqrt(
        np.mean(errors ** 2)
    )

    denominator = np.abs(actual) + np.abs(predicted)

    smape_values = np.divide(
        2 * np.abs(errors),
        denominator,
        out=np.zeros_like(errors),
        where=denominator != 0
    )

    smape = np.mean(smape_values) * 100

    return {
        "mae": round(float(mae), 4),
        "rmse": round(float(rmse), 4),
        "smape_pct": round(float(smape), 4),
    }


# --------------------------------------------------
# ROLLING-ORIGIN VALIDATION
# --------------------------------------------------

def rolling_origin_validation(df):
    """
    Expanding-window, one-month-ahead validation.

    Example:
    Train Apr-Nov 2025 -> predict Dec 2025.
    Train Apr-Dec 2025 -> predict Jan 2026.
    Continue until the latest observation.
    """

    values = df[TARGET_COLUMN].to_numpy(dtype=float)

    months = pd.PeriodIndex(
        df["parsed_month"],
        freq="M"
    )

    if len(values) <= MIN_TRAIN_SIZE:
        raise ValueError(
            "Not enough observations for rolling validation."
        )

    actual_values = []
    predictions = {
        "naive": [],
        "drift": [],
    }

    backtest_records = []

    for test_index in range(MIN_TRAIN_SIZE, len(values)):

        train_values = values[:test_index]

        actual = float(values[test_index])

        naive_prediction = make_forecast(
            train_values,
            "naive",
            horizon=1
        )[0]

        drift_prediction = make_forecast(
            train_values,
            "drift",
            horizon=1
        )[0]

        actual_values.append(actual)

        predictions["naive"].append(
            naive_prediction
        )

        predictions["drift"].append(
            drift_prediction
        )

        backtest_records.append({
            "reference_month": str(months[test_index]),
            "actual_wpr_pct": round(actual, 3),
            "naive_prediction_pct": round(
                naive_prediction, 3
            ),
            "drift_prediction_pct": round(
                drift_prediction, 3
            ),
        })

    # Calculate performance for both methods.
    model_comparison = []

    for model_name in MODEL_NAMES:

        metrics = calculate_metrics(
            actual_values,
            predictions[model_name]
        )

        model_comparison.append({
            "model": model_name,
            **metrics,
        })

    # Lowest MAE wins. Naive is preferred in an exact tie.
    selected_model = min(
        model_comparison,
        key=lambda result: (
            result["mae"],
            result["rmse"]
        )
    )

    return {
        "initial_training_observations": MIN_TRAIN_SIZE,
        "backtest_observations": len(actual_values),
        "model_comparison": model_comparison,
        "selected_model": selected_model["model"],
        "backtest_predictions": backtest_records,
    }


# --------------------------------------------------
# FINAL FORECAST
# --------------------------------------------------

def build_plfs_wpr_forecast(horizon=1):
    """
    Validate the baseline methods, select the better one,
    and forecast future monthly WPR values.

    Maximum forecast horizon: 3 months.
    """

    if horizon < 1 or horizon > 3:
        raise ValueError(
            "Forecast horizon must be between 1 and 3 months."
        )

    df = load_wpr_series()

    validation = rolling_origin_validation(df)

    selected_model = validation["selected_model"]

    all_values = df[TARGET_COLUMN].to_numpy(dtype=float)

    final_predictions = make_forecast(
        all_values,
        selected_model,
        horizon=horizon
    )

    latest_month = pd.Period(
        df["parsed_month"].iloc[-1],
        freq="M"
    )

    forecast_records = []

    for step, prediction in enumerate(
        final_predictions,
        start=1
    ):

        future_month = latest_month + step

        forecast_records.append({
            "reference_month": str(future_month),
            "forecast_wpr_pct": round(
                prediction, 3
            ),
        })

    # Historical observations for charts.
    history = []

    for _, row in df.iterrows():

        history.append({
            "reference_month": str(
                row["parsed_month"].to_period("M")
            ),
            "actual_wpr_pct": round(
                float(row[TARGET_COLUMN]), 3
            ),
        })

    source_documents = []

    if "source_document" in df.columns:
        source_documents = sorted(
            df["source_document"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

    source_urls = []

    if "source_url" in df.columns:
        source_urls = sorted(
            df["source_url"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

    return {
        "indicator": "Worker Population Ratio (WPR)",

        "population_scope": (
            "All India, persons aged 15 years and above, "
            "Current Weekly Status (CWS), rural and urban combined"
        ),

        "frequency": "Monthly",

        "unit": "Percent",

        "forecast_origin": str(latest_month),

        "observations": len(df),

        "history_start": str(
            df["parsed_month"].iloc[0].to_period("M")
        ),

        "history_end": str(latest_month),

        "selected_model": selected_model,

        "validation": validation,

        "history": history,

        "forecast": forecast_records,

        "source_documents": source_documents,

        "source_urls": source_urls,

        "methodology_warning": (
            "This is an exploratory WPR forecast, not a skill-gap "
            "forecast. Only a short monthly history is available. "
            "The forecast should not be interpreted as a long-term "
            "labour-market or skill-shortage prediction."
        ),
    }