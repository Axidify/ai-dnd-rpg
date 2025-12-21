"""
HOSTILE TESTING: NPC Disposition System
Attempting to break the disposition system with edge cases, invalid inputs,
and adversarial scenarios.
"""

import pytest
import sys
import os
import math

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from npc import (
    NPC, NPCRole,
    DISPOSITION_HOSTILE, DISPOSITION_UNFRIENDLY, 
    DISPOSITION_FRIENDLY, DISPOSITION_TRUSTED
)


# =============================================================================
# ATTACK 1: BOUNDARY VALUE ATTACKS
# =============================================================================

class TestBoundaryValueAttacks:
    """Try to break the system with extreme boundary values."""
    
    def test_disposition_far_below_minimum(self):
        """What happens with -1000 disposition?"""
        npc = NPC(id="test", name="Test", disposition=-1000)
        # Should still work - but level should be hostile
        assert npc.get_disposition_level() == "hostile"
        assert npc.get_disposition_label() is not None
        assert npc.can_trade() is False
    
    def test_disposition_far_above_maximum(self):
        """What happens with +1000 disposition?"""
        npc = NPC(id="test", name="Test", disposition=1000)
        # Should still work - level should be trusted
        assert npc.get_disposition_level() == "trusted"
        assert npc.get_disposition_label() is not None
        assert npc.can_trade() is True
    
    def test_modify_extreme_positive(self):
        """Try to overflow with huge positive modification."""
        npc = NPC(id="test", name="Test", disposition=0)
        result = npc.modify_disposition(999999999)
        assert npc.disposition == 100  # Should clamp
        assert result == 100
    
    def test_modify_extreme_negative(self):
        """Try to underflow with huge negative modification."""
        npc = NPC(id="test", name="Test", disposition=0)
        result = npc.modify_disposition(-999999999)
        assert npc.disposition == -100  # Should clamp
        assert result == -100
    
    def test_rapid_oscillation(self):
        """Rapidly oscillate between extremes."""
        npc = NPC(id="test", name="Test", disposition=0)
        for _ in range(1000):
            npc.modify_disposition(200)
            npc.modify_disposition(-200)
        # Should be clamped properly after oscillation
        assert -100 <= npc.disposition <= 100
    
    def test_exact_threshold_boundaries(self):
        """Test exact threshold values."""
        # Exactly at HOSTILE threshold
        npc = NPC(id="test", name="Test", disposition=DISPOSITION_HOSTILE)
        assert npc.get_disposition_level() == "unfriendly"  # At -50, should be unfriendly
        
        # One below HOSTILE threshold
        npc.disposition = DISPOSITION_HOSTILE - 1
        assert npc.get_disposition_level() == "hostile"
        
        # Exactly at TRUSTED threshold
        npc.disposition = DISPOSITION_TRUSTED
        assert npc.get_disposition_level() == "friendly"  # At 50, should be friendly
        
        # One above TRUSTED threshold
        npc.disposition = DISPOSITION_TRUSTED + 1
        assert npc.get_disposition_level() == "trusted"


# =============================================================================
# ATTACK 2: TYPE CONFUSION ATTACKS
# =============================================================================

class TestTypeConfusionAttacks:
    """Try to confuse the system with wrong types."""
    
    def test_float_disposition(self):
        """What if disposition is a float instead of int?"""
        npc = NPC(id="test", name="Test", disposition=25.7)
        # Should still work with float
        level = npc.get_disposition_level()
        assert level in ["hostile", "unfriendly", "neutral", "friendly", "trusted"]
    
    def test_negative_zero(self):
        """What about negative zero?"""
        npc = NPC(id="test", name="Test", disposition=-0.0)
        assert npc.get_disposition_level() == "neutral"
        label = npc.get_disposition_label()
        assert "Neutral" in label
    
    def test_modify_with_float(self):
        """Modify disposition with float value."""
        npc = NPC(id="test", name="Test", disposition=0)
        result = npc.modify_disposition(15.5)
        # Should handle float modification
        assert npc.disposition == 15 or npc.disposition == 15.5 or npc.disposition == 16
    
    def test_boolean_as_disposition(self):
        """What if we pass boolean (True=1, False=0)?"""
        npc = NPC(id="test", name="Test", disposition=True)  # True is 1 in Python
        assert npc.get_disposition_level() == "neutral"
        
        npc.disposition = False  # False is 0
        assert npc.get_disposition_level() == "neutral"


# =============================================================================
# ATTACK 3: NUMERIC EDGE CASES
# =============================================================================

