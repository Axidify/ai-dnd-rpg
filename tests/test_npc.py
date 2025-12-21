"""
Tests for NPC System (Phase 3.3, Step 3.3.1)
Tests NPC dataclass, NPCRole enum, NPCManager, and serialization.
"""

import pytest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from npc import NPC, NPCRole, NPCManager, format_npc_for_display
from scenario import create_goblin_cave_npcs


# =============================================================================
# NPC DATACLASS TESTS
# =============================================================================

class TestNPCDataclass:
    """Tests for the NPC dataclass."""
    
    def test_create_minimal_npc(self):
        """Test creating NPC with only required fields."""
        npc = NPC(id="test_npc", name="Test NPC")
        
        assert npc.id == "test_npc"
        assert npc.name == "Test NPC"
        assert npc.role == NPCRole.NEUTRAL
        assert npc.disposition == 0
        assert npc.dialogue == {}
        assert npc.quests == []
        assert npc.is_recruitable == False
    
    def test_create_full_npc(self):
        """Test creating NPC with all fields."""
        npc = NPC(
            id="quest_giver_bob",
            name="Bob the Quest Giver",
            description="A jolly quest giver",
            role=NPCRole.QUEST_GIVER,
            location_id="village_square",
            dialogue={"greeting": "Welcome!"},
            disposition=50,
            quests=["fetch_quest"],
            is_recruitable=True,
            recruitment_condition="gold:50"
        )
        
        assert npc.id == "quest_giver_bob"
        assert npc.name == "Bob the Quest Giver"
        assert npc.role == NPCRole.QUEST_GIVER
        assert npc.disposition == 50
        assert npc.dialogue["greeting"] == "Welcome!"
        assert npc.is_recruitable == True
    
    def test_npc_requires_id(self):
        """Test that NPC requires an id."""
        with pytest.raises(ValueError, match="NPC must have an id"):
            NPC(id="", name="Test")
    
    def test_npc_requires_name(self):
        """Test that NPC requires a name."""
        with pytest.raises(ValueError, match="NPC must have a name"):
            NPC(id="test", name="")


# =============================================================================
# DISPOSITION TESTS
# =============================================================================

class TestNPCDisposition:
    """Tests for NPC disposition system."""
    
    def test_disposition_levels(self):
        """Test disposition level descriptions."""
        npc = NPC(id="test", name="Test")
        
        npc.disposition = -75
        assert npc.get_disposition_level() == "hostile"
        
        npc.disposition = -35
        assert npc.get_disposition_level() == "unfriendly"
        
        npc.disposition = 0
        assert npc.get_disposition_level() == "neutral"
        
        npc.disposition = 35
        assert npc.get_disposition_level() == "friendly"
        
        npc.disposition = 75
        assert npc.get_disposition_level() == "trusted"
    
    def test_modify_disposition(self):
        """Test modifying disposition."""
        npc = NPC(id="test", name="Test", disposition=0)
        
        result = npc.modify_disposition(25)
        assert result == 25
        assert npc.disposition == 25
        
        result = npc.modify_disposition(-50)
        assert result == -25
        assert npc.disposition == -25
    
    def test_disposition_clamping_high(self):
        """Test disposition is clamped at 100."""
        npc = NPC(id="test", name="Test", disposition=90)
        
        result = npc.modify_disposition(50)
        assert result == 100
        assert npc.disposition == 100
    
    def test_disposition_clamping_low(self):
        """Test disposition is clamped at -100."""
        npc = NPC(id="test", name="Test", disposition=-90)
        
        result = npc.modify_disposition(-50)
        assert result == -100
        assert npc.disposition == -100


# =============================================================================
# DIALOGUE TESTS
# =============================================================================

