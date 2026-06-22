from fastapi import APIRouter, HTTPException, Depends
from pathlib import Path
from typing import List

from src.api.models import MealPlanRequest, MealPlanResponse, DayPlan
from src.tools.generate_plan import generate_meal_plan_from_request
from src.tools.update_state import update_state

router = APIRouter(prefix="/plan", tags=["Meal Plan"])

STATE_PATH = Path(__file__).parent.parent.parent / 'state' / 'state.json'


@router.post("/generate", response_model=MealPlanResponse)
async def generate_plan(request: MealPlanRequest):
    """
    Generate a meal plan based on the request parameters.
    
    Args:
        request: MealPlanRequest with days and optional preferences
    
    Returns:
        MealPlanResponse with generated plan and grocery list
    
    Example:
        POST /plan/generate
        {
            "days": ["Monday", "Tuesday"],
            "preferences": "ate out yesterday"
        }
    """
    try:
        request_data = {
            'days': request.days,
            'preferences': request.preferences
        }
        result = generate_meal_plan_from_request(str(STATE_PATH), request_data)
        return MealPlanResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate meal plan: {str(e)}")


@router.get("/{day}", response_model=DayPlan)
async def get_plan_for_day(day: str):
    """
    Get the meal plan for a specific day.
    
    Args:
        day: Day name (e.g., "Monday", "Tuesday")
    
    Returns:
        DayPlan with meals and nutritional information for the specified day
    
    Example:
        GET /plan/Monday
    """
    try:
        import json
        state_path = Path(STATE_PATH)
        if not state_path.exists():
            raise HTTPException(status_code=404, detail="State file not found")

        state = json.loads(state_path.read_text())
        plan = state.get('plan', [])

        # Find the plan for the requested day
        day_plan = next((p for p in plan if p.get('day') == day), None)

        if not day_plan:
            raise HTTPException(status_code=404, detail=f"No plan found for day: {day}")

        return DayPlan(**day_plan)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve plan: {str(e)}")


@router.get("/", response_model=MealPlanResponse)
async def get_current_plan():
    """
    Get the current complete meal plan.
    
    Returns:
        MealPlanResponse with all days, grocery list, and status
    
    Example:
        GET /plan
    """
    try:
        import json
        state_path = Path(STATE_PATH)
        if not state_path.exists():
            return MealPlanResponse(plan_id='', plan=[], grocery_list=[], status='success')

        state = json.loads(state_path.read_text())

        return MealPlanResponse(
            plan_id=state.get('plan_id', ''),
            plan=state.get('plan', []),
            grocery_list=state.get('grocery_list', []),
            status='success'
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve plan: {str(e)}")
