"""
Scenario System for AI D&D Text RPG (Phase 1, Step 1.3 + Phase 3.2 + Phase 3.3 + Phase 3.3.3 + Phase 3.3.4)
Manages scenes, story progression, narrative pacing, locations, NPCs, quests, and shops.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Callable, Tuple, Any
from enum import Enum
import functools

from text_match import has_any
from npc import NPCManager
from quest import QuestManager
from shop import ShopManager


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
        inventory = game_state.get("inventory") or []
        if inventory:
            # Check if player has the item
            for item in inventory:
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
    
    def move(
        self,
        direction: str,
        game_state: dict = None,
        skill_check_override: bool = False,
    ) -> Tuple[bool, Optional[Location], str, List[LocationEvent]]:
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
            travel_note = ""
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
                        if not skill_check_override:
                            return False, None, reason, []
                        location.unlock_exit(matched_exit_name)
                    else:
                        # Condition met - unlock the exit
                        location.unlock_exit(matched_exit_name)
                        if exit_cond.consume_item and exit_cond.condition.startswith("has_item:"):
                            item_key = exit_cond.condition.split(":")[1]
                            travel_note = f"CONSUME_ITEM:{item_key}"
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
                
                return True, new_location, travel_note, events
        
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
                inventory = game_state["inventory"] or []
                wanted = item_key.lower()
                if any(item.name.lower().replace(" ", "_") == wanted for item in inventory):
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
    # Objectives completed by events that aren't in the current scene's
    # objective list (e.g. "objective:rescue_lily" from a location event).
    extra_objectives_complete: List[str] = field(default_factory=list)
    
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
        if objective_id and objective_id not in self.extra_objectives_complete:
            self.extra_objectives_complete.append(objective_id)
        return False, 0

    @property
    def completed_objectives(self) -> List[str]:
        """Every objective completed so far, across all scenes and events."""
        done = list(self.extra_objectives_complete)
        for scene in self.scenes.values():
            done.extend(o for o in scene.objectives_complete if o not in done)
        return done
    
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
# SCENARIO CONTENT
# =============================================================================
# Scenario content lives in data/scenarios/<id>/*.yaml and is loaded by
# scenario_loader. These wrappers keep the original Goblin Cave entry points.

def create_goblin_cave_npcs() -> NPCManager:
    """NPCManager with all Goblin Cave NPCs (data/scenarios/goblin_cave/npcs.yaml)."""
    from scenario_loader import load_npcs
    return load_npcs("goblin_cave")


def create_goblin_cave_quests(quest_manager: QuestManager) -> None:
    """Register Goblin Cave quests (data/scenarios/goblin_cave/quests.yaml)."""
    from scenario_loader import register_quests
    register_quests("goblin_cave", quest_manager)


def create_goblin_cave_shops(shop_manager: ShopManager) -> None:
    """Register Goblin Cave shops (data/scenarios/goblin_cave/shops.yaml)."""
    from scenario_loader import register_shops
    register_shops("goblin_cave", shop_manager)


def create_goblin_cave_scenario() -> Scenario:
    """Build the Goblin Cave scenario from data/scenarios/goblin_cave/."""
    from scenario_loader import load_scenario
    return load_scenario("goblin_cave")


# =============================================================================
# SCENARIO MANAGER
# =============================================================================

class ScenarioManager:
    """Manages the active scenario and provides context to the game."""
    
    def __init__(self):
        self.active_scenario: Optional[Scenario] = None
        from scenario_loader import list_scenario_ids, load_scenario
        # Every folder under data/scenarios/ with a scenario.yaml
        self.available_scenarios: Dict[str, Callable[[], Scenario]] = {
            scenario_id: functools.partial(load_scenario, scenario_id)
            for scenario_id in list_scenario_ids()
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
        
        # Keyword detection for conversational/exploration objectives (whole
        # words only). Combat objectives (deal_with_goblins, defeat_chief) are
        # completed by an actual combat victory — see apply_combat_victory —
        # because prose like "rain falls" or "a small victory" proves nothing.
        scene = self.active_scenario.get_current_scene()
        if scene:
            if has_any(player_input, ["accept", "yes", "help", "agree", "count me in", "i'm in"]):
                if "accept_quest" in scene.objectives:
                    self.active_scenario.complete_objective("accept_quest")

            if has_any(dm_response, ["bram", "farmer"]):
                if "meet_bram" in scene.objectives:
                    self.active_scenario.complete_objective("meet_bram")

            if has_any(player_input, ["examine", "look", "search", "inspect", "investigate"]):
                if "examine_entrance" in scene.objectives:
                    self.active_scenario.complete_objective("examine_entrance")

            if has_any(dm_response, ["lily", "girl", "daughter"]):
                if "find_lily" in scene.objectives:
                    self.active_scenario.complete_objective("find_lily")

        # Check if we can transition
        if self.active_scenario.can_transition():
            # Look for transition signals in the AI response
            transition_keywords = [
                "you enter", "you step into", "you descend",
                "you arrive", "you reach", "you emerge",
                "leads you to", "takes you to",
                "the adventure concludes", "your adventure ends"
            ]

            if has_any(dm_response, transition_keywords):
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
