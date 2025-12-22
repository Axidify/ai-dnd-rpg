"""
Combat System for AI D&D Text RPG
Handles attack rolls, damage, and combat encounters.
"""

import html
import random
from dataclasses import dataclass, field
from typing import Optional, Tuple, List
from character import Character


# =============================================================================
# WEAPON DATA
# =============================================================================

WEAPONS = {
    # Simple Melee
    'dagger': {'damage': '1d4', 'type': 'piercing', 'finesse': True},
    'handaxe': {'damage': '1d6', 'type': 'slashing', 'finesse': False},
    'mace': {'damage': '1d6', 'type': 'bludgeoning', 'finesse': False},
    'quarterstaff': {'damage': '1d6', 'type': 'bludgeoning', 'finesse': False},
    'spear': {'damage': '1d6', 'type': 'piercing', 'finesse': False},
    
    # Martial Melee
    'longsword': {'damage': '1d8', 'type': 'slashing', 'finesse': False},
    'shortsword': {'damage': '1d6', 'type': 'piercing', 'finesse': True},
    'greataxe': {'damage': '1d12', 'type': 'slashing', 'finesse': False},
    'greatsword': {'damage': '2d6', 'type': 'slashing', 'finesse': False},
    'rapier': {'damage': '1d8', 'type': 'piercing', 'finesse': True},
    'warhammer': {'damage': '1d8', 'type': 'bludgeoning', 'finesse': False},
    
    # Ranged
    'shortbow': {'damage': '1d6', 'type': 'piercing', 'finesse': True},
    'longbow': {'damage': '1d8', 'type': 'piercing', 'finesse': True},
    'light_crossbow': {'damage': '1d8', 'type': 'piercing', 'finesse': True},
    
    # Unarmed
    'unarmed': {'damage': '1d1', 'type': 'bludgeoning', 'finesse': False},
}


# =============================================================================
# CLASS-APPROPRIATE WEAPON POOLS (Phase 3.2.2)
# =============================================================================

# Weapons appropriate for each class when dropped as loot
CLASS_WEAPON_POOLS = {
    "Fighter": ["longsword", "greatsword", "warhammer", "greataxe"],
    "Paladin": ["longsword", "warhammer", "greatsword", "mace"],
    "Ranger": ["shortbow", "longbow", "shortsword", "light_crossbow"],
    "Barbarian": ["greataxe", "greatsword", "warhammer", "handaxe"],
    "Wizard": ["quarterstaff", "dagger"],
    "Sorcerer": ["quarterstaff", "dagger"],
    "Rogue": ["shortsword", "dagger", "rapier"],
    "Bard": ["rapier", "shortsword", "dagger"],
    "Warlock": ["quarterstaff", "dagger"],
    "Monk": ["quarterstaff", "shortsword"],
    "Cleric": ["mace", "warhammer", "quarterstaff"],
    "Druid": ["quarterstaff", "spear"],
}

# Quality tiers with drop rates and stat bonuses
# Rolls 1-100: Common 1-60, Uncommon 61-85, Rare 86-97, Epic 98-100
QUALITY_TIERS = {
    "Common": {"max_roll": 60, "bonus": 0, "prefix": ""},
    "Uncommon": {"max_roll": 85, "bonus": 1, "prefix": "Fine "},
    "Rare": {"max_roll": 97, "bonus": 2, "prefix": "Superior "},
    "Epic": {"max_roll": 100, "bonus": 3, "prefix": "Legendary "},
}


def roll_quality_tier() -> Tuple[str, dict]:
    """Roll for weapon quality tier. Returns (tier_name, tier_data)."""
    roll = random.randint(1, 100)
    for tier_name, tier_data in QUALITY_TIERS.items():
        if roll <= tier_data["max_roll"]:
            return tier_name, tier_data
    return "Common", QUALITY_TIERS["Common"]


def generate_class_weapon(player_class: str) -> Tuple[str, str, int]:
    """
    Generate a class-appropriate weapon with random quality.
    
    Args:
        player_class: The player's character class
        
    Returns:
        Tuple of (weapon_id, display_name, bonus)
        - weapon_id: Base weapon type (e.g., "longsword")
        - display_name: Full name with quality (e.g., "Superior Longsword")
        - bonus: Stat bonus from quality tier (0-3)
    """
    # Get weapon pool for class, default to Fighter weapons
    weapon_pool = CLASS_WEAPON_POOLS.get(player_class, CLASS_WEAPON_POOLS["Fighter"])
    
    # Pick random weapon from pool
    base_weapon = random.choice(weapon_pool)
    
    # Roll quality tier
    tier_name, tier_data = roll_quality_tier()
    
    # Build display name (e.g., "Fine Longsword" or just "Longsword" for Common)
    display_name = f"{tier_data['prefix']}{base_weapon.replace('_', ' ').title()}"
    
    return base_weapon, display_name, tier_data["bonus"]


