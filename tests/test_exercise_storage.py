import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tools.exercise_storage import add_exercise, get_week, load_schedule, save_schedule


def test_load_schedule_missing_file_returns_empty_days(tmp_path):
    schedule = load_schedule(tmp_path / "missing.json")
    assert schedule == {"days": {}}


def test_load_schedule_empty_file_returns_empty_days(tmp_path):
    schedule_file = tmp_path / "empty.json"
    schedule_file.write_text("")

    schedule = load_schedule(schedule_file)
    assert schedule == {"days": {}}


def test_save_schedule_then_load_round_trips(tmp_path):
    schedule_file = tmp_path / "exercise_schedule.json"
    data = {"days": {"2026-06-22": {"date": "2026-06-22", "exercises": []}}}

    assert save_schedule(schedule_file, data) is True
    assert json.loads(schedule_file.read_text()) == data


def test_get_week_empty_returns_seven_correctly_dated_days():
    week = get_week({"days": {}}, "2026-06-22")

    assert len(week) == 7
    assert [day["date"] for day in week] == [
        "2026-06-22", "2026-06-23", "2026-06-24", "2026-06-25",
        "2026-06-26", "2026-06-27", "2026-06-28",
    ]
    assert week[0]["day_name"] == "Monday"
    assert week[6]["day_name"] == "Sunday"
    assert all(day["exercises"] == [] and day["total_calories"] == 0 for day in week)


def test_get_week_includes_stored_day_entry():
    stored_day = {
        "date": "2026-06-23",
        "day_name": "Tuesday",
        "exercises": [{"id": "abc", "type": "running"}],
        "total_calories": 0,
    }
    week = get_week({"days": {"2026-06-23": stored_day}}, "2026-06-22")

    assert week[1] == stored_day


def test_add_exercise_creates_date_entry_and_appends():
    data = {"days": {}}
    exercise = {"id": "abc123", "type": "running", "distance_miles": 3.1, "duration_minutes": 28, "calories": 0}

    result = add_exercise(data, "2026-06-22", exercise)

    assert result == exercise
    assert data["days"]["2026-06-22"]["day_name"] == "Monday"
    assert data["days"]["2026-06-22"]["exercises"] == [exercise]


def test_add_exercise_appends_to_existing_date():
    first = {"id": "one", "type": "running"}
    second = {"id": "two", "type": "running"}
    data = {"days": {}}

    add_exercise(data, "2026-06-22", first)
    add_exercise(data, "2026-06-22", second)

    assert data["days"]["2026-06-22"]["exercises"] == [first, second]
