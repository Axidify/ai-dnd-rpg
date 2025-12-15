"""
Scenario System for AI D&D Text RPG (Phase 1, Step 1.3)
Manages scenes, story progression, and narrative pacing.
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
    
    # Runtime state
    current_scene_id: Optional[str] = None
    is_complete: bool = False
    
    def start(self) -> Scene:
        """Start the scenario, return first scene."""
        if not self.scene_order:
            raise ValueError("Scenario has no scenes!")
        
        first_scene_id = self.scene_order[0]
        self.current_scene_id = first_scene_id
        self.scenes[first_scene_id].status = SceneStatus.ACTIVE
        return self.scenes[first_scene_id]
    
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
""",
            min_exchanges=3,
            objectives=["meet_bram", "accept_quest"],
            transition_hint="Player accepts the quest and prepares to leave",
            next_scene_id="journey"
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
Build tension as they approach the cave. When they arrive, describe the dark cave mouth.
""",
            min_exchanges=2,
            objectives=[],
            transition_hint="Player arrives at Darkhollow Cave entrance",
            next_scene_id="cave_entrance"
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
""",
            min_exchanges=2,
            objectives=["examine_entrance"],
            transition_hint="Player enters the cave",
            next_scene_id="goblin_camp"
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
- Stealth: Sneak past or to ambush position
- Combat: Fight the goblins
- Distraction: Create diversion
- Negotiation: (Very hard, goblins are hostile)

Resolve the encounter. If player frees Lily, she says the chief has more prisoners.
Chief is in the back chamber with the treasure.
""",
            min_exchanges=3,
            objectives=["deal_with_goblins", "find_lily"],
            transition_hint="Player either clears the camp or sneaks through to the chief's chamber",
            next_scene_id="boss_chamber"
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
""",
            min_exchanges=3,
            objectives=["defeat_chief"],
            transition_hint="Chief Grotnak is defeated",
            next_scene_id="resolution"
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
""",
            min_exchanges=2,
            objectives=[],
            transition_hint="Player receives reward and the adventure concludes",
            next_scene_id=None  # End of scenario
        )
    }
    
    scenario = Scenario(
        id="goblin_cave",
        name="The Goblin Cave",
        description="Rescue a farmer's daughter from a goblin lair. A classic starter adventure.",
        hook="A desperate farmer's daughter has been kidnapped by goblins. Will you brave the depths of Darkhollow Cave to save her?",
        estimated_duration="20-40 minutes",
        scenes=scenes,
        scene_order=["tavern", "journey", "cave_entrance", "goblin_camp", "boss_chamber", "resolution"]
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
