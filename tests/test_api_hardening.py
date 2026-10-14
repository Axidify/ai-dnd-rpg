"""Server hardening: input limits and CORS."""

import pytest

from api_server import app, MAX_ACTION_LENGTH


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def session_id(client):
    response = client.post("/api/game/start", json={
        "character": {"name": "Limits", "race": "Human", "class": "Fighter"},
        "scenario_id": "goblin_cave",
    })
    return response.get_json()["session_id"]


@pytest.mark.parametrize("endpoint", ["/api/game/action", "/api/game/action/stream"])
def test_overlong_action_rejected(client, session_id, endpoint):
    response = client.post(endpoint, json={
        "session_id": session_id,
        "action": "a" * (MAX_ACTION_LENGTH + 1),
    })
    assert response.status_code == 400


def test_cors_only_allows_configured_origins(client):
    allowed = client.get("/api/health", headers={"Origin": "http://localhost:3000"})
    assert allowed.headers.get("Access-Control-Allow-Origin") == "http://localhost:3000"

    other = client.get("/api/health", headers={"Origin": "https://evil.example"})
    assert "Access-Control-Allow-Origin" not in other.headers
