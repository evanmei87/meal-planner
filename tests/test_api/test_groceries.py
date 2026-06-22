from unittest.mock import patch


FAKE_INGREDIENT = {
    "raw_phrase": "2 lbs chicken thighs",
    "standardized_item": "chicken thighs",
    "quantity": 2.0,
    "unit": "lbs",
    "corgis_style_query": "Chicken thigh",
}

FAKE_META_AUTO = {
    **FAKE_INGREDIENT,
    "corgis_description": "Chicken thigh, meat only",
    "confidence_score": 0.86,
    "confidence_level": "high",
    "should_auto_save": True,
    "source": "corgis",
}

FAKE_META_MANUAL = {
    **FAKE_INGREDIENT,
    "raw_phrase": "arugula",
    "standardized_item": "arugula",
    "corgis_description": None,
    "confidence_score": 0.2,
    "confidence_level": "low",
    "should_auto_save": False,
    "source": "specialty",
}


def test_groceries_add_high_confidence_auto_saves(client, api_key_headers):
    with (
        patch("src.api.endpoints.groceries.parse_ingredients", return_value=[FAKE_INGREDIENT]),
        patch("src.api.endpoints.groceries.get_ingredient_metadata", return_value=FAKE_META_AUTO),
        patch("src.api.endpoints.groceries.add_inventory_items", return_value={"added": [FAKE_META_AUTO]}) as mock_add,
        patch("src.api.endpoints.groceries.add_unmatched_items") as mock_unmatched,
    ):
        response = client.post("/groceries", json={"text": "2 lbs chicken thighs"}, headers=api_key_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["saved_count"] == 1
    assert data["review_count"] == 0
    assert len(data["items"]) == 1
    assert data["items"][0]["raw_phrase"] == "2 lbs chicken thighs"
    assert data["items"][0]["status"] == "auto"
    assert data["items"][0]["confidence_score"] == 0.86
    assert data["items"][0]["match"] == "Chicken thigh, meat only"
    mock_add.assert_called_once()
    mock_unmatched.assert_not_called()


def test_groceries_add_low_confidence_goes_to_unmatched(client, api_key_headers):
    with (
        patch("src.api.endpoints.groceries.parse_ingredients", return_value=[FAKE_INGREDIENT]),
        patch("src.api.endpoints.groceries.get_ingredient_metadata", return_value=FAKE_META_MANUAL),
        patch("src.api.endpoints.groceries.add_inventory_items") as mock_add,
        patch("src.api.endpoints.groceries.add_unmatched_items") as mock_unmatched,
    ):
        response = client.post("/groceries", json={"text": "arugula"}, headers=api_key_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["saved_count"] == 0
    assert data["review_count"] == 1
    assert data["items"][0]["status"] == "manual"
    mock_add.assert_not_called()
    mock_unmatched.assert_called_once()


def test_groceries_add_requires_valid_api_key(client):
    response = client.post("/groceries", json={"text": "chicken"}, headers={"X-API-Key": "wrong"})
    assert response.status_code == 401


def test_groceries_add_rejects_empty_text(client, api_key_headers):
    response = client.post("/groceries", json={"text": ""}, headers=api_key_headers)
    assert response.status_code == 422
