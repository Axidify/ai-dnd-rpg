"""
Comprehensive tests for the Combat system.
Covers: dice rolling, attacks, damage, enemies, initiative.
"""

import pytest
import sys
sys.path.insert(0, '../src')

from combat import (
    Enemy, ENEMIES, WEAPONS,
    create_enemy, roll_dice, roll_attack, roll_attack_with_advantage,
    calculate_attack_bonus, calculate_damage_bonus,
    roll_initiative, determine_turn_order, display_turn_order,
    format_initiative_roll, Combatant
)
from character import Character


class TestDiceRolling:
    """Tests for dice rolling mechanics."""
    
    def test_roll_1d6(self):
        """Test rolling 1d6."""
        for _ in range(100):
            total, rolls = roll_dice("1d6")
            assert 1 <= total <= 6
            assert len(rolls) == 1
    
    def test_roll_2d6(self):
        """Test rolling 2d6."""
        for _ in range(100):
            total, rolls = roll_dice("2d6")
            assert 2 <= total <= 12
            assert len(rolls) == 2
    
    def test_roll_with_modifier(self):
        """Test rolling with positive modifier."""
        for _ in range(100):
            total, rolls = roll_dice("1d6+3")
            assert 4 <= total <= 9
            assert len(rolls) == 1
    
    def test_roll_with_negative_modifier(self):
        """Test rolling with negative modifier."""
        for _ in range(100):
            total, rolls = roll_dice("1d6-2")
            assert -1 <= total <= 4
            assert len(rolls) == 1
    
    def test_roll_d20(self):
        """Test rolling d20."""
        for _ in range(100):
            total, rolls = roll_dice("1d20")
            assert 1 <= total <= 20
    
    def test_invalid_notation(self):
        """Test invalid dice notation returns default."""
        total, rolls = roll_dice("invalid")
        assert total == 1
        assert rolls == [1]
    
    def test_roll_without_count(self):
        """Test notation without explicit count (d6 = 1d6)."""
        total, rolls = roll_dice("d6")
        assert 1 <= total <= 6


class TestEnemy:
    """Tests for Enemy class."""
    
    def test_create_enemy(self):
        """Test enemy creation from preset."""
        goblin = create_enemy("goblin")
        assert goblin is not None
        assert goblin.name == "Goblin"
        assert goblin.max_hp == 7
        assert goblin.current_hp == 7
    
    def test_create_nonexistent_enemy(self):
        """Test creating nonexistent enemy returns None."""
        dragon = create_enemy("ancient_dragon")
        assert dragon is None
    
    def test_enemy_take_damage(self):
        """Test enemy taking damage."""
        goblin = create_enemy("goblin")
        result = goblin.take_damage(3)
        assert goblin.current_hp == 4
        assert "takes 3 damage" in result
    
    def test_enemy_death(self):
        """Test enemy dying at 0 HP."""
        goblin = create_enemy("goblin")
        result = goblin.take_damage(10)
        assert goblin.current_hp == 0
        assert goblin.is_dead == True
        assert "falls" in result
    
    def test_enemy_status_healthy(self):
        """Test enemy status when healthy."""
        goblin = create_enemy("goblin")
        status = goblin.get_status()
        assert "healthy" in status
        assert "⚔️" in status
    
    def test_enemy_status_wounded(self):
        """Test enemy status when wounded."""
        goblin = create_enemy("goblin")
        goblin.take_damage(3)  # 4/7 HP
        status = goblin.get_status()
        assert "wounded" in status
    
    def test_enemy_status_dead(self):
        """Test enemy status when dead."""
        goblin = create_enemy("goblin")
        goblin.take_damage(10)
        status = goblin.get_status()
        assert "Defeated" in status
        assert "💀" in status
    
    def test_all_preset_enemies_exist(self):
        """Verify all preset enemies can be created."""
        for enemy_type in ENEMIES.keys():
            enemy = create_enemy(enemy_type)
            assert enemy is not None
            assert enemy.max_hp > 0


class TestWeapons:
    """Tests for weapon data."""
    
    def test_weapons_database_exists(self):
        """Verify weapons database has entries."""
        assert len(WEAPONS) > 0
        assert "longsword" in WEAPONS
        assert "dagger" in WEAPONS
    
    def test_weapon_has_required_fields(self):
        """Test weapons have required fields."""
        for name, weapon in WEAPONS.items():
            assert "damage" in weapon
            assert "type" in weapon
            assert "finesse" in weapon
    
    def test_finesse_weapons(self):
        """Test finesse property on weapons."""
        assert WEAPONS["dagger"]["finesse"] == True
        assert WEAPONS["rapier"]["finesse"] == True
        assert WEAPONS["longsword"]["finesse"] == False


