"""
Party System Unit Tests
Tests for PartyMember, Party, and recruitment system.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from party import (
    PartyMember, PartyMemberClass, Party,
    SpecialAbility, PARTY_ABILITIES,
    RecruitmentCondition, 
    check_recruitment_condition, can_attempt_recruitment, pay_recruitment_cost,
    create_elira_ranger, create_marcus_mercenary, create_shade_rogue,
    get_recruitable_npc, list_recruitable_npcs, RECRUITABLE_NPCS
)
from character import Character


# =============================================================================
# PARTY MEMBER TESTS
# =============================================================================

class TestPartyMemberCreation:
    """Test PartyMember dataclass creation."""
    
    def test_basic_creation(self):
        """Create a basic party member."""
        member = PartyMember(
            id="test_member",
            name="Test",
            char_class=PartyMemberClass.FIGHTER,
            description="A test party member"
        )
        
        assert member.id == "test_member"
        assert member.name == "Test"
        assert member.char_class == PartyMemberClass.FIGHTER
        assert member.current_hp == member.max_hp
        assert member.recruited == False
        assert member.is_dead == False
    
    def test_custom_stats(self):
        """Create party member with custom stats."""
        member = PartyMember(
            id="custom",
            name="Custom",
            char_class=PartyMemberClass.RANGER,
            description="Custom stats",
            level=3,
            max_hp=25,
            armor_class=15,
            attack_bonus=6,
            damage_dice="1d8+4"
        )
        
        assert member.level == 3
        assert member.max_hp == 25
        assert member.current_hp == 25
        assert member.armor_class == 15
        assert member.attack_bonus == 6
        assert member.damage_dice == "1d8+4"
    
    def test_ability_assignment(self):
        """Each class gets appropriate ability."""
        for cls in PartyMemberClass:
            member = PartyMember(
                id=f"test_{cls.value.lower()}",
                name=f"Test {cls.value}",
                char_class=cls,
                description="Testing"
            )
            
            expected_ability = PARTY_ABILITIES[cls]
            assert member.special_ability.name == expected_ability.name
            assert member.ability_uses_remaining == expected_ability.uses_per_combat


class TestPartyMemberCombat:
    """Test PartyMember combat functionality."""
    
    @pytest.fixture
    def fighter(self):
        return PartyMember(
            id="test_fighter",
            name="Fighter",
            char_class=PartyMemberClass.FIGHTER,
            description="Test fighter",
            max_hp=20
        )
    
    def test_take_damage(self, fighter):
        """Taking damage reduces HP."""
        assert fighter.current_hp == 20
        
        result = fighter.take_damage(5)
        
        assert fighter.current_hp == 15
        assert "takes 5 damage" in result
    
    def test_take_zero_damage(self, fighter):
        """Zero damage doesn't change HP."""
        original_hp = fighter.current_hp
        result = fighter.take_damage(0)
        assert fighter.current_hp == original_hp
    
    def test_take_negative_damage(self, fighter):
        """Negative damage is ignored."""
        original_hp = fighter.current_hp
        result = fighter.take_damage(-10)
        assert fighter.current_hp == original_hp
    
    def test_death_at_zero_hp(self, fighter):
        """Member dies when HP reaches 0."""
        result = fighter.take_damage(20)
        
        assert fighter.current_hp == 0
        assert fighter.is_dead == True
        assert "fallen" in result.lower()
    
    def test_overkill_damage(self, fighter):
        """Massive damage doesn't go below 0."""
        fighter.take_damage(100)
        assert fighter.current_hp == 0
        assert fighter.is_dead == True
    
    def test_heal(self, fighter):
        """Healing restores HP."""
        fighter.take_damage(10)
        assert fighter.current_hp == 10
        
        result = fighter.heal(5)
        
        assert fighter.current_hp == 15
        assert "heals 5 HP" in result
    
    def test_heal_caps_at_max(self, fighter):
        """Can't heal above max HP."""
        fighter.take_damage(5)
        fighter.heal(100)
        assert fighter.current_hp == fighter.max_hp
    
    def test_heal_dead_member(self, fighter):
        """Can't heal dead member."""
        fighter.take_damage(100)
        assert fighter.is_dead == True
        
        result = fighter.heal(10)
        
        assert fighter.current_hp == 0
        assert "unconscious" in result.lower()
    
    def test_rest_full_heal(self, fighter):
        """Rest fully heals and revives."""
        fighter.take_damage(100)
        assert fighter.is_dead == True
        
        fighter.rest()
        
        assert fighter.current_hp == fighter.max_hp
        assert fighter.is_dead == False


