"""
Test suite for NPC Disposition/Reputation System (Phase 3.3, Priority 6, Step 1)
Tests disposition constants, helper functions, and threshold behaviors.
"""

import pytest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from npc import (
    NPC, NPCRole,
    DISPOSITION_HOSTILE, DISPOSITION_UNFRIENDLY, 
    DISPOSITION_FRIENDLY, DISPOSITION_TRUSTED
)


# =============================================================================
# TEST: DISPOSITION CONSTANTS
# =============================================================================

class TestDispositionConstants:
    """Test that disposition constants are defined correctly."""
    
    def test_hostile_threshold(self):
        """HOSTILE threshold should be -50."""
        assert DISPOSITION_HOSTILE == -50
    
    def test_unfriendly_threshold(self):
        """UNFRIENDLY threshold should be -10."""
        assert DISPOSITION_UNFRIENDLY == -10
    
    def test_friendly_threshold(self):
        """FRIENDLY threshold should be 10."""
        assert DISPOSITION_FRIENDLY == 10
    
    def test_trusted_threshold(self):
        """TRUSTED threshold should be 50."""
        assert DISPOSITION_TRUSTED == 50
    
    def test_threshold_ordering(self):
        """Thresholds should be in ascending order."""
        assert DISPOSITION_HOSTILE < DISPOSITION_UNFRIENDLY < DISPOSITION_FRIENDLY < DISPOSITION_TRUSTED


# =============================================================================
# TEST: get_disposition_level()
# =============================================================================

class TestGetDispositionLevel:
    """Test get_disposition_level() returns correct level string."""
    
    def test_hostile_at_minus_100(self):
        """Disposition -100 should be hostile."""
        npc = NPC(id="test", name="Test", disposition=-100)
        assert npc.get_disposition_level() == "hostile"
    
    def test_hostile_at_minus_51(self):
        """Disposition -51 should be hostile."""
        npc = NPC(id="test", name="Test", disposition=-51)
        assert npc.get_disposition_level() == "hostile"
    
    def test_unfriendly_at_minus_50(self):
        """Disposition -50 (at threshold) should be unfriendly."""
        npc = NPC(id="test", name="Test", disposition=-50)
        assert npc.get_disposition_level() == "unfriendly"
    
    def test_unfriendly_at_minus_11(self):
        """Disposition -11 should be unfriendly."""
        npc = NPC(id="test", name="Test", disposition=-11)
        assert npc.get_disposition_level() == "unfriendly"
    
    def test_neutral_at_minus_10(self):
        """Disposition -10 (at threshold) should be neutral."""
        npc = NPC(id="test", name="Test", disposition=-10)
        assert npc.get_disposition_level() == "neutral"
    
    def test_neutral_at_zero(self):
        """Disposition 0 should be neutral."""
        npc = NPC(id="test", name="Test", disposition=0)
        assert npc.get_disposition_level() == "neutral"
    
    def test_neutral_at_10(self):
        """Disposition 10 (at threshold) should be neutral."""
        npc = NPC(id="test", name="Test", disposition=10)
        assert npc.get_disposition_level() == "neutral"
    
    def test_friendly_at_11(self):
        """Disposition 11 should be friendly."""
        npc = NPC(id="test", name="Test", disposition=11)
        assert npc.get_disposition_level() == "friendly"
    
    def test_friendly_at_50(self):
        """Disposition 50 (at threshold) should be friendly."""
        npc = NPC(id="test", name="Test", disposition=50)
        assert npc.get_disposition_level() == "friendly"
    
    def test_trusted_at_51(self):
        """Disposition 51 should be trusted."""
        npc = NPC(id="test", name="Test", disposition=51)
        assert npc.get_disposition_level() == "trusted"
    
    def test_trusted_at_100(self):
        """Disposition 100 should be trusted."""
        npc = NPC(id="test", name="Test", disposition=100)
        assert npc.get_disposition_level() == "trusted"


# =============================================================================
# TEST: get_disposition_label()
# =============================================================================

class TestGetDispositionLabel:
    """Test get_disposition_label() returns correct formatted label."""
    
    def test_hostile_label_format(self):
        """Hostile label should have red circle and negative value."""
        npc = NPC(id="test", name="Test", disposition=-75)
        label = npc.get_disposition_label()
        assert "🔴" in label
        assert "Hostile" in label
        assert "-75" in label
    
    def test_unfriendly_label_format(self):
        """Unfriendly label should have orange circle."""
        npc = NPC(id="test", name="Test", disposition=-25)
        label = npc.get_disposition_label()
        assert "🟠" in label
        assert "Unfriendly" in label
        assert "-25" in label
    
    def test_neutral_label_format(self):
        """Neutral label should have yellow circle."""
        npc = NPC(id="test", name="Test", disposition=0)
        label = npc.get_disposition_label()
        assert "🟡" in label
        assert "Neutral" in label
        assert "0" in label
    
    def test_friendly_label_format(self):
        """Friendly label should have green circle and positive value."""
        npc = NPC(id="test", name="Test", disposition=35)
        label = npc.get_disposition_label()
        assert "🟢" in label
        assert "Friendly" in label
        assert "+35" in label
    
    def test_trusted_label_format(self):
        """Trusted label should have blue circle."""
        npc = NPC(id="test", name="Test", disposition=75)
        label = npc.get_disposition_label()
        assert "🔵" in label
        assert "Trusted" in label
        assert "+75" in label
    
    def test_positive_sign_for_positive_values(self):
        """Positive values should have + sign."""
        npc = NPC(id="test", name="Test", disposition=25)
        label = npc.get_disposition_label()
        assert "+25" in label
    
    def test_no_sign_for_zero(self):
        """Zero should not have a sign prefix."""
        npc = NPC(id="test", name="Test", disposition=0)
        label = npc.get_disposition_label()
        # Should contain just "0" not "+0"
        assert "(0)" in label or "( 0)" in label


