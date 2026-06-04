import pytest
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tools.generate_plan import (
    load_state,
    save_state,
    get_days_to_generate,
    get_next_day,
    parse_user_updates,
    generate_day_plan,
    update_plan_in_state
)

def test_load_state_default(tmp_path):
    # If file doesn't exist, should return default state
    state_file = tmp_path / "nonexistent.json"
    state = load_state(str(state_file))
    assert state['current_day'] == 'Monday'
    assert state['plan_id'] == 'uuid-v4-placeholder'
    assert state['plan'] == []

def test_load_state_success(tmp_path):
    state_file = tmp_path / "state.json"
    test_data = {'current_day': 'Wednesday', 'plan_id': 'xyz'}
    state_file.write_text(json.dumps(test_data))
    
    state = load_state(str(state_file))
    assert state['current_day'] == 'Wednesday'
    assert state['plan_id'] == 'xyz'

def test_save_state(tmp_path):
    state_file = tmp_path / "state.json"
    state = {'current_day': 'Friday', 'plan_id': 'abc'}
    
    success = save_state(state, str(state_file))
    assert success is True
    assert state_file.exists()
    
    saved = json.loads(state_file.read_text())
    assert saved['current_day'] == 'Friday'

def test_get_days_to_generate():
    assert get_days_to_generate('Monday') == ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    assert get_days_to_generate('Friday') == ["Friday", "Saturday", "Sunday"]
    assert get_days_to_generate('Sunday') == ["Sunday"]
    assert get_days_to_generate('InvalidDay') == ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

def test_get_next_day():
    assert get_next_day('Monday') == 'Tuesday'
    assert get_next_day('Sunday') == 'Monday'

def test_parse_user_updates():
    # Ate out
    assert parse_user_updates("I ate out today")['ate_out'] is True
    assert parse_user_updates("I did not eat today")['ate_out'] is True
    assert parse_user_updates("regular day")['ate_out'] is False
    
    # Extra items
    assert parse_user_updates("have extra salmon")['extra_items'] == ['salmon']
    
    # Removed items
    assert parse_user_updates("remove rice")['removed_items'] == ['rice']

def test_generate_day_plan():
    state = {}
    static_data = {}
    updates = {'ate_out': False, 'extra_items': [], 'removed_items': []}
    
    # Friday is pre-long-run day -> 2700 kcal limit
    plan_friday = generate_day_plan(2500, 'Friday', state, static_data, updates)
    assert plan_friday['day'] == 'Friday'
    assert plan_friday['total_calories'] <= 2700
    
    # Monday -> 2250 kcal limit
    plan_monday = generate_day_plan(2500, 'Monday', state, static_data, updates)
    assert plan_monday['day'] == 'Monday'
    assert plan_monday['total_calories'] <= 2250

def test_update_plan_in_state():
    state = {
        'plan': [],
        'grocery_list': [],
        'missing_macros': []
    }
    day_plans = [
        {
            'day': 'Monday',
            'meals': [
                {'name': 'Oatmeal with Berries', 'calories': 500, 'ingredients': ['Oatmeal', 'Mixed Berries']}
            ],
            'total_calories': 500
        }
    ]
    updates = {'ate_out': False}
    
    updated = update_plan_in_state(state, day_plans, ['Monday'], updates)
    # Check grocery list items are populated and correctly mapped
    items = [item['item'] for item in updated['grocery_list']]
    assert 'Oatmeal' in items
    assert 'Mixed Berries' in items