class TestPartyMemberAbilities:
    """Test special ability system."""
    
    @pytest.fixture
    def ranger(self):
        return PartyMember(
            id="test_ranger",
            name="Ranger",
            char_class=PartyMemberClass.RANGER,
            description="Test ranger"
        )
    
    def test_can_use_ability_fresh(self, ranger):
        """Fresh member can use ability."""
        assert ranger.can_use_ability() == True
        assert ranger.ability_uses_remaining == 1
    
    def test_use_ability_success(self, ranger):
        """Using ability succeeds and decrements uses."""
        success, msg = ranger.use_ability()
        
        assert success == True
        assert ranger.ability_uses_remaining == 0
        assert "Hunter's Mark" in msg
    
    def test_use_ability_exhausted(self, ranger):
        """Can't use ability twice per combat."""
        ranger.use_ability()
        
        success, msg = ranger.use_ability()
        
        assert success == False
        assert "already used" in msg.lower()
    
    def test_dead_cant_use_ability(self, ranger):
        """Dead members can't use abilities."""
        ranger.take_damage(100)
        
        assert ranger.can_use_ability() == False
        success, msg = ranger.use_ability()
        assert success == False
    
    def test_reset_combat_state(self, ranger):
        """Reset restores ability uses."""
        ranger.use_ability()
        assert ranger.ability_uses_remaining == 0
        
        ranger.reset_combat_state()
        
        assert ranger.ability_uses_remaining == 1


class TestPartyMemberStatus:
    """Test status display."""
    
    @pytest.fixture
    def member(self):
        return PartyMember(
            id="test",
            name="Test",
            char_class=PartyMemberClass.FIGHTER,
            description="Test",
            max_hp=20
        )
    
    def test_status_healthy(self, member):
        """Full HP shows healthy."""
        assert "Healthy" in member.get_status()
    
    def test_status_wounded(self, member):
        """50-75% HP shows wounded."""
        member.take_damage(8)  # 12/20 = 60%
        assert "Wounded" in member.get_status()
    
    def test_status_bloodied(self, member):
        """25-50% HP shows bloodied."""
        member.take_damage(12)  # 8/20 = 40%
        assert "Bloodied" in member.get_status()
    
    def test_status_critical(self, member):
        """<25% HP shows critical."""
        member.take_damage(17)  # 3/20 = 15%
        assert "Critical" in member.get_status()
    
    def test_status_dead(self, member):
        """Dead shows unconscious."""
        member.take_damage(100)
        assert "Unconscious" in member.get_status()


class TestPartyMemberSerialization:
    """Test save/load functionality."""
    
    def test_to_dict(self):
        """Convert to dictionary."""
        member = create_elira_ranger()
        member.take_damage(5)
        member.recruited = True
        member.disposition = 25
        
        data = member.to_dict()
        
        assert data["id"] == "elira_ranger"
        assert data["name"] == "Elira"
        assert data["char_class"] == "Ranger"
        assert data["current_hp"] == member.current_hp
        assert data["recruited"] == True
        assert data["disposition"] == 25
    
    def test_from_dict(self):
        """Create from dictionary."""
        original = create_marcus_mercenary()
        original.take_damage(10)
        original.recruited = True
        
        data = original.to_dict()
        restored = PartyMember.from_dict(data)
        
        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.char_class == original.char_class
        assert restored.current_hp == original.current_hp
        assert restored.recruited == original.recruited
    
    def test_roundtrip(self):
        """Full save/load roundtrip."""
        original = create_shade_rogue()
        original.disposition = -10
        
        data = original.to_dict()
        restored = PartyMember.from_dict(data)
        data2 = restored.to_dict()
        
        assert data == data2


