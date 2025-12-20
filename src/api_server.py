"""
AI RPG API Server
Flask-based REST API that bridges the Flutter frontend with the game engine.
Also serves the Flutter web app for same-origin requests.
"""

import os
import sys
import json
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from character import Character, CLASSES, RACES
from scenario import ScenarioManager
from npc import NPCManager
from quest import QuestManager
from combat import create_enemy, ENEMIES
from inventory import ITEMS, get_item
from save_system import SaveManager
from party import Party

# Import game functions
from game import (
    roll_skill_check, format_roll_result,
    parse_roll_request, parse_combat_request,
    SKILL_ABILITIES
)

load_dotenv()

# Path to Flutter web build
FRONTEND_BUILD_PATH = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'build', 'web')

app = Flask(__name__, static_folder=FRONTEND_BUILD_PATH, static_url_path='')
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)  # Enable CORS for all origins

# Add request logging
@app.before_request
def log_request():
    if request.path.startswith('/api'):
        print(f"📥 {request.method} {request.path} from {request.remote_addr}")

# In-memory game sessions (in production, use Redis or database)
game_sessions = {}


class GameSession:
    """Represents an active game session."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.character = None
        self.scenario = None
        self.npc_manager = None
        self.quest_manager = None
        self.party = None
        self.messages = []
        self.current_location = None
        self.in_combat = False
        self.combat_state = None
        self.created_at = datetime.now()
        self.dm_model = None
        
    def to_dict(self):
        """Convert session to dictionary for JSON response."""
        return {
            'session_id': self.session_id,
            'character': self.character.to_dict() if self.character else None,
            'current_location': self.current_location,
            'in_combat': self.in_combat,
            'messages': self.messages[-50:],  # Last 50 messages
            'quest_log': self._get_quest_log(),
        }
    
    def _get_quest_log(self):
        """Get active quests."""
        if not self.quest_manager:
            return []
        return [q.to_dict() for q in self.quest_manager.get_active_quests()]


def get_or_create_session(session_id: str = None) -> GameSession:
    """Get existing session or create new one."""
    if session_id and session_id in game_sessions:
        return game_sessions[session_id]
    
    new_id = session_id or str(uuid.uuid4())
    session = GameSession(new_id)
    game_sessions[new_id] = session
    return session


def init_dm_model(session: GameSession):
    """Initialize the Gemini AI model for DM responses."""
    if session.dm_model:
        return session.dm_model
    
    try:
        import google.generativeai as genai
        api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        
        if not api_key:
            return None
            
        genai.configure(api_key=api_key)
        
        generation_config = {
            "temperature": 0.9,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 1024,
        }
        
        session.dm_model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=generation_config,
        )
        return session.dm_model
    except Exception as e:
        print(f"Failed to initialize DM model: {e}")
        return None


def get_dm_response(session: GameSession, player_action: str) -> str:
    """Get AI DM response for player action."""
    model = init_dm_model(session)
    
    if not model:
        # Fallback responses when no API key
        return get_fallback_response(session, player_action)
    
    try:
        # Build context for DM
        context = build_dm_context(session, player_action)
        
        # Get response from Gemini
        response = model.generate_content(context)
        return response.text
    except Exception as e:
        print(f"DM response error: {e}")
        return get_fallback_response(session, player_action)


def build_dm_context(session: GameSession, player_action: str) -> str:
    """Build the prompt context for the DM."""
    char = session.character
    
    # Get recent conversation history
    recent_messages = session.messages[-10:] if session.messages else []
    history = "\n".join([
        f"{'Player' if m['type'] == 'player' else 'DM'}: {m['content']}"
        for m in recent_messages
    ])
    
    prompt = f"""You are a Dungeon Master for a D&D 5e text adventure game.

CHARACTER INFO:
- Name: {char.name if char else 'Unknown Hero'}
- Class: {char.character_class if char else 'Fighter'}
- Level: {char.level if char else 1}
- HP: {char.current_hp}/{char.max_hp if char else '10/10'}
- Location: {session.current_location or 'Village Square'}

RECENT CONVERSATION:
{history}

