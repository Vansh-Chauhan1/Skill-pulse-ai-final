import asyncio
import os
import unittest
from unittest.mock import patch

from services.ai_service import (
    AIServiceError,
    _provider_error_message,
    generate_answer,
    llm_status,
)


class AIServiceConfigurationTests(unittest.TestCase):
    def test_missing_llm_credentials_do_not_block_api_startup(self):
        with patch.dict(os.environ, {"LLM_API_KEY": "", "LLM_MODEL": ""}):
            self.assertFalse(llm_status()["configured"])

            with self.assertRaises(AIServiceError) as raised:
                asyncio.run(generate_answer("Question", [], "Context"))

        self.assertEqual(raised.exception.status_code, 503)


class AIProviderErrorMessageTests(unittest.TestCase):
    def test_authentication_error_points_to_key_or_permissions(self):
        message = _provider_error_message(401)

        self.assertIn("API key", message)
        self.assertIn("model access", message)

    def test_missing_model_error_points_to_model_configuration(self):
        message = _provider_error_message(404)

        self.assertIn("LLM_MODEL", message)

    def test_quota_error_points_to_billing_or_usage_limits(self):
        message = _provider_error_message(429)

        self.assertIn("billing", message)
        self.assertIn("usage limits", message)


if __name__ == "__main__":
    unittest.main()
