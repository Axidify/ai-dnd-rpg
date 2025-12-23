"""
Tests for the Phase 3.4 Moral Choices system.

Tests cover:
- Choice and ChoiceOption dataclasses
- ChoiceManager registration and triggering
- Consequence application
- Ending point tracking
- API endpoints for choices
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from scenario import (
    Choice, ChoiceOption, ChoiceConsequence, ChoiceType, ChoiceManager,
    create_goblin_cave_choices, create_goblin_cave_scenario
)


# =============================================================================
# CHOICE DATACLASS TESTS
# =============================================================================

class TestChoiceDataclasses:
    """Test the Choice-related dataclasses."""
    
    def test_choice_consequence_creation(self):
        """Test creating a ChoiceConsequence."""
        consequence = ChoiceConsequence(
            id="helped_prisoner",
            description="You helped the prisoner escape",
            xp_reward=50,
            gold_change=-10,
            flag_changes={'helped_prisoner': True},
            ending_points={'mercy': 1}
        )
        
        assert consequence.id == "helped_prisoner"
        assert consequence.description == "You helped the prisoner escape"
        assert consequence.xp_reward == 50
        assert consequence.gold_change == -10
        assert consequence.flag_changes == {'helped_prisoner': True}
        assert consequence.ending_points == {'mercy': 1}
    
    def test_choice_consequence_defaults(self):
        """Test ChoiceConsequence with defaults for optional fields."""
        consequence = ChoiceConsequence(id="test", description="Test consequence")
        
        assert consequence.id == "test"
        assert consequence.xp_reward == 0
        assert consequence.gold_change == 0
        assert consequence.flag_changes == {}
        assert consequence.ending_points == {}
    
    def test_choice_consequence_to_dict(self):
        """Test ChoiceConsequence serialization."""
        consequence = ChoiceConsequence(
            id="test",
            description="Test",
            xp_reward=25,
            ending_points={'hero': 1}
        )
        data = consequence.to_dict()
        
        assert data['id'] == 'test'
        assert data['xp_reward'] == 25
        assert data['ending_points'] == {'hero': 1}
    
    def test_choice_consequence_from_dict(self):
        """Test ChoiceConsequence deserialization."""
        data = {
            'id': 'loaded',
            'description': 'Loaded consequence',
            'xp_reward': 30,
            'ending_points': {'mercy': 2}
        }
        consequence = ChoiceConsequence.from_dict(data)
        
        assert consequence.id == 'loaded'
        assert consequence.xp_reward == 30
        assert consequence.ending_points == {'mercy': 2}
    
    def test_choice_option_creation(self):
        """Test creating a ChoiceOption."""
        consequence = ChoiceConsequence(id="spare", description="Spared goblin", xp_reward=25)
        option = ChoiceOption(
            id="spare_option",
            text="Spare the goblin",
            consequence=consequence,
            skill_check="persuasion:12"
        )
        
        assert option.id == "spare_option"
        assert option.text == "Spare the goblin"
        assert option.consequence.xp_reward == 25
        assert option.skill_check == "persuasion:12"
    
    def test_choice_option_requirements(self):
        """Test ChoiceOption with requirements."""
        option = ChoiceOption(
            id="use_key",
            text="Use the magic key",
            consequence=ChoiceConsequence(id="used_key", description="Used the key"),
            required_item="magic_key",
            required_flag="knows_secret"
        )
        
        assert option.required_item == "magic_key"
        assert option.required_flag == "knows_secret"
    
    def test_choice_option_to_dict(self):
        """Test ChoiceOption serialization."""
        option = ChoiceOption(
            id="test_opt",
            text="Test option",
            consequence=ChoiceConsequence(id="c", description="Consequence"),
            is_default=True,
            tooltip="Extra info"
        )
        data = option.to_dict()
        
        assert data['id'] == 'test_opt'
        assert data['text'] == 'Test option'
        assert data['is_default'] is True
        assert data['tooltip'] == 'Extra info'
    
    def test_choice_creation(self):
        """Test creating a Choice."""
        options = [
            ChoiceOption(id="opt_a", text="Option A", consequence=ChoiceConsequence(id="a", description="A")),
            ChoiceOption(id="opt_b", text="Option B", consequence=ChoiceConsequence(id="b", description="B")),
        ]
        
        choice = Choice(
            id="test_choice",
            prompt="What do you do?",
            options=options,
            choice_type=ChoiceType.MORAL,
            trigger_location="cave"
        )
        
        assert choice.id == "test_choice"
        assert choice.prompt == "What do you do?"
        assert len(choice.options) == 2
        assert choice.choice_type == ChoiceType.MORAL
        assert choice.trigger_location == "cave"
    
    def test_choice_types(self):
        """Test different choice types."""
        assert ChoiceType.MORAL.value == "moral"
        assert ChoiceType.TACTICAL.value == "tactical"
        assert ChoiceType.DIALOGUE.value == "dialogue"
        assert ChoiceType.STORY.value == "story"


# =============================================================================
# CHOICE MANAGER TESTS
# =============================================================================

class TestChoiceManager:
    """Test the ChoiceManager class."""
    
    @pytest.fixture
    def manager(self):
        """Create a fresh ChoiceManager."""
        return ChoiceManager()
    
    @pytest.fixture
    def sample_choices(self):
        """Create sample choices for testing."""
        return [
            Choice(
                id="cave_prisoner",
                prompt="A goblin prisoner begs for mercy. What do you do?",
                options=[
                    ChoiceOption(
                        id="spare_prisoner",
                        text="Spare the prisoner",
                        consequence=ChoiceConsequence(
                            id="spared",
                            description="You spared the prisoner",
                            xp_reward=25,
                            ending_points={'mercy': 1}
                        )
                    ),
                    ChoiceOption(
                        id="kill_prisoner",
                        text="Kill the prisoner",
                        consequence=ChoiceConsequence(
                            id="killed",
                            description="You killed the prisoner",
                            xp_reward=10,
                            ending_points={'ruthless': 1}
                        )
                    ),
                ],
                choice_type=ChoiceType.MORAL,
                trigger_location="goblin_camp"
            ),
            Choice(
                id="chief_offer",
                prompt="The goblin chief offers a bribe.",
                options=[
                    ChoiceOption(
                        id="accept_bribe",
                        text="Accept the gold",
                        consequence=ChoiceConsequence(
                            id="accepted_bribe",
                            description="You accepted the bribe",
                            gold_change=100,
                            ending_points={'mercenary': 1}
                        )
                    ),
                    ChoiceOption(
                        id="refuse_fight",
                        text="Refuse and fight",
                        consequence=ChoiceConsequence(
                            id="refused_bribe",
                            description="You refused and chose to fight",
                            ending_points={'hero': 1}
                        )
                    ),
                ],
                choice_type=ChoiceType.MORAL,
                trigger_location="boss_chamber"
            ),
        ]
    
    def test_register_choice(self, manager):
        """Test registering a single choice."""
        choice = Choice(
            id="test",
            prompt="Test?",
            options=[ChoiceOption(id="yes", text="Yes", consequence=ChoiceConsequence(id="yes_c", description="Yes"))],
            choice_type=ChoiceType.MORAL
        )
        
        manager.register_choice(choice)
        
        assert "test" in manager.choices
        assert manager.get_choice("test") == choice
    
    def test_register_choices_list(self, manager, sample_choices):
        """Test registering multiple choices."""
        manager.register_choices(sample_choices)
        
        assert len(manager.choices) == 2
        assert "cave_prisoner" in manager.choices
        assert "chief_offer" in manager.choices
    
    def test_check_triggers_location(self, manager, sample_choices):
        """Test checking triggers by location."""
        manager.register_choices(sample_choices)
        
        triggered = manager.check_triggers(location_id='goblin_camp')
        
        assert len(triggered) == 1
        assert triggered[0].id == "cave_prisoner"
    
    def test_check_triggers_no_match(self, manager, sample_choices):
        """Test checking triggers with no match."""
        manager.register_choices(sample_choices)
        
        triggered = manager.check_triggers(location_id='tavern')
        
        assert len(triggered) == 0
    
    def test_check_triggers_by_flag(self, manager):
        """Test checking triggers by flag."""
        choice = Choice(
            id="revenge",
            prompt="Take revenge?",
            options=[ChoiceOption(id="yes_revenge", text="Yes", consequence=ChoiceConsequence(id="revenged", description="Took revenge"))],
            choice_type=ChoiceType.MORAL,
            trigger_flag="chief_defeated"
        )
        manager.register_choice(choice)
        
        # Without flag
        assert len(manager.check_triggers(location_id='anywhere')) == 0
        
        # With flag
        triggered = manager.check_triggers(flag='chief_defeated')
        assert len(triggered) == 1
        assert triggered[0].id == "revenge"
    
    def test_check_triggers_already_triggered(self, manager, sample_choices):
        """Test that already-triggered choices don't trigger again."""
        manager.register_choices(sample_choices)
        
        # First trigger
        triggered = manager.check_triggers(location_id='goblin_camp')
        assert len(triggered) == 1
        
        # Mark as triggered
        triggered[0].is_triggered = True
        
        # Should not trigger again
        triggered_again = manager.check_triggers(location_id='goblin_camp')
        assert len(triggered_again) == 0
    
    def test_select_option_by_id(self, manager, sample_choices):
        """Test selecting an option by ID."""
        manager.register_choices(sample_choices)
        
        consequence = manager.select_option("cave_prisoner", "spare_prisoner", None, {})
        
        assert consequence is not None
        assert consequence.xp_reward == 25
        assert consequence.ending_points == {'mercy': 1}
        assert "cave_prisoner" in manager.selected_choices
        assert manager.selected_choices["cave_prisoner"] == "spare_prisoner"
    
    def test_select_option_updates_ending_points(self, manager, sample_choices):
        """Test that selecting updates ending points."""
        manager.register_choices(sample_choices)
        
        manager.select_option("cave_prisoner", "spare_prisoner", None, {})  # Spare = mercy
        manager.select_option("chief_offer", "refuse_fight", None, {})      # Refuse = hero
        
        assert manager.ending_points.get('mercy', 0) == 1
        assert manager.ending_points.get('hero', 0) == 1
    
    def test_select_option_invalid_choice(self, manager):
        """Test selecting from invalid choice."""
        result = manager.select_option("nonexistent", "any", None, {})
        assert result is None
    
    def test_determine_ending_single_winner(self, manager):
        """Test ending determination with clear winner."""
        manager.ending_points = {'mercy': 3, 'ruthless': 1, 'hero': 0}
        
        ending = manager.determine_ending()
        
        assert ending == 'mercy'
    
    def test_determine_ending_neutral(self, manager):
        """Test ending determination with low scores returns neutral."""
        manager.ending_points = {'mercy': 1}  # Less than threshold of 2
        
        ending = manager.determine_ending()
        
        assert ending == 'neutral'
    
    def test_determine_ending_no_points(self, manager):
        """Test ending determination with no points."""
        ending = manager.determine_ending()
        
        assert ending == 'neutral'
    
    def test_manager_to_dict(self, manager, sample_choices):
        """Test serialization of ChoiceManager."""
        manager.register_choices(sample_choices)
        manager.select_option("cave_prisoner", "spare_prisoner", None, {})
        
        data = manager.to_dict()
        
        assert 'choices' in data
        assert 'triggered_choices' in data
        assert 'selected_choices' in data
        assert 'ending_points' in data
        assert data['selected_choices'].get('cave_prisoner') == 'spare_prisoner'


