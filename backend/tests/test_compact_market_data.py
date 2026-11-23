import tempfile
import unittest
from pathlib import Path

import pandas as pd

from services import compact_market_data as pipeline


class CompactMarketPipelineTests(unittest.TestCase):
    def test_builds_normalized_rows_and_quality_report(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plfs_dir = root / "plfs"
            ncs_dir = root / "ncs"
            plfs_dir.mkdir()
            ncs_dir.mkdir()

            pd.DataFrame([
                {"reference_month": "2025-04", "age_group": "15 years and above", "status_approach": "CWS", "rural_person_wpr_pct": 55.4, "urban_person_wpr_pct": 47.4, "rural_urban_person_wpr_pct": 52.8, "source_document": "test", "source_url": "https://example.test"},
                {"reference_month": "2025-05", "age_group": "15 years and above", "status_approach": "CWS", "rural_person_wpr_pct": 54.1, "urban_person_wpr_pct": 46.9, "rural_urban_person_wpr_pct": 51.7, "source_document": "test", "source_url": "https://example.test"},
            ]).to_csv(plfs_dir / "plfs_monthly_cws_wpr_2025_2026.csv", index=False)

            pd.DataFrame([
                {"state_ut": "All India", "survey_period": "2025", "age_group": "All ages", "status_approach": "Usual status", "rural_person_wpr_pct": 45.4, "urban_person_wpr_pct": 39.3, "rural_urban_person_wpr_pct": 43.5, "source_page": "Table 17", "source_url": "https://example.test"},
            ]).to_csv(plfs_dir / "plfs_state_wpr_2025.csv", index=False)

            pd.DataFrame([
                {"survey_period": "2022-23", "industry_broad_division_nic08": "Manufacturing", "rural_urban_person_pct": 11.4, "indicator": "share", "source_statement": "Statement 7", "source_url": "https://example.test"},
                {"survey_period": "2023-24", "industry_broad_division_nic08": "Manufacturing", "rural_urban_person_pct": 11.6, "indicator": "share", "source_statement": "Statement 7", "source_url": "https://example.test"},
            ]).to_csv(plfs_dir / "plfs_all_india_industry_distribution_2021_24.csv", index=False)

            pd.DataFrame([
                {"ncs_sector_as_published": "IT and Communication", "vacancies_fy2022_23": 100, "vacancies_fy2023_24": 150, "source_report": "NCS test report", "source_url": "https://example.test"},
            ]).to_csv(ncs_dir / "ncs_sector_vacancies_fy2022_23_fy2023_24.csv", index=False)

            pd.DataFrame([
                {"qualification_as_published": "Graduate", "vacancies_fy2022_23": 80, "vacancies_fy2023_24": 100, "source_report": "NCS test report", "source_url": "https://example.test"},
            ]).to_csv(ncs_dir / "ncs_qualification_vacancies_fy2022_23_fy2023_24.csv", index=False)

            pd.DataFrame([
                {"metric_as_published": "Vacancies mobilised", "value_fy2022_23": 200, "value_fy2023_24": 300, "source_report": "NCS test report", "source_url": "https://example.test"},
            ]).to_csv(ncs_dir / "ncs_summary_statistics_fy2022_23_fy2023_24.csv", index=False)

            original_plfs, original_ncs = pipeline.PLFS_DIR, pipeline.NCS_DIR
            try:
                pipeline.PLFS_DIR = plfs_dir
                pipeline.NCS_DIR = ncs_dir
                frame, report = pipeline.build_compact_market_dataset()
            finally:
                pipeline.PLFS_DIR, pipeline.NCS_DIR = original_plfs, original_ncs

            # 2 months x 3 WPR breakdowns + 3 annual WPR rows +
            # 2 industry rows + 2 sector + 2 qualification + 2 summary rows.
            self.assertEqual(len(frame), 17)
            self.assertTrue(report["quality_checks"]["incompatible_units_and_populations_kept_separate"])
            self.assertEqual(report["dataset_record_counts"]["plfs_monthly_wpr"], 6)


if __name__ == "__main__":
    unittest.main()
