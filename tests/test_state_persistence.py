import pytest
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tools.update_state import update_state
from tools.generate_plan import load_state, save_state

class TestStatePersistence:
    """Tests to ensure state.json is updated correctly after generation."""
    
    def test_state_saved_after_generation(self):
        """Test that state is saved after meal plan generation."""
        state_path = 'src/state/state.json'
        
        # Load initial state
        state = load_state(state_path)
        initial_grocery = state['grocery_list']
        
        # Generate plan (this updates state)
        result = generate_meal_plan(state_path, 'Generate plan')
        
        # Load updated state
        updated_state = load_state(state_path)
        
        # Verify state was updated
        assert isinstance(updated_state['plan'], list)
        assert isinstance(updated_state['grocery_list'], list)
    
    def test_state_persists_across_calls(self):
        """Test that state persists across multiple calls."""
        state_path = 'src/state/state.json'
        
        # Call generate multiple times
        for i in range(3):
            result = generate_meal_plan(state_path, f'Generate plan {i}')
        
        # Verify state still exists and is valid JSON
        with open(state_path, 'r') as f:
            state = json.load(f)
        
        assert 'plan' in state
        assert 'grocery_list' in state
        assert 'current_day' in state
    
    def test_state_structure(self):
        """Test that state has correct structure."""
        state_path = 'src/state/state.json'
        
        state = load_state(state_path)
        
        # Verify required fields exist
        assert 'current_day' in state
        assert 'plan_id' in state
        assert 'plan' in state
        assert 'grocery_list' in state
        assert 'missing_macros' in state
    
    def test_save_state_success(self):
        """Test that save_state returns True on success."""
        state = {
            'current_day': 'Tuesday',
            'plan_id': 'test-uuid-123',
            'plan': [],
            'grocery_list': [],
            'missing_macros': []
        }
        
        success = save_state(state, 'src/state/state.json')
        
        assert success is True
    
    def test_save_state_failure(self):
        """Test that save_state returns False on failure."""
        # Try to save to non-existent path
        success = save_state({}, '/nonexistent/path/state.json')
        
        assert success is False
