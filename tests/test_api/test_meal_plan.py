import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import json


def test_generate_plan_success(client, api_key_headers, sample_day_plan):
    """Test successful meal plan generation."""
    with patch('src.api.endpoints.meal_plan.generate_meal_plan_from_request') as mock_generate:
        mock_generate.return_value = {
            'plan_id': 'test-plan-123',
            'plan': [sample_day_plan],
            'grocery_list': [],
            'status': 'success'
        }
        
        response = client.post(
            "/plan/generate",
            json={"days": ["Monday"], "preferences": None},
            headers=api_key_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['plan_id'] == 'test-plan-123'
        assert len(data['plan']) == 1


def test_generate_plan_invalid_api_key(client):
    """Test meal plan generation with invalid API key."""
    response = client.post(
        "/plan/generate",
        json={"days": ["Monday"]},
        headers={"X-API-Key": "invalid-key"}
    )
    
    assert response.status_code == 401
    assert "Invalid or missing API Key" in response.json()['detail']


def test_generate_plan_missing_api_key(client):
    """Test meal plan generation without API key."""
    response = client.post(
        "/plan/generate",
        json={"days": ["Monday"]}
    )
    
    assert response.status_code == 401


def test_get_plan_for_day_success(client, api_key_headers, sample_day_plan, temp_state_file):
    """Test getting plan for a specific day."""
    # Write test state
    state_data = {
        'current_day': 'Monday',
        'plan_id': 'test-plan-123',
        'plan': [sample_day_plan],
        'grocery_list': [],
        'missing_macros': []
    }
    Path(temp_state_file).write_text(json.dumps(state_data))
    
    with patch('src.api.endpoints.meal_plan.STATE_PATH', temp_state_file):
        response = client.get(
            "/plan/Monday",
            headers=api_key_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['day'] == 'Monday'
        assert len(data['meals']) == 1


def test_get_plan_for_day_not_found(client, api_key_headers, temp_state_file):
    """Test getting plan for a day that doesn't exist."""
    state_data = {
        'current_day': 'Monday',
        'plan_id': 'test-plan-123',
        'plan': [],
        'grocery_list': [],
        'missing_macros': []
    }
    Path(temp_state_file).write_text(json.dumps(state_data))
    
    with patch('src.api.endpoints.meal_plan.STATE_PATH', temp_state_file):
        response = client.get(
            "/plan/Tuesday",
            headers=api_key_headers
        )
        
        assert response.status_code == 404


def test_get_current_plan_success(client, api_key_headers, sample_day_plan, temp_state_file):
    """Test getting current complete plan."""
    state_data = {
        'current_day': 'Monday',
        'plan_id': 'test-plan-123',
        'plan': [sample_day_plan],
        'grocery_list': [{'item': 'Chicken', 'quantity': 1, 'unit': 'lbs', 'category': 'Protein'}],
        'missing_macros': []
    }
    Path(temp_state_file).write_text(json.dumps(state_data))
    
    with patch('src.api.endpoints.meal_plan.STATE_PATH', temp_state_file):
        response = client.get(
            "/plan/",
            headers=api_key_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['plan_id'] == 'test-plan-123'
        assert len(data['plan']) == 1
        assert len(data['grocery_list']) == 1


def test_get_current_plan_state_not_found(client, api_key_headers):
    """Test getting plan when state file doesn't exist."""
    with patch('src.api.endpoints.meal_plan.STATE_PATH', '/nonexistent/path/state.json'):
        response = client.get(
            "/plan/",
            headers=api_key_headers
        )
        
        assert response.status_code == 404
