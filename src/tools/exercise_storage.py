import json
from datetime import datetime, timedelta
from pathlib import Path


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
