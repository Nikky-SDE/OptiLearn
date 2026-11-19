import unittest
from pydantic import ValidationError

from app.api.routes.chat import _session_belongs_to_user
from app.api.routes.chat import QueryRequest


class ChatSessionScopeTests(unittest.TestCase):
    def test_accepts_session_in_user_namespace(self):
        self.assertTrue(_session_belongs_to_user("user-123_session", "user-123"))

    def test_rejects_another_users_session(self):
        self.assertFalse(_session_belongs_to_user("other-user_session", "user-123"))

    def test_rejects_user_id_prefix_collision(self):
        self.assertFalse(_session_belongs_to_user("user-1234_session", "user-123"))

    def test_rejects_empty_session_nonce(self):
        self.assertFalse(_session_belongs_to_user("user-123_", "user-123"))

    def test_chat_request_limits_question_and_session_sizes(self):
        with self.assertRaises(ValidationError):
            QueryRequest(question="x" * 10_001)
        with self.assertRaises(ValidationError):
            QueryRequest(question="hello", session_id="x" * 129)


if __name__ == "__main__":
    unittest.main()
