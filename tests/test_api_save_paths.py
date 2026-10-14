"""Save/load endpoints must never touch files outside the saves directory."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from api_server import app, _resolve_save_path


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_resolve_strips_directories(tmp_path):
    saves = str(tmp_path)
    assert _resolve_save_path(saves, "quicksave") == os.path.join(saves, "quicksave.json")
    assert _resolve_save_path(saves, "/etc/passwd.json") == os.path.join(saves, "passwd.json")
    assert _resolve_save_path(saves, "..\\..\\secrets.json") == os.path.join(saves, "secrets.json")
    assert _resolve_save_path(saves, "C:/Windows/win.ini") is None
    assert _resolve_save_path(saves, "..") is None


def test_load_rejects_outside_file(client, tmp_path):
    outside = tmp_path / "outside.json"
    outside.write_text('{"character": {"name": "Pwned"}}', encoding="utf-8")
    response = client.post("/api/game/load", json={"filepath": str(outside)})
    assert response.status_code == 404


def test_save_rejects_non_integer_slot(client):
    start = client.post("/api/game/start", json={
        "character": {"name": "Saver", "race": "Human", "class": "Fighter"},
        "scenario_id": "goblin_cave",
    })
    session_id = start.get_json()["session_id"]
    response = client.post("/api/game/save", json={"session_id": session_id, "slot": "/../../x"})
    assert response.status_code == 400
