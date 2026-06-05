import pytest
from unittest.mock import patch


def test_add_meal_success(client, api_key_headers):
    """Test successful meal addition."""
    meal_data = {
        "name": "Test Meal",
        "ingredients": ["Ingredient 1", "Ingredient 2"],
        "macros": {"calories": 500, "protein": 30, "carbs": 20, "fat": 15},
        "instructions": ["Step 1", "Step 2"],
        "category": "Dinner",
        "tags": ["test"]
    }
    
    with patch('src.api.endpoints.meals.add_saved_meal_from_request') as mock_add:
        mock_add.return_value = {
            'success': True,
            'meal_name': 'Test Meal',
            'newly_added': [],
            'category': 'Dinner',
            'message': 'Meal added successfully'
        }
        
        response = client.post(
            "/meals/add",
            json=meal_data,
            headers=api_key_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['meal_name'] == 'Test Meal'


def test_add_meal_invalid_api_key(client):
    """Test meal addition with invalid API key."""
    response = client.post(
        "/meals/add",
        json={"name": "Test", "ingredients": [], "macros": {}, "instructions": []},
        headers={"X-API-Key": "invalid-key"}
    )
    
    assert response.status_code == 401


def test_list_meals_success(client, api_key_headers, sample_meal):
    """Test listing all meals."""
    with patch('src.api.endpoints.meals.load_saved_meals') as mock_load:
        mock_load.return_value = [sample_meal]
        
        response = client.get(
            "/meals/",
            headers=api_key_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['name'] == 'Chicken Stir-fry'


def test_list_meals_with_category_filter(client, api_key_headers, sample_meal):
    """Test listing meals with category filter."""
    with patch('src.api.endpoints.meals.load_saved_meals') as mock_load:
        mock_load.return_value = [sample_meal]
        
        response = client.get(
            "/meals/?category=Dinner",
            headers=api_key_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1


def test_list_meals_with_search(client, api_key_headers, sample_meal):
    """Test listing meals with search term."""
    with patch('src.api.endpoints.meals.load_saved_meals') as mock_load:
        mock_load.return_value = [sample_meal]
        
        response = client.get(
            "/meals/?search=chicken",
            headers=api_key_headers
        )
        
        assert response.status_code == 200


def test_search_meals_advanced(client, api_key_headers, sample_meal):
    """Test advanced meal search with multiple filters."""
    with patch('src.api.endpoints.meals.search_meals') as mock_search:
        mock_search.return_value = [sample_meal]
        
        response = client.get(
            "/meals/search?category=Dinner&min_cal=400&max_cal=600",
            headers=api_key_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1


def test_search_meals_by_ingredient(client, api_key_headers, sample_meal):
    """Test searching meals by ingredient."""
    with patch('src.api.endpoints.meals.search_meals') as mock_search:
        mock_search.return_value = [sample_meal]
        
        response = client.get(
            "/meals/search?ingredient=chicken",
            headers=api_key_headers
        )
        
        assert response.status_code == 200


def test_search_meals_invalid_api_key(client):
    """Test meal search with invalid API key."""
    response = client.get(
        "/meals/search",
        headers={"X-API-Key": "invalid-key"}
    )
    
    assert response.status_code == 401
