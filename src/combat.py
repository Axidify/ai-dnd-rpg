"""
Combat System for AI D&D Text RPG
Handles attack rolls, damage, and combat encounters.
"""

import random
from dataclasses import dataclass, field
from typing import Optional, Tuple
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
    current_hp: int = field(init=False)
    is_dead: bool = False
    initiative: int = 0
    
    def __post_init__(self):
        self.current_hp = self.max_hp
    
    def take_damage(self, damage: int) -> str:
        """Apply damage to enemy. Returns status message."""
        self.current_hp = max(0, self.current_hp - damage)
        if self.current_hp == 0:
            self.is_dead = True
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

ENEMIES = {
    'goblin': Enemy(
        name="Goblin",
        max_hp=7,
        armor_class=15,
        attack_bonus=4,
        damage_dice="1d6",
        damage_bonus=2,
        dex_modifier=2
    ),
    'goblin_boss': Enemy(
        name="Goblin Boss",
        max_hp=21,
        armor_class=17,
        attack_bonus=5,
        damage_dice="1d8",
        damage_bonus=3,
        dex_modifier=2
    ),
    'skeleton': Enemy(
        name="Skeleton",
        max_hp=13,
        armor_class=13,
        attack_bonus=4,
        damage_dice="1d6",
        damage_bonus=2,
        dex_modifier=2
    ),
    'orc': Enemy(
        name="Orc",
        max_hp=15,
        armor_class=13,
        attack_bonus=5,
        damage_dice="1d12",
        damage_bonus=3,
        dex_modifier=1
    ),
    'bandit': Enemy(
        name="Bandit",
        max_hp=11,
        armor_class=12,
        attack_bonus=3,
        damage_dice="1d6",
        damage_bonus=1,
        dex_modifier=1
    ),
    'wolf': Enemy(
        name="Wolf",
        max_hp=11,
        armor_class=13,
        attack_bonus=4,
        damage_dice="2d4",
        damage_bonus=2,
        dex_modifier=2
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
            dex_modifier=template.dex_modifier
        )
    return None


# =============================================================================
# INITIATIVE SYSTEM
# =============================================================================

@dataclass
class Combatant:
    """Wrapper for any combat participant."""
    name: str
    initiative: int
    is_player: bool
    entity: any  # Character or Enemy


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
                         enemies: list[Enemy]) -> list[Combatant]:
    """
    Roll initiative for all combatants and determine turn order.
    Returns sorted list of Combatants (highest initiative first).
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
    
    # Enemy initiatives
    for enemy in enemies:
        enemy_init = roll_initiative(enemy.dex_modifier)
        enemy.initiative = enemy_init['total']
        combatants.append(Combatant(
            name=enemy.name,
            initiative=enemy_init['total'],
            is_player=False,
            entity=enemy
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


def roll_damage(character: Character, weapon_name: str = 'longsword', is_crit: bool = False) -> dict:
    """
    Roll damage for a weapon hit.
    Critical hits roll damage dice twice.
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
    
    # Add modifier
    final_damage = max(1, total + damage_bonus)  # Minimum 1 damage
    
    return {
        'weapon': weapon_name.title(),
        'damage_dice': damage_dice,
        'damage_type': damage_type,
        'rolls': rolls,
        'crit_rolls': crit_rolls,
        'damage_bonus': damage_bonus,
        'total': final_damage,
        'is_crit': is_crit,
    }


def format_attack_result(attack: dict) -> str:
    """Format attack roll for display."""
    bonus_sign = '+' if attack['attack_bonus'] >= 0 else ''
    
    # Format roll display (with advantage shows both rolls)
    if attack.get('has_advantage'):
        roll_display = f"[{attack['d20_roll_1']}, {attack['d20_roll_2']}→{attack['d20_roll']}]"
        adv_label = "⬆️ ADV "
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
    
    if damage['is_crit']:
        all_rolls = damage['rolls'] + damage['crit_rolls']
        return (
            f"💥 Damage: {all_rolls}{bonus_sign}{damage['damage_bonus']} = "
            f"{damage['total']} {damage['damage_type']} damage (CRITICAL!)"
        )
    else:
        return (
            f"💥 Damage: {damage['rolls']}{bonus_sign}{damage['damage_bonus']} = "
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