PLAYER ACTION: {player_action}

Respond as the Dungeon Master. Be descriptive and engaging. Keep responses to 2-3 paragraphs.

If a skill check is needed, include [ROLL: skill_name DC X] in your response.
If combat should start, include [COMBAT: enemy_type] in your response.
Available enemies: {', '.join(ENEMIES.keys())}

Respond naturally and immersively:"""

    return prompt


def get_fallback_response(session: GameSession, action: str) -> str:
    """Fallback responses when AI is not available."""
    action_lower = action.lower()
    
    if 'look' in action_lower or 'examine' in action_lower:
        return ("You survey your surroundings carefully. The area seems quiet for now, "
                "but you sense there may be adventure waiting just beyond your sight.\n\n"
                "What would you like to do next?")
    
    if 'attack' in action_lower or 'fight' in action_lower:
        return ("[COMBAT: goblin]\n\n"
                "A goblin emerges from the shadows, brandishing a rusty shortsword! "
                "It snarls at you menacingly. Roll for initiative!")
    
    if 'talk' in action_lower or 'speak' in action_lower:
        return ("You call out, but no one responds. Perhaps there's someone nearby "
                "you could seek out for conversation.\n\n"
                "What would you like to do?")
    
    if 'north' in action_lower or 'south' in action_lower or 'east' in action_lower or 'west' in action_lower:
        return (f"You head {action_lower.split()[-1]}. The path winds before you, "
                "leading to new possibilities. The air grows thick with anticipation.\n\n"
                "What do you do?")
    
    return ("You consider your options carefully. The adventure awaits, "
            "and every choice may lead to danger... or glory.\n\n"
            "What would you like to do?")


# =============================================================================
# API ROUTES
# =============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/game/start', methods=['POST'])
def start_game():
    """Start a new game session."""
    data = request.get_json() or {}
    
    session_id = data.get('session_id')
    session = get_or_create_session(session_id)
    
    # Create character
    char_data = data.get('character', {})
    
    # Use provided data or defaults
    name = char_data.get('name', 'Hero')
    race = char_data.get('race', 'Human')
    char_class = char_data.get('class', 'Fighter')
    
    # Validate race and class
    if race not in RACES:
        race = 'Human'
    if char_class not in CLASSES:
        char_class = 'Fighter'
    
    # Create character with default stats
    session.character = Character(
        name=name,
        race=race,
        character_class=char_class,
    )
    
    # Initialize game systems
    session.scenario = ScenarioManager()
    session.npc_manager = NPCManager()
    session.quest_manager = QuestManager()
    session.party = Party(session.character)
    session.current_location = 'Village Square'
    
    # Welcome message
    welcome = (
        f"Welcome, {name} the {race} {char_class}!\n\n"
        "You stand in the village square of Willowbrook. The morning sun casts long shadows "
        "across the cobblestones. To the west, smoke rises from The Rusty Dragon tavern. "
        "To the east, you hear the rhythmic clanging of the blacksmith's hammer.\n\n"
        "Rumors speak of goblins that have made their home in caves to the north, "
        "terrorizing travelers on the forest road.\n\n"
        "What would you like to do?"
    )
    
    session.messages.append({
        'type': 'dm',
        'content': welcome,
        'timestamp': datetime.now().isoformat()
    })
    
    return jsonify({
        'success': True,
        'session_id': session.session_id,
        'message': welcome,
        'game_state': session.to_dict()
    })


@app.route('/api/game/action', methods=['POST'])
def game_action():
    """Process a player action."""
    data = request.get_json() or {}
    
    session_id = data.get('session_id')
    action = data.get('action', '').strip()
    
    if not session_id or session_id not in game_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    if not action:
        return jsonify({'error': 'No action provided'}), 400
    
    session = game_sessions[session_id]
    
    # Record player action
    session.messages.append({
        'type': 'player',
        'content': action,
        'timestamp': datetime.now().isoformat()
    })
    
    # Get DM response
    dm_response = get_dm_response(session, action)
    
    # Check for skill check request
    skill, dc = parse_roll_request(dm_response)
    roll_result = None
    
    if skill and dc and session.character:
        result = roll_skill_check(session.character, skill, dc)
        roll_result = {
            'skill': result['skill'],
            'roll': result['roll'],
            'modifier': result['modifier'],
            'total': result['total'],
            'dc': dc,
            'success': result['success'],
            'formatted': format_roll_result(result)
        }
        
        # Add roll result to response
        dm_response += f"\n\n{format_roll_result(result)}"
    
    # Check for combat request
    enemies, surprise = parse_combat_request(dm_response)
    combat_started = False
    
    if enemies:
        combat_started = True
        session.in_combat = True
        session.combat_state = {
            'enemies': enemies,
            'surprise': surprise,
            'round': 1
        }
    
    # Record DM response
    session.messages.append({
        'type': 'dm',
        'content': dm_response,
        'timestamp': datetime.now().isoformat(),
        'roll_result': roll_result,
        'combat_started': combat_started
    })
    
    return jsonify({
        'success': True,
        'message': dm_response,
        'roll_result': roll_result,
        'combat_started': combat_started,
        'game_state': session.to_dict()
    })


@app.route('/api/game/state', methods=['GET'])
def get_game_state():
    """Get current game state."""
    session_id = request.args.get('session_id')
    
    if not session_id or session_id not in game_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    session = game_sessions[session_id]
    return jsonify({
        'success': True,
        'game_state': session.to_dict()
    })


@app.route('/api/game/roll', methods=['POST'])
def roll_dice_endpoint():
    """Roll dice manually."""
    data = request.get_json() or {}
    
    session_id = data.get('session_id')
    dice = data.get('dice', 'd20')
    modifier = data.get('modifier', 0)
    
    # Parse dice notation (e.g., "2d6", "d20", "1d8+2")
    import re
    match = re.match(r'(\d*)d(\d+)', dice.lower())
    
    if not match:
        return jsonify({'error': 'Invalid dice notation'}), 400
    
    num_dice = int(match.group(1)) if match.group(1) else 1
    die_size = int(match.group(2))
    
    import random
    rolls = [random.randint(1, die_size) for _ in range(num_dice)]
    total = sum(rolls) + modifier
    
    result = {
        'dice': dice,
        'rolls': rolls,
        'modifier': modifier,
        'total': total,
        'formatted': f"🎲 {dice}: {rolls} + {modifier} = {total}" if modifier else f"🎲 {dice}: {rolls} = {total}"
    }
    
    # Record in session if provided
    if session_id and session_id in game_sessions:
        session = game_sessions[session_id]
        session.messages.append({
            'type': 'dice',
            'content': result['formatted'],
            'timestamp': datetime.now().isoformat(),
            'roll_data': result
        })
    
    return jsonify({
        'success': True,
        'result': result
    })


@app.route('/api/game/character', methods=['GET'])
def get_character():
    """Get character details."""
    session_id = request.args.get('session_id')
    
    if not session_id or session_id not in game_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    session = game_sessions[session_id]
    
    if not session.character:
        return jsonify({'error': 'No character in session'}), 400
    
    return jsonify({
        'success': True,
        'character': session.character.to_dict()
    })


@app.route('/api/game/save', methods=['POST'])
def save_game():
    """Save the current game."""
    data = request.get_json() or {}
    session_id = data.get('session_id')
    save_name = data.get('name', 'quicksave')
    
    if not session_id or session_id not in game_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    session = game_sessions[session_id]
    
    # Create save data
    save_data = {
        'session_id': session.session_id,
        'character': session.character.to_dict() if session.character else None,
        'messages': session.messages,
        'current_location': session.current_location,
        'in_combat': session.in_combat,
        'saved_at': datetime.now().isoformat()
    }
    
    # Save to file
    saves_dir = os.path.join(os.path.dirname(__file__), '..', 'saves')
    os.makedirs(saves_dir, exist_ok=True)
    
    save_path = os.path.join(saves_dir, f"{save_name}.json")
    with open(save_path, 'w') as f:
        json.dump(save_data, f, indent=2)
    
    return jsonify({
        'success': True,
        'message': f'Game saved as {save_name}',
        'save_path': save_path
    })


@app.route('/api/game/load', methods=['POST'])
def load_game():
    """Load a saved game."""
    data = request.get_json() or {}
    save_name = data.get('name', 'quicksave')
    
    saves_dir = os.path.join(os.path.dirname(__file__), '..', 'saves')
    save_path = os.path.join(saves_dir, f"{save_name}.json")
    
    if not os.path.exists(save_path):
        return jsonify({'error': 'Save not found'}), 404
    
    with open(save_path, 'r') as f:
        save_data = json.load(f)
    
    # Restore session
    session_id = save_data.get('session_id', str(uuid.uuid4()))
    session = get_or_create_session(session_id)
    
    # Restore character
    if save_data.get('character'):
        session.character = Character.from_dict(save_data['character'])
    
    session.messages = save_data.get('messages', [])
    session.current_location = save_data.get('current_location', 'Village Square')
    session.in_combat = save_data.get('in_combat', False)
    
    return jsonify({
        'success': True,
        'message': f'Game loaded from {save_name}',
        'session_id': session.session_id,
        'game_state': session.to_dict()
    })


@app.route('/api/game/saves', methods=['GET'])
def list_saves():
    """List available saves."""
    saves_dir = os.path.join(os.path.dirname(__file__), '..', 'saves')
    
    if not os.path.exists(saves_dir):
        return jsonify({'success': True, 'saves': []})
    
    saves = []
    for filename in os.listdir(saves_dir):
        if filename.endswith('.json'):
            save_path = os.path.join(saves_dir, filename)
            try:
                with open(save_path, 'r') as f:
                    save_data = json.load(f)
                saves.append({
                    'name': filename[:-5],  # Remove .json
                    'saved_at': save_data.get('saved_at'),
                    'character_name': save_data.get('character', {}).get('name', 'Unknown')
                })
            except:
                pass
    
    return jsonify({
        'success': True,
        'saves': saves
    })


@app.route('/api/classes', methods=['GET'])
def get_classes():
    """Get available character classes."""
    return jsonify({
        'success': True,
        'classes': list(CLASSES.keys())
    })


@app.route('/api/races', methods=['GET'])
def get_races():
    """Get available character races."""
    return jsonify({
        'success': True,
        'races': list(RACES.keys())
    })


# =============================================================================
# SERVE FLUTTER WEB APP
# =============================================================================

@app.route('/')
def serve_index():
    """Serve the Flutter web app index."""
    return send_from_directory(FRONTEND_BUILD_PATH, 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    """Serve Flutter web app static files."""
    # Don't serve API routes as static files
    if path.startswith('api/'):
        return jsonify({'error': 'Not found'}), 404
    
    # Try to serve the file, fallback to index.html for SPA routing
    file_path = os.path.join(FRONTEND_BUILD_PATH, path)
    
    print(f"📂 Request for static file: {path}")
    print(f"   Looking in: {file_path}")
    print(f"   Exists: {os.path.isfile(file_path)}")
    
    if os.path.isfile(file_path):
        # Explicitly set MIME type for JS files to avoid Windows registry issues
        if path.endswith('.js'):
            return send_from_directory(FRONTEND_BUILD_PATH, path, mimetype='application/javascript')
        return send_from_directory(FRONTEND_BUILD_PATH, path)
    else:
        print(f"   ⚠️ File not found, serving index.html")
        return send_from_directory(FRONTEND_BUILD_PATH, 'index.html')


if __name__ == '__main__':
    port = int(os.getenv('API_PORT', 5000))
    debug = os.getenv('DEBUG', 'true').lower() == 'true'
    
    print(f"🎲 AI RPG API Server starting on http://localhost:{port}")
    print(f"   Debug mode: {debug}")
    print(f"   API Key configured: {'Yes' if os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY') else 'No'}")
    print(f"   Frontend: {FRONTEND_BUILD_PATH}")
    print(f"\n   🌐 Open http://localhost:{port} in your browser to play!")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
