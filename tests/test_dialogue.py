"""
Tests for NPC Dialogue System (Phase 3.3, Priority 2)
Tests talk command, dialogue retrieval, and AI dialogue integration.
"""

import pytest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from npc import NPC, NPCRole, NPCManager
from scenario import create_goblin_cave_npcs


# =============================================================================
# DIALOGUE CONTEXT TESTS
# =============================================================================

class TestDialogueRetrieval:
    """Tests for NPC dialogue retrieval."""
    
    def setup_method(self):
        """Set up test NPC."""
        self.npc = NPC(
            id="test_npc",
            name="Test NPC",
            role=NPCRole.INFO,
            dialogue={
                "greeting": "Hello, traveler!",
                "farewell": "Safe travels!",
                "about_weather": "The weather has been quite pleasant lately.",
                "about_goblins": "Those wretched creatures have been causing trouble.",
                "quest": "I need someone to help me find my lost cat."
            },
            disposition=25  # Friendly
        )
    
    def test_get_greeting(self):
        """Test getting greeting dialogue."""
        assert self.npc.get_dialogue("greeting") == "Hello, traveler!"
    
    def test_get_about_topic(self):
        """Test getting 'about' topic dialogue."""
        assert self.npc.get_dialogue("about_goblins") is not None
        assert "creatures" in self.npc.get_dialogue("about_goblins").lower()
    
    def test_case_insensitive_topics(self):
        """Test that dialogue keys are case-insensitive."""
        assert self.npc.get_dialogue("ABOUT_WEATHER") == "The weather has been quite pleasant lately."
        assert self.npc.get_dialogue("About_Goblins") is not None
    
    def test_missing_topic(self):
        """Test that missing topics return None."""
        assert self.npc.get_dialogue("about_dragons") is None
        assert self.npc.get_dialogue("nonexistent") is None
    
    def test_has_dialogue(self):
        """Test checking if NPC has specific dialogue."""
        assert self.npc.has_dialogue("greeting") == True
        assert self.npc.has_dialogue("about_weather") == True
        assert self.npc.has_dialogue("about_dragons") == False


class TestNPCContext:
    """Tests for NPC context generation for AI."""
    
    def test_basic_context(self):
        """Test basic context includes essential info."""
        npc = NPC(
            id="test",
            name="Test",
            role=NPCRole.INFO,
            description="A helpful NPC",
            disposition=0
        )
        
        context = npc.get_context_for_dm()
        
        assert "Test" in context
        assert "INFO" in context
        assert "neutral" in context
    
    def test_quest_giver_context_includes_quests(self):
        """Test that quest giver context includes quest info."""
        npc = NPC(
            id="quest_giver",
            name="Quest Giver",
            role=NPCRole.QUEST_GIVER,
            quests=["rescue_princess", "slay_dragon"]
        )
        
        context = npc.get_context_for_dm()
        
        assert "rescue_princess" in context or "quests" in context.lower()
    
    def test_disposition_affects_context(self):
        """Test that disposition level is included in context."""
        hostile_npc = NPC(id="hostile", name="Hostile", disposition=-75)
        trusted_npc = NPC(id="trusted", name="Trusted", disposition=75)
        
        hostile_context = hostile_npc.get_context_for_dm()
        trusted_context = trusted_npc.get_context_for_dm()
        
        assert "hostile" in hostile_context
        assert "trusted" in trusted_context


# =============================================================================
# GOBLIN CAVE NPC DIALOGUE TESTS
# =============================================================================

class TestGoblinCaveDialogue:
    """Tests for Goblin Cave scenario NPC dialogue."""
    
    def setup_method(self):
        """Create NPCManager with Goblin Cave NPCs."""
        self.manager = create_goblin_cave_npcs()
    
    def test_bram_has_essential_dialogue(self):
        """Test that Bram has all essential dialogue keys."""
        bram = self.manager.get_npc("bram")
        
        assert bram.has_dialogue("greeting")
        assert bram.has_dialogue("quest")
        assert bram.has_dialogue("about_lily")
        assert bram.has_dialogue("about_goblins")
        assert bram.has_dialogue("about_cave")
        assert bram.has_dialogue("farewell")
    
    def test_barkeep_has_gossip_dialogue(self):
        """Test that barkeep has information dialogue."""
        barkeep = self.manager.get_npc("barkeep")
        
        assert barkeep.has_dialogue("greeting")
        assert barkeep.has_dialogue("about_goblins")
        assert barkeep.has_dialogue("about_village")
        assert barkeep.has_dialogue("about_rumors")
    
    def test_elira_has_recruitment_dialogue(self):
        """Test that Elira has dialogue for recruitment."""
        elira = self.manager.get_npc("elira")
        
        assert elira.has_dialogue("greeting")
        assert elira.has_dialogue("about_self")
        assert elira.has_dialogue("about_goblins")
        assert elira.has_dialogue("recruit_accept")
    
    def test_lily_has_rescue_dialogue(self):
        """Test that Lily has dialogue for rescue scene."""
        lily = self.manager.get_npc("lily")
        
        assert lily.has_dialogue("greeting")
        assert lily.has_dialogue("about_escape")
        assert lily.has_dialogue("about_chief")


