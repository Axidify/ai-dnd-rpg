"""The roll arbiter survives the malformed JSON real models send."""

import json

import pytest

import dm_arbiter
import llm_client
from dm_arbiter import get_arbiter_decision, get_fallback_decision, parse_arbiter_json

CLEAN = '{"action_type": "physical", "requires_roll": true, "skill": "Athletics", "dc": 12, "reasoning": "Forcing a gate"}'


def test_clean_json():
    assert parse_arbiter_json(CLEAN)["skill"] == "Athletics"


@pytest.mark.parametrize("wrapped", [
    f"```json\n{CLEAN}\n```",
    f"```\n{CLEAN}\n```",
    f"Here is my ruling:\n{CLEAN}\nHope that helps.",
])
def test_fences_and_prose_are_tolerated(wrapped):
    assert parse_arbiter_json(wrapped)["dc"] == 12


def test_truncated_reply_is_salvaged_when_essentials_arrived():
    truncated = ('{\n  "action_type": "physical",\n  "requires_roll": true,\n  "skill": "Athletics",\n'
                 '  "dc": 14,\n  "reasoning": "Forcing open a jammed')
    decision = parse_arbiter_json(truncated)
    assert decision["requires_roll"] is True
    assert decision["skill"] == "Athletics" and decision["dc"] == 14
    assert decision["reasoning"].startswith("Forcing open")


def test_truncated_no_roll_is_salvaged():
    decision = parse_arbiter_json('{"action_type": "social", "requires_roll": false, "skill": null, "dc": nu')
    assert decision["requires_roll"] is False and decision["skill"] is None


@pytest.mark.parametrize("garbage", ["", "Lying,", '{\n  "action_type', '{\n  "action'])
def test_unusable_replies_raise(garbage):
    with pytest.raises(json.JSONDecodeError):
        parse_arbiter_json(garbage)


def test_ai_decision_recovers_from_a_cut_off_reply(monkeypatch):
    replies = iter(['{\n  "action', CLEAN])
    monkeypatch.setattr(llm_client, "is_llm_configured", lambda: True)
    monkeypatch.setattr(llm_client, "generate_text", lambda *a, **k: next(replies))
    decision = get_arbiter_decision("I heave against the old gate", "A rusted gate")
    assert decision.source == "arbiter_ai" and decision.skill == "Athletics"


def test_arbiter_uses_the_classifier_budget(monkeypatch):
    seen = {}

    def fake_generate(prompt, **kwargs):
        seen.update(kwargs, prompt=prompt)
        return CLEAN

    monkeypatch.setattr(llm_client, "is_llm_configured", lambda: True)
    monkeypatch.setattr(llm_client, "generate_text", fake_generate)
    dm_arbiter.get_arbiter_ai_decision("I heave against the gate", "x" * 5000)
    assert seen["max_tokens"] == llm_client.CLASSIFIER_MAX_TOKENS >= 2048
    assert "x" * dm_arbiter.ARBITER_CONTEXT_CHARS in seen["prompt"]


def test_fallback_still_rolls_for_persuasion():
    decision = get_fallback_decision("I try to sway the captain")
    assert decision.requires_roll and decision.skill == "Persuasion"


def test_token_budgets_are_generous_and_env_overridable(monkeypatch):
    assert llm_client.NARRATION_MAX_TOKENS >= 4096
    monkeypatch.setenv("LLM_X_TOKENS", "1500")
    assert llm_client._env_int("LLM_X_TOKENS", 99) == 1500
    monkeypatch.setenv("LLM_X_TOKENS", "lots")
    assert llm_client._env_int("LLM_X_TOKENS", 99) == 99


def test_vllm_narration_uncapped_unless_configured(monkeypatch):
    monkeypatch.delenv("LLM_NARRATION_MAX_TOKENS", raising=False)
    assert llm_client._vllm_narration_limit() == {}
    monkeypatch.setenv("LLM_NARRATION_MAX_TOKENS", "3000")
    assert "max_tokens" in llm_client._vllm_narration_limit()