# =============================================================================
# GOBLIN CAVE CHOICES TESTS
# =============================================================================

class TestGoblinCaveChoices:
    """Test the goblin cave scenario choices."""
    
    def test_create_goblin_cave_choices(self):
        """Test that goblin cave choices are created correctly."""
        choices = create_goblin_cave_choices()
        
        assert len(choices) >= 3
        
        choice_ids = [c.id for c in choices]
        assert "goblin_prisoner" in choice_ids
        assert "chief_offer" in choice_ids
        assert "lily_revenge" in choice_ids
    
    def test_goblin_prisoner_choice(self):
        """Test the goblin prisoner choice details."""
        choices = create_goblin_cave_choices()
        prisoner_choice = next(c for c in choices if c.id == "goblin_prisoner")
        
        assert prisoner_choice.choice_type == ChoiceType.MORAL
        assert prisoner_choice.trigger_location == "goblin_camp"
        assert len(prisoner_choice.options) >= 2
        
        # Check options have consequences
        for option in prisoner_choice.options:
            assert option.consequence is not None
    
    def test_chief_offer_choice(self):
        """Test the chief offer choice details."""
        choices = create_goblin_cave_choices()
        chief_choice = next(c for c in choices if c.id == "chief_offer")
        
        assert chief_choice.trigger_location == "boss_chamber"
        assert any("take" in opt.text.lower() and "gold" in opt.text.lower() for opt in chief_choice.options)
        assert any("refuse" in opt.text.lower() for opt in chief_choice.options)
    
    def test_scenario_has_choice_manager(self):
        """Test that goblin cave scenario has choices."""
        scenario = create_goblin_cave_scenario()
        
        assert scenario.choice_manager is not None
        assert len(scenario.choice_manager.choices) >= 3


