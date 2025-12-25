"""
AI RPG API Server
Flask-based REST API that bridges the Flutter frontend with the game engine.
Also serves the Flutter web app for same-origin requests.
"""

import os
import sys
import json
import uuid
import random
import threading
import time
import logging
from dataclasses import asdict
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from dotenv import load_dotenv

# Load .env from project root (parent of src/) - do this early for DEBUG setting
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(PROJECT_ROOT, '.env')
load_dotenv(ENV_PATH)

# Configure verbose logging
VERBOSE_LOGGING = os.getenv('VERBOSE_LOGGING', 'true').lower() == 'true'
LOG_TO_FILE = os.getenv('LOG_TO_FILE', 'true').lower() == 'true'
LOG_FILE_PATH = os.path.join(PROJECT_ROOT, 'notes.log')

# Initialize log file with session marker
if LOG_TO_FILE:
    with open(LOG_FILE_PATH, 'a', encoding='utf-8') as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"🚀 Backend Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"{'='*60}\n")

def game_log(category: str, message: str, data: dict = None):
    """Log game events in a verbose, readable format. Outputs to console and notes.log."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    icon_map = {
        'ACTION': '🎮',
        'DM': '🎲',
        'PARSE': '🔍',
        'ROLL': '🎯',
        'COMBAT': '⚔️',
        'ITEM': '📦',
        'GOLD': '💰',
        'XP': '⭐',
        'QUEST': '📜',
        'RECRUIT': '👥',
        'PARTY': '🛡️',
        'LOCATION': '🗺️',
        'NPC': '🗣️',
        'SAVE': '💾',
        'ERROR': '❌',
        'API': '📡',
        'SESSION': '🔑',
    }
    icon = icon_map.get(category.upper(), '📌')
    
    log_line = f"[{timestamp}] {icon} [{category}] {message}"
    if data:
        data_str = json.dumps(data, indent=2, default=str)
        log_line += f"\n    ↳ {data_str}"
    
    # Print to console
    print(log_line)
    
    # Also write to notes.log
    if LOG_TO_FILE:
        try:
            with open(LOG_FILE_PATH, 'a', encoding='utf-8') as f:
                f.write(log_line + '\n')
        except Exception as e:
            print(f"Warning: Could not write to log file: {e}")

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from character import Character, CLASSES, RACES
from scenario import ScenarioManager, LocationManager, Location, create_goblin_cave_quests, ChoiceManager, Choice, ChoiceType
from npc import NPCManager
from quest import QuestManager
from combat import (
    create_enemy, ENEMIES, Enemy,
    roll_attack, roll_attack_with_advantage, roll_damage, enemy_attack,
    roll_initiative, format_attack_result, format_damage_result,
    get_enemy_xp, get_enemy_loot_for_class
)
from inventory import ITEMS, get_item, add_item_to_inventory, remove_item_from_inventory, ItemType
from save_system import SaveManager
from party import Party

# Import from shared DM engine (single source of truth)
from dm_engine import (
    DM_SYSTEM_PROMPT,
    parse_roll_request, parse_combat_request,
    parse_item_rewards, parse_gold_rewards, parse_xp_rewards, parse_buy_transactions,
    parse_gold_costs, parse_recruit_tags,
    roll_skill_check, format_roll_result,
    build_full_dm_context, apply_rewards,
    SKILL_ABILITIES
)
import re


def detect_npc_talk(action: str, npc_manager) -> list:
    """
    Detect if a player action involves talking to an NPC.
    
    Returns:
        List of NPC IDs that were talked to
    """
    if not npc_manager:
        return []
    
    talked_to = []
    action_lower = action.lower()
    
    # Common talk patterns
    talk_patterns = [
        r"talk\s+(?:to|with)\s+(\w+)",
        r"speak\s+(?:to|with)\s+(\w+)",
        r"greet\s+(\w+)",
        r"ask\s+(\w+)",
        r"approach\s+(\w+)",
        r"hello\s+(\w+)",
    ]
    
    for pattern in talk_patterns:
        matches = re.findall(pattern, action_lower)
        for name in matches:
            # Check if this name matches any NPC
            for npc in npc_manager.get_all_npcs():
                if name.lower() in npc.name.lower() or name.lower() == npc.id.lower():
                    if npc.id not in talked_to:
                        talked_to.append(npc.id)
    
    return talked_to


def detect_quest_acceptance(player_action: str, dm_response: str, quest_manager) -> list:
    """
    Detect if the player accepted a quest based on their action and the DM response.
    
    Triggers when:
    1. Player says accept-like words (accept, yes, i'll help, agree, etc.)
    2. DM response mentions quest-related keywords (thank you, grateful, quest, save, etc.)
    
    Returns:
        List of quest IDs that were accepted
    """
    if not quest_manager:
        return []
    
    accepted_quests = []
    action_lower = player_action.lower()
    response_lower = dm_response.lower()
    
    # Player acceptance patterns
    accept_patterns = [
        r"\byes\b", r"\baccept\b", r"\bi('ll| will) help\b", r"\bagree\b",
        r"\bcount me in\b", r"\bi'm in\b", r"\blet's do it\b", r"\bi'll save\b",
        r"\blet me help\b", r"\bof course\b", r"\bvery well\b"
    ]
    
    player_accepted = any(re.search(pat, action_lower) for pat in accept_patterns)
    
    if not player_accepted:
        return []
    
    # Check available (not yet accepted) quests and match by NPC/context
    for quest_id, quest in quest_manager.available_quests.items():
        # Check if DM response references the quest giver or quest content
        giver = quest.giver_npc_id.lower() if quest.giver_npc_id else ""
        
        # Match conditions (any of these trigger acceptance):
        # 1. DM mentions quest giver name
        # 2. DM response contains gratitude/acceptance words
        # 3. Quest name or key words from description mentioned
        dm_confirms = any([
            giver and giver in response_lower,
            any(word in response_lower for word in ["thank you", "grateful", "bless you", "knew someone"]),
            quest.name.lower() in response_lower,
            # Specific quest matching
            quest_id == "rescue_lily" and any(w in response_lower for w in ["lily", "daughter", "save her"]),
            quest_id == "clear_the_path" and any(w in response_lower for w in ["road", "path", "wolves", "safer"]),
        ])
        
        if dm_confirms:
            result = quest_manager.accept_quest(quest_id)
            if result:
                accepted_quests.append(quest_id)
    
    return accepted_quests
    
    return talked_to


def get_skill_hint(player_action: str) -> str:
    """
    Add skill check hints based on player action keywords.
    Helps the AI know when to request skill checks.
    """
    input_lower = player_action.lower()
    
    # Perception/Investigation triggers
    perception_words = ["look", "search", "examine", "inspect", "scan", "check", "investigate", 
                       "what do i see", "look around", "look for", "notice", "observe"]
    if any(word in input_lower for word in perception_words):
        return "\n[HINT: This is an exploration action. Consider calling for a Perception or Investigation check (DC 10-15) before revealing hidden details.]"
    
    # Stealth triggers
    stealth_words = ["sneak", "hide", "quietly", "stealthily", "creep", "silently", "lurk"]
    if any(word in input_lower for word in stealth_words):
        return "\n[HINT: This is a stealth action. Call for a Stealth check (DC 10-15) to determine success.]"
    
    # Social triggers - Persuasion
    persuade_words = ["convince", "persuade", "ask for", "request", "plead", "negotiate", "bargain", "deposit", "advance", "upfront"]
    if any(word in input_lower for word in persuade_words):
        return "\n[HINT: This is a social action. Consider calling for a Persuasion check (DC 10-15).]"
    
    # Social triggers - Intimidation
    intimidate_words = ["threaten", "intimidate", "demand", "scare", "menace", "warn"]
    if any(word in input_lower for word in intimidate_words):
        return "\n[HINT: This is an intimidation attempt. Consider calling for an Intimidation check (DC 12-18).]"
    
    # Social triggers - Deception
    deception_words = ["lie", "bluff", "deceive", "trick", "fool", "pretend", "fake", "disguise"]
    if any(word in input_lower for word in deception_words):
        return "\n[HINT: This is a deception attempt. Consider calling for a Deception check (DC 12-18).]"
    
    # Social triggers - Insight (reading people)
    insight_words = ["read", "sense motive", "tell if", "lying", "trust", "believe", "suspicious"]
    if any(word in input_lower for word in insight_words):
        return "\n[HINT: The player is trying to read someone. Consider calling for an Insight check (DC 10-15).]"
    
    # Physical triggers
    physical_words = ["climb", "jump", "break", "force", "push", "lift", "swim", "run"]
    if any(word in input_lower for word in physical_words):
        return "\n[HINT: This is a physical action. Consider calling for an Athletics check (DC 10-15).]"
    
    return ""


app = Flask(__name__)
app.json.ensure_ascii = False  # Allow non-ASCII (emojis) in JSON
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)  # Enable CORS for all origins

# Add request logging
@app.before_request
def log_request():
    if request.path.startswith('/api') and VERBOSE_LOGGING:
        # Get session ID from header or query param
        session_id = request.headers.get('X-Session-ID') or request.args.get('session_id', 'none')
        short_sid = session_id[:8] if session_id and session_id != 'none' else 'none'
        
        # Log with method, path, and session
        game_log('API', f"{request.method} {request.path}", {
            'session': short_sid,
            'from': request.remote_addr,
            'query_params': dict(request.args) if request.args else None,
            'has_body': request.content_length and request.content_length > 0
        })

# In-memory game sessions (in production, use Redis or database)
game_sessions = {}
session_lock = threading.Lock()  # Thread-safe session access

# Session timeout configuration
SESSION_TIMEOUT_MINUTES = 60  # Sessions expire after 1 hour of inactivity
SESSION_CLEANUP_INTERVAL_SECONDS = 300  # Check for expired sessions every 5 minutes


def cleanup_expired_sessions():
    """Background thread that removes expired sessions."""
    while True:
        time.sleep(SESSION_CLEANUP_INTERVAL_SECONDS)
        now = datetime.now()
        expired_sessions = []
        
        with session_lock:
            for session_id, session in game_sessions.items():
                if hasattr(session, 'last_activity'):
                    inactive_time = now - session.last_activity
                    if inactive_time > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
                        expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                del game_sessions[session_id]
                print(f"🧹 Session {session_id[:8]}... expired and cleaned up")
        
        if expired_sessions:
            print(f"🧹 Cleaned up {len(expired_sessions)} expired session(s). Active sessions: {len(game_sessions)}")


# Start background cleanup thread
cleanup_thread = threading.Thread(target=cleanup_expired_sessions, daemon=True)
cleanup_thread.start()


class GameSession:
    """Represents an active game session."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.character = None
        self.scenario = None
        self.npc_manager = None
        self.quest_manager = None
        self.location_manager = None
        self.choice_manager = None  # Phase 3.4: Moral choices
        self.party = None
        self.messages = []
        self.current_location = None
        self.current_location_id = None
        self.player_flags = {}  # Phase 3.4: Player flags for choice triggers
        self.in_combat = False
        self.combat_state = None
        self.created_at = datetime.now()
        self.last_activity = datetime.now()  # Track last activity for session cleanup
        self.dm_model = None
        self.dm_chat = None  # Chat session for stateful conversation
    
    def touch(self):
        """Update last_activity timestamp to prevent session expiration."""
        self.last_activity = datetime.now()
    
    def _serialize_character(self):
        """Serialize character with proper enum handling for inventory items."""
        if not self.character:
            return None
        
        char_dict = asdict(self.character)
        
        # Convert inventory items - handle enums
        serialized_inventory = []
        for item in char_dict.get('inventory', []):
            if isinstance(item, dict):
                # Convert enum values to strings
                if 'item_type' in item and hasattr(item['item_type'], 'value'):
                    item['item_type'] = item['item_type'].value
                if 'rarity' in item and hasattr(item['rarity'], 'value'):
                    item['rarity'] = item['rarity'].value
                serialized_inventory.append(item)
            else:
                # Item object - convert to dict with string enums
                item_dict = {
                    'name': item.name,
                    'item_type': item.item_type.value if hasattr(item.item_type, 'value') else str(item.item_type),
                    'description': item.description,
                    'rarity': item.rarity.value if hasattr(item.rarity, 'value') else str(item.rarity),
                    'value': item.value,
                    'stackable': item.stackable,
                    'quantity': item.quantity,
                    'damage_dice': item.damage_dice,
                    'finesse': item.finesse,
                    'ac_bonus': item.ac_bonus,
                    'heal_amount': item.heal_amount,
                    'effect': item.effect,
                }
                serialized_inventory.append(item_dict)
        
        char_dict['inventory'] = serialized_inventory
        return char_dict
        
    def to_dict(self):
        """Convert session to dictionary for JSON response."""
        return {
            'session_id': self.session_id,
            'character': self._serialize_character(),
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
    """Get existing session or create new one. Updates last_activity timestamp."""
    if session_id and session_id in game_sessions:
        session = game_sessions[session_id]
        session.touch()  # Update activity timestamp
        return session
    
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
            print(f"   ❌ No API key found! Checked GEMINI_API_KEY and GOOGLE_API_KEY")
            print(f"   📁 .env path: {ENV_PATH}")
            print(f"   📁 .env exists: {os.path.exists(ENV_PATH)}")
            return None
            
        genai.configure(api_key=api_key)
        
        generation_config = {
            "temperature": 0.9,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 2048,  # Increased for richer narration
        }
        
        # Read model from .env, fallback to gemini-2.0-flash
        model_name = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')
        
        session.dm_model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config,
        )
        print(f"   ✅ Using AI model: {model_name}")
        return session.dm_model
    except Exception as e:
        print(f"   ❌ Failed to initialize DM model: {e}")
        import traceback
        traceback.print_exc()
        return None


def init_dm_chat(session: GameSession):
    """Initialize or get the chat session for stateful conversation."""
    # If we already have a chat, return it
    if session.dm_chat:
        return session.dm_chat
    
    model = init_dm_model(session)
    if not model:
        return None
    
    # Build initial system context
    system_context = build_dm_context(session, "[GAME START]")
    
    # Start chat with system context as the first message
    session.dm_chat = model.start_chat(history=[
        {"role": "user", "parts": [system_context]},
        {"role": "model", "parts": ["I understand. I am ready to serve as your Dungeon Master. I will follow all the rules and constraints provided. Let the adventure begin!"]}
    ])
    
    print(f"   💬 Chat session initialized")
    return session.dm_chat


def refresh_chat_context(session: GameSession):
    """Refresh the chat session with updated game state context."""
    if not session.dm_chat:
        return init_dm_chat(session)
    
    # Build context update message (without full history since chat tracks it)
    from dm_engine import (
        build_character_context,
        build_scenario_context,
        build_location_context,
        build_npc_context,
        build_quest_context
    )
    
    context_update = f"""[CONTEXT UPDATE - Current game state:]
{build_character_context(session.character)}
Current Location: {session.current_location or 'Unknown'}
{build_scenario_context(session.scenario)}{build_location_context(session.location_manager)}{build_npc_context(session.npc_manager)}{build_quest_context(session.quest_manager)}"""
    
    return context_update


def get_dm_response(session: GameSession, player_action: str, is_opening: bool = False, max_retries: int = 3) -> str:
    """Get AI DM response for player action (non-streaming) using chat session."""
    import time
    
    chat = init_dm_chat(session)
    
    if not chat:
        # Fallback responses when no API key
        return get_fallback_response(session, player_action, is_opening)
    
    # Build the message with context refresh + action + skill hints
    context_refresh = refresh_chat_context(session)
    skill_hint = get_skill_hint(player_action)
    full_message = f"{context_refresh}\n\nPlayer action: {player_action}{skill_hint}"
    
    for attempt in range(max_retries):
        try:
            response = chat.send_message(full_message)
            if response.text:
                return response.text
            
            # Empty response - retry if possible
            if attempt < max_retries - 1:
                wait_time = 0.5 * (2 ** attempt)
                print(f"⚠️ Empty response (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                print(f"Warning: Gemini returned empty response after {max_retries} attempts")
                return "The Dungeon Master pauses thoughtfully... What would you like to do?"
                
        except Exception as e:
            error_msg = str(e)
            is_retryable = (
                "response.text" in error_msg or 
                "finish_reason" in error_msg or
                "rate limit" in error_msg.lower()
            )
            
            if is_retryable and attempt < max_retries - 1:
                wait_time = 1.0 * (2 ** attempt)
                print(f"⚠️ Retryable error (attempt {attempt + 1}/{max_retries}): {error_msg[:100]}")
                time.sleep(wait_time)
                continue
            
            print(f"❌ DM response error after {attempt + 1} attempts: {e}")
            session.dm_chat = None  # Reset chat for next attempt
            return get_fallback_response(session, player_action, is_opening)
    
    return get_fallback_response(session, player_action, is_opening)


def stream_dm_response(session: GameSession, player_action: str, max_retries: int = 3, is_roll_continuation: bool = False):
    """Generator that yields streaming DM response chunks using chat session.
    
    Args:
        session: The game session
        player_action: The player's action or roll result message
        max_retries: Number of retry attempts for API errors
        is_roll_continuation: If True, this is a continuation after a dice roll
    """
    import time
    
    chat = init_dm_chat(session)
    
    if not chat:
        yield get_fallback_response(session, player_action, False)
        return
    
    # Build the message with context refresh + action + skill hints
    # Only include context updates periodically or when state changes significantly
    context_refresh = refresh_chat_context(session)
    
    if is_roll_continuation:
        # For roll continuations, don't add skill hints (we already have the result)
        full_message = f"{context_refresh}\n\n{player_action}"
    else:
        skill_hint = get_skill_hint(player_action)
        full_message = f"{context_refresh}\n\nPlayer action: {player_action}{skill_hint}"
    
    for attempt in range(max_retries):
        try:
            # Use chat.send_message for stateful conversation (like terminal version)
            response = chat.send_message(full_message, stream=True)
            
            yielded_any = False
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    yielded_any = True
            
            # Handle empty response - retry if we have attempts left
            if not yielded_any:
                if attempt < max_retries - 1:
                    wait_time = 0.5 * (2 ** attempt)  # 0.5s, 1s, 2s
                    print(f"⚠️ Empty response (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"Warning: Gemini returned empty response after {max_retries} attempts")
                    print(f"  Action: {player_action[:50]}...")
                    yield "The Dungeon Master pauses thoughtfully... What would you like to do?"
            
            return  # Success - exit the retry loop
                
        except Exception as e:
            error_msg = str(e)
            
            # Check if this is a retryable error
            is_retryable = (
                "response.text" in error_msg or 
                "finish_reason" in error_msg or
                "rate limit" in error_msg.lower() or
                "503" in error_msg or
                "temporarily" in error_msg.lower()
            )
            
            if is_retryable and attempt < max_retries - 1:
                wait_time = 1.0 * (2 ** attempt)  # 1s, 2s, 4s
                print(f"⚠️ Retryable error (attempt {attempt + 1}/{max_retries}): {error_msg[:100]}")
                print(f"  Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
            
            # Final failure - reset chat session in case it's corrupted
            print(f"❌ Streaming DM error after {attempt + 1} attempts: {error_msg}")
            print(f"  Action was: {player_action[:100]}...")
            session.dm_chat = None  # Reset chat for next attempt
            
            if "response.text" in error_msg or "finish_reason" in error_msg:
                yield ("*The Dungeon Master's response was interrupted.*\n\n"
                       "Please try your action again, or try a different approach.")
            else:
                yield get_fallback_response(session, player_action, False)
            return


def build_dm_context(session: GameSession, player_action: str) -> str:
    """Build the prompt context for the DM using the shared dm_engine."""
    return build_full_dm_context(
        character=session.character,
        scenario_manager=session.scenario,
        location_manager=session.location_manager,
        npc_manager=session.npc_manager,
        quest_manager=session.quest_manager,
        current_location=session.current_location,
        conversation_history=session.messages,
        player_action=player_action,
        available_enemies=list(ENEMIES.keys())
    )


def get_fallback_response(session: GameSession, action: str, is_opening: bool = False) -> str:
    """Fallback responses when AI is not available - returns error message."""
    return (
        "⚠️ **AI Dungeon Master Unavailable**\n\n"
        "The AI model could not be initialized. Please check:\n"
        "1. GOOGLE_API_KEY is set in .env file\n"
        "2. The API key is valid\n"
        "3. The GEMINI_MODEL setting is correct\n\n"
        "You can still type actions, but responses will be limited until the AI is available."
    )


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
    name = char_data.get('name', '')
    race = char_data.get('race', 'Human')
    char_class = char_data.get('class', 'Fighter')
    
    # Validate character name
    MAX_NAME_LENGTH = 50
    if not name or not name.strip():
        return jsonify({'error': 'Character name is required'}), 400
    name = name.strip()
    if len(name) > MAX_NAME_LENGTH:
        return jsonify({'error': f'Character name too long (max {MAX_NAME_LENGTH} characters)'}), 400
    
    # Validate race and class
    if race not in RACES:
        race = 'Human'
    if char_class not in CLASSES:
        char_class = 'Fighter'
    
    # Roll stats using 4d6 drop lowest (like terminal version)
    session.character = Character(
        name=name,
        race=race,
        char_class=char_class,
        strength=Character.roll_stat(),
        dexterity=Character.roll_stat(),
        constitution=Character.roll_stat(),
        intelligence=Character.roll_stat(),
        wisdom=Character.roll_stat(),
        charisma=Character.roll_stat(),
    )
    
    # Add starting equipment and gold (like terminal version)
    session.character._add_starting_equipment()
    
    # Initialize game systems
    session.scenario = ScenarioManager()
    session.npc_manager = NPCManager()
    session.quest_manager = QuestManager()
    session.party = Party()
    session.location_manager = LocationManager()
    
    # Get scenario selection
    scenario_id = data.get('scenario_id')
    opening_narration = None
    
    if scenario_id:
        try:
            # Start the selected scenario
            first_scene = session.scenario.start_scenario(scenario_id)
            scenario = session.scenario.active_scenario
            
            # Use scenario's NPC manager if available (contains scenario NPCs!)
            if hasattr(scenario, 'npc_manager') and scenario.npc_manager:
                session.npc_manager = scenario.npc_manager
            
            # Use scenario's location manager if available
            if hasattr(scenario, 'location_manager') and scenario.location_manager:
                session.location_manager = scenario.location_manager
            
            # Use scenario's choice manager if available (Phase 3.4)
            if hasattr(scenario, 'choice_manager') and scenario.choice_manager:
                session.choice_manager = scenario.choice_manager
            
            # Initialize quests for the scenario
            if scenario_id == 'goblin_cave':
                create_goblin_cave_quests(session.quest_manager)
                # Quests are now REGISTERED but NOT ACCEPTED
                # They will be accepted when the player agrees to help (via [QUEST_ACCEPT:] tag or player says "accept"/"yes")
            
            # Initialize location manager with scenario locations (fallback for old scenarios)
            if hasattr(scenario, 'locations') and scenario.locations:
                for loc in scenario.locations:
                    session.location_manager.add_location(loc)
                    if loc.id not in session.location_manager.available_location_ids:
                        session.location_manager.available_location_ids.append(loc.id)
                
                # Set current location
                if scenario.locations:
                    start_loc = scenario.locations[0]
                    session.location_manager.set_current_location(start_loc.id)
                    session.current_location = start_loc.name
                    session.current_location_id = start_loc.id
            else:
                session.current_location = first_scene.name if first_scene else scenario.name
            
            # Build NPC names for opening prompt
            npc_names = []
            if session.npc_manager:
                for npc in session.npc_manager.get_all_npcs():
                    if hasattr(npc, 'location_id') and npc.location_id == session.current_location_id:
                        npc_names.append(f"{npc.name} ({npc.description[:50]}...)")
            
            npc_hint = ""
            if npc_names:
                npc_hint = f"\n\nNPCs PRESENT (use ONLY these names - never invent others!):\n- " + "\n- ".join(npc_names)
            
            # Generate AI opening narration (like terminal version)
            opening_prompt = f"""Begin the adventure for {name}, a {race} {char_class}.

SCENARIO: {scenario.name}
HOOK: {scenario.hook}

STARTING LOCATION: {first_scene.name if first_scene else session.current_location}
SETTING: {first_scene.setting if first_scene else 'A mysterious location awaits.'}{npc_hint}

You are the Dungeon Master. Set the scene dramatically and atmospherically. 
- Describe the immediate surroundings with vivid sensory details
- Create tension or intrigue appropriate to the scenario
- If introducing NPCs, use ONLY the names listed above - NEVER invent new names!
- Give the player a clear sense of what they see, hear, and feel
- End with something that invites player action

Keep it to 2-3 paragraphs. Be immersive and engaging."""

            # Get AI narration
            opening_narration = get_dm_response(session, opening_prompt, is_opening=True)
            
        except ValueError:
            # Scenario not found, use default
            scenario_id = None
    
    if not scenario_id:
        # Default welcome without scenario - still use AI
        session.current_location = 'Village Square'
        
        opening_prompt = f"""Begin a new adventure for {name}, a {race} {char_class}.

LOCATION: Village Square of Willowbrook

You are the Dungeon Master starting a free adventure. Set the scene:
- Describe the village square with vivid sensory details (sights, sounds, smells)
- Mention nearby points of interest (tavern to the west, blacksmith to the east)
- Create a sense of possibility and adventure
- Hint at rumors of danger (goblin caves to the north)
- End with something that invites the player to act

Keep it to 2-3 paragraphs. Be immersive and atmospheric."""

        opening_narration = get_dm_response(session, opening_prompt, is_opening=True)
    
    # Fallback if AI fails
    if not opening_narration:
        if scenario_id and session.scenario.active_scenario:
            scenario = session.scenario.active_scenario
            opening_narration = (
                f"🏰 **{scenario.name}**\n\n"
                f"{scenario.hook}\n\n"
                f"📍 You find yourself at: **{session.current_location}**\n\n"
                "What would you like to do?"
            )
        else:
            opening_narration = (
                f"Welcome, {name} the {race} {char_class}!\n\n"
                "You stand in the village square of Willowbrook. The morning sun casts long shadows "
                "across the cobblestones. To the west, smoke rises from The Rusty Dragon tavern. "
                "To the east, you hear the rhythmic clanging of the blacksmith's hammer.\n\n"
                "What would you like to do?"
            )
    
    welcome = f"📍 **{session.current_location}**\n\n{opening_narration}"
    
    session.messages.append({
        'type': 'dm',
        'content': welcome,
        'timestamp': datetime.now().isoformat()
    })
    
    # Log session start
    game_log('SESSION', f"New game started", {
        'session_id': session.session_id,
        'character': name,
        'race': race,
        'class': char_class,
        'scenario': scenario_id or 'free_adventure',
        'location': session.current_location,
        'gold': session.character.gold,
        'quests_available': len(session.quest_manager.available_quests) if session.quest_manager else 0
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
    raw_action = data.get('action', '')
    
    # Validate action type
    if not isinstance(raw_action, str):
        return jsonify({'error': 'Action must be a string'}), 400
    
    action = raw_action.strip()
    
    if not session_id or session_id not in game_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    if not action:
        return jsonify({'error': 'No action provided'}), 400
    
    session = game_sessions[session_id]
    session.touch()  # Update activity timestamp
    
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
        
        # Make a follow-up DM call to continue narration after the dice roll
        success_word = "SUCCESS" if result['success'] else "FAILURE"
        nat_20 = result['roll'] == 20
        nat_1 = result['roll'] == 1
        
        if nat_20:
            roll_continuation = f"[ROLL RESULT: {result['skill']} = {result['total']} vs DC {dc} = CRITICAL SUCCESS (NATURAL 20)!]\n\nContinue narrating what happens with this extraordinary success."
        elif nat_1:
            roll_continuation = f"[ROLL RESULT: {result['skill']} = {result['total']} vs DC {dc} = CRITICAL FAILURE (NATURAL 1)!]\n\nContinue narrating what happens with this spectacular failure."
        else:
            roll_continuation = f"[ROLL RESULT: {result['skill']} = {result['total']} vs DC {dc} = {success_word}]\n\nContinue narrating what happens based on this {'successful' if result['success'] else 'failed'} check."
        
        # Get continuation response (strip any roll requests to prevent infinite loops)
        continuation = get_dm_response(session, roll_continuation, is_opening=False)
        continuation = re.sub(r'\[ROLL:\s*\w+\s+DC\s*\d+\]', '', continuation)
        dm_response += f"\n\n{continuation}"
    
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
    
    # Parse and apply item rewards [ITEM: item_name]
    items_gained = parse_item_rewards(dm_response)
    for item_name in items_gained:
        item = get_item(item_name)
        if item and session.character:
            add_item_to_inventory(session.character.inventory, item)
    
    # Parse and apply gold rewards [GOLD: amount]
    gold_gained = parse_gold_rewards(dm_response)
    if gold_gained > 0 and session.character:
        session.character.gold += gold_gained
    
    # Parse and apply XP rewards [XP: amount | reason]
    xp_rewards = parse_xp_rewards(dm_response)
    leveled_up = False
    for xp_amount, reason in xp_rewards:
        if session.character:
            result = session.character.gain_xp(xp_amount, reason)
            if result.get('level_up'):
                leveled_up = True
    
    # Parse and apply buy transactions [BUY: item_name, price]
    buy_transactions = parse_buy_transactions(dm_response)
    for item_name, price in buy_transactions:
        if session.character and session.character.gold >= price:
            item = get_item(item_name)
            if item:
                session.character.gold -= price
                add_item_to_inventory(session.character.inventory, item)
    
    # Parse and apply gold costs [PAY: amount, reason] - for hiring, bribes, etc.
    gold_costs = parse_gold_costs(dm_response)
    gold_paid = 0
    for cost, reason in gold_costs:
        if session.character and session.character.gold >= cost:
            session.character.gold -= cost
            gold_paid += cost
            print(f"   💸 Paid {cost} gold: {reason}")
    
    # Parse and apply recruitment [RECRUIT: npc_id]
    recruited_npcs = parse_recruit_tags(dm_response)
    for npc_id in recruited_npcs:
        from party import get_recruitable_npc, Party
        if not session.party:
            session.party = Party()
        if not session.party.is_full:
            member = get_recruitable_npc(npc_id)
            if member:
                session.party.add_member(member)
                print(f"   🎉 {member.name} joined the party!")
    
    # Detect quest acceptance based on player action and DM response
    accepted_quests = detect_quest_acceptance(action, dm_response, session.quest_manager)
    if accepted_quests:
        print(f"   📜 Quests accepted: {accepted_quests}")
    
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
        'items_gained': items_gained,
        'gold_gained': gold_gained,
        'xp_gained': sum(xp for xp, _ in xp_rewards) if xp_rewards else 0,
        'leveled_up': leveled_up,
        'quests_accepted': accepted_quests,
        'game_state': session.to_dict()
    })


@app.route('/api/game/action/stream', methods=['POST'])
def game_action_stream():
    """Process a player action with streaming response (Server-Sent Events)."""
    from flask import Response, stream_with_context
    
    data = request.get_json() or {}
    
    session_id = data.get('session_id')
    raw_action = data.get('action', '')
    
    # Validate action type
    if not isinstance(raw_action, str):
        return jsonify({'error': 'Action must be a string'}), 400
    
    action = raw_action.strip()
    
    if not session_id or session_id not in game_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    if not action:
        return jsonify({'error': 'No action provided'}), 400
    
    session = game_sessions[session_id]
    session.touch()  # Update activity timestamp
    
    # Record player action
    session.messages.append({
        'type': 'player',
        'content': action,
        'timestamp': datetime.now().isoformat()
    })
    
    def generate():
        full_response = []
        
        # Log the player action
        if VERBOSE_LOGGING:
            game_log('ACTION', f"Player: {action[:100]}..." if len(action) > 100 else f"Player: {action}")
        
        # Helper for JSON with unicode support
        def json_sse(data):
            return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
        
        # Stream the DM response
        for chunk in stream_dm_response(session, action):
            full_response.append(chunk)
            # Send as SSE format
            yield json_sse({'type': 'chunk', 'content': chunk})
        
        # Combine full response for post-processing
        dm_response = ''.join(full_response)
        
        if VERBOSE_LOGGING:
            game_log('DM', f"Response length: {len(dm_response)} chars")
        
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
            game_log('ROLL', f"{skill} check DC {dc}", {'roll': result['roll'], 'modifier': result['modifier'], 'total': result['total'], 'success': result['success']})
            # Send roll result as both a roll event AND a visible chunk
            yield json_sse({'type': 'roll', 'result': roll_result})
            roll_text = f"\n\n{format_roll_result(result)}"
            yield json_sse({'type': 'chunk', 'content': roll_text})
            dm_response += roll_text
            
            # Make a follow-up DM call to continue narration after the dice roll
            success_word = "SUCCESS" if result['success'] else "FAILURE"
            nat_20 = result['roll'] == 20
            nat_1 = result['roll'] == 1
            
            if nat_20:
                roll_continuation = f"[ROLL RESULT: {result['skill']} = {result['total']} vs DC {dc} = CRITICAL SUCCESS (NATURAL 20)!]\n\nContinue narrating what happens with this extraordinary success."
            elif nat_1:
                roll_continuation = f"[ROLL RESULT: {result['skill']} = {result['total']} vs DC {dc} = CRITICAL FAILURE (NATURAL 1)!]\n\nContinue narrating what happens with this spectacular failure."
            else:
                roll_continuation = f"[ROLL RESULT: {result['skill']} = {result['total']} vs DC {dc} = {success_word}]\n\nContinue narrating what happens based on this {'successful' if result['success'] else 'failed'} check."
            
            # Stream the continuation response (no further roll processing to avoid loops)
            continuation_response = []
            for chunk in stream_dm_response(session, roll_continuation, is_roll_continuation=True):
                continuation_response.append(chunk)
                yield json_sse({'type': 'chunk', 'content': chunk})
            
            # Add continuation to response (rewards/items from continuation will be processed below)
            continuation_text = ''.join(continuation_response)
            # Strip any accidental roll requests from continuation to prevent infinite loops
            continuation_text = re.sub(r'\[ROLL:\s*\w+\s+DC\s*\d+\]', '', continuation_text)
            dm_response += '\n\n' + continuation_text
        
        # Check for combat request
        enemies, surprise = parse_combat_request(dm_response)
        if enemies:
            session.in_combat = True
            session.combat_state = {'enemies': enemies, 'surprise': surprise, 'round': 1}
            yield json_sse({'type': 'combat', 'enemies': enemies})
            combat_text = f"\n\n⚔️ COMBAT STARTED! Enemies: {', '.join(enemies)}"
            yield json_sse({'type': 'chunk', 'content': combat_text})
            game_log('COMBAT', f"Combat started", {'enemies': enemies, 'surprise': surprise})
        
        # Parse and apply item rewards [ITEM: item_name]
        items_gained = parse_item_rewards(dm_response)
        if items_gained and VERBOSE_LOGGING:
            game_log('PARSE', f"Found item tags", {'items': items_gained})
        for item_name in items_gained:
            item = get_item(item_name)
            if item and session.character:
                add_item_to_inventory(session.character.inventory, item)
                item_text = f"\n\n📦 Received: {item.name}"
                yield json_sse({'type': 'item', 'item': item_name, 'message': f'Received: {item.name}'})
                yield json_sse({'type': 'chunk', 'content': item_text})
                game_log('ITEM', f"Received: {item.name}", {'item_id': item_name})
                
                # Update quest objectives for item acquisition
                if session.quest_manager:
                    completed = session.quest_manager.on_item_acquired(item_name.lower().replace(' ', '_'))
                    for quest_id, objective in completed:
                        quest = session.quest_manager.get_quest(quest_id)
                        if quest:
                            yield json_sse({'type': 'quest_update', 'quest_id': quest_id, 'objective_id': objective.id, 'quest': quest.to_dict()})
                            game_log('QUEST', f"Item objective completed", {'quest': quest.name, 'item': item_name})
        
        # Parse and apply gold rewards [GOLD: amount]
        gold_gained = parse_gold_rewards(dm_response)
        if gold_gained > 0 and session.character:
            session.character.gold += gold_gained
            gold_text = f"\n\n💰 Received {gold_gained} gold (Total: {session.character.gold})"
            yield json_sse({'type': 'gold', 'amount': gold_gained, 'total': session.character.gold})
            yield json_sse({'type': 'chunk', 'content': gold_text})
            game_log('GOLD', f"Received {gold_gained} gold", {'total': session.character.gold})
        
        # Parse and apply XP rewards [XP: amount | reason]
        xp_rewards = parse_xp_rewards(dm_response)
        for xp_amount, reason in xp_rewards:
            if session.character:
                result = session.character.gain_xp(xp_amount, reason)
                leveled_up = result.get('level_up', False)
                xp_text = f"\n\n⭐ Gained {xp_amount} XP: {reason}" + (" 🎉 LEVEL UP!" if leveled_up else "")
                yield json_sse({'type': 'xp', 'amount': xp_amount, 'reason': reason, 'leveled_up': leveled_up})
                yield json_sse({'type': 'chunk', 'content': xp_text})
                game_log('XP', f"Gained {xp_amount} XP: {reason}", {'leveled_up': leveled_up})
        
        # Parse and apply buy transactions [BUY: item_name, price]
        buy_transactions = parse_buy_transactions(dm_response)
        for item_name, price in buy_transactions:
            if session.character and session.character.gold >= price:
                item = get_item(item_name)
                if item:
                    session.character.gold -= price
                    add_item_to_inventory(session.character.inventory, item)
                    buy_text = f"\n\n🛒 Purchased {item_name} for {price} gold (Gold: {session.character.gold})"
                    yield json_sse({'type': 'buy', 'item': item_name, 'price': price, 'gold_remaining': session.character.gold})
                    yield json_sse({'type': 'chunk', 'content': buy_text})
                    game_log('ITEM', f"Purchased: {item_name} for {price} gold", {'remaining': session.character.gold})
        
        # Parse and apply gold costs [PAY: amount, reason] - for hiring, bribes, etc.
        gold_costs = parse_gold_costs(dm_response)
        for cost, reason in gold_costs:
            if session.character and session.character.gold >= cost:
                session.character.gold -= cost
                pay_text = f"\n\n💸 Paid {cost} gold: {reason} (Gold: {session.character.gold})"
                yield json_sse({'type': 'pay', 'amount': cost, 'reason': reason, 'gold_remaining': session.character.gold})
                yield json_sse({'type': 'chunk', 'content': pay_text})
                game_log('GOLD', f"Paid {cost} gold: {reason}", {'remaining': session.character.gold})
        
        # Parse and apply recruitment [RECRUIT: npc_id]
        recruited_npcs = parse_recruit_tags(dm_response)
        if VERBOSE_LOGGING:
            game_log('PARSE', f"Checking for recruit tags", {'found': recruited_npcs, 'response_snippet': dm_response[:200] + '...'})
        
        for npc_id in recruited_npcs:
            from party import get_recruitable_npc, Party
            game_log('RECRUIT', f"Attempting to recruit: {npc_id}")
            
            if not session.party:
                session.party = Party()
                game_log('PARTY', "Created new party for session")
            
            if not session.party.is_full:
                member = get_recruitable_npc(npc_id)
                if member:
                    success, msg = session.party.add_member(member)
                    game_log('RECRUIT', f"Recruitment result: {msg}", {'success': success, 'npc_id': npc_id, 'member_name': member.name, 'party_size': session.party.size})
                    if success:
                        recruit_text = f"\n\n🎉 {member.name} joins your party!"
                        yield json_sse({'type': 'recruit', 'npc_id': npc_id, 'name': member.name})
                        yield json_sse({'type': 'chunk', 'content': recruit_text})
                else:
                    game_log('ERROR', f"Could not find recruitable NPC", {'npc_id': npc_id, 'search_term': npc_id})
            else:
                game_log('RECRUIT', f"Party is full, cannot recruit {npc_id}", {'party_size': session.party.size, 'max': session.party.MAX_COMPANIONS})
        
        # Check for NPC talk in player action for quest objectives
        if session.quest_manager and session.npc_manager:
            talked_npcs = detect_npc_talk(action, session.npc_manager)
            if talked_npcs and VERBOSE_LOGGING:
                game_log('NPC', f"Detected NPC talk", {'npcs': talked_npcs})
            for npc_id in talked_npcs:
                completed = session.quest_manager.on_npc_talked(npc_id)
                for quest_id, objective in completed:
                    quest = session.quest_manager.get_quest(quest_id)
                    if quest:
                        quest_text = f"\n\n📜 Quest Objective Complete: {objective.description}"
                        yield json_sse({'type': 'quest_update', 'quest_id': quest_id, 'objective_id': objective.id, 'quest': quest.to_dict()})
                        yield json_sse({'type': 'chunk', 'content': quest_text})
                        game_log('QUEST', f"Objective completed: {objective.description}", {'quest': quest.name})
        
        # Detect quest acceptance based on player action and DM response
        accepted_quests = detect_quest_acceptance(action, dm_response, session.quest_manager)
        for quest_id in accepted_quests:
            quest = session.quest_manager.get_quest(quest_id)
            if quest:
                quest_text = f"\n\n📜 Quest Accepted: {quest.name}"
                yield json_sse({'type': 'quest_accepted', 'quest_id': quest_id, 'quest': quest.to_dict()})
                yield json_sse({'type': 'chunk', 'content': quest_text})
                game_log('QUEST', f"Quest accepted: {quest.name}", {'quest_id': quest_id})
        
        # Record full DM response
        session.messages.append({
            'type': 'dm',
            'content': dm_response,
            'timestamp': datetime.now().isoformat(),
            'roll_result': roll_result,
            'combat_started': bool(enemies)
        })
        
        # Send completion signal
        yield json_sse({'type': 'done', 'game_state': session.to_dict()})
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )


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
    
    # Validate dice parameters
    if die_size < 1:
        return jsonify({'error': 'Dice must have at least 1 side'}), 400
    if num_dice < 1:
        return jsonify({'error': 'Must roll at least 1 die'}), 400
    if num_dice > 1000:
        return jsonify({'error': 'Maximum 1000 dice allowed'}), 400
    
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
        'character': session._serialize_character()
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
    
    # Validate and sanitize save name
    if not save_name or not isinstance(save_name, str):
        save_name = 'quicksave'
    
    # Remove path traversal attempts and dangerous characters
    import re
    # Strip path separators and traversal patterns
    save_name = save_name.replace('..', '').replace('/', '').replace('\\', '')
    # Only allow alphanumeric, underscore, hyphen, space
    save_name = re.sub(r'[^a-zA-Z0-9_\-\s]', '', save_name)
    # Limit length
    MAX_SAVE_NAME_LENGTH = 50
    save_name = save_name[:MAX_SAVE_NAME_LENGTH].strip()
    # Default if empty after sanitization
    if not save_name:
        save_name = 'quicksave'
    
    # Create save data
    save_data = {
        'session_id': session.session_id,
        'character': session._serialize_character(),
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
    
    if VERBOSE_LOGGING:
        game_log('SAVE', f"Game saved: {save_name}", {
            'character': session.character.name if session.character else 'None',
            'level': session.character.level if session.character else 0,
            'location': session.current_location,
            'in_combat': session.in_combat
        })
    
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
        if VERBOSE_LOGGING:
            game_log('ERROR', f"Save not found: {save_name}")
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
    
    if VERBOSE_LOGGING:
        game_log('SAVE', f"Game loaded: {save_name}", {
            'character': session.character.name if session.character else 'None',
            'level': session.character.level if session.character else 0,
            'location': session.current_location,
            'in_combat': session.in_combat,
            'messages_count': len(session.messages)
        })
    
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


@app.route('/api/scenarios', methods=['GET'])
def get_scenarios():
    """Get available game scenarios."""
    scenario_manager = ScenarioManager()
    scenarios = scenario_manager.list_available()
    return jsonify({
        'success': True,
        'scenarios': scenarios
    })


# =============================================================================
# LOCATION & TRAVEL ENDPOINTS
# =============================================================================

@app.route('/api/locations', methods=['GET'])
def get_locations():
    """Get current location info and available travel destinations with map data."""
    session_id = request.args.get('session_id')
    
    if not session_id or session_id not in game_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    session = game_sessions[session_id]
    
    # Build destinations list with map data
    destinations = []
    all_locations = []  # All known locations for map
    current_loc_data = None
    
    if session.location_manager:
        location = session.location_manager.get_current_location()
        exits = session.location_manager.get_exits()
        
        # Current location data
        if location:
            current_loc_data = {
                'id': location.id,
                'name': location.name,
                'map_x': location.map_x,
                'map_y': location.map_y,
                'map_icon': location.map_icon,
                'map_region': location.map_region
            }
        
        # Get all locations for map display
        for loc_id, loc in session.location_manager.locations.items():
            # Only show locations that are visited OR available OR not hidden
            show_on_map = loc.visited or (not loc.map_hidden and loc_id in session.location_manager.available_location_ids)
            
            all_locations.append({
                'id': loc_id,
                'name': loc.name if show_on_map else '???',
                'map_x': loc.map_x,
                'map_y': loc.map_y,
                'map_icon': loc.map_icon if show_on_map else '❓',
                'map_label': loc.map_label or loc.name,
                'map_region': loc.map_region,
                'visited': loc.visited,
                'hidden': loc.map_hidden and not loc.visited,
                'is_current': loc_id == session.current_location_id,
                'reachable': loc_id in exits.values()
            })
        
        # Available destinations (exits from current location)
        for exit_name, dest_id in exits.items():
            dest_location = session.location_manager.locations.get(dest_id)
            if dest_location:
                destinations.append({
                    'id': dest_id,
                    'name': dest_location.name,
                    'exit_name': exit_name,
                    'description': dest_location.description[:100] + '...' if len(dest_location.description) > 100 else dest_location.description,
                    'visited': dest_location.visited,
                    'map_x': dest_location.map_x,
                    'map_y': dest_location.map_y,
                    'map_icon': dest_location.map_icon
                })
    
    return jsonify({
        'success': True,
        'current_location': current_loc_data or {
            'id': session.current_location_id,
            'name': session.current_location,
            'map_x': 0.5,
            'map_y': 0.5,
            'map_icon': '📍',
            'map_region': 'default'
        },
        'destinations': destinations,
        'all_locations': all_locations
    })


@app.route('/api/travel', methods=['POST'])
def travel():
    """Move to a new location."""
    data = request.get_json() or {}
    session_id = data.get('session_id')
    destination = data.get('destination')  # Can be exit_name or destination_id
    
    if not session_id or session_id not in game_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    if not destination:
        return jsonify({'error': 'No destination specified'}), 400
    
    session = game_sessions[session_id]
    session.touch()  # Update activity timestamp
    
    # Block travel during combat - must defeat or flee from enemies first
    if session.in_combat:
        return jsonify({
            'error': 'Cannot travel during combat! Defeat enemies or flee first.',
            'in_combat': True
        }), 400
    
    if not session.location_manager:
        # Fallback for free adventure mode (no structured locations)
        old_location = session.current_location
        session.current_location = destination.title()
        
        travel_msg = f"📍 You travel to **{session.current_location}**."
        session.messages.append({
            'type': 'dm',
            'content': travel_msg,
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify({
            'success': True,
            'message': travel_msg,
            'new_location': session.current_location,
            'old_location': old_location
        })
    
    # Use location manager for structured scenarios
    game_state = {
        'character': session.character,
        'inventory': session.character.inventory if session.character else [],
        'visited_locations': [loc.id for loc in session.location_manager.locations.values() if loc.visited]
    }
    
    success, new_location, message, events = session.location_manager.move(destination, game_state)
    
    if success and new_location:
        session.current_location = new_location.name
        session.current_location_id = new_location.id
        
        # Update quest objectives for location entry
        quest_updates = []
        if session.quest_manager:
            completed = session.quest_manager.on_location_entered(new_location.id)
            for quest_id, objective in completed:
                quest = session.quest_manager.get_quest(quest_id)
                if quest:
                    quest_updates.append({
                        'quest_id': quest_id,
                        'objective_id': objective.id,
                        'quest': quest.to_dict()
                    })
        
        # Build travel narration
        travel_msg = f"📍 You travel to **{new_location.name}**.\n\n{new_location.description}"
        
        # Add any triggered events
        if events:
            for event in events:
                travel_msg += f"\n\nâš¡ {event.narration}"
        
        if VERBOSE_LOGGING:
            game_log('LOCATION', f"Traveled to {new_location.name}", {
                'from': session.current_location if hasattr(session, 'current_location') else 'unknown',
                'to': new_location.name,
                'location_id': new_location.id,
                'exits': list(session.location_manager.get_exits().keys()),
                'events_triggered': len(events) if events else 0
            })
        
        session.messages.append({
            'type': 'dm',
            'content': travel_msg,
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify({
            'success': True,
            'message': travel_msg,
            'new_location': {
                'id': new_location.id,
                'name': new_location.name,
                'description': new_location.description,
                'exits': list(session.location_manager.get_exits().keys())
            },
            'events': [e.to_dict() for e in events],
            'quest_updates': quest_updates,
            'game_state': session.to_dict()
        })
    else:
        return jsonify({
            'success': False,
            'message': message or "You cannot go that way."
        })


# =============================================================================
# COMBAT SYSTEM ENDPOINTS
# =============================================================================

@app.route('/api/combat/status', methods=['GET'])
def combat_status():
    """Get current combat status."""
    session_id = request.args.get('session_id')
    
    if not session_id or session_id not in game_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    session = game_sessions[session_id]
    
    if not session.in_combat:
        return jsonify({
            'success': True,
            'in_combat': False,
            'message': 'Not in combat'
        })
    
    # Get enemy statuses
    enemies_status = []
    if session.combat_state and 'enemy_objects' in session.combat_state:
        for enemy in session.combat_state['enemy_objects']:
            enemies_status.append({
                'name': enemy.name,
                'current_hp': enemy.current_hp,
                'max_hp': enemy.max_hp,
                'is_dead': enemy.is_dead,
                'status': enemy.get_status()
            })
    
    return jsonify({
        'success': True,
        'in_combat': True,
        'round': session.combat_state.get('round', 1),
        'surprise': session.combat_state.get('surprise', False),
        'enemies': enemies_status,
        'player_hp': session.character.current_hp if session.character else 0,
        'player_max_hp': session.character.max_hp if session.character else 0
    })


@app.route('/api/combat/attack', methods=['POST'])
def combat_attack():
    """Player attacks an enemy."""
    from combat import (
        create_enemy, roll_attack, roll_attack_with_advantage, roll_attack_with_disadvantage,
        roll_damage, format_attack_result, format_damage_result, enemy_attack, format_enemy_attack,
        get_enemy_loot_for_class, determine_turn_order, party_member_attack, format_party_member_attack,
        get_party_member_action, check_flanking
    )
    from dm_engine import check_darkness_penalty
    
    data = request.get_json() or {}
    session_id = data.get('session_id')
    target_index = data.get('target', 0)
    
    if not session_id or session_id not in game_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    session = game_sessions[session_id]
    
    if not session.in_combat:
        return jsonify({'error': 'Not in combat'}), 400
    
    if not session.character:
        return jsonify({'error': 'No character'}), 400
    
    # Initialize enemy objects if not done
    if 'enemy_objects' not in session.combat_state:
        session.combat_state['enemy_objects'] = []
        for enemy_type in session.combat_state.get('enemies', []):
            enemy = create_enemy(enemy_type.lower().replace(' ', '_'))
            if enemy:
                session.combat_state['enemy_objects'].append(enemy)
    
    enemies = session.combat_state['enemy_objects']
    living_enemies = [e for e in enemies if not e.is_dead]
    
    if not living_enemies:
        session.in_combat = False
        return jsonify({
            'success': True,
            'combat_over': True,
            'victory': True,
            'message': '🎉 Victory! All enemies defeated!'
        })
    
    if target_index >= len(living_enemies):
        target_index = 0
    target = living_enemies[target_index]
    
    # Get equipped weapon (or fallback to first weapon in inventory)
    weapon_name = 'longsword'
    if session.character.weapon:
        weapon_name = session.character.weapon.lower().replace(' ', '_')
    elif session.character.inventory:
        for item in session.character.inventory:
            if hasattr(item, 'damage_dice') and item.damage_dice:
                weapon_name = item.name.lower().replace(' ', '_')
                break
    
    # Check darkness penalty (Phase 3.6.7 integration)
    darkness_penalty = False
    darkness_message = ""
    if hasattr(session, 'location') and session.location:
        darkness_check = check_darkness_penalty(session.location, session.character)
        if darkness_check.get('in_darkness', False):
            darkness_penalty = True
            darkness_message = darkness_check.get('penalty_message', '')
    
    # Roll attack (advantage from surprise, disadvantage from darkness)
    has_surprise = session.combat_state.get('surprise', False) and session.combat_state.get('round', 1) == 1
    if has_surprise and not darkness_penalty:
        # Surprise gives advantage (darkness would cancel it out)
        attack = roll_attack_with_advantage(session.character, target.armor_class, weapon_name)
    elif darkness_penalty and not has_surprise:
        # Darkness gives disadvantage
        attack = roll_attack_with_disadvantage(session.character, target.armor_class, weapon_name)
    else:
        # Normal roll (or advantage/disadvantage cancel out)
        attack = roll_attack(session.character, target.armor_class, weapon_name)
    
    result_messages = []
    if darkness_message:
        result_messages.append(darkness_message)
    result_messages.append(format_attack_result(attack))
    damage_dealt = 0
    target_killed = False
    
    if attack['hit']:
        damage = roll_damage(session.character, weapon_name, attack['is_crit'])
        damage_dealt = damage['total']
        result_messages.append(format_damage_result(damage))
        status_msg = target.take_damage(damage_dealt)
        result_messages.append(status_msg)
        target_killed = target.is_dead
        
        # Track quest objective for killed enemies
        if target_killed and session.quest_manager:
            enemy_id = target.enemy_type if hasattr(target, 'enemy_type') else target.name.lower().replace(' ', '_')
            completed = session.quest_manager.on_enemy_killed(enemy_id)
            for quest_id, obj in completed:
                result_messages.append(f"📜 Quest Objective Complete: {obj.description}")
    
    living_enemies = [e for e in enemies if not e.is_dead]
    combat_over = len(living_enemies) == 0
    
    # Phase 3.5 P7 Step 6: Party Member Actions
    party_damage_dealt = 0
    if not combat_over and session.party and hasattr(session.party, 'members'):
        recruited_members = [m for m in session.party.members if m.recruited and not m.is_dead]
        if recruited_members:
            result_messages.append("\n--- Party Member Turns ---")
            
            # Build allies HP dict for AI decisions
            allies_hp = {
                session.character.name: (session.character.current_hp, session.character.max_hp)
            }
            for m in recruited_members:
                allies_hp[m.name] = (m.current_hp, m.max_hp)
            
            # Check if flanking (player + party members on same target)
            # Simplified: if player attacked an enemy and party member attacks same = flanking
            player_target_name = target.name if target else None
            
            for member in recruited_members:
                living_enemies = [e for e in enemies if not e.is_dead]
                if not living_enemies:
                    break  # All enemies dead
                    
                # Get AI decision for this party member
                action = get_party_member_action(member, living_enemies, allies_hp)
                
                if action['action_type'] == 'ability' and action.get('use_ability'):
                    # Use special ability
                    success, ability_msg = member.use_ability()
                    if success:
                        result_messages.append(ability_msg)
                        # Apply ability effects (simplified)
                        if action.get('ability_name') == 'Healing Word':
                            # Heal the target ally
                            heal_target = action.get('target')
                            heal_amount = random.randint(1, 8) + 2  # 1d8+2
                            if heal_target == session.character.name:
                                session.character.current_hp = min(
                                    session.character.max_hp,
                                    session.character.current_hp + heal_amount
                                )
                                result_messages.append(f"   💚 You heal {heal_amount} HP!")
                                allies_hp[session.character.name] = (session.character.current_hp, session.character.max_hp)
                
                elif action['action_type'] == 'attack' and action.get('target'):
                    enemy_target = action['target']
                    
                    # Check flanking (same target as player or another party member)
                    has_flanking = check_flanking(2)  # Simplified: always 2 if party present
                    
                    # Get member's class for formatting
                    member_class = member.char_class.value if hasattr(member.char_class, 'value') else str(member.char_class)
                    
                    # Party member attacks
                    pm_attack, pm_damage = party_member_attack(member, enemy_target, has_flanking)
                    result_messages.append(format_party_member_attack(pm_attack, pm_damage, member_class))
                    
                    if pm_damage:
                        party_damage_dealt += pm_damage['total']
                        status_msg = enemy_target.take_damage(pm_damage['total'])
                        if enemy_target.is_dead:
                            result_messages.append(f"   💀 {enemy_target.name} falls!")
                            # Track quest objective
                            if session.quest_manager:
                                enemy_id = enemy_target.name.lower().replace(' ', '_')
                                completed = session.quest_manager.on_enemy_killed(enemy_id)
                                for quest_id, obj in completed:
                                    result_messages.append(f"   📜 Quest Objective Complete: {obj.description}")
    
    living_enemies = [e for e in enemies if not e.is_dead]
    combat_over = len(living_enemies) == 0
    
    rewards = {'xp': 0, 'gold': 0, 'items': []}
    if combat_over:
        session.in_combat = False
        result_messages.append("\n🎉 **VICTORY!**")
        for enemy in enemies:
            rewards['xp'] += enemy.xp_reward
            rewards['gold'] += enemy.gold_drop
        if rewards['xp'] > 0:
            session.character.gain_xp(rewards['xp'], "combat victory")
            result_messages.append(f"⭐ Gained {rewards['xp']} XP!")
        if rewards['gold'] > 0:
            session.character.gold += rewards['gold']
            result_messages.append(f"💰 Looted {rewards['gold']} gold!")
        # Party damage summary
        if party_damage_dealt > 0:
            result_messages.append(f"📊 Party contributed {party_damage_dealt} total damage!")
    else:
        result_messages.append("\n--- Enemy Turn ---")
        for enemy in living_enemies:
            enemy_atk, enemy_dmg = enemy_attack(enemy, session.character.armor_class)
            result_messages.append(format_enemy_attack(enemy_atk, enemy_dmg))
            if enemy_dmg:
                session.character.current_hp -= enemy_dmg['total']
                if session.character.current_hp <= 0:
                    session.character.current_hp = 0
                    session.in_combat = False
                    result_messages.append("\n💀 **DEFEAT!**")
                    return jsonify({
                        'success': True,
                        'combat_over': True,
                        'victory': False,
                        'player_died': True,
                        'message': '\n'.join(result_messages),
                        'game_state': session.to_dict()
                    })
        session.combat_state['round'] = session.combat_state.get('round', 1) + 1
    
    return jsonify({
        'success': True,
        'hit': attack['hit'],
        'damage_dealt': damage_dealt,
        'target_killed': target_killed,
        'combat_over': combat_over,
        'victory': combat_over,
        'rewards': rewards if combat_over else None,
        'enemies': [{'name': e.name, 'hp': e.current_hp, 'max_hp': e.max_hp, 'dead': e.is_dead} for e in enemies],
        'player_hp': session.character.current_hp,
        'message': '\n'.join(result_messages),
        'game_state': session.to_dict()
    })


@app.route('/api/combat/defend', methods=['POST'])
def combat_defend():
    """Player takes defensive action."""
    from combat import enemy_attack, format_enemy_attack, create_enemy
    
    data = request.get_json() or {}
    session_id = data.get('session_id')
    
    if not session_id or session_id not in game_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    session = game_sessions[session_id]
    
    if not session.in_combat:
        return jsonify({'error': 'Not in combat'}), 400
    
    if 'enemy_objects' not in session.combat_state:
        session.combat_state['enemy_objects'] = []
        for enemy_type in session.combat_state.get('enemies', []):
            enemy = create_enemy(enemy_type.lower().replace(' ', '_'))
            if enemy:
                session.combat_state['enemy_objects'].append(enemy)
    
    enemies = session.combat_state['enemy_objects']
    living_enemies = [e for e in enemies if not e.is_dead]
    
    result_messages = ["🛡️ You take a defensive stance (+2 AC, half damage)"]
    boosted_ac = session.character.armor_class + 2
    
    for enemy in living_enemies:
        enemy_atk, enemy_dmg = enemy_attack(enemy, boosted_ac)
        result_messages.append(format_enemy_attack(enemy_atk, enemy_dmg))
        if enemy_dmg:
            reduced_damage = max(1, enemy_dmg['total'] // 2)
            session.character.current_hp -= reduced_damage
            result_messages.append(f"   (Reduced to {reduced_damage} damage)")
            if session.character.current_hp <= 0:
                session.character.current_hp = 0
                session.in_combat = False
                return jsonify({
                    'success': True,
                    'combat_over': True,
                    'player_died': True,
                    'message': '\n'.join(result_messages),
                    'game_state': session.to_dict()
                })
    
    session.combat_state['round'] = session.combat_state.get('round', 1) + 1
    
    return jsonify({
        'success': True,
        'message': '\n'.join(result_messages),
        'player_hp': session.character.current_hp,
        'game_state': session.to_dict()
    })


@app.route('/api/combat/flee', methods=['POST'])
def combat_flee():
    """Attempt to flee from combat."""
    from combat import enemy_attack, format_enemy_attack, create_enemy
    import random
    
    data = request.get_json() or {}
    session_id = data.get('session_id')
    
    if not session_id or session_id not in game_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    session = game_sessions[session_id]
    
    if not session.in_combat:
        return jsonify({'error': 'Not in combat'}), 400
    
    if 'enemy_objects' not in session.combat_state:
        session.combat_state['enemy_objects'] = []
        for enemy_type in session.combat_state.get('enemies', []):
            enemy = create_enemy(enemy_type.lower().replace(' ', '_'))
            if enemy:
                session.combat_state['enemy_objects'].append(enemy)
    
    enemies = session.combat_state['enemy_objects']
    living_enemies = [e for e in enemies if not e.is_dead]
    
    dex_mod = session.character.get_ability_modifier('dexterity')
    roll = random.randint(1, 20)
    dc = 10 + len(living_enemies)
    total = roll + dex_mod
    success = total >= dc
    
    result_messages = [f"🏃 DEX check: [{roll}]+{dex_mod} = {total} vs DC {dc}"]
    
    if success:
        session.in_combat = False
        result_messages.append("✅ You escape!")
        return jsonify({
            'success': True,
            'fled': True,
            'combat_over': True,
            'message': '\n'.join(result_messages),
            'game_state': session.to_dict()
        })
    
    result_messages.append("❌ Failed! Enemies attack...")
    for enemy in living_enemies:
        enemy_atk, enemy_dmg = enemy_attack(enemy, session.character.armor_class)
        result_messages.append(format_enemy_attack(enemy_atk, enemy_dmg))
        if enemy_dmg:
            session.character.current_hp -= enemy_dmg['total']
            if session.character.current_hp <= 0:
                session.character.current_hp = 0
                session.in_combat = False
                return jsonify({
                    'success': True,
                    'fled': False,
                    'combat_over': True,
                    'player_died': True,
                    'message': '\n'.join(result_messages),
                    'game_state': session.to_dict()
                })
    
    session.combat_state['round'] = session.combat_state.get('round', 1) + 1
    return jsonify({
        'success': True,
        'fled': False,
        'combat_over': False,
        'message': '\n'.join(result_messages),
        'game_state': session.to_dict()
    })


# =============================================================================
# CHARACTER ENDPOINTS
# =============================================================================

@app.route('/api/character/levelup', methods=['POST'])
def character_levelup():
    """Level up the character."""
    data = request.get_json() or {}
    session_id = data.get('session_id')
    
    if not session_id or session_id not in game_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    session = game_sessions[session_id]
    
    if not session.character:
        return jsonify({'error': 'No character'}), 400
    
    if not session.character.can_level_up():
        return jsonify({'success': False, 'message': 'Not enough XP'})
    
    result = session.character.level_up()
    
    return jsonify({
        'success': True,
        'old_level': result['old_level'],
        'new_level': result['new_level'],
        'hp_gain': result['hp_gain'],
        'benefits': result['benefits'],
        'message': f"🎉 Level {result['new_level']}!",
        'game_state': session.to_dict()
    })


@app.route('/api/character/rest', methods=['POST'])
def character_rest():
    """Take a short or long rest."""
    from combat import roll_dice
    
    data = request.get_json() or {}
    session_id = data.get('session_id')
    rest_type = data.get('type', 'short')
    
    if not session_id or session_id not in game_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    session = game_sessions[session_id]
    
    if not session.character:
        return jsonify({'error': 'No character'}), 400
    
    if session.in_combat:
        return jsonify({'success': False, 'message': "Can't rest in combat!"})
    
    if session.character.current_hp >= session.character.max_hp:
        return jsonify({'success': False, 'message': "Already at full health!"})
    
    if session.combat_state is None:
        session.combat_state = {}
    if 'hit_dice_remaining' not in session.combat_state:
        session.combat_state['hit_dice_remaining'] = session.character.level
    
    if rest_type == 'long':
        old_hp = session.character.current_hp
        session.character.current_hp = session.character.max_hp
        session.combat_state['hit_dice_remaining'] = session.character.level
        return jsonify({
            'success': True,
            'rest_type': 'long',
            'healed': session.character.max_hp - old_hp,
            'new_hp': session.character.current_hp,
            'message': f"😴 Long rest! Full HP restored.",
            'game_state': session.to_dict()
        })
    
    if session.combat_state['hit_dice_remaining'] <= 0:
        return jsonify({'success': False, 'message': "No hit dice remaining!"})
    
    session.combat_state['hit_dice_remaining'] -= 1
    heal_roll, _ = roll_dice("1d6")
    con_mod = session.character.get_ability_modifier('constitution')
    total_heal = max(1, heal_roll + con_mod)
    
    old_hp = session.character.current_hp
    session.character.current_hp = min(session.character.max_hp, session.character.current_hp + total_heal)
    
    return jsonify({
        'success': True,
        'rest_type': 'short',
        'roll': heal_roll,
        'healed': session.character.current_hp - old_hp,
        'new_hp': session.character.current_hp,
        'hit_dice_remaining': session.combat_state['hit_dice_remaining'],
        'message': f"😴 Healed {session.character.current_hp - old_hp} HP!",
        'game_state': session.to_dict()
    })


# =============================================================================
# INVENTORY ENDPOINTS
# =============================================================================

@app.route('/api/inventory/use', methods=['POST'])
def inventory_use():
    """Use an item."""
    from inventory import use_item, find_item_in_inventory, remove_item_from_inventory
    
    data = request.get_json() or {}
    session_id = data.get('session_id')
    item_name = data.get('item_name', '').strip()
    
    if not session_id or session_id not in game_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    session = game_sessions[session_id]
    
    if not session.character:
        return jsonify({'error': 'No character'}), 400
    
    item = find_item_in_inventory(session.character.inventory, item_name)
    if not item:
        return jsonify({'success': False, 'message': f"No '{item_name}' in inventory."})
    
    success, message = use_item(item, session.character)
    if success:
        remove_item_from_inventory(session.character.inventory, item_name, 1)
    
    return jsonify({
        'success': success,
        'message': message,
        'current_hp': session.character.current_hp,
        'game_state': session.to_dict()
    })


@app.route('/api/inventory/equip', methods=['POST'])
def inventory_equip():
    """Equip a weapon or armor."""
    from inventory import find_item_in_inventory, ItemType
    
    data = request.get_json() or {}
    session_id = data.get('session_id')
    item_name = data.get('item_name', '').strip()
    
    if not session_id or session_id not in game_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    session = game_sessions[session_id]
    
    if not session.character:
        return jsonify({'error': 'No character'}), 400
    
    item = find_item_in_inventory(session.character.inventory, item_name)
    if not item:
        return jsonify({'success': False, 'message': f"No '{item_name}' in inventory."})
    
    if item.item_type == ItemType.WEAPON:
        session.character.weapon = item.name
        return jsonify({
            'success': True,
            'message': f"⚔️ Equipped {item.name}!",
            'game_state': session.to_dict()
        })
    elif item.item_type == ItemType.ARMOR:
        session.character.equipped_armor = item.name
        if item.ac_bonus:
            session.character.armor_class = 10 + item.ac_bonus
        return jsonify({
            'success': True,
            'message': f"🛡️ Equipped {item.name}!",
            'game_state': session.to_dict()
        })
    
    return jsonify({'success': False, 'message': "Can't equip that."})


# =============================================================================
# SHOP ENDPOINTS
# =============================================================================

@app.route('/api/shop/browse', methods=['GET'])
def shop_browse():
    """Browse shop inventory."""
    from shop import create_general_shop, calculate_buy_price
    
    session_id = request.args.get('session_id')
    
    if not session_id or session_id not in game_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    session = game_sessions[session_id]
    
    shop = create_general_shop("general_shop", "General Store", "merchant")
    
    items = []
    for shop_item in shop.inventory:
        item = get_item(shop_item.item_id)
        if item and shop_item.is_in_stock():
            price = calculate_buy_price(item, shop.markup, shop_item.base_markup, 1.0)
            items.append({
                'id': shop_item.item_id,
                'name': item.name,
                'price': price,
                'stock': shop_item.get_available()
            })
    
    return jsonify({
        'success': True,
        'shop_name': shop.name,
        'items': items,
        'player_gold': session.character.gold if session.character else 0
    })


@app.route('/api/shop/buy', methods=['POST'])
def shop_buy():
    """Buy an item."""
    from shop import buy_item, create_general_shop
    
    data = request.get_json() or {}
    session_id = data.get('session_id')
    item_id = data.get('item_id', '').strip()
    quantity = data.get('quantity', 1)
    
    if not session_id or session_id not in game_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    session = game_sessions[session_id]
    
    if not session.character:
        return jsonify({'error': 'No character'}), 400
    
    # Validate quantity (prevents negative/invalid values)
    if not isinstance(quantity, int) or quantity <= 0:
        return jsonify({'error': 'Quantity must be a positive integer'}), 400
    if quantity > 99:
        return jsonify({'error': 'Maximum 99 items per purchase'}), 400
    
    # Create a generic shop with common items
    shop = create_general_shop(
        id="general_shop",
        name="General Store",
        owner_npc_id="merchant",
        location_id="village",
        items={
            "healing_potion": -1,  # Unlimited
            "torch": -1,
            "rope": -1,
            "rations": -1,
            "waterskin": -1,
            "bedroll": -1
        },
        markup=1.2
    )
    
    # FIX: Use correct function signature
    result = buy_item(
        character=session.character,
        shop=shop,
        item_id=item_id,
        quantity=quantity,
        npc_disposition="neutral"
    )
    
    # buy_item updates character.gold internally when successful
    
    return jsonify({
        'success': result.success,
        'message': result.message,
        'gold_remaining': session.character.gold,
        'game_state': session.to_dict()
    })


@app.route('/api/shop/sell', methods=['POST'])
def shop_sell():
    """Sell an item."""
    from shop import sell_item, create_general_shop
    from inventory import find_item_in_inventory
    
    data = request.get_json() or {}
    session_id = data.get('session_id')
    item_name = data.get('item_name', '').strip()
    
    if not session_id or session_id not in game_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    session = game_sessions[session_id]
    
    if not session.character:
        return jsonify({'error': 'No character'}), 400
    
    # Validate item_name
    if not item_name:
        return jsonify({'error': 'Item name is required'}), 400
    
    item = find_item_in_inventory(session.character.inventory, item_name)
    if not item:
        return jsonify({'success': False, 'message': f"No '{item_name}' to sell."})
    
    # Create a generic shop for selling
    shop = create_general_shop(
        id="general_shop",
        name="General Store",
        owner_npc_id="merchant",
        location_id="village",
        items={},  # Empty - just need a shop object for sell
        markup=1.2
    )
    
    # FIX: Use correct function signature
    result = sell_item(
        character=session.character,
        shop=shop,
        item_id=item.id,  # Use item.id not item_name
        quantity=1,
        npc_disposition="neutral"
    )
    
    return jsonify({
        'success': result.success,
        'message': result.message,
        'gold_remaining': session.character.gold,
        'game_state': session.to_dict()
    })


# =============================================================================
# PARTY ENDPOINTS
# =============================================================================

@app.route('/api/party/view', methods=['GET'])
def party_view():
    """View party members."""
    # Support both query param and header for session_id
    session_id = request.args.get('session_id') or request.headers.get('X-Session-ID')
    
    if not session_id or session_id not in game_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    session = game_sessions[session_id]
    
    if not session.party:
        return jsonify({'success': True, 'members': []})
    
    members = []
    for m in session.party.get_alive_members():
        members.append({
            'id': m.id,
            'name': m.name,
            'class': m.member_class.value,
            'hp': f"{m.current_hp}/{m.max_hp}"
        })
    
    return jsonify({'success': True, 'members': members})


@app.route('/api/party/recruit', methods=['POST'])
def party_recruit():
    """Recruit an NPC."""
    from party import get_recruitable_npc, check_recruitment_condition, pay_recruitment_cost, Party
    
    data = request.get_json() or {}
    session_id = data.get('session_id')
    npc_id = data.get('npc_id', '').strip()
    
    if not session_id or session_id not in game_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    session = game_sessions[session_id]
    
    if not session.character:
        return jsonify({'error': 'No character'}), 400
    
    if not session.party:
        session.party = Party()
    
    if session.party.is_full:  # is_full is a property, not a method
        return jsonify({'success': False, 'message': 'Party is full!'})
    
    member = get_recruitable_npc(npc_id)
    if not member:
        return jsonify({'success': False, 'message': f"Can't recruit '{npc_id}'."})
    
    game_state = {
        'gold': session.character.gold,
        'charisma_modifier': session.character.get_ability_modifier('charisma')
    }
    
    can_recruit, message, _ = check_recruitment_condition(member, game_state)
    if not can_recruit:
        return jsonify({'success': False, 'message': message})
    
    pay_success, pay_message, _ = pay_recruitment_cost(member, session.character)
    if not pay_success:
        return jsonify({'success': False, 'message': pay_message})
    
    session.party.add_member(member)
    
    return jsonify({
        'success': True,
        'message': f"🎉 {member.name} joins your party!",
        'game_state': session.to_dict()
    })


# =============================================================================
# QUEST ENDPOINTS
# =============================================================================

@app.route('/api/quests', methods=['GET'])
@app.route('/api/quests/list', methods=['GET'])
def quests_list():
    """List quests."""
    try:
        # Support both query param and header for session_id
        session_id = request.args.get('session_id') or request.headers.get('X-Session-ID')
        
        if not session_id or session_id not in game_sessions:
            return jsonify({'error': 'Invalid session'}), 400
        
        session = game_sessions[session_id]
        
        if not session.quest_manager:
            return jsonify({'success': True, 'quests': [], 'active': [], 'completed': []})
        
        all_quests = [q.to_dict() for q in session.quest_manager.get_active_quests()]
        all_quests.extend(session.quest_manager.get_completed_quests())
        
        return jsonify({
            'success': True,
            'quests': all_quests,
            'active': [q.to_dict() for q in session.quest_manager.get_active_quests()],
            'completed': session.quest_manager.get_completed_quests()
        })
    except Exception as e:
        app.logger.error(f"Quest list error: {e}")
        return jsonify({'error': f'Quest list failed: {str(e)}'}), 500


@app.route('/api/quests/complete', methods=['POST'])
def quests_complete():
    """Complete a quest."""
    data = request.get_json() or {}
    session_id = data.get('session_id')
    quest_id = data.get('quest_id', '')
    # Ensure quest_id is a string
    if not isinstance(quest_id, str):
        quest_id = str(quest_id) if quest_id is not None else ''
    quest_id = quest_id.strip()
    
    if not session_id or session_id not in game_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    session = game_sessions[session_id]
    
    if not session.quest_manager:
        return jsonify({'error': 'No quest system'}), 400
    
    quest = session.quest_manager.get_quest(quest_id)
    if not quest:
        return jsonify({'success': False, 'message': 'Quest not found.'})
    
    if not quest.is_complete():
        return jsonify({'success': False, 'message': 'Objectives not complete.'})
    
    quest.completed = True
    
    rewards = {'xp': 0, 'gold': 0}
    if session.character and quest.rewards:
        if quest.rewards.get('xp'):
            session.character.gain_xp(quest.rewards['xp'], quest.name)
            rewards['xp'] = quest.rewards['xp']
        if quest.rewards.get('gold'):
            session.character.gold += quest.rewards['gold']
            rewards['gold'] = quest.rewards['gold']
    
    return jsonify({
        'success': True,
        'rewards': rewards,
        'message': f"🎉 Quest Complete! +{rewards['xp']} XP, +{rewards['gold']} Gold",
        'game_state': session.to_dict()
    })


# =============================================================================
# LOCATION SCAN ENDPOINT
# =============================================================================

@app.route('/api/location/scan', methods=['GET'])
def location_scan():
    """Scan current location."""
    session_id = request.args.get('session_id')
    
    if not session_id or session_id not in game_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    session = game_sessions[session_id]
    
    result = {
        'location': session.current_location,
        'npcs': [],
        'exits': []
    }
    
    if session.npc_manager:
        for npc in session.npc_manager.get_all_npcs():
            if getattr(npc, 'location', None) == session.current_location or getattr(npc, 'location_id', None) == getattr(session, 'current_location_id', None):
                result['npcs'].append({'id': npc.id, 'name': npc.name})
    
    if session.location_manager:
        exits = session.location_manager.get_exits()
        result['exits'] = [{'direction': k, 'destination': v} for k, v in exits.items()]
    
    return jsonify({'success': True, **result})


# =============================================================================
# REPUTATION ENDPOINT
# =============================================================================

@app.route('/api/reputation', methods=['GET'])
def get_reputation():
    """
    Get all NPC relationships and disposition levels.
    
    Returns a list of NPCs the player has interacted with,
    their disposition values, and the resulting relationship level.
    """
    # Support both query param and header for session_id
    session_id = request.args.get('session_id') or request.headers.get('X-Session-ID')
    
    if not session_id or session_id not in game_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    session = game_sessions[session_id]
    
    relationships = []
    
    try:
        if session.npc_manager:
            for npc in session.npc_manager.get_all_npcs():
                # Get disposition level and related info
                level = npc.get_disposition_level()
                label = npc.get_disposition_label()
                can_trade = npc.can_trade()
                
                # Color coding for UI
                color_map = {
                    'hostile': '🔴',
                    'unfriendly': '🟠', 
                    'neutral': '🟡',
                    'friendly': '🟢',
                    'trusted': '💚'
                }
                
                # Safely get role value
                role_value = ''
                if hasattr(npc, 'role'):
                    if hasattr(npc.role, 'value'):
                        role_value = npc.role.value
                    elif hasattr(npc.role, 'name'):
                        role_value = npc.role.name
                    else:
                        role_value = str(npc.role)
                
                relationships.append({
                    'npc_id': npc.id,
                    'name': npc.name,
                    'disposition': npc.disposition,
                    'level': level,
                    'label': label,
                    'color': color_map.get(level, '⚪'),
                    'can_trade': can_trade,
                    'location': getattr(npc, 'location', ''),
                    'role': role_value
                })
    except Exception as e:
        # Log error but continue with empty relationships
        print(f"Error fetching NPC relationships: {e}")
    
    # Sort by disposition (highest first)
    relationships.sort(key=lambda x: x.get('disposition', 0), reverse=True)
    
    return jsonify({
        'success': True,
        'relationships': relationships,
        'summary': {
            'total_npcs': len(relationships),
            'hostile': sum(1 for r in relationships if r['level'] == 'hostile'),
            'unfriendly': sum(1 for r in relationships if r['level'] == 'unfriendly'),
            'neutral': sum(1 for r in relationships if r['level'] == 'neutral'),
            'friendly': sum(1 for r in relationships if r['level'] == 'friendly'),
            'trusted': sum(1 for r in relationships if r['level'] == 'trusted')
        }
    })


@app.route('/api/reputation/<npc_id>', methods=['GET'])
def get_reputation_detail(npc_id: str):
    """
    Get detailed reputation with a specific NPC.
    Returns disposition, level, price modifier, and available interactions.
    """
    # Support both query param and header for session_id
    session_id = request.args.get('session_id') or request.headers.get('X-Session-ID')
    
    if not session_id or session_id not in game_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    session = game_sessions[session_id]
    
    if not session.npc_manager:
        return jsonify({'error': 'No NPCs in current scenario'}), 400
    
    npc = session.npc_manager.get_npc(npc_id)
    if not npc:
        return jsonify({'error': f"NPC '{npc_id}' not found"}), 404
    
    # Calculate price modifier based on disposition
    level = npc.get_disposition_level()
    price_modifiers = {
        'hostile': None,  # Can't trade
        'unfriendly': 1.0,
        'neutral': 1.0,
        'friendly': 0.9,  # 10% discount
        'trusted': 0.8    # 20% discount
    }
    
    # Get available skill checks
    available_checks = []
    if hasattr(npc, 'skill_check_options') and npc.skill_check_options:
        for check in npc.get_available_skill_checks():
            available_checks.append({
                'id': check.id,
                'skill': check.skill,
                'dc': check.dc,
                'description': check.description
            })
    
    # Get role value safely
    role_value = ''
    if hasattr(npc, 'role'):
        if hasattr(npc.role, 'value'):
            role_value = npc.role.value
        elif hasattr(npc.role, 'name'):
            role_value = npc.role.name
        else:
            role_value = str(npc.role)
    
    return jsonify({
        'success': True,
        'npc': {
            'id': npc.id,
            'name': npc.name,
            'role': role_value,
            'disposition': npc.disposition,
            'level': level,
            'label': npc.get_disposition_label(),
            'can_trade': npc.can_trade(),
            'price_modifier': price_modifiers.get(level),
            'available_skill_checks': available_checks,
            'description': npc.description
        }
    })


# =============================================================================
# MORAL CHOICES ENDPOINTS (Phase 3.4)
# =============================================================================

@app.route('/api/choices/available', methods=['GET'])
def get_available_choices():
    """
    Get all currently available moral choices based on player's location and flags.
    
    Returns choices that can be triggered based on:
    - Current location matching choice trigger
    - Player flags matching choice trigger
    - Quest objectives completed
    """
    # Support both query param and header for session_id
    session_id = request.args.get('session_id') or request.headers.get('X-Session-ID')
    
    if not session_id or session_id not in game_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    session = game_sessions[session_id]
    
    if not session.choice_manager:
        return jsonify({'success': True, 'choices': [], 'message': 'No choice system in current scenario'})
    
    # Build player context for checking triggers
    player_context = {
        'location_id': getattr(session, 'current_location_id', None) or session.current_location,
        'flags': getattr(session, 'player_flags', {}),
        'completed_objectives': []
    }
    
    # Get completed quest objectives
    if session.quest_manager:
        for quest in session.quest_manager.get_all_quests():
            for obj in quest.objectives:
                if obj.current >= obj.required:
                    player_context['completed_objectives'].append(obj.id)
    
    # Check for triggered choices
    available = session.choice_manager.check_triggers(player_context)
    
    # Format choices for response
    choices_data = []
    for choice in available:
        # Check if already resolved
        if choice.id in session.choice_manager.choices_made:
            continue
            
        # Format options with availability
        options_data = []
        for i, option in enumerate(choice.options):
            option_available = True
            requirements = []
            
            # Check requirements
            if option.required_flag and option.required_flag not in player_context['flags']:
                option_available = False
                requirements.append(f"Requires: {option.required_flag}")
            
            if option.required_item and session.character:
                has_item = any(item.id == option.required_item for item in session.character.inventory)
                if not has_item:
                    option_available = False
                    requirements.append(f"Requires item: {option.required_item}")
            
            if option.min_disposition:
                # Check NPC disposition if needed
                requirements.append(f"Requires disposition: {option.min_disposition}")
            
            options_data.append({
                'index': i,
                'text': option.text,
                'available': option_available,
                'requirements': requirements,
                'skill_check': {
                    'skill': option.skill_check,
                    'dc': option.skill_dc
                } if option.skill_check else None
            })
        
        choices_data.append({
            'id': choice.id,
            'prompt': choice.prompt,
            'type': choice.type.value,
            'options': options_data,
            'time_limit': choice.time_limit
        })
    
    return jsonify({
        'success': True,
        'choices': choices_data,
        'player_context': {
            'location': player_context['location_id'],
            'flags': list(player_context['flags'].keys()) if isinstance(player_context['flags'], dict) else []
        }
    })


@app.route('/api/choices/select', methods=['POST'])
@app.route('/api/choices/<choice_id>/select', methods=['POST'])
def select_choice(choice_id=None):
    """
    Select an option for a moral choice.
    
    Applies consequences:
    - XP rewards
    - Gold changes
    - Item rewards
    - Flag changes
    - Disposition changes
    - Ending points
    """
    data = request.get_json() or {}
    # Support both query param, header, and body for session_id
    session_id = data.get('session_id') or request.headers.get('X-Session-ID')
    # Get choice_id from path or body
    choice_id = choice_id or data.get('choice_id')
    # Frontend sends option_id, backend expects option_index
    option_index = data.get('option_index') or data.get('option_id')
    
    if not session_id or session_id not in game_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    if choice_id is None or option_index is None:
        return jsonify({'error': 'choice_id and option_index required'}), 400
    
    session = game_sessions[session_id]
    
    if not session.choice_manager:
        return jsonify({'error': 'No choice system in current scenario'}), 400
    
    # Get player context for skill checks
    player_context = {
        'flags': getattr(session, 'player_flags', {})
    }
    
    # Get character stats for skill checks
    if session.character:
        player_context['stats'] = {
            'strength': session.character.strength,
            'dexterity': session.character.dexterity,
            'constitution': session.character.constitution,
            'intelligence': session.character.intelligence,
            'wisdom': session.character.wisdom,
            'charisma': session.character.charisma
        }
    
    try:
        result = session.choice_manager.select_option(choice_id, option_index, player_context)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    
    # Apply consequences
    rewards = {'xp': 0, 'gold': 0, 'items': []}
    
    if result['consequence']:
        consequence = result['consequence']
        
        # Apply XP reward
        if consequence.xp_reward and session.character:
            session.character.gain_xp(consequence.xp_reward, f"Choice: {choice_id}")
            rewards['xp'] = consequence.xp_reward
        
        # Apply gold change
        if consequence.gold_change and session.character:
            session.character.gold += consequence.gold_change
            rewards['gold'] = consequence.gold_change
        
        # Apply item rewards
        if consequence.item_rewards and session.character:
            for item_id in consequence.item_rewards:
                item = get_item(item_id)
                if item:
                    add_item_to_inventory(session.character, item)
                    rewards['items'].append(item.name)
        
        # Apply flag changes
        if consequence.flag_changes:
            if not hasattr(session, 'player_flags'):
                session.player_flags = {}
            session.player_flags.update(consequence.flag_changes)
        
        # Apply disposition changes
        if consequence.disposition_changes and session.npc_manager:
            for npc_id, change in consequence.disposition_changes.items():
                npc = session.npc_manager.get_npc(npc_id)
                if npc:
                    npc.modify_disposition(change)
    
    return jsonify({
        'success': True,
        'choice_id': choice_id,
        'selected_option': result['option'].text,
        'skill_check': result.get('skill_check'),
        'rewards': rewards,
        'narrative': result.get('narrative', f"You chose: {result['option'].text}"),
        'ending_points': session.choice_manager.ending_points,
        'game_state': session.to_dict()
    })


@app.route('/api/choices/history', methods=['GET'])
def get_choice_history():
    """
    Get the history of choices made in this session.
    Useful for showing player their moral path.
    """
    # Support both query param and header for session_id
    session_id = request.args.get('session_id') or request.headers.get('X-Session-ID')
    
    if not session_id or session_id not in game_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    session = game_sessions[session_id]
    
    if not session.choice_manager:
        return jsonify({'success': True, 'history': [], 'ending_points': {}})
    
    history = []
    for choice_id, option_index in session.choice_manager.choices_made.items():
        choice = session.choice_manager.get_choice(choice_id)
        if choice and 0 <= option_index < len(choice.options):
            option = choice.options[option_index]
            history.append({
                'choice_id': choice_id,
                'prompt': choice.prompt,
                'type': choice.type.value,
                'selected_option': option.text,
                'option_index': option_index
            })
    
    return jsonify({
        'success': True,
        'history': history,
        'ending_points': session.choice_manager.ending_points,
        'total_choices': len(history)
    })


@app.route('/api/choices/ending', methods=['GET'])
def get_ending_status():
    """
    Get the current ending trajectory based on choices made.
    Returns the likely ending based on accumulated ending points.
    """
    # Support both query param and header for session_id
    session_id = request.args.get('session_id') or request.headers.get('X-Session-ID')
    
    if not session_id or session_id not in game_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    session = game_sessions[session_id]
    
    if not session.choice_manager:
        return jsonify({'success': True, 'ending': None, 'points': {}})
    
    ending = session.choice_manager.determine_ending()
    
    return jsonify({
        'success': True,
        'ending': ending,
        'ending_points': session.choice_manager.ending_points,
        'choices_made': len(session.choice_manager.choices_made)
    })


# =============================================================================
# ROOT ENDPOINT - API INFO
# =============================================================================

@app.route('/')
def api_info():
    """Return API info since we're not serving a frontend here."""
    return jsonify({
        'name': 'AI D&D RPG API',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'health': '/api/health',
            'start_game': '/api/game/start',
            'game_action': '/api/game/action',
            'scenarios': '/api/scenarios'
        },
        'frontend': 'Run React frontend separately at http://localhost:3000'
    })


@app.route('/api/sessions/stats', methods=['GET'])
def get_session_stats():
    """Get session statistics for monitoring."""
    now = datetime.now()
    session_info = []
    
    for session_id, session in game_sessions.items():
        inactive_seconds = (now - session.last_activity).total_seconds()
        session_info.append({
            'session_id': session_id[:8] + '...',  # Truncate for privacy
            'character_name': session.character.name if session.character else None,
            'created_at': session.created_at.isoformat(),
            'last_activity': session.last_activity.isoformat(),
            'inactive_seconds': int(inactive_seconds),
            'in_combat': session.in_combat
        })
    
    return jsonify({
        'active_sessions': len(game_sessions),
        'session_timeout_minutes': SESSION_TIMEOUT_MINUTES,
        'sessions': session_info
    })


@app.route('/api/game/end', methods=['POST'])
def end_game():
    """Explicitly end a game session and clean up resources."""
    data = request.get_json() or {}
    session_id = data.get('session_id')
    
    if not session_id:
        return jsonify({'error': 'No session_id provided'}), 400
    
    if session_id not in game_sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    with session_lock:
        del game_sessions[session_id]
    
    print(f"🗑️ Session {session_id[:8]}... ended by user request")
    
    return jsonify({
        'success': True,
        'message': 'Session ended successfully'
    })


if __name__ == '__main__':
    port = int(os.getenv('API_PORT', 5000))
    debug = os.getenv('DEBUG', 'true').lower() == 'true'
    
    print(f"🎲 AI RPG API Server starting on http://localhost:{port}")
    print(f"   Debug mode: {debug}")
    print(f"   API Key configured: {'Yes' if os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY') else 'No'}")
    print(f"\n   📡 API endpoints available at http://localhost:{port}/api/*")
    print(f"   🌐 React frontend runs separately at http://localhost:3000")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
