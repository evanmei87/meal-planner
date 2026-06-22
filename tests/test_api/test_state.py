import pytest
from unittest.mock import patch
from pathlib import Path
import json


def test_get_state_success(client, api_key_headers, temp_state_file):
    """Test successful state retrieval."""
    state_data = {
        'current_day': 'Monday',
        'plan_id': 'test-plan-123',
        'plan': [],
        'grocery_list': [],
        'missing_macros': []
    }
    Path(temp_state_file).write_text(json.dumps(state_data))
    
    with patch('src.api.endpoints.state.STATE_PATH', temp_state_file):
        response = client.get(
            "/state/",
            headers=api_key_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['current_day'] == 'Monday'
        assert data['plan_id'] == 'test-plan-123'


def test_get_state_not_found(client, api_key_headers):
    """Test state retrieval returns empty state when state file doesn't exist."""
    with patch('src.api.endpoints.state.STATE_PATH', '/nonexistent/path/state.json'):
        response = client.get(
            "/state/",
            headers=api_key_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["plan"] == []
        assert data["grocery_list"] == []
        assert data["grocery_inventory"] == []


def test_get_state_invalid_api_key(client):
    """Test state retrieval with invalid API key."""
    response = client.get(
        "/state/",
        headers={"X-API-Key": "invalid-key"}
    )
    
    assert response.status_code == 401


def test_update_state_success(client, api_key_headers, temp_state_file, sample_day_plan):
    """Test successful state update."""
    initial_state = {
        'current_day': 'Monday',
        'plan_id': 'test-plan-123',
        'plan': [],
        'grocery_list': [],
        'missing_macros': []
    }
    Path(temp_state_file).write_text(json.dumps(initial_state))
    
    update_data = {
        'current_day': 'Tuesday'
    }
    
    with patch('src.api.endpoints.state.STATE_PATH', temp_state_file):
        with patch('src.api.endpoints.state.update_state') as mock_update:
            mock_update.return_value = True
            
            response = client.put(
                "/state/",
                json=update_data,
                headers=api_key_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['current_day'] == 'Tuesday'


def test_update_state_invalid_api_key(client):
    """Test state update with invalid API key."""
    response = client.put(
        "/state/",
        json={"current_day": "Tuesday"},
        headers={"X-API-Key": "invalid-key"}
    )
    
    assert response.status_code == 401


def test_update_state_failure(client, api_key_headers, temp_state_file):
    """Test state update when update fails."""
    initial_state = {
        'current_day': 'Monday',
        'plan_id': 'test-plan-123',
        'plan': [],
        'grocery_list': [],
        'missing_macros': []
    }
    Path(temp_state_file).write_text(json.dumps(initial_state))
    
    with patch('src.api.endpoints.state.STATE_PATH', temp_state_file):
        with patch('src.api.endpoints.state.update_state') as mock_update:
            mock_update.return_value = False
            
            response = client.put(
                "/state/",
                json={"current_day": "Tuesday"},
                headers=api_key_headers
            )
            
            assert response.status_code == 500
