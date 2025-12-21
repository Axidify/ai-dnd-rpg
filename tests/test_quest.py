"""
Tests for Quest System (Phase 3.3.4)
Tests quest creation, objectives, status, and QuestManager operations.
"""

import pytest
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from quest import (
    QuestStatus, ObjectiveType, QuestObjective, Quest, QuestManager,
    create_kill_objective, create_find_objective, create_talk_objective,
    create_location_objective, create_collect_objective
)


# =============================================================================
# QUEST OBJECTIVE TESTS
# =============================================================================

class TestQuestObjective:
    """Tests for QuestObjective dataclass."""
    
    def test_create_objective(self):
        """Test creating a basic objective."""
        obj = QuestObjective(
            id="kill_goblins",
            description="Kill 5 goblins",
            objective_type=ObjectiveType.KILL,
            target="goblin",
            required_count=5
        )
        assert obj.id == "kill_goblins"
        assert obj.description == "Kill 5 goblins"
        assert obj.objective_type == ObjectiveType.KILL
        assert obj.target == "goblin"
        assert obj.required_count == 5
        assert obj.current_count == 0
        assert obj.completed == False
    
    def test_objective_validation_no_id(self):
        """Test that objective requires id."""
        with pytest.raises(ValueError, match="must have an id"):
            QuestObjective(
                id="",
                description="Test",
                objective_type=ObjectiveType.KILL,
                target="goblin"
            )
    
    def test_objective_validation_no_description(self):
        """Test that objective requires description."""
        with pytest.raises(ValueError, match="must have a description"):
            QuestObjective(
                id="test",
                description="",
                objective_type=ObjectiveType.KILL,
                target="goblin"
            )
    
    def test_objective_validation_invalid_count(self):
        """Test that required_count must be at least 1."""
        with pytest.raises(ValueError, match="required_count must be at least 1"):
            QuestObjective(
                id="test",
                description="Test",
                objective_type=ObjectiveType.KILL,
                target="goblin",
                required_count=0
            )
    
    def test_update_progress_basic(self):
        """Test basic progress update."""
        obj = QuestObjective(
            id="kill_goblins",
            description="Kill 5 goblins",
            objective_type=ObjectiveType.KILL,
            target="goblin",
            required_count=5
        )
        
        result = obj.update_progress(1)
        assert result == False  # Not complete yet
        assert obj.current_count == 1
        assert obj.completed == False
    
    def test_update_progress_completion(self):
        """Test objective completion."""
        obj = QuestObjective(
            id="kill_goblins",
            description="Kill 5 goblins",
            objective_type=ObjectiveType.KILL,
            target="goblin",
            required_count=5
        )
        
        obj.update_progress(4)
        result = obj.update_progress(1)
        
        assert result == True  # Just completed
        assert obj.current_count == 5
        assert obj.completed == True
    
    def test_update_progress_already_complete(self):
        """Test that updating completed objective returns False."""
        obj = QuestObjective(
            id="find_item",
            description="Find the key",
            objective_type=ObjectiveType.FIND_ITEM,
            target="boss_key",
            required_count=1
        )
        
        obj.update_progress(1)  # Complete it
        result = obj.update_progress(1)  # Try to add more
        
        assert result == False
        assert obj.current_count == 1  # Didn't increase
    
    def test_update_progress_capped(self):
        """Test that progress doesn't exceed required."""
        obj = QuestObjective(
            id="collect_gems",
            description="Collect 3 gems",
            objective_type=ObjectiveType.COLLECT,
            target="gem",
            required_count=3
        )
        
        obj.update_progress(5)  # Add more than needed
        
        assert obj.current_count == 3  # Capped at required
        assert obj.completed == True
    
    def test_get_progress_string(self):
        """Test progress string formatting."""
        obj = QuestObjective(
            id="kill_goblins",
            description="Kill 5 goblins",
            objective_type=ObjectiveType.KILL,
            target="goblin",
            required_count=5
        )
        
        assert obj.get_progress_string() == "0/5"
        
        obj.update_progress(3)
        assert obj.get_progress_string() == "3/5"
        
        obj.update_progress(2)
        assert obj.get_progress_string() == "✓ Complete"
    
    def test_objective_serialization(self):
        """Test objective to_dict/from_dict."""
        obj = QuestObjective(
            id="kill_goblins",
            description="Kill 5 goblins",
            objective_type=ObjectiveType.KILL,
            target="goblin",
            required_count=5,
            optional=True,
            hidden=True
        )
        obj.update_progress(3)
        
        data = obj.to_dict()
        loaded = QuestObjective.from_dict(data)
        
        assert loaded.id == obj.id
        assert loaded.description == obj.description
        assert loaded.objective_type == obj.objective_type
        assert loaded.target == obj.target
        assert loaded.required_count == obj.required_count
        assert loaded.current_count == obj.current_count
        assert loaded.optional == obj.optional
        assert loaded.hidden == obj.hidden


