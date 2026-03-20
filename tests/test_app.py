import copy

import pytest
from fastapi.testclient import TestClient

from src import app as app_mod

client = TestClient(app_mod.app)

@pytest.fixture(autouse=True)
def reset_activities():
    original_state = copy.deepcopy(app_mod.activities)
    yield
    app_mod.activities = original_state


def test_get_activities_returns_activity_collection():
    # Arrange
    expected_activity = "Chess Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert expected_activity in payload
    assert isinstance(payload[expected_activity]["participants"], list)


def test_signup_for_activity_adds_participant_and_reflects_in_get():
    # Arrange
    activity_name = "Chess Club"
    new_email = "testuser@mergington.edu"

    # Act
    signup_response = client.post(f"/activities/{activity_name}/signup", params={"email": new_email})

    # Assert
    assert signup_response.status_code == 200
    assert "Signed up" in signup_response.json()["message"]

    # Act
    todos = client.get("/activities").json()

    # Assert
    assert new_email in todos[activity_name]["participants"]


def test_delete_participant_removes_entry_from_activity():
    # Arrange
    activity_name = "Chess Club"
    participant_email = "deleteme@mergington.edu"
    add_response = client.post(f"/activities/{activity_name}/signup", params={"email": participant_email})
    assert add_response.status_code == 200

    # Act
    delete_response = client.delete(f"/activities/{activity_name}/participants", params={"email": participant_email})

    # Assert
    assert delete_response.status_code == 200
    assert "Unregistered" in delete_response.json()["message"]

    # Act
    after_state = client.get("/activities").json()

    # Assert
    assert participant_email not in after_state[activity_name]["participants"]


def test_signup_existing_participant_returns_400():
    # Arrange
    activity_name = "Chess Club"
    duplicate_email = "duplicate@mergington.edu"

    client.post(f"/activities/{activity_name}/signup", params={"email": duplicate_email})

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": duplicate_email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up"


def test_delete_nonexistent_participant_returns_404():
    # Arrange
    activity_name = "Chess Club"
    missing_email = "missing@mergington.edu"

    # Act
    response = client.delete(f"/activities/{activity_name}/participants", params={"email": missing_email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"


def test_unknown_activity_endpoints_return_404():
    # Arrange
    unknown_activity = "Nonexistent Club"
    email = "test@mergington.edu"

    # Act
    signup_response = client.post(f"/activities/{unknown_activity}/signup", params={"email": email})
    delete_response = client.delete(f"/activities/{unknown_activity}/participants", params={"email": email})

    # Assert
    assert signup_response.status_code == 404
    assert signup_response.json()["detail"] == "Activity not found"
    assert delete_response.status_code == 404
    assert delete_response.json()["detail"] == "Activity not found"