# =============================================================================
# ENEMY CLASS
# =============================================================================

@dataclass
class Enemy:
    """Represents an enemy in combat."""
    name: str
    max_hp: int
    armor_class: int
    attack_bonus: int
    damage_dice: str
    damage_bonus: int = 0
    dex_modifier: int = 2  # For initiative
    xp_reward: int = 25    # XP awarded when defeated (Phase 3.2.2)
    loot: List[str] = field(default_factory=list)  # Phase 3.2.2: Fixed loot drops
    gold_drop: int = 0     # Phase 3.2.2: Fixed gold drop
    current_hp: int = field(init=False)
    _is_dead: bool = field(default=False, repr=False)  # Internal flag, use property
    initiative: int = 0
    
    def __post_init__(self):
        self.current_hp = self.max_hp
    
    @property
    def is_dead(self) -> bool:
        """Check if enemy is dead (HP <= 0)."""
        return self.current_hp <= 0
    
    @is_dead.setter
    def is_dead(self, value: bool):
        """Allow setting is_dead for compatibility (sets internal flag)."""
        self._is_dead = value
    
    def take_damage(self, damage: int) -> str:
        """Apply damage to enemy. Returns status message."""
        if damage <= 0:
            return f"{self.name} takes no damage."
        self.current_hp = max(0, self.current_hp - damage)
        if self.current_hp == 0:
            return f"{self.name} falls!"
        else:
            return f"{self.name} takes {damage} damage! ({self.current_hp}/{self.max_hp} HP)"
    
    def get_status(self) -> str:
        """Get enemy health status."""
        if self.is_dead:
            return f"💀 {self.name} (Defeated)"
        
        percent = self.current_hp / self.max_hp
        if percent > 0.75:
            condition = "healthy"
        elif percent > 0.5:
            condition = "wounded"
        elif percent > 0.25:
            condition = "badly wounded"
        else:
            condition = "near death"
        return f"⚔️ {self.name}: {condition} ({self.current_hp}/{self.max_hp} HP)"


# =============================================================================
# PRESET ENEMIES
# =============================================================================

# XP and Loot values balanced for the Goblin Cave scenario:
# - Players should reach ~Level 2 by boss fight (100 XP needed)
# - 4 goblins at camp = 100 XP (25 each)
# - Boss + 2 bodyguards = 150 XP (100 boss + 25 each minion)
# - Total combat XP: 250 XP (enough for Level 2, progress to Level 3)
#
# Loot distribution (Phase 3.2.2 - Fixed for balance):
# - Regular enemies: Small gold, maybe 1 common item (25% of goblins)
# - Boss enemies: Good gold, guaranteed useful item

ENEMIES = {
    'goblin': Enemy(
        name="Goblin",
        max_hp=5,           # Lowered for balance (was 7)
        armor_class=12,     # Lowered for balance (was 15)
        attack_bonus=3,     # Lowered for balance (was 4)
        damage_dice="1d6",
        damage_bonus=1,     # Lowered for balance (was 2)
        dex_modifier=2,
        xp_reward=25,      # Minor enemy
        loot=[],           # Basic goblins drop nothing (gold only)
        gold_drop=3        # 3 gold per goblin
    ),
    'goblin_boss': Enemy(
        name="Goblin Boss",
        max_hp=21,
        armor_class=17,
        attack_bonus=5,
        damage_dice="1d8",
        damage_bonus=3,
        dex_modifier=2,
        xp_reward=100,                       # Boss enemy
        loot=["healing_potion", "shortsword"],  # Guaranteed useful loot
        gold_drop=20                         # Good gold drop
    ),
    'skeleton': Enemy(
        name="Skeleton",
        max_hp=13,
        armor_class=13,
        attack_bonus=4,
        damage_dice="1d6",
        damage_bonus=2,
        dex_modifier=2,
        xp_reward=25,      # Minor enemy
        loot=[],           # Undead carry nothing
        gold_drop=0        # No gold
    ),
    'orc': Enemy(
        name="Orc",
        max_hp=15,
        armor_class=13,
        attack_bonus=5,
        damage_dice="1d12",
        damage_bonus=3,
        dex_modifier=1,
        xp_reward=50,                # Medium enemy
        loot=["rations"],            # Orcs carry food
        gold_drop=8                  # Moderate gold
    ),
    'bandit': Enemy(
        name="Bandit",
        max_hp=11,
        armor_class=12,
        attack_bonus=3,
        damage_dice="1d6",
        damage_bonus=1,
        dex_modifier=1,
        xp_reward=25,                # Minor enemy
        loot=["lockpicks"],          # Bandits carry tools
        gold_drop=10                 # Stolen gold
    ),
    'wolf': Enemy(
        name="Wolf",
        max_hp=8,           # Lowered for balance (was 11)
        armor_class=11,     # Lowered for balance (was 13)
        attack_bonus=4,
        damage_dice="2d4",
        damage_bonus=2,
        dex_modifier=2,
        xp_reward=25,      # Minor enemy
        loot=[],           # Animals don't carry items
        gold_drop=0        # No gold
    ),
    'giant_spider': Enemy(
        name="Giant Spider",
        max_hp=18,          # Lowered for balance (was 26)
        armor_class=13,     # Lowered for balance (was 14)
        attack_bonus=4,     # Lowered for balance (was 5)
        damage_dice="1d8",
        damage_bonus=2,     # Lowered for balance (was 3)
        dex_modifier=3,
        xp_reward=50,      # Moderate enemy
        loot=["poison_vial"],  # Venom can be harvested
        gold_drop=0        # Animals don't carry gold
    ),
}


