import asyncio
import unittest
from types import SimpleNamespace

from app.main import AskRequest, ask_agent, health, root, tools


class AppTests(unittest.TestCase):
    def test_info_endpoints(self):
        self.assertIn("ask", root()["endpoints"])
        self.assertGreaterEqual(len(tools()["tools"]), 1)
        self.assertEqual(health()["status"], "ok")

    def test_ask_uses_mock_without_gemini_key(self):
        request = SimpleNamespace(client=None)
        response = asyncio.run(
            ask_agent(
                AskRequest(question="Hello"),
                request,
                "dev-key-change-me",
            )
        )
        self.assertEqual(response.model, "mock")
        self.assertTrue(response.answer)


if __name__ == "__main__":
    unittest.main()
