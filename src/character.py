"""
Character System for AI D&D Text RPG (Phase 1, Step 1.2)
Handles player character creation and stat management.
"""

import random
from dataclasses import dataclass, field
from typing import Optional

# D&D 5e Classes
CLASSES = [
    "Fighter",
    "Wizard",
    "Rogue",
    "Cleric",
    "Ranger",
    "Barbarian",
    "Paladin",
    "Warlock",
    "Bard",
    "Monk",
    "Druid",
    "Sorcerer"
]

# D&D 5e Races
RACES = [
    "Human",
    "Elf",
    "Dwarf",
    "Halfling",
    "Half-Orc",
    "Tiefling",
    "Dragonborn",
    "Gnome",
    "Half-Elf"
]


@dataclass
class Character:
    """Represents a player character with D&D stats."""
    
    # Basic Info
    name: str = "Unnamed Hero"
    race: str = "Human"
    char_class: str = "Fighter"
    level: int = 1
    
    # Core Stats (Ability Scores)
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10
    
    # Derived Stats
    max_hp: int = 10
    current_hp: int = 10
    armor_class: int = 10
    
    # Experience
    experience: int = 0
    
    def __post_init__(self):
        """Calculate derived stats after initialization."""
        self._calculate_derived_stats()
    
    def _calculate_derived_stats(self):
        """Calculate HP and AC based on class and stats."""
        con_modifier = self.get_modifier(self.constitution)
        dex_modifier = self.get_modifier(self.dexterity)
        
        # HP based on class hit die + CON modifier
        hit_dice = {
            "Fighter": 10, "Paladin": 10, "Ranger": 10,
            "Barbarian": 12,
            "Wizard": 6, "Sorcerer": 6,
            "Rogue": 8, "Bard": 8, "Warlock": 8, "Monk": 8, "Cleric": 8, "Druid": 8
        }
        hit_die = hit_dice.get(self.char_class, 8)
        self.max_hp = hit_die + con_modifier
        self.current_hp = self.max_hp
        
        # AC = 10 + DEX modifier (unarmored)
        self.armor_class = 10 + dex_modifier
    
    @staticmethod
    def get_modifier(score: int) -> int:
        """Calculate ability modifier from score."""
        return (score - 10) // 2
    
    @staticmethod
    def roll_stat() -> int:
        """Roll 4d6, drop lowest (standard D&D stat generation)."""
        rolls = [random.randint(1, 6) for _ in range(4)]
        rolls.remove(min(rolls))
        return sum(rolls)
    
    @classmethod
    def create_random(cls, name: str) -> 'Character':
        """Create a character with random stats."""
        return cls(
            name=name,
            race=random.choice(RACES),
            char_class=random.choice(CLASSES),
            strength=cls.roll_stat(),
            dexterity=cls.roll_stat(),
            constitution=cls.roll_stat(),
            intelligence=cls.roll_stat(),
            wisdom=cls.roll_stat(),
            charisma=cls.roll_stat()
        )
    
    def format_modifier(self, score: int) -> str:
        """Format modifier as +X or -X."""
        mod = self.get_modifier(score)
        return f"+{mod}" if mod >= 0 else str(mod)
    
    def get_stat_block(self) -> str:
        """Return a formatted character sheet."""
        hp_bar = self._get_hp_bar()
        
        return f"""
╔══════════════════════════════════════════════════════════╗
║                    CHARACTER SHEET                       ║
╠══════════════════════════════════════════════════════════╣
║  Name:  {self.name:<20}  Level: {self.level:<3}            ║
║  Race:  {self.race:<20}  Class: {self.char_class:<12}    ║
╠══════════════════════════════════════════════════════════╣
║                    ABILITY SCORES                        ║
╠══════════════════════════════════════════════════════════╣
║  STR: {self.strength:>2} ({self.format_modifier(self.strength):>3})    DEX: {self.dexterity:>2} ({self.format_modifier(self.dexterity):>3})    CON: {self.constitution:>2} ({self.format_modifier(self.constitution):>3})  ║
║  INT: {self.intelligence:>2} ({self.format_modifier(self.intelligence):>3})    WIS: {self.wisdom:>2} ({self.format_modifier(self.wisdom):>3})    CHA: {self.charisma:>2} ({self.format_modifier(self.charisma):>3})  ║
╠══════════════════════════════════════════════════════════╣
║                    COMBAT STATS                          ║
╠══════════════════════════════════════════════════════════╣
║  HP: {self.current_hp}/{self.max_hp}  {hp_bar:<20}  AC: {self.armor_class:<2}            ║
║  XP: {self.experience:<10}                                       ║
╚══════════════════════════════════════════════════════════╝
"""
    
    def _get_hp_bar(self) -> str:
        """Generate a visual HP bar."""
        bar_length = 15
        filled = int((self.current_hp / self.max_hp) * bar_length)
        empty = bar_length - filled
        return f"[{'█' * filled}{'░' * empty}]"
    
    def take_damage(self, amount: int) -> str:
        """Apply damage to character."""
        self.current_hp = max(0, self.current_hp - amount)
        if self.current_hp == 0:
            return f"{self.name} has fallen unconscious!"
        return f"{self.name} takes {amount} damage! ({self.current_hp}/{self.max_hp} HP)"
    
    def heal(self, amount: int) -> str:
        """Heal the character."""
        old_hp = self.current_hp
        self.current_hp = min(self.max_hp, self.current_hp + amount)
        healed = self.current_hp - old_hp
        return f"{self.name} heals {healed} HP! ({self.current_hp}/{self.max_hp} HP)"
    
    def get_context_for_dm(self) -> str:
        """Return character info formatted for the DM AI."""
        return f"""
PLAYER CHARACTER INFO:
- Name: {self.name}
- Race: {self.race}
- Class: {self.char_class}
- Level: {self.level}
- HP: {self.current_hp}/{self.max_hp}
- AC: {self.armor_class}
- Stats: STR {self.strength}, DEX {self.dexterity}, CON {self.constitution}, INT {self.intelligence}, WIS {self.wisdom}, CHA {self.charisma}

When narrating, incorporate this character's race and class appropriately.
Reference their stats when relevant (a strong character might break down a door, a wise one notices details).
"""


