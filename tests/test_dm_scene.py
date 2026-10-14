"""Tests for scene-aware DM rules."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dm_scene import (
    classify_exploration_action,
    apply_scene_arbiter_rules,
    build_scene_redirect_narration,
    is_weak_roll_narration,
    get_survey_count,
    increment_survey_count,
)
from dm_arbiter import ArbiterDecision, ActionType, get_arbiter_decision
from character import Character


class FakeSession:
    def __init__(self, location="Village Square", location_id=None):
        self.current_location = location
        self.current_location_id = location_id
        self.scene_state = {}
        self.character = Character(name="T", race="Human", char_class="Wizard")


def test_classify_vague_vs_specific():
    assert classify_exploration_action("I look carefully around me.") == "vague_survey"
    assert classify_exploration_action("I look for hidden tracks near the well") == "specific_search"
    assert classify_exploration_action("I examine the crate closely") == "specific_search"
    assert classify_exploration_action("I enter the tavern") == "other"


def test_first_survey_no_roll():
    session = FakeSession()
    decision = ArbiterDecision(
        action_type=ActionType.EXPLORATION.value,
        requires_roll=True,
        skill="Perception",
        dc=12,
        source="code_override",
    )
    new_decision, scene_action = apply_scene_arbiter_rules(
        "I look around", decision, session
    )
    assert scene_action == "survey_first"
    assert new_decision.requires_roll is False


def test_repeat_survey_redirect():
    session = FakeSession()
    increment_survey_count(session)
    decision = ArbiterDecision(
        action_type=ActionType.EXPLORATION.value,
        requires_roll=True,
        skill="Perception",
        dc=12,
    )
    new_decision, scene_action = apply_scene_arbiter_rules(
        "I look around", decision, session
    )
    assert scene_action == "survey_repeat"
    assert new_decision.requires_roll is False
    text = build_scene_redirect_narration(session)
    assert "engage" in text.lower() or "Where will you go" in text


def test_vague_look_not_forced_roll_by_code_override():
    decision = get_arbiter_decision(
        "I look carefully around me.", "Location: Village Square", use_ai=False
    )
    assert decision.requires_roll is False


def test_basic_conversation_no_roll():
    ctx = "Location: The Rusty Dragon. NPC Bram is present."
    for action in [
        "I speak up.",
        "I ask Bram where his daughter was taken.",
        "Tell me about the cave, barkeep.",
        "Yes, I will help you Bram.",
        "Hello Bram.",
    ]:
        decision = get_arbiter_decision(action, ctx, use_ai=False)
        assert decision.requires_roll is False, action


def test_negotiation_still_requires_roll():
    decision = get_arbiter_decision(
        "I try to convince Bram to pay me more gold.",
        "Location: Tavern",
        use_ai=False,
    )
    assert decision.requires_roll is True
    assert decision.skill == "Persuasion"


def test_weak_roll_narration_detects_setup_only():
    weak = (
        "You narrow your eyes and scan the square, focusing on the crowd at the well. "
        "You look for anything out of place."
    )
    roll = {"success": True, "skill": "Perception"}
    assert is_weak_roll_narration(weak, roll) is True

    strong = "You spot fresh clawed prints leading north from the well."
    assert is_weak_roll_narration(strong, roll) is False


def test_survey_count_per_location():
    session = FakeSession(location="Village Square")
    assert get_survey_count(session) == 0
    increment_survey_count(session)
    assert get_survey_count(session) == 1
    session.current_location = "Tavern"
    assert get_survey_count(session) == 0