# =============================================================================
# TEST: can_trade()
# =============================================================================

class TestCanTrade:
    """Test can_trade() returns correct interaction availability."""
    
    def test_hostile_cannot_trade(self):
        """Hostile NPCs refuse to interact positively."""
        npc = NPC(id="test", name="Test", disposition=-75)
        assert npc.can_trade() is False
    
    def test_unfriendly_can_trade(self):
        """Unfriendly NPCs can still interact."""
        npc = NPC(id="test", name="Test", disposition=-25)
        assert npc.can_trade() is True
    
    def test_neutral_can_trade(self):
        """Neutral NPCs can trade."""
        npc = NPC(id="test", name="Test", disposition=0)
        assert npc.can_trade() is True
    
    def test_friendly_can_trade(self):
        """Friendly NPCs can trade."""
        npc = NPC(id="test", name="Test", disposition=35)
        assert npc.can_trade() is True
    
    def test_trusted_can_trade(self):
        """Trusted NPCs can trade."""
        npc = NPC(id="test", name="Test", disposition=75)
        assert npc.can_trade() is True
    
    def test_boundary_hostile_cannot_trade(self):
        """At -51 (just hostile), cannot trade."""
        npc = NPC(id="test", name="Test", disposition=-51)
        assert npc.can_trade() is False
    
    def test_boundary_unfriendly_can_trade(self):
        """At -50 (just unfriendly), can trade."""
        npc = NPC(id="test", name="Test", disposition=-50)
        assert npc.can_trade() is True


# =============================================================================
# TEST: modify_disposition()
# =============================================================================

class TestModifyDisposition:
    """Test modify_disposition() correctly changes and clamps values."""
    
    def test_increase_disposition(self):
        """Should increase disposition by given amount."""
        npc = NPC(id="test", name="Test", disposition=0)
        result = npc.modify_disposition(25)
        assert npc.disposition == 25
        assert result == 25
    
    def test_decrease_disposition(self):
        """Should decrease disposition by negative amount."""
        npc = NPC(id="test", name="Test", disposition=50)
        result = npc.modify_disposition(-30)
        assert npc.disposition == 20
        assert result == 20
    
    def test_clamp_at_max_100(self):
        """Should clamp at maximum 100."""
        npc = NPC(id="test", name="Test", disposition=80)
        result = npc.modify_disposition(50)
        assert npc.disposition == 100
        assert result == 100
    
    def test_clamp_at_min_minus_100(self):
        """Should clamp at minimum -100."""
        npc = NPC(id="test", name="Test", disposition=-80)
        result = npc.modify_disposition(-50)
        assert npc.disposition == -100
        assert result == -100
    
    def test_modify_zero(self):
        """Modifying by 0 should not change disposition."""
        npc = NPC(id="test", name="Test", disposition=25)
        result = npc.modify_disposition(0)
        assert npc.disposition == 25
        assert result == 25
    
    def test_modify_changes_level(self):
        """Modifying should change disposition level when crossing threshold."""
        npc = NPC(id="test", name="Test", disposition=5)
        assert npc.get_disposition_level() == "neutral"
        npc.modify_disposition(10)
        assert npc.get_disposition_level() == "friendly"
    
    def test_returns_new_value(self):
        """Should return the new disposition value."""
        npc = NPC(id="test", name="Test", disposition=0)
        result = npc.modify_disposition(15)
        assert result == 15
        assert result == npc.disposition


# =============================================================================
# TEST: EDGE CASES AND INTEGRATION
# =============================================================================

