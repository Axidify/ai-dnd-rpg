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


def test_roll_outcome_text_matches_the_skill():
    from dm_scene import build_roll_outcome_narration, SKILL_OUTCOMES, LOCATION_DATA

    session = FakeSession()
    search_lines = [
        line
        for loc in LOCATION_DATA.values()
        for line in loc["success_clues"] + loc["failure_complications"]
    ]

    for success in (True, False):
        text = build_roll_outcome_narration(
            session, "I sneak past the guard", {"skill": "Stealth", "success": success}
        )
        assert any(line in text for line in SKILL_OUTCOMES["stealth"]["success" if success else "failure"])
        assert "searching" not in text and not any(line in text for line in search_lines)

    # Underscore/title-case skill names from the roller still match
    text = build_roll_outcome_narration(session, "I pick the lock", {"skill": "Sleight_Of_Hand", "success": False})
    assert any(line in text for line in SKILL_OUTCOMES["sleight of hand"]["failure"])


def test_search_rolls_still_use_location_clues():
    from dm_scene import build_roll_outcome_narration, LOCATION_DATA

    session = FakeSession(location="Village Square")
    text = build_roll_outcome_narration(session, "I search the well", {"skill": "Perception", "success": True})
    assert any(clue in text for clue in LOCATION_DATA["village square"]["success_clues"])

    crit = build_roll_outcome_narration(
        session, "I search the well", {"skill": "Perception", "success": False, "is_nat_1": True}
    )
    assert crit.startswith("**Critical failure** on your perception")


@pytest.mark.parametrize("skill, success, text", [
    ("Stealth", True, "You slip past the guards."),
    ("Stealth", False, "A floorboard creaks and the guard turns toward you."),
    ("Athletics", True, "You haul yourself over the wall."),
    ("Athletics", False, "Your fingers slip and you fall back into the mud."),
    ("Sleight_Of_Hand", True, "The lock clicks open."),
    ("Persuasion", False, "She folds her arms and refuses."),
    ("Intimidation", True, "He pales and steps back."),
    ("Deception", False, "The guard narrows his eyes."),
])
def test_short_skill_outcomes_are_not_weak(skill, success, text):
    assert is_weak_roll_narration(text, {"skill": skill, "success": success}) is False


@pytest.mark.parametrize("skill, success", [("Stealth", True), ("Athletics", False), ("Persuasion", True)])
def test_setup_only_narration_is_still_weak(skill, success):
    assert is_weak_roll_narration("You take a deep breath and begin.", {"skill": skill, "success": success})


def test_canned_outcome_lines_pass_their_own_check():
    from dm_scene import SKILL_OUTCOMES

    for skill, lines in SKILL_OUTCOMES.items():
        for outcome, texts in lines.items():
            for text in texts:
                roll = {"skill": skill, "success": outcome == "success"}
                assert not is_weak_roll_narration(text, roll), (skill, outcome, text)