# =============================================================================
# API ENDPOINT TESTS
# =============================================================================

class TestChoiceAPIEndpoints:
    """Test the choice API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        # Import here to avoid circular imports
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
        from api_server import app
        app.config['TESTING'] = True
        return app.test_client()
    
    @pytest.fixture
    def game_session(self, client):
        """Create a game session with choices."""
        # Start a new game
        response = client.post('/api/game/start', json={
            'character': {
                'name': 'TestHero',
                'race': 'Human',
                'class': 'Fighter'
            },
            'scenario': 'goblin_cave'
        })
        data = response.get_json()
        return data.get('session_id')
    
    def test_get_available_choices_invalid_session(self, client):
        """Test getting choices with invalid session."""
        response = client.get('/api/choices/available?session_id=invalid')
        assert response.status_code == 400
    
    def test_get_available_choices_with_session(self, client, game_session):
        """Test getting choices with valid session."""
        response = client.get(f'/api/choices/available?session_id={game_session}')
        data = response.get_json()
        
        assert data['success'] is True
        assert 'choices' in data
        # Note: player_context may not be present if no choice system
    
    def test_get_choice_history(self, client, game_session):
        """Test getting choice history."""
        response = client.get(f'/api/choices/history?session_id={game_session}')
        data = response.get_json()
        
        assert data['success'] is True
        assert 'history' in data
    
    def test_get_ending_status(self, client, game_session):
        """Test getting ending status."""
        response = client.get(f'/api/choices/ending?session_id={game_session}')
        data = response.get_json()
        
        assert data['success'] is True
        assert 'ending' in data
        # The key could be 'ending_points' or 'points' depending on implementation
    
    def test_select_choice_invalid_session(self, client):
        """Test selecting choice with invalid session."""
        response = client.post('/api/choices/select', json={
            'session_id': 'invalid',
            'choice_id': 'test',
            'option_index': 0
        })
        assert response.status_code == 400
    
    def test_select_choice_missing_params(self, client, game_session):
        """Test selecting choice without required params."""
        response = client.post('/api/choices/select', json={
            'session_id': game_session
        })
        assert response.status_code == 400


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestChoiceIntegration:
    """Integration tests for the choice system."""
    
    def test_full_choice_flow(self):
        """Test complete flow from scenario to choice selection."""
        # Create scenario with choices
        scenario = create_goblin_cave_scenario()
        manager = scenario.choice_manager
        
        # Simulate arriving at goblin camp
        triggered = manager.check_triggers(location_id='goblin_camp')
        assert len(triggered) >= 1
        
        prisoner_choice = next((c for c in triggered if c.id == "goblin_prisoner"), None)
        assert prisoner_choice is not None
        
        # Get the first option ID
        first_option_id = prisoner_choice.options[0].id
        
        # Make a choice
        consequence = manager.select_option("goblin_prisoner", first_option_id, None, {})
        
        # Verify result
        assert consequence is not None
        
        # Choice should now be recorded
        assert "goblin_prisoner" in manager.selected_choices
        
        # Mark choice as triggered
        prisoner_choice.is_triggered = True
        
        # Choice should not trigger again
        triggered_again = manager.check_triggers(location_id='goblin_camp')
        prisoner_again = [c for c in triggered_again if c.id == "goblin_prisoner"]
        assert len(prisoner_again) == 0
    
    def test_ending_points_accumulate(self):
        """Test that ending points accumulate across choices."""
        manager = ChoiceManager()
        choices = create_goblin_cave_choices()
        manager.register_choices(choices)
        
        # Get the prisoner choice and find the mercy option
        prisoner_choice = manager.get_choice("goblin_prisoner")
        mercy_option = None
        for opt in prisoner_choice.options:
            if 'mercy' in opt.consequence.ending_points:
                mercy_option = opt
                break
        
        if mercy_option:
            manager.select_option("goblin_prisoner", mercy_option.id, None, {})
            
            # Check ending points
            assert manager.ending_points.get('mercy', 0) >= 1
    
    def test_flags_are_stored(self):
        """Test that flag changes from choices are stored."""
        manager = ChoiceManager()
        choices = create_goblin_cave_choices()
        manager.register_choices(choices)
        
        # Get any choice and select an option
        first_choice = list(manager.choices.values())[0]
        first_option = first_choice.options[0]
        
        manager.select_option(first_choice.id, first_option.id, None, {})
        
        # If the consequence had flag changes, they should be in manager.flags
        for flag, value in first_option.consequence.flag_changes.items():
            assert manager.flags.get(flag) == value


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