class TestDispositionEdgeCases:
    """Test edge cases and integration between disposition methods."""
    
    def test_all_levels_have_labels(self):
        """Every disposition level should have a formatted label."""
        test_values = [-100, -75, -50, -25, -10, 0, 10, 25, 50, 75, 100]
        for val in test_values:
            npc = NPC(id="test", name="Test", disposition=val)
            label = npc.get_disposition_label()
            assert label is not None
            assert len(label) > 0
            assert str(abs(val)) in label or "0" in label
    
    def test_can_trade_follows_disposition(self):
        """can_trade() should match disposition level."""
        hostile = NPC(id="test", name="Test", disposition=-75)
        unfriendly = NPC(id="test", name="Test", disposition=-25)
        neutral = NPC(id="test", name="Test", disposition=0)
        friendly = NPC(id="test", name="Test", disposition=35)
        trusted = NPC(id="test", name="Test", disposition=75)
        
        # Only hostile cannot trade
        assert hostile.can_trade() is False
        assert unfriendly.can_trade() is True
        assert neutral.can_trade() is True
        assert friendly.can_trade() is True
        assert trusted.can_trade() is True
    
    def test_default_disposition_is_neutral(self):
        """NPC with default disposition should be neutral."""
        npc = NPC(id="test", name="Test")
        assert npc.disposition == 0
        assert npc.get_disposition_level() == "neutral"
        assert npc.can_trade() is True


# =============================================================================
# TEST: calculate_gift_disposition()
# =============================================================================

class TestGiftDisposition:
    """Test gift disposition calculation based on item value."""
    
    def test_gift_zero_value(self):
        """Zero value item gives no disposition."""
        from npc import calculate_gift_disposition
        assert calculate_gift_disposition(0) == 0
    
    def test_gift_cheap_item(self):
        """Cheap item (1-10g) gives +5 disposition."""
        from npc import calculate_gift_disposition
        assert calculate_gift_disposition(5) == 5
        assert calculate_gift_disposition(10) == 5
    
    def test_gift_modest_item(self):
        """Modest item (11-25g) gives +8 disposition."""
        from npc import calculate_gift_disposition
        assert calculate_gift_disposition(15) == 8
        assert calculate_gift_disposition(25) == 8
    
    def test_gift_nice_item(self):
        """Nice item (26-50g) gives +12 disposition."""
        from npc import calculate_gift_disposition
        assert calculate_gift_disposition(30) == 12
        assert calculate_gift_disposition(50) == 12
    
    def test_gift_generous_item(self):
        """Generous item (51-100g) gives +15 disposition."""
        from npc import calculate_gift_disposition
        assert calculate_gift_disposition(75) == 15
        assert calculate_gift_disposition(100) == 15
    
    def test_gift_extravagant_item(self):
        """Extravagant item (100+g) gives +20 disposition."""
        from npc import calculate_gift_disposition
        assert calculate_gift_disposition(150) == 20
        assert calculate_gift_disposition(500) == 20
    
    def test_gift_negative_value(self):
        """Negative value item gives no disposition."""
        from npc import calculate_gift_disposition
        assert calculate_gift_disposition(-10) == 0


# =============================================================================
# TEST: Quest Disposition Rewards
# =============================================================================

class TestQuestDisposition:
    """Test quest disposition rewards based on quest type."""
    
    def test_main_quest_reward(self):
        """Main quest gives +25 disposition."""
        from quest import Quest, QuestType
        quest = Quest(id="main", name="Main Quest", description="Test", quest_type=QuestType.MAIN)
        assert quest.get_disposition_reward() == 25
    
    def test_side_quest_reward(self):
        """Side quest gives +15 disposition."""
        from quest import Quest, QuestType
        quest = Quest(id="side", name="Side Quest", description="Test", quest_type=QuestType.SIDE)
        assert quest.get_disposition_reward() == 15
    
    def test_minor_quest_reward(self):
        """Minor quest gives +10 disposition."""
        from quest import Quest, QuestType
        quest = Quest(id="minor", name="Minor Quest", description="Test", quest_type=QuestType.MINOR)
        assert quest.get_disposition_reward() == 10
    
    def test_main_quest_penalty(self):
        """Main quest failure gives -15 disposition."""
        from quest import Quest, QuestType
        quest = Quest(id="main", name="Main Quest", description="Test", quest_type=QuestType.MAIN)
        assert quest.get_disposition_penalty() == -15
    
    def test_side_quest_penalty(self):
        """Side quest failure gives -10 disposition."""
        from quest import Quest, QuestType
        quest = Quest(id="side", name="Side Quest", description="Test", quest_type=QuestType.SIDE)
        assert quest.get_disposition_penalty() == -10
    
    def test_minor_quest_penalty(self):
        """Minor quest failure gives -5 disposition."""
        from quest import Quest, QuestType
        quest = Quest(id="minor", name="Minor Quest", description="Test", quest_type=QuestType.MINOR)
        assert quest.get_disposition_penalty() == -5
    
    def test_default_quest_type_is_side(self):
        """Default quest type is SIDE."""
        from quest import Quest, QuestType
        quest = Quest(id="test", name="Test", description="Test")
        assert quest.quest_type == QuestType.SIDE
    
    def test_quest_type_serialization(self):
        """Quest type should serialize and deserialize correctly."""
        from quest import Quest, QuestType
        quest = Quest(id="main", name="Main Quest", description="Test", quest_type=QuestType.MAIN)
        data = quest.to_dict()
        loaded = Quest.from_dict(data)
        assert loaded.quest_type == QuestType.MAIN


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