def create_enemy(enemy_type: str) -> Optional[Enemy]:
    """Create a new enemy instance from preset."""
    if enemy_type.lower() in ENEMIES:
        template = ENEMIES[enemy_type.lower()]
        return Enemy(
            name=template.name,
            max_hp=template.max_hp,
            armor_class=template.armor_class,
            attack_bonus=template.attack_bonus,
            damage_dice=template.damage_dice,
            damage_bonus=template.damage_bonus,
            dex_modifier=template.dex_modifier,
            xp_reward=template.xp_reward,  # Phase 3.2.2: Include XP reward
            loot=template.loot.copy(),     # Phase 3.2.2: Fixed loot drops
            gold_drop=template.gold_drop   # Phase 3.2.2: Fixed gold drop
        )
    return None


def get_enemy_xp(enemy_type: str) -> int:
    """Get XP reward for an enemy type. Returns 0 if unknown."""
    if enemy_type.lower() in ENEMIES:
        return ENEMIES[enemy_type.lower()].xp_reward
    return 0


def get_enemy_loot(enemy_type: str) -> tuple:
    """
    Get fixed loot for an enemy type (Phase 3.2.2).
    Returns (loot_items: List[str], gold: int).
    """
    if enemy_type.lower() in ENEMIES:
        enemy = ENEMIES[enemy_type.lower()]
        return enemy.loot.copy(), enemy.gold_drop
    return [], 0


def get_enemy_loot_for_class(enemy_type: str, player_class: str) -> tuple:
    """
    Get loot for an enemy type with class-appropriate weapon drops (Phase 3.2.2).
    
    Replaces generic weapon drops (like "shortsword") with class-appropriate
    weapons of random quality.
    
    Args:
        enemy_type: The type of enemy (e.g., "goblin_boss")
        player_class: The player's character class (e.g., "Fighter")
        
    Returns:
        Tuple of (loot_items: List[str], gold: int)
        - loot_items now contains class-appropriate weapon names with quality
    """
    # Get base loot
    loot, gold = get_enemy_loot(enemy_type)
    
    # List of base weapon IDs that should be replaced with class weapons
    replaceable_weapons = ["shortsword", "longsword", "dagger", "mace", 
                          "quarterstaff", "greataxe", "shortbow", "longbow"]
    
    # Process each loot item
    processed_loot = []
    for item in loot:
        if item.lower() in replaceable_weapons:
            # Replace with class-appropriate weapon
            base_weapon, display_name, bonus = generate_class_weapon(player_class)
            processed_loot.append(display_name)
        else:
            # Keep non-weapon items as-is
            processed_loot.append(item)
    
    return processed_loot, gold


# =============================================================================
# INITIATIVE SYSTEM
# =============================================================================

@dataclass
class Combatant:
    """Wrapper for any combat participant."""
    name: str
    initiative: int
    is_player: bool
    entity: any  # Character, Enemy, or PartyMember
    is_ally: bool = False  # True for party members (Phase 3.5 P7 Step 6)
    
    def is_enemy(self) -> bool:
        """Check if this combatant is an enemy."""
        return not self.is_player and not self.is_ally


def roll_initiative(dex_modifier: int) -> dict:
    """Roll initiative (d20 + DEX modifier)."""
    roll = random.randint(1, 20)
    total = roll + dex_modifier
    return {
        'roll': roll,
        'modifier': dex_modifier,
        'total': total,
    }


