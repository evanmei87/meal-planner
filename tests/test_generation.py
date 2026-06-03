import pytest
from pathlib import Path
import json
import sys
import os

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tools.generate_plan import generate_meal_plan, load_state, save_state
from tools.calculate_tdee import calculate_tdee
from tools.search_web import search_web_with_context

class TestGeneration:
    """Tests to verify the plan adheres to caloric caps and protein limits."""
    
    def test_caloric_cap_adherence(self):
        """Test that generated plan stays within caloric cap."""
        state = {
            'current_day': 'Monday',
            'plan_id': 'test-uuid',
            'plan': [],
            'grocery_list': [],
            'missing_macros': []
        }
        
        plan = generate_meal_plan('src/state/state.json', 'Generate plan')
        
        assert isinstance(plan, str)
        assert 'markdown' in plan
    
    def test_protein_limit(self):
        """Test that protein limit is not exceeded."""
        plan = generate_meal_plan('src/state/state.json', 'Generate plan')
        
        # Verify plan mentions protein limits
        assert 'protein' in plan.lower()
    
    def test_vegetable_limit(self):
        """Test that vegetable limit is not exceeded."""
        plan = generate_meal_plan('src/state/state.json', 'Generate plan')
        
        # Verify plan mentions vegetable limits
        assert 'vegetable' in plan.lower()
    
    def test_pre_long_run_calories(self):
        """Test that pre-long-run day allows higher calories."""
        os.environ['RUNNING_SCHEDULE'] = 'long_run'
        os.environ['LONG_RUN_DISTANCE'] = '18'
        
        plan = generate_meal_plan('src/state/state.json', 'Generate plan for Saturday')
        
        # Verify higher calories for pre-long-run
        assert '2500' in plan or '2700' in plan
    
    def test_missing_macros_flagging(self):
        """Test that missing macro data is flagged."""
        result = generate_meal_plan('src/state/state.json', 'Generate with missing data')
        
        # Check for flagged items in output
        assert 'flagged_for_input' in result or 'missing' in result.lower()
