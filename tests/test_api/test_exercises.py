import json
from pathlib import Path
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


def test_add_walking_exercise_returns_created_item(client, api_key_headers, temp_schedule_file):
    with patch('src.api.endpoints.exercises.SCHEDULE_PATH', temp_schedule_file):
        with patch('src.tools.calculate_exercise_calories.get_user_stats') as mock_get_user_stats:
            mock_get_user_stats.return_value = {"weight_kg": 70.0}
            response = client.post(
                "/exercises/",
                json={
                    "date": "2026-06-22",
                    "type": "walking",
                    "distance_miles": 2.0,
                    "duration_minutes": 30,
                },
                headers=api_key_headers
            )

    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "walking"
    assert data["distance_miles"] == 2.0
    assert data["calories"] == round(3.5 * 70.0 * (30 / 60))


def test_add_biking_exercise_returns_created_item(client, api_key_headers, temp_schedule_file):
    with patch('src.api.endpoints.exercises.SCHEDULE_PATH', temp_schedule_file):
        with patch('src.tools.calculate_exercise_calories.get_user_stats') as mock_get_user_stats:
            mock_get_user_stats.return_value = {"weight_kg": 70.0}
            response = client.post(
                "/exercises/",
                json={
                    "date": "2026-06-22",
                    "type": "biking",
                    "distance_miles": 10.0,
                    "duration_minutes": 40,
                },
                headers=api_key_headers
            )

    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "biking"
    assert data["distance_miles"] == 10.0
    assert data["calories"] == round(7.5 * 70.0 * (40 / 60))


def test_add_swimming_exercise_returns_created_item(client, api_key_headers, temp_schedule_file):
    with patch('src.api.endpoints.exercises.SCHEDULE_PATH', temp_schedule_file):
        with patch('src.tools.calculate_exercise_calories.get_user_stats') as mock_get_user_stats:
            mock_get_user_stats.return_value = {"weight_kg": 70.0}
            response = client.post(
                "/exercises/",
                json={
                    "date": "2026-06-22",
                    "type": "swimming",
                    "distance_miles": 1.0,
                    "duration_minutes": 30,
                },
                headers=api_key_headers
            )

    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "swimming"
    assert data["distance_miles"] == 1.0
    assert data["calories"] == round(6.0 * 70.0 * (30 / 60))


def test_add_strength_exercise_returns_created_item(client, api_key_headers, temp_schedule_file):
    with patch('src.api.endpoints.exercises.SCHEDULE_PATH', temp_schedule_file):
        with patch('src.tools.calculate_exercise_calories.get_user_stats') as mock_get_user_stats:
            mock_get_user_stats.return_value = {"weight_kg": 70.0}
            response = client.post(
                "/exercises/",
                json={
                    "date": "2026-06-22",
                    "type": "strength",
                    "duration_minutes": 45,
                    "sets": 3,
                    "reps": 10,
                },
                headers=api_key_headers
            )

    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "strength"
    assert data["distance_miles"] is None
    assert data["sets"] == 3
    assert data["reps"] == 10
    assert data["calories"] == round(5.0 * 70.0 * (45 / 60))


def test_add_running_exercise_without_distance_returns_422(client, api_key_headers, temp_schedule_file):
    with patch('src.api.endpoints.exercises.SCHEDULE_PATH', temp_schedule_file):
        response = client.post(
            "/exercises/",
            json={"date": "2026-06-22", "type": "running", "duration_minutes": 28},
            headers=api_key_headers
        )

    assert response.status_code == 422


def test_add_walking_exercise_without_distance_returns_422(client, api_key_headers, temp_schedule_file):
    with patch('src.api.endpoints.exercises.SCHEDULE_PATH', temp_schedule_file):
        response = client.post(
            "/exercises/",
            json={"date": "2026-06-22", "type": "walking", "duration_minutes": 30},
            headers=api_key_headers
        )

    assert response.status_code == 422


def test_add_biking_exercise_without_distance_returns_422(client, api_key_headers, temp_schedule_file):
    with patch('src.api.endpoints.exercises.SCHEDULE_PATH', temp_schedule_file):
        response = client.post(
            "/exercises/",
            json={"date": "2026-06-22", "type": "biking", "duration_minutes": 40},
            headers=api_key_headers
        )

    assert response.status_code == 422


def test_add_swimming_exercise_without_distance_returns_422(client, api_key_headers, temp_schedule_file):
    with patch('src.api.endpoints.exercises.SCHEDULE_PATH', temp_schedule_file):
        response = client.post(
            "/exercises/",
            json={"date": "2026-06-22", "type": "swimming", "duration_minutes": 30},
            headers=api_key_headers
        )

    assert response.status_code == 422


