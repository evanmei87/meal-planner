from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException

from src.api.models import ExercisePresetsResponse, PresetExerciseItem
from src.tools.exercise_presets import load_presets, save_presets, set_preset

router = APIRouter(prefix="/exercise-presets", tags=["Exercise Presets"])

PRESETS_PATH = Path(__file__).parent.parent.parent / 'state' / 'exercise_presets.json'


@router.post("/{day_name}", response_model=List[PresetExerciseItem])
async def set_preset_endpoint(day_name: str, request: List[PresetExerciseItem]):
    """
    Save a day-of-week's set of exercises as a reusable preset.

    Args:
        day_name: Day-of-week name to save the preset for (e.g. "Monday")
        request: List of exercises (type, distance/duration or sets/reps, notes)

    Returns:
        The saved list of preset exercises.

    Example:
        POST /exercise-presets/Monday
        [{"type": "running", "distance_miles": 3.1, "duration_minutes": 28}]
    """
    try:
        presets_path = Path(PRESETS_PATH)
        data = load_presets(presets_path)

        exercises = [exercise.model_dump() for exercise in request]
        saved = set_preset(data, day_name, exercises)

        if not save_presets(presets_path, data):
            raise HTTPException(status_code=500, detail="Failed to save preset")

        return [PresetExerciseItem(**exercise) for exercise in saved]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save preset: {str(e)}")


@router.get("/", response_model=ExercisePresetsResponse)
async def get_presets_endpoint():
    """
    Get the full presets map, keyed by day-of-week name.

    Returns:
        ExercisePresetsResponse with the presets map.

    Example:
        GET /exercise-presets/
    """
    try:
        data = load_presets(Path(PRESETS_PATH))
        return ExercisePresetsResponse(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve presets: {str(e)}")