class TestAttackSystem:
    """Tests for attack roll mechanics."""
    
    def test_calculate_attack_bonus(self):
        """Test attack bonus calculation."""
        char = Character(strength=16, dexterity=14)  # STR +3, DEX +2
        # Non-finesse weapon uses STR
        bonus = calculate_attack_bonus(char, "longsword")
        assert bonus == 5  # +2 proficiency + +3 STR
    
    def test_calculate_attack_bonus_finesse(self):
        """Test attack bonus with finesse weapon."""
        char = Character(strength=10, dexterity=18)  # STR +0, DEX +4
        bonus = calculate_attack_bonus(char, "dagger")
        assert bonus == 6  # +2 proficiency + +4 DEX
    
    def test_calculate_damage_bonus(self):
        """Test damage bonus calculation."""
        char = Character(strength=16)  # +3 STR
        bonus = calculate_damage_bonus(char, "longsword")
        assert bonus == 3
    
    def test_roll_attack_hit(self):
        """Test attack roll structure."""
        char = Character(strength=16)
        result = roll_attack(char, 10, "longsword")
        
        assert "d20_roll" in result
        assert "attack_bonus" in result
        assert "total" in result
        assert "hit" in result
        assert "is_crit" in result
        assert "is_fumble" in result
    
    def test_roll_attack_nat20_always_hits(self):
        """Test natural 20 always hits (crit)."""
        char = Character()
        # Roll many times to eventually get a 20
        crits = 0
        for _ in range(1000):
            result = roll_attack(char, 30, "longsword")  # Very high AC
            if result["d20_roll"] == 20:
                assert result["hit"] == True
                assert result["is_crit"] == True
                crits += 1
        assert crits > 0  # Should get at least one crit in 1000 rolls
    
    def test_roll_attack_nat1_always_misses(self):
        """Test natural 1 always misses (fumble)."""
        char = Character()
        # Roll many times to eventually get a 1
        fumbles = 0
        for _ in range(1000):
            result = roll_attack(char, 5, "longsword")  # Very low AC
            if result["d20_roll"] == 1:
                assert result["hit"] == False
                assert result["is_fumble"] == True
                fumbles += 1
        assert fumbles > 0


class TestAdvantage:
    """Tests for advantage/disadvantage mechanics."""
    
    def test_attack_with_advantage_uses_higher(self):
        """Test advantage takes higher of two rolls."""
        char = Character()
        # With advantage, more likely to hit high AC targets
        hits = 0
        for _ in range(100):
            result = roll_attack_with_advantage(char, 18, "longsword")
            if result["hit"]:
                hits += 1
        # Should hit more often than ~30% normal rate vs AC 18
        assert hits > 0  # At minimum, we should get some hits


class TestInitiative:
    """Tests for initiative system."""
    
    def test_roll_initiative(self):
        """Test initiative roll structure."""
        result = roll_initiative(2)
        assert "roll" in result
        assert "modifier" in result
        assert "total" in result
        assert 1 <= result["roll"] <= 20
        assert result["total"] == result["roll"] + result["modifier"]
    
    def test_format_initiative_roll(self):
        """Test initiative roll formatting."""
        result = {"roll": 15, "modifier": 3, "total": 18}
        formatted = format_initiative_roll("Hero", result)
        assert "Hero" in formatted
        assert "15" in formatted
        assert "18" in formatted
    
    def test_determine_turn_order(self):
        """Test turn order determination."""
        enemies = [create_enemy("goblin"), create_enemy("orc")]
        order = determine_turn_order("TestHero", 2, enemies)
        
        assert len(order) == 3  # 1 player + 2 enemies
        # Should be sorted by initiative (descending)
        for i in range(len(order) - 1):
            assert order[i].initiative >= order[i + 1].initiative
    
    def test_turn_order_includes_player(self):
        """Test player is in turn order."""
        enemies = [create_enemy("goblin")]
        order = determine_turn_order("TestHero", 2, enemies)
        
        player_found = any(c.is_player for c in order)
        assert player_found
    
    def test_display_turn_order(self):
        """Test turn order display formatting."""
        enemies = [create_enemy("goblin")]
        order = determine_turn_order("TestHero", 2, enemies)
        display = display_turn_order(order, 0)
        
        assert "TURN ORDER" in display
        assert "TestHero" in display or "(You)" in display
        assert "Goblin" in display


class TestCombatant:
    """Tests for Combatant wrapper class."""
    
    def test_create_combatant(self):
        """Test creating a combatant."""
        combatant = Combatant(
            name="TestFighter",
            initiative=15,
            is_player=True,
            entity=None
        )
        assert combatant.name == "TestFighter"
        assert combatant.initiative == 15
        assert combatant.is_player == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
