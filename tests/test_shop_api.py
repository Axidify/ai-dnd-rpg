"""Shop endpoints: the shop depends on where you are; equipped gear can't be sold."""

import pytest

from api_server import app, game_sessions


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def sid(client):
    body = client.post("/api/game/start", json={
        "character": {"name": "Trader", "race": "Human", "class": "Rogue"},
        "scenario_id": "goblin_cave",
    }).get_json()
    return body["session_id"]


def browse(client, sid):
    return client.get("/api/shop/browse", query_string={"session_id": sid}).get_json()


def test_general_store_away_from_shops(client, sid):
    data = browse(client, sid)
    assert data["shop_name"] == "General Store" and data["is_local"] is False


def test_local_shop_at_its_location(client, sid):
    game_sessions[sid].location_manager.set_current_location("blacksmith_shop")
    data = browse(client, sid)
    assert data["shop_name"] == "Gavin's Forge" and data["is_local"] is True
    assert data["owner_name"]
    names = {i["id"] for i in data["items"]}
    assert "longsword" in names
    longsword = next(i for i in data["items"] if i["id"] == "longsword")
    assert longsword["stock"] == 2 and longsword["description"]


def test_sell_offers_flag_equipped_gear(client, sid):
    offers = {o["name"]: o for o in browse(client, sid)["sell_offers"]}
    assert offers["Shortsword"]["can_sell"] is False and offers["Shortsword"]["reason"] == "equipped"
    assert offers["Leather Armor"]["reason"] == "equipped"
    assert offers["Healing Potion"]["can_sell"] is True and offers["Healing Potion"]["price"] >= 1


def test_cannot_sell_equipped_armor(client, sid):
    body = client.post("/api/shop/sell", json={"session_id": sid, "item_name": "Leather Armor"}).get_json()
    assert body["success"] is False and "using" in body["message"]
    inventory = [i.name for i in game_sessions[sid].character.inventory]
    assert "Leather Armor" in inventory