def format_initiative_roll(name: str, result: dict) -> str:
    """Format initiative roll for display."""
    mod_sign = '+' if result['modifier'] >= 0 else ''
    return f"🎯 {name} Initiative: [{result['roll']}]{mod_sign}{result['modifier']} = {result['total']}"


def determine_turn_order(player_name: str, player_dex_mod: int, 
                         enemies: list[Enemy], 
                         party_members: list = None) -> list[Combatant]:
    """
    Roll initiative for all combatants and determine turn order.
    Returns sorted list of Combatants (highest initiative first).
    
    Args:
        player_name: The player character's name
        player_dex_mod: Player's DEX modifier
        enemies: List of Enemy objects
        party_members: Optional list of PartyMember objects (from party.py)
    """
    combatants = []
    
    # Player initiative
    player_init = roll_initiative(player_dex_mod)
    combatants.append(Combatant(
        name=player_name,
        initiative=player_init['total'],
        is_player=True,
        entity=None  # Will be set externally
    ))
    
    # Party member initiatives (Phase 3.5 P7 Step 6)
    if party_members:
        for member in party_members:
            if hasattr(member, 'is_dead') and member.is_dead:
                continue  # Skip dead party members
            if hasattr(member, 'recruited') and not member.recruited:
                continue  # Skip non-recruited members
            member_init = roll_initiative(getattr(member, 'dex_modifier', 2))
            member.initiative = member_init['total']
            combatants.append(Combatant(
                name=member.name,
                initiative=member_init['total'],
                is_player=False,  # Not player, but ally
                entity=member,
                is_ally=True  # Mark as party member
            ))
    
    # Enemy initiatives
    for enemy in enemies:
        enemy_init = roll_initiative(enemy.dex_modifier)
        enemy.initiative = enemy_init['total']
        combatants.append(Combatant(
            name=enemy.name,
            initiative=enemy_init['total'],
            is_player=False,
            entity=enemy,
            is_ally=False  # Enemy
        ))
    
    # Sort by initiative (descending), ties go to higher DEX
    combatants.sort(key=lambda c: c.initiative, reverse=True)
    
    return combatants


def display_turn_order(combatants: list[Combatant], current_idx: int = 0) -> str:
    """Display the turn order with current turn marked."""
    lines = ["╔══════════════════════════════════════╗",
             "║          ⚔️ TURN ORDER ⚔️            ║",
             "╠══════════════════════════════════════╣"]
    
    for i, c in enumerate(combatants):
        marker = "▶" if i == current_idx else " "
        player_tag = "(You)" if c.is_player else ""
        lines.append(f"║  {marker} {c.initiative:2d} - {c.name} {player_tag}".ljust(39) + "║")
    
    lines.append("╚══════════════════════════════════════╝")
    return "\n".join(lines)


# =============================================================================
# DICE ROLLING
# =============================================================================

def roll_dice(dice_notation: str) -> Tuple[int, list]:
    """
    Roll dice from notation like "1d6", "2d8+3", "1d20".
    Returns (total, individual_rolls).
    """
    import re
    pattern = r'^(\d*)d(\d+)([+-]\d+)?$'
    match = re.match(pattern, dice_notation.lower().replace(' ', ''))
    
    if not match:
        return (1, [1])  # Default to 1 on invalid notation
    
    count = int(match.group(1)) if match.group(1) else 1
    sides = int(match.group(2))
    modifier = int(match.group(3)) if match.group(3) else 0
    
    rolls = [random.randint(1, sides) for _ in range(count)]
    total = sum(rolls) + modifier
    
    return (total, rolls)


# =============================================================================
# ATTACK SYSTEM
# =============================================================================

def calculate_attack_bonus(character: Character, weapon_name: str = 'longsword') -> int:
    """Calculate character's attack bonus for a weapon."""
    weapon = WEAPONS.get(weapon_name.lower(), WEAPONS['unarmed'])
    
    # Proficiency bonus (simplified: level 1-4 = +2)
    proficiency = 2
    
    # Use DEX for finesse weapons, STR otherwise
    if weapon.get('finesse', False):
        stat_mod = character.get_ability_modifier('dexterity')
    else:
        stat_mod = character.get_ability_modifier('strength')
    
    return proficiency + stat_mod


def calculate_damage_bonus(character: Character, weapon_name: str = 'longsword') -> int:
    """Calculate character's damage bonus for a weapon."""
    weapon = WEAPONS.get(weapon_name.lower(), WEAPONS['unarmed'])
    
    # Use DEX for finesse weapons, STR otherwise
    if weapon.get('finesse', False):
        return character.get_ability_modifier('dexterity')
    else:
        return character.get_ability_modifier('strength')


