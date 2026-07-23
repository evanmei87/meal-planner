import json
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tools.exercise_presets import apply_presets_to_week, load_presets, save_presets, set_preset


def test_load_presets_missing_file_returns_empty_presets(tmp_path):
    presets = load_presets(tmp_path / "missing.json")
    assert presets == {"presets": {}}


def test_load_presets_empty_file_returns_empty_presets(tmp_path):
    presets_file = tmp_path / "empty.json"
    presets_file.write_text("")

    presets = load_presets(presets_file)
    assert presets == {"presets": {}}


def test_save_presets_then_load_round_trips(tmp_path):
    presets_file = tmp_path / "exercise_presets.json"
    data = {"presets": {"Monday": [{"type": "running", "distance_miles": 3.1, "duration_minutes": 28}]}}

    assert save_presets(presets_file, data) is True
    assert json.loads(presets_file.read_text()) == data


def test_set_preset_stores_stripped_exercise_fields():
    data = {"presets": {}}
    exercises = [{
        "id": "should-be-stripped",
        "date": "2026-06-22",
        "type": "running",
        "distance_miles": 3.1,
        "duration_minutes": 28,
        "sets": None,
        "reps": None,
        "calories": 999,
        "notes": "easy run",
    }]

    result = set_preset(data, "Monday", exercises)

    assert result == [{
        "type": "running",
        "distance_miles": 3.1,
        "duration_minutes": 28,
        "sets": None,
        "reps": None,
        "notes": "easy run",
    }]
    assert data["presets"]["Monday"] == result


def test_set_preset_overwrites_existing_preset_for_day():
    data = {"presets": {"Monday": [{"type": "running", "distance_miles": 1.0, "duration_minutes": 10,
                                     "sets": None, "reps": None, "notes": None}]}}

    set_preset(data, "Monday", [{"type": "walking", "distance_miles": 2.0, "duration_minutes": 30}])

    assert data["presets"]["Monday"] == [{
        "type": "walking",
        "distance_miles": 2.0,
        "duration_minutes": 30,
        "sets": None,
        "reps": None,
        "notes": None,
    }]


def test_apply_presets_to_week_fills_empty_day():
    week_days = [{
        "date": "2026-06-22",
        "day_name": "Monday",
        "exercises": [],
        "total_calories": 0,
    }]
    presets = {"presets": {"Monday": [{
        "type": "running", "distance_miles": 3.1, "duration_minutes": 28,
        "sets": None, "reps": None, "notes": None,
    }]}}

    with patch('tools.exercise_presets.estimate_calories', return_value=300):
        result = apply_presets_to_week(week_days, presets)

    assert len(result[0]["exercises"]) == 1
    filled = result[0]["exercises"][0]
    assert filled["type"] == "running"
    assert filled["distance_miles"] == 3.1
    assert filled["calories"] == 300
    assert filled["id"]
    assert result[0]["total_calories"] == 300


def test_apply_presets_to_week_leaves_day_with_existing_exercises_untouched():
    existing_exercise = {"id": "abc123", "type": "running", "distance_miles": 5.0,
                          "duration_minutes": 45, "calories": 500, "notes": None}
    week_days = [{
        "date": "2026-06-22",
        "day_name": "Monday",
        "exercises": [existing_exercise],
        "total_calories": 500,
    }]
    presets = {"presets": {"Monday": [{
        "type": "walking", "distance_miles": 2.0, "duration_minutes": 30,
        "sets": None, "reps": None, "notes": None,
    }]}}

    result = apply_presets_to_week(week_days, presets)

    assert result[0]["exercises"] == [existing_exercise]
    assert result[0]["total_calories"] == 500


def test_apply_presets_to_week_leaves_day_empty_when_no_preset_for_that_day():
    week_days = [{
        "date": "2026-06-22",
        "day_name": "Monday",
        "exercises": [],
        "total_calories": 0,
    }]

    result = apply_presets_to_week(week_days, {"presets": {}})

    assert result[0]["exercises"] == []
    assert result[0]["total_calories"] == 0


def test_apply_presets_to_week_generates_distinct_ids_for_multiple_exercises():
    week_days = [{
        "date": "2026-06-22",
        "day_name": "Monday",
        "exercises": [],
        "total_calories": 0,
    }]
    presets = {"presets": {"Monday": [
        {"type": "running", "distance_miles": 3.1, "duration_minutes": 28, "sets": None, "reps": None, "notes": None},
        {"type": "strength", "distance_miles": None, "duration_minutes": 45, "sets": 3, "reps": 10, "notes": None},
    ]}}

    result = apply_presets_to_week(week_days, presets)

    ids = [exercise["id"] for exercise in result[0]["exercises"]]
    assert len(ids) == 2
    assert len(set(ids)) == 2