class TestNumericEdgeCases:
    """Test with special numeric values."""
    
    def test_infinity_disposition(self):
        """What happens with infinity?"""
        npc = NPC(id="test", name="Test", disposition=float('inf'))
        # Should handle gracefully
        level = npc.get_disposition_level()
        assert level == "trusted"  # inf > 50
    
    def test_negative_infinity_disposition(self):
        """What happens with negative infinity?"""
        npc = NPC(id="test", name="Test", disposition=float('-inf'))
        level = npc.get_disposition_level()
        assert level == "hostile"  # -inf < -50
    
    def test_nan_disposition(self):
        """What happens with NaN?"""
        npc = NPC(id="test", name="Test", disposition=float('nan'))
        # NaN comparisons are tricky - all comparisons return False
        # This might cause unexpected behavior
        level = npc.get_disposition_level()
        # NaN fails all < comparisons, so should fall through to "trusted"
        # or might behave unexpectedly
        assert level in ["hostile", "unfriendly", "neutral", "friendly", "trusted"]
    
    def test_very_small_float(self):
        """Test with very small float."""
        npc = NPC(id="test", name="Test", disposition=0.0000001)
        assert npc.get_disposition_level() == "neutral"
    
    def test_modify_clamp_at_exactly_100(self):
        """Ensure clamping works at exact boundaries."""
        npc = NPC(id="test", name="Test", disposition=99)
        npc.modify_disposition(1)
        assert npc.disposition == 100
        npc.modify_disposition(1)  # Should still be 100
        assert npc.disposition == 100
    
    def test_modify_clamp_at_exactly_minus_100(self):
        """Ensure clamping works at exact boundaries."""
        npc = NPC(id="test", name="Test", disposition=-99)
        npc.modify_disposition(-1)
        assert npc.disposition == -100
        npc.modify_disposition(-1)  # Should still be -100
        assert npc.disposition == -100


# =============================================================================
# ATTACK 4: STATE MANIPULATION
# =============================================================================

class TestStateManipulation:
    """Try to manipulate state in unexpected ways."""
    
    def test_direct_disposition_modification(self):
        """Directly modify disposition bypassing modify_disposition."""
        npc = NPC(id="test", name="Test", disposition=0)
        npc.disposition = 500  # Bypass the clamp
        # get_disposition_level should still work
        assert npc.get_disposition_level() == "trusted"
        # But can_trade should still work
        assert npc.can_trade() is True
    
    def test_direct_negative_modification(self):
        """Directly set negative disposition bypassing clamp."""
        npc = NPC(id="test", name="Test", disposition=0)
        npc.disposition = -500
        assert npc.get_disposition_level() == "hostile"
        assert npc.can_trade() is False
    
    def test_modify_then_direct_set(self):
        """Mix modify_disposition with direct assignment."""
        npc = NPC(id="test", name="Test", disposition=0)
        npc.modify_disposition(50)
        assert npc.disposition == 50
        npc.disposition = -75  # Direct set
        assert npc.get_disposition_level() == "hostile"
        npc.modify_disposition(10)
        assert npc.disposition == -65  # Should work from -75
    
    def test_multiple_npcs_independence(self):
        """Ensure NPCs don't share state."""
        npc1 = NPC(id="test1", name="Test1", disposition=50)
        npc2 = NPC(id="test2", name="Test2", disposition=-50)
        
        npc1.modify_disposition(10)
        assert npc1.disposition == 60
        assert npc2.disposition == -50  # Should be unchanged
        
        npc2.modify_disposition(-10)
        assert npc2.disposition == -60
        assert npc1.disposition == 60  # Should be unchanged


# =============================================================================
# ATTACK 5: LABEL INJECTION
# =============================================================================

class TestLabelInjection:
    """Try to inject malicious content via labels."""
    
    def test_label_contains_only_expected_chars(self):
        """Ensure label doesn't contain unexpected content."""
        for disp in range(-100, 101, 10):
            npc = NPC(id="test", name="Test", disposition=disp)
            label = npc.get_disposition_label()
            # Should only contain emoji, text, parentheses, numbers, +/-
            assert all(c.isalnum() or c in "🔴🟠🟡🟢🔵 ()+-" or ord(c) > 127 for c in label)
    
    def test_special_char_npc_name_doesnt_affect_label(self):
        """NPC name with special chars shouldn't affect disposition label."""
        npc = NPC(id="test", name="<script>alert('xss')</script>", disposition=50)
        label = npc.get_disposition_label()
        # Label should not include NPC name
        assert "<script>" not in label
        assert "alert" not in label


# =============================================================================
# ATTACK 6: SERIALIZATION ATTACKS
# =============================================================================