def roll_attack(character: Character, target_ac: int, weapon_name: str = 'longsword') -> dict:
    """
    Roll an attack against a target AC.
    Returns dict with roll details and hit/miss.
    """
    weapon = WEAPONS.get(weapon_name.lower(), WEAPONS['longsword'])
    attack_bonus = calculate_attack_bonus(character, weapon_name)
    
    # Roll d20
    d20_roll = random.randint(1, 20)
    total = d20_roll + attack_bonus
    
    is_nat_20 = d20_roll == 20
    is_nat_1 = d20_roll == 1
    
    # Nat 20 always hits, Nat 1 always misses
    if is_nat_20:
        hit = True
    elif is_nat_1:
        hit = False
    else:
        hit = total >= target_ac
    
    return {
        'weapon': weapon_name.title(),
        'd20_roll': d20_roll,
        'attack_bonus': attack_bonus,
        'total': total,
        'target_ac': target_ac,
        'hit': hit,
        'is_crit': is_nat_20,
        'is_fumble': is_nat_1,
    }


def roll_attack_with_advantage(character: Character, target_ac: int, weapon_name: str = 'longsword') -> dict:
    """
    Roll an attack with ADVANTAGE (roll 2d20, take higher).
    Used when player has surprised enemies or other advantageous conditions.
    Returns dict with roll details and hit/miss, plus both rolls shown.
    """
    weapon = WEAPONS.get(weapon_name.lower(), WEAPONS['longsword'])
    attack_bonus = calculate_attack_bonus(character, weapon_name)
    
    # Roll 2d20, take higher
    roll1 = random.randint(1, 20)
    roll2 = random.randint(1, 20)
    d20_roll = max(roll1, roll2)
    total = d20_roll + attack_bonus
    
    is_nat_20 = d20_roll == 20
    is_nat_1 = d20_roll == 1 and roll1 == 1 and roll2 == 1  # Both must be 1 for fumble with advantage
    
    # Nat 20 always hits, Nat 1 always misses
    if is_nat_20:
        hit = True
    elif is_nat_1:
        hit = False
    else:
        hit = total >= target_ac
    
    return {
        'weapon': weapon_name.title(),
        'd20_roll': d20_roll,
        'd20_roll_1': roll1,
        'd20_roll_2': roll2,
        'has_advantage': True,
        'attack_bonus': attack_bonus,
        'total': total,
        'target_ac': target_ac,
        'hit': hit,
        'is_crit': is_nat_20,
        'is_fumble': is_nat_1,
    }


def roll_attack_with_disadvantage(character: Character, target_ac: int, weapon_name: str = 'longsword') -> dict:
    """
    Roll an attack with DISADVANTAGE (roll 2d20, take lower).
    Used when player is in darkness without light or other hindering conditions.
    Returns dict with roll details and hit/miss, plus both rolls shown.
    """
    weapon = WEAPONS.get(weapon_name.lower(), WEAPONS['longsword'])
    attack_bonus = calculate_attack_bonus(character, weapon_name)
    
    # Roll 2d20, take lower
    roll1 = random.randint(1, 20)
    roll2 = random.randint(1, 20)
    d20_roll = min(roll1, roll2)
    total = d20_roll + attack_bonus
    
    is_nat_20 = d20_roll == 20 and roll1 == 20 and roll2 == 20  # Both must be 20 for crit with disadvantage
    is_nat_1 = d20_roll == 1
    
    # Nat 20 always hits, Nat 1 always misses
    if is_nat_20:
        hit = True
    elif is_nat_1:
        hit = False
    else:
        hit = total >= target_ac
    
    return {
        'weapon': weapon_name.title(),
        'd20_roll': d20_roll,
        'd20_roll_1': roll1,
        'd20_roll_2': roll2,
        'has_disadvantage': True,
        'attack_bonus': attack_bonus,
        'total': total,
        'target_ac': target_ac,
        'hit': hit,
        'is_crit': is_nat_20,
        'is_fumble': is_nat_1,
    }