class TestNPCDialogue:
    """Tests for NPC dialogue system."""
    
    def test_get_dialogue(self):
        """Test getting dialogue by key."""
        npc = NPC(
            id="test", 
            name="Test",
            dialogue={"greeting": "Hello!", "farewell": "Goodbye!"}
        )
        
        assert npc.get_dialogue("greeting") == "Hello!"
        assert npc.get_dialogue("farewell") == "Goodbye!"
        assert npc.get_dialogue("nonexistent") is None
    
    def test_dialogue_case_insensitive(self):
        """Test dialogue keys are case-insensitive."""
        npc = NPC(
            id="test",
            name="Test",
            dialogue={"greeting": "Hello!"}
        )
        
        assert npc.get_dialogue("GREETING") == "Hello!"
        assert npc.get_dialogue("Greeting") == "Hello!"
    
    def test_has_dialogue(self):
        """Test checking if NPC has dialogue."""
        npc = NPC(
            id="test",
            name="Test",
            dialogue={"greeting": "Hello!"}
        )
        
        assert npc.has_dialogue("greeting") == True
        assert npc.has_dialogue("GREETING") == True
        assert npc.has_dialogue("quest") == False
    
    def test_add_dialogue(self):
        """Test adding dialogue to NPC."""
        npc = NPC(id="test", name="Test")
        
        npc.add_dialogue("greeting", "Hello!")
        assert npc.get_dialogue("greeting") == "Hello!"
        
        # Test update
        npc.add_dialogue("greeting", "Hey there!")
        assert npc.get_dialogue("greeting") == "Hey there!"


# =============================================================================
# DM CONTEXT TESTS
# =============================================================================

class TestNPCContext:
    """Tests for NPC DM context generation."""
    
    def test_basic_context(self):
        """Test basic context generation."""
        npc = NPC(id="test", name="Test NPC", role=NPCRole.INFO)
        
        context = npc.get_context_for_dm()
        
        assert "NPC: Test NPC" in context
        assert "Role: INFO" in context
        assert "Disposition: neutral (0)" in context
    
    def test_quest_giver_context(self):
        """Test quest giver context includes quests."""
        npc = NPC(
            id="quest_giver",
            name="Quest Giver",
            role=NPCRole.QUEST_GIVER,
            quests=["save_princess", "kill_dragon"]
        )
        
        context = npc.get_context_for_dm()
        
        assert "Offers quests: save_princess, kill_dragon" in context
    
    def test_recruitable_context(self):
        """Test recruitable context includes condition."""
        npc = NPC(
            id="recruit",
            name="Recruit",
            is_recruitable=True,
            recruitment_condition="skill:charisma:14"
        )
        
        context = npc.get_context_for_dm()
        
        assert "Recruitable (condition: skill:charisma:14)" in context


# =============================================================================
# SERIALIZATION TESTS
# =============================================================================

class TestNPCSerialization:
    """Tests for NPC serialization."""
    
    def test_to_dict(self):
        """Test converting NPC to dictionary."""
        npc = NPC(
            id="test",
            name="Test NPC",
            description="A test NPC",
            role=NPCRole.QUEST_GIVER,
            location_id="tavern",
            dialogue={"greeting": "Hello!"},
            disposition=25,
            quests=["quest1"],
            is_recruitable=True,
            recruitment_condition="gold:50",
            recruited=True
        )
        
        data = npc.to_dict()
        
        assert data["id"] == "test"
        assert data["name"] == "Test NPC"
        assert data["role"] == "QUEST_GIVER"
        assert data["disposition"] == 25
        assert data["dialogue"]["greeting"] == "Hello!"
        assert data["recruited"] == True
    
    def test_from_dict(self):
        """Test creating NPC from dictionary."""
        data = {
            "id": "test",
            "name": "Test NPC",
            "description": "A test NPC",
            "role": "QUEST_GIVER",
            "location_id": "village",
            "dialogue": {"quest": "Kill goblins!"},
            "disposition": -20,
            "quests": ["kill_goblins"],
            "is_recruitable": False,
            "recruitment_condition": "",
            "recruited": False
        }
        
        npc = NPC.from_dict(data)
        
        assert npc.id == "test"
        assert npc.name == "Test NPC"
        assert npc.role == NPCRole.QUEST_GIVER
        assert npc.disposition == -20
        assert npc.get_dialogue("quest") == "Kill goblins!"
    
    def test_round_trip_serialization(self):
        """Test that to_dict -> from_dict preserves data."""
        original = NPC(
            id="roundtrip",
            name="Round Trip NPC",
            role=NPCRole.RECRUITABLE,
            disposition=42,
            is_recruitable=True,
            recruited=True
        )
        
        data = original.to_dict()
        restored = NPC.from_dict(data)
        
        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.role == original.role
        assert restored.disposition == original.disposition
        assert restored.is_recruitable == original.is_recruitable
        assert restored.recruited == original.recruited


