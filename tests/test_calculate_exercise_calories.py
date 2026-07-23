import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tools.calculate_exercise_calories import estimate_running_calories


def test_estimate_running_calories_uses_weight_from_user_stats(monkeypatch):
    monkeypatch.setattr(
        "tools.calculate_exercise_calories.get_user_stats",
        lambda: {"weight_kg": 70.0},
    )

    assert estimate_running_calories(5) == round(70.0 * 5 * 1.668)
