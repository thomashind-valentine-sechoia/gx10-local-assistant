"""Render Private Web Search templates from the Home Assistant package.

Home Assistant strips template output. These tests parse the package YAML and
render the same strings, so an empty HTTP 200 cannot keep the live-results
instructions.
"""

import unittest
from pathlib import Path

import yaml
from jinja2 import Environment

PACKAGE = (
    Path(__file__).resolve().parents[1]
    / "configs/homeassistant/packages/local_knowledge.yaml"
)

LIVE_INSTRUCTIONS = (
    "These live results are newer than your training data. Answer ONLY from "
    "them, preferring the most recent figure, and say which site it came from. "
    "If sources disagree, give the range and name them."
)

WIKI_OFFER = "Offline Wikipedia Search"


def _env():
    return Environment(autoescape=False)


def _render(template, web_http=None, include_web_http=True):
    variables = {}
    if include_web_http:
        variables["web_http"] = web_http
    return _env().from_string(template).render(**variables).strip()


def _package():
    return yaml.safe_load(PACKAGE.read_text())


def _web_script():
    return _package()["script"]["private_web_search"]


def _web_result_templates():
    # Render the variable mapping the way the package declares it. Passing the
    # parsed strings through Jinja matches HA after YAML folding.
    return _web_script()["sequence"][1]["variables"]["web_result"]


class PrivateWebSearchTemplateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.web_result = _web_result_templates()
        cls.instructions = cls.web_result["instructions"]
        cls.results = cls.web_result["results"]
        cls.status = cls.web_result["status"]

    def outcome(self, web_http=None, include_web_http=True):
        return {
            "instructions": _render(self.instructions, web_http, include_web_http),
            "results": _render(self.results, web_http, include_web_http),
            "status": _render(self.status, web_http, include_web_http),
            "source": self.web_result["source"],
        }

    def assert_not_live_claim(self, rendered):
        self.assertNotIn("These live results", rendered["instructions"])
        self.assertNotIn("Answer ONLY from them", rendered["instructions"])
        self.assertNotIn("These live results", rendered["results"])
        self.assertNotIn(LIVE_INSTRUCTIONS, rendered["instructions"])
        self.assertIn("no live evidence", rendered["instructions"].lower())
        self.assertIn("no live evidence", rendered["results"].lower())
        self.assertIn(WIKI_OFFER, rendered["instructions"])
        self.assertIn(WIKI_OFFER, rendered["results"])
        self.assertIn("not a web search", rendered["instructions"])
        self.assertIn("was not called", rendered["instructions"])
        self.assertNotIn("offline web", rendered["instructions"].lower())
        self.assertNotIn("offline web", rendered["results"].lower())
        self.assertNotEqual(rendered["results"], "[]")

    def test_package_shape_is_unchanged_outside_search_wording(self):
        package = _package()
        rest = package["rest_command"]
        self.assertEqual(
            set(rest),
            {"private_web_search", "local_wikipedia_search", "local_wikipedia_article"},
        )
        self.assertEqual(rest["private_web_search"]["timeout"], 30)
        self.assertIn("127.0.0.1:8888/search", rest["private_web_search"]["url"])
        self.assertIn("language=en-GB", rest["private_web_search"]["url"])
        script = _web_script()
        self.assertEqual(script["alias"], "script__private_web_search")
        self.assertEqual(script["mode"], "parallel")
        self.assertIn("script__private_web_search", script["description"])
        self.assertNotIn("Private Web Search is", script["description"])
        self.assertEqual(script["max"], 3)
        self.assertEqual(list(script["fields"]), ["query"])
        self.assertEqual(
            [step.get("action") or step.get("stop") for step in script["sequence"]],
            [
                "rest_command.private_web_search",
                None,
                "Return web search results",
            ],
        )
        self.assertEqual(script["sequence"][0]["data"]["query"], "{{ query[:300] }}")
        self.assertEqual(script["sequence"][0]["response_variable"], "web_http")
        self.assertTrue(script["sequence"][0]["continue_on_error"])
        self.assertEqual(script["sequence"][2]["response_variable"], "web_result")
        self.assertEqual(
            list(self.web_result),
            ["source", "instructions", "status", "results"],
        )
        self.assertEqual(self.web_result["source"], "Self-hosted SearXNG web search")
        text = PACKAGE.read_text()
        self.assertNotIn("!secret", text)
        self.assertNotIn("<GENERATE_LOCALLY>", text)
        self.assertNotIn("REDACTED", text)
        for name in ("offline_wikipedia_search", "offline_wikipedia_article"):
            self.assertIn(name, package["script"])

    def test_nonempty_results_keep_live_instructions_and_bounds(self):
        long_snippet = "s" * 2005
        payload = {
            "status": 200,
            "content": {
                "results": [
                    {
                        "title": "First",
                        "url": "https://example.com/1",
                        "content": long_snippet,
                        "engine": "ignored",
                    },
                    {"title": "Second", "url": "https://example.com/2", "content": "two"},
                    {"title": "Third", "url": "https://example.com/3", "content": "three"},
                    {"title": "Fourth", "url": "https://example.com/4", "content": "nope"},
                ],
                "unresponsive_engines": [["bing", "timeout"]],
            },
        }
        rendered = self.outcome(payload)
        self.assertEqual(rendered["instructions"], LIVE_INSTRUCTIONS)
        self.assertEqual(rendered["status"], "200")
        self.assertNotIn(WIKI_OFFER, rendered["instructions"])
        self.assertNotIn("Fourth", rendered["results"])
        self.assertNotIn("ignored", rendered["results"])
        self.assertIn("'title': 'First'", rendered["results"])
        self.assertIn("'url': 'https://example.com/2'", rendered["results"])
        self.assertIn("'snippet': '" + ("s" * 2000) + "'", rendered["results"])
        self.assertNotIn("s" * 2001, rendered["results"])
        self.assertEqual(rendered["results"].count("'title':"), 3)

    def test_non_string_snippet_does_not_fail_the_result(self):
        payload = {
            "status": 200,
            "content": {
                "results": [
                    {"title": "Docs", "url": "https://example.com/docs", "content": None}
                ]
            },
        }
        rendered = self.outcome(payload)
        self.assertEqual(rendered["instructions"], LIVE_INSTRUCTIONS)
        self.assertEqual(
            rendered["results"],
            "[{'title': 'Docs', 'url': 'https://example.com/docs', 'snippet': ''}]",
        )

    def test_single_result_renders_the_same_fields(self):
        payload = {
            "status": 200,
            "content": {
                "results": [
                    {"title": "Docs", "url": "https://www.home-assistant.io/voice_control/", "content": "Assist"}
                ]
            },
        }
        rendered = self.outcome(payload)
        self.assertEqual(rendered["instructions"], LIVE_INSTRUCTIONS)
        self.assertEqual(
            rendered["results"],
            "[{'title': 'Docs', 'url': 'https://www.home-assistant.io/voice_control/', 'snippet': 'Assist'}]",
        )

    def test_empty_http_200_is_not_live_evidence(self):
        payload = {
            "status": 200,
            "content": {
                "query": "something obscure",
                "number_of_results": 0,
                "results": [],
                "unresponsive_engines": [],
            },
        }
        rendered = self.outcome(payload)
        self.assert_not_live_claim(rendered)
        self.assertIn("no matching web results", rendered["instructions"].lower())
        self.assertIn("No matching web results", rendered["results"])
        self.assertNotIn("unavailable", rendered["instructions"].lower())
        self.assertEqual(rendered["status"], "200")

    def test_empty_results_with_unresponsive_engines_are_a_failure(self):
        payload = {
            "status": 200,
            "content": {
                "results": [],
                "unresponsive_engines": [["google", "timeout", "Suspended"]],
            },
        }
        rendered = self.outcome(payload)
        self.assert_not_live_claim(rendered)
        self.assertNotIn("no matching web results", rendered["instructions"].lower())
        self.assertIn("unavailable", rendered["instructions"].lower())
        self.assertTrue(rendered["results"].startswith("Web search unavailable."))
        self.assertEqual(rendered["status"], "200")

    def test_http_error_is_unavailable(self):
        rendered = self.outcome(
            {"status": 503, "content": {"results": [{"title": "ignored", "url": "https://x", "content": "no"}]}}
        )
        self.assert_not_live_claim(rendered)
        self.assertIn("unavailable", rendered["instructions"].lower())
        self.assertNotIn("ignored", rendered["results"])
        self.assertEqual(rendered["status"], "503")

    def test_timeout_without_response_is_unavailable(self):
        rendered = self.outcome(include_web_http=False)
        self.assert_not_live_claim(rendered)
        self.assertIn("timed out", rendered["instructions"].lower())
        self.assertEqual(rendered["status"], "503")

    def test_malformed_shapes_are_unavailable(self):
        shapes = [
            {"status": 200, "content": "<html>not json</html>"},
            {"status": 200, "content": {"query": "x"}},
            {"status": 200, "content": {"results": "not-a-list"}},
            {"status": 200, "content": {"results": {"title": "one"}}},
            {"status": 200, "content": {"results": None}},
            {"status": 200, "content": None},
            {"status": 200, "content": {"results": ["only a string"]}},
            {"status": 200},
        ]
        for shape in shapes:
            with self.subTest(shape=shape):
                rendered = self.outcome(shape)
                self.assert_not_live_claim(rendered)
                self.assertIn("malformed", rendered["instructions"].lower())
                self.assertNotIn("no matching web results", rendered["instructions"].lower())
                self.assertTrue(rendered["results"].startswith("Web search unavailable."))


if __name__ == "__main__":
    unittest.main()