# =============================================================================
# NPC ROLE TESTS
# =============================================================================

class TestNPCRole:
    """Tests for NPCRole enum."""
    
    def test_all_roles_exist(self):
        """Test that all expected roles exist."""
        roles = [r.name for r in NPCRole]
        
        assert "QUEST_GIVER" in roles
        assert "INFO" in roles
        assert "HOSTILE" in roles
        assert "RECRUITABLE" in roles
        assert "NEUTRAL" in roles
    
    def test_role_from_string(self):
        """Test creating role from string."""
        assert NPCRole["QUEST_GIVER"] == NPCRole.QUEST_GIVER
        assert NPCRole["INFO"] == NPCRole.INFO


# =============================================================================
# NPC MANAGER TESTS
# =============================================================================

class TestNPCManager:
    """Tests for NPCManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = NPCManager()
        
        self.npc1 = NPC(id="npc1", name="NPC One", location_id="loc_a", role=NPCRole.QUEST_GIVER)
        self.npc2 = NPC(id="npc2", name="NPC Two", location_id="loc_a", role=NPCRole.INFO)
        self.npc3 = NPC(id="npc3", name="NPC Three", location_id="loc_b", role=NPCRole.QUEST_GIVER)
        
        self.manager.add_npc(self.npc1)
        self.manager.add_npc(self.npc2)
        self.manager.add_npc(self.npc3)
    
    def test_add_and_get_npc(self):
        """Test adding and getting NPCs."""
        npc = self.manager.get_npc("npc1")
        assert npc is not None
        assert npc.name == "NPC One"
    
    def test_get_nonexistent_npc(self):
        """Test getting nonexistent NPC returns None."""
        npc = self.manager.get_npc("nonexistent")
        assert npc is None
    
    def test_get_npc_by_name(self):
        """Test getting NPC by name."""
        npc = self.manager.get_npc_by_name("NPC Two")
        assert npc is not None
        assert npc.id == "npc2"
    
    def test_get_npc_by_name_case_insensitive(self):
        """Test getting NPC by name is case-insensitive."""
        npc = self.manager.get_npc_by_name("npc one")
        assert npc is not None
        assert npc.id == "npc1"
    
    def test_get_npcs_at_location(self):
        """Test getting NPCs at a location."""
        npcs = self.manager.get_npcs_at_location("loc_a")
        
        assert len(npcs) == 2
        ids = [n.id for n in npcs]
        assert "npc1" in ids
        assert "npc2" in ids
    
    def test_get_npcs_by_role(self):
        """Test getting NPCs by role."""
        quest_givers = self.manager.get_npcs_by_role(NPCRole.QUEST_GIVER)
        
        assert len(quest_givers) == 2
        ids = [n.id for n in quest_givers]
        assert "npc1" in ids
        assert "npc3" in ids
    
    def test_get_quest_givers(self):
        """Test getting quest givers shortcut."""
        quest_givers = self.manager.get_quest_givers()
        assert len(quest_givers) == 2
    
    def test_get_all_npcs(self):
        """Test getting all NPCs."""
        npcs = self.manager.get_all_npcs()
        assert len(npcs) == 3
    
    def test_remove_npc(self):
        """Test removing an NPC."""
        result = self.manager.remove_npc("npc1")
        
        assert result == True
        assert self.manager.get_npc("npc1") is None
        assert len(self.manager.get_all_npcs()) == 2
    
    def test_remove_nonexistent_npc(self):
        """Test removing nonexistent NPC returns False."""
        result = self.manager.remove_npc("nonexistent")
        assert result == False
    
    def test_move_npc(self):
        """Test moving NPC to new location."""
        result = self.manager.move_npc("npc1", "loc_c")
        
        assert result == True
        npc = self.manager.get_npc("npc1")
        assert npc.location_id == "loc_c"
    
    def test_get_recruitable_excludes_recruited(self):
        """Test that get_recruitable excludes recruited NPCs."""
        recruit = NPC(
            id="recruit1",
            name="Recruit",
            is_recruitable=True,
            recruited=False
        )
        self.manager.add_npc(recruit)
        
        recruitables = self.manager.get_recruitable()
        assert len(recruitables) == 1
        
        recruit.recruited = True
        recruitables = self.manager.get_recruitable()
        assert len(recruitables) == 0
    
    def test_get_npcs_at_location_excludes_recruited(self):
        """Test that recruited NPCs don't appear at locations."""
        recruit = NPC(
            id="recruit1",
            name="Recruit",
            location_id="loc_a",
            is_recruitable=True,
            recruited=False
        )
        self.manager.add_npc(recruit)
        
        # Before recruiting
        npcs = self.manager.get_npcs_at_location("loc_a")
        assert len(npcs) == 3
        
        # After recruiting
        recruit.recruited = True
        npcs = self.manager.get_npcs_at_location("loc_a")
        assert len(npcs) == 2