# =============================================================================
# PARTY CLASS TESTS
# =============================================================================

class TestPartyManagement:
    """Test Party class functionality."""
    
    @pytest.fixture
    def party(self):
        return Party()
    
    @pytest.fixture
    def fighter(self):
        return PartyMember(
            id="fighter",
            name="Fighter",
            char_class=PartyMemberClass.FIGHTER,
            description="Test"
        )
    
    @pytest.fixture
    def ranger(self):
        return PartyMember(
            id="ranger",
            name="Ranger",
            char_class=PartyMemberClass.RANGER,
            description="Test"
        )
    
    def test_empty_party(self, party):
        """New party is empty."""
        assert party.size == 0
        assert party.is_full == False
        assert party.get_alive_members() == []
    
    def test_add_member(self, party, fighter):
        """Add a member to party."""
        success, msg = party.add_member(fighter)
        
        assert success == True
        assert party.size == 1
        assert fighter.recruited == True
        assert "joined" in msg.lower()
    
    def test_add_multiple_members(self, party, fighter, ranger):
        """Add multiple members."""
        party.add_member(fighter)
        party.add_member(ranger)
        
        assert party.size == 2
    
    def test_party_max_limit(self, party):
        """Party enforces max limit."""
        for i in range(Party.MAX_COMPANIONS):
            member = PartyMember(
                id=f"member_{i}",
                name=f"Member {i}",
                char_class=PartyMemberClass.FIGHTER,
                description="Test"
            )
            success, _ = party.add_member(member)
            assert success == True
        
        assert party.is_full == True
        
        # Try to add one more
        extra = PartyMember(
            id="extra",
            name="Extra",
            char_class=PartyMemberClass.FIGHTER,
            description="Test"
        )
        success, msg = party.add_member(extra)
        
        assert success == False
        assert "full" in msg.lower()
    
    def test_no_duplicate_members(self, party, fighter):
        """Can't add same member twice."""
        party.add_member(fighter)
        success, msg = party.add_member(fighter)
        
        assert success == False
        assert "already" in msg.lower()
    
    def test_remove_member_by_id(self, party, fighter):
        """Remove member by ID."""
        party.add_member(fighter)
        
        success, msg, removed = party.remove_member("fighter")
        
        assert success == True
        assert party.size == 0
        assert removed.id == "fighter"
        assert removed.recruited == False
    
    def test_remove_member_by_name(self, party, fighter):
        """Remove member by name."""
        party.add_member(fighter)
        
        success, msg, removed = party.remove_member("Fighter")
        
        assert success == True
    
    def test_remove_nonexistent(self, party):
        """Removing nonexistent member fails."""
        success, msg, removed = party.remove_member("nobody")
        
        assert success == False
        assert removed is None
    
    def test_dismiss_affects_disposition(self, party, fighter):
        """Dismissing a member reduces disposition."""
        fighter.disposition = 20
        party.add_member(fighter)
        
        success, msg, removed = party.remove_member("fighter")
        
        assert removed.disposition < 20
    
    def test_get_member(self, party, fighter, ranger):
        """Find member by ID or name."""
        party.add_member(fighter)
        party.add_member(ranger)
        
        found = party.get_member("ranger")
        assert found.name == "Ranger"
        
        found = party.get_member("Fighter")
        assert found.id == "fighter"
    
    def test_get_alive_members(self, party, fighter, ranger):
        """Get only living members."""
        party.add_member(fighter)
        party.add_member(ranger)
        fighter.take_damage(100)
        
        alive = party.get_alive_members()
        
        assert len(alive) == 1
        assert alive[0].name == "Ranger"
    
    def test_rest_all(self, party, fighter, ranger):
        """Rest heals all members."""
        party.add_member(fighter)
        party.add_member(ranger)
        fighter.take_damage(10)
        ranger.take_damage(100)
        
        party.rest_all()
        
        assert fighter.current_hp == fighter.max_hp
        assert ranger.current_hp == ranger.max_hp
        assert ranger.is_dead == False
    
    def test_reset_combat_state_all(self, party, fighter, ranger):
        """Reset combat state for all members."""
        party.add_member(fighter)
        party.add_member(ranger)
        fighter.use_ability()
        ranger.use_ability()
        
        party.reset_combat_state()
        
        assert fighter.ability_uses_remaining == 1
        assert ranger.ability_uses_remaining == 1


