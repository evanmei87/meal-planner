import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parent.parent))

from src import server


def test_review_uncertain_item_can_create_specialty_from_candidate_menu(monkeypatch):
    meta = {
        "raw_phrase": "custom powder",
        "standardized_item": "custom powder",
        "quantity": 1.0,
        "unit": "scoops",
    }
    candidates = [
        {"corgis_description": "Candidate 1", "confidence_score": 0.60, "source": "corgis"},
        {"corgis_description": "Candidate 2", "confidence_score": 0.55, "source": "corgis"},
        {"corgis_description": "Candidate 3", "confidence_score": 0.50, "source": "corgis"},
    ]
    specialty = {**meta, "source": "specialty"}

    monkeypatch.setattr(server, "get_food_match_candidates", lambda *args, **kwargs: candidates)
    monkeypatch.setattr("builtins.input", lambda _prompt: "5")
    monkeypatch.setattr(server, "_save_specialty_ingredient", lambda item: specialty)

    assert server._review_uncertain_item(meta) == specialty


def test_review_uncertain_item_can_create_specialty_without_candidates(monkeypatch):
    meta = {
        "raw_phrase": "custom powder",
        "standardized_item": "custom powder",
        "quantity": 1.0,
        "unit": "scoops",
    }
    specialty = {**meta, "source": "specialty"}

    monkeypatch.setattr(server, "get_food_match_candidates", lambda *args, **kwargs: [])
    monkeypatch.setattr("builtins.input", lambda _prompt: "2")
    monkeypatch.setattr(server, "_save_specialty_ingredient", lambda item: specialty)

    assert server._review_uncertain_item(meta) == specialty


def test_review_uncertain_item_can_reword_more_than_once(monkeypatch):
    meta = {
        "raw_phrase": "skinless chicken thighs",
        "standardized_item": "chicken thighs",
        "quantity": 2.0,
        "unit": "lbs",
    }
    candidates = [
        {"corgis_description": "Chicken thigh, skin not eaten", "confidence_score": 0.90, "source": "corgis"},
        {"corgis_description": "Chicken thigh, skin eaten", "confidence_score": 0.90, "source": "corgis"},
        {"corgis_description": "Chicken leg", "confidence_score": 0.60, "source": "corgis"},
    ]
    inputs = iter(["4", "Chicken Thigh", "4", "skinless chicken thigh", "1"])
    parsed_items = [
        SimpleNamespace(raw_phrase="Chicken Thigh", standardized_item="chicken thigh", quantity=2.0, unit="lbs"),
        SimpleNamespace(raw_phrase="skinless chicken thigh", standardized_item="skinless chicken thigh", quantity=2.0, unit="lbs"),
    ]

    monkeypatch.setattr(server, "get_food_match_candidates", lambda *args, **kwargs: candidates)
    monkeypatch.setattr("builtins.input", lambda _prompt: next(inputs))
    monkeypatch.setattr(server, "parse_ingredients", lambda _text: [parsed_items.pop(0)])
    monkeypatch.setattr(
        server,
        "get_ingredient_metadata",
        lambda item: {
            "raw_phrase": item.raw_phrase,
            "standardized_item": item.standardized_item,
            "quantity": item.quantity,
            "unit": item.unit,
        },
    )

    resolved = server._review_uncertain_item(meta)

    assert resolved["corgis_description"] == "Chicken thigh, skin not eaten"
    assert resolved["should_auto_save"] is True
