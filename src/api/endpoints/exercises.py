import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from src.api.models import AddExerciseRequest, ExerciseItem, ExerciseWeekResponse
from src.tools.exercise_storage import add_exercise, get_week, load_schedule, save_schedule

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
    Add a running exercise to a given date.

    Args:
        request: AddExerciseRequest with date, distance, duration, and notes

    Returns:
        The created ExerciseItem. Calorie calculation is wired in by issue 03,
        so calories is always 0 here.

    Example:
        POST /exercises/
        {
            "date": "2026-06-22",
            "distance_miles": 3.1,
            "duration_minutes": 28
        }
    """
    try:
        schedule_path = Path(SCHEDULE_PATH)
        data = load_schedule(schedule_path)

        exercise = {
            "id": uuid.uuid4().hex,
            "type": "running",
            "distance_miles": request.distance_miles,
            "duration_minutes": request.duration_minutes,
            "calories": 0,
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
