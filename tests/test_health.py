import unittest

from app.main import health_check


class HealthRouteTests(unittest.TestCase):
    def test_health_check_reports_service_status(self) -> None:
        response = health_check()

        self.assertEqual(response["status"], "healthy")
        self.assertEqual(response["service"], "optilearn-ai-tutor")
        self.assertIn("version", response)


if __name__ == "__main__":
    unittest.main()
