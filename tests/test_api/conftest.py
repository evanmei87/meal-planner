import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import json
import tempfile

from src.api.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def api_key_headers():
    """Provide valid API key headers for testing."""
    return {"X-API-Key": "dev-key-change-in-production"}


@pytest.fixture
def temp_state_file():
    """Create a temporary state file for testing."""
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    default_state = {
        'current_day': 'Monday',
        'plan_id': 'test-plan-123',
        'plan': [],
        'grocery_list': [],
        'missing_macros': []
    }
    temp_file.write(json.dumps(default_state, indent=2))
    temp_file.close()
    
    yield temp_file.name
    
    # Cleanup
    Path(temp_file.name).unlink(missing_ok=True)


@pytest.fixture
def temp_schedule_file():
    """Create a temporary exercise schedule file for testing."""
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    temp_file.write(json.dumps({'days': {}}, indent=2))
    temp_file.close()

    yield temp_file.name

    Path(temp_file.name).unlink(missing_ok=True)


@pytest.fixture
def temp_presets_file():
    """Create a temporary exercise presets file for testing."""
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    temp_file.write(json.dumps({'presets': {}}, indent=2))
    temp_file.close()

    yield temp_file.name

    Path(temp_file.name).unlink(missing_ok=True)


@pytest.fixture
def sample_day_plan():
    """Sample day plan for testing."""
    return {
        'day': 'Monday',
        'meals': [
            {
                'name': 'Oatmeal with Berries',
                'calories': 500,
                'macros': {'protein': 25, 'carbs': 70, 'fat': 12},
                'ingredients': ['Oatmeal', 'Mixed Berries', 'Milk']
            }
        ],
        'total_calories': 500,
        'total_protein': 25,
        'total_carbs': 70
    }


@pytest.fixture
def sample_meal():
    """Sample meal for testing."""
    return {
        'name': 'Chicken Stir-fry',
        'version': '2024-01-01T00:00:00',
        'category': 'Dinner',
        'macros': {'calories': 500, 'protein': 30, 'carbs': 20, 'fat': 15},
        'ingredients': ['Chicken', 'Vegetables', 'Soy Sauce'],
        'instructions': ['Cook chicken', 'Add vegetables', 'Season with soy sauce'],
        'tags': ['quick', 'healthy']
    }