class TestPartyDisplay:
    """Test party display formatting."""
    
    def test_empty_roster(self):
        """Empty party shows appropriate message."""
        party = Party()
        display = party.format_roster()
        assert "empty" in display.lower() or "alone" in display.lower()
    
    def test_roster_with_members(self):
        """Roster shows all members."""
        party = Party()
        party.add_member(create_elira_ranger())
        party.add_member(create_marcus_mercenary())
        
        display = party.format_roster()
        
        assert "Elira" in display
        assert "Marcus" in display
        assert "Ranger" in display
        assert "Fighter" in display


class TestPartySerialization:
    """Test party save/load."""
    
    def test_empty_party_to_dict(self):
        """Empty party serializes."""
        party = Party()
        data = party.to_dict()
        assert data["members"] == []
    
    def test_party_to_dict(self):
        """Party with members serializes."""
        party = Party()
        party.add_member(create_elira_ranger())
        
        data = party.to_dict()
        
        assert len(data["members"]) == 1
        assert data["members"][0]["id"] == "elira_ranger"
    
    def test_party_from_dict(self):
        """Restore party from dict."""
        original = Party()
        original.add_member(create_elira_ranger())
        original.add_member(create_marcus_mercenary())
        original.members[0].take_damage(5)
        
        data = original.to_dict()
        restored = Party.from_dict(data)
        
        assert restored.size == 2
        assert restored.members[0].current_hp == original.members[0].current_hp


# =============================================================================
# RECRUITMENT CONDITION TESTS
# =============================================================================

class TestRecruitmentConditionParsing:
    """Test recruitment condition parsing."""
    
    def test_parse_skill_check(self):
        """Parse skill check condition."""
        cond = RecruitmentCondition.parse("skill:charisma:14")
        
        assert cond.condition_type == "skill"
        assert cond.value == "charisma"
        assert cond.dc == 14
    
    def test_parse_gold(self):
        """Parse gold requirement."""
        cond = RecruitmentCondition.parse("gold:50")
        
        assert cond.condition_type == "gold"
        assert cond.value == "50"
    
    def test_parse_item(self):
        """Parse item requirement."""
        cond = RecruitmentCondition.parse("item:eliras_bow")
        
        assert cond.condition_type == "item"
        assert cond.value == "eliras_bow"
    
    def test_parse_objective(self):
        """Parse objective requirement."""
        cond = RecruitmentCondition.parse("objective:cleared_camp")
        
        assert cond.condition_type == "objective"
        assert cond.value == "cleared_camp"
    
    def test_parse_invalid(self):
        """Invalid condition returns None."""
        assert RecruitmentCondition.parse("invalid") is None
        assert RecruitmentCondition.parse("") is None
        assert RecruitmentCondition.parse("skill") is None
    
    def test_to_string_roundtrip(self):
        """Convert to string and back."""
        original = "skill:perception:12"
        cond = RecruitmentCondition.parse(original)
        assert cond.to_string() == original