class TestObjectiveHelpers:
    """Tests for objective factory functions."""
    
    def test_create_kill_objective(self):
        """Test kill objective factory."""
        obj = create_kill_objective("kill_5", "Kill 5 goblins", "goblin", 5)
        assert obj.objective_type == ObjectiveType.KILL
        assert obj.target == "goblin"
        assert obj.required_count == 5
    
    def test_create_find_objective(self):
        """Test find item objective factory."""
        obj = create_find_objective("find_key", "Find the key", "boss_key")
        assert obj.objective_type == ObjectiveType.FIND_ITEM
        assert obj.target == "boss_key"
        assert obj.required_count == 1
    
    def test_create_talk_objective(self):
        """Test talk to NPC objective factory."""
        obj = create_talk_objective("talk_lily", "Talk to Lily", "lily_npc")
        assert obj.objective_type == ObjectiveType.TALK_TO
        assert obj.target == "lily_npc"
    
    def test_create_location_objective(self):
        """Test reach location objective factory."""
        obj = create_location_objective("reach_boss", "Reach the boss chamber", "boss_chamber")
        assert obj.objective_type == ObjectiveType.REACH_LOCATION
        assert obj.target == "boss_chamber"
    
    def test_create_collect_objective(self):
        """Test collect items objective factory."""
        obj = create_collect_objective("collect_gems", "Collect 3 gems", "gem", 3)
        assert obj.objective_type == ObjectiveType.COLLECT
        assert obj.required_count == 3


# =============================================================================
# QUEST TESTS
# =============================================================================

