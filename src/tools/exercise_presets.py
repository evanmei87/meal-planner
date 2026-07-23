import json
import uuid
from pathlib import Path

from src.tools.calculate_exercise_calories import estimate_calories

PRESET_FIELDS = ("type", "distance_miles", "duration_minutes", "sets", "reps", "notes")


def load_presets(path: Path) -> dict:
    """
    Load exercise presets from disk.

    Args:
        path: Path to exercise_presets.json

    Returns:
        Dict with a "presets" key mapping day-of-week name -> list of
        preset exercises. Returns {"presets": {}} if the file is missing
        or empty.
    """
    if not path.exists():
        return {"presets": {}}

    content = path.read_text()
    if not content.strip():
        return {"presets": {}}

    return json.loads(content)


def save_presets(path: Path, data: dict) -> bool:
    """
    Write exercise presets to disk.

    Args:
        path: Path to exercise_presets.json
        data: Preset data to persist

    Returns:
        True if successful, False otherwise
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2))
        return True
    except Exception:
        return False


def set_preset(data: dict, day_name: str, exercises: list[dict]) -> list[dict]:
    """
    Overwrite the preset for a day-of-week with the given exercises.

    Args:
        data: Preset data as returned by load_presets (mutated in place)
        day_name: Day-of-week name (e.g. "Monday")
        exercises: List of exercise dicts. Only type/distance_miles/
                   duration_minutes/sets/reps/notes are kept — id,
                   calories, and date are stripped, since a preset is a
                   reusable template rather than a scheduled instance.

    Returns:
        The stored list of preset exercises.
    """
    presets = data.setdefault("presets", {})
    stripped = [{field: exercise.get(field) for field in PRESET_FIELDS} for exercise in exercises]
    presets[day_name] = stripped
    return stripped


def apply_presets_to_week(week_days: list[dict], presets: dict, stored_dates: set[str]) -> list[dict]:
    """
    Fill empty days in a week with fresh copies of that day's preset.

    Args:
        week_days: List of day dicts as returned by exercise_storage.get_week
                   (mutated in place)
        presets: Preset data as returned by load_presets
        stored_dates: Dates that already have an entry in the schedule,
                       even an empty one. A stored date means the user has
                       already taken that day over — either by adding
                       exercises, or by deleting everything a preset once
                       filled in — so it must never be refilled.

    Returns:
        The same list of day dicts. Days with no entry in storage are
        filled from presets[day["day_name"]] with new ids and freshly
        computed calories. Days already in storage are left untouched —
        a preset never overwrites real data, and never reclaims a day the
        user has explicitly emptied.
    """
    day_presets = presets.get("presets", {})

    for day in week_days:
        if day["date"] in stored_dates:
            continue

        preset_exercises = day_presets.get(day["day_name"], [])
        day["exercises"] = [
            {
                **exercise,
                "id": uuid.uuid4().hex,
                "calories": estimate_calories(
                    exercise["type"], exercise.get("distance_miles"), exercise["duration_minutes"]
                ),
            }
            for exercise in preset_exercises
        ]
        day["total_calories"] = sum(exercise["calories"] for exercise in day["exercises"])

    return week_days