def test_add_strength_exercise_without_sets_and_reps_returns_422(client, api_key_headers, temp_schedule_file):
    with patch('src.api.endpoints.exercises.SCHEDULE_PATH', temp_schedule_file):
        response = client.post(
            "/exercises/",
            json={"date": "2026-06-22", "type": "strength", "duration_minutes": 45},
            headers=api_key_headers
        )

    assert response.status_code == 422


def test_update_exercise_to_strength_type(client, api_key_headers, temp_schedule_file):
    with patch('src.api.endpoints.exercises.SCHEDULE_PATH', temp_schedule_file):
        with patch('src.tools.calculate_exercise_calories.get_user_stats') as mock_get_user_stats:
            mock_get_user_stats.return_value = {"weight_kg": 70.0}
            create_response = client.post(
                "/exercises/",
                json={"date": "2026-06-22", "distance_miles": 3.1, "duration_minutes": 28},
                headers=api_key_headers
            )
            exercise_id = create_response.json()["id"]

            update_response = client.put(
                f"/exercises/{exercise_id}",
                json={"type": "strength", "duration_minutes": 45, "sets": 4, "reps": 8},
                headers=api_key_headers
            )

    assert update_response.status_code == 200
    data = update_response.json()
    assert data["type"] == "strength"
    assert data["sets"] == 4
    assert data["reps"] == 8
    assert data["calories"] == round(5.0 * 70.0 * (45 / 60))


def test_update_exercise_to_strength_without_sets_and_reps_returns_422(client, api_key_headers, temp_schedule_file):
    with patch('src.api.endpoints.exercises.SCHEDULE_PATH', temp_schedule_file):
        with patch('src.tools.calculate_exercise_calories.get_user_stats') as mock_get_user_stats:
            mock_get_user_stats.return_value = {"weight_kg": 70.0}
            create_response = client.post(
                "/exercises/",
                json={"date": "2026-06-22", "distance_miles": 3.1, "duration_minutes": 28},
                headers=api_key_headers
            )
            exercise_id = create_response.json()["id"]

            update_response = client.put(
                f"/exercises/{exercise_id}",
                json={"type": "strength", "duration_minutes": 45},
                headers=api_key_headers
            )

    assert update_response.status_code == 422


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


def test_update_exercise_omitting_type_preserves_stored_non_running_type(client, api_key_headers, temp_schedule_file):
    with patch('src.api.endpoints.exercises.SCHEDULE_PATH', temp_schedule_file):
        with patch('src.tools.calculate_exercise_calories.get_user_stats') as mock_get_user_stats:
            mock_get_user_stats.return_value = {"weight_kg": 70.0}
            create_response = client.post(
                "/exercises/",
                json={
                    "date": "2026-06-22",
                    "type": "strength",
                    "duration_minutes": 45,
                    "sets": 3,
                    "reps": 10,
                },
                headers=api_key_headers
            )
            exercise_id = create_response.json()["id"]

            update_response = client.put(
                f"/exercises/{exercise_id}",
                json={"duration_minutes": 50, "sets": 4, "reps": 12},
                headers=api_key_headers
            )

    assert update_response.status_code == 200
    data = update_response.json()
    assert data["type"] == "strength"
    assert data["sets"] == 4
    assert data["reps"] == 12
    assert data["calories"] == round(5.0 * 70.0 * (50 / 60))


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


def test_get_exercise_week_fills_day_with_no_stored_data_from_preset(
    client, api_key_headers, temp_schedule_file, temp_presets_file
):
    Path(temp_presets_file).write_text(json.dumps({
        "presets": {"Monday": [{
            "type": "running", "distance_miles": 3.1, "duration_minutes": 28,
            "sets": None, "reps": None, "notes": "easy run",
        }]}
    }))

    with patch('src.api.endpoints.exercises.SCHEDULE_PATH', temp_schedule_file), \
         patch('src.api.endpoints.exercises.PRESETS_PATH', temp_presets_file), \
         patch('src.tools.calculate_exercise_calories.get_user_stats') as mock_get_user_stats:
        mock_get_user_stats.return_value = {"weight_kg": 70.0}
        response = client.get(
            "/exercises/?week_start=2026-06-22",
            headers=api_key_headers
        )

    assert response.status_code == 200
    monday = response.json()["days"][0]
    assert monday["day_name"] == "Monday"
    assert len(monday["exercises"]) == 1
    filled = monday["exercises"][0]
    assert filled["type"] == "running"
    assert filled["distance_miles"] == 3.1
    assert filled["calories"] == round(70.0 * 3.1 * 1.668)
    assert filled["notes"] == "easy run"
    assert filled["id"]
    assert monday["total_calories"] == filled["calories"]
