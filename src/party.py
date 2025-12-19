"""
Party System for AI D&D Text RPG
Handles party member management, recruitment, and combat integration.

FEATURES:
- PartyMember dataclass with combat stats and abilities
- Party class for managing party roster (max 2 companions)
- Recruitment system with condition parsing
- Combat integration with turn order and abilities
- Save/load persistence

Per DEVELOPMENT_PLAN.md Phase 3.3.7
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum, auto
import random
import re


# =============================================================================
# PARTY MEMBER CLASSES
# =============================================================================

class PartyMemberClass(Enum):
    """Available classes for party members."""
    FIGHTER = "Fighter"
    RANGER = "Ranger"
    ROGUE = "Rogue"
    CLERIC = "Cleric"
    WIZARD = "Wizard"


# =============================================================================
# SPECIAL ABILITIES
# =============================================================================

@dataclass
class SpecialAbility:
    """
    Represents a party member's special ability.
    
    Abilities can be used once per combat and have various effects.
    """
    name: str
    description: str
    ability_type: str  # "damage", "buff", "heal", "debuff"
    effect_value: str  # Dice notation or flat value, e.g., "1d4", "2", "+2"
    target: str  # "enemy", "self", "ally", "party"
    uses_per_combat: int = 1


# Predefined abilities per class
PARTY_ABILITIES = {
    PartyMemberClass.FIGHTER: SpecialAbility(
        name="Shield Wall",
        description="+2 AC to entire party for 1 round",
        ability_type="buff",
        effect_value="+2",
        target="party",
        uses_per_combat=1
    ),
    PartyMemberClass.RANGER: SpecialAbility(
        name="Hunter's Mark",
        description="+1d4 damage to marked target for rest of combat",
        ability_type="damage",
        effect_value="1d4",
        target="enemy",
        uses_per_combat=1
    ),
    PartyMemberClass.ROGUE: SpecialAbility(
        name="Sneak Attack",
        description="+2d6 damage when flanking (party member attacking same target)",
        ability_type="damage",
        effect_value="2d6",
        target="enemy",
        uses_per_combat=1
    ),
    PartyMemberClass.CLERIC: SpecialAbility(
        name="Healing Word",
        description="Heal an ally for 1d8+2 HP",
        ability_type="heal",
        effect_value="1d8+2",
        target="ally",
        uses_per_combat=1
    ),
    PartyMemberClass.WIZARD: SpecialAbility(
        name="Magic Missile",
        description="Auto-hit attack dealing 1d4+1 damage",
        ability_type="damage",
        effect_value="1d4+1",
        target="enemy",
        uses_per_combat=1
    ),
}


# =============================================================================
# RECRUITMENT CONDITIONS
# =============================================================================

@dataclass
class RecruitmentCondition:
    """
    Represents a single recruitment requirement.
    
    Condition types:
    - skill:<skill_name>:<dc> - Skill check (e.g., "skill:charisma:14")
    - gold:<amount> - Pay gold (e.g., "gold:50")
    - item:<item_id> - Have item (e.g., "item:eliras_bow")
    - objective:<objective_id> - Complete objective (e.g., "objective:cleared_camp")
    """
    condition_type: str  # "skill", "gold", "item", "objective"
    value: str  # skill name, amount, item id, or objective id
    dc: int = 0  # For skill checks
    
    @staticmethod
    def parse(condition_str: str) -> Optional['RecruitmentCondition']:
        """Parse a condition string like 'skill:charisma:14' or 'gold:50'."""
        if not condition_str:
            return None
            
        parts = condition_str.split(":")
        if len(parts) < 2:
            return None
            
        cond_type = parts[0].lower()
        
        if cond_type == "skill" and len(parts) >= 3:
            try:
                dc = int(parts[2])
                return RecruitmentCondition(
                    condition_type="skill",
                    value=parts[1].lower(),
                    dc=dc
                )
            except ValueError:
                return None
                
        elif cond_type == "gold":
            try:
                amount = int(parts[1])
                return RecruitmentCondition(
                    condition_type="gold",
                    value=str(amount)
                )
            except ValueError:
                return None
                
        elif cond_type == "item":
            return RecruitmentCondition(
                condition_type="item",
                value=parts[1].lower()
            )
            
        elif cond_type == "objective":
            return RecruitmentCondition(
                condition_type="objective",
                value=parts[1].lower()
            )
            
        return None
    
    def to_string(self) -> str:
        """Convert back to string format."""
        if self.condition_type == "skill":
            return f"skill:{self.value}:{self.dc}"
        elif self.condition_type == "gold":
            return f"gold:{self.value}"
        elif self.condition_type == "item":
            return f"item:{self.value}"
        elif self.condition_type == "objective":
            return f"objective:{self.value}"
        return ""


# =============================================================================
# PARTY MEMBER DATACLASS
# =============================================================================

@dataclass
class PartyMember:
    """
    Represents a recruitable party member with combat stats and abilities.
    
    Party members can join the player's party and fight alongside them.
    """
    # Identity
    id: str                          # Unique identifier (e.g., "elira_ranger")
    name: str                        # Display name (e.g., "Elira")
    char_class: PartyMemberClass     # Class enum
    description: str                 # Personality/background
    portrait: str = "🧝"             # Emoji/ASCII for display
    
    # Combat Stats
    level: int = 2
    max_hp: int = 18
    current_hp: int = field(init=False)
    armor_class: int = 14
    attack_bonus: int = 4
    damage_dice: str = "1d8+2"
    dex_modifier: int = 2            # For initiative
    
    # Ability
    special_ability: SpecialAbility = field(init=False)
    ability_uses_remaining: int = field(init=False)
    
    # Recruitment
    recruitment_location: str = ""   # Location ID where they can be found
    recruitment_conditions: List[str] = field(default_factory=list)  # OR logic
    recruitment_dialogue: Dict[str, str] = field(default_factory=dict)
    
    # State
    recruited: bool = False          # Has joined the party
    disposition: int = 0             # Attitude toward player (-100 to 100)
    is_dead: bool = False
    initiative: int = 0
    
    # Combat state (reset each combat)
    marked_target: Optional[str] = None  # For Hunter's Mark
    
    def __post_init__(self):
        self.current_hp = self.max_hp
        self.special_ability = PARTY_ABILITIES.get(
            self.char_class,
            PARTY_ABILITIES[PartyMemberClass.FIGHTER]
        )
        self.ability_uses_remaining = self.special_ability.uses_per_combat
    
    def take_damage(self, damage: int) -> str:
        """Apply damage to party member. Returns status message."""
        if damage <= 0:
            return f"{self.name} takes no damage."
            
        self.current_hp -= damage
        
        if self.current_hp <= 0:
            self.current_hp = 0
            self.is_dead = True
            return f"{self.name} has fallen! 💀"
        else:
            return f"{self.name} takes {damage} damage! ({self.current_hp}/{self.max_hp} HP)"
    
    def heal(self, amount: int) -> str:
        """Heal party member. Returns status message."""
        if self.is_dead:
            return f"{self.name} is unconscious and cannot be healed!"
            
        if amount <= 0:
            return f"{self.name} is not healed."
            
        old_hp = self.current_hp
        self.current_hp = min(self.current_hp + amount, self.max_hp)
        healed = self.current_hp - old_hp
        
        return f"{self.name} heals {healed} HP! ({self.current_hp}/{self.max_hp} HP)"
    
    def rest(self):
        """Fully heal on long rest."""
        self.current_hp = self.max_hp
        self.is_dead = False
        self.reset_combat_state()
    
    def reset_combat_state(self):
        """Reset combat-specific state for new encounter."""
        self.ability_uses_remaining = self.special_ability.uses_per_combat
        self.marked_target = None
        self.initiative = 0
    
    def get_status(self) -> str:
        """Get current status string."""
        hp_percent = self.current_hp / self.max_hp
        if self.is_dead:
            return "💀 Unconscious"
        elif hp_percent >= 0.75:
            return "🟢 Healthy"
        elif hp_percent >= 0.5:
            return "🟡 Wounded"
        elif hp_percent >= 0.25:
            return "🟠 Bloodied"
        else:
            return "🔴 Critical"
    
    def can_use_ability(self) -> bool:
        """Check if ability can be used."""
        return self.ability_uses_remaining > 0 and not self.is_dead
    
    def use_ability(self) -> Tuple[bool, str]:
        """Use special ability. Returns (success, message)."""
        if self.is_dead:
            return False, f"{self.name} is unconscious!"
        if self.ability_uses_remaining <= 0:
            return False, f"{self.name} has already used {self.special_ability.name} this combat!"
            
        self.ability_uses_remaining -= 1
        return True, f"✨ {self.name} uses {self.special_ability.name}! {self.special_ability.description}"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for saving."""
        return {
            "id": self.id,
            "name": self.name,
            "char_class": self.char_class.value,
            "description": self.description,
            "portrait": self.portrait,
            "level": self.level,
            "max_hp": self.max_hp,
            "current_hp": self.current_hp,
            "armor_class": self.armor_class,
            "attack_bonus": self.attack_bonus,
            "damage_dice": self.damage_dice,
            "dex_modifier": self.dex_modifier,
            "ability_uses_remaining": self.ability_uses_remaining,
            "recruitment_location": self.recruitment_location,
            "recruitment_conditions": self.recruitment_conditions,
            "recruitment_dialogue": self.recruitment_dialogue,
            "recruited": self.recruited,
            "disposition": self.disposition,
            "is_dead": self.is_dead,
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'PartyMember':
        """Create PartyMember from dictionary."""
        # Parse class enum
        class_str = data.get("char_class", "Fighter")
        try:
            char_class = PartyMemberClass(class_str)
        except ValueError:
            char_class = PartyMemberClass.FIGHTER
        
        member = PartyMember(
            id=data.get("id", "unknown"),
            name=data.get("name", "Unknown"),
            char_class=char_class,
            description=data.get("description", ""),
            portrait=data.get("portrait", "🧝"),
            level=data.get("level", 2),
            max_hp=data.get("max_hp", 18),
            armor_class=data.get("armor_class", 14),
            attack_bonus=data.get("attack_bonus", 4),
            damage_dice=data.get("damage_dice", "1d8+2"),
            dex_modifier=data.get("dex_modifier", 2),
            recruitment_location=data.get("recruitment_location", ""),
            recruitment_conditions=data.get("recruitment_conditions", []),
            recruitment_dialogue=data.get("recruitment_dialogue", {}),
        )
        
        # Restore state
        member.current_hp = data.get("current_hp", member.max_hp)
        member.recruited = data.get("recruited", False)
        member.disposition = data.get("disposition", 0)
        member.is_dead = data.get("is_dead", False)
        
        # Restore ability uses (default to 0 if spent)
        if "ability_uses_remaining" in data:
            member.ability_uses_remaining = data["ability_uses_remaining"]
        
        return member


# =============================================================================
# PARTY CLASS
# =============================================================================

class Party:
    """
    Manages the player's party of companions.
    
    Max party size: 2 companions (player + 2)
    """
    MAX_COMPANIONS = 2
    
    def __init__(self):
        self.members: List[PartyMember] = []
    
    @property
    def size(self) -> int:
        """Current number of party members."""
        return len(self.members)
    
    @property
    def is_full(self) -> bool:
        """Check if party is at maximum capacity."""
        return self.size >= self.MAX_COMPANIONS
    
    def add_member(self, member: PartyMember) -> Tuple[bool, str]:
        """
        Add a party member.
        
        Returns:
            (success, message)
        """
        if self.is_full:
            return False, f"Your party is full! (Max {self.MAX_COMPANIONS} companions)"
        
        # Check if already in party
        if any(m.id == member.id for m in self.members):
            return False, f"{member.name} is already in your party!"
        
        member.recruited = True
        self.members.append(member)
        return True, f"🎉 {member.name} has joined your party!"
    
    def remove_member(self, member_id: str) -> Tuple[bool, str, Optional[PartyMember]]:
        """
        Remove a party member by ID.
        
        Returns:
            (success, message, removed_member)
        """
        for i, member in enumerate(self.members):
            if member.id.lower() == member_id.lower() or member.name.lower() == member_id.lower():
                removed = self.members.pop(i)
                removed.recruited = False
                removed.disposition -= 10  # Dismissal affects disposition
                return True, f"😢 {removed.name} leaves the party.", removed
        
        return False, f"No party member named '{member_id}' found.", None
    
    def get_member(self, member_id: str) -> Optional[PartyMember]:
        """Find a party member by ID or name."""
        for member in self.members:
            if member.id.lower() == member_id.lower() or member.name.lower() == member_id.lower():
                return member
        return None
    
    def get_alive_members(self) -> List[PartyMember]:
        """Get all living party members."""
        return [m for m in self.members if not m.is_dead]
    
    def rest_all(self):
        """Rest all party members (full heal)."""
        for member in self.members:
            member.rest()
    
    def reset_combat_state(self):
        """Reset combat state for all members."""
        for member in self.members:
            member.reset_combat_state()
    
    def format_roster(self) -> str:
        """Format party roster for display."""
        if not self.members:
            return "👥 Your party is empty. You travel alone."
        
        lines = [
            "╔═══════════════════════════════════════════════╗",
            "║ 👥 YOUR PARTY                                 ║",
            "╠═══════════════════════════════════════════════╣",
        ]
        
        for member in self.members:
            status = member.get_status()
            class_str = member.char_class.value
            hp_str = f"{member.current_hp}/{member.max_hp}"
            
            line = f"║ {member.portrait} {member.name} ({class_str}, Lvl {member.level})"
            line = line.ljust(48) + "║"
            lines.append(line)
            
            hp_line = f"║    {status} - HP: {hp_str}"
            hp_line = hp_line.ljust(48) + "║"
            lines.append(hp_line)
        
        lines.append("╚═══════════════════════════════════════════════╝")
        
        return "\n".join(lines)
    
    def format_combat_status(self) -> str:
        """Format party status for combat display."""
        if not self.members:
            return ""
        
        lines = ["  📋 Party:"]
        for member in self.members:
            status_icon = "💀" if member.is_dead else "❤️"
            hp_str = f"{member.current_hp}/{member.max_hp}"
            ability_status = "⭐" if member.can_use_ability() else "○"
            lines.append(f"    {status_icon} {member.name}: {hp_str} HP [{ability_status}]")
        
        return "\n".join(lines)
    
    def to_dict(self) -> dict:
        """Convert party to dictionary for saving."""
        return {
            "members": [m.to_dict() for m in self.members]
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'Party':
        """Create Party from dictionary."""
        party = Party()
        for member_data in data.get("members", []):
            member = PartyMember.from_dict(member_data)
            party.members.append(member)
        return party


# =============================================================================
# RECRUITMENT SYSTEM
# =============================================================================

def check_recruitment_condition(
    condition: RecruitmentCondition,
    character,  # Character object
    quest_manager=None,  # QuestManager for objective checks
    roll_skill_check=None  # Function to perform skill checks
) -> Tuple[bool, str]:
    """
    Check if a recruitment condition is met.
    
    Args:
        condition: The condition to check
        character: Player character
        quest_manager: For checking completed objectives
        roll_skill_check: Function to perform skill checks
        
    Returns:
        (success, message)
    """
    if condition.condition_type == "gold":
        try:
            cost = int(condition.value)
            if character.gold >= cost:
                return True, f"You have enough gold ({cost} gp required)."
            else:
                return False, f"You need {cost} gold. (You have {character.gold} gp)"
        except ValueError:
            return False, "Invalid gold requirement."
    
    elif condition.condition_type == "item":
        # Check if player has the item
        from inventory import find_item_in_inventory
        item = find_item_in_inventory(character.inventory, condition.value)
        if item:
            return True, f"You have the {item.name}."
        else:
            return False, f"You need the item: {condition.value}"
    
    elif condition.condition_type == "objective":
        if quest_manager:
            # Check if objective is completed
            for quest in quest_manager.get_all_quests():
                for obj in quest.objectives:
                    if obj.id.lower() == condition.value.lower() and obj.completed:
                        return True, f"Objective '{obj.description}' completed."
            return False, f"You haven't completed: {condition.value}"
        return False, "Quest system unavailable."
    
    elif condition.condition_type == "skill":
        # Skill check - requires dice roll
        # Returns "pending" state - actual roll happens in game loop
        return True, f"Requires {condition.value.title()} check (DC {condition.dc})"
    
    return False, "Unknown condition type."


def can_attempt_recruitment(
    member: PartyMember,
    character,
    quest_manager=None
) -> Tuple[bool, List[Tuple[str, bool, str]]]:
    """
    Check if recruitment can be attempted.
    
    Conditions use OR logic - any one condition met allows recruitment.
    
    Returns:
        (any_condition_possible, list of (condition_str, met, message))
    """
    if not member.recruitment_conditions:
        # No conditions = always recruitable
        return True, [("none", True, "No requirements.")]
    
    results = []
    any_met = False
    
    for cond_str in member.recruitment_conditions:
        cond = RecruitmentCondition.parse(cond_str)
        if cond:
            met, msg = check_recruitment_condition(cond, character, quest_manager)
            results.append((cond_str, met, msg))
            if met:
                any_met = True
    
    return any_met, results


def pay_recruitment_cost(
    condition: RecruitmentCondition,
    character
) -> Tuple[bool, str]:
    """
    Pay the cost of a recruitment condition (gold, item).
    
    Returns:
        (success, message)
    """
    if condition.condition_type == "gold":
        try:
            cost = int(condition.value)
            if character.gold >= cost:
                character.gold -= cost
                return True, f"Paid {cost} gold."
            else:
                return False, f"Not enough gold!"
        except ValueError:
            return False, "Invalid gold amount."
    
    elif condition.condition_type == "item":
        from inventory import find_item_in_inventory, remove_item_from_inventory
        item = find_item_in_inventory(character.inventory, condition.value)
        if item:
            remove_item_from_inventory(character.inventory, condition.value)
            return True, f"Gave {item.name}."
        else:
            return False, f"You don't have {condition.value}!"
    
    # Skill checks and objectives don't have costs
    return True, ""


# =============================================================================
# PREDEFINED RECRUITABLE NPCs
# =============================================================================

def create_elira_ranger() -> PartyMember:
    """Create Elira the Ranger - forest tracker."""
    return PartyMember(
        id="elira_ranger",
        name="Elira",
        char_class=PartyMemberClass.RANGER,
        description="A half-elf ranger tracking the goblin clan that killed her brother. Reserved and vengeful, but knows goblin tactics better than anyone.",
        portrait="🏹",
        level=2,
        max_hp=18,
        armor_class=14,
        attack_bonus=5,
        damage_dice="1d8+3",
        dex_modifier=3,
        recruitment_location="forest_clearing",
        recruitment_conditions=["skill:charisma:12", "objective:find_scout_body"],
        recruitment_dialogue={
            "greeting": "The ranger barely acknowledges you, eyes scanning the forest. 'You're not one of them. What do you want?'",
            "motivation": "My brother... they took him. I've been tracking this warband for weeks. I know their patterns, their hideouts.",
            "recruit_success": "Perhaps together we stand a better chance. Very well, I'll join you. But we hunt them MY way.",
            "recruit_fail": "I don't trust easily, stranger. Prove yourself first.",
        }
    )


def create_marcus_mercenary() -> PartyMember:
    """Create Marcus the Mercenary - tavern sellsword."""
    return PartyMember(
        id="marcus_mercenary",
        name="Marcus",
        char_class=PartyMemberClass.FIGHTER,
        description="A gruff, practical mercenary between contracts. He's seen it all and survived. Experienced but expensive.",
        portrait="⚔️",
        level=2,
        max_hp=24,
        armor_class=16,
        attack_bonus=5,
        damage_dice="1d10+3",
        dex_modifier=1,
        recruitment_location="tavern_main",
        recruitment_conditions=["gold:25", "skill:charisma:15"],
        recruitment_dialogue={
            "greeting": "The scarred warrior eyes you over his ale. 'Looking for muscle? It'll cost you.'",
            "motivation": "Work's been slow. Goblins, you say? Nasty little things, but gold spends the same.",
            "recruit_success": "Twenty-five gold and we have a deal. Lead the way, boss.",
            "recruit_fail": "Can't work for free, friend. Come back with coin or a VERY convincing argument.",
        }
    )


def create_shade_rogue() -> PartyMember:
    """Create Shade the Rogue - mysterious informant."""
    return PartyMember(
        id="shade_rogue",
        name="Shade",
        char_class=PartyMemberClass.ROGUE,
        description="A mysterious figure lurking in shadows. They seem to know more than they should. Hidden agenda suspected.",
        portrait="🗡️",
        level=2,
        max_hp=14,
        armor_class=15,
        attack_bonus=6,
        damage_dice="1d6+4",
        dex_modifier=4,
        recruitment_location="goblin_camp_shadows",
        recruitment_conditions=["skill:perception:14", "skill:charisma:14"],
        recruitment_dialogue={
            "greeting": "A whisper from the shadows. 'You're more observant than most. Interesting.'",
            "motivation": "The goblins have something that belongs to... someone I work for. Our goals align, for now.",
            "recruit_success": "Consider me your shadow. Just don't ask too many questions.",
            "recruit_fail": "Not everyone can be trusted with certain knowledge. Perhaps later.",
        }
    )


# Registry of all recruitable party members
RECRUITABLE_NPCS = {
    "elira_ranger": create_elira_ranger,
    "marcus_mercenary": create_marcus_mercenary,
    "shade_rogue": create_shade_rogue,
}


def get_recruitable_npc(npc_id: str) -> Optional[PartyMember]:
    """Get a fresh instance of a recruitable NPC."""
    factory = RECRUITABLE_NPCS.get(npc_id.lower())
    if factory:
        return factory()
    return None


def list_recruitable_npcs() -> List[str]:
    """List all recruitable NPC IDs."""
    return list(RECRUITABLE_NPCS.keys())
