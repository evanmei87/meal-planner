from unittest.mock import patch


def test_set_preset_returns_saved_list(client, api_key_headers, temp_presets_file):
    with patch('src.api.endpoints.exercise_presets.PRESETS_PATH', temp_presets_file):
        response = client.post(
            "/exercise-presets/Monday",
            json=[{"type": "running", "distance_miles": 3.1, "duration_minutes": 28, "notes": "easy run"}],
            headers=api_key_headers
        )

    assert response.status_code == 200
    data = response.json()
    assert data == [{
        "type": "running",
        "distance_miles": 3.1,
        "duration_minutes": 28,
        "sets": None,
        "reps": None,
        "notes": "easy run",
    }]


def test_set_preset_running_without_distance_returns_422(client, api_key_headers, temp_presets_file):
    with patch('src.api.endpoints.exercise_presets.PRESETS_PATH', temp_presets_file):
        response = client.post(
            "/exercise-presets/Monday",
            json=[{"type": "running", "duration_minutes": 28}],
            headers=api_key_headers
        )

    assert response.status_code == 422


def test_get_presets_returns_full_map(client, api_key_headers, temp_presets_file):
    with patch('src.api.endpoints.exercise_presets.PRESETS_PATH', temp_presets_file):
        client.post(
            "/exercise-presets/Monday",
            json=[{"type": "running", "distance_miles": 3.1, "duration_minutes": 28}],
            headers=api_key_headers
        )
        response = client.get("/exercise-presets/", headers=api_key_headers)

    assert response.status_code == 200
    data = response.json()
    assert list(data["presets"].keys()) == ["Monday"]
    assert data["presets"]["Monday"][0]["type"] == "running"


def test_get_presets_no_file_returns_empty_map(client, api_key_headers):
    with patch('src.api.endpoints.exercise_presets.PRESETS_PATH', '/nonexistent/path/exercise_presets.json'):
        response = client.get("/exercise-presets/", headers=api_key_headers)

    assert response.status_code == 200
    assert response.json() == {"presets": {}}


def test_set_preset_invalid_api_key(client):
    response = client.post(
        "/exercise-presets/Monday",
        json=[{"type": "running", "distance_miles": 3.1, "duration_minutes": 28}],
        headers={"X-API-Key": "invalid-key"}
    )

    assert response.status_code == 401


def test_get_presets_invalid_api_key(client):
    response = client.get(
        "/exercise-presets/",
        headers={"X-API-Key": "invalid-key"}
    )

    assert response.status_code == 401