def create_character_interactive() -> Character:
    """Interactive character creation flow."""
    print("\n" + "=" * 60)
    print("              ⚔️  CHARACTER CREATION  ⚔️")
    print("=" * 60)
    
    # Get name
    print("\nWhat is your character's name?")
    name = input("Name: ").strip()
    if not name:
        name = "Unnamed Hero"
    
    # Choose race
    print("\n📜 Choose your race:")
    for i, race in enumerate(RACES, 1):
        print(f"  {i}. {race}")
    print(f"  0. Random")
    
    race_choice = input("\nEnter number: ").strip()
    if race_choice == "0" or not race_choice:
        race = random.choice(RACES)
        print(f"  → Randomly selected: {race}")
    else:
        try:
            race = RACES[int(race_choice) - 1]
        except (ValueError, IndexError):
            race = random.choice(RACES)
            print(f"  → Invalid choice, randomly selected: {race}")
    
    # Choose class
    print("\n⚔️  Choose your class:")
    for i, cls in enumerate(CLASSES, 1):
        print(f"  {i}. {cls}")
    print(f"  0. Random")
    
    class_choice = input("\nEnter number: ").strip()
    if class_choice == "0" or not class_choice:
        char_class = random.choice(CLASSES)
        print(f"  → Randomly selected: {char_class}")
    else:
        try:
            char_class = CLASSES[int(class_choice) - 1]
        except (ValueError, IndexError):
            char_class = random.choice(CLASSES)
            print(f"  → Invalid choice, randomly selected: {char_class}")
    
    # Roll stats
    print("\n🎲 Rolling ability scores (4d6, drop lowest)...")
    print("   Press Enter to roll...")
    input()
    
    stats = {
        "strength": Character.roll_stat(),
        "dexterity": Character.roll_stat(),
        "constitution": Character.roll_stat(),
        "intelligence": Character.roll_stat(),
        "wisdom": Character.roll_stat(),
        "charisma": Character.roll_stat()
    }
    
    print(f"   STR: {stats['strength']:>2}  DEX: {stats['dexterity']:>2}  CON: {stats['constitution']:>2}")
    print(f"   INT: {stats['intelligence']:>2}  WIS: {stats['wisdom']:>2}  CHA: {stats['charisma']:>2}")
    
    # Create character
    character = Character(
        name=name,
        race=race,
        char_class=char_class,
        **stats
    )
    
    print("\n✨ Character created!")
    print(character.get_stat_block())
    
    return character


def quick_create_character(name: str = None) -> Character:
    """Quick character creation with defaults."""
    if name is None:
        name = "Hero"
    return Character.create_random(name)
