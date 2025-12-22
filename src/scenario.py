"""
Scenario System for AI D&D Text RPG (Phase 1, Step 1.3 + Phase 3.2 + Phase 3.3 + Phase 3.3.3 + Phase 3.3.4)
Manages scenes, story progression, narrative pacing, locations, NPCs, quests, and shops.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Callable, Tuple, Any
from enum import Enum
import json

from npc import NPC, NPCRole, NPCManager, Personality, SkillCheckOption
from quest import (
    Quest, QuestObjective, QuestManager, QuestStatus, QuestType, ObjectiveType,
    create_kill_objective, create_find_objective, create_talk_objective,
    create_location_objective, create_collect_objective
)
from shop import (
    Shop, ShopManager, ShopType, create_blacksmith_shop, create_traveling_merchant_shop
)

class SceneStatus(Enum):
    """Status of a scene."""
    LOCKED = "locked"           # Not yet accessible
    ACTIVE = "active"           # Currently playing
    COMPLETED = "completed"     # Finished


class EventTrigger(Enum):
    """When a location event can trigger."""
    ON_ENTER = "on_enter"           # When player enters location
    ON_FIRST_VISIT = "on_first_visit"  # Only on first visit
    ON_LOOK = "on_look"             # When player uses 'look' command
    ON_ITEM_TAKE = "on_item_take"   # When player takes a specific item


# =============================================================================
# LOCATION EVENT SYSTEM (Phase 3.2.1 Priority 3)
# =============================================================================

@dataclass
class LocationEvent:
    """
    Represents a triggered event at a location.
    
    Events are one-time or repeatable occurrences that add narrative
    and mechanical depth to locations (traps, discoveries, ambushes).
    
    Follows "Mechanics First, Narration Last" principle:
    - effect: The mechanical outcome (deterministic)
    - narration: Hint for AI DM to narrate (creative)
    """
    
    id: str                         # Unique identifier (e.g., "tripwire_trap")
    trigger: EventTrigger           # When this event fires
    narration: str                  # Hint for AI DM ("A wire catches your foot...")
    
    # Optional mechanics
    effect: Optional[str] = None    # Mechanical effect: "damage:1d4", "add_item:key"
    condition: Optional[str] = None # Prerequisite: "has_item:torch", "skill:perception:15"
    
    # Behavior
    one_time: bool = True           # Only fires once per game?
    
    def to_dict(self) -> dict:
        """Serialize event definition."""
        return {
            "id": self.id,
            "trigger": self.trigger.value,
            "narration": self.narration,
            "effect": self.effect,
            "condition": self.condition,
            "one_time": self.one_time
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'LocationEvent':
        """Create event from dictionary."""
        return cls(
            id=data["id"],
            trigger=EventTrigger(data["trigger"]),
            narration=data["narration"],
            effect=data.get("effect"),
            condition=data.get("condition"),
            one_time=data.get("one_time", True)
        )


# =============================================================================
# HIDDEN ITEM SYSTEM (Phase 3.3.5)
# =============================================================================

@dataclass
class HiddenItem:
    """
    Represents a hidden item that requires a skill check to discover.
    
    Hidden items are not visible until the player succeeds on a skill check
    (typically Perception or Investigation). Once discovered, they move to
    the location's regular items list.
    
    Examples:
        - Secret compartment in a desk (Investigation DC 14)
        - Glint of metal under debris (Perception DC 12)
        - Trap mechanism to disarm (Investigation DC 16)
    """
    
    item_id: str              # The item key from ITEMS database (e.g., "enchanted_dagger")
    skill: str                # Skill required: "perception" or "investigation"
    dc: int                   # Difficulty class (typically 10-20)
    hint: str = ""            # DM hint when player searches: "You notice faint scratches..."
    found: bool = False       # Runtime state: has this been discovered?
    
    def to_dict(self) -> dict:
        """Serialize hidden item for saving."""
        return {
            "item_id": self.item_id,
            "skill": self.skill,
            "dc": self.dc,
            "hint": self.hint,
            "found": self.found
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'HiddenItem':
        """Create hidden item from dictionary."""
        return cls(
            item_id=data["item_id"],
            skill=data["skill"],
            dc=data["dc"],
            hint=data.get("hint", ""),
            found=data.get("found", False)
        )


# =============================================================================
# LOCATION ATMOSPHERE SYSTEM (Phase 3.4.1)
# =============================================================================

@dataclass
class LocationAtmosphere:
    """
    Atmospheric hints for the DM to create immersive location descriptions.
    These are suggestions, not scripts - the AI weaves them into narrative.
    
    All fields are optional. Use what makes sense for each location.
    The DM picks 2-3 sensory details to incorporate into descriptions.
    """
    
    # Sensory palette (DM picks from these)
    sounds: List[str] = field(default_factory=list)    # ["dripping water", "distant echoes"]
    smells: List[str] = field(default_factory=list)    # ["musty earth", "torch smoke"]
    textures: List[str] = field(default_factory=list)  # ["damp stone", "slippery moss"]
    lighting: str = ""                                  # "dim torchlight", "pitch black"
    temperature: str = ""                               # "cold and damp", "warm"
    
    # Mood guidance (not prescriptive emotion, just tone)
    mood: str = ""                                      # "tense", "eerie", "welcoming"
    danger_level: str = ""                              # "safe", "uneasy", "threatening", "deadly"
    
    # Approach DCs for travel menu system (Phase 3.2.1 Priority 9)
    stealth_dc: int = 12                                # DC for stealth approach
    perception_dc: int = 10                             # DC for cautious approach
    
    # Random flavor pool (small details DM can sprinkle in)
    random_details: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize atmosphere for saving."""
        return {
            "sounds": self.sounds.copy() if self.sounds else [],
            "smells": self.smells.copy() if self.smells else [],
            "textures": self.textures.copy() if self.textures else [],
            "lighting": self.lighting,
            "temperature": self.temperature,
            "mood": self.mood,
            "danger_level": self.danger_level,
            "stealth_dc": self.stealth_dc,
            "perception_dc": self.perception_dc,
            "random_details": self.random_details.copy() if self.random_details else []
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LocationAtmosphere":
        """Create atmosphere from dictionary."""
        return cls(
            sounds=data.get("sounds", []),
            smells=data.get("smells", []),
            textures=data.get("textures", []),
            lighting=data.get("lighting", ""),
            temperature=data.get("temperature", ""),
            mood=data.get("mood", ""),
            danger_level=data.get("danger_level", ""),
            stealth_dc=data.get("stealth_dc", 12),
            perception_dc=data.get("perception_dc", 10),
            random_details=data.get("random_details", [])
        )
    
    def get_dm_summary(self) -> str:
        """
        Generate a summary for inclusion in DM context.
        Returns empty string if no atmosphere data.
        """
        parts = []
        
        if self.sounds:
            parts.append(f"Sounds: {', '.join(self.sounds)}")
        
        if self.smells:
            parts.append(f"Smells: {', '.join(self.smells)}")
        
        if self.textures:
            parts.append(f"Textures: {', '.join(self.textures)}")
        
        if self.lighting:
            parts.append(f"Lighting: {self.lighting}")
        
        if self.temperature:
            parts.append(f"Temperature: {self.temperature}")
        
        if self.mood:
            parts.append(f"Mood: {self.mood}")
        
        if self.danger_level:
            parts.append(f"Danger: {self.danger_level}")
        
        if self.random_details:
            parts.append(f"Details pool: {', '.join(self.random_details[:3])}...")
        
        return "\n".join(parts) if parts else ""


# =============================================================================
# LOCATION SYSTEM (Phase 3.2)
# =============================================================================

# Cardinal direction aliases (Phase 3.2.1 Priority 6)
CARDINAL_ALIASES = {
    "n": "north", "s": "south", "e": "east", "w": "west",
    "ne": "northeast", "nw": "northwest", "se": "southeast", "sw": "southwest",
    "u": "up", "d": "down"
}

def resolve_direction_alias(direction: str) -> str:
    """
    Resolve cardinal shorthand to full direction name.
    
    Examples:
        'n' → 'north'
        'ne' → 'northeast'
        'north' → 'north' (unchanged)
        'forest_path' → 'forest_path' (unchanged)
    """
    direction_lower = direction.lower().strip()
    return CARDINAL_ALIASES.get(direction_lower, direction_lower)


def normalize_travel_input(direction: str) -> str:
    """
    Normalize player travel input for more flexible matching.
    
    Strips filler words and normalizes for matching:
    - "to the village square" → "village square"
    - "towards the forest" → "forest"
    - "into the cave" → "cave"
    - "head outside" → "outside"
    
    Returns: Normalized direction string
    """
    direction_lower = direction.lower().strip()
    
    # Remove common travel prefixes
    prefixes_to_strip = [
        "to the ", "to ", "towards the ", "towards ", "toward the ", "toward ",
        "into the ", "into ", "inside the ", "inside ", "through the ", "through ",
        "back to the ", "back to ", "back ", "over to the ", "over to ", "over ",
        "out to the ", "out to ", "outside to the ", "outside to ",
        "head to the ", "head to ", "head ", "go to the ", "go to ", "go ",
        "enter the ", "enter ", "leave for ", "leave to "
    ]
    
    for prefix in prefixes_to_strip:
        if direction_lower.startswith(prefix):
            direction_lower = direction_lower[len(prefix):]
            break
    
    return direction_lower.strip()


def fuzzy_location_match(search_term: str, location_id: str, location_name: str) -> bool:
    """
    Check if search term matches a location ID or name with fuzzy matching.
    
    Matches:
    - Exact match: "village_square" matches "village_square"
    - Name match: "village square" matches location named "Village Square"
    - Partial: "village" matches "village_square"
    - Underscore normalization: "village square" matches "village_square"
    
    Returns: True if match found
    """
    search_clean = search_term.lower().strip()
    id_clean = location_id.lower()
    name_clean = location_name.lower()
    
    # Normalize underscores to spaces for comparison
    search_normalized = search_clean.replace("_", " ")
    id_normalized = id_clean.replace("_", " ")
    
    # Exact matches
    if search_clean == id_clean or search_clean == name_clean:
        return True
    
    # Normalized matches (underscore ↔ space)
    if search_normalized == id_normalized or search_normalized == name_clean:
        return True
    
    # Partial matches (search term contained in location name/id)
    if search_normalized in id_normalized or search_normalized in name_clean:
        return True
    
    # Reverse partial (location name contained in search - for verbose input)
    if len(search_normalized) > 3 and (id_normalized in search_normalized or name_clean in search_normalized):
        return True
    
    return False


@dataclass 
class ExitCondition:
    """Defines a condition that must be met to use an exit."""
    exit_name: str                    # Which exit this applies to
    condition: str                    # "has_item:rusty_key", "skill:strength:15", "visited:cave_entrance"
    fail_message: str = ""            # Custom message when blocked: "The door is locked."
    consume_item: bool = False        # If True, the key item is consumed on use
    
    def to_dict(self) -> dict:
        """Serialize for saving."""
        return {
            "exit_name": self.exit_name,
            "condition": self.condition,
            "fail_message": self.fail_message,
            "consume_item": self.consume_item
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ExitCondition':
        """Deserialize from saved data."""
        return cls(
            exit_name=data["exit_name"],
            condition=data["condition"],
            fail_message=data.get("fail_message", ""),
            consume_item=data.get("consume_item", False)
        )


@dataclass
class RandomEncounter:
    """
    Defines a random encounter that can trigger when entering a location.
    
    Random encounters add variety to exploration. Each time a player enters
    a location with random encounters, there's a chance an encounter triggers.
    
    Follows "Mechanics First, Narration Last" principle:
    - The chance and enemies are deterministic (roll vs threshold)
    - The AI DM narrates the encounter introduction
    """
    
    id: str                              # Unique identifier ("wolf_ambush")
    enemies: List[str]                   # Enemy types to spawn ["wolf"] or ["wolf", "wolf"]
    chance: int = 20                     # Percentage chance (0-100) to trigger
    
    # Optional conditions
    condition: Optional[str] = None      # Prerequisite: "not_visited:goblin_camp", "has_item:meat"
    min_visits: int = 0                  # Only triggers after N visits (0 = always eligible)
    max_triggers: int = 1                # Max times this can trigger (1 = once, -1 = unlimited)
    cooldown: int = 0                    # Visits before can trigger again after triggering
    
    # Narration hint for AI DM
    narration: str = ""                  # "A wolf emerges from the shadows!"
    
    # Runtime tracking (not saved in dataclass, tracked by location)
    # times_triggered and last_triggered are tracked in Location state
    
    def to_dict(self) -> dict:
        """Serialize for scenario definition."""
        return {
            "id": self.id,
            "enemies": self.enemies.copy(),
            "chance": self.chance,
            "condition": self.condition,
            "min_visits": self.min_visits,
            "max_triggers": self.max_triggers,
            "cooldown": self.cooldown,
            "narration": self.narration
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'RandomEncounter':
        """Create from dictionary."""
        return cls(
            id=data["id"],
            enemies=data.get("enemies", []),
            chance=data.get("chance", 20),
            condition=data.get("condition"),
            min_visits=data.get("min_visits", 0),
            max_triggers=data.get("max_triggers", 1),
            cooldown=data.get("cooldown", 0),
            narration=data.get("narration", "")
        )


# =============================================================================
# Phase 4.5: Interactive World Map Data Structures
# =============================================================================

@dataclass
class MapNode:
    """Visual map representation of a location."""
    
    location_id: str                # References Location.id
    x: float                        # Normalized X coordinate (0-1)
    y: float                        # Normalized Y coordinate (0-1)
    icon: str                       # Display icon (emoji or icon ID)
    label: str                      # Display label
    
    # Visual State
    is_current: bool = False        # Player is here
    is_visited: bool = False        # Has been visited (full color)
    is_visible: bool = True         # Not hidden by fog of war
    is_accessible: bool = True      # Can travel to (not locked)
    
    # Status Indicators
    danger_level: str = "safe"      # safe/uneasy/threatening/deadly
    has_shop: bool = False          # Show shop icon overlay
    has_quest: bool = False         # Show quest marker overlay
    has_npc: bool = False           # Show NPC indicator overlay
    
    def to_dict(self) -> dict:
        """Serialize for API/save."""
        return {
            "location_id": self.location_id,
            "x": self.x,
            "y": self.y,
            "icon": self.icon,
            "label": self.label,
            "is_current": self.is_current,
            "is_visited": self.is_visited,
            "is_visible": self.is_visible,
            "is_accessible": self.is_accessible,
            "danger_level": self.danger_level,
            "has_shop": self.has_shop,
            "has_quest": self.has_quest,
            "has_npc": self.has_npc
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MapNode':
        """Create from dictionary."""
        return cls(
            location_id=data["location_id"],
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            icon=data.get("icon", "🏠"),
            label=data.get("label", ""),
            is_current=data.get("is_current", False),
            is_visited=data.get("is_visited", False),
            is_visible=data.get("is_visible", True),
            is_accessible=data.get("is_accessible", True),
            danger_level=data.get("danger_level", "safe"),
            has_shop=data.get("has_shop", False),
            has_quest=data.get("has_quest", False),
            has_npc=data.get("has_npc", False)
        )


@dataclass
class MapConnection:
    """Visual line between two map nodes."""
    
    from_id: str                    # Source location ID
    to_id: str                      # Destination location ID
    is_bidirectional: bool = True   # Arrow on both ends?
    is_visible: bool = True         # Show this connection?
    is_locked: bool = False         # Dashed line for locked exits
    travel_time: str = ""           # Optional: "5 min", "1 hour"
    
    def to_dict(self) -> dict:
        """Serialize for API."""
        return {
            "from_id": self.from_id,
            "to_id": self.to_id,
            "is_bidirectional": self.is_bidirectional,
            "is_visible": self.is_visible,
            "is_locked": self.is_locked,
            "travel_time": self.travel_time
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MapConnection':
        """Create from dictionary."""
        return cls(
            from_id=data["from_id"],
            to_id=data["to_id"],
            is_bidirectional=data.get("is_bidirectional", True),
            is_visible=data.get("is_visible", True),
            is_locked=data.get("is_locked", False),
            travel_time=data.get("travel_time", "")
        )


@dataclass
class MapRegion:
    """A visual region/zone on the map (e.g., 'Village', 'Forest', 'Cave')."""
    
    id: str                         # "willowmere_village"
    name: str                       # "Willowmere Village"
    description: str = ""           # "A peaceful farming village..."
    
    # Visual Properties
    background_color: str = "#2D5A3D"   # Region tint color
    border_color: str = "#1A3D1A"       # Border color
    icon: str = "🏘️"                    # Region icon
    
    # Bounds (normalized 0-1)
    bounds_x: float = 0.0           # Left edge
    bounds_y: float = 0.0           # Top edge
    bounds_width: float = 1.0       # Width
    bounds_height: float = 1.0      # Height
    
    # State
    is_unlocked: bool = True        # Can player enter this region?
    unlock_condition: str = ""      # "objective:rescue_lily"
    
    def to_dict(self) -> dict:
        """Serialize for API."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "background_color": self.background_color,
            "border_color": self.border_color,
            "icon": self.icon,
            "bounds_x": self.bounds_x,
            "bounds_y": self.bounds_y,
            "bounds_width": self.bounds_width,
            "bounds_height": self.bounds_height,
            "is_unlocked": self.is_unlocked,
            "unlock_condition": self.unlock_condition
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MapRegion':
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            background_color=data.get("background_color", "#2D5A3D"),
            border_color=data.get("border_color", "#1A3D1A"),
            icon=data.get("icon", "🏘️"),
            bounds_x=data.get("bounds_x", 0.0),
            bounds_y=data.get("bounds_y", 0.0),
            bounds_width=data.get("bounds_width", 1.0),
            bounds_height=data.get("bounds_height", 1.0),
            is_unlocked=data.get("is_unlocked", True),
            unlock_condition=data.get("unlock_condition", "")
        )


@dataclass
class Location:
    """Represents a physical location in the game world."""
    
    id: str                              # Unique identifier (e.g., "tavern_main")
    name: str                            # Display name (e.g., "The Rusty Tankard")
    description: str                     # Full description for AI
    
    # Navigation - maps exit names to location IDs
    exits: Dict[str, str] = field(default_factory=dict)  # {"door": "street", "stairs": "upper_floor"}
    
    # Direction aliases (Phase 3.2.1 - Priority 6: Cardinal Aliases)
    # Maps cardinal directions (n/s/e/w) to exit names
    direction_aliases: Dict[str, str] = field(default_factory=dict)  # {"n": "forest_path", "e": "tavern_door"}
    
    # Conditional exits (Phase 3.2.1 - Priority 5)
    exit_conditions: List[ExitCondition] = field(default_factory=list)  # Requirements for specific exits
    
    # Secret/Hidden Location (Phase 3.2.1 - Priority 8)
    hidden: bool = False                 # If True, exit to this location is hidden until discovered
    discovery_condition: str = ""        # How to reveal: "skill:perception:14", "has_item:map", etc.
    discovery_hint: str = ""             # Hint for player: "Something seems off about this wall..."
    
    # Contents
    npcs: List[str] = field(default_factory=list)        # NPC IDs present here
    items: List[str] = field(default_factory=list)       # Item keys that can be found (visible)
    hidden_items: List[HiddenItem] = field(default_factory=list)  # Items requiring skill check to find
    
    # AI Guidance
    atmosphere: Optional[LocationAtmosphere] = None      # Sensory/mood hints for DM
    atmosphere_text: str = ""                            # Legacy: simple text atmosphere (deprecated)
    enter_text: str = ""                                 # First-time entry description
    
    # Events (Phase 3.2.1)
    events: List[LocationEvent] = field(default_factory=list)  # Events that can trigger here
    
    # Combat Encounters (Phase 3.2.2 - Fixed difficulty)
    encounter: List[str] = field(default_factory=list)  # Fixed enemy types for this location
    encounter_triggered: bool = False  # Whether encounter has already occurred
    
    # Random Encounters (Phase 3.2.1 - Priority 7)
    random_encounters: List[RandomEncounter] = field(default_factory=list)  # Possible random encounters
    
    # Map Visualization (Phase 4.5 - Interactive World Map)
    map_x: float = 0.0                   # X coordinate on map (0.0 to 1.0 normalized)
    map_y: float = 0.0                   # Y coordinate on map (0.0 to 1.0 normalized)
    map_icon: str = "🏠"                 # Emoji or icon ID for map marker
    map_label: str = ""                  # Short label (defaults to name if empty)
    map_region: str = "default"          # Region/zone this location belongs to
    map_hidden: bool = False             # If True, not shown on map until visited/discovered
    
    # Phase 3.6.7 - Darkness Mechanics
    is_dark: bool = False                # If True, requires torch for full visibility
    
    # State (runtime)
    visited: bool = False
    visit_count: int = 0                                    # Times player has entered this location
    events_triggered: List[str] = field(default_factory=list)  # Event IDs already triggered
    unlocked_exits: List[str] = field(default_factory=list)    # Exits that have been unlocked
    random_encounter_triggers: Dict[str, int] = field(default_factory=dict)  # encounter_id -> times triggered
    random_encounter_last_visit: Dict[str, int] = field(default_factory=dict)  # encounter_id -> visit count when last triggered
    
    def get_exits_display(self) -> str:
        """Get a formatted string of available exits."""
        if not self.exits:
            return "There are no obvious exits."
        exits_list = list(self.exits.keys())
        if len(exits_list) == 1:
            return f"You can go: {exits_list[0]}"
        return f"You can go: {', '.join(exits_list[:-1])} or {exits_list[-1]}"
    
    def to_dict(self) -> dict:
        """Serialize location state for saving."""
        return {
            "id": self.id,
            "visited": self.visited,
            "visit_count": self.visit_count,  # Phase 3.2.1 Priority 7: Track visits
            "events_triggered": self.events_triggered.copy(),
            "items": self.items.copy(),  # Phase 3.2.1: Save picked-up items state
            "hidden_items": [hi.to_dict() for hi in self.hidden_items],  # Phase 3.3.5: Hidden items
            "encounter_triggered": self.encounter_triggered,  # Phase 3.2.2: Save encounter state
            "unlocked_exits": self.unlocked_exits.copy(),  # Phase 3.2.1: Save unlocked doors
            "random_encounter_triggers": self.random_encounter_triggers.copy(),  # Phase 3.2.1 Priority 7
            "random_encounter_last_visit": self.random_encounter_last_visit.copy()  # Phase 3.2.1 Priority 7
        }
    
    @classmethod
    def from_state(cls, location: 'Location', state: dict) -> 'Location':
        """Apply saved state to a location."""
        location.visited = state.get("visited", False)
        location.visit_count = state.get("visit_count", 0)  # Phase 3.2.1 Priority 7
        location.events_triggered = state.get("events_triggered", [])
        # Restore items if saved (Phase 3.2.1)
        if "items" in state:
            location.items = state.get("items", [])
        # Restore hidden items state (Phase 3.3.5)
        if "hidden_items" in state:
            # Match by item_id and update found state
            saved_hidden = {hi["item_id"]: hi for hi in state.get("hidden_items", [])}
            for hi in location.hidden_items:
                if hi.item_id in saved_hidden:
                    hi.found = saved_hidden[hi.item_id].get("found", False)
        # Restore encounter state (Phase 3.2.2)
        location.encounter_triggered = state.get("encounter_triggered", False)
        # Restore unlocked exits (Phase 3.2.1)
        location.unlocked_exits = state.get("unlocked_exits", [])
        # Restore random encounter state (Phase 3.2.1 Priority 7)
        location.random_encounter_triggers = state.get("random_encounter_triggers", {})
        location.random_encounter_last_visit = state.get("random_encounter_last_visit", {})
        return location
    
    def get_exit_condition(self, exit_name: str) -> Optional[ExitCondition]:
        """Get the condition for a specific exit, if any."""
        exit_lower = exit_name.lower()
        for cond in self.exit_conditions:
            if cond.exit_name.lower() == exit_lower:
                return cond
        return None
    
    def is_exit_unlocked(self, exit_name: str) -> bool:
        """Check if an exit has been permanently unlocked."""
        return exit_name.lower() in [e.lower() for e in self.unlocked_exits]
    
    def unlock_exit(self, exit_name: str):
        """Permanently unlock an exit (e.g., after using a key)."""
        if not self.is_exit_unlocked(exit_name):
            self.unlocked_exits.append(exit_name.lower())
    
    def has_item(self, item_key: str) -> bool:
        """Check if an item is present in this location.
        
        Normalizes spaces to underscores for user-friendly matching.
        E.g. 'healing potion' matches 'healing_potion'.
        """
        normalized_key = item_key.lower().replace(" ", "_")
        return normalized_key in [i.lower() for i in self.items]
    
    def remove_item(self, item_key: str) -> bool:
        """Remove an item from this location. Returns True if removed.
        
        Normalizes spaces to underscores for user-friendly matching.
        """
        normalized_key = item_key.lower().replace(" ", "_")
        for i, item in enumerate(self.items):
            if item.lower() == normalized_key:
                self.items.pop(i)
                return True
        return False
    
    def has_npc(self, npc_id: str) -> bool:
        """Check if an NPC is present in this location."""
        return npc_id.lower() in [n.lower() for n in self.npcs]
    
    def get_items_display(self) -> str:
        """Get a formatted string of items in this location."""
        if not self.items:
            return ""
        # Format item names for display (underscore → space, title case)
        item_names = [item.replace("_", " ").title() for item in self.items]
        return f"🎒 Items here: {', '.join(item_names)}"
    
    def get_npcs_display(self) -> str:
        """Get a formatted string of NPCs in this location."""
        if not self.npcs:
            return ""
        # Capitalize NPC names for display
        npc_names = [npc.replace("_", " ").title() for npc in self.npcs]
        return f"👤 Present: {', '.join(npc_names)}"
    
    # =========================================================================
    # HIDDEN ITEMS SYSTEM (Phase 3.3.5)
    # =========================================================================
    
    def get_undiscovered_hidden_items(self) -> List[HiddenItem]:
        """Get all hidden items that haven't been found yet."""
        return [hi for hi in self.hidden_items if not hi.found]
    
    def has_searchable_secrets(self) -> bool:
        """Check if there are hidden items to search for."""
        return len(self.get_undiscovered_hidden_items()) > 0
    
    def get_search_hints(self) -> List[str]:
        """Get hints for undiscovered hidden items (for DM narration)."""
        return [hi.hint for hi in self.get_undiscovered_hidden_items() if hi.hint]
    
    def discover_hidden_item(self, item_id: str) -> bool:
        """
        Mark a hidden item as discovered and add to visible items.
        
        Returns:
            True if item was found and added, False if not found or already discovered
        """
        for hi in self.hidden_items:
            if hi.item_id == item_id and not hi.found:
                hi.found = True
                # Add to visible items list
                if hi.item_id not in self.items:
                    self.items.append(hi.item_id)
                return True
        return False
    
    def get_hidden_item(self, item_id: str) -> Optional[HiddenItem]:
        """Get a hidden item by ID."""
        for hi in self.hidden_items:
            if hi.item_id == item_id:
                return hi
        return None
    
    # =========================================================================
    # EVENT SYSTEM METHODS (Phase 3.2.1)
    # =========================================================================
    
    def get_events_for_trigger(self, trigger: EventTrigger, is_first_visit: bool = False) -> List[LocationEvent]:
        """
        Get events that should fire for a given trigger.
        
        Args:
            trigger: The event trigger type
            is_first_visit: Whether this is the player's first time here
            
        Returns:
            List of events that should fire (not yet triggered if one_time)
        """
        result = []
        for event in self.events:
            # Skip if already triggered and one-time
            if event.one_time and event.id in self.events_triggered:
                continue
            
            # Check trigger match
            if event.trigger == trigger:
                result.append(event)
            # First visit triggers also fire on_enter events marked as first-visit
            elif trigger == EventTrigger.ON_ENTER and event.trigger == EventTrigger.ON_FIRST_VISIT:
                if is_first_visit:
                    result.append(event)
        
        return result
    
    def trigger_event(self, event_id: str) -> bool:
        """
        Mark an event as triggered.
        
        Args:
            event_id: The ID of the event to mark as triggered
            
        Returns:
            True if event was found and marked, False otherwise
        """
        for event in self.events:
            if event.id == event_id:
                if event_id not in self.events_triggered:
                    self.events_triggered.append(event_id)
                return True
        return False
    
    def has_event(self, event_id: str) -> bool:
        """Check if a specific event exists at this location."""
        return any(e.id == event_id for e in self.events)
    
    def is_event_triggered(self, event_id: str) -> bool:
        """Check if a specific event has already been triggered."""
        return event_id in self.events_triggered
    
    def add_event(self, event: LocationEvent):
        """Add an event to this location."""
        self.events.append(event)
    
    # =========================================================================
    # RANDOM ENCOUNTER METHODS (Phase 3.2.1 - Priority 7)
    # =========================================================================
    
    def check_random_encounter(self, game_state: dict = None) -> Optional[RandomEncounter]:
        """
        Check if a random encounter triggers on entering this location.
        
        Follows "Mechanics First" principle - deterministic roll against chance.
        
        Args:
            game_state: Optional dict for checking conditions
            
        Returns:
            RandomEncounter if one triggers, None otherwise
        """
        import random
        
        for encounter in self.random_encounters:
            # Check if encounter can trigger
            if not self._can_encounter_trigger(encounter, game_state):
                continue
            
            # Roll for encounter (1-100)
            roll = random.randint(1, 100)
            if roll <= encounter.chance:
                # Encounter triggers!
                self._record_encounter_trigger(encounter)
                return encounter
        
        return None
    
    def _can_encounter_trigger(self, encounter: RandomEncounter, game_state: dict = None) -> bool:
        """Check if a specific encounter is eligible to trigger."""
        
        # Check min_visits requirement
        if encounter.min_visits > 0 and self.visit_count < encounter.min_visits:
            return False
        
        # Check max_triggers limit
        triggers = self.random_encounter_triggers.get(encounter.id, 0)
        if encounter.max_triggers != -1 and triggers >= encounter.max_triggers:
            return False
        
        # Check cooldown (visits since last trigger)
        if encounter.cooldown > 0:
            last_visit = self.random_encounter_last_visit.get(encounter.id, -999)
            visits_since = self.visit_count - last_visit
            if visits_since < encounter.cooldown:
                return False
        
        # Check condition if present
        if encounter.condition and game_state:
            success, _ = check_exit_condition(encounter.condition, game_state)
            if not success:
                return False
        
        return True
    
    def _record_encounter_trigger(self, encounter: RandomEncounter):
        """Record that an encounter has triggered."""
        # Increment trigger count
        current = self.random_encounter_triggers.get(encounter.id, 0)
        self.random_encounter_triggers[encounter.id] = current + 1
        
        # Record visit count when triggered (for cooldown)
        self.random_encounter_last_visit[encounter.id] = self.visit_count


# =============================================================================
# CONDITION CHECKING (Phase 3.2.1 - Priority 5)
# =============================================================================

def check_exit_condition(condition: str, game_state: dict) -> Tuple[bool, str]:
    """
    Check if an exit condition is met.
    
    Args:
        condition: Condition string like "has_item:rusty_key" or "skill:strength:15"
        game_state: Dict with 'character' (Character object), 'inventory' (Inventory object),
                   'visited_locations' (list of location IDs), etc.
    
    Returns:
        (success, reason) - success=True if condition met, reason explains failure
    
    Condition formats:
        - "has_item:<item_key>" - Player has the item in inventory
        - "visited:<location_id>" - Player has visited this location
        - "gold:<amount>" - Player has at least this much gold
        - "skill:<ability>:<dc>" - Returns (True, "skill_check") to trigger a check
        - "objective:<objective_id>" - An objective has been completed
        - "flag:<flag_name>" - A game flag is set (for custom triggers)
    """
    if not condition:
        return True, ""
    
    parts = condition.split(":")
    cond_type = parts[0].lower()
    
    if cond_type == "has_item":
        if len(parts) < 2:
            return True, ""  # Malformed, pass through
        item_key = parts[1].lower()
        inventory = game_state.get("inventory")
        if inventory:
            # Check if player has the item
            for item in inventory.items:
                if item.name.lower().replace(" ", "_") == item_key or item_key in item.name.lower():
                    return True, f"You use the {item.name}."
        return False, f"You need a key or tool to pass."
    
    elif cond_type == "visited":
        if len(parts) < 2:
            return True, ""
        location_id = parts[1].lower()
        visited = game_state.get("visited_locations", [])
        if location_id in [v.lower() for v in visited]:
            return True, ""
        return False, "You haven't discovered how to reach there yet."
    
    elif cond_type == "gold":
        if len(parts) < 2:
            return True, ""
        try:
            required = int(parts[1])
            character = game_state.get("character")
            if character and character.gold >= required:
                return True, f"You pay {required} gold."
            return False, f"You need {required} gold to proceed."
        except ValueError:
            return True, ""
    
    elif cond_type == "skill":
        # Return special marker - game.py will handle the actual check
        if len(parts) < 3:
            return True, ""
        ability = parts[1]
        dc = parts[2]
        return True, f"skill_check:{ability}:{dc}"
    
    elif cond_type == "objective":
        if len(parts) < 2:
            return True, ""
        objective_id = parts[1]
        completed = game_state.get("completed_objectives", [])
        if objective_id in completed:
            return True, ""
        return False, "You haven't completed the required task yet."
    
    elif cond_type == "flag":
        if len(parts) < 2:
            return True, ""
        flag_name = parts[1]
        flags = game_state.get("flags", {})
        if flags.get(flag_name, False):
            return True, ""
        return False, "Something is blocking your way."
    
    # Unknown condition type - pass through
    return True, ""


# =============================================================================
# Phase 4.5: WorldMap Class - Manages Interactive World Map
# =============================================================================

class WorldMap:
    """Manages the visual world map for a scenario."""
    
    def __init__(self, scenario_id: str = ""):
        self.scenario_id = scenario_id
        self.nodes: Dict[str, MapNode] = {}          # location_id -> MapNode
        self.connections: List[MapConnection] = []    # All connections
        self.regions: Dict[str, MapRegion] = {}       # region_id -> MapRegion
        self.current_location: str = ""               # Current location ID
    
    def build_from_locations(self, locations: Dict[str, 'Location'], 
                              npc_locations: Dict[str, List[str]] = None,
                              quest_locations: List[str] = None):
        """Generate map from Location objects.
        
        Args:
            locations: Dict of location_id -> Location
            npc_locations: Dict of location_id -> list of NPC IDs (optional)
            quest_locations: List of location IDs with active quests (optional)
        """
        if npc_locations is None:
            npc_locations = {}
        if quest_locations is None:
            quest_locations = []
        
        # Build nodes from locations
        for loc_id, loc in locations.items():
            # Determine danger level from atmosphere
            danger = "safe"
            if loc.atmosphere:
                danger = loc.atmosphere.danger_level or "safe"
            
            # Check for shop NPCs
            has_shop = False
            npcs_at_loc = npc_locations.get(loc_id, []) or loc.npcs
            # We'd need to check NPC roles, but for now just check if any NPCs present
            has_npc = len(npcs_at_loc) > 0
            
            # Check for quests
            has_quest = loc_id in quest_locations
            
            self.nodes[loc_id] = MapNode(
                location_id=loc_id,
                x=loc.map_x,
                y=loc.map_y,
                icon=loc.map_icon,
                label=loc.map_label or loc.name,
                is_visited=loc.visited,
                is_visible=not loc.map_hidden or loc.visited,
                is_accessible=True,  # Will be updated based on locked exits
                danger_level=danger,
                has_shop=has_shop,
                has_quest=has_quest,
                has_npc=has_npc
            )
        
        # Build connections from exits (deduplicate bidirectional)
        seen_connections = set()
        for loc_id, loc in locations.items():
            for exit_name, dest_id in loc.exits.items():
                if dest_id in self.nodes:
                    # Create a canonical key for bidirectional deduplication
                    conn_key = tuple(sorted([loc_id, dest_id]))
                    if conn_key not in seen_connections:
                        seen_connections.add(conn_key)
                        
                        # Check if connection is locked
                        is_locked = False
                        for cond in loc.exit_conditions:
                            if cond.exit_name == exit_name:
                                is_locked = True
                                break
                        
                        self.connections.append(MapConnection(
                            from_id=loc_id,
                            to_id=dest_id,
                            is_bidirectional=True,
                            is_locked=is_locked
                        ))
    
    def add_region(self, region: MapRegion):
        """Add a map region."""
        self.regions[region.id] = region
    
    def update_current(self, location_id: str):
        """Update current location marker."""
        self.current_location = location_id
        for node in self.nodes.values():
            node.is_current = (node.location_id == location_id)
    
    def mark_visited(self, location_id: str):
        """Mark location as visited (reveal fog of war)."""
        if location_id in self.nodes:
            self.nodes[location_id].is_visited = True
            self.nodes[location_id].is_visible = True
    
    def reveal_adjacent(self, location_id: str, locations: Dict[str, 'Location']):
        """Reveal nodes adjacent to visited location."""
        if location_id in locations:
            loc = locations[location_id]
            for dest_id in loc.exits.values():
                if dest_id in self.nodes:
                    self.nodes[dest_id].is_visible = True
    
    def unlock_connection(self, from_id: str, to_id: str):
        """Unlock a locked connection."""
        for conn in self.connections:
            if (conn.from_id == from_id and conn.to_id == to_id) or \
               (conn.from_id == to_id and conn.to_id == from_id and conn.is_bidirectional):
                conn.is_locked = False
    
    def get_clickable_nodes(self) -> List[MapNode]:
        """Get nodes player can click to travel to."""
        if not self.current_location:
            return []
        
        # Find adjacent locations
        adjacent = set()
        for conn in self.connections:
            if not conn.is_visible:
                continue
            if conn.from_id == self.current_location:
                adjacent.add(conn.to_id)
            if conn.to_id == self.current_location and conn.is_bidirectional:
                adjacent.add(conn.from_id)
        
        return [
            node for node in self.nodes.values()
            if node.location_id in adjacent
            and node.is_visible
            and node.is_accessible
        ]
    
    def get_all_visible_nodes(self) -> List[MapNode]:
        """Get all visible nodes for rendering."""
        return [node for node in self.nodes.values() if node.is_visible]
    
    def get_visible_connections(self) -> List[MapConnection]:
        """Get connections between visible nodes."""
        visible_ids = {n.location_id for n in self.get_all_visible_nodes()}
        return [
            conn for conn in self.connections
            if conn.is_visible and conn.from_id in visible_ids and conn.to_id in visible_ids
        ]
    
    def to_dict(self) -> dict:
        """Serialize entire map state for API."""
        return {
            "scenario_id": self.scenario_id,
            "current_location": self.current_location,
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
            "connections": [c.to_dict() for c in self.connections if c.is_visible],
            "regions": {k: v.to_dict() for k, v in self.regions.items()}
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'WorldMap':
        """Create from dictionary."""
        world_map = cls(scenario_id=data.get("scenario_id", ""))
        world_map.current_location = data.get("current_location", "")
        
        # Load nodes
        nodes_data = data.get("nodes", {})
        for node_id, node_data in nodes_data.items():
            world_map.nodes[node_id] = MapNode.from_dict(node_data)
        
        # Load connections
        connections_data = data.get("connections", [])
        for conn_data in connections_data:
            world_map.connections.append(MapConnection.from_dict(conn_data))
        
        # Load regions
        regions_data = data.get("regions", {})
        for region_id, region_data in regions_data.items():
            world_map.regions[region_id] = MapRegion.from_dict(region_data)
        
        return world_map


class LocationManager:
    """Manages player location and movement within a scenario."""
    
    def __init__(self):
        self.locations: Dict[str, Location] = {}
        self.current_location_id: Optional[str] = None
        self.available_location_ids: List[str] = []  # Locations unlocked by current scene
        self.discovered_secrets: List[str] = []  # Phase 3.2.1 Priority 8: Hidden locations that have been revealed
    
    def add_location(self, location: Location):
        """Register a location."""
        self.locations[location.id] = location
    
    def set_available_locations(self, location_ids: List[str]):
        """Set which locations are currently accessible (based on scene)."""
        self.available_location_ids = location_ids
    
    def set_current_location(self, location_id: str) -> Optional[Location]:
        """Set the current location. Returns the location or None if invalid."""
        if location_id in self.locations:
            self.current_location_id = location_id
            location = self.locations[location_id]
            # Increment visit count (Phase 3.2.1 Priority 7)
            location.visit_count += 1
            if not location.visited:
                location.visited = True
            return location
        return None
    
    def get_current_location(self) -> Optional[Location]:
        """Get the current location."""
        if self.current_location_id:
            return self.locations.get(self.current_location_id)
        return None
    
    def get_exits(self) -> Dict[str, str]:
        """Get available exits from current location.
        
        Filters out:
        - Exits to locations not in available_location_ids
        - Exits to hidden locations that haven't been discovered (Phase 3.2.1 Priority 8)
        """
        location = self.get_current_location()
        if location:
            result = {}
            for exit_name, dest_id in location.exits.items():
                # Check if destination is available in current scene
                if dest_id not in self.available_location_ids:
                    continue
                    
                # Check if destination is hidden (Phase 3.2.1 Priority 8)
                dest_location = self.locations.get(dest_id)
                if dest_location and dest_location.hidden:
                    # Only show if discovered
                    if dest_id not in self.discovered_secrets:
                        continue
                
                result[exit_name] = dest_id
            return result
        return {}
    
    def move(self, direction: str, game_state: dict = None) -> Tuple[bool, Optional[Location], str, List[LocationEvent]]:
        """
        Attempt to move in a direction.
        
        Args:
            direction: Direction or exit name to move toward. Supports:
                       - Cardinal aliases: n/s/e/w
                       - Exit names: "tavern", "outside"
                       - Natural language: "to the village square", "towards the forest"
                       - Destination matching: "village square" matches exit leading to village_square
            game_state: Optional dict with 'character', 'inventory', 'visited_locations' 
                       for checking exit conditions (locked doors, skill checks, etc.)
        
        Returns: (success, new_location, message, triggered_events)
            - success: Whether movement was successful
            - new_location: The new Location object if successful
            - message: Error message if failed, or special commands like "skill_check:strength:15"
            - triggered_events: List of events that fired on entry (empty if none)
        """
        location = self.get_current_location()
        if not location:
            return False, None, "You are nowhere.", []
        
        # Reject empty or whitespace-only direction
        if not direction or not direction.strip():
            return False, None, "You need to specify a direction.", []
        
        # Normalize direction (expand n → north, strip filler words)
        direction_lower = direction.lower().strip()
        expanded_direction = resolve_direction_alias(direction_lower)
        normalized_direction = normalize_travel_input(direction_lower)
        
        # Check for matching exit
        available_exits = self.get_exits()
        dest_id = None
        matched_exit_name = None
        
        # Phase 3.2.1 Priority 6: Check direction_aliases first
        # If player typed 'n' or 'north', check if location has alias mapping
        if location.direction_aliases:
            # Check if the expanded direction (e.g., "north") maps to an exit
            if expanded_direction in location.direction_aliases:
                alias_target = location.direction_aliases[expanded_direction]
                if alias_target in available_exits:
                    dest_id = available_exits[alias_target]
                    matched_exit_name = alias_target
            # Also check original shorthand (e.g., "n")
            elif direction_lower in location.direction_aliases:
                alias_target = location.direction_aliases[direction_lower]
                if alias_target in available_exits:
                    dest_id = available_exits[alias_target]
                    matched_exit_name = alias_target
        
        # If no alias matched, try exact exit name match
        if not dest_id:
            if direction_lower in available_exits:
                dest_id = available_exits[direction_lower]
                matched_exit_name = direction_lower
            elif normalized_direction in available_exits:
                # Try normalized (stripped filler words)
                dest_id = available_exits[normalized_direction]
                matched_exit_name = normalized_direction
            else:
                # Try partial match on exit name
                # Require at least 3 characters to avoid false positives like "in" matching "tavern"
                for exit_name, exit_dest_id in available_exits.items():
                    exit_lower = exit_name.lower()
                    # Only do partial matching for search terms >= 3 chars
                    if len(normalized_direction) >= 3:
                        if normalized_direction in exit_lower or exit_lower in normalized_direction:
                            dest_id = exit_dest_id
                            matched_exit_name = exit_name
                            break
        
        # NEW: Destination-based matching - match against where exits lead
        # Allows "go to village square" to work even if exit is named "outside"
        if not dest_id:
            for exit_name, exit_dest_id in available_exits.items():
                dest_location = self.locations.get(exit_dest_id)
                if dest_location:
                    # Check if normalized direction matches destination
                    if fuzzy_location_match(normalized_direction, exit_dest_id, dest_location.name):
                        dest_id = exit_dest_id
                        matched_exit_name = exit_name
                        break
        
        if dest_id and matched_exit_name:
            # Phase 3.2.1 Priority 6: Check exit conditions
            exit_cond = location.get_exit_condition(matched_exit_name)
            if exit_cond and not location.is_exit_unlocked(matched_exit_name):
                # Check if condition is met
                if game_state:
                    success, reason = check_exit_condition(exit_cond.condition, game_state)
                    if not success:
                        # Condition not met - blocked
                        fail_msg = exit_cond.fail_message or reason or "You can't go that way."
                        return False, None, fail_msg, []
                    elif reason.startswith("skill_check:"):
                        # Skill check needed - return special message for game.py to handle
                        return False, None, reason, []
                    else:
                        # Condition met - unlock the exit
                        location.unlock_exit(matched_exit_name)
                        # If consume_item is True, remove the key from inventory
                        if exit_cond.consume_item and exit_cond.condition.startswith("has_item:"):
                            item_key = exit_cond.condition.split(":")[1]
                            # The actual removal happens in game.py since we don't have inventory methods here
                            # We'll add a marker to the message
                            reason = f"CONSUME_ITEM:{item_key}|{reason}"
                else:
                    # No game_state provided, can't check conditions
                    fail_msg = exit_cond.fail_message or "Something blocks your path."
                    return False, None, fail_msg, []
            
            # Check if this will be a first visit BEFORE setting current location
            target_location = self.locations.get(dest_id)
            is_first_visit = target_location and not target_location.visited
            
            # Perform the move
            new_location = self.set_current_location(dest_id)
            if new_location:
                # Get events that should fire on entry
                events = new_location.get_events_for_trigger(
                    EventTrigger.ON_ENTER, 
                    is_first_visit=is_first_visit
                )
                
                # Mark events as triggered
                for event in events:
                    new_location.trigger_event(event.id)
                
                return True, new_location, "", events
        
        # No valid exit found
        valid_exits = list(available_exits.keys())
        if valid_exits:
            return False, None, f"You can't go '{direction}'. Available exits: {', '.join(valid_exits)}", []
        return False, None, "There's nowhere to go from here.", []
    
    def check_random_encounter(self, game_state: dict = None) -> Optional[RandomEncounter]:
        """
        Check if a random encounter triggers at the current location.
        
        Should be called after successful movement to a new location.
        
        Args:
            game_state: Optional dict for checking encounter conditions
            
        Returns:
            RandomEncounter if one triggers, None otherwise
        """
        location = self.get_current_location()
        if location and location.random_encounters:
            return location.check_random_encounter(game_state)
        return None
    
    def get_context_for_dm(self) -> str:
        """Get location context for the AI DM."""
        location = self.get_current_location()
        if not location:
            return ""
        
        context = f"""
=== CURRENT LOCATION: {location.name} ===
{location.description}
Atmosphere: {location.atmosphere}
{location.get_exits_display()}
"""
        if location.npcs:
            context += f"\nNPCs present: {', '.join(location.npcs)}"
        if location.items:
            context += f"\nItems here: {', '.join(location.items)}"
        
        # Phase 3.2.2: Fixed encounter info for predictable difficulty
        if location.encounter and not location.encounter_triggered:
            enemy_counts = {}
            for enemy in location.encounter:
                enemy_counts[enemy] = enemy_counts.get(enemy, 0) + 1
            encounter_desc = ", ".join([f"{count} {name}{'s' if count > 1 else ''}" for name, count in enemy_counts.items()])
            combat_tag = ", ".join(location.encounter)
            context += f"\n\n⚔️ FIXED ENCOUNTER (not yet triggered): {encounter_desc}"
            context += f"\nWhen combat starts here, you MUST use EXACTLY: [COMBAT: {combat_tag}]"
            context += f"\nDo NOT vary the enemy count - this ensures fair, balanced difficulty."
        elif location.encounter and location.encounter_triggered:
            context += f"\n\n✓ Encounter already completed at this location."
        
        return context
    
    def to_dict(self) -> dict:
        """Serialize location manager state for saving."""
        return {
            "current_location_id": self.current_location_id,
            "available_location_ids": self.available_location_ids.copy(),
            "discovered_secrets": self.discovered_secrets.copy(),  # Phase 3.2.1 Priority 8
            "location_states": {
                loc_id: loc.to_dict() 
                for loc_id, loc in self.locations.items()
            }
        }
    
    def restore_state(self, state: dict):
        """Restore state from saved data."""
        self.current_location_id = state.get("current_location_id")
        self.available_location_ids = state.get("available_location_ids", [])
        self.discovered_secrets = state.get("discovered_secrets", [])  # Phase 3.2.1 Priority 8
        
        # Restore individual location states
        location_states = state.get("location_states", {})
        for loc_id, loc_state in location_states.items():
            if loc_id in self.locations:
                Location.from_state(self.locations[loc_id], loc_state)
    
    # =========================================================================
    # SECRET DISCOVERY SYSTEM (Phase 3.2.1 - Priority 8)
    # =========================================================================
    
    def discover_secret(self, location_id: str) -> bool:
        """
        Mark a hidden location as discovered.
        
        Args:
            location_id: The ID of the hidden location to reveal
            
        Returns:
            True if location was hidden and is now discovered, False otherwise
        """
        location = self.locations.get(location_id)
        if not location or not location.hidden:
            return False
        
        if location_id not in self.discovered_secrets:
            self.discovered_secrets.append(location_id)
            return True
        return False  # Already discovered
    
    def is_secret_discovered(self, location_id: str) -> bool:
        """Check if a hidden location has been discovered."""
        return location_id in self.discovered_secrets
    
    def get_hidden_exits(self) -> Dict[str, str]:
        """
        Get exits that are currently hidden (not discovered).
        
        Returns:
            Dict mapping exit name to destination location ID for hidden exits
        """
        location = self.get_current_location()
        if not location:
            return {}
        
        hidden = {}
        for exit_name, dest_id in location.exits.items():
            if dest_id not in self.available_location_ids:
                continue
            
            dest_location = self.locations.get(dest_id)
            if dest_location and dest_location.hidden:
                if dest_id not in self.discovered_secrets:
                    hidden[exit_name] = dest_id
        
        return hidden
    
    def get_discovery_hints(self) -> List[str]:
        """
        Get discovery hints for any hidden exits from current location.
        
        Returns:
            List of hint strings for hidden locations
        """
        hints = []
        hidden_exits = self.get_hidden_exits()
        
        for exit_name, dest_id in hidden_exits.items():
            dest_location = self.locations.get(dest_id)
            if dest_location and dest_location.discovery_hint:
                hints.append(dest_location.discovery_hint)
        
        return hints
    
    def check_discovery(self, location_id: str, game_state: dict = None) -> Tuple[bool, str]:
        """
        Check if discovery conditions are met for a hidden location.
        
        Condition formats supported:
        - "skill:perception:14" - Requires perception skill check DC 14
        - "has_item:map" - Requires player has specific item
        - "level:5" - Requires player level 5+
        - "visited:cave_entrance" - Requires visiting another location first
        - "cond1 OR cond2" - Either condition can be met (Phase 3.6.3)
        
        Args:
            location_id: The hidden location to check discovery for
            game_state: Dict with 'character', 'inventory', 'visited_locations'
            
        Returns:
            (can_discover, requirement_message)
            - can_discover: True if conditions met or no condition
            - requirement_message: String describing what's needed (e.g., "skill_check:perception:14")
        """
        location = self.locations.get(location_id)
        if not location:
            return False, "Location not found."
        
        if not location.hidden:
            return True, ""  # Not hidden, always accessible
        
        if location_id in self.discovered_secrets:
            return True, ""  # Already discovered
        
        if not location.discovery_condition:
            return True, ""  # No condition, always discoverable
        
        condition = location.discovery_condition
        
        # Handle OR conditions (Phase 3.6.3)
        if " OR " in condition:
            conditions = [c.strip() for c in condition.split(" OR ")]
            messages = []
            for sub_condition in conditions:
                # Temporarily set condition to check each
                can_discover, message = self._check_single_condition(sub_condition, game_state)
                if can_discover:
                    return True, ""  # Any condition met is enough
                messages.append(message)
            # Return combined message if none met
            return False, " or ".join(messages)
        
        return self._check_single_condition(condition, game_state)
    
    def _check_single_condition(self, condition: str, game_state: dict = None) -> Tuple[bool, str]:
        """Check a single discovery condition (helper for OR logic)."""
        # Parse condition
        if condition.startswith("skill:"):
            # Format: "skill:perception:14"
            parts = condition.split(":")
            if len(parts) == 3:
                skill = parts[1]
                dc = parts[2]
                return False, f"skill_check:{skill}:{dc}"
            return False, "Invalid skill condition."
        
        elif condition.startswith("has_item:"):
            # Format: "has_item:treasure_map"
            item_key = condition.split(":")[1] if ":" in condition else ""
            if game_state and "inventory" in game_state:
                inventory = game_state["inventory"]
                # Support both list inventory and objects with has_item method
                if hasattr(inventory, "has_item"):
                    if inventory.has_item(item_key):
                        return True, ""
                elif isinstance(inventory, list):
                    # List of items - check if any item.name matches
                    normalized = item_key.lower().replace(" ", "_")
                    for item in inventory:
                        if hasattr(item, 'name') and item.name.lower().replace(" ", "_") == normalized:
                            return True, ""
                        elif isinstance(item, str) and item.lower().replace(" ", "_") == normalized:
                            return True, ""
            return False, f"Requires item: {item_key.replace('_', ' ')}"
        
        elif condition.startswith("level:"):
            # Format: "level:5"
            required_level = int(condition.split(":")[1]) if ":" in condition else 1
            if game_state and "character" in game_state:
                character = game_state["character"]
                if hasattr(character, "level") and character.level >= required_level:
                    return True, ""
            return False, f"Requires level {required_level}+"
        
        elif condition.startswith("visited:"):
            # Format: "visited:cave_entrance"
            required_location = condition.split(":")[1] if ":" in condition else ""
            if game_state and "visited_locations" in game_state:
                if required_location in game_state["visited_locations"]:
                    return True, ""
            prereq = self.locations.get(required_location)
            prereq_name = prereq.name if prereq else required_location
            return False, f"Must first visit: {prereq_name}"
        
        return True, ""  # Unknown condition type, allow by default


# =============================================================================
# SCENE SYSTEM
# =============================================================================

@dataclass
class Scene:
    """Represents a single scene in the scenario."""
    
    id: str                         # Unique identifier
    name: str                       # Display name
    description: str                # What this scene is about
    
    # AI Guidance
    setting: str                    # Where this takes place
    mood: str                       # Tone: "tense", "mysterious", "lighthearted"
    dm_instructions: str            # Specific guidance for AI
    
    # Pacing
    min_exchanges: int = 2          # Minimum player actions before can transition
    
    # Objectives (optional)
    objectives: List[str] = field(default_factory=list)
    objective_xp: Dict[str, int] = field(default_factory=dict)  # Phase 3.2.2: XP per objective
    
    # Transition
    transition_hint: str = ""       # What triggers moving to next scene
    next_scene_id: Optional[str] = None  # ID of next scene (None = scenario end)
    
    # Location System (Phase 3.2)
    location_ids: List[str] = field(default_factory=list)  # Available locations in this scene
    starting_location_id: Optional[str] = None              # Where player starts in this scene
    
    # Runtime state
    status: SceneStatus = SceneStatus.LOCKED
    exchange_count: int = 0
    objectives_complete: List[str] = field(default_factory=list)


@dataclass
class Scenario:
    """A complete adventure/scenario with multiple scenes."""
    
    id: str                         # Unique identifier
    name: str                       # Display name (e.g., "The Goblin Cave")
    description: str                # Brief summary
    
    # Story info
    hook: str                       # Opening hook/premise
    estimated_duration: str         # E.g., "15-30 minutes"
    
    # Scenes
    scenes: Dict[str, Scene] = field(default_factory=dict)
    scene_order: List[str] = field(default_factory=list)
    
    # Location System (Phase 3.2)
    location_manager: Optional[LocationManager] = field(default=None)
    
    # NPC System (Phase 3.3)
    npc_manager: Optional[NPCManager] = field(default=None)
    
    # Runtime state
    current_scene_id: Optional[str] = None
    is_complete: bool = False
    
    def __post_init__(self):
        """Initialize location manager and NPC manager if not provided."""
        if self.location_manager is None:
            self.location_manager = LocationManager()
        if self.npc_manager is None:
            self.npc_manager = NPCManager()
    
    def _setup_scene_locations(self, scene: Scene):
        """Set up locations for a scene."""
        if self.location_manager and scene.location_ids:
            self.location_manager.set_available_locations(scene.location_ids)
            if scene.starting_location_id:
                self.location_manager.set_current_location(scene.starting_location_id)
    
    def start(self) -> Scene:
        """Start the scenario, return first scene."""
        if not self.scene_order:
            raise ValueError("Scenario has no scenes!")
        
        first_scene_id = self.scene_order[0]
        self.current_scene_id = first_scene_id
        first_scene = self.scenes[first_scene_id]
        first_scene.status = SceneStatus.ACTIVE
        
        # Set up locations for the first scene
        self._setup_scene_locations(first_scene)
        
        return first_scene
    
    def get_current_scene(self) -> Optional[Scene]:
        """Get the currently active scene."""
        if self.current_scene_id:
            return self.scenes.get(self.current_scene_id)
        return None
    
    def record_exchange(self):
        """Record a player exchange in the current scene."""
        scene = self.get_current_scene()
        if scene:
            scene.exchange_count += 1
    
    def complete_objective(self, objective_id: str) -> tuple:
        """
        Mark an objective as complete. 
        Returns (success: bool, xp_reward: int).
        Phase 3.2.2: Now returns XP to award.
        """
        scene = self.get_current_scene()
        if scene and objective_id in scene.objectives:
            if objective_id not in scene.objectives_complete:
                scene.objectives_complete.append(objective_id)
                xp = scene.objective_xp.get(objective_id, 0)
                return True, xp
            return True, 0  # Already complete, no XP
        return False, 0
    
    def can_transition(self) -> bool:
        """Check if current scene can transition to next."""
        scene = self.get_current_scene()
        if not scene:
            return False
        
        # Must have minimum exchanges
        if scene.exchange_count < scene.min_exchanges:
            return False
        
        # Must have all objectives complete (if any)
        if scene.objectives:
            for obj in scene.objectives:
                if obj not in scene.objectives_complete:
                    return False
        
        return True
    
    def transition_to_next(self) -> Optional[Scene]:
        """Transition to the next scene. Returns new scene or None if complete."""
        scene = self.get_current_scene()
        if not scene:
            return None
        
        # Mark current as complete
        scene.status = SceneStatus.COMPLETED
        
        # Check if there's a next scene
        if scene.next_scene_id:
            self.current_scene_id = scene.next_scene_id
            next_scene = self.scenes[scene.next_scene_id]
            next_scene.status = SceneStatus.ACTIVE
            
            # Set up locations for the new scene
            self._setup_scene_locations(next_scene)
            
            return next_scene
        else:
            self.is_complete = True
            self.current_scene_id = None
            return None
    
    def get_scene_context_for_dm(self) -> str:
        """Generate context string for the AI DM."""
        scene = self.get_current_scene()
        if not scene:
            if self.is_complete:
                return "\nSCENARIO COMPLETE: Wrap up the adventure with a satisfying conclusion.\n"
            return ""
        
        context = f"""
=== CURRENT SCENE: {scene.name} ===
Setting: {scene.setting}
Mood: {scene.mood}

{scene.dm_instructions}

PACING:
- Exchanges so far: {scene.exchange_count}/{scene.min_exchanges} minimum
- {"Take your time, build atmosphere" if scene.exchange_count < scene.min_exchanges else "Player has explored enough, transition when appropriate"}
"""
        
        # Add location context if available
        if self.location_manager and self.location_manager.get_current_location():
            context += self.location_manager.get_context_for_dm()
        
        if scene.objectives:
            complete = scene.objectives_complete
            pending = [o for o in scene.objectives if o not in complete]
            context += f"\nOBJECTIVES:"
            context += f"\n- Complete: {', '.join(complete) if complete else 'None'}"
            context += f"\n- Pending: {', '.join(pending) if pending else 'None'}"
        
        if scene.transition_hint:
            context += f"\n\nTRANSITION TRIGGER: {scene.transition_hint}"
        
        return context
    
    def get_progress_display(self) -> str:
        """Get a progress bar/indicator for the player."""
        total = len(self.scene_order)
        if self.is_complete:
            current_idx = total
        elif self.current_scene_id:
            current_idx = self.scene_order.index(self.current_scene_id) + 1
        else:
            current_idx = 0
        
        scene = self.get_current_scene()
        scene_name = scene.name if scene else "Complete!"
        
        bar_filled = "█" * current_idx
        bar_empty = "░" * (total - current_idx)
        
        return f"[{bar_filled}{bar_empty}] Scene {current_idx}/{total}: {scene_name}"


# =============================================================================
# PREDEFINED SCENARIO: The Goblin Cave
# =============================================================================

def create_goblin_cave_npcs() -> NPCManager:
    """
    Create and return NPCManager with all NPCs for the Goblin Cave scenario.
    
    This is a scenario-specific factory function. Each scenario/DLC should
    define its own NPC factory function to create its unique NPCs.
    
    Pattern for new scenarios:
        def create_my_scenario_npcs() -> NPCManager:
            manager = NPCManager()
            manager.add_npc(NPC(id="...", name="...", ...))
            return manager
    """
    manager = NPCManager()
    
    # =========================================================================
    # TAVERN NPCs
    # =========================================================================
    
    bram = NPC(
        id="bram",
        name="Bram",
        description="A panicked farmer in his 40s with bloodshot eyes from sleepless nights. "
                   "His daughter Lily was kidnapped by goblins, and trauma has made his memory unreliable.",
        role=NPCRole.QUEST_GIVER,
        location_id="tavern_main",
        dialogue={
            "greeting": "Please, you have to help me! The goblins - they took my Lily!",
            "quest": "They came at night - a whole swarm of them! Or... or maybe just a few, but they moved "
                    "so fast in the dark. Dragged her off toward Darkhollow Cave. "
                    "I'll give you everything I have - 50 gold - just bring her back safely!",
            "about_goblins": "*wrings hands nervously* Wicked little creatures. I saw six or seven... "
                           "maybe more? It was dark, I could barely see. They moved like shadows, like wolves. "
                           "Or was it four? I can't... I can't remember clearly.",
            "about_lily": "She's only sixteen. Strong-willed, like her mother was. She'll be fighting them, I know it. "
                         "*voice cracks* She has to be okay. She HAS to be.",
            "about_cave": "Darkhollow Cave, half a day east through the Whisperwood. Dark place. Bad reputation. "
                         "*shudders* The villagers tell stories about it. I never believed them until now.",
            "farewell": "*grabs player's arm* Please hurry. Every moment they have her... I can't bear it."
        },
        disposition=30,  # Desperate and hopeful toward player
        quests=["rescue_lily"],
        personality=Personality(
            traits=["desperate", "loving father", "unreliable witness", "prone to panic"],
            speech_style="fragmented, interrupts himself, repeats key points",
            voice_notes="voice trembles and cracks, speaks rapidly when emotional",
            motivations=["save daughter Lily", "keep family safe"],
            fears=["losing Lily forever", "goblins returning", "being helpless"],
            quirks=["wrings hands when anxious", "grabs listener's arm for emphasis", "contradicts his own numbers"],
            secrets=["only saw 3-4 goblins but panic made him think there were more", 
                    "blames himself for not being home that night"]
        ),
        skill_check_options=[
            SkillCheckOption(
                id="upfront_payment",
                skill="persuasion",
                dc=14,
                description="Ask Bram for an advance payment before the dangerous mission",
                success_effect="gold:25",
                success_dialogue="*sighs heavily* You're right, you're right... you'll need supplies. "
                               "Here's 25 gold now - it's half my savings. Please, just bring her back!",
                failure_dialogue="I... I can't spare any coin until I know she's safe. "
                               "What if you take my money and never return? Please understand..."
            ),
            SkillCheckOption(
                id="better_reward",
                skill="persuasion",
                dc=16,
                description="Negotiate a higher reward for the dangerous rescue mission",
                success_effect="flag:reward_bonus_25",
                success_dialogue="*swallows hard* You drive a hard bargain... but Lily's worth everything. "
                               "75 gold. I'll find a way. Just bring her home!",
                failure_dialogue="Fifty gold is all I have! *voice cracks* I'd give you the world if I could, "
                               "but I'm just a farmer. Please, don't abandon my Lily over coin..."
            )
        ]
    )
    manager.add_npc(bram)
    
    barkeep = NPC(
        id="barkeep",
        name="Greth the Barkeep",
        description="A stout, graying man with a watchful eye. Greth has run the Rusty Dragon tavern "
                   "for two decades and knows all the village gossip and tales from travelers.",
        role=NPCRole.INFO,
        location_id="tavern_bar",
        dialogue={
            "greeting": "What'll it be, traveler?",
            "about_goblins": "Those goblins have been getting bolder lately. Used to stay in their caves, "
                           "but now they're raiding farms. Something's stirred them up.",
            "about_cave": "Darkhollow Cave? Bad place. Old stories say it goes deep, connects to tunnels "
                         "that run under the mountains. Goblins have nested there for generations.",
            "about_village": "Small farming community. Good folk, but not fighters. When trouble comes, "
                           "they pray for adventurers like yourself.",
            "about_rumors": "Word is the goblins have a new chief. Bigger, smarter than the rest. "
                          "Some travelers went missing on the east road last month.",
            "about_help": "Looking for swords-for-hire? *nods toward corner* See that big fella Marcus? "
                        "He's a sellsword, been asking about Darkhollow himself. "
                        "*lowers voice* I've also heard there's an elf ranger out in the forest - Elira, "
                        "she's called. Lost her brother to those goblins. She's not in town, but you might "
                        "cross paths on the east road.",
            "farewell": "Safe travels. And watch your back in those woods."
        },
        disposition=0,  # Neutral
        personality=Personality(
            traits=["observant", "pragmatic", "discreet", "worldly-wise"],
            speech_style="measured and calm, never wastes words",
            voice_notes="low gravelly voice, pauses before answering sensitive questions",
            motivations=["keep tavern running", "protect villagers", "gather useful information"],
            fears=["village being destroyed", "trouble that's bad for business"],
            quirks=["wipes glasses while talking", "glances at door when discussing danger", 
                   "lowers voice for rumors"],
            secrets=["knows more about the goblins than he lets on", 
                    "has a hidden cellar in case the village is attacked"]
        ),
        skill_check_options=[
            SkillCheckOption(
                id="secret_intel",
                skill="persuasion",
                dc=10,
                description="Convince Greth to share his secret knowledge about the cave",
                success_effect="flag:knows_secret_tunnel",
                success_dialogue="*leans in close* Look, I don't tell everyone this... but there's an old "
                               "mining tunnel that comes up near the back of that cave. Hunters used it years ago. "
                               "Entrance is hidden by a boulder with a crack shaped like a lightning bolt. "
                               "Might give you an edge.",
                failure_dialogue="*shakes head* I've told you what I know. Anything else is just rumor "
                               "and speculation. Best not to go chasing shadows."
            ),
            SkillCheckOption(
                id="free_drink",
                skill="persuasion",
                dc=8,
                description="Talk Greth into a free drink for the road",
                success_effect="flag:free_drink",
                success_dialogue="*chuckles* You've got a silver tongue. One ale, on the house. "
                               "Consider it my investment in the village's safety.",
                failure_dialogue="Nothing's free in this world. Two copper for an ale, same as anyone."
            )
        ]
    )
    manager.add_npc(barkeep)
    
    # Marcus the Mercenary - Recruitable Fighter
    marcus = NPC(
        id="marcus",
        name="Marcus",
        description="A weathered sellsword with a scarred face and a well-maintained greatsword. "
                   "He sits alone at a corner table, nursing a drink and watching the room.",
        role=NPCRole.RECRUITABLE,
        location_id="tavern_main",
        dialogue={
            "greeting": "Looking for muscle? I'm between jobs. Name's Marcus.",
            "about_self": "Twenty years as a mercenary. Fought in the Border Wars, the Siege of Blackgate, "
                         "dozen smaller conflicts. I've killed more men than I care to remember.",
            "about_goblins": "Goblins are easy prey if you know what you're doing. Quick, cowardly, "
                           "but dangerous in numbers. They fight dirty.",
            "about_work": "My last employer couldn't pay. That's why I'm here, drinking away the last "
                         "of my coin. If you've got gold, I've got steel.",
            "recruit_accept": "Twenty-five gold and we have a deal. My sword is yours until the job's done.",
            "recruit_decline": "Convince me you're worth my time, or come back with coin. I don't work for free.",
            "farewell": "You know where to find me. The offer stands."
        },
        disposition=-5,  # Gruff, needs convincing
        is_recruitable=True,
        recruitment_condition="gold:25",  # OR logic: gold OR high charisma
        personality=Personality(
            traits=["gruff", "pragmatic", "experienced", "weary", "professional"],
            speech_style="direct and blunt, military precision, no wasted words",
            voice_notes="deep gravelly voice, speaks slowly and deliberately",
            motivations=["find steady work", "earn enough to retire", "stay alive"],
            fears=["dying poor and forgotten", "becoming what he's fought against"],
            quirks=["sharpens sword while talking", "checks exits when entering rooms", 
                   "never sits with back to door"],
            secrets=["deserted from army after war crimes he couldn't stomach",
                    "has a daughter in distant city he sends money to"]
        ),
        skill_check_options=[
            SkillCheckOption(
                id="appeal_to_honor",
                skill="persuasion",
                dc=15,
                description="Appeal to Marcus's sense of honor about rescuing an innocent girl",
                success_effect="flag:marcus_discounted",
                success_dialogue="*pauses mid-drink* A kidnapped girl? *sets down mug* "
                               "Damn it. Fine. Ten gold. I'm not a monster.",
                failure_dialogue="*shakes head* Honor doesn't pay for food and lodging. "
                               "Twenty-five gold or find another sword."
            ),
            SkillCheckOption(
                id="impress_with_knowledge",
                skill="history",
                dc=14,
                description="Recognize Marcus's unit insignia and impress him with military knowledge",
                success_effect="disposition:+15",
                success_dialogue="*eyes widen* You know the Black Wolves? *leans forward* "
                               "Not many remember. Maybe you're not just another greenhorn after all.",
                failure_dialogue="*grunts* Never heard of them? Typical. Kids these days know nothing of real war."
            )
        ]
    )
    manager.add_npc(marcus)
    
    # =========================================================================
    # FOREST NPCs (Recruitable)
    # =========================================================================
    
    elira = NPC(
        id="elira",
        name="Elira",
        description="A tall, lean elf woman with sharp eyes and a longbow across her back. "
                   "She moves with the quiet grace of a hunter. Her expression is grim, vengeful.",
        role=NPCRole.RECRUITABLE,
        location_id="forest_clearing",
        dialogue={
            "greeting": "You're heading to Darkhollow? So am I. Those goblins killed my brother.",
            "about_self": "I'm a ranger. I've been tracking this clan for three weeks. They ambushed a patrol "
                         "from my village. My brother was with them.",
            "about_goblins": "There's about a dozen in the main cave. But I've seen signs of more in the tunnels. "
                           "They're organized now. That's unusual for goblins.",
            "about_cave": "I've scouted the entrance. Two guards, usually drunk. "
                         "We could take them quietly if we work together.",
            "recruit_accept": "A fellow hunter? Very well. But understand - I'm not leaving until every last goblin pays.",
            "recruit_decline": "I work alone. Unless... you can prove you're worth trusting.",
            "farewell": "We'll meet again at the cave. Don't slow me down."
        },
        disposition=10,  # Slightly guarded but hopeful
        is_recruitable=True,
        recruitment_condition="skill:charisma:12",
        personality=Personality(
            traits=["vengeful", "skilled", "guarded", "grief-stricken", "deadly calm"],
            speech_style="clipped and direct, no pleasantries, tactical focus",
            voice_notes="cold and controlled, but voice tightens when mentioning brother",
            motivations=["avenge brother's death", "eliminate the goblin threat"],
            fears=["failing to avenge brother", "letting emotions compromise the mission"],
            quirks=["touches bow when talking about combat", "scans surroundings constantly",
                   "refuses to smile"],
            secrets=["secretly fears she's becoming consumed by vengeance",
                    "brother was trying to negotiate peace when killed"]
        ),
        skill_check_options=[
            SkillCheckOption(
                id="share_tracking_knowledge",
                skill="survival",
                dc=12,
                description="Demonstrate tracking skills to earn Elira's respect",
                success_effect="disposition:+15",
                success_dialogue="*raises eyebrow* You know how to read a trail. Good. "
                               "Perhaps you won't slow me down after all.",
                failure_dialogue="*shakes head* You'd miss a goblin track even if you stepped in it."
            ),
            SkillCheckOption(
                id="empathize_with_loss",
                skill="persuasion",
                dc=12,
                description="Share understanding of loss to connect with Elira",
                success_effect="disposition:+10",
                success_dialogue="*pauses, grip on bow softens* You understand. "
                               "Perhaps... we're not so different. Very well. Let's hunt together.",
                failure_dialogue="*cold stare* Don't pretend to understand my pain. You can't."
            ),
            SkillCheckOption(
                id="notice_brother_truth",
                skill="insight",
                dc=16,
                description="Sense that Elira is hiding something about her brother's death",
                success_effect="flag:knows_brother_truth",
                success_dialogue="*freezes* How did you...? *voice cracks* He was trying to negotiate. "
                               "Make peace. And they... *trails off* I should have stopped him.",
                failure_dialogue="*looks away* My brother died fighting. That's all you need to know."
            )
        ]
    )
    manager.add_npc(elira)
    
    # =========================================================================
    # CAVE NPCs
    # =========================================================================
    
    # Shade the Rogue - Recruitable, found hiding in shadows
    shade = NPC(
        id="shade",
        name="Shade",
        description="A hooded figure barely visible in the darkness. Quick eyes glint from beneath the cowl, "
                   "and a pair of daggers hang at their belt.",
        role=NPCRole.RECRUITABLE,
        location_id="goblin_camp_shadows",
        dialogue={
            "greeting": "So... you noticed me. Impressive. Most don't until it's too late.",
            "about_self": "Names are dangerous things to share in my line of work. Call me Shade. "
                         "I'm here for my own reasons.",
            "about_goblins": "These vermin stole something from my employer. I intend to retrieve it. "
                           "Our goals may align... temporarily.",
            "about_stealth": "I've been watching them for hours. The guards change every two hours, "
                           "the chief sleeps light, and there's a back passage they don't guard well.",
            "recruit_accept": "An alliance of convenience. I watch your back, you watch mine. "
                            "But don't expect me to stick around after we're done here.",
            "recruit_decline": "You'll need to prove you can move quietly before I trust you at my back. "
                             "Too many have gotten me caught before.",
            "farewell": "I'll be watching. If you survive, perhaps we'll talk again."
        },
        disposition=-10,  # Suspicious, hard to win over
        is_recruitable=True,
        recruitment_condition="skill:charisma:14",  # Hard to convince
        personality=Personality(
            traits=["mysterious", "calculating", "observant", "distrustful", "efficient"],
            speech_style="soft whispers, careful word choice, never reveals more than necessary",
            voice_notes="barely audible, pauses often as if listening for danger",
            motivations=["complete the mission", "survive", "uncover secrets"],
            fears=["betrayal", "being exposed", "losing the shadows"],
            quirks=["disappears mid-conversation", "appears from unexpected directions", 
                   "never makes eye contact for long"],
            secrets=["assassin sent to kill the goblin chief for political reasons",
                    "has killed before and will again if necessary"]
        ),
        skill_check_options=[
            SkillCheckOption(
                id="prove_stealth",
                skill="stealth",
                dc=12,
                description="Demonstrate your own stealth ability to earn Shade's respect",
                success_effect="disposition:+20",
                success_dialogue="*nods slowly* So... you know how to move. That's rare. "
                               "Perhaps you're not as clumsy as most who stumble through these caves.",
                failure_dialogue="*sighs* You move like a wounded bear. I heard you coming three chambers away."
            ),
            SkillCheckOption(
                id="read_intentions",
                skill="insight",
                dc=16,
                description="Perceive Shade's true mission and confront them",
                success_effect="flag:knows_shade_assassin",
                success_dialogue="*goes very still* ...You're perceptive. Yes. I'm here to kill the chief. "
                               "Someone powerful wants him dead. We can help each other.",
                failure_dialogue="*gives nothing away* I'm here for my own reasons. That's all you need to know."
            )
        ]
    )
    manager.add_npc(shade)
    
    lily = NPC(
        id="lily",
        name="Lily",
        description="A young woman of sixteen with dirty clothes and a defiant expression. "
                   "Despite her captivity, her spirit is unbroken.",
        role=NPCRole.INFO,
        location_id="goblin_camp_main",  # She's in a cage here
        dialogue={
            "greeting": "You came! Father sent you, didn't he?",
            "about_escape": "They keep the key on the big one's belt. The chief. He's in the back chamber.",
            "about_goblins": "There's so many of them. But at night, most of them sleep. That's when I've seen chances...",
            "about_chief": "He's different from the others. Bigger, smarter. He speaks Common! "
                         "I heard him talking about 'the tunnels' and 'the others below.'",
            "farewell": "Please be careful. And thank you."
        },
        disposition=50,  # Grateful and hopeful
        personality=Personality(
            traits=["brave", "resourceful", "observant", "hopeful despite fear"],
            speech_style="whispered urgency, quick to share useful info",
            voice_notes="hushed and hurried, glances at guards frequently",
            motivations=["escape captivity", "see father again", "help rescuers succeed"],
            fears=["being moved deeper into caves", "rescuers getting killed"],
            quirks=["grips cage bars when speaking", "listens for goblin footsteps mid-sentence"],
            secrets=["overheard goblins talking about 'something bigger' in the deep tunnels",
                    "has been secretly loosening a bar in her cage"]
        ),
        skill_check_options=[
            SkillCheckOption(
                id="pick_cage_lock",
                skill="sleight_of_hand",
                dc=12,
                description="Use your lockpicks to open Lily's cage",
                success_effect="flag:freed_lily_lockpicks",
                success_dialogue="*click* The lock gives way! Lily squeezes through the bars. "
                               "'You did it! I knew you could save me!'",
                failure_dialogue="The lock is more complex than you expected. The pick slips. "
                               "You'll need the key... or try again with steadier hands.",
                requires_item="lockpicks",
                consumes_item=True
            ),
            SkillCheckOption(
                id="bend_cage_bars",
                skill="athletics",
                dc=14,
                description="Use rope to bend the cage bars apart",
                success_effect="flag:freed_lily_rope",
                success_dialogue="You loop the rope around the weakest bar and pull with all your might. "
                               "*CREAK* The bar bends just enough for Lily to squeeze through! "
                               "'You're so strong!'",
                failure_dialogue="The bar groans but holds firm. You'll need more leverage... "
                               "or a different approach.",
                requires_item="rope",
                consumes_item=True
            ),
            SkillCheckOption(
                id="encourage_escape_help",
                skill="persuasion",
                dc=8,
                description="Convince Lily to share her secret about the loosened bar",
                success_effect="flag:knows_loose_bar",
                success_dialogue="*glances around* I... I've been working on one of the bars. "
                               "It's almost free. If you can distract the guards, I might be able to squeeze through!",
                failure_dialogue="I... I can't say more. The guards might hear. Please just get the key."
            ),
            SkillCheckOption(
                id="learn_deep_secret",
                skill="insight",
                dc=12,
                description="Notice Lily is holding back important information",
                success_effect="flag:knows_deep_tunnels",
                success_dialogue="*eyes widen* You can tell? I... I heard them talking. "
                               "There's something down there. In the deep tunnels. "
                               "Something even the goblins are afraid of. They call it 'the Old One.'",
                failure_dialogue="*looks away* There's nothing else. Please, just get me out of here."
            )
        ]
    )
    manager.add_npc(lily)
    
    # Chief Grotnak - Boss NPC with negotiation options
    grotnak = NPC(
        id="grotnak",
        name="Chief Grotnak",
        description="A massive goblin seated on a throne of bones and scrap metal. Unlike his smaller kin, "
                   "Grotnak stands nearly five feet tall with a cunning gleam in his yellow eyes. "
                   "He wears a crown of bent forks and speaks surprisingly good Common.",
        role=NPCRole.HOSTILE,
        location_id="boss_chamber",
        dialogue={
            "greeting": "*looks up from counting coins* Ah, a visitor! You come to steal from Grotnak? "
                       "Or maybe... we talk first? Grotnak is civilized goblin.",
            "about_self": "I am Chief! Greatest goblin in a hundred caves. I read books! "
                        "I speak human-talk! I am... evolved. *grins with pointed teeth*",
            "about_lily": "The girl? She is valuable. Father pays, or someone else pays. "
                        "*shrugs* Is business. You understand business?",
            "about_treasure": "My hoard? *clutches coin pouch* You want to trade? I respect trade. "
                            "But steal... stealing from Grotnak means death.",
            "threat_response": "*stands, drawing scimitar* So it is fighting you choose? "
                             "Then Grotnak shows you why he is CHIEF!",
            "deal_accept": "*narrows eyes* You drive hard bargain. But deal is deal. "
                         "Take girl. We not cross paths again. Go now, before I change mind.",
            "deal_decline": "*spits on floor* Then we have nothing more to say. "
                          "Boys! KILL THEM!",
            "farewell": "*waves dismissively* Go, go. Grotnak has coins to count."
        },
        disposition=-40,  # Hostile but will parley
        personality=Personality(
            traits=["cunning", "greedy", "surprisingly intelligent", "pragmatic", "cruel but reasonable"],
            speech_style="broken Common with occasional sophisticated words, third person references",
            voice_notes="deep gravelly voice, emphatic gestures, sudden mood shifts",
            motivations=["accumulate wealth", "maintain power", "prove goblin superiority"],
            fears=["being seen as weak", "losing his hoard", "the 'deeper things' in the tunnels"],
            quirks=["counts coins while talking", "refers to self in third person", 
                   "randomly uses big words incorrectly"],
            secrets=["traded with dark forces for intelligence", 
                    "knows about something terrible deeper in the caves",
                    "secretly fears his own bodyguards plotting against him"]
        ),
        skill_check_options=[
            SkillCheckOption(
                id="intimidate_release",
                skill="intimidation",
                dc=16,
                description="Intimidate Grotnak into releasing Lily without a fight",
                success_effect="flag:lily_freed_peacefully",
                success_dialogue="*eyes widen, steps back* You... you are strong. Grotnak sees this. "
                               "Take girl! Take her and go! Is not worth dying for one human.",
                failure_dialogue="*laughs* You try to scare GROTNAK? In his own lair? "
                               "Maybe Grotnak scare YOU instead! *draws weapon*"
            ),
            SkillCheckOption(
                id="deceive_distraction",
                skill="deception",
                dc=18,
                description="Deceive Grotnak with a lie about reinforcements coming",
                success_effect="flag:grotnak_distracted",
                success_dialogue="*looks toward tunnel nervously* An army? How many? "
                               "*barks at guards* Go check tunnels! All of you! "
                               "*mutters* Maybe Grotnak negotiate with army instead...",
                failure_dialogue="*sneers* You think Grotnak stupid? My scouts see nothing. "
                               "You lie to Grotnak? That costs extra... maybe costs your life."
            ),
            SkillCheckOption(
                id="negotiate_ransom",
                skill="persuasion",
                dc=14,
                description="Negotiate a reasonable ransom for Lily's release",
                success_effect="flag:ransom_deal",
                success_dialogue="*strokes chin* Fifty gold? Is... acceptable. Grotnak is fair goblin. "
                               "Gold for girl. Simple trade. We have deal.",
                failure_dialogue="*scoffs* Fifty gold? For valuable hostage? "
                               "You insult Grotnak! Price is now ONE HUNDRED gold or we fight!"
            )
        ]
    )
    manager.add_npc(grotnak)
    
    # =========================================================================
    # MERCHANT NPCs (Phase 3.3.3 - Shop System)
    # =========================================================================
    
    gavin = NPC(
        id="gavin",
        name="Gavin the Blacksmith",
        description="A burly man in his fifties with a soot-stained leather apron and arms like tree trunks. "
                   "His forge-roughened hands are surprisingly gentle with his craft.",
        role=NPCRole.MERCHANT,
        location_id="blacksmith_shop",
        dialogue={
            "greeting": "*wipes hands on apron* Welcome to me forge! Looking for steel?",
            "about_weapons": "Everything I make is battle-tested. Not like that mass-produced city rubbish. "
                           "Each blade has character.",
            "about_armor": "Good armor's like good ale - worth every coin. I've saved more lives "
                         "with me anvil than any healer.",
            "about_goblins": "*scowls* Nasty business. If you're heading to Darkhollow, you'll want "
                           "proper equipment. Those little blighters are vicious.",
            "about_lily": "Bram's girl? Sweet child. I hope someone finds her. *sets down hammer* "
                        "Tell you what - help rescue her, and I'll give you a discount.",
            "haggle_success": "*chuckles* Sharp tongue you've got. Fine, I can work with that price.",
            "haggle_fail": "*frowns* I've got a business to run. Price is what it is.",
            "farewell": "May your steel stay sharp and your armor hold true!"
        },
        disposition=10,  # Neutral-friendly, business-like
        personality=Personality(
            traits=["gruff", "honest", "proud of craft", "protective of village"],
            speech_style="direct, occasional forge metaphors, northern accent",
            voice_notes="deep gravelly voice, rhythmic like hammer strikes",
            motivations=["run a successful business", "protect the village", "craft the finest steel"],
            fears=["seeing young people die with poor equipment", "the village falling to threats"],
            quirks=["taps anvil when thinking", "judges people by their weapon maintenance"],
            secrets=["served as a soldier decades ago", "hides a masterwork sword under the forge for emergencies"]
        ),
        skill_check_options=[
            SkillCheckOption(
                id="haggle_discount",
                skill="persuasion",
                dc=12,
                description="Haggle for better prices at the forge",
                success_effect="flag:gavin_discount",
                success_dialogue="*chuckles* Sharp tongue you've got! Fine, 10% off for you. "
                               "But don't go telling everyone, or I'll have no business left!",
                failure_dialogue="*frowns* I've got costs to cover. Price is fair, take it or leave it."
            ),
            SkillCheckOption(
                id="soldier_bond",
                skill="history",
                dc=14,
                description="Recognize Gavin's old military insignia and bond over shared knowledge",
                success_effect="disposition:+20",
                success_dialogue="*eyes widen* You recognize the Third Regiment? *grips your arm* "
                               "Been a long time since anyone remembered. *voice softens* "
                               "You need anything special, you come to me first.",
                failure_dialogue="*shrugs* Just an old decoration. Don't mean nothing anymore."
            ),
            SkillCheckOption(
                id="masterwork_reveal",
                skill="persuasion",
                dc=18,
                description="Convince Gavin to show you his hidden masterwork blade",
                success_effect="flag:knows_masterwork",
                success_dialogue="*looks around* You're serious about this, aren't you? "
                               "*pulls aside floorboard* This here... this is me finest work. "
                               "If things get truly dire... come back. We'll talk.",
                failure_dialogue="*shakes head* Some things aren't for sale. Or for showing."
            )
        ]
    )
    manager.add_npc(gavin)
    
    return manager


def create_goblin_cave_quests(quest_manager: QuestManager) -> None:
    """
    Create and register quests for the Goblin Cave scenario.
    
    Phase 3.3.4: Quest System Implementation
    
    Quests:
    - Rescue Lily (Main Quest): Save the farmer's daughter
    - Recover Heirlooms (Side Quest): Find stolen family items
    - Clear the Path (Side Quest): Eliminate threats on the forest road
    """
    
    # =========================================================================
    # MAIN QUEST: Rescue Lily
    # =========================================================================
    rescue_lily = Quest(
        id="rescue_lily",
        name="Rescue Lily",
        description="Farmer Bram's daughter Lily has been kidnapped by goblins and taken to Darkhollow Cave. Find her and bring her home safely.",
        giver_npc_id="bram",
        quest_type=QuestType.MAIN,
        objectives=[
            create_location_objective(
                "reach_cave",
                "Enter Darkhollow Cave",
                "cave_entrance"
            ),
            create_talk_objective(
                "find_lily",
                "Find and rescue Lily",
                "lily"
            ),
            create_location_objective(
                "return_lily",
                "Return Lily to the village",
                "tavern_celebration"
            )
        ],
        rewards={
            "xp": 100,
            "gold": 50,
            "items": ["healing_potion"]
        }
    )
    quest_manager.register_quest(rescue_lily)
    
    # =========================================================================
    # SIDE QUEST: Recover Heirlooms
    # =========================================================================
    recover_heirlooms = Quest(
        id="recover_heirlooms",
        name="Recover the Family Heirlooms",
        description="The goblins also stole family heirlooms during their raid - a silver locket and Bram's father's ring. Search the goblin lair to find them.",
        giver_npc_id="bram",
        quest_type=QuestType.MINOR,
        objectives=[
            create_find_objective(
                "find_locket",
                "Find the silver locket",
                "silver_locket"
            ),
            create_find_objective(
                "find_ring",
                "Find the family ring",
                "family_ring"
            )
        ],
        rewards={
            "xp": 50,
            "gold": 25
        },
        prerequisites=["rescue_lily"]  # Must accept main quest first
    )
    quest_manager.register_quest(recover_heirlooms)
    
    # =========================================================================
    # SIDE QUEST: Clear the Path
    # =========================================================================
    clear_path = Quest(
        id="clear_the_path",
        name="Clear the Path",
        description="Wolves and goblins have been threatening travelers on the road to Darkhollow. Eliminate them to make the path safer.",
        giver_npc_id="barkeep",
        quest_type=QuestType.SIDE,
        objectives=[
            create_kill_objective(
                "kill_wolves",
                "Eliminate wolves on the forest path",
                "wolf",
                count=2
            ),
            create_kill_objective(
                "kill_goblins",
                "Clear goblins from the cave",
                "goblin",
                count=6
            )
        ],
        rewards={
            "xp": 75,
            "gold": 30
        }
    )
    quest_manager.register_quest(clear_path)
    
    # =========================================================================
    # SIDE QUEST: The Chief's Treasure
    # =========================================================================
    chiefs_treasure = Quest(
        id="chiefs_treasure",
        name="The Chief's Treasure",
        description="Rumors say Chief Grotnak has amassed quite a hoard. Defeat him and claim the treasure for yourself.",
        giver_npc_id="barkeep",
        quest_type=QuestType.SIDE,
        objectives=[
            create_kill_objective(
                "defeat_chief",
                "Defeat Chief Grotnak",
                "goblin_chief",
                count=1
            ),
            create_location_objective(
                "find_treasure",
                "Discover the treasure nook",
                "treasure_nook"
            )
        ],
        rewards={
            "xp": 100,
            "gold": 100
        }
    )
    quest_manager.register_quest(chiefs_treasure)
    
    # =========================================================================
    # SIDE QUEST: Thin the Herd (Goblin Ear Bounty) - Phase 3.6.1
    # =========================================================================
    thin_the_herd = Quest(
        id="thin_the_herd",
        name="Thin the Herd",
        description="The village offers a bounty for proof of goblin kills. Bring back goblin ears as evidence.",
        giver_npc_id="barkeep",
        quest_type=QuestType.SIDE,
        objectives=[
            create_collect_objective(
                "collect_ears",
                "Collect 5 goblin ears",
                "goblin_ear",
                count=5
            )
        ],
        rewards={
            "xp": 50,
            "gold": 25
        }
    )
    quest_manager.register_quest(thin_the_herd)


def create_goblin_cave_shops(shop_manager: ShopManager) -> None:
    """
    Create and register shops for the Goblin Cave scenario.
    
    Phase 3.3.3: Shop System Implementation
    
    Shops:
    - Gavin's Forge (Blacksmith): Weapons and armor
    """
    
    # =========================================================================
    # GAVIN'S FORGE - Blacksmith Shop
    # =========================================================================
    gavins_forge = create_blacksmith_shop(
        id="gavins_forge",
        name="Gavin's Forge",
        owner_npc_id="gavin",
        location_id="blacksmith_shop",
        weapons={
            "dagger": -1,           # Unlimited stock
            "shortsword": 3,        # Limited stock
            "longsword": 2,
            "handaxe": 3,
            "club": -1,             # Unlimited
        },
        armor={
            "leather_armor": 2,
            "chain_shirt": 1,
            "shield": 3,
        },
        markup=1.15  # Fair prices for a village blacksmith
    )
    shop_manager.add_shop(gavins_forge)


def create_goblin_cave_scenario() -> Scenario:
    """Create the first starter scenario: The Goblin Cave."""
    
    # =========================================================================
    # MAP REGIONS (Phase 4.5 - World Map UI)
    # =========================================================================
    
    # Define the three main regions of the Goblin Cave scenario
    map_regions = [
        MapRegion(
            id="village",
            name="Willowbrook Village",
            description="A peaceful farming village, the starting point of your adventure.",
            bounds_x=0.0, bounds_y=0.0, bounds_width=1.0, bounds_height=0.20,
            background_color="#E8F5E9",  # Light green background
            border_color="#2E7D32",
            icon="🏘️"
        ),
        MapRegion(
            id="forest",
            name="Darkhollow Forest",
            description="An ancient forest with winding paths. Danger lurks deeper within.",
            bounds_x=0.0, bounds_y=0.20, bounds_width=1.0, bounds_height=0.35,
            background_color="#FFF3E0",  # Light orange background
            border_color="#E65100",
            icon="🌲"
        ),
        MapRegion(
            id="cave",
            name="Darkhollow Cave",
            description="The goblin lair. Chief Grotnak rules from his throne of bones.",
            bounds_x=0.0, bounds_y=0.55, bounds_width=1.0, bounds_height=0.45,
            background_color="#FFEBEE",  # Light red background
            border_color="#B71C1C",
            icon="🕳️"
        )
    ]
    
    # =========================================================================
    # LOCATIONS (Phase 3.2)
    # =========================================================================
    
    locations = {
        # === TAVERN SCENE LOCATIONS ===
        "tavern_main": Location(
            id="tavern_main",
            name="The Rusty Dragon - Main Room",
            description="A cozy common room with a crackling hearth. Wooden tables are scattered about, some occupied by locals nursing their drinks. A bar runs along one wall where Greth the barkeep polishes mugs.",
            exits={"bar": "tavern_bar", "outside": "village_square"},
            # Map coordinates for world map UI
            map_x=0.15, map_y=0.08, map_icon="🍺", map_region="village",
            direction_aliases={"n": "bar", "north": "bar", "s": "outside", "south": "outside"},
            npcs=["bram", "marcus", "locals"],
            items=["torch"],
            atmosphere=LocationAtmosphere(
                sounds=["crackling hearth", "murmured conversations", "clinking tankards", "occasional laughter", "creaking floorboards"],
                smells=["wood smoke", "spilled ale", "roasting meat", "pipe tobacco"],
                textures=["worn wooden tables", "sticky ale rings", "rough-hewn chairs"],
                lighting="warm firelight casting dancing shadows",
                temperature="comfortably warm from the hearth",
                mood="welcoming with undercurrents of worry",
                danger_level="safe",
                random_details=["a cat dozing by the fire", "a farmer's muddy boots by the door", "a wanted poster curling on the wall", "scratches on the floor from moved furniture"]
            ),
            enter_text="You push through the tavern door, warmth washing over you."
        ),
        "tavern_bar": Location(
            id="tavern_bar",
            name="The Rusty Dragon - Bar",
            description="A worn wooden bar with a gruff but friendly barkeep polishing mugs. Bottles line the shelves behind.",
            exits={"main room": "tavern_main"},
            # Map coordinates for world map UI
            map_x=0.15, map_y=0.02, map_icon="🍻", map_region="village",
            direction_aliases={"s": "main room", "south": "main room"},
            npcs=["barkeep"],
            items=[],
            atmosphere_text="Clinking glasses, the barkeep's watchful eye",
            enter_text="You approach the bar. The barkeep nods in greeting."
        ),
        "village_square": Location(
            id="village_square",
            name="Village Square",
            description="A small village square with a well at the center. Most shops are closed for the evening, but warm light and the clang of a hammer spill from the blacksmith's forge to the west.",
            exits={"tavern": "tavern_main", "east road": "forest_path", "forge": "blacksmith_shop"},
            # Map coordinates for world map UI
            map_x=0.50, map_y=0.08, map_icon="🏛️", map_region="village",
            direction_aliases={"n": "tavern", "north": "tavern", "e": "east road", "east": "east road", "w": "forge", "west": "forge", "blacksmith": "forge", "in": "forge", "inside": "forge", "enter": "forge"},
            npcs=[],
            items=[],
            atmosphere_text="Quiet evening, the rhythmic clang of a hammer from the forge, distant sounds of village life",
            enter_text="You step out into the cool evening air of the village square. The blacksmith's forge glows nearby to the west."
        ),
        "blacksmith_shop": Location(
            id="blacksmith_shop",
            name="Blacksmith's Forge",
            description="A warm, smoky forge with an anvil at the center. Weapons and armor hang on the walls, and the heat from the furnace fills the small shop.",
            exits={"outside": "village_square", "square": "village_square"},
            # Map coordinates for world map UI
            map_x=0.85, map_y=0.08, map_icon="🛠️", map_region="village",
            direction_aliases={"e": "outside", "east": "outside"},
            npcs=["gavin"],
            items=[],
            atmosphere_text="Heat from the forge, the smell of hot metal and coal, rhythmic hammering",
            enter_text="You step into the warmth of the forge."
        ),
        
        # === JOURNEY SCENE LOCATIONS ===
        "forest_path": Location(
            id="forest_path",
            name="Forest Path",
            description="A winding dirt path through an ancient forest. Autumn leaves crunch underfoot.",
            exits={"village": "village_square", "deeper": "forest_clearing", "east": "forest_clearing"},
            # Map coordinates for world map UI
            map_x=0.50, map_y=0.28, map_icon="🌲", map_region="forest",
            direction_aliases={"w": "village", "west": "village", "e": "deeper", "east": "deeper"},
            npcs=[],
            items=[],
            atmosphere_text="Dappled sunlight, bird calls, rustling leaves",
            enter_text="The village fades behind as you enter the forest.",
            # Phase 3.2.1 Priority 7: Random encounters
            random_encounters=[
                RandomEncounter(
                    id="wolf_ambush",
                    enemies=["wolf"],
                    chance=20,  # 20% chance on each visit
                    max_triggers=2,  # Can happen twice per playthrough
                    cooldown=3,  # Must wait 3 visits before can happen again
                    narration="A hungry wolf emerges from the underbrush, teeth bared!"
                )
            ]
        ),
        "forest_clearing": Location(
            id="forest_clearing",
            name="Forest Clearing",
            description="A small clearing where the path forks. An old signpost points east toward 'Darkhollow'.",
            exits={"back": "forest_path", "east": "darkhollow_approach", "cave": "darkhollow_approach", "hidden path": "secret_cave"},
            # Map coordinates for world map UI
            map_x=0.35, map_y=0.38, map_icon="🌳", map_region="forest",
            direction_aliases={"w": "back", "west": "back", "e": "east", "east": "east"},
            npcs=["elira"],
            items=["rations"],
            atmosphere_text="Birds go quiet here. An uneasy stillness.",
            enter_text="You emerge into a clearing. The trees seem to lean away from the eastern path."
        ),
        # === SECRET LOCATION (Phase 3.2.1 - Priority 8) ===
        "secret_cave": Location(
            id="secret_cave",
            name="Hidden Hollow",
            description="A small natural cave hidden behind overgrown vines. It's cool and quiet inside, clearly undisturbed for years.",
            exits={"out": "forest_clearing", "exit": "forest_clearing"},
            # Map coordinates for world map UI (hidden until discovered)
            map_x=0.20, map_y=0.42, map_icon="🔮", map_region="forest", map_hidden=True,
            direction_aliases={"w": "out", "west": "out"},
            npcs=[],
            items=["ancient_amulet", "healing_potion", "gold_coins"],
            atmosphere_text="Peaceful, ancient, the scent of old magic",
            enter_text="You push through the vines and discover a hidden hollow. Treasure glints in the dim light!",
            # Hidden location - requires perception OR mysterious_key (Phase 3.6.3)
            hidden=True,
            discovery_condition="skill:perception:14 OR has_item:mysterious_key",
            discovery_hint="The vines along the cliff face seem unusually thick in one spot...",
            events=[
                LocationEvent(
                    id="secret_discovery",
                    trigger=EventTrigger.ON_FIRST_VISIT,
                    narration="This hollow has been hidden for decades! Old adventurer's gear lies scattered about, including some valuable items.",
                    effect=None,
                    one_time=True
                )
            ]
        ),
        "darkhollow_approach": Location(
            id="darkhollow_approach",
            name="Approach to Darkhollow",
            description="The forest grows darker and more twisted. Goblin signs become visible - crude markers, bones hanging from branches.",
            exits={"back": "forest_clearing", "cave": "cave_entrance"},
            # Map coordinates for world map UI
            map_x=0.65, map_y=0.38, map_icon="⚠️", map_region="forest",
            direction_aliases={"w": "back", "west": "back", "e": "cave", "east": "cave"},
            npcs=[],
            items=["goblin_ear"],
            atmosphere_text="Ominous, the smell of something foul ahead",
            enter_text="The path narrows. Crude goblin warnings hang from the trees.",
            events=[
                LocationEvent(
                    id="goblin_warning_signs",
                    trigger=EventTrigger.ON_FIRST_VISIT,
                    narration="Crude goblin totems and skulls on spikes line the path - a clear warning to trespassers.",
                    effect=None,
                    one_time=True
                )
            ]
        ),
        
        # === CAVE ENTRANCE SCENE LOCATIONS ===
        "cave_entrance": Location(
            id="cave_entrance",
            name="Darkhollow Cave Entrance",
            description="A gaping maw in the rocky hillside. Goblin totems flank the entrance, and bones litter the ground.",
            exits={"forest": "darkhollow_approach", "enter cave": "cave_tunnel", "inside": "cave_tunnel"},
            # Map coordinates for world map UI
            map_x=0.65, map_y=0.50, map_icon="💀", map_region="forest",
            direction_aliases={"w": "forest", "west": "forest", "e": "enter cave", "east": "enter cave", "d": "enter cave", "down": "enter cave"},
            npcs=[],
            items=["torch"],
            atmosphere=LocationAtmosphere(
                sounds=["wind moaning through the cave mouth", "distant dripping", "faint echoes", "the occasional bone crunching underfoot"],
                smells=["decay", "goblin musk", "damp earth", "rotting meat"],
                textures=["rough stone", "slippery moss near entrance", "scattered bones", "crude goblin carvings"],
                lighting="daylight fading into oppressive darkness",
                temperature="cold air flowing from within",
                mood="foreboding",
                danger_level="threatening",
                random_details=["a human skull on a spike", "claw marks on the entrance stones", "old torch stubs ground into the dirt", "a tattered cloak caught on a rock"]
            ),
            enter_text="Before you looms the entrance to Darkhollow Cave.",
            events=[
                LocationEvent(
                    id="cave_ambience",
                    trigger=EventTrigger.ON_FIRST_VISIT,
                    narration="A cold wind rushes out from the cave mouth, carrying the stench of goblins and something worse.",
                    effect=None,
                    one_time=True
                )
            ]
        ),
        "cave_tunnel": Location(
            id="cave_tunnel",
            name="Dark Tunnel",
            description="A narrow passage descending into darkness. The walls are slick with moisture. Distant goblin chatter echoes ahead.",
            exits={"outside": "cave_entrance", "deeper": "goblin_camp_entrance", "forward": "goblin_camp_entrance"},
            # Map coordinates for world map UI
            map_x=0.50, map_y=0.62, map_icon="🕯️", map_region="cave",
            direction_aliases={"w": "outside", "west": "outside", "u": "outside", "up": "outside", "e": "deeper", "east": "deeper", "d": "deeper", "down": "deeper"},
            npcs=[],
            items=[],
            is_dark=True,  # Phase 3.6.7: Requires torch for full visibility
            atmosphere_text="Pitch black without light, dripping water, echoing sounds",
            enter_text="You descend into the darkness. The light fades behind you.",
            # Phase 3.2.1 Priority 7: Random encounters
            random_encounters=[
                RandomEncounter(
                    id="giant_spider",
                    enemies=["giant_spider"],
                    chance=25,  # 25% chance
                    max_triggers=1,  # Only once
                    min_visits=1,  # Not on first entry
                    narration="A massive spider drops from the ceiling, blocking your path!"
                )
            ]
        ),
        
        # === GOBLIN CAMP SCENE LOCATIONS ===
        "goblin_camp_entrance": Location(
            id="goblin_camp_entrance",
            name="Goblin Warren - Entrance",
            description="The tunnel opens into a larger cavern. Firelight flickers ahead, and you can see goblin shadows moving.",
            exits={"tunnel": "cave_tunnel", "camp": "goblin_camp_main", "sneak left": "goblin_camp_shadows"},
            # Map coordinates for world map UI
            map_x=0.50, map_y=0.72, map_icon="👁️", map_region="cave",
            direction_aliases={"w": "tunnel", "west": "tunnel", "e": "camp", "east": "camp", "n": "sneak left", "north": "sneak left"},
            npcs=[],
            items=[],
            atmosphere_text="Goblin stench, crackling fire ahead, guttural voices",
            enter_text="The passage widens. You see the goblin camp ahead."
        ),
        "goblin_camp_main": Location(
            id="goblin_camp_main",
            name="Goblin Warren - Main Camp",
            description="A large cavern lit by smoky torches. Four goblins lounge around a central fire. Cages line the far wall - one holds a young girl! A sturdy door to the side is marked 'STORAGE'.",
            exits={"back": "goblin_camp_entrance", "cages": "goblin_camp_cages", "chief": "chief_tunnel", "storage": "goblin_storage"},
            # Map coordinates for world map UI
            map_x=0.50, map_y=0.82, map_icon="⚔️", map_region="cave",
            direction_aliases={"w": "back", "west": "back", "e": "cages", "east": "cages", "n": "chief", "north": "chief", "s": "storage", "south": "storage"},
            npcs=["goblins"],
            items=["shortsword", "rations", "healing_potion", "gold_pouch_small"],
            atmosphere=LocationAtmosphere(
                sounds=["guttural goblin chatter", "crackling campfire", "dice rattling", "distant sobbing", "chains clinking"],
                smells=["unwashed bodies", "burnt meat", "smoke", "fear sweat"],
                textures=["greasy pelts on the ground", "crude bone dice", "smoky air stinging eyes"],
                lighting="flickering torchlight, deep shadows in corners",
                temperature="uncomfortably warm from the fire",
                mood="chaotic and dangerous",
                danger_level="deadly",
                random_details=["a goblin picking its teeth with a bone", "stolen village goods piled haphazardly", "crude drawings of violence on the walls", "a half-eaten rat on a plate"]
            ),
            enter_text="You enter the main goblin camp. Four goblins look up from their fire.",
            # Phase 3.2.2: Fixed encounter for predictable difficulty (4 goblins)
            encounter=["goblin", "goblin", "goblin", "goblin"],
            # Phase 3.2.1 Priority 5: Locked storage door
            exit_conditions=[
                ExitCondition(
                    exit_name="storage",
                    condition="has_item:storage_key",
                    fail_message="The storage door is locked. You need a key.",
                    consume_item=False  # Key can be reused
                )
            ]
        ),
        "goblin_camp_shadows": Location(
            id="goblin_camp_shadows",
            name="Goblin Warren - Shadows",
            description="A dark alcove along the cavern wall. From here you can observe the camp without being seen. Something glints in the corner.",
            exits={"camp": "goblin_camp_main", "cages": "goblin_camp_cages", "chief": "chief_tunnel"},
            # Map coordinates for world map UI
            map_x=0.35, map_y=0.78, map_icon="👤", map_region="cave",
            direction_aliases={"s": "camp", "south": "camp", "e": "cages", "east": "cages", "n": "chief", "north": "chief"},
            npcs=["shade"],
            items=["poison_vial", "dagger", "storage_key"],
            is_dark=True,  # Phase 3.6.7: Dark alcove, requires torch
            atmosphere_text="Hidden, good vantage point for surprise attack",
            enter_text="You slip into the shadows. From here you can see the whole camp.",
            events=[
                LocationEvent(
                    id="shadow_discovery",
                    trigger=EventTrigger.ON_FIRST_VISIT,
                    narration="You find a dead goblin scout here - poisoned. Someone else is hunting these creatures. A brass key hangs from his belt.",
                    effect=None,
                    one_time=True
                )
            ]
        ),
        "goblin_storage": Location(
            id="goblin_storage",
            name="Goblin Warren - Storage Room",
            description="A cramped storage room full of stolen goods. Barrels of food, crates of weapons, and a locked chest in the corner.",
            exits={"camp": "goblin_camp_main"},
            # Map coordinates for world map UI
            map_x=0.35, map_y=0.88, map_icon="📦", map_region="cave",
            direction_aliases={"n": "camp", "north": "camp"},
            npcs=[],
            items=["healing_potion", "healing_potion", "gold_pouch", "shortsword", "leather_armor", "silver_locket", "family_ring"],
            is_dark=True,  # Phase 3.6.7: No windows, requires torch
            atmosphere_text="Musty, piles of stolen village goods, potential treasure",
            enter_text="The storage door creaks open. You've found the goblins' loot stash!",
            events=[
                LocationEvent(
                    id="storage_discovery",
                    trigger=EventTrigger.ON_FIRST_VISIT,
                    narration="You recognize some of the stolen goods - supplies from the village! There's enough here to make looting worthwhile. You spot something glinting - family heirlooms perhaps?",
                    effect="xp:25",
                    one_time=True
                )
            ]
        ),
        "goblin_camp_cages": Location(
            id="goblin_camp_cages",
            name="Goblin Warren - Prisoner Cages",
            description="Crude iron cages along the wall. A young girl (Lily) cowers in one, her eyes wide with fear and hope.",
            exits={"camp": "goblin_camp_main"},
            # Map coordinates for world map UI
            map_x=0.65, map_y=0.82, map_icon="🔒", map_region="cave",
            direction_aliases={"w": "camp", "west": "camp"},
            npcs=["lily"],
            items=["lockpicks"],
            atmosphere_text="Lily's quiet sobs, the clink of chains",
            enter_text="You approach the cages. The girl's eyes light up with hope.",
            events=[
                LocationEvent(
                    id="lily_found",
                    trigger=EventTrigger.ON_FIRST_VISIT,
                    narration="Lily gasps and reaches through the bars. 'Please, help me! The chief wants to eat me!'",
                    effect="objective:rescue_lily",
                    one_time=True
                )
            ]
        ),
        
        # === BOSS CHAMBER SCENE LOCATIONS ===
        "chief_tunnel": Location(
            id="chief_tunnel",
            name="Passage to Chief's Lair",
            description="A passage leading to the back of the cave. It's more decorated - skulls on spikes, crude paintings. An antidote vial lies forgotten in a corner.",
            exits={"camp": "goblin_camp_main", "lair": "boss_chamber"},
            # Map coordinates for world map UI
            map_x=0.50, map_y=0.92, map_icon="⚰️", map_region="cave",
            direction_aliases={"s": "camp", "south": "camp", "n": "lair", "north": "lair"},
            npcs=[],
            items=["antidote"],
            atmosphere_text="More 'decorated' than the camp, clearly important",
            enter_text="You head toward the chief's lair. The decorations grow more gruesome.",
            events=[
                LocationEvent(
                    id="tunnel_tripwire",
                    trigger=EventTrigger.ON_FIRST_VISIT,
                    narration="A thin wire is stretched across the passage! It's a trap!",
                    effect="skill_check:dex:12|damage:1d4",
                    one_time=True
                )
            ]
        ),
        "boss_chamber": Location(
            id="boss_chamber",
            name="Chief Grotnak's Throne Room",
            description="A large chamber dominated by a throne of bones. Chief Grotnak sits counting coins, flanked by two goblin bodyguards.",
            exits={"escape": "chief_tunnel", "hidden alcove": "treasure_nook"},
            # Map coordinates for world map UI
            map_x=0.50, map_y=0.98, map_icon="👑", map_region="cave",
            direction_aliases={"s": "escape", "south": "escape"},
            npcs=["grotnak", "bodyguards"],
            items=["healing_potion", "gold_pouch", "longsword"],
            # Hidden treasure under the throne (Phase 3.3.5)
            hidden_items=[
                HiddenItem(
                    item_id="chiefs_medallion",
                    skill="investigation",
                    dc=14,
                    hint="Something glints beneath the throne of bones..."
                )
            ],
            atmosphere=LocationAtmosphere(
                sounds=["Grotnak's low chuckling", "coins clinking", "bodyguards shifting their weight", "dripping from stalactites"],
                smells=["blood", "wet fur", "smoke from braziers", "the chief's rancid breath"],
                textures=["bones underfoot", "cold stone walls", "oily torchlight on metal"],
                lighting="dramatic torchlight, the throne casting long shadows",
                temperature="cold with hot braziers",
                mood="menacing confrontation",
                danger_level="deadly",
                random_details=["trophies from fallen adventurers on the walls", "a crude map scratched into the floor", "the chief's rusted crown askew", "bodyguards' yellow eyes following every movement"]
            ),
            enter_text="You enter the throne room. Chief Grotnak looks up with a wicked grin.",
            # Phase 3.2.2: Fixed boss encounter (chief + 1 bodyguard - balanced)
            encounter=["goblin_boss", "goblin"],
            events=[
                LocationEvent(
                    id="chief_confrontation",
                    trigger=EventTrigger.ON_FIRST_VISIT,
                    narration="The Goblin Chief rises from his bone throne with a thunderous roar! 'You dare enter MY domain?!'",
                    effect="start_combat:goblin_boss",
                    one_time=True
                )
            ]
        ),
        # === SECRET LOCATION (Phase 3.2.1 - Priority 8) ===
        "treasure_nook": Location(
            id="treasure_nook",
            name="Chief's Secret Stash",
            description="A cramped alcove hidden behind a false panel in the wall. The chief's personal treasure hoard!",
            exits={"out": "boss_chamber", "back": "boss_chamber"},
            # Map coordinates for world map UI (hidden until discovered)
            map_x=0.65, map_y=0.98, map_icon="💎", map_region="cave", map_hidden=True,
            direction_aliases={"s": "out", "south": "out"},
            npcs=[],
            items=["enchanted_dagger", "ruby_ring", "gold_pile", "rare_scroll"],
            atmosphere_text="Dusty, glittering, the smell of wealth hoarded over years",
            enter_text="You squeeze through the hidden passage into the chief's secret stash!",
            # Hidden location - requires investigation after combat
            hidden=True,
            discovery_condition="skill:investigation:12",
            discovery_hint="One section of the wall behind the throne looks different from the rest...",
            events=[
                LocationEvent(
                    id="treasure_found",
                    trigger=EventTrigger.ON_FIRST_VISIT,
                    narration="The chief was hoarding more than you realized! Piles of gold and magical items fill this cramped space.",
                    effect=None,
                    one_time=True
                )
            ]
        ),
        
        # === RESOLUTION SCENE LOCATIONS ===
        "cave_exit": Location(
            id="cave_exit",
            name="Cave Exit",
            description="Daylight streams through the cave entrance. Fresh air replaces the goblin stench.",
            exits={"outside": "return_path"},
            # Map coordinates for world map UI
            map_x=0.65, map_y=0.50, map_icon="☀️", map_region="forest",
            direction_aliases={"w": "outside", "west": "outside"},
            npcs=["lily"],
            items=[],
            atmosphere_text="Relief, fresh air, sense of accomplishment",
            enter_text="You emerge from the cave into blessed sunlight."
        ),
        "return_path": Location(
            id="return_path",
            name="Return Journey",
            description="The forest path back to the village. The journey feels lighter now.",
            exits={"village": "village_return"},
            # Map coordinates for world map UI
            map_x=0.50, map_y=0.28, map_icon="🏃", map_region="forest",
            direction_aliases={"w": "village", "west": "village"},
            npcs=["lily"],
            items=[],
            atmosphere_text="Lighter mood, Lily's grateful chatter",
            enter_text="The journey home begins. Lily walks beside you, still shaken but safe."
        ),
        "village_return": Location(
            id="village_return",
            name="Village - Hero's Return",
            description="The village square, but now filled with people. Word has spread of your success!",
            exits={"tavern": "tavern_celebration"},
            # Map coordinates for world map UI
            map_x=0.50, map_y=0.08, map_icon="🎊", map_region="village",
            npcs=["bram", "villagers"],
            items=[],
            atmosphere_text="Cheering crowds, tearful reunion",
            enter_text="The village erupts in cheers as you return with Lily!"
        ),
        "tavern_celebration": Location(
            id="tavern_celebration",
            name="The Rusty Dragon - Celebration",
            description="The tavern is packed! Drinks flow freely and the villagers toast your heroism.",
            exits={},
            # Map coordinates for world map UI
            map_x=0.15, map_y=0.08, map_icon="🎉", map_region="village",
            npcs=["bram", "barkeep", "villagers"],
            items=[],
            atmosphere_text="Celebration, gratitude, hints of future adventures",
            enter_text="The tavern welcomes you as a hero. Bram approaches with tears in his eyes."
        )
    }
    
    # =========================================================================
    # SCENES (with location references)
    # =========================================================================
    
    scenes = {
        "tavern": Scene(
            id="tavern",
            name="The Rusty Dragon Tavern",
            description="A small-town tavern where adventure begins",
            setting="A cozy but weathered tavern. A fire crackles in the hearth. Locals murmur over their drinks.",
            mood="welcoming, mysterious undertones",
            dm_instructions="""
Introduce a worried farmer named Bram who approaches the player.
His daughter Lily was taken by goblins who raided their farm last night.
He offers the family's savings (50 gold) as reward.
The goblin lair is in Darkhollow Cave, a half-day's journey east.
Let the player ask questions, gather information from locals.

IMPORTANT - WHEN PLAYER ACCEPTS THE QUEST:
- DO NOT use [XP: ...] tags - XP is awarded automatically by the system
- Give any items (torch, etc.) using [ITEM: torch]
- Describe Bram's relief and gratitude
- END YOUR RESPONSE in the tavern
- DO NOT narrate the journey - the player will navigate using 'go' commands
- Suggest the player can explore the village or head east toward the forest

LOCATION NOTES:
- Player starts in main room, can explore bar or go outside
- Bram is in the main room
- Barkeep has gossip if asked
- Player uses 'go outside' to leave tavern to village_square
- Player uses 'go east' from village to start the journey
""",
            min_exchanges=3,
            objectives=["meet_bram", "accept_quest"],
            objective_xp={"meet_bram": 10, "accept_quest": 15},  # Phase 3.2.2: Objective XP
            transition_hint="Player accepts the quest and prepares to leave",
            next_scene_id="journey",
            # Location System
            location_ids=["tavern_main", "tavern_bar", "village_square", "blacksmith_shop", "forest_path"],
            starting_location_id="tavern_main"
        ),
        
        "journey": Scene(
            id="journey",
            name="The Road to Darkhollow",
            description="Traveling through the forest toward the cave",
            setting="A winding forest path. Afternoon sun filters through autumn leaves. Birds go quiet as you travel deeper.",
            mood="atmospheric, building tension",
            dm_instructions="""
Describe the journey through increasingly wild terrain.
Include sensory details: crunching leaves, distant animal sounds, cooling air.
Partway through, have the player encounter EITHER:
- A frightened merchant whose cart was raided (information source)
- Goblin tracks and signs of recent passage
- An old woodsman who warns of increased goblin activity
Build tension as they approach the cave.

LOCATION NOTES:
- Player moves from forest_path → forest_clearing → darkhollow_approach
- Merchant encounter at clearing
- Goblin signs at darkhollow_approach
""",
            min_exchanges=2,
            objectives=[],
            transition_hint="Player arrives at Darkhollow Cave entrance",
            next_scene_id="cave_entrance",
            # Location System
            location_ids=["village_square", "blacksmith_shop", "forest_path", "forest_clearing", "darkhollow_approach", "secret_cave"],
            starting_location_id="forest_path"
        ),
        
        "cave_entrance": Scene(
            id="cave_entrance",
            name="Cave Entrance",
            description="The mouth of Darkhollow Cave",
            setting="A rocky hillside with a dark cave opening. Goblin totems and bones mark the entrance. Faint sounds echo from within.",
            mood="ominous, dangerous",
            dm_instructions="""
Describe the cave entrance: crude goblin warnings, a foul smell, distant echoing sounds.
Let the player investigate the area. They might find:
- Recent footprints (many goblins, plus small human - Lily!)
- Discarded supplies from other victims
- A narrow entrance that forces single-file
When player enters, describe the descent into darkness.
Ask how they're providing light (torch, magic, etc.)

LOCATION NOTES:
- Cave entrance outside, then dark tunnel inside
- Ask about light source when entering tunnel
""",
            min_exchanges=2,
            objectives=["examine_entrance"],
            objective_xp={"examine_entrance": 15},  # Phase 3.2.2: Objective XP
            transition_hint="Player enters the cave",
            next_scene_id="goblin_camp",
            # Location System
            location_ids=["darkhollow_approach", "cave_entrance", "cave_tunnel"],
            starting_location_id="cave_entrance"
        ),
        
        "goblin_camp": Scene(
            id="goblin_camp",
            name="The Goblin Warren",
            description="A goblin encampment deep in the cave",
            setting="A large cavern lit by smoky torches. Exactly 4 goblins lounge around a fire. Cages line the far wall. The smell is overwhelming.",
            mood="tense, combat-ready",
            dm_instructions="""
The player enters a main cavern with:
- EXACTLY 4 goblins (distracted, gambling, eating) - DO NOT vary this number
- A cage with a young girl (Lily, scared but alive)
- Tunnels leading deeper (to the chief's chamber)
- Crude fortifications (overturnable tables, weapon racks)

Let the player choose their approach:
- Stealth: Sneak past or to ambush position (go to shadows location)
- Combat: Fight the goblins - USE EXACTLY [COMBAT: goblin, goblin, goblin, goblin]
- Distraction: Create diversion
- Negotiation: (Very hard, goblins are hostile)

⚠️ FIXED ENCOUNTER: When combat occurs at goblin_camp_main, you MUST use:
[COMBAT: goblin, goblin, goblin, goblin]
Do NOT add or remove enemies - this ensures fair, balanced gameplay.

Resolve the encounter. If player frees Lily, she says the chief has more prisoners.
Chief is in the back chamber with the treasure.

LOCATION NOTES:
- goblin_camp_entrance: can see camp, plan approach
- goblin_camp_shadows: stealth position for surprise
- goblin_camp_main: direct confrontation (4 goblins)
- goblin_camp_cages: where Lily is held
""",
            min_exchanges=3,
            objectives=["deal_with_goblins", "find_lily"],
            objective_xp={"deal_with_goblins": 25, "find_lily": 50},  # Phase 3.2.2: Combat XP separate
            transition_hint="Player either clears the camp or sneaks through to the chief's chamber",
            next_scene_id="boss_chamber",
            # Location System
            location_ids=["cave_tunnel", "goblin_camp_entrance", "goblin_camp_main", "goblin_camp_shadows", "goblin_camp_cages", "chief_tunnel", "goblin_storage"],
            starting_location_id="goblin_camp_entrance"
        ),
        
        "boss_chamber": Scene(
            id="boss_chamber",
            name="Chief Grotnak's Lair",
            description="The goblin chief's personal chamber",
            setting="A larger chamber with a crude throne made of bones. A brutish goblin chief sits counting coins. Exactly two goblin bodyguards flank him.",
            mood="climactic, dangerous, decisive",
            dm_instructions="""
BOSS ENCOUNTER: Chief Grotnak
- Larger, meaner, smarter than regular goblins
- Has EXACTLY 2 goblin bodyguards (not more, not less)
- Sits on bone throne with a chest of stolen treasure nearby
- If player has Lily, he might threaten her
- If player caused commotion earlier, he's prepared

⚠️ FIXED ENCOUNTER: When combat starts, you MUST use:
[COMBAT: goblin_boss, goblin, goblin]
Do NOT add or remove enemies - this ensures fair, balanced gameplay.

This is the climax! Make it dramatic:
- Describe his menacing appearance
- Let player make tactical choices
- Include dramatic moments in the fight
- When defeated, describe his fall dramatically

Treasure includes: gold, a minor magic item, personal effects from victims.

LOCATION NOTES:
- chief_tunnel: approach, can hear him counting coins
- boss_chamber: the confrontation (1 boss + 2 bodyguards)
""",
            min_exchanges=3,
            objectives=["defeat_chief"],
            objective_xp={"defeat_chief": 50},  # Phase 3.2.2: Victory objective XP
            transition_hint="Chief Grotnak is defeated",
            next_scene_id="resolution",
            # Location System
            location_ids=["goblin_camp_main", "chief_tunnel", "boss_chamber", "treasure_nook"],
            starting_location_id="chief_tunnel"
        ),
        
        "resolution": Scene(
            id="resolution",
            name="Heroes Return",
            description="The aftermath and reward",
            setting="Emerging from the cave into daylight, then back to the village as heroes.",
            mood="triumphant, satisfying, hopeful",
            dm_instructions="""
Wrap up the adventure:
1. Describe leaving the cave (relief, satisfaction)
2. The journey back (lighter mood, Lily's gratitude)
3. Return to village (crowds gather, word has spread)
4. Bram's tearful reunion with Lily
5. Reward: 50 gold + a family heirloom (e.g., grandfather's dagger)
6. Celebration at the tavern
7. Hint at future adventures (other problems mentioned, traveler with a map, etc.)

Make the player feel HEROIC. This is their first victory.
End with a sense of completion but also possibility.

LOCATION NOTES:
- cave_exit: leaving the cave
- return_path: journey home with Lily
- village_return: hero's welcome
- tavern_celebration: reward and celebration
""",
            min_exchanges=2,
            objectives=[],
            transition_hint="Player receives reward and the adventure concludes",
            next_scene_id=None,  # End of scenario
            # Location System
            location_ids=["boss_chamber", "cave_exit", "return_path", "village_return", "tavern_celebration"],
            starting_location_id="cave_exit"
        )
    }
    
    # Create location manager and add all locations
    location_manager = LocationManager()
    for loc in locations.values():
        location_manager.add_location(loc)
    
    # Create NPC manager with Goblin Cave NPCs (Phase 3.3)
    npc_manager = create_goblin_cave_npcs()
    
    scenario = Scenario(
        id="goblin_cave",
        name="The Goblin Cave",
        description="Rescue a farmer's daughter from a goblin lair. A classic starter adventure.",
        hook="A desperate farmer's daughter has been kidnapped by goblins. Will you brave the depths of Darkhollow Cave to save her?",
        estimated_duration="20-40 minutes",
        scenes=scenes,
        scene_order=["tavern", "journey", "cave_entrance", "goblin_camp", "boss_chamber", "resolution"],
        location_manager=location_manager,
        npc_manager=npc_manager
    )
    
    return scenario


# =============================================================================
# SCENARIO MANAGER
# =============================================================================

class ScenarioManager:
    """Manages the active scenario and provides context to the game."""
    
    def __init__(self):
        self.active_scenario: Optional[Scenario] = None
        self.available_scenarios: Dict[str, Callable[[], Scenario]] = {
            "goblin_cave": create_goblin_cave_scenario
        }
    
    def list_available(self) -> List[Dict[str, str]]:
        """List available scenarios."""
        scenarios = []
        for scenario_id, creator in self.available_scenarios.items():
            scenario = creator()
            scenarios.append({
                "id": scenario_id,
                "name": scenario.name,
                "description": scenario.description,
                "duration": scenario.estimated_duration
            })
        return scenarios
    
    def start_scenario(self, scenario_id: str) -> Scene:
        """Start a scenario by ID."""
        if scenario_id not in self.available_scenarios:
            raise ValueError(f"Unknown scenario: {scenario_id}")
        
        self.active_scenario = self.available_scenarios[scenario_id]()
        return self.active_scenario.start()
    
    def get_dm_context(self) -> str:
        """Get current scenario/scene context for the DM."""
        if not self.active_scenario:
            return ""
        return self.active_scenario.get_scene_context_for_dm()
    
    def record_exchange(self):
        """Record a player exchange."""
        if self.active_scenario:
            self.active_scenario.record_exchange()
    
    def check_transition(self, player_input: str, dm_response: str) -> Optional[str]:
        """
        Check if a scene transition should occur based on the exchange.
        Returns transition message if transitioning, None otherwise.
        """
        if not self.active_scenario:
            return None
        
        # Simple keyword detection for objectives
        scene = self.active_scenario.get_current_scene()
        if scene:
            input_lower = player_input.lower()
            response_lower = dm_response.lower()
            
            # Check for common objective triggers
            if "accept" in input_lower or "yes" in input_lower or "help" in input_lower:
                if "accept_quest" in scene.objectives:
                    self.active_scenario.complete_objective("accept_quest")
            
            if "bram" in response_lower or "farmer" in response_lower:
                if "meet_bram" in scene.objectives:
                    self.active_scenario.complete_objective("meet_bram")
            
            if "examine" in input_lower or "look" in input_lower or "search" in input_lower:
                if "examine_entrance" in scene.objectives:
                    self.active_scenario.complete_objective("examine_entrance")
            
            if "lily" in response_lower or "girl" in response_lower or "daughter" in response_lower:
                if "find_lily" in scene.objectives:
                    self.active_scenario.complete_objective("find_lily")
            
            if any(word in response_lower for word in ["defeat", "killed", "slain", "falls", "victory"]):
                if "deal_with_goblins" in scene.objectives:
                    self.active_scenario.complete_objective("deal_with_goblins")
                if "defeat_chief" in scene.objectives:
                    self.active_scenario.complete_objective("defeat_chief")
        
        # Check if we can transition
        if self.active_scenario.can_transition():
            # Look for transition signals in the AI response
            transition_keywords = [
                "you enter", "you step into", "you descend",
                "you arrive", "you reach", "you emerge",
                "leads you to", "takes you to",
                "the adventure concludes", "your adventure ends"
            ]
            
            if any(keyword in response_lower for keyword in transition_keywords):
                next_scene = self.active_scenario.transition_to_next()
                if next_scene:
                    return f"\n{'='*50}\n📍 {next_scene.name}\n{'='*50}\n"
                elif self.active_scenario.is_complete:
                    return f"\n{'='*50}\n🏆 ADVENTURE COMPLETE: {self.active_scenario.name}\n{'='*50}\n"
        
        return None
    
    def get_progress(self) -> str:
        """Get scenario progress display."""
        if self.active_scenario:
            return self.active_scenario.get_progress_display()
        return ""
    
    def is_active(self) -> bool:
        """Check if a scenario is currently active."""
        return self.active_scenario is not None and not self.active_scenario.is_complete

# =============================================================================
# UTILITY FUNCTIONS (Migrated from legacy game.py)
# =============================================================================

def get_exit_by_number(number: int, exits: dict) -> str | None:
    """Get exit name by numbered choice. Returns None if invalid."""
    exit_list = list(exits.keys())
    if 1 <= number <= len(exit_list):
        return exit_list[number - 1]
    return None


def build_location_context(location, is_first_visit: bool = False, events: list = None) -> dict:
    """Build context dict for location narration.
    
    Args:
        location: The Location object being described
        is_first_visit: Whether this is the player's first time here
        events: Any events that just triggered (optional)
    
    Returns:
        Dict with all location context for AI narration
    """
    from inventory import ITEMS as ITEM_DATABASE
    
    context = {
        'name': location.name,
        'description': location.description,
        'is_first_visit': is_first_visit,
    }
    
    # Add structured atmosphere if available (Phase 3.4.1)
    if location.atmosphere:
        # Use structured LocationAtmosphere
        atmo = location.atmosphere
        atmosphere_context = {}
        if atmo.sounds:
            atmosphere_context['sounds'] = atmo.sounds
        if atmo.smells:
            atmosphere_context['smells'] = atmo.smells
        if atmo.textures:
            atmosphere_context['textures'] = atmo.textures
        if atmo.lighting:
            atmosphere_context['lighting'] = atmo.lighting
        if atmo.temperature:
            atmosphere_context['temperature'] = atmo.temperature
        if atmo.mood:
            atmosphere_context['mood'] = atmo.mood
        if atmo.danger_level:
            atmosphere_context['danger_level'] = atmo.danger_level
        if atmo.random_details:
            atmosphere_context['detail_pool'] = atmo.random_details
        
        if atmosphere_context:
            context['atmosphere'] = atmosphere_context
            context['atmosphere_instruction'] = "Weave 2-3 sensory details naturally into the description. Match the mood without stating emotions directly."
    elif location.atmosphere_text:
        # Legacy fallback: simple text atmosphere
        context['atmosphere'] = location.atmosphere_text
    else:
        context['atmosphere'] = "neutral"
    
    # Add items with rich descriptions for DM to weave into narrative
    if location.items:
        items_with_descriptions = []
        for item_id in location.items:
            item_name = item_id.replace("_", " ").title()
            # Try to get item description from database
            item_data = ITEM_DATABASE.get(item_id)
            if item_data:
                # Provide more context for the DM
                items_with_descriptions.append({
                    "name": item_name,
                    "type": item_data.item_type.value,
                    "description": item_data.description[:50] + "..." if len(item_data.description) > 50 else item_data.description
                })
            else:
                items_with_descriptions.append({"name": item_name})
        context['items_present'] = items_with_descriptions
        context['items_note'] = "Describe these items naturally in the scene - where they are, how they look. Don't list them."
    
    # Add NPCs with context
    if location.npcs:
        npc_names = [npc.replace("_", " ").title() for npc in location.npcs]
        context['npcs_present'] = npc_names
    
    # Add exits/directions
    if location.exits:
        context['available_directions'] = list(location.exits.keys())
    
    # Add events if any triggered
    if events:
        event_texts = [e.narration for e in events]
        context['events'] = event_texts
    
    # Add enter text for first visits
    if is_first_visit and location.enter_text:
        context['enter_text'] = location.enter_text
    
    # Add hints about hidden items for the DM to weave into narration
    if hasattr(location, 'get_search_hints') and location.has_searchable_secrets():
        hints = location.get_search_hints()
        if hints:
            context['hidden_item_hints'] = hints
            context['dm_note'] = "Subtly hint that there may be something hidden here for observant adventurers."
    
    return context