"""
AI RPG API Server
Flask-based REST API that bridges the Flutter frontend with the game engine.
Also serves the Flutter web app for same-origin requests.
"""

import os
import sys
import json
import re
import uuid
import threading
import time
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Optional
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from dotenv import load_dotenv

# Log lines contain emoji; a Windows console or pipe defaults to cp1252 and
# would crash the server on the first print. Never let logging kill a request.
for _stream in (sys.stdout, sys.stderr):
    try:
        # line_buffering: logs show up immediately when stdout is a pipe
        _stream.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    except (AttributeError, ValueError):
        pass

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from character import Character, CLASSES, RACES
from scenario import ScenarioManager, LocationManager
from scenario_loader import register_quests
from npc import NPCManager
from quest import QuestManager
from combat import (
    ENEMIES
)
from inventory import get_item, add_item_to_inventory
from save_system import SaveManager
from party import Party
from dm_scene import (
    build_survey_dm_instruction,
    build_roll_outcome_instruction,
)
from game_mechanics import (
    run_party_ally_attacks,
    serialize_session_state,
    restore_session_state,
    sync_session_from_scenario,
    get_class_hit_die,
    is_thin_legacy_save,
    apply_player_damage,
    on_player_defeat,
    is_session_blocked,
    process_travel,
)

from text_match import has_any
from turn_service import (
    start_turn,
    finish_turn,
    message_text,
    detect_npc_talk,  # noqa: F401  (re-exported; tests import it from here)
    detect_quest_acceptance,  # noqa: F401
)

# Import from shared DM engine (single source of truth)
from dm_engine import (
    build_full_dm_context, StreamTagFilter,
)


def safe_json_sse(data: dict) -> str:
    """Serialize an SSE payload; never raise — broken JSON must not kill the stream."""
    try:
        return f"data: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"
    except Exception as exc:
        print(f"⚠️ SSE JSON encode failed: {exc}")
        minimal = {'type': data.get('type', 'error'), 'message': 'Serialization error'}
        return f"data: {json.dumps(minimal)}\n\n"


# Load .env from project root (parent of src/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(PROJECT_ROOT, '.env')
load_dotenv(ENV_PATH)
load_dotenv(os.path.join(PROJECT_ROOT, '.env.local'), override=True)


def get_skill_hint(player_action: str) -> str:
    """
    Add skill check hints based on player action keywords.
    Helps the AI know when to request skill checks.
    """
    # Specific search only — vague "look around" gets free survey (no roll hint)
    from dm_scene import classify_exploration_action
    if classify_exploration_action(player_action) == "specific_search":
        return (
            "\n[HINT: The player is searching for something specific. "
            "The skill check (if any) is handled by the arbiter — do NOT add [ROLL:] tags "
            "unless the arbiter did not resolve one. Narrate the outcome.]"
        )
    
    # Stealth triggers
    stealth_words = ["sneak", "hide", "quietly", "stealthily", "creep", "silently", "lurk"]
    if has_any(player_action, stealth_words):
        return "\n[HINT: This is a stealth action. Call for a Stealth check (DC 10-15) to determine success.]"
    
    # Social triggers - Persuasion
    persuade_words = ["convince", "persuade", "ask for", "request", "plead", "negotiate", "bargain", "deposit", "advance", "upfront"]
    if has_any(player_action, persuade_words):
        return "\n[HINT: This is a social action. Consider calling for a Persuasion check (DC 10-15).]"
    
    # Social triggers - Intimidation
    intimidate_words = ["threaten", "intimidate", "demand", "scare", "menace", "warn"]
    if has_any(player_action, intimidate_words):
        return "\n[HINT: This is an intimidation attempt. Consider calling for an Intimidation check (DC 12-18).]"
    
    # Social triggers - Deception
    deception_words = ["lie", "bluff", "deceive", "trick", "fool", "pretend", "fake", "disguise"]
    if has_any(player_action, deception_words):
        return "\n[HINT: This is a deception attempt. Consider calling for a Deception check (DC 12-18).]"
    
    # Social triggers - Insight (reading people)
    insight_words = ["read", "sense motive", "tell if", "lying", "trust", "believe", "suspicious"]
    if has_any(player_action, insight_words):
        return "\n[HINT: The player is trying to read someone. Consider calling for an Insight check (DC 10-15).]"
    
    # Physical triggers
    physical_words = ["climb", "jump", "break", "force", "push", "lift", "swim", "run"]
    if has_any(player_action, physical_words):
        return "\n[HINT: This is a physical action. Consider calling for an Athletics check (DC 10-15).]"
    
    return ""


app = Flask(__name__)
app.json.ensure_ascii = False  # Allow non-ASCII (emojis) in JSON
# The React dev server proxies /api (same origin), so CORS is only needed for
# clients served from another origin. Override with a comma-separated list.
CORS_ORIGINS = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
    if o.strip()
]
CORS(app, resources={r"/api/*": {"origins": CORS_ORIGINS}})

MAX_ACTION_LENGTH = 1000  # characters; player actions go into LLM prompts

# Add request logging
@app.before_request
def log_request():
    if request.path.startswith('/api'):
        print(f"📥 {request.method} {request.path} from {request.remote_addr}")

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


ABILITIES = ("strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma")


def serialize_character(character):
    """Character as JSON-ready dict, plus derived stats the UI shows."""
    if not character:
        return None
    from combat import calculate_attack_bonus, get_weapon_stats
    from character import XP_THRESHOLDS

    char_dict = asdict(character)
    serialized_inventory = []
    for item in character.inventory:
        if isinstance(item, dict):
            item = dict(item)
            for key in ('item_type', 'rarity'):
                if hasattr(item.get(key), 'value'):
                    item[key] = item[key].value
            serialized_inventory.append(item)
            continue
        serialized_inventory.append({
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
        })
    char_dict['inventory'] = serialized_inventory

    weapon = resolve_equipped_weapon(character)
    char_dict['attack_bonus'] = calculate_attack_bonus(character, weapon)
    char_dict['weapon_damage'] = get_weapon_stats(weapon).get('damage')
    char_dict['proficiency_bonus'] = character.get_proficiency_bonus()
    char_dict['ability_modifiers'] = {a: character.get_ability_modifier(a) for a in ABILITIES}
    char_dict['next_level_xp'] = XP_THRESHOLDS.get(character.level + 1)
    return char_dict