# =============================================================================
# NPC MANAGER SERIALIZATION TESTS
# =============================================================================

class TestNPCManagerSerialization:
    """Tests for NPCManager serialization."""
    
    def test_manager_to_dict(self):
        """Test converting manager to dictionary."""
        manager = NPCManager()
        manager.add_npc(NPC(id="npc1", name="NPC One"))
        manager.add_npc(NPC(id="npc2", name="NPC Two"))
        
        data = manager.to_dict()
        
        assert "npcs" in data
        assert "npc1" in data["npcs"]
        assert "npc2" in data["npcs"]
        assert data["npcs"]["npc1"]["name"] == "NPC One"
    
    def test_manager_from_dict(self):
        """Test restoring manager from dictionary."""
        data = {
            "npcs": {
                "npc1": {"id": "npc1", "name": "NPC One", "role": "INFO"},
                "npc2": {"id": "npc2", "name": "NPC Two", "role": "QUEST_GIVER"}
            }
        }
        
        manager = NPCManager()
        manager.from_dict(data)
        
        npcs = manager.get_all_npcs()
        assert len(npcs) == 2
        assert manager.get_npc("npc1").name == "NPC One"
    
    def test_update_npc_states(self):
        """Test updating NPC states from saved data."""
        manager = NPCManager()
        manager.add_npc(NPC(id="npc1", name="NPC One", disposition=0))
        manager.add_npc(NPC(id="npc2", name="NPC Two", disposition=0, is_recruitable=True))
        
        saved_states = {
            "npc1": {"disposition": 50},
            "npc2": {"disposition": 25, "recruited": True, "location_id": "new_loc"}
        }
        
        manager.update_npc_states(saved_states)
        
        assert manager.get_npc("npc1").disposition == 50
        assert manager.get_npc("npc2").disposition == 25
        assert manager.get_npc("npc2").recruited == True
        assert manager.get_npc("npc2").location_id == "new_loc"


# =============================================================================
# GOBLIN CAVE NPCS TESTS
# =============================================================================

