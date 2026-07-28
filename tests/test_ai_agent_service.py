import unittest

from Services.ai_agent_service import build_polished_portfolio_html, inject_commit_metadata


class AiAgentServiceTests(unittest.TestCase):
    def test_inject_commit_metadata_adds_timestamp_marker(self):
        html = "<html><body>Portfolio</body></html>"
        updated = inject_commit_metadata(html, timestamp="2026-07-23T12:00:00Z")

        self.assertIn("Portfolio", updated)
        self.assertIn("portfolio-generated-at", updated)
        self.assertIn("2026-07-23T12:00:00Z", updated)

    def test_inject_commit_metadata_changes_content_for_new_timestamp(self):
        html = "<html><body>Portfolio</body></html>"
        first = inject_commit_metadata(html, timestamp="2026-07-23T12:00:00Z")
        second = inject_commit_metadata(html, timestamp="2026-07-23T12:00:01Z")

        self.assertNotEqual(first, second)

    def test_build_polished_portfolio_html_adds_professional_styles(self):
        html = "<html><body><h1>Jane Doe</h1><p>Data Engineer</p></body></html>"
        updated = build_polished_portfolio_html(html)

        self.assertIn("portfolio-shell", updated)
        self.assertIn("font-family: 'Inter', 'Segoe UI', sans-serif", updated)
        self.assertIn("Jane Doe", updated)
        self.assertIn("<style>", updated)


if __name__ == "__main__":
    unittest.main()
