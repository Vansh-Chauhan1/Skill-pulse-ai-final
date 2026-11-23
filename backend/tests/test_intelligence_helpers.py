import unittest
import pandas as pd

from services.intelligence_engine import (
    _build_industry_changes,
    _build_monthly_wpr_summary,
    _build_qualification_demand,
)


class IntelligenceHelperTests(unittest.TestCase):
    def test_monthly_wpr_summary(self):
        df = pd.DataFrame([
            {"reference_month": "2026-09", "rural_urban_person_wpr_pct": 52.7, "age_group": "15 years and above", "status_approach": "CWS"},
            {"reference_month": "2026-10", "rural_urban_person_wpr_pct": 53.0, "age_group": "15 years and above", "status_approach": "CWS"},
        ])
        summary = _build_monthly_wpr_summary(df)
        self.assertEqual(summary["latest_month"], "2026-10")
        self.assertEqual(summary["month_on_month_change_percentage_points"], 0.3)

    def test_industry_change_is_percentage_points(self):
        df = pd.DataFrame([
            {"survey_period": "2022-23", "industry_broad_division_nic08": "Manufacturing", "rural_urban_person_pct": 11.4},
            {"survey_period": "2023-24", "industry_broad_division_nic08": "Manufacturing", "rural_urban_person_pct": 11.6},
        ])
        result = _build_industry_changes(df)
        self.assertEqual(result[0]["change_percentage_points"], 0.2)

    def test_qualification_change(self):
        df = pd.DataFrame([
            {"qualification_as_published": "Graduate", "vacancies_fy2022_23": 100, "vacancies_fy2023_24": 150},
        ])
        result = _build_qualification_demand(df)
        self.assertEqual(result[0]["calculated_change_pct"], 50.0)


if __name__ == "__main__":
    unittest.main()