class TestGoblinCaveNPCs:
    """Tests for Goblin Cave scenario NPCs."""
    
    def setup_method(self):
        """Create the goblin cave NPC manager."""
        self.manager = create_goblin_cave_npcs()
    
    def test_bram_exists(self):
        """Test that Bram the farmer exists."""
        bram = self.manager.get_npc("bram")
        
        assert bram is not None
        assert bram.name == "Bram"
        assert bram.role == NPCRole.QUEST_GIVER
        assert bram.location_id == "tavern_main"
        assert "rescue_lily" in bram.quests
    
    def test_barkeep_exists(self):
        """Test that the barkeep exists."""
        barkeep = self.manager.get_npc("barkeep")
        
        assert barkeep is not None
        assert barkeep.name == "Greth the Barkeep"
        assert barkeep.role == NPCRole.INFO
        assert barkeep.location_id == "tavern_bar"
    
    def test_elira_exists(self):
        """Test that Elira the ranger exists."""
        elira = self.manager.get_npc("elira")
        
        assert elira is not None
        assert elira.name == "Elira"
        assert elira.role == NPCRole.RECRUITABLE
        assert elira.is_recruitable == True
        assert elira.location_id == "forest_clearing"
    
    def test_lily_exists(self):
        """Test that Lily the captive exists."""
        lily = self.manager.get_npc("lily")
        
        assert lily is not None
        assert lily.name == "Lily"
        assert lily.location_id == "goblin_camp_main"
    
    def test_tavern_has_npcs(self):
        """Test that tavern has correct NPCs."""
        tavern_npcs = self.manager.get_npcs_at_location("tavern_main")
        
        assert len(tavern_npcs) == 2  # Bram, Marcus (barkeep is at tavern_bar)
        names = [n.name for n in tavern_npcs]
        assert "Bram" in names
        assert "Marcus" in names  # Recruitable mercenary
    
    def test_tavern_bar_has_barkeep(self):
        """Test that tavern bar has barkeep."""
        bar_npcs = self.manager.get_npcs_at_location("tavern_bar")
        
        assert len(bar_npcs) == 1  # Just the barkeep
        assert bar_npcs[0].name == "Greth the Barkeep"
    
    def test_bram_dialogue(self):
        """Test Bram has essential dialogue."""
        bram = self.manager.get_npc("bram")
        
        assert bram.has_dialogue("greeting")
        assert bram.has_dialogue("quest")
        assert bram.has_dialogue("about_lily")
        assert bram.has_dialogue("about_cave")
    
    def test_barkeep_dialogue(self):
        """Test barkeep has essential dialogue."""
        barkeep = self.manager.get_npc("barkeep")
        
        assert barkeep.has_dialogue("greeting")
        assert barkeep.has_dialogue("about_goblins")
        assert barkeep.has_dialogue("about_village")


# =============================================================================
# PERSONALITY SYSTEM TESTS (Phase 3.4)
# =============================================================================

