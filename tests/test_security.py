import unittest

from app.core.security import create_access_token, verify_token


class TokenSecurityTests(unittest.TestCase):
    def test_access_token_round_trip(self) -> None:
        token = create_access_token({"sub": "student-123"})

        self.assertEqual(verify_token(token), "student-123")

    def test_token_type_must_match(self) -> None:
        token = create_access_token({"sub": "student-123"})

        self.assertIsNone(verify_token(token, token_type="refresh"))

    def test_invalid_token_is_rejected(self) -> None:
        self.assertIsNone(verify_token("not-a-token"))


if __name__ == "__main__":
    unittest.main()
