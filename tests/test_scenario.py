"""
Comprehensive tests for the Scenario system.
Covers: scenes, scenarios, progression, objectives, transitions.
"""

import pytest
import sys
sys.path.insert(0, '../src')

from scenario import (
    Scene, SceneStatus, Scenario,
    create_goblin_cave_scenario
)


class TestSceneBasics:
    """Tests for Scene dataclass."""
    
    def test_create_scene(self):
        """Test creating a basic scene."""
        scene = Scene(
            id="test_scene",
            name="Test Scene",
            description="A test scene",
            setting="A test location",
            mood="neutral",
            dm_instructions="Test instructions"
        )
        assert scene.id == "test_scene"
        assert scene.name == "Test Scene"
        assert scene.status == SceneStatus.LOCKED
        assert scene.exchange_count == 0
    
    def test_scene_status_enum(self):
        """Test all scene statuses exist."""
        assert SceneStatus.LOCKED.value == "locked"
        assert SceneStatus.ACTIVE.value == "active"
        assert SceneStatus.COMPLETED.value == "completed"
    
    def test_scene_with_objectives(self):
        """Test scene with objectives."""
        scene = Scene(
            id="objective_scene",
            name="Objective Scene",
            description="Scene with objectives",
            setting="Test",
            mood="test",
            dm_instructions="Test",
            objectives=["find_key", "defeat_boss"]
        )
        assert len(scene.objectives) == 2
        assert "find_key" in scene.objectives


class TestScenarioBasics:
    """Tests for Scenario dataclass."""
    
    def test_create_scenario(self):
        """Test creating an empty scenario."""
        scenario = Scenario(
            id="test",
            name="Test Scenario",
            description="A test scenario",
            hook="Begin your adventure!",
            estimated_duration="5 minutes"
        )
        assert scenario.id == "test"
        assert scenario.name == "Test Scenario"
        assert scenario.is_complete == False
        assert scenario.current_scene_id is None
    
    def test_scenario_start(self):
        """Test starting a scenario."""
        scenario = _create_test_scenario()
        first_scene = scenario.start()
        
        assert scenario.current_scene_id == "scene1"
        assert first_scene.status == SceneStatus.ACTIVE
        assert first_scene.id == "scene1"
    
    def test_scenario_start_no_scenes_raises(self):
        """Test starting scenario with no scenes raises error."""
        scenario = Scenario(
            id="empty",
            name="Empty",
            description="Empty",
            hook="None",
            estimated_duration="0"
        )
        with pytest.raises(ValueError):
            scenario.start()


class TestScenarioProgression:
    """Tests for scenario progression mechanics."""
    
    def test_get_current_scene(self):
        """Test getting current scene."""
        scenario = _create_test_scenario()
        scenario.start()
        
        scene = scenario.get_current_scene()
        assert scene is not None
        assert scene.id == "scene1"
    
    def test_record_exchange(self):
        """Test recording player exchanges."""
        scenario = _create_test_scenario()
        scenario.start()
        
        assert scenario.get_current_scene().exchange_count == 0
        scenario.record_exchange()
        assert scenario.get_current_scene().exchange_count == 1
        scenario.record_exchange()
        assert scenario.get_current_scene().exchange_count == 2
    
    def test_can_transition_min_exchanges(self):
        """Test transition requires minimum exchanges."""
        scenario = _create_test_scenario()
        scenario.start()
        
        # Need 2 exchanges minimum
        assert scenario.can_transition() == False
        scenario.record_exchange()
        assert scenario.can_transition() == False
        scenario.record_exchange()
        assert scenario.can_transition() == True
    
    def test_transition_to_next_scene(self):
        """Test transitioning between scenes."""
        scenario = _create_test_scenario()
        scenario.start()
        scenario.record_exchange()
        scenario.record_exchange()
        
        next_scene = scenario.transition_to_next()
        
        assert next_scene is not None
        assert next_scene.id == "scene2"
        assert scenario.current_scene_id == "scene2"
        assert scenario.scenes["scene1"].status == SceneStatus.COMPLETED
    
    def test_transition_ends_scenario(self):
        """Test transitioning when at last scene."""
        scenario = _create_test_scenario()
        scenario.start()
        
        # Move through scene1
        scenario.record_exchange()
        scenario.record_exchange()
        scenario.transition_to_next()
        
        # Move through scene2
        scenario.record_exchange()
        scenario.record_exchange()
        next_scene = scenario.transition_to_next()
        
        assert next_scene is None
        assert scenario.is_complete == True
        assert scenario.current_scene_id is None


