import unittest

import pandas as pd

from services.sector_demand_engine import (
    build_sector_demand_summary,
    calculate_sector_demand_trends,
    classify_sector_trend,
)


class SectorDemandEngineTests(unittest.TestCase):
    def test_growth_signal(self):
        signal, low_base, _ = classify_sector_trend(100, 120)
        self.assertEqual(signal, "growth")
        self.assertFalse(low_base)

    def test_small_base_warning(self):
        signal, low_base, _ = classify_sector_trend(100, 250)
        self.assertEqual(signal, "rapid_growth")
        self.assertTrue(low_base)

    def test_decline_signal(self):
        signal, _, _ = classify_sector_trend(100, 80)
        self.assertEqual(signal, "decline")

    def test_zero_baseline(self):
        signal, low_base, _ = classify_sector_trend(0, 15)
        self.assertEqual(signal, "new_or_zero_baseline")
        self.assertTrue(low_base)

    def test_duplicate_sector_rejected(self):
        df = pd.DataFrame([
            {"ncs_sector_as_published": "IT", "vacancies_fy2022_23": 10, "vacancies_fy2023_24": 20},
            {"ncs_sector_as_published": "IT", "vacancies_fy2022_23": 12, "vacancies_fy2023_24": 21},
        ])
        with self.assertRaises(ValueError):
            calculate_sector_demand_trends(df)

    def test_summary_counts(self):
        df = pd.DataFrame([
            {"ncs_sector_as_published": "Growth", "vacancies_fy2022_23": 100, "vacancies_fy2023_24": 130},
            {"ncs_sector_as_published": "Decline", "vacancies_fy2022_23": 100, "vacancies_fy2023_24": 80},
        ])
        output = calculate_sector_demand_trends(df)
        summary = build_sector_demand_summary(output)
        self.assertEqual(summary["sector_count"], 2)
        self.assertEqual(summary["trend_signal_counts"]["growth"], 1)
        self.assertEqual(summary["trend_signal_counts"]["decline"], 1)
        self.assertFalse(summary["forecast_ready"])


if __name__ == "__main__":
    unittest.main()
