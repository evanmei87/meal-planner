import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from src.api.models import (
    AddExerciseRequest,
    ExerciseItem,
    ExerciseWeekResponse,
    ReorderExercisesRequest,
    UpdateExerciseRequest,
    _require_fields_for_exercise_type,
)
from src.tools.calculate_exercise_calories import estimate_calories
from src.tools.exercise_presets import apply_presets_to_week, load_presets
from src.tools.exercise_storage import (
    add_exercise,
    delete_exercise,
    find_exercise_date,
    get_exercise,
    get_week,
    load_schedule,
    reorder_exercises,
    save_schedule,
    update_exercise,
)

router = APIRouter(prefix="/exercises", tags=["Exercises"])

SCHEDULE_PATH = Path(__file__).parent.parent.parent / 'state' / 'exercise_schedule.json'
PRESETS_PATH = Path(__file__).parent.parent.parent / 'state' / 'exercise_presets.json'


def _current_week_start_est() -> str:
    """Return the ISO date of the Monday of the current EST/EDT week."""
    est = timezone(timedelta(hours=-4))
    today = datetime.now(est)
    monday = today - timedelta(days=today.weekday())
    return monday.strftime('%Y-%m-%d')


@router.get("/", response_model=ExerciseWeekResponse)
async def get_exercise_week(
    week_start: Optional[str] = Query(None, description="ISO date of the Monday to start the week from")
):
    """
    Get a week's exercise schedule.

    Args:
        week_start: ISO date of the Monday to start the week from. Defaults
                    to the Monday of the current server week.

    Returns:
        ExerciseWeekResponse with 7 days. Days with no entry in storage
        are pre-filled from that day-of-week's saved preset, if any. A
        day filled this way is persisted immediately, so it behaves like
        any other real, editable/deletable data from then on — including
        staying empty on later requests if the user deletes everything
        the preset filled in.

    Example:
        GET /exercises/?week_start=2026-06-22
    """
    try:
        if week_start is None:
            week_start = _current_week_start_est()

        schedule_path = Path(SCHEDULE_PATH)
        data = load_schedule(schedule_path)
        days = get_week(data, week_start)
        stored_dates = set(data.get("days", {}).keys())

        presets = load_presets(Path(PRESETS_PATH))
        days = apply_presets_to_week(days, presets, stored_dates)

        newly_filled_days = [day for day in days if day["date"] not in stored_dates and day["exercises"]]
        if newly_filled_days:
            for day in newly_filled_days:
                data.setdefault("days", {})[day["date"]] = day
            save_schedule(schedule_path, data)

        return ExerciseWeekResponse(week_start=week_start, days=days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve exercise week: {str(e)}")


@router.post("/", response_model=ExerciseItem)
async def add_exercise_endpoint(request: AddExerciseRequest):
    """
    Add an exercise to a given date.

    Args:
        request: AddExerciseRequest with date, type, distance/duration or
                 sets/reps, and notes

    Returns:
        The created ExerciseItem, with calories estimated for its type.

    Example:
        POST /exercises/
        {
            "date": "2026-06-22",
            "type": "running",
            "distance_miles": 3.1,
            "duration_minutes": 28
        }
    """
    try:
        schedule_path = Path(SCHEDULE_PATH)
        data = load_schedule(schedule_path)

        existing_exercises = data.get("days", {}).get(request.date, {}).get("exercises", [])
        exercise = {
            "id": uuid.uuid4().hex,
            "type": request.type,
            "distance_miles": request.distance_miles,
            "duration_minutes": request.duration_minutes,
            "sets": request.sets,
            "reps": request.reps,
            "calories": estimate_calories(request.type, request.distance_miles, request.duration_minutes),
            "notes": request.notes,
            "order": len(existing_exercises),
        }
        add_exercise(data, request.date, exercise)

        if not save_schedule(schedule_path, data):
            raise HTTPException(status_code=500, detail="Failed to save exercise")

        return ExerciseItem(**exercise)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add exercise: {str(e)}")


@router.put("/reorder", status_code=204)
async def reorder_exercises_endpoint(request: ReorderExercisesRequest):
    """
    Persist a new within-day ordering for exercises.

    Registered ahead of PUT /{exercise_id} so "reorder" is never matched
    as an exercise id.

    Args:
        request: ReorderExercisesRequest with date and ordered_ids

    Example:
        PUT /exercises/reorder
        {"date": "2026-06-22", "ordered_ids": ["ex2", "ex1"]}
    """
    try:
        schedule_path = Path(SCHEDULE_PATH)
        data = load_schedule(schedule_path)

        if not reorder_exercises(data, request.date, request.ordered_ids):
            raise HTTPException(status_code=404, detail="Day not found")

        if not save_schedule(schedule_path, data):
            raise HTTPException(status_code=500, detail="Failed to save exercise order")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reorder exercises: {str(e)}")


@router.put("/{exercise_id}", response_model=ExerciseItem)
async def update_exercise_endpoint(exercise_id: str, request: UpdateExerciseRequest):
    """
    Update an existing exercise's type, distance/duration or sets/reps,
    and notes. Optionally moves it to a different day.

    Args:
        exercise_id: id of the exercise to update
        request: UpdateExerciseRequest with type, distance/duration or
                 sets/reps, notes, and optionally date (to move days) and
                 order (to persist within-day position)

    Returns:
        The updated ExerciseItem, with calories recalculated for its type.

    Example:
        PUT /exercises/abc123
        {
            "type": "running",
            "distance_miles": 5.0,
            "duration_minutes": 45,
            "date": "2026-06-24"
        }
    """
    try:
        schedule_path = Path(SCHEDULE_PATH)
        data = load_schedule(schedule_path)

        existing = get_exercise(data, exercise_id)
        if existing is None:
            raise HTTPException(status_code=404, detail="Exercise not found")

        # type is optional on the request so that omitting it preserves the
        # exercise's stored type instead of resetting it to "running". The
        # model can't validate this merged case itself, since it doesn't
        # know the stored type — do it here against the effective type.
        effective_type = request.type if request.type is not None else existing["type"]
        try:
            _require_fields_for_exercise_type(effective_type, request.distance_miles, request.sets, request.reps)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

        updates = {
            "type": effective_type,
            "distance_miles": request.distance_miles,
            "duration_minutes": request.duration_minutes,
            "sets": request.sets,
            "reps": request.reps,
            "calories": estimate_calories(effective_type, request.distance_miles, request.duration_minutes),
            "notes": request.notes,
        }
        if request.order is not None:
            updates["order"] = request.order
        exercise = update_exercise(data, exercise_id, updates)

        if request.date is not None:
            current_date = find_exercise_date(data, exercise_id)
            if current_date != request.date:
                delete_exercise(data, exercise_id)
                add_exercise(data, request.date, exercise)

        if not save_schedule(schedule_path, data):
            raise HTTPException(status_code=500, detail="Failed to save exercise")

        return ExerciseItem(**exercise)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update exercise: {str(e)}")


@router.delete("/{exercise_id}", status_code=204)
async def delete_exercise_endpoint(exercise_id: str):
    """
    Delete an exercise.

    Args:
        exercise_id: id of the exercise to delete

    Example:
        DELETE /exercises/abc123
    """
    try:
        schedule_path = Path(SCHEDULE_PATH)
        data = load_schedule(schedule_path)

        if not delete_exercise(data, exercise_id):
            raise HTTPException(status_code=404, detail="Exercise not found")

        if not save_schedule(schedule_path, data):
            raise HTTPException(status_code=500, detail="Failed to save exercise")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete exercise: {str(e)}")
