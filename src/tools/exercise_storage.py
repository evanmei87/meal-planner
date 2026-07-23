import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


def load_schedule(path: Path) -> dict:
    """
    Load the exercise schedule from disk.

    Args:
        path: Path to exercise_schedule.json

    Returns:
        Dict with a "days" key mapping ISO date -> day entry. Returns
        {"days": {}} if the file is missing or empty.
    """
    if not path.exists():
        return {"days": {}}

    content = path.read_text()
    if not content.strip():
        return {"days": {}}

    return json.loads(content)


def save_schedule(path: Path, data: dict) -> bool:
    """
    Write the exercise schedule to disk.

    Args:
        path: Path to exercise_schedule.json
        data: Schedule data to persist

    Returns:
        True if successful, False otherwise
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2))
        return True
    except Exception:
        return False


def _empty_day(date: str) -> dict:
    return {
        "date": date,
        "day_name": datetime.fromisoformat(date).strftime("%A"),
        "exercises": [],
        "total_calories": 0,
    }


def get_week(data: dict, week_start: str) -> list[dict]:
    """
    Build the 7 days of a week starting at week_start (Monday).

    Args:
        data: Schedule data as returned by load_schedule
        week_start: ISO date of the Monday to start the week from

    Returns:
        List of 7 day dicts shaped like ExerciseDayPlan, in date order.
        Dates not present in storage are returned as empty days.
        total_calories is recomputed from each day's exercises so it
        never drifts from the stored per-exercise values.
    """
    days = data.get("days", {})
    start = datetime.fromisoformat(week_start)

    week = []
    for offset in range(7):
        date = (start + timedelta(days=offset)).strftime("%Y-%m-%d")
        day = days[date] if date in days else _empty_day(date)
        day["total_calories"] = sum(exercise.get("calories", 0) for exercise in day["exercises"])
        week.append(day)

    return week


def add_exercise(data: dict, date: str, exercise: dict) -> dict:
    """
    Append an exercise to the given date, creating the day if needed.

    Args:
        data: Schedule data as returned by load_schedule (mutated in place)
        date: ISO date to add the exercise to
        exercise: Exercise dict to append

    Returns:
        The appended exercise dict
    """
    days = data.setdefault("days", {})
    if date not in days:
        days[date] = _empty_day(date)

    days[date]["exercises"].append(exercise)
    return exercise


def find_exercise_date(data: dict, exercise_id: str) -> Optional[str]:
    """
    Find the date of the day entry that contains the given exercise.

    Args:
        data: Schedule data as returned by load_schedule
        exercise_id: id of the exercise to look for

    Returns:
        The ISO date string containing that exercise, or None if not found.
    """
    for date, day in data.get("days", {}).items():
        if any(exercise["id"] == exercise_id for exercise in day["exercises"]):
            return date
    return None


def get_exercise(data: dict, exercise_id: str) -> Optional[dict]:
    """
    Find the stored exercise dict with the given id.

    Args:
        data: Schedule data as returned by load_schedule
        exercise_id: id of the exercise to look for

    Returns:
        The exercise dict, or None if no exercise with that id exists.
    """
    for day in data.get("days", {}).values():
        for exercise in day["exercises"]:
            if exercise["id"] == exercise_id:
                return exercise
    return None


def update_exercise(data: dict, exercise_id: str, updates: dict) -> Optional[dict]:
    """
    Apply updates to an existing exercise, in place.

    Args:
        data: Schedule data as returned by load_schedule (mutated in place)
        exercise_id: id of the exercise to update
        updates: Fields to merge into the exercise dict

    Returns:
        The updated exercise dict, or None if no exercise with that id exists.
    """
    date = find_exercise_date(data, exercise_id)
    if date is None:
        return None

    exercises = data["days"][date]["exercises"]
    for exercise in exercises:
        if exercise["id"] == exercise_id:
            exercise.update(updates)
            return exercise
    return None


def reorder_exercises(data: dict, date: str, ordered_ids: list[str]) -> bool:
    """
    Set each exercise's order field to match its index in ordered_ids.

    Args:
        data: Schedule data as returned by load_schedule (mutated in place)
        date: ISO date of the day whose exercises to reorder
        ordered_ids: Exercise ids in the desired display order

    Returns:
        True if the date has a day entry in storage, False otherwise.
    """
    day = data.get("days", {}).get(date)
    if day is None:
        return False

    index_by_id = {exercise_id: index for index, exercise_id in enumerate(ordered_ids)}
    for exercise in day["exercises"]:
        if exercise["id"] in index_by_id:
            exercise["order"] = index_by_id[exercise["id"]]
    return True


def delete_exercise(data: dict, exercise_id: str) -> bool:
    """
    Remove an exercise by id.

    Args:
        data: Schedule data as returned by load_schedule (mutated in place)
        exercise_id: id of the exercise to remove

    Returns:
        True if the exercise was found and removed, False otherwise.
    """
    date = find_exercise_date(data, exercise_id)
    if date is None:
        return False

    exercises = data["days"][date]["exercises"]
    data["days"][date]["exercises"] = [e for e in exercises if e["id"] != exercise_id]
    return True