class TestRecruitmentConditionChecks:
    """Test condition checking."""
    
    @pytest.fixture
    def character(self):
        char = Character("Test", "fighter", "human")
        char.gold = 100
        return char
    
    def test_check_gold_pass(self, character):
        """Gold check passes with enough gold."""
        cond = RecruitmentCondition.parse("gold:50")
        met, msg = check_recruitment_condition(cond, character)
        
        assert met == True
        assert "enough gold" in msg.lower()
    
    def test_check_gold_fail(self, character):
        """Gold check fails without enough gold."""
        character.gold = 10
        cond = RecruitmentCondition.parse("gold:50")
        met, msg = check_recruitment_condition(cond, character)
        
        assert met == False
        assert "need" in msg.lower()
    
    def test_check_item_pass(self, character):
        """Item check passes with item in inventory."""
        from inventory import get_item, add_item_to_inventory
        potion = get_item("healing_potion")
        add_item_to_inventory(character.inventory, potion)
        
        # Search by display name, not item key
        cond = RecruitmentCondition.parse("item:Healing Potion")
        met, msg = check_recruitment_condition(cond, character)
        
        assert met == True
    
    def test_check_item_fail(self, character):
        """Item check fails without item."""
        cond = RecruitmentCondition.parse("item:legendary_sword")
        met, msg = check_recruitment_condition(cond, character)
        
        assert met == False
    
    def test_check_skill_returns_true(self, character):
        """Skill check returns True (actual roll in game loop)."""
        cond = RecruitmentCondition.parse("skill:charisma:14")
        met, msg = check_recruitment_condition(cond, character)
        
        assert met == True  # Skill checks always return "can attempt"
        assert "DC 14" in msg


class TestRecruitmentPayment:
    """Test paying recruitment costs."""
    
    @pytest.fixture
    def character(self):
        char = Character("Test", "fighter", "human")
        char.gold = 100
        return char
    
    def test_pay_gold(self, character):
        """Pay gold cost."""
        cond = RecruitmentCondition.parse("gold:25")
        success, msg = pay_recruitment_cost(cond, character)
        
        assert success == True
        assert character.gold == 75
    
    def test_pay_gold_insufficient(self, character):
        """Can't pay more than you have."""
        character.gold = 10
        cond = RecruitmentCondition.parse("gold:25")
        success, msg = pay_recruitment_cost(cond, character)
        
        assert success == False
        assert character.gold == 10
    
    def test_pay_item(self, character):
        """Pay item cost removes item."""
        from inventory import get_item, add_item_to_inventory, find_item_in_inventory
        potion = get_item("healing_potion")
        add_item_to_inventory(character.inventory, potion)
        
        # Search by display name, not item key  
        cond = RecruitmentCondition.parse("item:Healing Potion")
        success, msg = pay_recruitment_cost(cond, character)
        
        assert success == True
        assert find_item_in_inventory(character.inventory, "Healing Potion") is None
    
    def test_skill_no_cost(self, character):
        """Skill checks have no cost."""
        cond = RecruitmentCondition.parse("skill:charisma:14")
        success, msg = pay_recruitment_cost(cond, character)
        
        assert success == True  # No cost to pay


class TestCanAttemptRecruitment:
    """Test overall recruitment check."""
    
    def test_no_conditions(self):
        """No conditions = always recruitable."""
        member = PartyMember(
            id="test",
            name="Test",
            char_class=PartyMemberClass.FIGHTER,
            description="Test",
            recruitment_conditions=[]
        )
        char = Character("Player", "fighter", "human")
        
        possible, results = can_attempt_recruitment(member, char)
        
        assert possible == True
    
    def test_or_logic_one_met(self):
        """OR logic - one condition met allows recruitment."""
        member = create_marcus_mercenary()  # gold:25 OR skill:charisma:15
        char = Character("Player", "fighter", "human")
        char.gold = 100  # Has enough gold
        
        possible, results = can_attempt_recruitment(member, char)
        
        assert possible == True


# =============================================================================
# PREDEFINED NPC TESTS
# =============================================================================