def roll_new_character(name: str, race: str, char_class: str) -> Character:
    """Roll a level-1 character: 4d6-drop-lowest stats plus class gear and gold."""
    character = Character(
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
    character._add_starting_equipment()
    return character


def validate_character_request(char_data):
    """Returns (name, race, char_class, error_response)."""
    if not isinstance(char_data, dict):
        char_data = {}
    name = char_data.get('name', '')
    race = char_data.get('race', 'Human')
    char_class = char_data.get('class', 'Fighter')
    if not isinstance(name, str) or not name.strip():
        return None, None, None, (jsonify({'error': 'Character name is required'}), 400)
    name = name.strip()
    MAX_NAME_LENGTH = 50
    if len(name) > MAX_NAME_LENGTH:
        return None, None, None, (jsonify({'error': f'Character name too long (max {MAX_NAME_LENGTH} characters)'}), 400)
    if race not in RACES:
        race = 'Human'
    if char_class not in CLASSES:
        char_class = 'Fighter'
    return name, race, char_class, None


# Characters rolled by /api/character/preview, waiting for /api/game/start.
# Keyed by an unguessable token so the stats shown are the stats played.
PREVIEW_TTL_SECONDS = 30 * 60
MAX_PENDING_PREVIEWS = 1000
pending_previews = {}  # token -> (Character, created_at)
pending_previews_lock = threading.Lock()


def _prune_previews(now: float) -> None:
    expired = [t for t, (_, created) in pending_previews.items() if now - created > PREVIEW_TTL_SECONDS]
    for token in expired:
        del pending_previews[token]
    while len(pending_previews) >= MAX_PENDING_PREVIEWS:
        oldest = min(pending_previews, key=lambda t: pending_previews[t][1])
        del pending_previews[oldest]


class GameSession:
    """Represents an active game session."""
    
    # Game over threshold for social failures
    MAX_SOCIAL_FAILURES = 3
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.character = None
        self.scenario = None
        self.npc_manager = None
        self.shop_manager = None  # Shop stock / haggle state (persisted in saves)
        self.quest_manager = None
        self.location_manager = None
        self.party = None
        self.messages = []
        self.current_location = None
        self.current_location_id = None
        self.in_combat = False
        self.combat_state = None
        self.created_at = datetime.now()
        self.last_activity = datetime.now()  # Track last activity for session cleanup
        self.dm_model = None
        self.dm_chat = None  # Chat session for stateful conversation
        self.dm_unavailable = False  # Last narration failed: the LLM couldn't be reached
        self.previous_location_id = None  # Last place travelled from (flee destination)
        self.dm_notes = []  # Facts the DM must learn on its next turn (e.g. combat results)
        
        # Social check tracking (retry prevention + game over)
        self.failed_social_checks = 0  # Total failed social checks
        self.last_social_check_npc = None  # NPC involved in last social check
        self.last_social_check_skill = None  # Skill used in last social check
        self.social_check_blocked_npcs = set()  # NPCs who won't talk to player anymore
        self.game_over = False
        self.game_over_reason = None
        self.scene_state = {}  # Per-location survey counts, scene memory
    
    def touch(self):
        """Update last_activity timestamp to prevent session expiration."""
        self.last_activity = datetime.now()
    
    def record_social_failure(self, npc_context: str = None, skill: str = None):
        """Record a failed social check and check for game over."""
        self.failed_social_checks += 1
        self.last_social_check_npc = npc_context
        self.last_social_check_skill = skill
        
        # After 2 failures with same NPC context, block that NPC
        if npc_context:
            self.social_check_blocked_npcs.add(npc_context)
        
        # Check for game over
        if self.failed_social_checks >= self.MAX_SOCIAL_FAILURES:
            self.game_over = True
            self.game_over_reason = "You've alienated too many people. Word has spread about your difficult nature, and no one in town will deal with you. Your adventure ends here."
        
        return {
            'failures': self.failed_social_checks,
            'max_failures': self.MAX_SOCIAL_FAILURES,
            'game_over': self.game_over,
            'warning': self.failed_social_checks == self.MAX_SOCIAL_FAILURES - 1
        }
    
    def is_social_retry_blocked(self, npc_context: str = None, skill: str = None) -> tuple[bool, str]:
        """
        Check if a social check should be blocked (retry prevention).
        Returns (blocked, reason).
        """
        # Game over - all actions blocked
        if self.game_over:
            return (True, "game_over")
        
        # Same NPC + same skill = blocked retry
        if (npc_context and skill and 
            npc_context == self.last_social_check_npc and 
            skill == self.last_social_check_skill):
            return (True, "same_approach")
        
        # NPC has rejected player entirely
        if npc_context and npc_context in self.social_check_blocked_npcs:
            return (True, "npc_hostile")
        
        return (False, None)
    
    def get_social_warning(self) -> Optional[str]:
        """Get warning message if player is close to game over."""
        if self.failed_social_checks == self.MAX_SOCIAL_FAILURES - 1:
            return "⚠️ **Warning:** You've failed multiple social checks. One more failure may end your adventure."
        return None
    
    def _serialize_character(self):
        return serialize_character(self.character)

    def to_dict(self):
        """Convert session to dictionary for JSON response."""
        party_members = []
        if self.party and self.party.members:
            for m in self.party.members:
                party_members.append({
                    'id': m.id,
                    'name': m.name,
                    'class': m.char_class.value if hasattr(m.char_class, 'value') else str(m.char_class),
                    'hp': m.current_hp,
                    'max_hp': m.max_hp,
                })
        return {
            'session_id': self.session_id,
            'character': self._serialize_character(),
            'current_location': self.current_location,
            'current_location_id': self.current_location_id,
            'in_combat': self.in_combat,
            'messages': self.messages[-50:],  # Last 50 messages
            'quest_log': self._get_quest_log(),
            'party': party_members,
            'game_over': self.game_over,
            'game_over_reason': self.game_over_reason,
            'dm_unavailable': self.dm_unavailable,
        }
    
    def _get_quest_log(self):
        """Get active quests."""
        if not self.quest_manager:
            return []
        return [q.to_dict() for q in self.quest_manager.get_active_quests()]


# Quest kill targets may use different ids than combat presets (goblin_chief vs goblin_boss)
ENEMY_KILL_ALIASES = {
    'goblin_boss': ['goblin_boss', 'goblin_chief'],
}


def ensure_combat_enemies(session: GameSession):
    """Materialize Enemy objects from combat_state enemy type list."""
    from combat import create_enemy

    if session.combat_state is None:
        session.combat_state = {}
    if session.combat_state.get('enemy_objects'):
        return session.combat_state['enemy_objects']

    session.combat_state['enemy_objects'] = []
    for enemy_type in session.combat_state.get('enemies', []):
        enemy = create_enemy(enemy_type.lower().replace(' ', '_'))
        if enemy:
            session.combat_state['enemy_objects'].append(enemy)
    return session.combat_state['enemy_objects']


def build_combat_status_payload(session: GameSession) -> dict:
    """JSON payload for combat status (shared by status + attack endpoints)."""
    if not session.in_combat:
        return {
            'success': True,
            'in_combat': False,
            'active': False,
            'message': 'Not in combat',
        }

    enemies = ensure_combat_enemies(session)
    enemies_status = []
    for enemy in enemies:
        enemies_status.append({
            'name': enemy.name,
            'current_hp': enemy.current_hp,
            'max_hp': enemy.max_hp,
            'hp': enemy.current_hp,
            'is_dead': enemy.is_dead,
            'status': enemy.get_status(),
        })

    return {
        'success': True,
        'in_combat': True,
        'active': True,
        'round': session.combat_state.get('round', 1),
        'surprise': session.combat_state.get('surprise', False),
        'enemies': enemies_status,
        'player_hp': session.character.current_hp if session.character else 0,
        'player_max_hp': session.character.max_hp if session.character else 0,
    }


def resolve_equipped_weapon(character):
    """
    Return the weapon to attack with: the equipped inventory Item when present
    (so quality bonuses like "1d12+3" apply), else a WEAPONS table key.
    """
    from combat import WEAPONS, weapon_base_key

    name = (character.weapon if character and character.weapon else 'longsword')
    weapons = [i for i in (character.inventory if character else []) if getattr(i, 'damage_dice', None)]
    for item in weapons:
        if item.name.lower() == name.lower():
            return item
    key = weapon_base_key(name)
    if key in WEAPONS:
        return key
    for item in weapons:
        if weapon_base_key(item.name) in WEAPONS:
            return item
    return 'longsword'


def quest_kills_for_enemy(enemy) -> list:
    """Enemy type ids to report to quest manager on kill."""
    primary = getattr(enemy, 'enemy_type', None) or enemy.name.lower().replace(' ', '_')
    ids = [primary]
    for alias in ENEMY_KILL_ALIASES.get(primary, []):
        if alias not in ids:
            ids.append(alias)
    return ids


def record_quest_kill(session: GameSession, enemy, result_messages: list) -> None:
    """Credit a kill to quest objectives once, whoever landed the blow."""
    if getattr(enemy, 'kill_recorded', False) or not session.quest_manager:
        return
    enemy.kill_recorded = True
    for enemy_id in quest_kills_for_enemy(enemy):
        for _quest_id, obj in session.quest_manager.on_enemy_killed(enemy_id):
            result_messages.append(f"📜 Quest Objective Complete: {obj.description}")


def apply_combat_victory(session: GameSession, enemies: list, result_messages: list) -> dict:
    """Grant XP, gold, loot, and boss hit-dice restore after combat victory."""
    from combat import get_enemy_loot_for_class
    from inventory import get_item, add_item_to_inventory

    rewards = {'xp': 0, 'gold': 0, 'items': []}
    boss_killed = False
    fallen = [e.name for e in enemies if e.is_dead]
    for enemy in enemies:
        if enemy.is_dead:
            record_quest_kill(session, enemy, result_messages)  # allies' kills count too
    if fallen:
        session.dm_notes.append(
            f"The party won a fight and killed: {', '.join(fallen)}. They are dead and stay dead."
        )

    for enemy in enemies:
        if not enemy.is_dead:
            continue
        rewards['xp'] += enemy.xp_reward
        rewards['gold'] += enemy.gold_drop
        etype = getattr(enemy, 'enemy_type', '') or enemy.name.lower()
        if 'boss' in etype or 'chief' in etype:
            boss_killed = True
        if session.character:
            loot_items, _ = get_enemy_loot_for_class(
                getattr(enemy, 'enemy_type', None) or etype,
                session.character.char_class,
            )
            for item_name in loot_items:
                item = get_item(item_name)
                if item:
                    add_item_to_inventory(session.character.inventory, item)
                    rewards['items'].append(item.name)
                    result_messages.append(f"📦 Looted: {item.name}")

    if session.character:
        if rewards['xp'] > 0:
            session.character.gain_xp(rewards['xp'], 'combat victory')
            result_messages.append(f"⭐ Gained {rewards['xp']} XP!")
        if rewards['gold'] > 0:
            session.character.gold += rewards['gold']
            result_messages.append(f"💰 Looted {rewards['gold']} gold!")
        if boss_killed:
            if session.combat_state is None:
                session.combat_state = {}
            session.combat_state['hit_dice_remaining'] = session.character.level
            result_messages.append('🎲 Hit dice restored after boss victory!')

    # Story objectives that depend on winning a fight are completed by the
    # combat result, never by keywords in the DM's prose.
    scenario = session.scenario.active_scenario if session.scenario else None
    if scenario and any(enemy.is_dead for enemy in enemies):
        scenario.complete_objective('deal_with_goblins')
        if boss_killed:
            scenario.complete_objective('defeat_chief')

    from game_mechanics import complete_ready_quests
    result_messages.extend(complete_ready_quests(session))

    return rewards


def run_enemy_turn(session: GameSession, living_enemies: list, result_messages: list,
                   ac_override: int = None, halve_player_damage: bool = False) -> bool:
    """
    Each enemy attacks the player or a living party member, chosen at random,
    so companions share the danger. Returns True if the player died.
    Skips attacks when player ambushed (surprise) on round 1.
    ``ac_override`` / ``halve_player_damage`` apply to the player (Defend).
    """
    import random
    from combat import enemy_attack, format_enemy_attack

    surprise = (
        session.combat_state.get('surprise', False)
        and session.combat_state.get('round', 1) == 1
    )
    if surprise:
        result_messages.append('\n⚡ Enemies are surprised and cannot act this round!')
        return False

    result_messages.append('\n--- Enemy Turn ---')
    player_ac = ac_override if ac_override is not None else session.character.armor_class
    for enemy in living_enemies:
        allies = session.party.get_alive_members() if session.party else []
        target = random.choice([None] + allies)  # None = the player
        if target is not None:
            enemy_atk, enemy_dmg = enemy_attack(enemy, target.armor_class)
            verdict = '✅ HIT!' if enemy_atk['hit'] else '❌ MISS'
            result_messages.append(
                f"👹 {enemy.name} attacks {target.name}: [{enemy_atk['d20_roll']}]+{enemy_atk['attack_bonus']}"
                f" = {enemy_atk['total']} vs AC {target.armor_class} = {verdict}"
            )
            if enemy_dmg:
                result_messages.append(f"   {target.take_damage(enemy_dmg['total'])}")
            continue

        enemy_atk, enemy_dmg = enemy_attack(enemy, player_ac)
        result_messages.append(format_enemy_attack(enemy_atk, enemy_dmg))
        if enemy_dmg:
            damage = enemy_dmg['total']
            if halve_player_damage:
                damage = max(1, damage // 2)
                result_messages.append(f"   (Reduced to {damage} damage)")
            _, defeated = apply_player_damage(session, damage, enemy.name)
            if defeated:
                return True
    return False


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
    """Initialize the AI model for DM responses (Gemini or vLLM)."""
    if session.dm_model:
        return session.dm_model

    from llm_client import create_dm_model, get_llm_provider, is_llm_configured

    if not is_llm_configured():
        print(f"   ❌ LLM not configured for provider: {get_llm_provider()}")
        print(f"   📁 .env path: {ENV_PATH}")
        print(f"   📁 .env exists: {os.path.exists(ENV_PATH)}")
        return None

    try:
        session.dm_model = create_dm_model()
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
    if session.dm_notes:
        # Things that happened outside narration (fights resolved by the rules engine)
        notes = "\n".join(f"- {note}" for note in session.dm_notes)
        context_update += f"\n\n[SINCE YOUR LAST NARRATION - these are facts, narrate consistently:]\n{notes}"
        session.dm_notes = []
    
    return context_update


def get_dm_response(
    session: GameSession,
    player_action: str,
    is_opening: bool = False,
    max_retries: int = 3,
    pre_roll_result: dict = None,
    scene_action: str = None,
    arbiter_no_roll: bool = False,
) -> str:
    """
    Get AI DM response for player action (non-streaming) using chat session.
    
    Args:
        session: Game session
        player_action: The player's action text
        is_opening: Whether this is the opening narration
        max_retries: Number of retries for API errors
        pre_roll_result: If provided, the skill check result (from two-phase arbiter system)
                        This tells the DM what the roll result was so it can narrate appropriately.
    """
    import time
    
    session.dm_unavailable = False
    chat = init_dm_chat(session)
    
    if not chat:
        # Fallback responses when no API key
        return get_fallback_response(session, player_action, is_opening)
    
    # Build the message with context refresh + action + skill hints
    context_refresh = refresh_chat_context(session)
    skill_hint = get_skill_hint(player_action)
    
    # If we have a pre-resolved skill check result, include it in the message
    if pre_roll_result:
        is_social = pre_roll_result.get('action_type') == 'social'
        is_failure = not pre_roll_result['success']
        
        # Add "push your luck" warning for social failures
        push_luck_warning = ""
        if is_social and is_failure:
            push_luck_warning = """

IMPORTANT: Since this was a FAILED social check, end your narration with a subtle hint that pushing their luck further with this NPC/approach would be unwise. Examples:
- "Something in their eyes tells you that pressing further would only make things worse."
- "You sense that any more demands would sour the situation beyond repair."
- "The moment for negotiation seems to be slipping away."
Do NOT be too heavy-handed - just a subtle narrative hint."""
        
        roll_instruction = f"""
[SKILL CHECK ALREADY RESOLVED - DO NOT request another roll]
The player attempted: {player_action}
Skill Check Result: {pre_roll_result['skill']} DC {pre_roll_result['dc']} - {"SUCCESS" if pre_roll_result['success'] else "FAILURE"}
Roll: {pre_roll_result['roll']} + {pre_roll_result['modifier']} = {pre_roll_result['total']}
{"🌟 CRITICAL SUCCESS (Natural 20)!" if pre_roll_result.get('is_nat_20') else ""}
{"💀 CRITICAL FAILURE (Natural 1)!" if pre_roll_result.get('is_nat_1') else ""}

NARRATE the {"positive" if pre_roll_result['success'] else "negative"} outcome of this check. Do NOT add [ROLL:] tags - the roll is already done.{push_luck_warning}"""
        outcome_rules = build_roll_outcome_instruction(player_action, pre_roll_result)
        full_message = f"{context_refresh}\n\n{roll_instruction}{outcome_rules}"
    elif scene_action == "survey_first":
        survey_instruction = build_survey_dm_instruction(session)
        full_message = (
            f"{context_refresh}\n\n{survey_instruction}\n\n"
            f"Player action: {player_action}"
        )
    else:
        no_roll_note = ""
        if arbiter_no_roll:
            no_roll_note = (
                "\n[ARBITER: No skill check needed for this action. "
                "Do NOT add [ROLL:] tags. Narrate freely.]"
            )
        full_message = f"{context_refresh}\n\nPlayer action: {player_action}{skill_hint}{no_roll_note}"
    
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


def stream_dm_response(
    session: GameSession,
    player_action: str,
    max_retries: int = 3,
    pre_roll_result: dict = None,
    scene_action: str = None,
    arbiter_no_roll: bool = False,
):
    """
    Generator that yields streaming DM response chunks using chat session.
    
    Args:
        session: Game session
        player_action: The player's action text
        max_retries: Number of retries for API errors
        pre_roll_result: If provided, the skill check result (from two-phase arbiter system)
    """
    import time
    
    session.dm_unavailable = False
    chat = init_dm_chat(session)
    
    if not chat:
        yield get_fallback_response(session, player_action, False)
        return
    
    # Build the message with context refresh + action + skill hints
    # Only include context updates periodically or when state changes significantly
    context_refresh = refresh_chat_context(session)
    skill_hint = get_skill_hint(player_action)
    
    # If we have a pre-resolved skill check result, include it in the message
    if pre_roll_result:
        is_social = pre_roll_result.get('action_type') == 'social'
        is_failure = not pre_roll_result['success']
        
        # Add "push your luck" warning for social failures
        push_luck_warning = ""
        if is_social and is_failure:
            push_luck_warning = """

IMPORTANT: Since this was a FAILED social check, end your narration with a subtle hint that pushing their luck further with this NPC/approach would be unwise. Examples:
- "Something in their eyes tells you that pressing further would only make things worse."
- "You sense that any more demands would sour the situation beyond repair."
- "The moment for negotiation seems to be slipping away."
Do NOT be too heavy-handed - just a subtle narrative hint."""
        
        roll_instruction = f"""
[SKILL CHECK ALREADY RESOLVED - DO NOT request another roll]
The player attempted: {player_action}
Skill Check Result: {pre_roll_result['skill']} DC {pre_roll_result['dc']} - {"SUCCESS" if pre_roll_result['success'] else "FAILURE"}
Roll: {pre_roll_result['roll']} + {pre_roll_result['modifier']} = {pre_roll_result['total']}
{"🌟 CRITICAL SUCCESS (Natural 20)!" if pre_roll_result.get('is_nat_20') else ""}
{"💀 CRITICAL FAILURE (Natural 1)!" if pre_roll_result.get('is_nat_1') else ""}

NARRATE the {"positive" if pre_roll_result['success'] else "negative"} outcome of this check. Do NOT add [ROLL:] tags - the roll is already done.{push_luck_warning}"""
        outcome_rules = build_roll_outcome_instruction(player_action, pre_roll_result)
        full_message = f"{context_refresh}\n\n{roll_instruction}{outcome_rules}"
    elif scene_action == "survey_first":
        survey_instruction = build_survey_dm_instruction(session)
        full_message = (
            f"{context_refresh}\n\n{survey_instruction}\n\n"
            f"Player action: {player_action}"
        )
    else:
        no_roll_note = ""
        if arbiter_no_roll:
            no_roll_note = (
                "\n[ARBITER: No skill check needed for this action. "
                "Do NOT add [ROLL:] tags. Narrate freely.]"
            )
        full_message = f"{context_refresh}\n\nPlayer action: {player_action}{skill_hint}{no_roll_note}"
    
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
                session.dm_unavailable = True
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
    """
    Player-facing narration when the LLM can't be reached.

    The configuration checklist goes to the server log, not the story; the
    session is flagged so the UI can offer to retry the action.
    """
    from llm_client import get_llm_provider

    session.dm_unavailable = True
    if get_llm_provider() == "vllm":
        config_help = (
            "VLLM_BASE_URL is set and reachable; VLLM_MODEL matches the served model; "
            "the vLLM server is running"
        )
    else:
        config_help = "GOOGLE_API_KEY is set and valid; GEMINI_MODEL is correct"
    print(f"   ⚠️ DM unavailable ({get_llm_provider()}): check {config_help}")

    # Atmosphere only: the UI shows the plain explanation and a retry button
    if is_opening:
        return "*The lamplight gutters, and the storyteller has not yet taken their seat.*"
    return "*The lamplight gutters, and the Dungeon Master falls silent.*"


# =============================================================================
# API ROUTES
# =============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'version': '1.2.0',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/character/preview', methods=['POST'])
def preview_character():
    """Roll a character for review before the game starts (see /api/game/start)."""
    data = request.get_json(silent=True) or {}
    name, race, char_class, error = validate_character_request(data.get('character', {}))
    if error:
        return error

    character = roll_new_character(name, race, char_class)
    token = uuid.uuid4().hex
    now = time.time()
    with pending_previews_lock:
        _prune_previews(now)
        pending_previews[token] = (character, now)

    return jsonify({
        'success': True,
        'preview_token': token,
        'character': serialize_character(character),
    })


@app.route('/api/game/start', methods=['POST'])
def start_game():
    """Start a new game session."""
    data = request.get_json() or {}
    
    session_id = data.get('session_id')
    session = get_or_create_session(session_id)
    
    # Create character: reuse the previewed roll when the client confirms one
    name, race, char_class, error = validate_character_request(data.get('character', {}))
    if error:
        return error

    previewed = None
    token = data.get('preview_token')
    if isinstance(token, str):
        with pending_previews_lock:
            entry = pending_previews.pop(token, None)
        if entry and time.time() - entry[1] <= PREVIEW_TTL_SECONDS:
            candidate = entry[0]
            if (candidate.name, candidate.race, candidate.char_class) == (name, race, char_class):
                previewed = candidate
    session.character = previewed or roll_new_character(name, race, char_class)
    
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
            
            # Initialize quests for the scenario (from data/scenarios/<id>/quests.yaml)
            register_quests(scenario_id, session.quest_manager)
            # Quests are now REGISTERED but NOT ACCEPTED: they're accepted when
            # the player agrees to help (see turn_service.detect_quest_acceptance)

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
    
    return jsonify({
        'success': True,
        'session_id': session.session_id,
        'message': welcome,
        'game_state': session.to_dict()
    })


def _parse_action_request():
    """Validate an action request. Returns (session, action, error_response)."""
    data = request.get_json(silent=True) or {}
    session_id = data.get('session_id')
    raw_action = data.get('action', '')

    if not isinstance(raw_action, str):
        return None, None, (jsonify({'error': 'Action must be a string'}), 400)
    if len(raw_action) > MAX_ACTION_LENGTH:
        return None, None, (jsonify({'error': f'Action too long (max {MAX_ACTION_LENGTH} characters)'}), 400)

    action = raw_action.strip()
    if not session_id or session_id not in game_sessions:
        return None, None, (jsonify({'error': 'Invalid session'}), 400)
    if not action:
        return None, None, (jsonify({'error': 'No action provided'}), 400)

    return game_sessions[session_id], action, None


def _sse_response(events) -> Response:
    return Response(
        stream_with_context(events),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',
        },
    )


@app.route('/api/game/action', methods=['POST'])
def game_action():
    """Process a player action using two-phase AI (arbiter + narrator)."""
    session, action, error = _parse_action_request()
    if error:
        return error

    start = start_turn(session, action)
    if start.finished:
        return jsonify({
            'success': True,
            'message': message_text(start.events),
            **start.response,
            'game_state': session.to_dict(),
        })

    narrator_text = get_dm_response(
        session,
        action,
        pre_roll_result=start.arbiter_roll_result,
        scene_action=start.scene_action,
        arbiter_no_roll=start.arbiter_no_roll,
    )
    outcome = finish_turn(session, action, narrator_text, start)

    return jsonify({
        'success': True,
        # finish_turn records exactly what the player sees this turn
        'message': session.messages[-1]['content'],
        'roll_result': outcome.roll_result,
        'combat_started': outcome.combat_started,
        'items_gained': outcome.items_gained,
        'gold_gained': outcome.gold_gained,
        'xp_gained': outcome.xp_gained,
        'leveled_up': outcome.leveled_up,
        'quests_accepted': outcome.quests_accepted,
        'game_over': session.game_over,
        'social_failures': session.failed_social_checks,
        'game_state': session.to_dict(),
    })


@app.route('/api/game/action/stream', methods=['POST'])
def game_action_stream():
    """Process a player action with streaming response (Server-Sent Events)."""
    session, action, error = _parse_action_request()
    if error:
        return error

    start = start_turn(session, action)

    def done_event():
        return safe_json_sse({'type': 'done', 'game_state': session.to_dict(), 'game_over': session.game_over})

    def generate():
        for event in start.events:
            yield safe_json_sse(event)
        if start.finished:
            yield done_event()
            return

        # raw_narration keeps the narrator's unfiltered text (control tags
        # included) for mechanics; only tag-free text is sent to the player.
        raw_narration = []
        shown = []
        tag_filter = StreamTagFilter()
        try:
            for piece in stream_dm_response(
                session,
                action,
                pre_roll_result=start.arbiter_roll_result,
                scene_action=start.scene_action,
                arbiter_no_roll=start.arbiter_no_roll,
            ):
                raw_narration.append(piece)
                visible = tag_filter.feed(piece)
                if visible:
                    shown.append(visible)
                    yield safe_json_sse({'type': 'chunk', 'content': visible})
            tail = tag_filter.flush()
            if tail:
                shown.append(tail)
                yield safe_json_sse({'type': 'chunk', 'content': tail})

            outcome = finish_turn(session, action, ''.join(raw_narration), start,
                                  shown_narration=''.join(shown))
            for event in outcome.events:
                yield safe_json_sse(event)
            yield done_event()

        except Exception as e:
            # Never let a mid-stream error silently truncate the turn. Always
            # close out the stream so the client stops loading and stays usable.
            print(f"❌ Stream post-processing error: {e}")
            import traceback
            traceback.print_exc()
            yield safe_json_sse({'type': 'chunk', 'content': "\n\n*The threads of fate tangle for a moment. (Try your action again.)*"})
            try:
                yield done_event()
            except Exception:
                yield safe_json_sse({'type': 'done', 'game_state': None, 'game_over': False})

    return _sse_response(generate())


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
    save_name = data.get('name')
    if not save_name and data.get('slot') is not None:
        save_name = f"slot_{data.get('slot')}"
    if not save_name:
        save_name = 'quicksave'
    
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
    
    if not session.character:
        return jsonify({'error': 'No character to save'}), 400
    
    slot_num = data.get('slot')
    if slot_num is not None:
        # Slot ends up in the filename, so it must be a small integer.
        if isinstance(slot_num, bool) or not isinstance(slot_num, int) or not 0 <= slot_num <= 99:
            return jsonify({'error': 'Slot must be an integer between 0 and 99'}), 400
    if slot_num is None and save_name.startswith('slot_'):
        try:
            slot_num = int(save_name.replace('slot_', ''))
        except ValueError:
            slot_num = None
    
    saves_dir = os.path.join(os.path.dirname(__file__), '..', 'saves')
    os.makedirs(saves_dir, exist_ok=True)
    save_manager = SaveManager(saves_dir)
    
    filepath, message = save_manager.save_game(
        session.character,
        scenario_manager=session.scenario,
        quest_manager=session.quest_manager,
        chat_history=session.messages,
        slot=slot_num,
        description=data.get('description', ''),
        party=session.party,
        session_state=serialize_session_state(session),
    )
    
    if not filepath:
        return jsonify({'success': False, 'error': message}), 500
    
    return jsonify({
        'success': True,
        'message': message,
        'save_path': filepath,
        'name': os.path.basename(filepath)[:-5],
    })


SAVE_NAME_RE = re.compile(r'^[A-Za-z0-9_\- ]{1,100}$')


def _resolve_save_path(saves_dir: str, save_name: str) -> Optional[str]:
    """
    Resolve a save name to a file inside ``saves_dir``.

    Only a bare save name is honoured; any directory component the client
    sends (including a full path returned by an older /saves listing) is
    discarded, so a request can never reach a file outside ``saves_dir``.
    Returns None if the name is not a valid save name.
    """
    name = os.path.basename(str(save_name).replace('\\', '/'))
    if name.endswith('.json'):
        name = name[:-5]
    if not SAVE_NAME_RE.match(name):
        return None
    path = os.path.join(saves_dir, f"{name}.json")
    if os.path.exists(path):
        return path
    slot_match = re.match(r'slot_(\d+)$', name)
    if slot_match and os.path.isdir(saves_dir):
        slot_suffix = f"_slot{slot_match.group(1)}.json"
        for filename in os.listdir(saves_dir):
            if filename.endswith(slot_suffix):
                return os.path.join(saves_dir, filename)
    return path


@app.route('/api/game/load', methods=['POST'])
def load_game():
    """Load a saved game."""
    data = request.get_json() or {}
    save_name = data.get('name') or data.get('filepath')
    if not save_name:
        save_name = 'quicksave'
    
    saves_dir = os.path.join(os.path.dirname(__file__), '..', 'saves')
    save_path = _resolve_save_path(saves_dir, save_name)
    
    if not save_path or not os.path.exists(save_path):
        return jsonify({'error': 'Save not found'}), 404
    
    with open(save_path, 'r', encoding='utf-8') as f:
        save_data = json.load(f)
    
    session_id = str(uuid.uuid4())
    with session_lock:
        session = GameSession(session_id)
        game_sessions[session_id] = session
    
    session.dm_chat = None
    session.failed_social_checks = 0
    session.social_check_blocked_npcs = set()
    
    if is_thin_legacy_save(save_data):
        session.scenario = ScenarioManager()
        session.npc_manager = NPCManager()
        session.quest_manager = QuestManager()
        session.party = Party()
        session.location_manager = LocationManager()
        session.combat_state = None
        session.game_over = False
        
        if save_data.get('character'):
            session.character = Character.from_dict(save_data['character'])
        session.messages = save_data.get('messages', [])
        session.current_location = save_data.get('current_location', 'Village Square')
        session.current_location_id = save_data.get('current_location_id')
        session.in_combat = save_data.get('in_combat', False)
        if session.in_combat and save_data.get('combat_state'):
            session.combat_state = save_data.get('combat_state')
    else:
        save_manager = SaveManager(saves_dir)
        quest_manager = QuestManager()
        result = save_manager.load_game(
            save_path, Character, ScenarioManager, quest_manager, Party
        )
        if not result or not result.get('character'):
            return jsonify({'error': 'Failed to load save data'}), 500
        
        session.character = result['character']
        session.messages = result.get('chat_history', [])
        session.scenario = result.get('scenario_manager') or ScenarioManager()
        session.quest_manager = quest_manager
        session.party = result.get('party') or Party()
        session.npc_manager = NPCManager()
        session.location_manager = LocationManager()
        sync_session_from_scenario(session)
        restore_session_state(session, result.get('session_state'))
        # Saves hold quest progress, not quest definitions: re-register them so
        # quests not yet accepted can still be offered after loading
        if session.scenario and session.scenario.active_scenario:
            register_quests(session.scenario.active_scenario.id, session.quest_manager)
    
    return jsonify({
        'success': True,
        'message': f'Game loaded from {os.path.basename(save_path)}',
        'session_id': session.session_id,
        'game_state': session.to_dict()
    })


@app.route('/api/game/saves', methods=['GET'])
def list_saves():
    """List available saves."""
    saves_dir = os.path.join(os.path.dirname(__file__), '..', 'saves')
    
    if not os.path.exists(saves_dir):
        return jsonify({'success': True, 'saves': []})
    
    save_manager = SaveManager(saves_dir)
    saves, _errors = save_manager.list_saves()
    seen_paths = {s['filepath'] for s in saves}
    
    for filename in os.listdir(saves_dir):
        if not filename.endswith('.json') or filename.startswith('save_'):
            continue
        save_path = os.path.join(saves_dir, filename)
        if save_path in seen_paths:
            continue
        try:
            with open(save_path, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            char = save_data.get('character', {})
            saves.append({
                'filename': filename,
                'name': filename[:-5],
                'filepath': save_path,
                'timestamp': save_data.get('saved_at') or save_data.get('timestamp', ''),
                'character_name': char.get('name', 'Unknown'),
                'character_class': char.get('char_class') or char.get('class', 'Adventurer'),
                'character_level': char.get('level', 1),
                'description': save_data.get('description', ''),
            })
        except Exception:
            pass
    
    saves.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    # Clients load by filename; don't expose server filesystem paths
    for save in saves:
        save.pop('filepath', None)
    return jsonify({'success': True, 'saves': saves})


@app.route('/api/classes', methods=['GET'])
def get_classes():
    """Character classes with their starting kit (hit die, weapon, armor)."""
    from character import CLASS_HIT_DICE

    classes = []
    for name in CLASSES:
        # Build a throwaway level-1 character to read the real starting kit
        sample = Character(name='sample', race='Human', char_class=name)
        sample._add_starting_equipment()
        classes.append({
            'name': name,
            'hit_die': CLASS_HIT_DICE.get(name, 8),
            'weapon': sample.weapon.replace('_', ' ').title(),
            'armor': sample.equipped_armor.replace('_', ' ').title() if sample.equipped_armor else None,
        })
    return jsonify({'success': True, 'classes': classes})


@app.route('/api/races', methods=['GET'])
def get_races():
    """Get available character races."""
    return jsonify({
        'success': True,
        'races': list(RACES),
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
        # The location manager is the source of truth (the session's copy of
        # the id isn't set until the first travel)
        current_id = location.id if location else session.current_location_id

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
            # Secret places aren't on the map at all until found
            discovered = loc_id in session.location_manager.discovered_secrets
            if loc.map_hidden and not (loc.visited or discovered):
                continue
            # Known = visited, or part of the current scene; others are unnamed dots
            known = loc.visited or loc_id in session.location_manager.available_location_ids
            description = loc.description if known else ''

            all_locations.append({
                'id': loc_id,
                'name': loc.name if known else '???',
                'map_x': loc.map_x,
                'map_y': loc.map_y,
                'map_icon': loc.map_icon if known else '❓',
                'map_label': (loc.map_label or loc.name) if known else '???',
                'map_region': loc.map_region,
                'description': (
                    description if len(description) <= 200
                    else description[:200].rsplit(' ', 1)[0].rstrip(',;:') + '…'
                ),
                'known': known,
                'visited': loc.visited,
                'hidden': False,
                'is_current': loc_id == current_id,
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
    
    from game_mechanics import blocked_path_hint
    return jsonify({
        'success': True,
        'path_hint': blocked_path_hint(session),
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

    blocked, block_reason = is_session_blocked(session)
    if blocked:
        return jsonify({
            'success': False,
            'message': block_reason,
            'game_over': True,
            'game_state': session.to_dict(),
        }), 400

    result = process_travel(session, destination)

    if result.get('success'):
        session.messages.append({
            'type': 'dm',
            'content': result['message'],
            'timestamp': datetime.now().isoformat(),
        })
        payload = {
            'success': True,
            'message': result['message'],
            'new_location': result.get('new_location'),
            'events': result.get('events', []),
            'quest_updates': result.get('quest_updates', []),
            'in_combat': session.in_combat,
            'combat_started': result.get('combat_started', False),
            'game_over': session.game_over,
            'game_state': session.to_dict(),
        }
        if session.game_over:
            payload['game_over_reason'] = session.game_over_reason
        return jsonify(payload)

    return jsonify({
        'success': False,
        'message': result.get('message') or "You cannot go that way.",
        'game_over': result.get('game_over', False),
        'game_state': session.to_dict() if session.game_over else None,
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
    return jsonify(build_combat_status_payload(session))


@app.route('/api/combat/attack', methods=['POST'])
def combat_attack():
    """Player attacks an enemy."""
    from combat import roll_attack, roll_attack_with_advantage, roll_damage, format_attack_result, format_damage_result
    
    data = request.get_json() or {}
    session_id = data.get('session_id')
    target_index = data.get('target', data.get('target_index', 0))
    
    if not session_id or session_id not in game_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    session = game_sessions[session_id]
    
    if not session.in_combat:
        return jsonify({'error': 'Not in combat'}), 400
    
    if not session.character:
        return jsonify({'error': 'No character'}), 400
    
    enemies = ensure_combat_enemies(session)
    living_enemies = [e for e in enemies if not e.is_dead]
    
    if not living_enemies:
        session.in_combat = False
        return jsonify({
            'success': True,
            'combat_over': True,
            'victory': True,
            'message': '🎉 Victory! All enemies defeated!',
            'game_state': session.to_dict(),
            'combat_status': build_combat_status_payload(session),
        })
    
    try:
        target_index = int(target_index)
    except (TypeError, ValueError):
        target_index = 0
    if target_index >= len(living_enemies):
        target_index = 0
    target = living_enemies[target_index]
    
    weapon_name = resolve_equipped_weapon(session.character)
    
    has_surprise = session.combat_state.get('surprise', False) and session.combat_state.get('round', 1) == 1
    if has_surprise:
        attack = roll_attack_with_advantage(session.character, target.armor_class, weapon_name)
    else:
        attack = roll_attack(session.character, target.armor_class, weapon_name)
    
    result_messages = [format_attack_result(attack)]
    damage_dealt = 0
    target_killed = False
    
    if attack['hit']:
        damage = roll_damage(session.character, weapon_name, attack['is_crit'])
        damage_dealt = damage['total']
        result_messages.append(format_damage_result(damage))
        status_msg = target.take_damage(damage_dealt)
        result_messages.append(status_msg)
        target_killed = target.is_dead
        
        if target_killed:
            record_quest_kill(session, target, result_messages)
    
    living_enemies = [e for e in enemies if not e.is_dead]
    combat_over = len(living_enemies) == 0
    rewards = {'xp': 0, 'gold': 0, 'items': []}
    
    if combat_over:
        session.in_combat = False
        result_messages.append("\n🎉 **VICTORY!**")
        rewards = apply_combat_victory(session, enemies, result_messages)
    else:
        living_enemies = run_party_ally_attacks(session, living_enemies, result_messages)
        living_enemies = [e for e in enemies if not e.is_dead]
        if len(living_enemies) == 0:
            combat_over = True
            session.in_combat = False
            result_messages.append("\n🎉 **VICTORY!**")
            rewards = apply_combat_victory(session, enemies, result_messages)
        elif run_enemy_turn(session, living_enemies, result_messages):
            on_player_defeat(session, "You have fallen in battle.")
            result_messages.append("\n💀 **DEFEAT!**")
            return jsonify({
                'success': True,
                'combat_over': True,
                'victory': False,
                'player_died': True,
                'game_over': True,
                'message': '\n'.join(result_messages),
                'game_state': session.to_dict(),
                'combat_status': build_combat_status_payload(session),
            })
        else:
            session.combat_state['round'] = session.combat_state.get('round', 1) + 1
    
    combat_payload = build_combat_status_payload(session)
    return jsonify({
        'success': True,
        'hit': attack['hit'],
        'damage_dealt': damage_dealt,
        'target_killed': target_killed,
        'combat_over': combat_over,
        'victory': combat_over,
        'rewards': rewards if combat_over else None,
        'enemies': combat_payload.get('enemies', []),
        'player_hp': session.character.current_hp,
        'message': '\n'.join(result_messages),
        'game_state': session.to_dict(),
        'combat_status': combat_payload,
    })


@app.route('/api/combat/defend', methods=['POST'])
def combat_defend():
    """Player takes defensive action."""
    
    data = request.get_json() or {}
    session_id = data.get('session_id')
    
    if not session_id or session_id not in game_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    session = game_sessions[session_id]
    
    if not session.in_combat:
        return jsonify({'error': 'Not in combat'}), 400
    
    enemies = ensure_combat_enemies(session)
    living_enemies = [e for e in enemies if not e.is_dead]
    
    result_messages = ["🛡️ You take a defensive stance (+2 AC, half damage)"]
    boosted_ac = session.character.armor_class + 2
    
    if run_enemy_turn(session, living_enemies, result_messages,
                      ac_override=boosted_ac, halve_player_damage=True):
        return jsonify({
            'success': True,
            'combat_over': True,
            'player_died': True,
            'game_over': True,
            'message': '\n'.join(result_messages),
            'game_state': session.to_dict(),
            'combat_status': build_combat_status_payload(session),
        })
    
    session.combat_state['round'] = session.combat_state.get('round', 1) + 1
    combat_payload = build_combat_status_payload(session)
    
    return jsonify({
        'success': True,
        'message': '\n'.join(result_messages),
        'player_hp': session.character.current_hp,
        'game_state': session.to_dict(),
        'combat_status': combat_payload,
    })


@app.route('/api/combat/flee', methods=['POST'])
def combat_flee():
    """Attempt to flee from combat."""
    import random
    
    data = request.get_json() or {}
    session_id = data.get('session_id')
    
    if not session_id or session_id not in game_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    session = game_sessions[session_id]
    
    if not session.in_combat:
        return jsonify({'error': 'Not in combat'}), 400
    
    enemies = ensure_combat_enemies(session)
    living_enemies = [e for e in enemies if not e.is_dead]
    
    dex_mod = session.character.get_ability_modifier('dexterity')
    roll = random.randint(1, 20)
    dc = 10 + len(living_enemies)
    total = roll + dex_mod
    success = total >= dc
    
    result_messages = [f"🏃 DEX check: [{roll}]+{dex_mod} = {total} vs DC {dc}"]
    
    if success:
        session.in_combat = False
        session.combat_state = None
        # Run back the way you came, if that way is open from here
        manager = session.location_manager
        retreat = session.previous_location_id
        if manager and retreat and retreat in manager.get_exits().values():
            manager.set_current_location(retreat)
            here = manager.get_current_location()
            session.current_location, session.current_location_id = here.name, here.id
            result_messages.append(f"✅ You escape back to {here.name}!")
        else:
            result_messages.append("✅ You break away and slip out of sight!")
        return jsonify({
            'success': True,
            'fled': True,
            'combat_over': True,
            'message': '\n'.join(result_messages),
            'game_state': session.to_dict(),
            'combat_status': build_combat_status_payload(session),
        })
    
    result_messages.append("❌ Failed! Enemies attack...")
    if run_enemy_turn(session, living_enemies, result_messages):
        on_player_defeat(session, "You were cut down while trying to flee.")
        return jsonify({
            'success': True,
            'fled': False,
            'combat_over': True,
            'player_died': True,
            'game_over': True,
            'message': '\n'.join(result_messages),
            'game_state': session.to_dict(),
            'combat_status': build_combat_status_payload(session),
        })
    
    session.combat_state['round'] = session.combat_state.get('round', 1) + 1
    return jsonify({
        'success': True,
        'fled': False,
        'combat_over': False,
        'message': '\n'.join(result_messages),
        'game_state': session.to_dict(),
        'combat_status': build_combat_status_payload(session),
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

    blocked, block_reason = is_session_blocked(session)
    if blocked:
        return jsonify({
            'success': False,
            'message': block_reason or "You cannot rest now.",
            'game_over': True,
            'game_state': session.to_dict(),
        })
    
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
        if session.party:
            session.party.rest_all()
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
    hit_die = get_class_hit_die(session.character.char_class)
    heal_roll, _ = roll_dice(f"1d{hit_die}")
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

    # In combat, using an item takes your turn: the enemies act
    player_died = False
    if success and session.in_combat and session.combat_state:
        enemies = ensure_combat_enemies(session)
        living_enemies = [e for e in enemies if not e.is_dead]
        result_messages = [message]
        player_died = run_enemy_turn(session, living_enemies, result_messages)
        session.combat_state['round'] = session.combat_state.get('round', 1) + 1
        message = '\n'.join(result_messages)

    return jsonify({
        'success': success,
        'message': message,
        'current_hp': session.character.current_hp,
        'player_died': player_died,
        'game_over': session.game_over,
        'game_state': session.to_dict(),
        'combat_status': build_combat_status_payload(session) if session.in_combat else None,
    })


@app.route('/api/inventory/equip', methods=['POST'])
def inventory_equip():
    """Equip a weapon or armor."""
    from inventory import find_item_in_inventory, ItemType, calculate_armor_class
    
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
            dex_mod = session.character.get_ability_modifier('dexterity')
            session.character.armor_class = calculate_armor_class(dex_mod, item)
        return jsonify({
            'success': True,
            'message': f"🛡️ Equipped {item.name}!",
            'game_state': session.to_dict()
        })
    
    return jsonify({'success': False, 'message': "Can't equip that."})


# =============================================================================
# SHOP ENDPOINTS
# =============================================================================

GENERAL_SHOP_ITEMS = {
    "healing_potion": -1,  # Unlimited
    "torch": -1,
    "rope": -1,
    "rations": -1,
    "waterskin": -1,
    "bedroll": -1,
}


def get_session_shop(session):
    """
    The shop the player is trading with: the scenario's shop at the current
    location if there is one (e.g. Gavin's Forge at the blacksmith), else the
    general store. Shops live on the session so stock and haggle state persist.
    """
    from shop import ShopManager, create_general_shop
    from scenario_loader import load_shops

    if session.shop_manager is None:
        session.shop_manager = ShopManager()

    scenario = session.scenario.active_scenario if session.scenario else None
    if scenario:
        for shop in load_shops(scenario.id):
            if session.shop_manager.get_shop(shop.id) is None:
                session.shop_manager.add_shop(shop)
        here = session.location_manager.get_current_location() if session.location_manager else None
        if here:
            for shop in load_shops(scenario.id):
                if shop.location_id == here.id:
                    return session.shop_manager.get_shop(shop.id)

    shop = session.shop_manager.get_shop("general_shop")
    if shop is None:
        shop = create_general_shop(
            id="general_shop",
            name="General Store",
            owner_npc_id="merchant",
            location_id="village",
            items=dict(GENERAL_SHOP_ITEMS),
            markup=1.2
        )
        session.shop_manager.add_shop(shop)
    return shop


def _equipped_names(character) -> set:
    return {
        str(name).lower().replace('_', ' ')
        for name in (character.weapon, character.equipped_armor)
        if name
    }


@app.route('/api/shop/browse', methods=['GET'])
def shop_browse():
    """Browse shop inventory."""
    from shop import calculate_buy_price
    
    session_id = request.args.get('session_id')
    
    if not session_id or session_id not in game_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    session = game_sessions[session_id]
    
    shop = get_session_shop(session)
    haggle = session.shop_manager.get_haggle_state(shop.id)
    
    items = []
    for shop_item in shop.inventory:
        item = get_item(shop_item.item_id)
        if item and shop_item.is_in_stock():
            price = calculate_buy_price(
                item.value, shop.base_markup, shop_item.base_markup, 1.0,
                haggle_discount=haggle.get("discount", 0.0),
                haggle_increase=haggle.get("increase", 0.0),
            )
            available = shop_item.get_available()
            items.append({
                'id': shop_item.item_id,
                'name': item.name,
                'description': item.description,
                'price': price,
                'stock': available,  # -1 = unlimited
            })

    # What the shop will pay for each item the player carries
    from shop import calculate_sell_price
    from inventory import ItemType
    sell_offers = []
    if session.character:
        equipped = _equipped_names(session.character)
        for item in session.character.inventory:
            reason = None
            if item.item_type == ItemType.QUEST:
                reason = 'quest'
            elif item.name.lower() in equipped:
                reason = 'equipped'
            sell_offers.append({
                'name': item.name,
                'quantity': item.quantity,
                'price': calculate_sell_price(item.value),
                'can_sell': reason is None,
                'reason': reason,
            })

    owner = session.npc_manager.get_npc(shop.owner_npc_id) if session.npc_manager else None
    return jsonify({
        'success': True,
        'shop_name': shop.name,
        'owner_name': owner.name if owner else None,
        'is_local': shop.id != 'general_shop',
        'items': items,
        'sell_offers': sell_offers,
        'player_gold': session.character.gold if session.character else 0
    })


@app.route('/api/shop/buy', methods=['POST'])
def shop_buy():
    """Buy an item."""
    from shop import buy_item
    
    data = request.get_json() or {}
    session_id = data.get('session_id')
    item_id = (data.get('item_id') or data.get('item_name', '')).strip()
    quantity = data.get('quantity', 1)
    
    if not session_id or session_id not in game_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    session = game_sessions[session_id]
    
    if not session.character:
        return jsonify({'error': 'No character'}), 400
    
    if not item_id:
        return jsonify({'error': 'item_id is required'}), 400
    
    # Validate quantity (prevents negative/invalid values)
    if not isinstance(quantity, int) or quantity <= 0:
        return jsonify({'error': 'Quantity must be a positive integer'}), 400
    if quantity > 99:
        return jsonify({'error': 'Maximum 99 items per purchase'}), 400
    
    shop = get_session_shop(session)
    
    result = buy_item(
        character=session.character,
        shop=shop,
        item_id=item_id,
        quantity=quantity,
        shop_manager=session.shop_manager,
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
    from shop import sell_item
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
    if item.name.lower() in _equipped_names(session.character):
        return jsonify({
            'success': False,
            'message': f"You're using your {item.name}. Equip something else before selling it.",
        })

    shop = get_session_shop(session)
    
    result = sell_item(
        character=session.character,
        shop=shop,
        item_id=item_name,
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
    session_id = request.args.get('session_id')
    
    if not session_id or session_id not in game_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    session = game_sessions[session_id]
    
    from party import list_recruitable_npcs, get_recruitable_npc, can_attempt_recruitment

    members = []
    available_recruits = []

    if session.party:
        for m in session.party.members:
            members.append({
                'id': m.id,
                'name': m.name,
                'class': m.char_class.value if hasattr(m.char_class, 'value') else str(m.char_class),
                'hp': m.current_hp,
                'max_hp': m.max_hp,
            })

        if not session.party.is_full and session.character:
            for npc_key in list_recruitable_npcs():
                template = get_recruitable_npc(npc_key)
                if not template or session.party.get_member(template.id):
                    continue
                can_recruit, cond_results = can_attempt_recruitment(
                    template, session.character, session.quest_manager
                )
                available_recruits.append({
                    'npc_id': template.id,
                    'name': template.name,
                    'description': template.description,
                    'can_recruit': can_recruit,
                    'requirement': cond_results[0][0] if cond_results else '',
                })
    
    return jsonify({
        'success': True,
        'members': members,
        'party': members,
        'available_recruits': available_recruits,
    })


@app.route('/api/party/recruit', methods=['POST'])
def party_recruit():
    """Recruit an NPC."""
    from party import get_recruitable_npc, can_attempt_recruitment, Party
    
    data = request.get_json() or {}
    session_id = data.get('session_id')
    npc_id = (data.get('npc_id') or data.get('npc_name', '')).strip()
    
    if not session_id or session_id not in game_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    session = game_sessions[session_id]
    
    if not session.character:
        return jsonify({'error': 'No character'}), 400
    
    if not session.party:
        session.party = Party()
    
    if session.party.is_full:
        return jsonify({'success': False, 'message': 'Party is full!'})
    
    member = get_recruitable_npc(npc_id)
    if not member:
        return jsonify({'success': False, 'message': f"Can't recruit '{npc_id}'."})
    
    if session.party.get_member(member.id):
        return jsonify({'success': False, 'message': f"{member.name} is already in your party."})
    
    can_recruit, cond_results = can_attempt_recruitment(
        member, session.character, session.quest_manager
    )
    if not can_recruit:
        hint = '; '.join(msg for _, _, msg in cond_results if msg)
        return jsonify({'success': False, 'message': hint or 'Recruitment requirements not met.'})
    
    from party import (
        pay_recruitment_cost,
        RecruitmentCondition,
        check_recruitment_condition,
    )

    for cond_str in member.recruitment_conditions:
        cond = RecruitmentCondition.parse(cond_str)
        if not cond or cond.condition_type not in ("gold", "item"):
            continue
        met, _ = check_recruitment_condition(
            cond, session.character, session.quest_manager
        )
        if met:
            paid, pay_msg = pay_recruitment_cost(cond, session.character)
            if not paid:
                return jsonify({'success': False, 'message': pay_msg})

    added, add_message = session.party.add_member(member)
    if not added:
        return jsonify({'success': False, 'message': add_message})
    
    return jsonify({
        'success': True,
        'message': add_message or f"🎉 {member.name} joins your party!",
        'game_state': session.to_dict()
    })


# =============================================================================
# QUEST ENDPOINTS
# =============================================================================

@app.route('/api/quests/list', methods=['GET'])
def quests_list():
    """List quests."""
    try:
        session_id = request.args.get('session_id')
        
        if not session_id or session_id not in game_sessions:
            return jsonify({'error': 'Invalid session'}), 400
        
        session = game_sessions[session_id]
        
        if not session.quest_manager:
            return jsonify({'success': True, 'active': [], 'completed': []})
        
        return jsonify({
            'success': True,
            'active': [q.to_dict() for q in session.quest_manager.get_active_quests()],
            'completed': session.quest_manager.get_completed_quests()  # Already returns dicts
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
    
    from game_mechanics import finish_quest
    rewards = finish_quest(session, quest_id)
    if not rewards:
        quest = session.quest_manager.get_quest(quest_id)
        if not quest:
            return jsonify({'success': False, 'message': 'Quest not found.'})
        return jsonify({'success': False, 'message': 'Objectives not complete.'})

    rewards.pop('quest', None)
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
    session_id = request.args.get('session_id')
    
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


# =============================================================================
# ROOT ENDPOINT - API INFO
# =============================================================================

@app.route('/')
def api_info():
    """Return API info since we're not serving a frontend here."""
    return jsonify({
        'name': 'AI D&D RPG API',
        'version': '1.2.0',
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
    # Local-only and non-debug by default: the Werkzeug debugger allows code
    # execution, and the API has no auth. Opt in explicitly via .env.
    host = os.getenv('API_HOST', '127.0.0.1')
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    
    print(f"🎲 AI RPG API Server starting on http://{host}:{port}")
    print(f"   Debug mode: {debug}")
    from llm_client import get_llm_provider, get_active_model_name, is_llm_configured
    print(f"   LLM provider: {get_llm_provider()}")
    print(f"   LLM configured: {'Yes' if is_llm_configured() else 'No'}")
    print(f"   LLM model: {get_active_model_name()}")
    print(f"\n   📡 API endpoints available at http://localhost:{port}/api/*")
    print(f"   🌐 React frontend runs separately at http://localhost:3000")
    
    app.run(host=host, port=port, debug=debug)
