import unittest

import numpy as np
import pandas as pd

from ml.plfs_forecasting import (
    calculate_metrics,
    drift_forecast,
    naive_forecast,
    rolling_origin_validation,
)
from services.sector_demand_engine import (
    build_sector_demand_summary,
    calculate_sector_demand_trends,
    classify_sector_trend,
)


class ForecastBaselineTests(unittest.TestCase):
    def test_naive_uses_last_value(self):
        self.assertEqual(naive_forecast([50.0, 51.0, 52.0], 2), [52.0, 52.0])

    def test_drift_projects_average_change(self):
        self.assertEqual(drift_forecast([50.0, 52.0, 54.0], 2), [56.0, 58.0])

    def test_metrics(self):
        result = calculate_metrics([10, 20], [12, 18])
        self.assertEqual(result["mae"], 2.0)
        self.assertEqual(result["rmse"], 2.0)

    def test_rolling_validation_compares_two_models(self):
        months = pd.date_range("2025-01-01", periods=12, freq="MS")
        frame = pd.DataFrame({
            "parsed_month": months,
            "rural_urban_person_wpr_pct": np.linspace(50, 52, 12),
        })
        result = rolling_origin_validation(frame)
        self.assertEqual(result["backtest_observations"], 4)
        self.assertEqual({row["model"] for row in result["model_comparison"]}, {"naive", "drift"})
        self.assertIn(result["selected_model"], {"naive", "drift"})


class SectorDemandTests(unittest.TestCase):
    def test_classification(self):
        self.assertEqual(classify_sector_trend(100, 120)[0], "growth")
        self.assertEqual(classify_sector_trend(100, 80)[0], "decline")
        self.assertEqual(classify_sector_trend(0, 10)[0], "new_or_zero_baseline")

    def test_calculation_and_summary(self):
        source = pd.DataFrame([
            {"ncs_sector_as_published": "IT", "vacancies_fy2022_23": 100, "vacancies_fy2023_24": 150},
            {"ncs_sector_as_published": "Education", "vacancies_fy2022_23": 100, "vacancies_fy2023_24": 90},
        ])
        trends = calculate_sector_demand_trends(source)
        self.assertEqual(len(trends), 2)
        summary = build_sector_demand_summary(trends)
        self.assertEqual(summary["sector_count"], 2)
        self.assertFalse(summary["forecast_ready"])


if __name__ == "__main__":
    unittest.main()
