import json
from pathlib import Path


def update_state(state_path: str, updated_plan: dict) -> bool:
    """
    Write the generated plan and grocery list back to state.json.

    Args:
        state_path: Path to state.json
        updated_plan: Dictionary with updated plan data

    Returns:
        True if successful, False otherwise
    """
    state_file = Path(state_path)

    try:
        # Load existing state
        if state_file.exists():
            existing_state = json.loads(state_file.read_text())
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

        # Update with new plan
        existing_state['plan'] = updated_plan.get('plan', existing_state['plan'])
        existing_state['grocery_list'] = updated_plan.get('grocery_list', existing_state['grocery_list'])
        existing_state['missing_macros'] = updated_plan.get('missing_macros', existing_state['missing_macros'])
        existing_state['current_day'] = updated_plan.get('current_day', existing_state['current_day'])
        if 'grocery_inventory' in updated_plan:
            existing_state['grocery_inventory'] = updated_plan['grocery_inventory']
        if 'unmatched_groceries' in updated_plan:
            existing_state['unmatched_groceries'] = updated_plan['unmatched_groceries']
        if 'inventory_usage' in updated_plan:
            existing_state['inventory_usage'] = updated_plan['inventory_usage']
        if 'preferences' in updated_plan:
            existing_state['preferences'] = updated_plan['preferences']
        if 'normalized_exclusions' in updated_plan:
            existing_state['normalized_exclusions'] = updated_plan['normalized_exclusions']

        # Save updated state
        state_file.write_text(json.dumps(existing_state, indent=2))

        return True
    except Exception as e:
        print(f"Error updating state: {e}")
        return False
