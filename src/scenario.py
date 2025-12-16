"""
Scenario System for AI D&D Text RPG (Phase 1, Step 1.3 + Phase 3.2)
Manages scenes, story progression, narrative pacing, and locations.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Callable
from enum import Enum
import json


class SceneStatus(Enum):
    """Status of a scene."""
    LOCKED = "locked"           # Not yet accessible
    ACTIVE = "active"           # Currently playing
    COMPLETED = "completed"     # Finished


# =============================================================================
# LOCATION SYSTEM (Phase 3.2)
# =============================================================================

@dataclass
class Location:
    """Represents a physical location in the game world."""
    
    id: str                              # Unique identifier (e.g., "tavern_main")
    name: str                            # Display name (e.g., "The Rusty Tankard")
    description: str                     # Full description for AI
    
    # Navigation - maps exit names to location IDs
    exits: Dict[str, str] = field(default_factory=dict)  # {"door": "street", "stairs": "upper_floor"}
    
    # Contents
    npcs: List[str] = field(default_factory=list)        # NPC IDs present here
    items: List[str] = field(default_factory=list)       # Item keys that can be found
    
    # AI Guidance
    atmosphere: str = ""                 # "dim lighting, rowdy crowd"
    enter_text: str = ""                 # First-time entry description
    
    # State (runtime)
    visited: bool = False
    events_triggered: List[str] = field(default_factory=list)
    
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
            "events_triggered": self.events_triggered.copy()
        }
    
    @classmethod
    def from_state(cls, location: 'Location', state: dict) -> 'Location':
        """Apply saved state to a location."""
        location.visited = state.get("visited", False)
        location.events_triggered = state.get("events_triggered", [])
        return location


class LocationManager:
    """Manages player location and movement within a scenario."""
    
    def __init__(self):
        self.locations: Dict[str, Location] = {}
        self.current_location_id: Optional[str] = None
        self.available_location_ids: List[str] = []  # Locations unlocked by current scene
    
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
        """Get available exits from current location."""
        location = self.get_current_location()
        if location:
            # Filter exits to only show available locations
            return {
                exit_name: dest_id 
                for exit_name, dest_id in location.exits.items()
                if dest_id in self.available_location_ids
            }
        return {}
    
    def move(self, direction: str) -> tuple[bool, Optional[Location], str]:
        """
        Attempt to move in a direction.
        Returns: (success, new_location, message)
        """
        location = self.get_current_location()
        if not location:
            return False, None, "You are nowhere."
        
        # Normalize direction
        direction_lower = direction.lower().strip()
        
        # Check for matching exit
        available_exits = self.get_exits()
        
        # Try exact match first
        if direction_lower in available_exits:
            dest_id = available_exits[direction_lower]
            new_location = self.set_current_location(dest_id)
            if new_location:
                first_visit = not new_location.visited
                return True, new_location, ""
        
        # Try partial match
        for exit_name, dest_id in available_exits.items():
            if direction_lower in exit_name.lower() or exit_name.lower() in direction_lower:
                new_location = self.set_current_location(dest_id)
                if new_location:
                    return True, new_location, ""
        
        # No valid exit found
        valid_exits = list(available_exits.keys())
        if valid_exits:
            return False, None, f"You can't go '{direction}'. Available exits: {', '.join(valid_exits)}"
        return False, None, "There's nowhere to go from here."
    
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
        
        return context
    
    def to_dict(self) -> dict:
        """Serialize location manager state for saving."""
        return {
            "current_location_id": self.current_location_id,
            "available_location_ids": self.available_location_ids.copy(),
            "location_states": {
                loc_id: loc.to_dict() 
                for loc_id, loc in self.locations.items()
            }
        }
    
    def restore_state(self, state: dict):
        """Restore state from saved data."""
        self.current_location_id = state.get("current_location_id")
        self.available_location_ids = state.get("available_location_ids", [])
        
        # Restore individual location states
        location_states = state.get("location_states", {})
        for loc_id, loc_state in location_states.items():
            if loc_id in self.locations:
                Location.from_state(self.locations[loc_id], loc_state)


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
    
    # Runtime state
    current_scene_id: Optional[str] = None
    is_complete: bool = False
    
    def __post_init__(self):
        """Initialize location manager if not provided."""
        if self.location_manager is None:
            self.location_manager = LocationManager()
    
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
    
    def complete_objective(self, objective_id: str) -> bool:
        """Mark an objective as complete. Returns True if valid."""
        scene = self.get_current_scene()
        if scene and objective_id in scene.objectives:
            if objective_id not in scene.objectives_complete:
                scene.objectives_complete.append(objective_id)
            return True
        return False
    
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

def create_goblin_cave_scenario() -> Scenario:
    """Create the first starter scenario: The Goblin Cave."""
    
    # =========================================================================
    # LOCATIONS (Phase 3.2)
    # =========================================================================
    
    locations = {
        # === TAVERN SCENE LOCATIONS ===
        "tavern_main": Location(
            id="tavern_main",
            name="The Rusty Dragon - Main Room",
            description="A cozy common room with a crackling hearth. Wooden tables are scattered about, some occupied by locals nursing their drinks.",
            exits={"bar": "tavern_bar", "outside": "village_square"},
            npcs=["bram", "locals"],
            items=["torch"],
            atmosphere="Warm firelight, murmured conversations, smell of ale and stew",
            enter_text="You push through the tavern door, warmth washing over you."
        ),
        "tavern_bar": Location(
            id="tavern_bar",
            name="The Rusty Dragon - Bar",
            description="A worn wooden bar with a gruff but friendly barkeep polishing mugs. Bottles line the shelves behind.",
            exits={"main room": "tavern_main"},
            npcs=["barkeep"],
            items=[],
            atmosphere="Clinking glasses, the barkeep's watchful eye",
            enter_text="You approach the bar. The barkeep nods in greeting."
        ),
        "village_square": Location(
            id="village_square",
            name="Village Square",
            description="A small village square with a well at the center. A few shops line the edges, mostly closed at this hour.",
            exits={"tavern": "tavern_main", "east road": "forest_path"},
            npcs=[],
            items=[],
            atmosphere="Quiet evening, distant sounds of village life winding down",
            enter_text="You step out into the cool evening air of the village square."
        ),
        
        # === JOURNEY SCENE LOCATIONS ===
        "forest_path": Location(
            id="forest_path",
            name="Forest Path",
            description="A winding dirt path through an ancient forest. Autumn leaves crunch underfoot.",
            exits={"village": "village_square", "deeper": "forest_clearing", "east": "forest_clearing"},
            npcs=[],
            items=[],
            atmosphere="Dappled sunlight, bird calls, rustling leaves",
            enter_text="The village fades behind as you enter the forest."
        ),
        "forest_clearing": Location(
            id="forest_clearing",
            name="Forest Clearing",
            description="A small clearing where the path forks. An old signpost points east toward 'Darkhollow'.",
            exits={"back": "forest_path", "east": "darkhollow_approach", "cave": "darkhollow_approach"},
            npcs=["merchant"],  # Random encounter possibility
            items=["rations"],
            atmosphere="Birds go quiet here. An uneasy stillness.",
            enter_text="You emerge into a clearing. The trees seem to lean away from the eastern path."
        ),
        "darkhollow_approach": Location(
            id="darkhollow_approach",
            name="Approach to Darkhollow",
            description="The forest grows darker and more twisted. Goblin signs become visible - crude markers, bones hanging from branches.",
            exits={"back": "forest_clearing", "cave": "cave_entrance"},
            npcs=[],
            items=["goblin_ear"],
            atmosphere="Ominous, the smell of something foul ahead",
            enter_text="The path narrows. Crude goblin warnings hang from the trees."
        ),
        
        # === CAVE ENTRANCE SCENE LOCATIONS ===
        "cave_entrance": Location(
            id="cave_entrance",
            name="Darkhollow Cave Entrance",
            description="A gaping maw in the rocky hillside. Goblin totems flank the entrance, and bones litter the ground.",
            exits={"forest": "darkhollow_approach", "enter cave": "cave_tunnel", "inside": "cave_tunnel"},
            npcs=[],
            items=["torch"],
            atmosphere="Foul smell, echoing sounds from within, sense of danger",
            enter_text="Before you looms the entrance to Darkhollow Cave."
        ),
        "cave_tunnel": Location(
            id="cave_tunnel",
            name="Dark Tunnel",
            description="A narrow passage descending into darkness. The walls are slick with moisture. Distant goblin chatter echoes ahead.",
            exits={"outside": "cave_entrance", "deeper": "goblin_camp_entrance", "forward": "goblin_camp_entrance"},
            npcs=[],
            items=[],
            atmosphere="Pitch black without light, dripping water, echoing sounds",
            enter_text="You descend into the darkness. The light fades behind you."
        ),
        
        # === GOBLIN CAMP SCENE LOCATIONS ===
        "goblin_camp_entrance": Location(
            id="goblin_camp_entrance",
            name="Goblin Warren - Entrance",
            description="The tunnel opens into a larger cavern. Firelight flickers ahead, and you can see goblin shadows moving.",
            exits={"tunnel": "cave_tunnel", "camp": "goblin_camp_main", "sneak left": "goblin_camp_shadows"},
            npcs=[],
            items=[],
            atmosphere="Goblin stench, crackling fire ahead, guttural voices",
            enter_text="The passage widens. You see the goblin camp ahead."
        ),
        "goblin_camp_main": Location(
            id="goblin_camp_main",
            name="Goblin Warren - Main Camp",
            description="A large cavern lit by smoky torches. Goblins lounge around a central fire. Cages line the far wall - one holds a young girl!",
            exits={"back": "goblin_camp_entrance", "cages": "goblin_camp_cages", "chief": "chief_tunnel"},
            npcs=["goblins"],
            items=["shortsword", "rations"],
            atmosphere="Overwhelming stench, gambling goblins, a girl sobbing in a cage",
            enter_text="You enter the main goblin camp. Four goblins look up from their fire."
        ),
        "goblin_camp_shadows": Location(
            id="goblin_camp_shadows",
            name="Goblin Warren - Shadows",
            description="A dark alcove along the cavern wall. From here you can observe the camp without being seen.",
            exits={"camp": "goblin_camp_main", "cages": "goblin_camp_cages", "chief": "chief_tunnel"},
            npcs=[],
            items=[],
            atmosphere="Hidden, good vantage point for surprise attack",
            enter_text="You slip into the shadows. From here you can see the whole camp."
        ),
        "goblin_camp_cages": Location(
            id="goblin_camp_cages",
            name="Goblin Warren - Prisoner Cages",
            description="Crude iron cages along the wall. A young girl (Lily) cowers in one, her eyes wide with fear and hope.",
            exits={"camp": "goblin_camp_main"},
            npcs=["lily"],
            items=["lockpicks"],
            atmosphere="Lily's quiet sobs, the clink of chains",
            enter_text="You approach the cages. The girl's eyes light up with hope."
        ),
        
        # === BOSS CHAMBER SCENE LOCATIONS ===
        "chief_tunnel": Location(
            id="chief_tunnel",
            name="Passage to Chief's Lair",
            description="A passage leading to the back of the cave. It's more decorated - skulls on spikes, crude paintings.",
            exits={"camp": "goblin_camp_main", "lair": "boss_chamber"},
            npcs=[],
            items=[],
            atmosphere="More 'decorated' than the camp, clearly important",
            enter_text="You head toward the chief's lair. The decorations grow more gruesome."
        ),
        "boss_chamber": Location(
            id="boss_chamber",
            name="Chief Grotnak's Throne Room",
            description="A large chamber dominated by a throne of bones. Chief Grotnak sits counting coins, flanked by two bodyguards.",
            exits={"escape": "chief_tunnel"},
            npcs=["grotnak", "bodyguards"],
            items=["healing_potion", "gold"],
            atmosphere="Menacing, the chief's cruel eyes watching, bodyguards ready",
            enter_text="You enter the throne room. Chief Grotnak looks up with a wicked grin."
        ),
        
        # === RESOLUTION SCENE LOCATIONS ===
        "cave_exit": Location(
            id="cave_exit",
            name="Cave Exit",
            description="Daylight streams through the cave entrance. Fresh air replaces the goblin stench.",
            exits={"outside": "return_path"},
            npcs=["lily"],
            items=[],
            atmosphere="Relief, fresh air, sense of accomplishment",
            enter_text="You emerge from the cave into blessed sunlight."
        ),
        "return_path": Location(
            id="return_path",
            name="Return Journey",
            description="The forest path back to the village. The journey feels lighter now.",
            exits={"village": "village_return"},
            npcs=["lily"],
            items=[],
            atmosphere="Lighter mood, Lily's grateful chatter",
            enter_text="The journey home begins. Lily walks beside you, still shaken but safe."
        ),
        "village_return": Location(
            id="village_return",
            name="Village - Hero's Return",
            description="The village square, but now filled with people. Word has spread of your success!",
            exits={"tavern": "tavern_celebration"},
            npcs=["bram", "villagers"],
            items=[],
            atmosphere="Cheering crowds, tearful reunion",
            enter_text="The village erupts in cheers as you return with Lily!"
        ),
        "tavern_celebration": Location(
            id="tavern_celebration",
            name="The Rusty Dragon - Celebration",
            description="The tavern is packed! Drinks flow freely and the villagers toast your heroism.",
            exits={},
            npcs=["bram", "barkeep", "villagers"],
            items=[],
            atmosphere="Celebration, gratitude, hints of future adventures",
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
When player agrees to help, describe them leaving the tavern.

LOCATION NOTES:
- Player starts in main room, can explore bar or go outside
- Bram is in the main room
- Barkeep has gossip if asked
""",
            min_exchanges=3,
            objectives=["meet_bram", "accept_quest"],
            transition_hint="Player accepts the quest and prepares to leave",
            next_scene_id="journey",
            # Location System
            location_ids=["tavern_main", "tavern_bar", "village_square"],
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
            location_ids=["village_square", "forest_path", "forest_clearing", "darkhollow_approach"],
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
            setting="A large cavern lit by smoky torches. 4-5 goblins lounge around a fire. Cages line the far wall. The smell is overwhelming.",
            mood="tense, combat-ready",
            dm_instructions="""
The player enters a main cavern with:
- 4-5 goblins (distracted, gambling, eating)
- A cage with a young girl (Lily, scared but alive)
- Tunnels leading deeper (to the chief's chamber)
- Crude fortifications (overturnable tables, weapon racks)

Let the player choose their approach:
- Stealth: Sneak past or to ambush position (go to shadows location)
- Combat: Fight the goblins
- Distraction: Create diversion
- Negotiation: (Very hard, goblins are hostile)

Resolve the encounter. If player frees Lily, she says the chief has more prisoners.
Chief is in the back chamber with the treasure.

LOCATION NOTES:
- goblin_camp_entrance: can see camp, plan approach
- goblin_camp_shadows: stealth position for surprise
- goblin_camp_main: direct confrontation
- goblin_camp_cages: where Lily is held
""",
            min_exchanges=3,
            objectives=["deal_with_goblins", "find_lily"],
            transition_hint="Player either clears the camp or sneaks through to the chief's chamber",
            next_scene_id="boss_chamber",
            # Location System
            location_ids=["cave_tunnel", "goblin_camp_entrance", "goblin_camp_main", "goblin_camp_shadows", "goblin_camp_cages", "chief_tunnel"],
            starting_location_id="goblin_camp_entrance"
        ),
        
        "boss_chamber": Scene(
            id="boss_chamber",
            name="Chief Grotnak's Lair",
            description="The goblin chief's personal chamber",
            setting="A larger chamber with a crude throne made of bones. A brutish goblin chief sits counting coins. Two goblin bodyguards flank him.",
            mood="climactic, dangerous, decisive",
            dm_instructions="""
BOSS ENCOUNTER: Chief Grotnak
- Larger, meaner, smarter than regular goblins
- Has 2 goblin bodyguards
- Sits on bone throne with a chest of stolen treasure nearby
- If player has Lily, he might threaten her
- If player caused commotion earlier, he's prepared

This is the climax! Make it dramatic:
- Describe his menacing appearance
- Let player make tactical choices
- Include dramatic moments in the fight
- When defeated, describe his fall dramatically

Treasure includes: gold, a minor magic item, personal effects from victims.

LOCATION NOTES:
- chief_tunnel: approach, can hear him counting coins
- boss_chamber: the confrontation
""",
            min_exchanges=3,
            objectives=["defeat_chief"],
            transition_hint="Chief Grotnak is defeated",
            next_scene_id="resolution",
            # Location System
            location_ids=["goblin_camp_main", "chief_tunnel", "boss_chamber"],
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
    
    scenario = Scenario(
        id="goblin_cave",
        name="The Goblin Cave",
        description="Rescue a farmer's daughter from a goblin lair. A classic starter adventure.",
        hook="A desperate farmer's daughter has been kidnapped by goblins. Will you brave the depths of Darkhollow Cave to save her?",
        estimated_duration="20-40 minutes",
        scenes=scenes,
        scene_order=["tavern", "journey", "cave_entrance", "goblin_camp", "boss_chamber", "resolution"],
        location_manager=location_manager
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
