"""Test quest hook detection functions."""
import sys
sys.path.insert(0, 'src')

from api_server import detect_npc_talk
from npc import NPCManager, NPC


def test_npc_talk_detection():
    """Test that NPC talk is properly detected from player actions."""
    # Create a test NPC manager
    npc_manager = NPCManager()
    npc_manager.add_npc(NPC(id='bram', name='Farmer Bram', description='A worried farmer'))
    npc_manager.add_npc(NPC(id='barkeep', name='The Barkeep', description='A friendly tavern keeper'))
    
    # Should detect NPC talk
    assert 'bram' in detect_npc_talk('talk to bram', npc_manager)
    assert 'barkeep' in detect_npc_talk('speak with the barkeep', npc_manager)
    assert 'bram' in detect_npc_talk('greet farmer bram', npc_manager)
    assert 'barkeep' in detect_npc_talk('ask the barkeep about rumors', npc_manager)
    
    # Should NOT detect NPC talk
    assert detect_npc_talk('I attack the goblin', npc_manager) == []
    assert detect_npc_talk('look around', npc_manager) == []
    assert detect_npc_talk('inventory', npc_manager) == []
    
    print('✅ NPC talk detection tests passed!')


def test_quest_manager_hooks():
    """Test that quest manager hooks update objectives."""
    from quest import QuestManager, Quest, QuestObjective, ObjectiveType, QuestType
    
    qm = QuestManager()
    
    # Create a test quest with various objectives
    quest = Quest(
        id='test_quest',
        name='Test Quest',
        description='A test quest',
        giver_npc_id='test_npc',
        quest_type=QuestType.SIDE,
        objectives=[
            QuestObjective(
                id='talk_npc',
                description='Talk to Test NPC',
                objective_type=ObjectiveType.TALK_TO,
                target='test_npc'
            ),
            QuestObjective(
                id='find_item',
                description='Find Test Item',
                objective_type=ObjectiveType.FIND_ITEM,
                target='test_item'
            ),
            QuestObjective(
                id='reach_loc',
                description='Reach Test Location',
                objective_type=ObjectiveType.REACH_LOCATION,
                target='test_location'
            ),
            QuestObjective(
                id='kill_enemy',
                description='Kill Test Enemy',
                objective_type=ObjectiveType.KILL,
                target='test_enemy'
            )
        ]
    )
    
    qm.register_quest(quest)
    qm.accept_quest('test_quest')
    
    # Test NPC talk hook
    completed = qm.on_npc_talked('test_npc')
    assert len(completed) == 1
    quest_id, objective = completed[0]
    assert quest_id == 'test_quest'
    assert objective.id == 'talk_npc'
    
    # Test item acquire hook
    completed = qm.on_item_acquired('test_item')
    assert len(completed) == 1
    quest_id, objective = completed[0]
    assert quest_id == 'test_quest'
    assert objective.id == 'find_item'
    
    # Test location enter hook
    completed = qm.on_location_entered('test_location')
    assert len(completed) == 1
    quest_id, objective = completed[0]
    assert quest_id == 'test_quest'
    assert objective.id == 'reach_loc'
    
    # Test enemy kill hook
    completed = qm.on_enemy_killed('test_enemy')
    assert len(completed) == 1
    quest_id, objective = completed[0]
    assert quest_id == 'test_quest'
    assert objective.id == 'kill_enemy'
    
    # Verify all objectives are complete
    quest = qm.get_quest('test_quest')
    assert quest is not None
    for obj in quest.objectives:
        assert obj.completed, f'Objective {obj.id} should be completed'
    
    print('✅ Quest manager hooks tests passed!')


if __name__ == '__main__':
    test_npc_talk_detection()
    test_quest_manager_hooks()
    print('\n✅ All quest hook tests passed!')
