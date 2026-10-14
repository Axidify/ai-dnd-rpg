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


def test_map_hides_secret_and_unknown_places(client, session_id):
    data = client.get("/api/locations", query_string={"session_id": session_id}).get_json()
    by_id = {loc["id"]: loc for loc in data["all_locations"]}
    # Secret places aren't sent at all until found
    assert "secret_cave" not in by_id and "treasure_nook" not in by_id
    # Places outside the current scene keep their names (and labels) to themselves
    unknown = [loc for loc in by_id.values() if not loc["known"]]
    assert unknown, "expected undiscovered places in the first scene"
    for loc in unknown:
        assert loc["name"] == "???" and loc["map_label"] == "???" and loc["description"] == ""
    assert any(loc["is_current"] for loc in by_id.values())


def test_class_and_race_lists(client):
    classes = client.get("/api/classes").get_json()["classes"]
    by_name = {c["name"]: c for c in classes}
    assert len(by_name) == 12
    assert by_name["Barbarian"]["hit_die"] == 12
    assert by_name["Rogue"]["weapon"] == "Shortsword" and by_name["Rogue"]["armor"] == "Leather Armor"
    races = client.get("/api/races").get_json()["races"]
    assert "Half-Orc" in races and len(races) == 9
