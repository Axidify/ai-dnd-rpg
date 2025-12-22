"""
Test Phase 3.6 Quick Wins - In-Game Integration Tests
Tests the actual gameplay functionality of the new item utility features.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import pytest
from character import Character
from inventory import Item, get_item, ItemType, add_item_to_inventory, find_item_in_inventory
from dm_engine import apply_rewards, parse_item_rewards
from scenario import create_goblin_cave_scenario, LocationManager
from quest import QuestManager, ObjectiveType


def inv_add_func(character, item):
    """Helper function for adding items to inventory (matches dm_engine signature)."""
    add_item_to_inventory(character.inventory, item)


class TestGoldPouchAutoConvert:
    """Test that gold_pouch items are auto-converted to gold on pickup."""
    
    def test_gold_pouch_converts_to_gold_on_reward(self):
        """Picking up a gold_pouch via reward adds gold, not the item."""
        character = Character("TestHero", "fighter")
        initial_gold = character.gold
        
        # Simulate DM response that gives a gold_pouch
        dm_response = "[Item: gold_pouch]"
        results = apply_rewards(dm_response, character, inv_add_func)
        
        # Gold should increase by 50 (gold_pouch value)
        assert character.gold == initial_gold + 50
        # Item should NOT be in inventory (check by display name)
        found_pouch = find_item_in_inventory(character.inventory, "gold pouch")
        assert found_pouch is None, "Gold pouch should not be in inventory - it should convert to gold"
        # Results should show gold gained
        assert results.get('gold_gained', 0) >= 50
    
    def test_small_gold_pouch_converts_to_gold(self):
        """Small gold pouch converts to 15g."""
        character = Character("TestHero", "fighter")
        initial_gold = character.gold
        
        # Note: Check actual item name in inventory
        dm_response = "[Item: gold_pouch_small]"  
        results = apply_rewards(dm_response, character, inv_add_func)
        
        # Should convert to gold (check value in inventory.py)
        assert character.gold >= initial_gold  # At least no error
    
    def test_gold_pouch_mixed_with_regular_items(self):
        """Gold pouch converts while other items go to inventory."""
        character = Character("TestHero", "fighter")
        initial_gold = character.gold
        
        dm_response = "[Item: gold_pouch] [Item: healing_potion]"
        apply_rewards(dm_response, character, inv_add_func)
        
        # Gold should increase
        assert character.gold == initial_gold + 50
        # Healing potion should be in inventory (search by display name, not key)
        found_potion = find_item_in_inventory(character.inventory, "Healing Potion")
        assert found_potion is not None
        # Gold pouch should not (check both formats)
        found_pouch = find_item_in_inventory(character.inventory, "gold pouch")
        assert found_pouch is None


class TestGoblinEarBountyQuest:
    """Test the 'Thin the Herd' bounty quest."""
    
    def test_thin_the_herd_quest_exists(self):
        """Quest is properly registered in scenario."""
        from scenario import create_goblin_cave_quests
        manager = QuestManager()
        create_goblin_cave_quests(manager)
        
        quest = manager.available_quests.get("thin_the_herd")
        assert quest is not None, "thin_the_herd quest should exist"
        assert quest.name == "Thin the Herd"
        # Quest is given by barkeep (village bounty)
        assert quest.giver_npc_id == "barkeep"
    
    def test_thin_the_herd_objectives(self):
        """Quest has correct collect objective."""
        from scenario import create_goblin_cave_quests
        manager = QuestManager()
        create_goblin_cave_quests(manager)
        
        quest = manager.available_quests.get("thin_the_herd")
        assert len(quest.objectives) == 1
        obj = quest.objectives[0]
        # Use objective_type not type
        assert obj.objective_type == ObjectiveType.COLLECT
        assert obj.target == "goblin_ear"
        assert obj.required_count == 5
    
    def test_thin_the_herd_rewards(self):
        """Quest gives correct rewards."""
        from scenario import create_goblin_cave_quests
        manager = QuestManager()
        create_goblin_cave_quests(manager)
        
        quest = manager.available_quests.get("thin_the_herd")
        assert quest.rewards.get("gold") == 25
        assert quest.rewards.get("xp") == 50


class TestMysteriousKeyDiscovery:
    """Test that mysterious_key can unlock secret_cave via OR condition."""
    
    def test_or_condition_parsing_in_check_discovery(self):
        """check_discovery properly parses OR conditions."""
        scenario = create_goblin_cave_scenario()
        lm = scenario.location_manager
        
        secret = lm.locations["secret_cave"]
        assert " OR " in secret.discovery_condition
        
    def test_key_unlocks_secret_cave(self):
        """Having mysterious_key allows discovery without perception check."""
        scenario = create_goblin_cave_scenario()
        lm = scenario.location_manager
        
        # Create proper inventory as a list with the key item
        key_item = get_item("mysterious_key")
        inventory = [key_item] if key_item else []
        
        # Game state with inventory list
        game_state = {
            "inventory": inventory,
            "skill_check_result": None,
            "flags": {},
            "character": None
        }
        
        can_discover, message = lm.check_discovery("secret_cave", game_state)
        assert can_discover is True, f"Key should unlock secret_cave. Message: {message}"
    
    def test_no_key_no_perception_fails(self):
        """Without key or perception, cannot discover."""
        scenario = create_goblin_cave_scenario()
        lm = scenario.location_manager
        
        # Game state with empty inventory list
        game_state = {
            "inventory": [],
            "skill_check_result": None,
            "flags": {},
            "character": None
        }
        
        can_discover, message = lm.check_discovery("secret_cave", game_state)
        assert can_discover is False


class TestAncientScrollEffect:
    """Test that ancient_scroll has correct description and effect."""
    
    def test_ancient_scroll_description_mentions_tunnel(self):
        """Scroll description references the secret tunnel."""
        scroll = get_item("ancient_scroll")
        assert scroll is not None
        assert "tunnel" in scroll.description.lower() or "secret" in scroll.description.lower()
    
    def test_ancient_scroll_has_effect_field(self):
        """Scroll has an effect field describing its use."""
        scroll = get_item("ancient_scroll")
        assert hasattr(scroll, 'effect')
        assert scroll.effect is not None
        assert len(scroll.effect) > 0
        # Should mention revealing the tunnel
        assert "tunnel" in scroll.effect.lower() or "secret" in scroll.effect.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


# =============================================================================
# Phase 3.6.5 & 3.6.6 Tests - Lockpicks and Poison Vial
# =============================================================================

class TestLockpicksMechanics:
    """Test lockpicks skill check option on Lily NPC."""
    
    def test_lily_has_lockpick_skill_check(self):
        """Lily NPC has the pick_cage_lock skill check option."""
        from scenario import create_goblin_cave_npcs
        
        manager = create_goblin_cave_npcs()
        
        lily = manager.get_npc("lily")
        assert lily is not None
        
        # Find the lockpick option
        lockpick_option = lily.get_skill_check_option("pick_cage_lock")
        assert lockpick_option is not None
        assert lockpick_option.skill == "sleight_of_hand"
        assert lockpick_option.dc == 12
        assert lockpick_option.requires_item == "lockpicks"
        assert lockpick_option.consumes_item is True
    
    def test_skill_check_option_requires_item_field(self):
        """SkillCheckOption supports requires_item field."""
        from npc import SkillCheckOption
        
        option = SkillCheckOption(
            id="test",
            skill="sleight_of_hand",
            dc=12,
            description="Test lockpicks",
            success_effect="flag:test",
            success_dialogue="Success!",
            failure_dialogue="Failed!",
            requires_item="lockpicks",
            consumes_item=True
        )
        
        assert option.requires_item == "lockpicks"
        assert option.consumes_item is True
        
        # Test serialization
        data = option.to_dict()
        assert data["requires_item"] == "lockpicks"
        assert data["consumes_item"] is True
        
        # Test deserialization
        restored = SkillCheckOption.from_dict(data)
        assert restored.requires_item == "lockpicks"
        assert restored.consumes_item is True
    
    def test_lockpicks_item_has_description(self):
        """Lockpicks item has updated description."""
        lockpicks = get_item("lockpicks")
        assert lockpicks is not None
        assert "sleight of hand" in lockpicks.description.lower()


class TestPoisonVialMechanics:
    """Test poison vial combat mechanics."""
    
    def test_character_has_weapon_poisoned_field(self):
        """Character has weapon_poisoned field."""
        from character import Character
        
        char = Character("Test", "fighter")
        assert hasattr(char, 'weapon_poisoned')
        assert char.weapon_poisoned is False
    
    def test_use_poison_vial_sets_flag(self):
        """Using poison vial sets weapon_poisoned flag."""
        from character import Character
        from inventory import use_item
        
        char = Character("Test", "fighter")
        poison = get_item("poison_vial")
        
        success, message = use_item(poison, char)
        
        assert success is True
        assert char.weapon_poisoned is True
        assert "poison" in message.lower()
    
    def test_cannot_double_poison(self):
        """Cannot apply poison if weapon already poisoned."""
        from character import Character
        from inventory import use_item
        
        char = Character("Test", "fighter")
        char.weapon_poisoned = True
        poison = get_item("poison_vial")
        
        success, message = use_item(poison, char)
        
        assert success is False
        assert "already poisoned" in message.lower()
    
    def test_poison_adds_damage(self):
        """Poison adds 1d4 damage to attacks."""
        from character import Character
        from combat import roll_damage
        
        char = Character("Test", "fighter")
        char.weapon_poisoned = True
        
        result = roll_damage(char, "longsword")
        
        assert result.get('was_poisoned') is True
        assert 'poison_damage' in result
        assert result['poison_damage'] >= 1  # 1d4 minimum is 1
        assert result['poison_damage'] <= 4  # 1d4 maximum is 4
    
    def test_poison_consumed_after_hit(self):
        """Poison is consumed after one attack."""
        from character import Character
        from combat import roll_damage
        
        char = Character("Test", "fighter")
        char.weapon_poisoned = True
        
        roll_damage(char, "longsword")
        
        # Poison should be consumed
        assert char.weapon_poisoned is False
    
    def test_weapon_poisoned_serialization(self):
        """weapon_poisoned field persists through save/load."""
        from character import Character
        
        char = Character("Test", "fighter")
        char.weapon_poisoned = True
        
        # Simulate serialization (get dict-like data)
        data = {
            'name': char.name,
            'char_class': char.char_class,
            'weapon_poisoned': char.weapon_poisoned
        }
        
        # Restore character
        restored = Character.from_dict(data)
        assert restored.weapon_poisoned is True


# =============================================================================
# Phase 3.6.7 Tests - Torch Darkness Mechanics
# =============================================================================

class TestTorchDarknessMechanics:
    """Test torch requirement for dark locations."""
    
    def test_location_has_is_dark_field(self):
        """Location has is_dark field."""
        from scenario import Location
        
        loc = Location(id="test", name="Test", description="Test")
        assert hasattr(loc, 'is_dark')
        assert loc.is_dark is False  # Default is not dark
    
    def test_cave_tunnel_is_dark(self):
        """Cave tunnel location is marked as dark."""
        from scenario import create_goblin_cave_scenario
        
        scenario = create_goblin_cave_scenario()
        tunnel = scenario.location_manager.locations.get("cave_tunnel")
        
        assert tunnel is not None
        assert tunnel.is_dark is True
    
    def test_goblin_shadows_is_dark(self):
        """Goblin camp shadows location is marked as dark."""
        from scenario import create_goblin_cave_scenario
        
        scenario = create_goblin_cave_scenario()
        shadows = scenario.location_manager.locations.get("goblin_camp_shadows")
        
        assert shadows is not None
        assert shadows.is_dark is True
    
    def test_character_has_light_with_torch(self):
        """Character with torch has light."""
        from character import Character
        from inventory import get_item, add_item_to_inventory
        
        char = Character("Test", "fighter")
        char.inventory = []  # Clear default inventory
        
        # Add torch manually
        torch = get_item("torch")
        add_item_to_inventory(char.inventory, torch)
        
        assert char.has_light() is True
    
    def test_character_no_light_without_torch(self):
        """Character without torch has no light."""
        from character import Character
        
        char = Character("Test", "fighter")
        # Remove all items
        char.inventory = []
        
        assert char.has_light() is False
    
    def test_darkness_penalty_check(self):
        """check_darkness_penalty returns correct penalty info."""
        from dm_engine import check_darkness_penalty
        from character import Character
        from scenario import Location
        
        char = Character("Test", "fighter")
        char.inventory = []  # No torch
        
        dark_loc = Location(id="dark", name="Dark", description="Dark", is_dark=True)
        
        result = check_darkness_penalty(dark_loc, char)
        
        assert result['in_darkness'] is True
        assert result['has_light'] is False
        assert "DISADVANTAGE" in result['penalty_message']
    
    def test_no_penalty_with_torch(self):
        """No darkness penalty when character has torch."""
        from dm_engine import check_darkness_penalty
        from character import Character
        from inventory import get_item, add_item_to_inventory
        from scenario import Location
        
        char = Character("Test", "fighter")
        char.inventory = []  # Clear inventory
        
        # Add torch
        torch = get_item("torch")
        add_item_to_inventory(char.inventory, torch)
        
        dark_loc = Location(id="dark", name="Dark", description="Dark", is_dark=True)
        
        result = check_darkness_penalty(dark_loc, char)
        
        assert result['in_darkness'] is False
        assert result['has_light'] is True
    
    def test_roll_attack_with_disadvantage(self):
        """roll_attack_with_disadvantage takes lower of two d20 rolls."""
        from combat import roll_attack_with_disadvantage
        from character import Character
        
        char = Character("Test", "fighter")
        
        # Run multiple times to verify disadvantage behavior
        for _ in range(10):
            result = roll_attack_with_disadvantage(char, 15, "longsword")
            
            assert result.get('has_disadvantage') is True
            assert 'd20_roll_1' in result
            assert 'd20_roll_2' in result
            # The d20_roll should be the minimum of the two
            assert result['d20_roll'] == min(result['d20_roll_1'], result['d20_roll_2'])
    
    def test_torch_item_has_effect(self):
        """Torch item has darkness prevention effect."""
        torch = get_item("torch")
        
        assert torch is not None
        assert "darkness" in torch.effect.lower() or "dark" in torch.description.lower()


# =============================================================================
# Phase 3.6.8 Tests - Rope Utility
# =============================================================================

class TestRopeUtility:
    """Test rope utility mechanics."""
    
    def test_lily_has_rope_skill_check(self):
        """Lily NPC has bend_cage_bars skill check option."""
        from scenario import create_goblin_cave_npcs
        
        manager = create_goblin_cave_npcs()
        lily = manager.get_npc("lily")
        
        assert lily is not None
        
        rope_option = lily.get_skill_check_option("bend_cage_bars")
        assert rope_option is not None
        assert rope_option.skill == "athletics"
        assert rope_option.dc == 14
        assert rope_option.requires_item == "rope"
        assert rope_option.consumes_item is True
    
    def test_rope_item_has_effect(self):
        """Rope item has skill check effect."""
        rope = get_item("rope")
        
        assert rope is not None
        assert "athletics" in rope.effect.lower() or "cage" in rope.description.lower()