class TestQuest:
    """Tests for Quest dataclass."""
    
    def test_create_quest(self):
        """Test creating a basic quest."""
        quest = Quest(
            id="rescue_lily",
            name="Rescue Lily",
            description="Find and rescue Lily from the goblin cave."
        )
        
        assert quest.id == "rescue_lily"
        assert quest.name == "Rescue Lily"
        assert quest.status == QuestStatus.NOT_STARTED
        assert quest.objectives == []
        assert quest.rewards == {}
    
    def test_quest_validation_no_id(self):
        """Test that quest requires id."""
        with pytest.raises(ValueError, match="must have an id"):
            Quest(id="", name="Test", description="A test.")
    
    def test_quest_validation_no_name(self):
        """Test that quest requires name."""
        with pytest.raises(ValueError, match="must have a name"):
            Quest(id="test", name="", description="A test.")
    
    def test_quest_accept(self):
        """Test accepting a quest."""
        quest = Quest(id="test", name="Test Quest", description="A test.")
        
        result = quest.accept()
        
        assert result == True
        assert quest.status == QuestStatus.ACTIVE
    
    def test_quest_accept_already_active(self):
        """Test that can't accept already active quest."""
        quest = Quest(id="test", name="Test Quest", description="A test.")
        quest.accept()
        
        result = quest.accept()
        
        assert result == False
    
    def test_quest_fail(self):
        """Test failing a quest."""
        quest = Quest(id="test", name="Test Quest", description="A test.")
        quest.accept()
        
        result = quest.fail()
        
        assert result == True
        assert quest.status == QuestStatus.FAILED
    
    def test_quest_fail_not_active(self):
        """Test that can't fail non-active quest."""
        quest = Quest(id="test", name="Test Quest", description="A test.")
        
        result = quest.fail()
        
        assert result == False
    
    def test_quest_is_ready_no_objectives(self):
        """Test quest with no objectives is ready to complete."""
        quest = Quest(id="test", name="Test Quest", description="A test.")
        quest.accept()
        
        assert quest.is_ready_to_complete() == True
    
    def test_quest_is_ready_with_objectives(self):
        """Test quest ready when required objectives complete."""
        quest = Quest(id="test", name="Test Quest", description="A test.")
        quest.add_objective(create_kill_objective("k1", "Kill goblin", "goblin", 1))
        quest.add_objective(create_find_objective("f1", "Find key", "key", optional=True))
        quest.accept()
        
        assert quest.is_ready_to_complete() == False
        
        # Complete required objective
        quest.objectives[0].update_progress(1)
        
        assert quest.is_ready_to_complete() == True  # Optional not needed
    
    def test_quest_complete(self):
        """Test completing a quest."""
        quest = Quest(
            id="test",
            name="Test Quest",
            description="A test.",
            rewards={"gold": 100, "xp": 50}
        )
        quest.accept()
        
        result = quest.complete()
        
        assert result == True
        assert quest.status == QuestStatus.COMPLETE
    
    def test_quest_complete_not_ready(self):
        """Test can't complete quest with incomplete objectives."""
        quest = Quest(id="test", name="Test Quest", description="A test.")
        quest.add_objective(create_kill_objective("k1", "Kill goblin", "goblin", 1))
        quest.accept()
        
        result = quest.complete()
        
        assert result == False
        assert quest.status == QuestStatus.ACTIVE
    
    def test_quest_check_objective(self):
        """Test checking objectives in quest."""
        quest = Quest(id="test", name="Test Quest", description="A test.")
        quest.add_objective(create_kill_objective("k1", "Kill 3 goblins", "goblin", 3))
        quest.add_objective(create_kill_objective("k2", "Kill wolf", "wolf", 1))
        quest.accept()
        
        completed = quest.check_objective(ObjectiveType.KILL, "goblin", 2)
        
        assert len(completed) == 0  # Not complete yet
        assert quest.objectives[0].current_count == 2
        
        completed = quest.check_objective(ObjectiveType.KILL, "goblin", 1)
        
        assert len(completed) == 1  # First objective completed
        assert quest.objectives[0].completed == True
    
    def test_quest_get_completion_percentage(self):
        """Test quest completion percentage."""
        quest = Quest(id="test", name="Test Quest", description="A test.")
        quest.add_objective(create_kill_objective("k1", "Kill goblin 1", "goblin", 1))
        quest.add_objective(create_kill_objective("k2", "Kill goblin 2", "goblin", 1))
        quest.add_objective(create_find_objective("f1", "Find item", "item", optional=True))
        quest.accept()
        
        assert quest.get_completion_percentage() == 0.0
        
        quest.objectives[0].update_progress(1)
        assert quest.get_completion_percentage() == 50.0
        
        quest.objectives[1].update_progress(1)
        assert quest.get_completion_percentage() == 100.0  # Optional doesn't count
    
    def test_quest_time_limit(self):
        """Test time-limited quest."""
        quest = Quest(
            id="test",
            name="Test Quest",
            description="A test.",
            time_limit=3
        )
        quest.accept()
        
        assert quest.turns_remaining == 3
        
        quest.tick_time()
        assert quest.turns_remaining == 2
        
        quest.tick_time()
        assert quest.turns_remaining == 1
        
        failed = quest.tick_time()
        assert failed == True
        assert quest.status == QuestStatus.FAILED
    
    def test_quest_serialization(self):
        """Test quest to_dict/from_dict."""
        quest = Quest(
            id="rescue_lily",
            name="Rescue Lily",
            description="Find and rescue Lily.",
            giver_npc_id="bram",
            rewards={"gold": 100, "xp": 50},
            prerequisites=["intro_quest"],
            time_limit=10,
            on_accept_dialogue="Help me!"
        )
        quest.add_objective(create_kill_objective("k1", "Kill chief", "goblin_chieftain", 1))
        quest.accept()
        quest.objectives[0].update_progress(1)
        
        data = quest.to_dict()
        loaded = Quest.from_dict(data)
        
        assert loaded.id == quest.id
        assert loaded.name == quest.name
        assert loaded.status == quest.status
        assert len(loaded.objectives) == 1
        assert loaded.objectives[0].completed == True
        assert loaded.rewards == quest.rewards
        assert loaded.time_limit == quest.time_limit
    
    def test_quest_get_summary(self):
        """Test quest summary display."""
        quest = Quest(id="test", name="Test Quest", description="A test.")
        
        assert "○" in quest.get_summary()  # Not started
        
        quest.accept()
        assert "◉" in quest.get_summary()  # Active
        
        quest.complete()
        assert "✓" in quest.get_summary()  # Complete
    
    def test_quest_get_detailed_display(self):
        """Test quest detailed display."""
        quest = Quest(
            id="test",
            name="Test Quest",
            description="A test quest description.",
            rewards={"gold": 100, "xp": 50}
        )
        quest.add_objective(create_kill_objective("k1", "Kill goblin", "goblin", 1))
        
        display = quest.get_detailed_display()
        
        assert "Test Quest" in display
        assert "OBJECTIVES:" in display
        assert "Kill goblin" in display
        assert "REWARDS:" in display
        assert "100g" in display


