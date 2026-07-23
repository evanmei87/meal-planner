import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tools.calculate_exercise_calories import estimate_calories, estimate_running_calories


def test_estimate_running_calories_uses_weight_from_user_stats(monkeypatch):
    monkeypatch.setattr(
        "tools.calculate_exercise_calories.get_user_stats",
        lambda: {"weight_kg": 70.0},
    )

    assert estimate_running_calories(5) == round(70.0 * 5 * 1.668)


def test_estimate_calories_running_matches_distance_based_estimate(monkeypatch):
    monkeypatch.setattr(
        "tools.calculate_exercise_calories.get_user_stats",
        lambda: {"weight_kg": 70.0},
    )

    assert estimate_calories("running", 5, 45) == round(70.0 * 5 * 1.668)


def test_estimate_calories_walking_uses_met_formula(monkeypatch):
    monkeypatch.setattr(
        "tools.calculate_exercise_calories.get_user_stats",
        lambda: {"weight_kg": 70.0},
    )

    assert estimate_calories("walking", 2.0, 30) == round(3.5 * 70.0 * (30 / 60))


def test_estimate_calories_biking_uses_met_formula(monkeypatch):
    monkeypatch.setattr(
        "tools.calculate_exercise_calories.get_user_stats",
        lambda: {"weight_kg": 70.0},
    )

    assert estimate_calories("biking", 10.0, 40) == round(7.5 * 70.0 * (40 / 60))


def test_estimate_calories_swimming_uses_met_formula(monkeypatch):
    monkeypatch.setattr(
        "tools.calculate_exercise_calories.get_user_stats",
        lambda: {"weight_kg": 70.0},
    )

    assert estimate_calories("swimming", 1.0, 30) == round(6.0 * 70.0 * (30 / 60))


def test_estimate_calories_strength_uses_met_formula_and_ignores_distance(monkeypatch):
    monkeypatch.setattr(
        "tools.calculate_exercise_calories.get_user_stats",
        lambda: {"weight_kg": 70.0},
    )

    assert estimate_calories("strength", None, 45) == round(5.0 * 70.0 * (45 / 60))
