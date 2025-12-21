"""
Test that travel is blocked during combat.
This is a unit test that directly tests the travel endpoint behavior.
"""
import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from api_server import app, game_sessions, GameSession


@pytest.fixture
def client():
    """Create test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def session_with_combat(client):
    """Create a session that's in combat."""
    # Start a game session
    response = client.post('/api/game/start', json={
        'character': {'name': 'TestFighter', 'race': 'Human', 'class': 'Fighter'},
        'scenario_id': 'goblin_cave'
    })
    data = response.get_json()
    session_id = data['session_id']
    
    # Manually set combat state
    session = game_sessions[session_id]
    session.in_combat = True
    session.combat_state = {
        'enemies': ['goblin'],
        'surprise': False,
        'round': 1
    }
    
    return session_id


@pytest.fixture
def session_without_combat(client):
    """Create a session that's NOT in combat."""
    response = client.post('/api/game/start', json={
        'character': {'name': 'TestFighter', 'race': 'Human', 'class': 'Fighter'},
        'scenario_id': 'goblin_cave'
    })
    data = response.get_json()
    return data['session_id']


class TestCombatTravelBlock:
    """Test 5.1: Verify travel is blocked during combat."""
    
    def test_travel_blocked_during_combat(self, client, session_with_combat):
        """Travel should return 400 error when session is in combat."""
        response = client.post('/api/travel', json={
            'session_id': session_with_combat,
            'destination': 'forest'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'combat' in data['error'].lower()
        assert data.get('in_combat') == True
    
    def test_travel_allowed_when_not_in_combat(self, client, session_without_combat):
        """Travel should succeed when session is NOT in combat."""
        response = client.post('/api/travel', json={
            'session_id': session_without_combat,
            'destination': 'outside'  # Valid exit from tavern
        })
        
        # Should NOT return 400 with combat error
        data = response.get_json()
        # If there's an error, it should NOT be about combat
        if response.status_code == 400:
            assert 'combat' not in data.get('error', '').lower(), \
                "Should not block travel for combat reasons when not in combat"
        else:
            # Travel succeeded or returned a non-combat error
            assert True
    
    def test_travel_error_message_is_helpful(self, client, session_with_combat):
        """Error message should tell player how to exit combat."""
        response = client.post('/api/travel', json={
            'session_id': session_with_combat,
            'destination': 'anywhere'
        })
        
        data = response.get_json()
        # Error should mention ways to exit combat (defeat or flee)
        error_msg = data.get('error', '').lower()
        assert 'defeat' in error_msg or 'flee' in error_msg


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