def roll_damage(character: Character, weapon_name: str = 'longsword', is_crit: bool = False) -> dict:
    """
    Roll damage for a weapon hit.
    Critical hits roll damage dice twice.
    Poison adds +1d4 damage and is consumed after use.
    """
    weapon = WEAPONS.get(weapon_name.lower(), WEAPONS['longsword'])
    damage_dice = weapon['damage']
    damage_type = weapon['type']
    damage_bonus = calculate_damage_bonus(character, weapon_name)
    
    # Roll damage
    total, rolls = roll_dice(damage_dice)
    
    # Critical: roll again
    crit_rolls = []
    if is_crit:
        crit_total, crit_rolls = roll_dice(damage_dice)
        total += crit_total
    
    # Phase 3.6.6: Poison damage bonus (+1d4)
    poison_rolls = []
    poison_damage = 0
    weapon_was_poisoned = False
    if hasattr(character, 'weapon_poisoned') and character.weapon_poisoned:
        poison_damage, poison_rolls = roll_dice('1d4')
        total += poison_damage
        character.weapon_poisoned = False  # Consume after one hit
        weapon_was_poisoned = True
    
    # Add modifier
    final_damage = max(1, total + damage_bonus)  # Minimum 1 damage
    
    result = {
        'weapon': weapon_name.title(),
        'damage_dice': damage_dice,
        'damage_type': damage_type,
        'rolls': rolls,
        'crit_rolls': crit_rolls,
        'damage_bonus': damage_bonus,
        'total': final_damage,
        'is_crit': is_crit,
    }
    
    # Add poison info if applicable
    if weapon_was_poisoned:
        result['poison_rolls'] = poison_rolls
        result['poison_damage'] = poison_damage
        result['was_poisoned'] = True
    
    return result


def format_attack_result(attack: dict) -> str:
    """Format attack roll for display."""
    bonus_sign = '+' if attack['attack_bonus'] >= 0 else ''
    
    # Format roll display (with advantage/disadvantage shows both rolls)
    if attack.get('has_advantage'):
        roll_display = f"[{attack['d20_roll_1']}, {attack['d20_roll_2']}→{attack['d20_roll']}]"
        adv_label = "⬆️ ADV "
    elif attack.get('has_disadvantage'):
        roll_display = f"[{attack['d20_roll_1']}, {attack['d20_roll_2']}→{attack['d20_roll']}]"
        adv_label = "⬇️ DIS "
    else:
        roll_display = f"[{attack['d20_roll']}]"
        adv_label = ""
    
    if attack['is_crit']:
        return (
            f"🗡️ {adv_label}Attack ({attack['weapon']}): "
            f"{roll_display}{bonus_sign}{attack['attack_bonus']} = {attack['total']} "
            f"vs AC {attack['target_ac']} = ⚡ CRITICAL HIT!"
        )
    elif attack['is_fumble']:
        return (
            f"🗡️ {adv_label}Attack ({attack['weapon']}): "
            f"{roll_display}{bonus_sign}{attack['attack_bonus']} = {attack['total']} "
            f"vs AC {attack['target_ac']} = 💥 CRITICAL MISS!"
        )
    elif attack['hit']:
        return (
            f"🗡️ {adv_label}Attack ({attack['weapon']}): "
            f"{roll_display}{bonus_sign}{attack['attack_bonus']} = {attack['total']} "
            f"vs AC {attack['target_ac']} = ✅ HIT!"
        )
    else:
        return (
            f"🗡️ {adv_label}Attack ({attack['weapon']}): "
            f"{roll_display}{bonus_sign}{attack['attack_bonus']} = {attack['total']} "
            f"vs AC {attack['target_ac']} = ❌ MISS"
        )


def format_damage_result(damage: dict) -> str:
    """Format damage roll for display."""
    bonus_sign = '+' if damage['damage_bonus'] >= 0 else ''
    
    # Check for poison damage
    poison_text = ""
    if damage.get('was_poisoned'):
        poison_text = f" + 🧪{damage['poison_rolls']} poison"
    
    if damage['is_crit']:
        all_rolls = damage['rolls'] + damage['crit_rolls']
        return (
            f"💥 Damage: {all_rolls}{bonus_sign}{damage['damage_bonus']}{poison_text} = "
            f"{damage['total']} {damage['damage_type']} damage (CRITICAL!)"
        )
    else:
        return (
            f"💥 Damage: {damage['rolls']}{bonus_sign}{damage['damage_bonus']}{poison_text} = "
            f"{damage['total']} {damage['damage_type']} damage"
        )


# =============================================================================
# ENEMY ATTACK
# =============================================================================