class TestPredefinedNPCs:
    """Test predefined recruitable NPCs."""
    
    def test_elira_creation(self):
        """Elira the Ranger is correctly configured."""
        elira = create_elira_ranger()
        
        assert elira.id == "elira_ranger"
        assert elira.name == "Elira"
        assert elira.char_class == PartyMemberClass.RANGER
        assert elira.recruitment_location == "forest_clearing"
        assert "skill:charisma:12" in elira.recruitment_conditions
        assert elira.special_ability.name == "Hunter's Mark"
    
    def test_marcus_creation(self):
        """Marcus the Mercenary is correctly configured."""
        marcus = create_marcus_mercenary()
        
        assert marcus.id == "marcus_mercenary"
        assert marcus.name == "Marcus"
        assert marcus.char_class == PartyMemberClass.FIGHTER
        assert "gold:25" in marcus.recruitment_conditions
        assert marcus.special_ability.name == "Shield Wall"
    
    def test_shade_creation(self):
        """Shade the Rogue is correctly configured."""
        shade = create_shade_rogue()
        
        assert shade.id == "shade_rogue"
        assert shade.name == "Shade"
        assert shade.char_class == PartyMemberClass.ROGUE
        assert shade.special_ability.name == "Sneak Attack"
    
    def test_get_recruitable_npc(self):
        """Get NPC by ID."""
        elira = get_recruitable_npc("elira_ranger")
        assert elira is not None
        assert elira.name == "Elira"
        
        unknown = get_recruitable_npc("unknown_npc")
        assert unknown is None
    
    def test_list_recruitable_npcs(self):
        """List all recruitable NPCs."""
        npcs = list_recruitable_npcs()
        
        assert "elira_ranger" in npcs
        assert "marcus_mercenary" in npcs
        assert "shade_rogue" in npcs
    
    def test_all_have_dialogue(self):
        """All NPCs have recruitment dialogue."""
        for npc_id in list_recruitable_npcs():
            npc = get_recruitable_npc(npc_id)
            assert "greeting" in npc.recruitment_dialogue
            assert "recruit_success" in npc.recruitment_dialogue
            assert "recruit_fail" in npc.recruitment_dialogue


# =============================================================================
# SPECIAL ABILITY TESTS
# =============================================================================

class TestSpecialAbilities:
    """Test special ability definitions."""
    
    def test_all_classes_have_abilities(self):
        """Every class has an ability defined."""
        for cls in PartyMemberClass:
            assert cls in PARTY_ABILITIES
            ability = PARTY_ABILITIES[cls]
            assert ability.name
            assert ability.description
            assert ability.effect_value
    
    def test_fighter_shield_wall(self):
        """Fighter has Shield Wall."""
        ability = PARTY_ABILITIES[PartyMemberClass.FIGHTER]
        assert ability.name == "Shield Wall"
        assert ability.ability_type == "buff"
        assert ability.target == "party"
    
    def test_ranger_hunters_mark(self):
        """Ranger has Hunter's Mark."""
        ability = PARTY_ABILITIES[PartyMemberClass.RANGER]
        assert ability.name == "Hunter's Mark"
        assert ability.ability_type == "damage"
        assert ability.effect_value == "1d4"
    
    def test_rogue_sneak_attack(self):
        """Rogue has Sneak Attack."""
        ability = PARTY_ABILITIES[PartyMemberClass.ROGUE]
        assert ability.name == "Sneak Attack"
        assert ability.effect_value == "2d6"
    
    def test_cleric_healing_word(self):
        """Cleric has Healing Word."""
        ability = PARTY_ABILITIES[PartyMemberClass.CLERIC]
        assert ability.name == "Healing Word"
        assert ability.ability_type == "heal"
    
    def test_wizard_magic_missile(self):
        """Wizard has Magic Missile."""
        ability = PARTY_ABILITIES[PartyMemberClass.WIZARD]
        assert ability.name == "Magic Missile"
        assert ability.ability_type == "damage"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