class TestPersonalitySystem:
    """Tests for NPC Personality dataclass and integration."""
    
    def test_create_personality(self):
        """Test creating a Personality with all fields."""
        from npc import Personality
        
        personality = Personality(
            traits=["gruff", "honest", "protective"],
            speech_style="blunt and direct",
            voice_notes="deep rumbling voice",
            motivations=["protect village", "quality work"],
            fears=["goblin attacks"],
            quirks=["hammers while talking"],
            secrets=["lost his son to bandits"]
        )
        
        assert personality.traits == ["gruff", "honest", "protective"]
        assert personality.speech_style == "blunt and direct"
        assert personality.voice_notes == "deep rumbling voice"
        assert len(personality.motivations) == 2
        assert len(personality.fears) == 1
        assert len(personality.quirks) == 1
        assert len(personality.secrets) == 1
    
    def test_personality_defaults(self):
        """Test Personality with default empty fields."""
        from npc import Personality
        
        personality = Personality()
        
        assert personality.traits == []
        assert personality.speech_style == ""
        assert personality.voice_notes == ""
        assert personality.motivations == []
        assert personality.fears == []
        assert personality.quirks == []
        assert personality.secrets == []
    
    def test_personality_to_dict(self):
        """Test Personality serialization."""
        from npc import Personality
        
        personality = Personality(
            traits=["brave", "reckless"],
            speech_style="rapid fire",
            quirks=["taps foot"]
        )
        
        data = personality.to_dict()
        
        assert data["traits"] == ["brave", "reckless"]
        assert data["speech_style"] == "rapid fire"
        assert data["quirks"] == ["taps foot"]
        assert data["secrets"] == []  # Empty list serialized
    
    def test_personality_from_dict(self):
        """Test Personality deserialization."""
        from npc import Personality
        
        data = {
            "traits": ["calm", "wise"],
            "speech_style": "measured",
            "voice_notes": "soft spoken",
            "motivations": ["seek knowledge"],
            "fears": [],
            "quirks": [],
            "secrets": ["is actually a dragon"]
        }
        
        personality = Personality.from_dict(data)
        
        assert personality.traits == ["calm", "wise"]
        assert personality.speech_style == "measured"
        assert personality.secrets == ["is actually a dragon"]
    
    def test_personality_dm_summary(self):
        """Test get_dm_summary output."""
        from npc import Personality
        
        personality = Personality(
            traits=["gruff", "honest"],
            speech_style="blunt",
            motivations=["protect family"],
            secrets=["has a hidden cellar"]
        )
        
        summary = personality.get_dm_summary()
        
        assert "Personality: gruff, honest" in summary
        assert "Speech: blunt" in summary
        assert "Motivated by: protect family" in summary
        assert "[SECRET]: has a hidden cellar" in summary
    
    def test_personality_dm_summary_no_secrets(self):
        """Test get_dm_summary can exclude secrets."""
        from npc import Personality
        
        personality = Personality(
            traits=["cheerful"],
            secrets=["is a spy"]
        )
        
        summary = personality.get_dm_summary(include_secrets=False)
        
        assert "cheerful" in summary
        assert "spy" not in summary
    
    def test_npc_with_personality(self):
        """Test NPC can have a Personality attached."""
        from npc import Personality
        
        personality = Personality(
            traits=["nervous", "helpful"],
            speech_style="stammers when stressed"
        )
        
        npc = NPC(
            id="villager",
            name="Timid Tim",
            personality=personality
        )
        
        assert npc.personality is not None
        assert npc.personality.traits == ["nervous", "helpful"]
    
    def test_npc_personality_in_context(self):
        """Test personality appears in get_context_for_dm."""
        from npc import Personality
        
        personality = Personality(
            traits=["wise", "patient"],
            secrets=["knows the secret passage"]
        )
        
        npc = NPC(
            id="sage",
            name="Elder Sage",
            personality=personality
        )
        
        context = npc.get_context_for_dm()
        
        assert "PERSONALITY" in context
        assert "wise, patient" in context
        assert "[SECRET]: knows the secret passage" in context
    
    def test_npc_without_personality_context(self):
        """Test NPC without personality doesn't crash get_context_for_dm."""
        npc = NPC(id="basic", name="Basic NPC")
        
        context = npc.get_context_for_dm()
        
        assert "Basic NPC" in context
        assert "PERSONALITY" not in context  # No personality section
    
    def test_npc_personality_serialization(self):
        """Test NPC with personality serializes and deserializes correctly."""
        from npc import Personality
        
        personality = Personality(
            traits=["grumpy"],
            speech_style="curt",
            secrets=["hides gold under floorboards"]
        )
        
        npc = NPC(
            id="miser",
            name="Old Miser",
            personality=personality
        )
        
        # Serialize
        data = npc.to_dict()
        assert data["personality"] is not None
        assert data["personality"]["traits"] == ["grumpy"]
        
        # Deserialize
        restored_npc = NPC.from_dict(data)
        assert restored_npc.personality is not None
        assert restored_npc.personality.traits == ["grumpy"]
        assert restored_npc.personality.secrets == ["hides gold under floorboards"]
    
    def test_goblin_cave_npcs_have_personalities(self):
        """Test that key NPCs in Goblin Cave scenario have personalities."""
        npc_manager = create_goblin_cave_npcs()
        
        bram = npc_manager.get_npc("bram")
        assert bram is not None
        assert bram.personality is not None
        assert "desperate" in bram.personality.traits or "unreliable witness" in bram.personality.traits
        
        barkeep = npc_manager.get_npc("barkeep")
        assert barkeep is not None
        assert barkeep.personality is not None
        
        marcus = npc_manager.get_npc("marcus")
        assert marcus is not None
        assert marcus.personality is not None


# =============================================================================
# UTILITY FUNCTION TESTS
# =============================================================================

class TestUtilityFunctions:
    """Tests for utility functions."""
    
    def test_format_npc_for_display(self):
        """Test NPC display formatting."""
        info_npc = NPC(id="i", name="Info NPC", role=NPCRole.INFO, disposition=35)
        quest_giver = NPC(id="q", name="Quest Giver", role=NPCRole.QUEST_GIVER)
        
        info_display = format_npc_for_display(info_npc)
        assert "💬" in info_display
        assert "Info NPC" in info_display
        assert "friendly" in info_display
        
        quest_display = format_npc_for_display(quest_giver)
        assert "❗" in quest_display
        assert "Quest Giver" in quest_display


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
