import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app
from services.ai_service import (
    generate_answer,
    generate_forecast_interpretation,
    llm_status,
)


FORECAST_FIXTURE = {
    "indicator": "Worker Population Ratio (WPR)",
    "population_scope": "All India, persons aged 15 years and above",
    "forecast_origin": "2026-10",
    "selected_model": "naive",
    "best_validated_model": "naive",
    "trend_model": "holt_damped_trend",
    "history": [{"reference_month": "2026-10", "actual_wpr_pct": 53.0}],
    "forecast": [
        {"reference_month": "2026-11", "forecast_wpr_pct": 53.0},
        {"reference_month": "2026-12", "forecast_wpr_pct": 53.0},
    ],
    "trend_forecast": [
        {"reference_month": "2026-11", "forecast_wpr_pct": 53.129},
        {"reference_month": "2026-12", "forecast_wpr_pct": 53.21},
    ],
    "validation": {
        "model_comparison": [
            {
                "model": "naive",
                "mae": 0.3818,
                "rmse": 0.4954,
                "smape_pct": 0.7285,
            },
            {
                "model": "holt_damped_trend",
                "mae": 0.4042,
                "rmse": 0.5428,
                "smape_pct": 0.773,
            }
        ]
    },
    "methodology_warning": "This is an exploratory WPR forecast.",
}


class LocalAIServiceTests(unittest.TestCase):
    def test_local_engine_does_not_require_provider_credentials(self):
        status = llm_status()

        self.assertTrue(status["configured"])
        self.assertEqual(status["provider"], "skillpulse-local")

    def test_empty_question_returns_validation_message(self):
        answer = generate_answer("", "")

        self.assertEqual(answer, "Please enter a question.")

    def test_missing_data_returns_explanatory_answer(self):
        answer = generate_answer("What are the employment trends?", "")

        self.assertIn("couldn't retrieve", answer)

    def test_chat_route_handles_synchronous_local_answer(self):
        context = SimpleNamespace(
            text="",
            sources=[],
            data_timestamp=None,
            retrieved_at="2026-11-24T00:00:00Z",
            states=[],
            topics=[],
        )

        async def build_chat_context(question, history):
            return context

        with patch("routers.ai.build_chat_context", new=build_chat_context):
            response = TestClient(app).post(
                "/api/ai/chat",
                json={"question": "What are the employment trends?", "history": []},
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("couldn't retrieve", response.json()["answer"])


class ForecastInterpretationTests(unittest.TestCase):
    def test_interpretation_explains_trend_validation_and_scope(self):
        answer = generate_forecast_interpretation(FORECAST_FIXTURE)

        self.assertIn("remained unchanged at the reported precision", answer)
        self.assertIn("increased by 0.210 percentage points", answer)
        self.assertIn("MAE 0.3818", answer)
        self.assertIn("not reliable evidence of an improvement", answer)
        self.assertIn("not an unemployment rate", answer)

    def test_missing_forecast_values_are_reported(self):
        answer = generate_forecast_interpretation({"forecast": []})

        self.assertIn("no valid predicted WPR values", answer)

    def test_chat_forecast_intent_returns_an_interpretation(self):
        context = (
            "=== DATA BLOCK 1: PLFS WPR statistical forecast ===\n"
            "Data (JSON):\n"
            f"{json.dumps(FORECAST_FIXTURE)}"
        )

        answer = generate_answer("Interpret the WPR forecast.", context)

        self.assertIn("FUTURE OUTLOOK", answer)
        self.assertIn("MODEL RELIABILITY", answer)

    def test_forecast_endpoint_uses_requested_horizon(self):
        with patch(
            "ml.plfs_forecasting.build_plfs_wpr_forecast",
            return_value=FORECAST_FIXTURE,
        ) as build_forecast:
            response = TestClient(app).get(
                "/api/ai/forecast-interpretation?horizon=2"
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["forecast_horizon"], 2)
        self.assertIn("FUTURE OUTLOOK", response.json()["answer"])
        build_forecast.assert_called_once_with(horizon=2)

    def test_forecast_endpoint_rejects_out_of_range_horizon(self):
        response = TestClient(app).get(
            "/api/ai/forecast-interpretation?horizon=4"
        )

        self.assertEqual(response.status_code, 422)


class StateAnalysisTests(unittest.TestCase):
    def test_chat_state_analysis_combines_state_and_national_data(self):
        state_data = {
            "rows_for_requested_state": [
                {
                    "state_ut": "Chhattisgarh",
                    "survey_period": "January-December 2025",
                    "rural_urban_person_wpr_pct": 54.0,
                    "rural_person_wpr_pct": 57.0,
                    "urban_person_wpr_pct": 42.0,
                    "rural_urban_male_wpr_pct": 62.6,
                    "rural_urban_female_wpr_pct": 45.4,
                }
            ],
            "all_rows_for_comparison": [],
        }
        sector_data = [
            {
                "ncs_sector_as_published": "Finance and Insurance",
                "vacancies_fy2022_23": 1998196,
                "vacancies_fy2023_24": 4668845,
                "reported_percent_change": 134.0,
            }
        ]
        context = "\n\n".join(
            [
                "=== DATA BLOCK 1: PLFS state-wise worker population ratio (WPR) ===\n"
                f"Data (JSON):\n{json.dumps(state_data)}",
                "=== DATA BLOCK 2: NCS sector-wise vacancies ===\n"
                f"Data (JSON):\n{json.dumps(sector_data)}",
            ]
        )

        answer = generate_answer(
            "Analyze Chhattisgarh using state-level PLFS WPR and national "
            "NCS sector vacancy data.",
            context,
        )

        self.assertIn("Chhattisgarh: combined WPR 54.0%", answer)
        self.assertIn("Finance and Insurance: 4,668,845 vacancies", answer)
        self.assertIn("not state-level vacancy counts", answer)
        self.assertIn("do not establish local vacancies", answer)


if __name__ == "__main__":
    unittest.main()