def enemy_attack(enemy: Enemy, target_ac: int) -> Tuple[dict, Optional[dict]]:
    """
    Enemy attacks the player.
    Returns (attack_result, damage_result or None).
    """
    d20_roll = random.randint(1, 20)
    total = d20_roll + enemy.attack_bonus
    
    is_nat_20 = d20_roll == 20
    is_nat_1 = d20_roll == 1
    
    if is_nat_20:
        hit = True
    elif is_nat_1:
        hit = False
    else:
        hit = total >= target_ac
    
    attack_result = {
        'attacker': enemy.name,
        'd20_roll': d20_roll,
        'attack_bonus': enemy.attack_bonus,
        'total': total,
        'target_ac': target_ac,
        'hit': hit,
        'is_crit': is_nat_20,
        'is_fumble': is_nat_1,
    }
    
    damage_result = None
    if hit:
        damage_total, rolls = roll_dice(enemy.damage_dice)
        if is_nat_20:
            crit_total, _ = roll_dice(enemy.damage_dice)
            damage_total += crit_total
        
        damage_result = {
            'attacker': enemy.name,
            'total': max(1, damage_total + enemy.damage_bonus),
            'is_crit': is_nat_20,
        }
    
    return attack_result, damage_result


def format_enemy_attack(attack: dict, damage: Optional[dict]) -> str:
    """Format enemy attack for display."""
    bonus_sign = '+' if attack['attack_bonus'] >= 0 else ''
    
    line1 = (
        f"👹 {attack['attacker']} attacks: "
        f"[{attack['d20_roll']}]{bonus_sign}{attack['attack_bonus']} = {attack['total']} "
        f"vs your AC {attack['target_ac']}"
    )
    
    if attack['is_crit']:
        line1 += " = ⚡ CRITICAL HIT!"
    elif attack['is_fumble']:
        line1 += " = 💥 FUMBLE! (Miss)"
        return line1
    elif attack['hit']:
        line1 += " = ✅ HIT!"
    else:
        line1 += " = ❌ MISS"
        return line1
    
    if damage:
        crit_note = " (CRITICAL!)" if damage['is_crit'] else ""
        line1 += f"\n   You take {damage['total']} damage{crit_note}!"
    
    return line1


# =============================================================================
# PARTY MEMBER COMBAT (Phase 3.5 P7 Step 6)
# =============================================================================

def party_member_attack(member, target, has_flanking: bool = False) -> Tuple[dict, Optional[dict]]:
    """
    Party member attacks an enemy.
    
    Args:
        member: PartyMember object
        target: Enemy object
        has_flanking: True if 2+ allies attacking same target (advantage)
        
    Returns (attack_result, damage_result or None).
    """
    attack_bonus = getattr(member, 'attack_bonus', 4)
    damage_dice = getattr(member, 'damage_dice', '1d8+2')
    
    # Roll attack (with advantage if flanking)
    if has_flanking:
        roll1 = random.randint(1, 20)
        roll2 = random.randint(1, 20)
        d20_roll = max(roll1, roll2)
    else:
        d20_roll = random.randint(1, 20)
        roll1, roll2 = d20_roll, None
    
    total = d20_roll + attack_bonus
    
    is_nat_20 = d20_roll == 20
    is_nat_1 = d20_roll == 1
    
    if is_nat_20:
        hit = True
    elif is_nat_1:
        hit = False
    else:
        hit = total >= target.armor_class
    
    attack_result = {
        'attacker': member.name,
        'd20_roll': d20_roll,
        'd20_roll_1': roll1,
        'd20_roll_2': roll2,
        'has_flanking': has_flanking,
        'attack_bonus': attack_bonus,
        'total': total,
        'target_ac': target.armor_class,
        'target_name': target.name,
        'hit': hit,
        'is_crit': is_nat_20,
        'is_fumble': is_nat_1,
    }
    
    damage_result = None
    if hit:
        damage_total, rolls = roll_dice(damage_dice)
        if is_nat_20:
            crit_total, _ = roll_dice(damage_dice)
            damage_total += crit_total
        
        damage_result = {
            'attacker': member.name,
            'total': max(1, damage_total),  # Damage bonus already in damage_dice
            'rolls': rolls,
            'is_crit': is_nat_20,
        }
    
    return attack_result, damage_result


