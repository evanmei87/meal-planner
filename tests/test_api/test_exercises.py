from unittest.mock import patch


def test_get_exercise_week_no_file_returns_seven_empty_days(client, api_key_headers):
    with patch('src.api.endpoints.exercises.SCHEDULE_PATH', '/nonexistent/path/exercise_schedule.json'):
        response = client.get(
            "/exercises/?week_start=2026-06-22",
            headers=api_key_headers
        )

    assert response.status_code == 200
    data = response.json()
    assert data["week_start"] == "2026-06-22"
    assert len(data["days"]) == 7
    assert data["days"][0]["date"] == "2026-06-22"
    assert data["days"][0]["day_name"] == "Monday"
    assert data["days"][0]["exercises"] == []
    assert data["days"][0]["total_calories"] == 0


def test_add_exercise_returns_created_item(client, api_key_headers, temp_schedule_file):
    with patch('src.api.endpoints.exercises.SCHEDULE_PATH', temp_schedule_file):
        with patch('src.tools.calculate_exercise_calories.get_user_stats') as mock_get_user_stats:
            mock_get_user_stats.return_value = {"weight_kg": 70.0}
            response = client.post(
                "/exercises/",
                json={
                    "date": "2026-06-22",
                    "distance_miles": 3.1,
                    "duration_minutes": 28,
                    "notes": "easy morning run",
                },
                headers=api_key_headers
            )

    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "running"
    assert data["distance_miles"] == 3.1
    assert data["duration_minutes"] == 28
    assert data["calories"] == round(70.0 * 3.1 * 1.668)
    assert data["calories"] > 0
    assert data["notes"] == "easy morning run"
    assert data["id"]


def test_get_exercise_week_invalid_api_key(client):
    response = client.get(
        "/exercises/",
        headers={"X-API-Key": "invalid-key"}
    )

    assert response.status_code == 401


def test_add_exercise_invalid_api_key(client):
    response = client.post(
        "/exercises/",
        json={"date": "2026-06-22", "distance_miles": 3.1, "duration_minutes": 28},
        headers={"X-API-Key": "invalid-key"}
    )

    assert response.status_code == 401


def test_update_exercise_recalculates_calories(client, api_key_headers, temp_schedule_file):
    with patch('src.api.endpoints.exercises.SCHEDULE_PATH', temp_schedule_file):
        with patch('src.tools.calculate_exercise_calories.get_user_stats') as mock_get_user_stats:
            mock_get_user_stats.return_value = {"weight_kg": 70.0}
            create_response = client.post(
                "/exercises/",
                json={
                    "date": "2026-06-22",
                    "distance_miles": 3.1,
                    "duration_minutes": 28,
                    "notes": "easy morning run",
                },
                headers=api_key_headers
            )
            exercise_id = create_response.json()["id"]

            update_response = client.put(
                f"/exercises/{exercise_id}",
                json={
                    "distance_miles": 5.0,
                    "duration_minutes": 45,
                    "notes": "long run",
                },
                headers=api_key_headers
            )

    assert update_response.status_code == 200
    data = update_response.json()
    assert data["id"] == exercise_id
    assert data["distance_miles"] == 5.0
    assert data["duration_minutes"] == 45
    assert data["notes"] == "long run"
    assert data["calories"] == round(70.0 * 5.0 * 1.668)


def test_update_exercise_unknown_id_returns_404(client, api_key_headers, temp_schedule_file):
    with patch('src.api.endpoints.exercises.SCHEDULE_PATH', temp_schedule_file):
        response = client.put(
            "/exercises/unknown-id",
            json={"distance_miles": 5.0, "duration_minutes": 45},
            headers=api_key_headers
        )

    assert response.status_code == 404


def test_delete_exercise_removes_it(client, api_key_headers, temp_schedule_file):
    with patch('src.api.endpoints.exercises.SCHEDULE_PATH', temp_schedule_file):
        with patch('src.tools.calculate_exercise_calories.get_user_stats') as mock_get_user_stats:
            mock_get_user_stats.return_value = {"weight_kg": 70.0}
            create_response = client.post(
                "/exercises/",
                json={"date": "2026-06-22", "distance_miles": 3.1, "duration_minutes": 28},
                headers=api_key_headers
            )
            exercise_id = create_response.json()["id"]

            delete_response = client.delete(f"/exercises/{exercise_id}", headers=api_key_headers)

            week_response = client.get("/exercises/?week_start=2026-06-22", headers=api_key_headers)

    assert delete_response.status_code == 204
    week_data = week_response.json()
    assert week_data["days"][0]["exercises"] == []


def test_delete_exercise_unknown_id_returns_404(client, api_key_headers, temp_schedule_file):
    with patch('src.api.endpoints.exercises.SCHEDULE_PATH', temp_schedule_file):
        response = client.delete("/exercises/unknown-id", headers=api_key_headers)

    assert response.status_code == 404


def test_update_exercise_invalid_api_key(client):
    response = client.put(
        "/exercises/some-id",
        json={"distance_miles": 5.0, "duration_minutes": 45},
        headers={"X-API-Key": "invalid-key"}
    )

    assert response.status_code == 401


def test_delete_exercise_invalid_api_key(client):
    response = client.delete(
        "/exercises/some-id",
        headers={"X-API-Key": "invalid-key"}
    )

    assert response.status_code == 401
