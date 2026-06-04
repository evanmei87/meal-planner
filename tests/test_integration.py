import pytest
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tools.generate_plan import generate_meal_plan, load_state

def test_generate_meal_plan_integration(tmp_path):
    state_file = tmp_path / "state.json"
    
    # Write a clean starting state
    initial_state = {
        'current_day': 'Monday',
        'plan_id': 'test-uuid-999',
        'plan': [],
        'grocery_list': [],
        'missing_macros': []
    }
    state_file.write_text(json.dumps(initial_state))
    
    # Run the generator
    plan_markdown = generate_meal_plan(str(state_file), "Generate my weekly plan")
    
    # Verify it returns a formatted markdown block
    assert plan_markdown.startswith("```")
    assert plan_markdown.endswith("```")
    assert "Meal Plan" in plan_markdown
    assert "Grocery List" in plan_markdown
    
    # Verify the state was written back
    updated_state = load_state(str(state_file))
    assert len(updated_state['plan']) > 0
    assert len(updated_state['grocery_list']) > 0
    
    # Verify that plan elements conform to structure
    for day_plan in updated_state['plan']:
        assert 'day' in day_plan
        assert 'meals' in day_plan
        assert 'total_calories' in day_plan
        # Verify caloric cap adherence (core meals are always included, can go slightly over 2250)
        limit = 2700 if 'friday' in day_plan['day'].lower() else 2300
        assert day_plan['total_calories'] <= limit
