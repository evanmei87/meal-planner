import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tools import food_processor as fp


def test_get_food_match_candidates_returns_ranked_matches(monkeypatch):
    monkeypatch.setattr(
        fp,
        "_FOOD_DB",
        [
            {"Description": "Greek yogurt", "Category": "Dairy", "Nutrient Data Bank Number": "1"},
            {"Description": "Blueberries, raw", "Category": "Fruit", "Nutrient Data Bank Number": "2"},
            {"Description": "Breakfast tart", "Category": "Dessert", "Nutrient Data Bank Number": "3"},
        ],
    )

    candidates = fp.get_food_match_candidates("greek non fat yogurt", "greek non fat yogurt", limit=2)

    assert len(candidates) == 2
    assert candidates[0]["corgis_description"] == "Greek yogurt"
    assert candidates[0]["confidence_score"] >= candidates[1]["confidence_score"]


def test_match_food_item_returns_best_candidate(monkeypatch):
    monkeypatch.setattr(
        fp,
        "_FOOD_DB",
        [
            {"Description": "Greek yogurt", "Category": "Dairy", "Nutrient Data Bank Number": "1"},
            {"Description": "Breakfast tart", "Category": "Dessert", "Nutrient Data Bank Number": "3"},
        ],
    )

    match = fp.match_food_item("greek non fat yogurt", "greek non fat yogurt")

    assert match is not None
    assert match["corgis_description"] == "Greek yogurt"


def test_greek_nonfat_yogurt_matches_real_corgis_row():
    candidates = fp.get_food_match_candidates("greek yogurt non fat", "greek yogurt non fat", limit=3)

    assert candidates
    assert candidates[0]["corgis_description"] == "Yogurt, Greek, nonfat milk, plain"
    assert candidates[0]["confidence_level"] == "high"


def test_skinless_chicken_thighs_prefers_skin_not_eaten_real_corgis_row():
    candidates = fp.get_food_match_candidates(
        "2 pounds of skinless chicken thighs",
        "chicken thighs",
        limit=3,
    )

    assert candidates
    assert "Chicken thigh" in candidates[0]["corgis_description"]
    assert "skin not eaten" in candidates[0]["corgis_description"]
    assert candidates[0]["confidence_level"] == "high"


def test_unrelated_sequence_similarity_is_capped(monkeypatch):
    monkeypatch.setattr(
        fp,
        "_FOOD_DB",
        [
            {"Description": "Greyhound", "Category": "Beverages", "Nutrient Data Bank Number": "1"},
            {"Description": "Yogurt, Greek, nonfat milk, plain", "Category": "Yogurt", "Nutrient Data Bank Number": "2"},
        ],
    )

    candidates = fp.get_food_match_candidates("greek non fat yogurt", "greek non fat yogurt", limit=2)

    assert candidates[0]["corgis_description"] == "Yogurt, Greek, nonfat milk, plain"
    assert candidates[0]["confidence_score"] > candidates[1]["confidence_score"]
