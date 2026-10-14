"""Regression tests for keyword-based arbiter overrides (whole-word matching)."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dm_arbiter import check_code_overrides, get_fallback_decision
from text_match import has_any, has_phrase


@pytest.mark.parametrize("action, skill", [
    ("I swim in the river", "Athletics"),
    ("I bow and pick the lock", "Sleight_of_Hand"),
    ("I nod and sneak past the guard", "Stealth"),
    ("I grab the flask and climb the wall", "Athletics"),
    ("where is the hidden lever? I search the wall", "Perception"),
    ("I pick the lock on the secret door", "Sleight_of_Hand"),
    ("I tell him his price is too high, I want a discount", "Persuasion"),
    ("I demand 10 more gold now", "Intimidation"),
])
def test_rolls_not_skipped_by_social_shortcuts(action, skill):
    decision = check_code_overrides(action)
    assert decision is not None and decision.requires_roll, action
    assert decision.skill == skill


@pytest.mark.parametrize("action", [
    "I shoot my crossbow at the guard",
    "I offer the beggar a gold coin",
    "I pay the innkeeper for a room",
])
def test_no_false_override(action):
    decision = check_code_overrides(action)
    assert decision is None or not decision.requires_roll or decision.skill != "Persuasion", action
    if decision is not None:
        assert "greeting" not in decision.reasoning.lower(), action


def test_crossbow_is_not_a_greeting():
    assert check_code_overrides("I shoot my crossbow at the guard") is None
    assert "greeting" not in get_fallback_decision("I shoot my crossbow at the guard").reasoning.lower()


def test_know_does_not_count_as_now():
    decision = check_code_overrides("You know I want a lower price for 5 gold")
    assert decision.skill == "Persuasion"


def test_text_match_whole_words():
    assert has_phrase("I bow to the king", "bow")
    assert not has_phrase("I shoot my crossbow", "bow")
    assert not has_phrase("with all my force", "orc")
    assert not has_phrase("his sword", "hi")
    assert has_phrase("He hides in the barrel", "hide")
    assert has_phrase("I'm climbing the cliff", "climb")
    assert has_phrase("Take  it or LEAVE it", "take it or leave it")
    assert has_any("I'll kill you", ["i'll kill"])
