"""Both action endpoints run turns through turn_service and must agree."""

import json
import re

import pytest

import api_server
from api_server import app, game_sessions

NARRATION = (
    "You pry open the chest and find a small pouch. "
    "[GOLD: 10] [ITEM: healing potion] [XP: 25 | found the stash]"
)


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(api_server, "get_dm_response", lambda *a, **k: NARRATION)

    def fake_stream(*args, **kwargs):
        # Split mid-tag to exercise the streaming tag filter
        yield NARRATION[:60]
        yield NARRATION[60:75]
        yield NARRATION[75:]

    monkeypatch.setattr(api_server, "stream_dm_response", fake_stream)
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def _new_session(client):
    response = client.post("/api/game/start", json={
        "character": {"name": "Twin", "race": "Human", "class": "Fighter"},
        "scenario_id": "goblin_cave",
    })
    return response.get_json()["session_id"]


def _sse_events(response):
    body = response.get_data(as_text=True)
    return [json.loads(line[6:]) for line in body.splitlines() if line.startswith("data: ")]


ACTION = "I open the old chest by the wall"


def test_json_and_stream_apply_same_mechanics(client):
    json_sid = _new_session(client)
    stream_sid = _new_session(client)
    gold_before = {sid: game_sessions[sid].character.gold for sid in (json_sid, stream_sid)}

    body = client.post("/api/game/action", json={"session_id": json_sid, "action": ACTION}).get_json()
    events = _sse_events(client.post("/api/game/action/stream",
                                     json={"session_id": stream_sid, "action": ACTION}))

    # JSON summary
    assert body["gold_gained"] == 10
    assert body["xp_gained"] == 25
    assert body["items_gained"] == ["healing potion"]
    assert "[GOLD" not in body["message"] and "[ITEM" not in body["message"]

    # Stream events carry the same mechanics, and no raw tags leak in chunks
    types = [e["type"] for e in events]
    assert "gold" in types and "item" in types and "xp" in types
    assert types[-1] == "done"
    streamed_text = "".join(e["content"] for e in events if e["type"] == "chunk")
    assert "[" not in streamed_text

    json_session, stream_session = game_sessions[json_sid], game_sessions[stream_sid]
    for sid, session in ((json_sid, json_session), (stream_sid, stream_session)):
        assert session.character.gold == gold_before[sid] + 10
        assert session.character.experience == 25

    # Same transcript text (ignoring each hero's random starting gold and the
    # spacing left where the stream filter removed tags), and each endpoint
    # records exactly what it showed
    def same_gold(text):
        return " ".join(re.sub(r"Total: \d+", "Total: N", text).split())
    assert same_gold(json_session.messages[-1]["content"]) == same_gold(stream_session.messages[-1]["content"])
    assert body["message"] == json_session.messages[-1]["content"]
    assert streamed_text.strip() == stream_session.messages[-1]["content"]


def test_combat_lock_is_identical(client):
    json_sid = _new_session(client)
    stream_sid = _new_session(client)
    for sid in (json_sid, stream_sid):
        game_sessions[sid].in_combat = True

    body = client.post("/api/game/action", json={"session_id": json_sid, "action": "I dance"}).get_json()
    events = _sse_events(client.post("/api/game/action/stream",
                                     json={"session_id": stream_sid, "action": "I dance"}))

    assert "Combat is underway" in body["message"]
    assert [e["type"] for e in events] == ["chunk", "done"]
    assert events[0]["content"] == body["message"]
    assert game_sessions[json_sid].messages[-1] == {**game_sessions[stream_sid].messages[-1],
                                                    "timestamp": game_sessions[json_sid].messages[-1]["timestamp"]}


def test_unreachable_dm_is_flagged_without_config_text():
    # No LLM is configured under the offline test suite, so narration falls back
    app.config["TESTING"] = True
    with app.test_client() as plain:
        sid = _new_session(plain)
        assert game_sessions[sid].dm_unavailable is True  # the opening fell back too
        body = plain.post("/api/game/action", json={"session_id": sid, "action": "I wave"}).get_json()
    assert body["game_state"]["dm_unavailable"] is True
    for text in (body["message"], game_sessions[sid].messages[0]["content"]):
        assert "VLLM" not in text and "GOOGLE_API_KEY" not in text


def test_roll_fallback_starts_a_new_paragraph(monkeypatch):
    monkeypatch.setattr(api_server, "get_dm_response", lambda *a, **k: "You try.")
    app.config["TESTING"] = True
    with app.test_client() as c:
        sid = _new_session(c)
        body = c.post("/api/game/action", json={"session_id": sid, "action": "I sneak past the guard"}).get_json()
    assert body["roll_result"] is not None
    assert body["message"].startswith("You try.\n\n")
