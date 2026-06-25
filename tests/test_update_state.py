import pytest
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tools.update_state import update_state

def test_update_state_success(tmp_path):
    state_file = tmp_path / "state.json"
    
    # Initialize with default structure or let it create one
    initial_data = {
        'current_day': 'Monday',
        'plan_id': 'test-uuid-123',
        'plan': [],
        'grocery_list': [],
        'missing_macros': []
    }
    state_file.write_text(json.dumps(initial_data))
    
    updated_plan = {
        'current_day': 'Tuesday',
        'plan': [{'day': 'Tuesday', 'meals': []}],
        'grocery_list': [{'item': 'Apples', 'quantity': 5, 'unit': 'count', 'category': 'Fruit'}],
        'missing_macros': ['Quinoa']
    }
    
    success = update_state(str(state_file), updated_plan)
    assert success is True
    
    # Read and assert
    saved_state = json.loads(state_file.read_text())
    assert saved_state['current_day'] == 'Tuesday'
    assert saved_state['plan'] == [{'day': 'Tuesday', 'meals': []}]
    assert saved_state['grocery_list'] == [{'item': 'Apples', 'quantity': 5, 'unit': 'count', 'category': 'Fruit'}]
    assert saved_state['missing_macros'] == ['Quinoa']

def test_update_state_creates_file_if_not_exists(tmp_path):
    state_file = tmp_path / "new_state.json"
    assert not state_file.exists()
    
    updated_plan = {
        'current_day': 'Wednesday',
        'plan': [{'day': 'Wednesday', 'meals': []}]
    }
    
    success = update_state(str(state_file), updated_plan)
    assert success is True
    assert state_file.exists()
    
    saved_state = json.loads(state_file.read_text())
    assert saved_state['current_day'] == 'Wednesday'
    assert saved_state['plan'] == [{'day': 'Wednesday', 'meals': []}]
    assert saved_state['grocery_list'] == []

def test_update_state_persists_preferences(tmp_path):
    state_file = tmp_path / "state.json"
    state_file.write_text(json.dumps({'current_day': 'Monday', 'plan': [], 'grocery_list': [], 'missing_macros': []}))

    success = update_state(str(state_file), {'preferences': 'no salmon'})
    assert success is True

    saved = json.loads(state_file.read_text())
    assert saved['preferences'] == 'no salmon'


def test_update_state_preserves_existing_preferences_when_not_in_update(tmp_path):
    state_file = tmp_path / "state.json"
    state_file.write_text(json.dumps({'current_day': 'Monday', 'plan': [], 'grocery_list': [], 'missing_macros': [], 'preferences': 'no chicken'}))

    update_state(str(state_file), {'current_day': 'Tuesday'})

    saved = json.loads(state_file.read_text())
    assert saved['preferences'] == 'no chicken'


def test_update_state_persists_normalized_exclusions(tmp_path):
    state_file = tmp_path / "state.json"
    state_file.write_text(json.dumps({'current_day': 'Monday', 'plan': [], 'grocery_list': [], 'missing_macros': []}))

    success = update_state(str(state_file), {'normalized_exclusions': ['salmon', 'oatmeal']})
    assert success is True

    saved = json.loads(state_file.read_text())
    assert saved['normalized_exclusions'] == ['salmon', 'oatmeal']


def test_update_state_failure():
    # Try to write to an invalid path
    success = update_state('/nonexistent/directory/structure/state.json', {})
    assert success is False