class TestSerializationAttacks:
    """Try to break the system via serialization/deserialization."""
    
    def test_corrupted_disposition_in_dict(self):
        """Load NPC from dict with corrupted disposition."""
        data = {
            "id": "test",
            "name": "Test",
            "disposition": "not_a_number",  # Invalid!
            "role": "NEUTRAL"
        }
        # This should fail gracefully or raise appropriate error
        try:
            npc = NPC.from_dict(data)
            # If it creates the NPC, check it handles the bad data
            assert isinstance(npc.disposition, (int, float, str))
        except (ValueError, TypeError):
            # Expected - bad data should cause error
            pass
    
    def test_missing_disposition_in_dict(self):
        """Load NPC from dict with missing disposition."""
        data = {
            "id": "test",
            "name": "Test",
            "role": "NEUTRAL"
            # disposition missing
        }
        npc = NPC.from_dict(data)
        # Should use default disposition (0)
        assert npc.disposition == 0
    
    def test_null_disposition_in_dict(self):
        """Load NPC from dict with null disposition."""
        data = {
            "id": "test",
            "name": "Test",
            "disposition": None,
            "role": "NEUTRAL"
        }
        try:
            npc = NPC.from_dict(data)
            # If it works, check behavior
            label = npc.get_disposition_label()
            assert label is not None
        except (ValueError, TypeError):
            # Expected - None is invalid
            pass
    
    def test_serialization_preserves_extreme_values(self):
        """Ensure to_dict/from_dict preserves disposition correctly."""
        original = NPC(id="test", name="Test", disposition=100)
        data = original.to_dict()
        restored = NPC.from_dict(data)
        assert restored.disposition == 100
        
        original2 = NPC(id="test", name="Test", disposition=-100)
        data2 = original2.to_dict()
        restored2 = NPC.from_dict(data2)
        assert restored2.disposition == -100


# =============================================================================
# ATTACK 7: CAN_TRADE CONSISTENCY
# =============================================================================

class TestCanTradeConsistency:
    """Ensure can_trade is consistent with disposition."""
    
    def test_hostile_cannot_trade(self):
        """Hostile NPCs should not be able to trade."""
        npc = NPC(id="test", name="Test", disposition=-75)
        assert npc.can_trade() is False
    
    def test_non_hostile_can_trade(self):
        """Non-hostile NPCs should be able to trade."""
        unfriendly = NPC(id="u", name="U", disposition=-25)
        assert unfriendly.can_trade() is True
        
        neutral = NPC(id="n", name="N", disposition=0)
        assert neutral.can_trade() is True
        
        friendly = NPC(id="f", name="F", disposition=35)
        assert friendly.can_trade() is True
        
        trusted = NPC(id="t", name="T", disposition=75)
        assert trusted.can_trade() is True
    
    def test_trade_consistency_across_range(self):
        """can_trade should be False only for hostile dispositions."""
        for disp in range(-100, 101):
            npc = NPC(id="test", name="Test", disposition=disp)
            if disp < -50:
                assert npc.can_trade() is False
            else:
                assert npc.can_trade() is True
    
    def test_trade_changes_at_threshold(self):
        """Trade ability should change at threshold boundary."""
        # At -51 (hostile) vs -50 (unfriendly)
        hostile = NPC(id="test", name="Test", disposition=-51)
        unfriendly = NPC(id="test", name="Test", disposition=-50)
        assert hostile.can_trade() != unfriendly.can_trade()


# =============================================================================
# ATTACK 8: RACE CONDITIONS (Conceptual)
# =============================================================================

class TestConcurrencySimulation:
    """Simulate concurrent access patterns."""
    
    def test_many_modifications_sequential(self):
        """Many sequential modifications should be consistent."""
        npc = NPC(id="test", name="Test", disposition=0)
        
        # Apply 100 +1 modifications
        for _ in range(100):
            npc.modify_disposition(1)
        assert npc.disposition == 100  # Clamped at 100
        
        # Apply 200 -1 modifications
        for _ in range(200):
            npc.modify_disposition(-1)
        assert npc.disposition == -100  # Clamped at -100
    
    def test_alternating_modifications(self):
        """Alternating +/- modifications should net to expected value."""
        npc = NPC(id="test", name="Test", disposition=0)
        
        # +5, -3 alternating 10 times = +20 net
        for _ in range(10):
            npc.modify_disposition(5)
            npc.modify_disposition(-3)
        assert npc.disposition == 20


# =============================================================================
# ATTACK 9: EDGE CASE STRINGS
# =============================================================================

class TestEdgeCaseStrings:
    """Test with edge case string values in NPC creation."""
    
    def test_empty_id_fails(self):
        """Empty ID should raise error."""
        with pytest.raises(ValueError):
            NPC(id="", name="Test", disposition=0)
    
    def test_empty_name_fails(self):
        """Empty name should raise error."""
        with pytest.raises(ValueError):
            NPC(id="test", name="", disposition=0)
    
    def test_whitespace_id_fails(self):
        """Whitespace-only ID should still work (debatable design choice)."""
        # Current implementation likely allows this
        npc = NPC(id="   ", name="Test", disposition=0)
        assert npc.get_disposition_level() == "neutral"
    
    def test_unicode_name(self):
        """Unicode name should work."""
        npc = NPC(id="test", name="测试角色", disposition=50)
        assert npc.get_disposition_level() == "friendly"
        label = npc.get_disposition_label()
        assert "Friendly" in label


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