# =============================================================================
# QUEST MANAGER TESTS
# =============================================================================

class TestQuestManager:
    """Tests for QuestManager class."""
    
    def test_create_manager(self):
        """Test creating a quest manager."""
        manager = QuestManager()
        
        assert manager.available_quests == {}
        assert manager.active_quests == {}
        assert manager.completed_quests == []
        assert manager.failed_quests == []
    
    def test_register_quest(self):
        """Test registering a quest."""
        manager = QuestManager()
        quest = Quest(id="test", name="Test Quest", description="A test.")
        
        manager.register_quest(quest)
        
        assert "test" in manager.available_quests
        assert manager.get_available_quest("test") == quest
    
    def test_accept_quest(self):
        """Test accepting a quest."""
        manager = QuestManager()
        quest = Quest(id="test", name="Test Quest", description="A test.")
        manager.register_quest(quest)
        
        accepted = manager.accept_quest("test")
        
        assert accepted is not None
        assert accepted.status == QuestStatus.ACTIVE
        assert "test" in manager.active_quests
    
    def test_accept_quest_not_available(self):
        """Test accepting non-existent quest."""
        manager = QuestManager()
        
        result = manager.accept_quest("nonexistent")
        
        assert result is None
    
    def test_accept_quest_already_active(self):
        """Test can't accept quest twice."""
        manager = QuestManager()
        quest = Quest(id="test", name="Test Quest", description="A test.")
        manager.register_quest(quest)
        manager.accept_quest("test")
        
        result = manager.accept_quest("test")
        
        assert result is None
    
    def test_complete_quest(self):
        """Test completing a quest."""
        manager = QuestManager()
        quest = Quest(
            id="test",
            name="Test Quest",
            description="A test.",
            rewards={"gold": 100, "xp": 50}
        )
        manager.register_quest(quest)
        manager.accept_quest("test")
        
        result = manager.complete_quest("test")
        
        assert result is not None
        rewards, completed_quest = result
        assert rewards == {"gold": 100, "xp": 50}
        assert completed_quest.id == "test"
        assert "test" in manager.completed_quests
        assert "test" not in manager.active_quests
    
    def test_complete_quest_not_ready(self):
        """Test can't complete quest with incomplete objectives."""
        manager = QuestManager()
        quest = Quest(id="test", name="Test Quest", description="A test.")
        quest.add_objective(create_kill_objective("k1", "Kill goblin", "goblin", 1))
        manager.register_quest(quest)
        manager.accept_quest("test")
        
        rewards = manager.complete_quest("test")
        
        assert rewards is None
        assert "test" in manager.active_quests
    
    def test_fail_quest(self):
        """Test failing a quest."""
        manager = QuestManager()
        quest = Quest(id="test", name="Test Quest", description="A test.")
        manager.register_quest(quest)
        manager.accept_quest("test")
        
        result = manager.fail_quest("test")
        
        assert result == True
        assert "test" in manager.failed_quests
        assert "test" not in manager.active_quests
    
    def test_abandon_quest(self):
        """Test abandoning a quest."""
        manager = QuestManager()
        quest = Quest(id="test", name="Test Quest", description="A test.")
        manager.register_quest(quest)
        manager.accept_quest("test")
        
        result = manager.abandon_quest("test")
        
        assert result == True
        assert "test" not in manager.active_quests
        assert "test" not in manager.failed_quests  # Can be re-accepted
    
    def test_check_objective_kill(self):
        """Test kill objective tracking."""
        manager = QuestManager()
        quest = Quest(id="test", name="Test Quest", description="A test.")
        quest.add_objective(create_kill_objective("k1", "Kill 3 goblins", "goblin", 3))
        manager.register_quest(quest)
        manager.accept_quest("test")
        
        completed = manager.on_enemy_killed("goblin", 2)
        assert len(completed) == 0
        
        completed = manager.on_enemy_killed("goblin", 1)
        assert len(completed) == 1
        assert completed[0][0] == "test"
        assert completed[0][1].id == "k1"
    
    def test_check_objective_item(self):
        """Test item pickup objective tracking."""
        manager = QuestManager()
        quest = Quest(id="test", name="Test Quest", description="A test.")
        quest.add_objective(create_find_objective("f1", "Find the key", "boss_key"))
        manager.register_quest(quest)
        manager.accept_quest("test")
        
        completed = manager.on_item_acquired("boss_key")
        
        assert len(completed) == 1
    
    def test_check_objective_location(self):
        """Test location objective tracking."""
        manager = QuestManager()
        quest = Quest(id="test", name="Test Quest", description="A test.")
        quest.add_objective(create_location_objective("l1", "Reach boss room", "boss_chamber"))
        manager.register_quest(quest)
        manager.accept_quest("test")
        
        completed = manager.on_location_entered("boss_chamber")
        
        assert len(completed) == 1
    
    def test_check_objective_talk(self):
        """Test talk to NPC objective tracking."""
        manager = QuestManager()
        quest = Quest(id="test", name="Test Quest", description="A test.")
        quest.add_objective(create_talk_objective("t1", "Talk to Lily", "lily"))
        manager.register_quest(quest)
        manager.accept_quest("test")
        
        completed = manager.on_npc_talked("lily")
        
        assert len(completed) == 1
    
    def test_check_objective_collect(self):
        """Test collect items objective tracking."""
        manager = QuestManager()
        quest = Quest(id="test", name="Test Quest", description="A test.")
        quest.add_objective(create_collect_objective("c1", "Collect 3 gems", "gem", 3))
        manager.register_quest(quest)
        manager.accept_quest("test")
        
        manager.on_item_acquired("gem", 2)
        completed = manager.on_item_acquired("gem", 1)
        
        assert len(completed) == 1
    
    def test_prerequisite_check(self):
        """Test prerequisite quest checking."""
        manager = QuestManager()
        
        quest1 = Quest(id="intro", name="Intro Quest", description="First quest.")
        quest2 = Quest(
            id="main",
            name="Main Quest",
            description="Requires intro.",
            prerequisites=["intro"]
        )
        
        manager.register_quest(quest1)
        manager.register_quest(quest2)
        
        # Can't accept main before completing intro
        result = manager.accept_quest("main")
        assert result is None
        
        # Complete intro
        manager.accept_quest("intro")
        manager.complete_quest("intro")
        
        # Now can accept main
        result = manager.accept_quest("main")
        assert result is not None
    
    def test_get_available_quests_for_npc(self):
        """Test getting quests from specific NPC."""
        manager = QuestManager()
        
        quest1 = Quest(id="q1", name="Quest 1", description="A", giver_npc_id="bram")
        quest2 = Quest(id="q2", name="Quest 2", description="B", giver_npc_id="bram")
        quest3 = Quest(id="q3", name="Quest 3", description="C", giver_npc_id="mira")
        
        manager.register_quest(quest1)
        manager.register_quest(quest2)
        manager.register_quest(quest3)
        
        bram_quests = manager.get_available_quests_for_npc("bram")
        
        assert len(bram_quests) == 2
        assert all(q.giver_npc_id == "bram" for q in bram_quests)
    
    def test_get_ready_to_complete(self):
        """Test getting quests ready to turn in."""
        manager = QuestManager()
        
        quest1 = Quest(id="q1", name="Quest 1", description="A")
        quest1.add_objective(create_kill_objective("k1", "Kill", "goblin", 1))
        
        quest2 = Quest(id="q2", name="Quest 2", description="B")  # No objectives
        
        manager.register_quest(quest1)
        manager.register_quest(quest2)
        manager.accept_quest("q1")
        manager.accept_quest("q2")
        
        ready = manager.get_ready_to_complete()
        
        assert len(ready) == 1
        assert ready[0].id == "q2"
    
    def test_tick_all_quests(self):
        """Test advancing time for all quests."""
        manager = QuestManager()
        
        quest1 = Quest(id="q1", name="Quest 1", description="A", time_limit=2)
        quest2 = Quest(id="q2", name="Quest 2", description="B")  # No time limit
        
        manager.register_quest(quest1)
        manager.register_quest(quest2)
        manager.accept_quest("q1")
        manager.accept_quest("q2")
        
        manager.tick_all_quests()
        assert len(manager.failed_quests) == 0
        
        failed = manager.tick_all_quests()
        assert len(failed) == 1
        assert "q1" in failed
        assert "q1" in manager.failed_quests
    
    def test_manager_serialization(self):
        """Test quest manager to_dict/from_dict."""
        manager = QuestManager()
        
        quest1 = Quest(id="q1", name="Quest 1", description="A")
        quest1.add_objective(create_kill_objective("k1", "Kill", "goblin", 3))
        
        manager.register_quest(quest1)
        manager.accept_quest("q1")
        manager.active_quests["q1"].objectives[0].update_progress(2)
        
        data = manager.to_dict()
        
        # Create new manager and load
        new_manager = QuestManager()
        new_manager.register_quest(quest1)  # Re-register definitions
        new_manager.from_dict(data)
        
        assert "q1" in new_manager.active_quests
        assert new_manager.active_quests["q1"].objectives[0].current_count == 2
    
    def test_format_quest_log(self):
        """Test quest log formatting."""
        manager = QuestManager()
        
        quest = Quest(id="q1", name="Test Quest", description="A")
        manager.register_quest(quest)
        manager.accept_quest("q1")
        
        log = manager.format_quest_log()
        
        assert "QUEST LOG" in log
        assert "Test Quest" in log
    
    def test_is_quest_queries(self):
        """Test quest status query methods."""
        manager = QuestManager()
        
        quest = Quest(id="test", name="Test", description="A")
        manager.register_quest(quest)
        
        assert manager.is_quest_active("test") == False
        assert manager.is_quest_complete("test") == False
        assert manager.is_quest_failed("test") == False
        
        manager.accept_quest("test")
        assert manager.is_quest_active("test") == True
        
        manager.complete_quest("test")
        assert manager.is_quest_complete("test") == True
        assert manager.is_quest_active("test") == False
    
    def test_clear_manager(self):
        """Test clearing quest manager."""
        manager = QuestManager()
        
        quest = Quest(id="test", name="Test", description="A")
        manager.register_quest(quest)
        manager.accept_quest("test")
        manager.completed_quests.append("old")
        
        manager.clear()
        
        assert manager.available_quests == {}
        assert manager.active_quests == {}
        assert manager.completed_quests == []


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestQuestIntegration:
    """Integration tests for quest system workflows."""
    
    def test_full_quest_workflow(self):
        """Test complete quest from accept to complete."""
        manager = QuestManager()
        
        # Create quest with multiple objectives
        quest = Quest(
            id="rescue_mission",
            name="Rescue Mission",
            description="Save the captive!",
            giver_npc_id="bram",
            rewards={"gold": 100, "xp": 150, "items": ["family_ring"]}
        )
        quest.add_objective(create_location_objective(
            "reach_boss", "Reach the boss chamber", "boss_chamber"
        ))
        quest.add_objective(create_kill_objective(
            "kill_chief", "Defeat the chieftain", "goblin_chieftain", 1
        ))
        quest.add_objective(create_talk_objective(
            "talk_lily", "Speak with Lily", "lily"
        ))
        quest.add_objective(create_find_objective(
            "bonus_ring", "Find the hidden ring", "ancient_ring", optional=True
        ))
        
        manager.register_quest(quest)
        
        # Accept quest
        accepted = manager.accept_quest("rescue_mission")
        assert accepted is not None
        assert accepted.status == QuestStatus.ACTIVE
        
        # Progress through objectives
        manager.on_location_entered("boss_chamber")
        assert accepted.get_completion_percentage() == pytest.approx(33.3, rel=0.1)
        
        manager.on_enemy_killed("goblin_chieftain")
        assert accepted.get_completion_percentage() == pytest.approx(66.6, rel=0.1)
        
        manager.on_npc_talked("lily")
        assert accepted.get_completion_percentage() == 100.0
        
        # Quest is ready (optional not required)
        assert accepted.is_ready_to_complete() == True
        assert manager.get_ready_to_complete() == [accepted]
        
        # Complete and get rewards
        result = manager.complete_quest("rescue_mission")
        assert result is not None
        rewards, completed_quest = result
        assert rewards == {"gold": 100, "xp": 150, "items": ["family_ring"]}
        assert completed_quest.id == "rescue_mission"
        assert manager.is_quest_complete("rescue_mission") == True
    
    def test_multiple_active_quests(self):
        """Test tracking multiple quests simultaneously."""
        manager = QuestManager()
        
        quest1 = Quest(id="q1", name="Kill Goblins", description="A", giver_npc_id="guard")
        quest1.add_objective(create_kill_objective("k1", "Kill 5 goblins", "goblin", 5))
        
        quest2 = Quest(id="q2", name="Find Items", description="B", giver_npc_id="elder")
        quest2.add_objective(create_collect_objective("c1", "Collect 3 gems", "gem", 3))
        
        manager.register_quest(quest1)
        manager.register_quest(quest2)
        
        manager.accept_quest("q1")
        manager.accept_quest("q2")
        
        assert len(manager.get_active_quests()) == 2
        
        # Kill goblins should only affect q1
        manager.on_enemy_killed("goblin", 3)
        assert manager.active_quests["q1"].objectives[0].current_count == 3
        assert manager.active_quests["q2"].objectives[0].current_count == 0
        
        # Gems should only affect q2
        manager.on_item_acquired("gem", 2)
        assert manager.active_quests["q1"].objectives[0].current_count == 3
        assert manager.active_quests["q2"].objectives[0].current_count == 2
    
    def test_objective_callback(self):
        """Test objective completion callbacks."""
        manager = QuestManager()
        
        quest = Quest(id="test", name="Test", description="A")
        quest.add_objective(create_kill_objective("k1", "Kill goblin", "goblin", 1))
        manager.register_quest(quest)
        manager.accept_quest("test")
        
        # Track callback calls
        callback_calls = []
        def on_complete(quest_id, obj):
            callback_calls.append((quest_id, obj.id))
        
        manager.register_objective_callback(on_complete)
        
        manager.on_enemy_killed("goblin")
        
        assert len(callback_calls) == 1
        assert callback_calls[0] == ("test", "k1")
