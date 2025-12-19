"""
NPC System for AI D&D Text RPG (Phase 3.3, Step 3.3.1)
Handles Non-Player Characters with dialogue and quests.

FEATURES:
- NPC dataclass with role-based behavior (quest_giver, etc.)
- Dialogue system with keyed responses
- Disposition tracking for relationship building
- Quest assignment for quest givers
- Recruitment system for party members
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Any


# =============================================================================
# DISPOSITION THRESHOLDS (Phase 3.3, Priority 6)
# =============================================================================

# Disposition level thresholds - used for behavior changes
DISPOSITION_HOSTILE = -50      # Below this: hostile behavior (threats)
DISPOSITION_UNFRIENDLY = -10   # Below this: unfriendly behavior
DISPOSITION_FRIENDLY = 10      # Above this: friendly behavior
DISPOSITION_TRUSTED = 50       # Above this: trusted behavior (special quests)


def calculate_gift_disposition(item_value: int) -> int:
    """
    Calculate disposition bonus from giving an item as a gift.
    
    Args:
        item_value: The gold value of the item being given
        
    Returns:
        Disposition bonus to apply (+5 to +20 based on value)
    """
    if item_value <= 0:
        return 0
    elif item_value <= 10:
        return 5       # Cheap gift
    elif item_value <= 25:
        return 8       # Modest gift
    elif item_value <= 50:
        return 12      # Nice gift
    elif item_value <= 100:
        return 15      # Generous gift
    else:
        return 20      # Extravagant gift


# =============================================================================
# NPC ROLE ENUM
# =============================================================================

class NPCRole(Enum):
    """Defines the primary role/behavior of an NPC."""
    QUEST_GIVER = auto()    # Offers quests
    INFO = auto()           # Provides information/gossip
    HOSTILE = auto()        # Enemy NPC (may trigger combat)
    RECRUITABLE = auto()    # Can join player's party
    MERCHANT = auto()       # Runs a shop, can buy/sell items
    NEUTRAL = auto()        # Generic NPC, no special role


# =============================================================================
# PERSONALITY SYSTEM (Phase 3.4 - Consistent NPC Characterization)
# =============================================================================

@dataclass
class Personality:
    """
    Structured personality data for consistent NPC characterization.
    
    The DM uses this data to roleplay NPCs consistently across interactions.
    All fields are optional - use what makes sense for each NPC.
    
    Attributes:
        traits: 3-5 core personality adjectives (e.g., ["gruff", "honest", "protective"])
        speech_style: How they talk (e.g., "formal", "folksy", "curt", "flowery")
        voice_notes: Acting direction for dialogue (e.g., "deep gravelly voice")
        motivations: What drives this character (e.g., ["protect family", "make money"])
        fears: What they avoid or worry about
        quirks: Behavioral tics and habits (e.g., ["scratches beard when nervous"])
        secrets: Hidden info only the DM should know (not revealed unless discovered)
    """
    traits: List[str] = field(default_factory=list)
    speech_style: str = ""
    voice_notes: str = ""
    motivations: List[str] = field(default_factory=list)
    fears: List[str] = field(default_factory=list)
    quirks: List[str] = field(default_factory=list)
    secrets: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "traits": self.traits.copy(),
            "speech_style": self.speech_style,
            "voice_notes": self.voice_notes,
            "motivations": self.motivations.copy(),
            "fears": self.fears.copy(),
            "quirks": self.quirks.copy(),
            "secrets": self.secrets.copy()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Personality":
        """Create Personality from dictionary."""
        return cls(
            traits=data.get("traits", []),
            speech_style=data.get("speech_style", ""),
            voice_notes=data.get("voice_notes", ""),
            motivations=data.get("motivations", []),
            fears=data.get("fears", []),
            quirks=data.get("quirks", []),
            secrets=data.get("secrets", [])
        )
    
    def get_dm_summary(self, include_secrets: bool = True) -> str:
        """
        Generate a summary string for the DM to use during roleplay.
        
        Args:
            include_secrets: Whether to include secret info (True for DM, False for players)
        """
        parts = []
        
        if self.traits:
            parts.append(f"Personality: {', '.join(self.traits)}")
        
        if self.speech_style:
            parts.append(f"Speech: {self.speech_style}")
        
        if self.voice_notes:
            parts.append(f"Voice: {self.voice_notes}")
        
        if self.motivations:
            parts.append(f"Motivated by: {', '.join(self.motivations)}")
        
        if self.fears:
            parts.append(f"Fears: {', '.join(self.fears)}")
        
        if self.quirks:
            parts.append(f"Quirks: {', '.join(self.quirks)}")
        
        if include_secrets and self.secrets:
            parts.append(f"[SECRET]: {'; '.join(self.secrets)}")
        
        return "\n".join(parts) if parts else ""


# =============================================================================
# NPC DATACLASS
# =============================================================================

@dataclass
class NPC:
    """
    Represents a Non-Player Character in the game world.
    
    Attributes:
        id: Unique identifier (e.g., "bram_farmer", "barkeep")
        name: Display name (e.g., "Bram", "The Barkeep")
        description: Physical/personality description for AI context
        role: Primary NPC role (affects available interactions)
        location_id: Current location where NPC can be found
        dialogue: Dict of keyed responses ("greeting", "quest", "farewell", etc.)
        disposition: Attitude toward player (-100 to 100, 0 = neutral)
        quests: List of quest IDs this NPC can give
        is_recruitable: Can this NPC join the player's party?
        recruitment_condition: Condition to recruit (e.g., "skill:charisma:14")
    """
    id: str
    name: str
    description: str = ""
    role: NPCRole = NPCRole.NEUTRAL
    location_id: str = ""
    
    # Dialogue system
    dialogue: Dict[str, str] = field(default_factory=dict)
    
    # Relationship
    disposition: int = 0  # -100 (hostile) to +100 (friendly)
    
    # Quest giver
    quests: List[str] = field(default_factory=list)
    
    # Recruitable
    is_recruitable: bool = False
    recruitment_condition: str = ""  # e.g., "skill:charisma:14" or "gold:25"
    recruited: bool = False
    
    # Personality System (Phase 3.4 - Consistent Characterization)
    personality: Optional[Personality] = None  # Structured personality data for DM
    
    def __post_init__(self):
        """Validate NPC data after initialization."""
        if not self.id:
            raise ValueError("NPC must have an id")
        if not self.name:
            raise ValueError("NPC must have a name")
    
    # =========================================================================
    # DISPOSITION SYSTEM
    # =========================================================================
    
    def get_disposition_level(self) -> str:
        """
        Get a descriptive level for current disposition.
        Uses module-level threshold constants.
        
        Returns:
            str: One of 'hostile', 'unfriendly', 'neutral', 'friendly', 'trusted'
        """
        if self.disposition < DISPOSITION_HOSTILE:
            return "hostile"
        elif self.disposition < DISPOSITION_UNFRIENDLY:
            return "unfriendly"
        elif self.disposition <= DISPOSITION_FRIENDLY:
            return "neutral"
        elif self.disposition <= DISPOSITION_TRUSTED:
            return "friendly"
        else:
            return "trusted"
    
    def get_disposition_label(self) -> str:
        """
        Get a display-friendly label with emoji for current disposition.
        
        Returns:
            str: Formatted label like "🔴 Hostile (-75)" or "🟢 Friendly (+35)"
        """
        level = self.get_disposition_level()
        sign = "+" if self.disposition > 0 else ""
        
        labels = {
            "hostile": f"🔴 Hostile ({sign}{self.disposition})",
            "unfriendly": f"🟠 Unfriendly ({sign}{self.disposition})",
            "neutral": f"🟡 Neutral ({sign}{self.disposition})",
            "friendly": f"🟢 Friendly ({sign}{self.disposition})",
            "trusted": f"🔵 Trusted ({sign}{self.disposition})"
        }
        return labels.get(level, f"Unknown ({self.disposition})")
    
    def can_trade(self) -> bool:
        """
        Check if the NPC will interact with the player based on disposition.
        
        Returns:
            bool: True if disposition allows interaction, False if hostile
        """
        return self.get_disposition_level() != "hostile"
    
    def modify_disposition(self, amount: int) -> int:
        """
        Modify disposition by amount, clamping to -100 to +100.
        Returns the new disposition value.
        """
        self.disposition = max(-100, min(100, self.disposition + amount))
        return self.disposition
    
    # =========================================================================
    # DIALOGUE SYSTEM
    # =========================================================================
    
    def get_dialogue(self, key: str) -> Optional[str]:
        """
        Get a dialogue response by key.
        Keys: "greeting", "farewell", "quest", "recruit", "about_<topic>"
        """
        return self.dialogue.get(key.lower())
    
    def has_dialogue(self, key: str) -> bool:
        """Check if NPC has dialogue for a specific key."""
        return key.lower() in self.dialogue
    
    def add_dialogue(self, key: str, text: str):
        """Add or update a dialogue entry."""
        self.dialogue[key.lower()] = text
    
    def get_context_for_dm(self) -> str:
        """
        Build context string about this NPC for the AI DM.
        Used to inform AI about NPC personality and available interactions.
        """
        context_parts = [
            f"NPC: {self.name}",
            f"Role: {self.role.name}",
            f"Disposition: {self.get_disposition_level()} ({self.disposition})"
        ]
        
        if self.description:
            context_parts.append(f"Description: {self.description}")
        
        if self.role == NPCRole.QUEST_GIVER and self.quests:
            context_parts.append(f"Offers quests: {', '.join(self.quests)}")
        
        if self.is_recruitable and not self.recruited:
            context_parts.append(f"Recruitable (condition: {self.recruitment_condition})")
        
        # Include personality data for consistent characterization
        if self.personality:
            personality_summary = self.personality.get_dm_summary(include_secrets=True)
            if personality_summary:
                context_parts.append("")  # Blank line for readability
                context_parts.append("=== PERSONALITY ===")
                context_parts.append(personality_summary)
        
        return "\n".join(context_parts)
    
    # =========================================================================
    # SERIALIZATION
    # =========================================================================
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert NPC to dictionary for saving."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "role": self.role.name,
            "location_id": self.location_id,
            "dialogue": self.dialogue.copy(),
            "disposition": self.disposition,
            "quests": self.quests.copy(),
            "is_recruitable": self.is_recruitable,
            "recruitment_condition": self.recruitment_condition,
            "recruited": self.recruited,
            "personality": self.personality.to_dict() if self.personality else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NPC':
        """Create NPC from dictionary (for loading)."""
        role = NPCRole[data.get("role", "NEUTRAL")]
        
        # Load personality if present
        personality_data = data.get("personality")
        personality = Personality.from_dict(personality_data) if personality_data else None
        
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            role=role,
            location_id=data.get("location_id", ""),
            dialogue=data.get("dialogue", {}),
            disposition=data.get("disposition", 0),
            quests=data.get("quests", []),
            is_recruitable=data.get("is_recruitable", False),
            recruitment_condition=data.get("recruitment_condition", ""),
            recruited=data.get("recruited", False),
            personality=personality
        )


# =============================================================================
# NPC MANAGER
# =============================================================================

class NPCManager:
    """
    Manages all NPCs in the game world.
    Handles NPC lookup, filtering by location, and state persistence.
    """
    
    def __init__(self):
        self._npcs: Dict[str, NPC] = {}
    
    def add_npc(self, npc: NPC):
        """Add an NPC to the manager."""
        self._npcs[npc.id] = npc
    
    def get_npc(self, npc_id: str) -> Optional[NPC]:
        """Get an NPC by ID."""
        return self._npcs.get(npc_id)
    
    def get_npc_by_name(self, name: str) -> Optional[NPC]:
        """Get an NPC by name (case-insensitive)."""
        name_lower = name.lower()
        for npc in self._npcs.values():
            if npc.name.lower() == name_lower:
                return npc
        return None
    
    def get_npcs_at_location(self, location_id: str) -> List[NPC]:
        """Get all NPCs at a specific location."""
        return [npc for npc in self._npcs.values() 
                if npc.location_id == location_id and not npc.recruited]
    
    def get_npcs_by_role(self, role: NPCRole) -> List[NPC]:
        """Get all NPCs with a specific role."""
        return [npc for npc in self._npcs.values() if npc.role == role]
    
    def get_quest_givers(self) -> List[NPC]:
        """Get all quest giver NPCs."""
        return self.get_npcs_by_role(NPCRole.QUEST_GIVER)
    
    def get_recruitable(self) -> List[NPC]:
        """Get all recruitable NPCs who haven't been recruited yet."""
        return [npc for npc in self._npcs.values() 
                if npc.is_recruitable and not npc.recruited]
    
    def get_all_npcs(self) -> List[NPC]:
        """Get all NPCs."""
        return list(self._npcs.values())
    
    def remove_npc(self, npc_id: str) -> bool:
        """Remove an NPC from the manager. Returns True if removed."""
        if npc_id in self._npcs:
            del self._npcs[npc_id]
            return True
        return False
    
    def move_npc(self, npc_id: str, new_location_id: str) -> bool:
        """Move an NPC to a new location. Returns True if successful."""
        npc = self.get_npc(npc_id)
        if npc:
            npc.location_id = new_location_id
            return True
        return False
    
    # =========================================================================
    # SERIALIZATION
    # =========================================================================
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert NPC manager state to dictionary for saving."""
        return {
            "npcs": {npc_id: npc.to_dict() for npc_id, npc in self._npcs.items()}
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """Restore NPC manager state from dictionary."""
        self._npcs.clear()
        for npc_id, npc_data in data.get("npcs", {}).items():
            self._npcs[npc_id] = NPC.from_dict(npc_data)
    
    def update_npc_states(self, saved_states: Dict[str, Dict[str, Any]]):
        """
        Update NPC states from saved data without replacing the whole NPC.
        Useful for loading dynamic state (disposition, recruited, etc.)
        """
        for npc_id, state in saved_states.items():
            npc = self.get_npc(npc_id)
            if npc:
                if "disposition" in state:
                    npc.disposition = state["disposition"]
                if "recruited" in state:
                    npc.recruited = state["recruited"]
                if "location_id" in state:
                    npc.location_id = state["location_id"]


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def format_npc_for_display(npc: NPC) -> str:
    """Format NPC info for player display."""
    role_icons = {
        NPCRole.QUEST_GIVER: "❗",
        NPCRole.INFO: "💬",
        NPCRole.HOSTILE: "⚔️",
        NPCRole.RECRUITABLE: "👥",
        NPCRole.NEUTRAL: "👤"
    }
    icon = role_icons.get(npc.role, "👤")
    disp = npc.get_disposition_level()
    
    return f"{icon} {npc.name} ({disp})"