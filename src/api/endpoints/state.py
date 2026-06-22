from fastapi import APIRouter, HTTPException
from pathlib import Path

from src.api.models import StateResponse, UpdateStateRequest
from src.tools.update_state import update_state

router = APIRouter(prefix="/state", tags=["State"])

STATE_PATH = Path(__file__).parent.parent.parent / 'state' / 'state.json'


@router.get("/", response_model=StateResponse)
async def get_state():
    """
    Get the current application state.
    
    Returns:
        StateResponse with current day, plan ID, plan, grocery list, and missing macros
    
    Example:
        GET /state
    """
    try:
        import json
        state_path = Path(STATE_PATH)
        if not state_path.exists():
            return StateResponse(
                current_day='Monday',
                plan_id='',
                plan=[],
                grocery_list=[],
                missing_macros=[],
                grocery_inventory=[],
                unmatched_groceries=[],
                inventory_usage={"used": [], "unused": [], "supplemental": []},
            )

        state = json.loads(state_path.read_text())

        return StateResponse(
            current_day=state.get('current_day', 'Monday'),
            plan_id=state.get('plan_id', 'unknown'),
            plan=state.get('plan', []),
            grocery_list=state.get('grocery_list', []),
            missing_macros=state.get('missing_macros', []),
            grocery_inventory=state.get('grocery_inventory', []),
            unmatched_groceries=state.get('unmatched_groceries', []),
            inventory_usage=state.get('inventory_usage', {"used": [], "unused": [], "supplemental": []})
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve state: {str(e)}")


@router.put("/", response_model=StateResponse)
async def update_state_endpoint(request: UpdateStateRequest):
    """
    Update the application state with new plan data.
    
    Args:
        request: UpdateStateRequest with optional plan, grocery_list, missing_macros, and current_day
    
    Returns:
        StateResponse with updated state
    
    Example:
        PUT /state
        {
            "current_day": "Tuesday",
            "plan": [...],
            "grocery_list": [...]
        }
    """
    try:
        import json
        state_path = Path(STATE_PATH)

        # Load existing state
        if state_path.exists():
            existing_state = json.loads(state_path.read_text())
        else:
            existing_state = {
                'current_day': 'Monday',
                'plan_id': 'uuid-v4-placeholder',
                'plan': [],
                'grocery_list': [],
                'missing_macros': [],
                'grocery_inventory': [],
                'unmatched_groceries': [],
                'inventory_usage': {'used': [], 'unused': [], 'supplemental': []}
            }

        # Build update data
        update_data = {}
        if request.plan is not None:
            update_data['plan'] = [p.dict() if hasattr(p, 'dict') else p for p in request.plan]
        if request.grocery_list is not None:
            update_data['grocery_list'] = [g.dict() if hasattr(g, 'dict') else g for g in request.grocery_list]
        if request.missing_macros is not None:
            update_data['missing_macros'] = request.missing_macros
        if request.current_day is not None:
            update_data['current_day'] = request.current_day
        if request.grocery_inventory is not None:
            update_data['grocery_inventory'] = request.grocery_inventory
        if request.unmatched_groceries is not None:
            update_data['unmatched_groceries'] = request.unmatched_groceries
        if request.inventory_usage is not None:
            update_data['inventory_usage'] = request.inventory_usage

        # Update state using the tool
        success = update_state(str(state_path), update_data)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to update state")

        # Merge updates into the in-memory state to build the response
        merged_state = {**existing_state, **update_data}

        return StateResponse(
            current_day=merged_state.get('current_day', 'Monday'),
            plan_id=merged_state.get('plan_id', 'unknown'),
            plan=merged_state.get('plan', []),
            grocery_list=merged_state.get('grocery_list', []),
            missing_macros=merged_state.get('missing_macros', []),
            grocery_inventory=merged_state.get('grocery_inventory', []),
            unmatched_groceries=merged_state.get('unmatched_groceries', []),
            inventory_usage=merged_state.get('inventory_usage', {"used": [], "unused": [], "supplemental": []})
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update state: {str(e)}")