class TestObjectives:
    """Tests for objective system."""
    
    def test_complete_objective(self):
        """Test completing an objective."""
        scenario = _create_objective_scenario()
        scenario.start()
        
        result = scenario.complete_objective("find_treasure")
        assert result == True
        assert "find_treasure" in scenario.get_current_scene().objectives_complete
    
    def test_complete_invalid_objective(self):
        """Test completing non-existent objective."""
        scenario = _create_objective_scenario()
        scenario.start()
        
        result = scenario.complete_objective("nonexistent")
        assert result == False
    
    def test_cannot_transition_without_objectives(self):
        """Test can't transition until objectives complete."""
        scenario = _create_objective_scenario()
        scenario.start()
        scenario.record_exchange()
        scenario.record_exchange()
        
        # Have min exchanges but not objectives
        assert scenario.can_transition() == False
        
        # Complete objective
        scenario.complete_objective("find_treasure")
        assert scenario.can_transition() == True
    
    def test_duplicate_objective_completion(self):
        """Test completing same objective twice doesn't double-add."""
        scenario = _create_objective_scenario()
        scenario.start()
        
        scenario.complete_objective("find_treasure")
        scenario.complete_objective("find_treasure")
        
        scene = scenario.get_current_scene()
        count = scene.objectives_complete.count("find_treasure")
        assert count == 1


class TestScenarioDisplay:
    """Tests for display/formatting methods."""
    
    def test_get_scene_context_for_dm(self):
        """Test DM context generation."""
        scenario = _create_test_scenario()
        scenario.start()
        
        context = scenario.get_scene_context_for_dm()
        assert "Scene 1" in context
        assert "CURRENT SCENE" in context
        assert "Setting" in context
        assert "Mood" in context
    
    def test_get_progress_display(self):
        """Test progress display formatting."""
        scenario = _create_test_scenario()
        scenario.start()
        
        progress = scenario.get_progress_display()
        assert "Scene 1/2" in progress
        assert "█" in progress or "░" in progress
    
    def test_progress_display_complete(self):
        """Test progress display when complete."""
        scenario = _create_test_scenario()
        scenario.start()
        scenario.record_exchange()
        scenario.record_exchange()
        scenario.transition_to_next()
        scenario.record_exchange()
        scenario.record_exchange()
        scenario.transition_to_next()
        
        progress = scenario.get_progress_display()
        assert "Complete" in progress


class TestGoblinCaveScenario:
    """Tests for the preset Goblin Cave scenario."""
    
    def test_create_goblin_cave(self):
        """Test creating the Goblin Cave scenario."""
        scenario = create_goblin_cave_scenario()
        assert scenario is not None
        assert scenario.name == "The Goblin Cave"
        assert len(scenario.scenes) > 0
    
    def test_goblin_cave_has_scenes(self):
        """Test Goblin Cave has multiple scenes."""
        scenario = create_goblin_cave_scenario()
        assert len(scenario.scene_order) > 0
    
    def test_goblin_cave_can_start(self):
        """Test Goblin Cave can be started."""
        scenario = create_goblin_cave_scenario()
        scene = scenario.start()
        assert scene is not None
        assert scenario.current_scene_id is not None
    
    def test_goblin_cave_first_scene(self):
        """Test first scene has proper setup."""
        scenario = create_goblin_cave_scenario()
        scene = scenario.start()
        
        assert scene.name is not None
        assert scene.setting is not None
        assert scene.dm_instructions is not None


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_get_current_scene_when_none(self):
        """Test getting current scene when not started."""
        scenario = _create_test_scenario()
        scene = scenario.get_current_scene()
        assert scene is None
    
    def test_record_exchange_no_scene(self):
        """Test recording exchange with no current scene."""
        scenario = _create_test_scenario()
        # Should not raise error
        scenario.record_exchange()
    
    def test_complete_objective_no_scene(self):
        """Test completing objective with no current scene."""
        scenario = _create_test_scenario()
        result = scenario.complete_objective("test")
        assert result == False
    
    def test_context_when_complete(self):
        """Test DM context when scenario is complete."""
        scenario = _create_test_scenario()
        scenario.is_complete = True
        
        context = scenario.get_scene_context_for_dm()
        assert "COMPLETE" in context


# =============================================================================
# Helper Functions
# =============================================================================

def _create_test_scenario() -> Scenario:
    """Create a simple test scenario with 2 scenes."""
    scenario = Scenario(
        id="test",
        name="Test Scenario",
        description="A test scenario",
        hook="Test hook",
        estimated_duration="5 minutes"
    )
    
    scene1 = Scene(
        id="scene1",
        name="Scene 1",
        description="First scene",
        setting="Test location 1",
        mood="neutral",
        dm_instructions="Test instructions 1",
        min_exchanges=2,
        next_scene_id="scene2"
    )
    
    scene2 = Scene(
        id="scene2",
        name="Scene 2",
        description="Second scene",
        setting="Test location 2",
        mood="neutral",
        dm_instructions="Test instructions 2",
        min_exchanges=2,
        next_scene_id=None  # Final scene
    )
    
    scenario.scenes = {"scene1": scene1, "scene2": scene2}
    scenario.scene_order = ["scene1", "scene2"]
    
    return scenario


def _create_objective_scenario() -> Scenario:
    """Create a test scenario with objectives."""
    scenario = Scenario(
        id="objective_test",
        name="Objective Test",
        description="Test with objectives",
        hook="Test",
        estimated_duration="5 minutes"
    )
    
    scene = Scene(
        id="objective_scene",
        name="Objective Scene",
        description="Scene with objectives",
        setting="Test",
        mood="test",
        dm_instructions="Test",
        min_exchanges=2,
        objectives=["find_treasure"]
    )
    
    scenario.scenes = {"objective_scene": scene}
    scenario.scene_order = ["objective_scene"]
    
    return scenario


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