def format_party_member_attack(attack: dict, damage: Optional[dict], member_class: str = "Fighter") -> str:
    """Format party member attack for display."""
    # Sanitize user-controlled strings to prevent XSS
    attacker_name = html.escape(str(attack.get('attacker', 'Unknown')))
    target_name = html.escape(str(attack.get('target_name', 'Enemy')))
    
    # Class emoji mapping
    class_emoji = {
        "Fighter": "🛡️",
        "Ranger": "🏹",
        "Rogue": "🗡️",
        "Cleric": "✝️",
        "Wizard": "🔮",
    }
    emoji = class_emoji.get(member_class, "⚔️")
    bonus_sign = '+' if attack['attack_bonus'] >= 0 else ''
    
    # Format roll display
    if attack.get('has_flanking') and attack.get('d20_roll_2'):
        roll_display = f"[{attack['d20_roll_1']}, {attack['d20_roll_2']}→{attack['d20_roll']}]"
        flank_label = "⚔️ FLANKING "
    else:
        roll_display = f"[{attack['d20_roll']}]"
        flank_label = ""
    
    line1 = (
        f"{emoji} {attacker_name} {flank_label}attacks {target_name}: "
        f"{roll_display}{bonus_sign}{attack['attack_bonus']} = {attack['total']} "
        f"vs AC {attack['target_ac']}"
    )
    
    if attack['is_crit']:
        line1 += " → ⚡ CRITICAL HIT!"
    elif attack['is_fumble']:
        line1 += " → 💥 MISS!"
        return line1
    elif attack['hit']:
        line1 += " → ✅ HIT!"
    else:
        line1 += " → ❌ MISS"
        return line1
    
    if damage:
        crit_note = " (CRITICAL!)" if damage['is_crit'] else ""
        line1 += f" {damage['total']} damage{crit_note}!"
    
    return line1


def check_flanking(attackers_on_target: int) -> bool:
    """
    Check if flanking bonus applies (simplified D&D 5e flanking).
    In this simplified version, 2+ allies attacking same target = flanking.
    
    Args:
        attackers_on_target: Number of party members (including player) targeting this enemy
        
    Returns True if flanking bonus applies.
    """
    return attackers_on_target >= 2


def get_party_member_action(member, enemies: list, allies_hp: dict) -> dict:
    """
    AI decision for what a party member does on their turn.
    
    Args:
        member: PartyMember object
        enemies: List of living Enemy objects
        allies_hp: Dict mapping ally name -> (current_hp, max_hp)
        
    Returns dict with: action_type, target, use_ability
    """
    char_class = getattr(member, 'char_class', None)
    class_name = char_class.value if hasattr(char_class, 'value') else str(char_class)
    
    # Check if should use ability
    can_use_ability = getattr(member, 'can_use_ability', lambda: False)()
    
    # Cleric: Heal if any ally below 50% HP
    if class_name == "Cleric" and can_use_ability:
        for ally_name, (current, maximum) in allies_hp.items():
            if current / maximum < 0.5:
                return {
                    'action_type': 'ability',
                    'target': ally_name,
                    'use_ability': True,
                    'ability_name': 'Healing Word'
                }
    
    # Fighter: Use Shield Wall if any ally below 30% HP
    if class_name == "Fighter" and can_use_ability:
        for ally_name, (current, maximum) in allies_hp.items():
            if current / maximum < 0.3:
                return {
                    'action_type': 'ability',
                    'target': None,
                    'use_ability': True,
                    'ability_name': 'Shield Wall'
                }
    
    # Default: Attack lowest HP enemy
    if enemies:
        target = min(enemies, key=lambda e: e.current_hp)
        return {
            'action_type': 'attack',
            'target': target,
            'use_ability': False,
            'ability_name': None
        }
    
    return {'action_type': 'wait', 'target': None, 'use_ability': False}


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("=== Combat System Test ===\n")
    
    # Create a test character
    from character import Character
    hero = Character(
        name="Test Hero",
        race="Human",
        char_class="Fighter",
        strength=16,
        dexterity=14,
        constitution=14,
        intelligence=10,
        wisdom=12,
        charisma=8
    )
    
    print(f"Hero: {hero.name} (STR +{hero.get_ability_modifier('strength')}, DEX +{hero.get_ability_modifier('dexterity')})")
    print(f"HP: {hero.current_hp}/{hero.max_hp}, AC: {hero.armor_class}")
    
    # Create enemy
    goblin = create_enemy('goblin')
    print(f"\nEnemy: {goblin.get_status()}")
    
    # Test attack
    print("\n--- Hero attacks Goblin ---")
    attack = roll_attack(hero, goblin.armor_class, 'longsword')
    print(format_attack_result(attack))
    
    if attack['hit']:
        damage = roll_damage(hero, 'longsword', attack['is_crit'])
        print(format_damage_result(damage))
        status = goblin.take_damage(damage['total'])
        print(status)
    
    print(f"\n{goblin.get_status()}")
    
    # Test enemy attack
    print("\n--- Goblin attacks Hero ---")
    enemy_atk, enemy_dmg = enemy_attack(goblin, hero.armor_class)
    print(format_enemy_attack(enemy_atk, enemy_dmg))
    
    if enemy_dmg:
        hero.current_hp -= enemy_dmg['total']
        print(f"Hero HP: {hero.current_hp}/{hero.max_hp}")
