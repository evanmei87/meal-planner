import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from src.api.models import AddExerciseRequest, ExerciseItem, ExerciseWeekResponse, UpdateExerciseRequest
from src.tools.calculate_exercise_calories import estimate_calories
from src.tools.exercise_storage import (
    add_exercise,
    delete_exercise,
    find_exercise_date,
    get_week,
    load_schedule,
    save_schedule,
    update_exercise,
)

router = APIRouter(prefix="/exercises", tags=["Exercises"])

SCHEDULE_PATH = Path(__file__).parent.parent.parent / 'state' / 'exercise_schedule.json'


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
        ExerciseWeekResponse with 7 days, empty for dates with no exercises.

    Example:
        GET /exercises/?week_start=2026-06-22
    """
    try:
        if week_start is None:
            week_start = _current_week_start_est()

        data = load_schedule(Path(SCHEDULE_PATH))
        days = get_week(data, week_start)

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

        exercise = {
            "id": uuid.uuid4().hex,
            "type": request.type,
            "distance_miles": request.distance_miles,
            "duration_minutes": request.duration_minutes,
            "sets": request.sets,
            "reps": request.reps,
            "calories": estimate_calories(request.type, request.distance_miles, request.duration_minutes),
            "notes": request.notes,
        }
        add_exercise(data, request.date, exercise)

        if not save_schedule(schedule_path, data):
            raise HTTPException(status_code=500, detail="Failed to save exercise")

        return ExerciseItem(**exercise)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add exercise: {str(e)}")


@router.put("/{exercise_id}", response_model=ExerciseItem)
async def update_exercise_endpoint(exercise_id: str, request: UpdateExerciseRequest):
    """
    Update an existing exercise's type, distance/duration or sets/reps, and notes.

    The exercise stays on its existing day; moving it to a different day
    is out of scope (see issue #36).

    Args:
        exercise_id: id of the exercise to update
        request: UpdateExerciseRequest with type, distance/duration or
                 sets/reps, and notes

    Returns:
        The updated ExerciseItem, with calories recalculated for its type.

    Example:
        PUT /exercises/abc123
        {
            "type": "running",
            "distance_miles": 5.0,
            "duration_minutes": 45
        }
    """
    try:
        schedule_path = Path(SCHEDULE_PATH)
        data = load_schedule(schedule_path)

        if find_exercise_date(data, exercise_id) is None:
            raise HTTPException(status_code=404, detail="Exercise not found")

        updates = {
            "type": request.type,
            "distance_miles": request.distance_miles,
            "duration_minutes": request.duration_minutes,
            "sets": request.sets,
            "reps": request.reps,
            "calories": estimate_calories(request.type, request.distance_miles, request.duration_minutes),
            "notes": request.notes,
        }
        exercise = update_exercise(data, exercise_id, updates)

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