# =============================================================================
# NPC LOOKUP BY NAME TESTS
# =============================================================================

class TestNPCLookup:
    """Tests for finding NPCs by name in various formats."""
    
    def setup_method(self):
        """Create NPCManager with test NPCs."""
        self.manager = create_goblin_cave_npcs()
    
    def test_find_by_id(self):
        """Test finding NPC by ID."""
        npc = self.manager.get_npc("bram")
        assert npc is not None
        assert npc.name == "Bram"
    
    def test_find_by_name(self):
        """Test finding NPC by name."""
        npc = self.manager.get_npc_by_name("Bram")
        assert npc is not None
        assert npc.id == "bram"
    
    def test_find_by_name_case_insensitive(self):
        """Test that name lookup is case-insensitive."""
        npc1 = self.manager.get_npc_by_name("BRAM")
        npc2 = self.manager.get_npc_by_name("bram")
        npc3 = self.manager.get_npc_by_name("Bram")
        
        assert npc1 is not None
        assert npc2 is not None
        assert npc3 is not None
        assert npc1.id == npc2.id == npc3.id
    
    def test_find_barkeep(self):
        """Test finding barkeep NPC (now in tavern_bar)."""
        npc = self.manager.get_npc("barkeep")
        assert npc is not None
        assert npc.location_id == "tavern_bar"
        
        # Full name lookup (name is "Greth the Barkeep")
        npc_by_name = self.manager.get_npc_by_name("Greth the Barkeep")
        assert npc_by_name is not None
        assert npc_by_name.id == "barkeep"


# =============================================================================
# DISPOSITION DIALOGUE TONE TESTS
# =============================================================================

class TestDispositionTone:
    """Tests for how disposition affects dialogue tone."""
    
    def test_hostile_disposition_level(self):
        """Test that hostile NPCs report correct disposition level."""
        npc = NPC(id="hostile", name="Hostile", disposition=-60)
        assert npc.get_disposition_level() == "hostile"
    
    def test_unfriendly_disposition_level(self):
        """Test that unfriendly NPCs report correct disposition level."""
        npc = NPC(id="unfriendly", name="Unfriendly", disposition=-30)
        assert npc.get_disposition_level() == "unfriendly"
    
    def test_neutral_disposition_level(self):
        """Test that neutral NPCs report correct disposition level."""
        npc = NPC(id="neutral", name="Neutral", disposition=0)
        assert npc.get_disposition_level() == "neutral"
    
    def test_friendly_disposition_level(self):
        """Test that friendly NPCs report correct disposition level."""
        npc = NPC(id="friendly", name="Friendly", disposition=35)
        assert npc.get_disposition_level() == "friendly"
    
    def test_trusted_disposition_level(self):
        """Test that trusted NPCs report correct disposition level."""
        npc = NPC(id="trusted", name="Trusted", disposition=60)
        assert npc.get_disposition_level() == "trusted"


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestDialogueIntegration:
    """Integration tests for dialogue system with scenarios."""
    
    def test_npcs_at_tavern_location(self):
        """Test that tavern location has expected NPCs."""
        manager = create_goblin_cave_npcs()
        tavern_npcs = manager.get_npcs_at_location("tavern_main")
        
        npc_ids = [npc.id for npc in tavern_npcs]
        assert "bram" in npc_ids
        assert "marcus" in npc_ids  # Marcus is in tavern_main
        
        # Barkeep is in tavern_bar, not tavern_main
        bar_npcs = manager.get_npcs_at_location("tavern_bar")
        bar_npc_ids = [npc.id for npc in bar_npcs]
        assert "barkeep" in bar_npc_ids
    
    def test_npcs_have_matching_location_ids(self):
        """Test that NPCs have correct location_id set."""
        manager = create_goblin_cave_npcs()
        
        bram = manager.get_npc("bram")
        assert bram.location_id == "tavern_main"
        
        elira = manager.get_npc("elira")
        assert elira.location_id == "forest_clearing"
        
        lily = manager.get_npc("lily")
        assert lily.location_id == "goblin_camp_main"
    
    def test_quest_giver_has_quests(self):
        """Test that quest giver NPCs have quests defined."""
        manager = create_goblin_cave_npcs()
        bram = manager.get_npc("bram")
        
        assert bram.role == NPCRole.QUEST_GIVER
        assert len(bram.quests) > 0
        assert "rescue_lily" in bram.quests


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
