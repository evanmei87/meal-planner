import pytest
import sys
from pathlib import Path
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tools.preference_normalizer import normalize_preferences, _fallback_exclusions


class _FakeAgent:
    def __init__(self, terms):
        self._terms = terms

    def process(self, prompt, response_schema=None):
        return response_schema(excluded_terms=self._terms)


class _FailingAgent:
    def process(self, prompt, response_schema=None):
        raise RuntimeError("API unavailable")


def _patch_agent(monkeypatch, agent):
    monkeypatch.setattr("tools.preference_normalizer.GeminiAgent", lambda: agent)


def test_normalize_empty_string_returns_empty():
    assert normalize_preferences("") == []


def test_normalize_whitespace_only_returns_empty():
    assert normalize_preferences("   ") == []


def test_normalize_calls_gemini_and_returns_terms(monkeypatch):
    _patch_agent(monkeypatch, _FakeAgent(["chicken thighs", "chicken breast"]))
    result = normalize_preferences("no chicken")
    assert "chicken thighs" in result
    assert "chicken breast" in result


def test_normalize_lowercases_gemini_output(monkeypatch):
    _patch_agent(monkeypatch, _FakeAgent(["Salmon", "OATMEAL"]))
    result = normalize_preferences("no fish, no grains")
    assert all(t == t.lower() for t in result)


def test_normalize_falls_back_on_gemini_error(monkeypatch):
    _patch_agent(monkeypatch, _FailingAgent())
    result = normalize_preferences("no salmon")
    assert "salmon" in result


def test_fallback_exclusions_parses_no_phrases():
    assert _fallback_exclusions("no salmon, no chicken") == ["salmon", "chicken"]


def test_fallback_exclusions_ignores_non_no_phrases():
    assert _fallback_exclusions("high protein, no red meat") == ["red meat"]


def test_fallback_exclusions_empty():
    assert _fallback_exclusions("") == []
