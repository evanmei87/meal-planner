import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tools.exercise_storage import (
    add_exercise,
    delete_exercise,
    find_exercise_date,
    get_month,
    get_week,
    load_schedule,
    reorder_exercises,
    save_schedule,
    update_exercise,
)


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


def test_get_month_returns_correct_number_of_days_for_30_day_month():
    month = get_month({"days": {}}, "2026-06")

    assert len(month) == 30
    assert month[0]["date"] == "2026-06-01"
    assert month[-1]["date"] == "2026-06-30"
    assert all(day["exercises"] == [] and day["total_calories"] == 0 for day in month)


def test_get_month_returns_correct_number_of_days_for_31_day_month():
    month = get_month({"days": {}}, "2026-07")

    assert len(month) == 31
    assert month[0]["date"] == "2026-07-01"
    assert month[-1]["date"] == "2026-07-31"


def test_get_month_returns_29_days_for_leap_year_february():
    month = get_month({"days": {}}, "2028-02")

    assert len(month) == 29
    assert month[-1]["date"] == "2028-02-29"


def test_get_month_returns_28_days_for_non_leap_year_february():
    month = get_month({"days": {}}, "2026-02")

    assert len(month) == 28
    assert month[-1]["date"] == "2026-02-28"


def test_get_month_includes_stored_day_entry():
    stored_day = {
        "date": "2026-06-15",
        "day_name": "Monday",
        "exercises": [{"id": "abc", "type": "running"}],
        "total_calories": 0,
    }
    month = get_month({"days": {"2026-06-15": stored_day}}, "2026-06")

    assert month[14] == stored_day


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


def test_find_exercise_date_returns_date_containing_exercise():
    data = {"days": {}}
    add_exercise(data, "2026-06-22", {"id": "abc123", "type": "running"})

    assert find_exercise_date(data, "abc123") == "2026-06-22"


def test_find_exercise_date_returns_none_when_not_found():
    data = {"days": {}}
    add_exercise(data, "2026-06-22", {"id": "abc123", "type": "running"})

    assert find_exercise_date(data, "unknown-id") is None


def test_update_exercise_applies_updates_and_returns_exercise():
    data = {"days": {}}
    add_exercise(data, "2026-06-22", {
        "id": "abc123", "type": "running", "distance_miles": 3.1, "duration_minutes": 28, "calories": 300, "notes": None,
    })

    updated = update_exercise(data, "abc123", {"distance_miles": 5.0, "duration_minutes": 45, "calories": 500})

    assert updated == {
        "id": "abc123", "type": "running", "distance_miles": 5.0, "duration_minutes": 45, "calories": 500, "notes": None,
    }
    assert data["days"]["2026-06-22"]["exercises"][0] == updated


def test_update_exercise_returns_none_when_not_found():
    data = {"days": {}}
    add_exercise(data, "2026-06-22", {"id": "abc123", "type": "running"})

    assert update_exercise(data, "unknown-id", {"distance_miles": 5.0}) is None


def test_delete_exercise_removes_and_returns_true():
    data = {"days": {}}
    add_exercise(data, "2026-06-22", {"id": "abc123", "type": "running"})

    assert delete_exercise(data, "abc123") is True
    assert data["days"]["2026-06-22"]["exercises"] == []


def test_delete_exercise_returns_false_when_not_found():
    data = {"days": {}}
    add_exercise(data, "2026-06-22", {"id": "abc123", "type": "running"})

    assert delete_exercise(data, "unknown-id") is False
    assert data["days"]["2026-06-22"]["exercises"] == [{"id": "abc123", "type": "running"}]


def test_reorder_exercises_sets_order_to_match_ordered_ids():
    data = {"days": {}}
    add_exercise(data, "2026-06-22", {"id": "one", "type": "running", "order": 0})
    add_exercise(data, "2026-06-22", {"id": "two", "type": "running", "order": 1})
    add_exercise(data, "2026-06-22", {"id": "three", "type": "running", "order": 2})

    assert reorder_exercises(data, "2026-06-22", ["three", "one", "two"]) is True

    exercises = data["days"]["2026-06-22"]["exercises"]
    assert {e["id"]: e["order"] for e in exercises} == {"three": 0, "one": 1, "two": 2}


def test_reorder_exercises_returns_false_when_date_not_found():
    data = {"days": {}}

    assert reorder_exercises(data, "2026-06-22", ["one", "two"]) is False
