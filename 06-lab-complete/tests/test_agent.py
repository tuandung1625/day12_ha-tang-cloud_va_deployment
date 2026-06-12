import unittest

from app.agent import ResearchAgent
from app.config import settings
from app.tools import TOOL_FUNCTIONS, execute_tool, format_digest, summarize_text


class AgentTests(unittest.TestCase):
    def test_mock_fallback(self):
        original_key = settings.gemini_api_key
        settings.gemini_api_key = ""
        try:
            result = ResearchAgent().run("What tools are available?")
        finally:
            settings.gemini_api_key = original_key

        self.assertEqual(result.model, "mock")
        self.assertEqual(result.tools_used, [])
        self.assertTrue(result.answer)

    def test_tool_registry_is_read_only_subset(self):
        self.assertIn("web_search", TOOL_FUNCTIONS)
        self.assertIn("weather", TOOL_FUNCTIONS)
        self.assertNotIn("send", TOOL_FUNCTIONS)

    def test_local_tools(self):
        summary = summarize_text("One. Two. Three.", max_sentences=2)
        self.assertEqual(summary["summary"], "One. Two.")

        digest = format_digest(
            [{"title": "Example", "url": "https://example.com", "summary": "Text"}]
        )
        self.assertIn("Example", digest["markdown"])

    def test_unknown_tool_is_reported(self):
        result = execute_tool("does_not_exist", {})
        self.assertEqual(result["error"], "UnknownTool")


if __name__ == "__main__":
    unittest.main()
