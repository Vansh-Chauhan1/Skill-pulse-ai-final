import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from ml import plfs_forecasting as forecast


class PlfsForecastTests(unittest.TestCase):
    def test_holt_trend_changes_over_horizon(self):
        values = [52.8, 51.7, 51.2, 52.0, 52.2, 52.4, 52.5, 53.2, 53.4]
        result = forecast.holt_damped_forecast(values, horizon=3)
        self.assertEqual(len(result), 3)
        self.assertGreater(len(set(result)), 1)

    def test_forecast_returns_best_baseline_and_dynamic_scenario(self):
        values = [
            52.8, 51.7, 51.2, 52.0, 52.2, 52.4, 52.5, 53.2, 53.4,
            53.1, 53.2, 52.6, 52.2, 51.4, 51.4, 52.5, 52.8, 52.7, 53.0,
        ]
        months = pd.date_range("2025-04-01", periods=len(values), freq="MS")
        fixture = pd.DataFrame({
            "reference_month": months.strftime("%Y-%m"),
            "age_group": "15 years and above",
            "status_approach": "Current Weekly Status (CWS)",
            "rural_urban_person_wpr_pct": values,
        })
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_path = Path(temp_dir) / "monthly_wpr.csv"
            fixture.to_csv(fixture_path, index=False)
            with patch.object(forecast, "DATA_FILE", fixture_path):
                result = forecast.build_plfs_wpr_forecast(horizon=3)

        self.assertEqual(len(result["forecast"]), 3)
        self.assertEqual(len(result["trend_forecast"]), 3)
        self.assertEqual(result["trend_model"], "holt_damped_trend")
        self.assertIn(result["best_validated_model"], {
            "naive", "drift", "linear_recent6", "holt_damped_trend"
        })
        trend_values = [row["forecast_wpr_pct"] for row in result["trend_forecast"]]
        self.assertGreater(len(set(trend_values)), 1)

    def test_horizon_validation(self):
        with self.assertRaises(ValueError):
            forecast.build_plfs_wpr_forecast(horizon=4)

    def test_naive_forecast_is_flat_by_definition(self):
        self.assertEqual(forecast.naive_forecast([1, 2, 3], 3), [3.0, 3.0, 3.0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
