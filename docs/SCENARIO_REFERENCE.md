# 🗺️ GOBLIN CAVE SCENARIO - COMPLETE REFERENCE
============================================================

This document contains all locations, NPCs, items, and connections
in the Goblin Cave scenario for quick reference.

## 📖 SCENARIO OVERVIEW

**Name:** The Goblin Menace  
**Hook:** A farmer's daughter (Lily) has been kidnapped by goblins. Rescue her from Darkhollow Cave.  
**Start Location:** The Rusty Dragon Tavern (tavern_main)  
**Regions:** Village → Forest → Cave

### Key Objectives:
1. 🎯 Accept quest from Bram in the tavern
2. 🤝 (Optional) Recruit party members: Marcus (tavern), Elira (forest), Shade (cave)
3. 🗡️ Navigate to Darkhollow Cave through the forest
4. 🔓 Find and rescue Lily from the goblin cages
5. ⚔️ Defeat or negotiate with Chief Grotnak

### Recruitable NPCs Summary:
| NPC | Location | Recruitment Condition | Class |
|-----|----------|----------------------|-------|
| Marcus | tavern_main | Pay 25 gold | Fighter |
| Elira | forest_clearing | CHA DC 12 | Ranger |
| Shade | goblin_camp_shadows | CHA DC 14 | Rogue |


============================================================
## 📍 LOCATIONS BY REGION
============================================================

### 🏷️ VILLAGE
----------------------------------------

**Blacksmith's Forge** (`blacksmith_shop`)
  📝 A warm, smoky forge with an anvil at the center. Weapons and armor hang on the walls, and the heat f...
  🚪 Exits: outside → village_square, square → village_square
  👤 NPCs: gavin

**The Rusty Dragon - Bar** (`tavern_bar`)
  📝 A worn wooden bar with a gruff but friendly barkeep polishing mugs. Bottles line the shelves behind.
  🚪 Exits: main room → tavern_main
  👤 NPCs: barkeep

**The Rusty Dragon - Celebration** (`tavern_celebration`)
  📝 The tavern is packed! Drinks flow freely and the villagers toast your heroism.
  👤 NPCs: bram, barkeep, villagers

**The Rusty Dragon - Main Room** (`tavern_main`)
  📝 A cozy common room with a crackling hearth. Wooden tables are scattered about, some occupied by loca...
  🚪 Exits: bar → tavern_bar, outside → village_square
  👤 NPCs: bram, marcus, locals
  📦 Items: torch

**Village - Hero's Return** (`village_return`)
  📝 The village square, but now filled with people. Word has spread of your success!
  🚪 Exits: tavern → tavern_celebration
  👤 NPCs: bram, villagers

**Village Square** (`village_square`)
  📝 A small village square with a well at the center. Most shops are closed for the evening, but warm li...
  🚪 Exits: tavern → tavern_main, east road → forest_path, forge → blacksmith_shop

### 🏷️ FOREST
----------------------------------------

**Darkhollow Cave Entrance** (`cave_entrance`)
  📝 A gaping maw in the rocky hillside. Goblin totems flank the entrance, and bones litter the ground.
  🚪 Exits: forest → darkhollow_approach, enter cave → cave_tunnel, inside → cave_tunnel
  📦 Items: torch

**Cave Exit** (`cave_exit`)
  📝 Daylight streams through the cave entrance. Fresh air replaces the goblin stench.
  🚪 Exits: outside → return_path
  👤 NPCs: lily

**Approach to Darkhollow** (`darkhollow_approach`)
  📝 The forest grows darker and more twisted. Goblin signs become visible - crude markers, bones hanging...
  🚪 Exits: back → forest_clearing, cave → cave_entrance
  📦 Items: goblin_ear

**Forest Clearing** (`forest_clearing`)
  📝 A small clearing where the path forks. An old signpost points east toward 'Darkhollow'.
  🚪 Exits: back → forest_path, east → darkhollow_approach, cave → darkhollow_approach, hidden path → secret_cave
  👤 NPCs: elira
  📦 Items: rations

**Forest Path** (`forest_path`)
  📝 A winding dirt path through an ancient forest. Autumn leaves crunch underfoot.
  🚪 Exits: village → village_square, deeper → forest_clearing, east → forest_clearing

**Return Journey** (`return_path`)
  📝 The forest path back to the village. The journey feels lighter now.
  🚪 Exits: village → village_return
  👤 NPCs: lily

**Hidden Hollow** (`secret_cave`)
  📝 A small natural cave hidden behind overgrown vines. It's cool and quiet inside, clearly undisturbed ...
  🚪 Exits: out → forest_clearing, exit → forest_clearing
  📦 Items: ancient_amulet, healing_potion, gold_coins
  🔒 Hidden: Requires skill:perception:14

### 🏷️ CAVE
----------------------------------------

**Chief Grotnak's Throne Room** (`boss_chamber`)
  📝 A large chamber dominated by a throne of bones. Chief Grotnak sits counting coins, flanked by two go...
  🚪 Exits: escape → chief_tunnel, hidden alcove → treasure_nook
  👤 NPCs: grotnak, bodyguards
  📦 Items: healing_potion, gold_pouch, longsword
  ⚔️ Encounter: goblin_boss, goblin

**Dark Tunnel** (`cave_tunnel`)
  📝 A narrow passage descending into darkness. The walls are slick with moisture. Distant goblin chatter...
  🚪 Exits: outside → cave_entrance, deeper → goblin_camp_entrance, forward → goblin_camp_entrance

**Passage to Chief's Lair** (`chief_tunnel`)
  📝 A passage leading to the back of the cave. It's more decorated - skulls on spikes, crude paintings. ...
  🚪 Exits: camp → goblin_camp_main, lair → boss_chamber
  📦 Items: antidote

**Goblin Warren - Prisoner Cages** (`goblin_camp_cages`)
  📝 Crude iron cages along the wall. A young girl (Lily) cowers in one, her eyes wide with fear and hope...
  🚪 Exits: camp → goblin_camp_main
  👤 NPCs: lily
  📦 Items: lockpicks

**Goblin Warren - Entrance** (`goblin_camp_entrance`)
  📝 The tunnel opens into a larger cavern. Firelight flickers ahead, and you can see goblin shadows movi...
  🚪 Exits: tunnel → cave_tunnel, camp → goblin_camp_main, sneak left → goblin_camp_shadows

**Goblin Warren - Main Camp** (`goblin_camp_main`)
  📝 A large cavern lit by smoky torches. Four goblins lounge around a central fire. Cages line the far w...
  🚪 Exits: back → goblin_camp_entrance, cages → goblin_camp_cages, chief → chief_tunnel, storage → goblin_storage
  👤 NPCs: goblins
  📦 Items: shortsword, rations, healing_potion, gold_pouch_small
  ⚔️ Encounter: goblin, goblin, goblin, goblin

**Goblin Warren - Shadows** (`goblin_camp_shadows`)
  📝 A dark alcove along the cavern wall. From here you can observe the camp without being seen. Somethin...
  🚪 Exits: camp → goblin_camp_main, cages → goblin_camp_cages, chief → chief_tunnel
  👤 NPCs: shade
  📦 Items: poison_vial, dagger, storage_key

**Goblin Warren - Storage Room** (`goblin_storage`)
  📝 A cramped storage room full of stolen goods. Barrels of food, crates of weapons, and a locked chest ...
  🚪 Exits: camp → goblin_camp_main
  📦 Items: healing_potion, healing_potion, gold_pouch, shortsword, leather_armor, silver_locket, family_ring

**Chief's Secret Stash** (`treasure_nook`)
  📝 A cramped alcove hidden behind a false panel in the wall. The chief's personal treasure hoard!
  🚪 Exits: out → boss_chamber, back → boss_chamber
  📦 Items: enchanted_dagger, ruby_ring, gold_pile, rare_scroll
  🔒 Hidden: Requires skill:investigation:12


============================================================
## 👥 ALL NPCs (DETAILED)
============================================================

### 🏠 VILLAGE NPCs

#### **Bram** (Quest Giver) - `tavern_main`
A panicked farmer whose daughter Lily was kidnapped by goblins.
- **Role:** QUEST_GIVER
- **Disposition:** 20 (Friendly - desperate for help)
- **Offers Quest:** "Rescue Lily" - 50 gold reward
- **Key Dialogue:**
  - "My daughter Lily was taken by goblins! Please help!"
  - "The goblins came from Darkhollow Cave to the east..."

#### **Greth the Barkeep** (Info) - `tavern_bar`
The gruff but knowledgeable tavern keeper of The Rusty Dragon.
- **Role:** INFO
- **Disposition:** 0 (Neutral)
- **Key Dialogue:**
  - "Those goblins have been getting bolder lately..."
  - "Darkhollow Cave? Bad place. Old stories say it goes deep..."
  - "Word is the goblins have a new chief. Bigger, smarter..."

#### **Gavin the Blacksmith** (Merchant) - `blacksmith_shop`
A burly man in his fifties with a soot-stained leather apron. Sells weapons and armor.
- **Role:** MERCHANT
- **Disposition:** 10 (Neutral-friendly, business-like)
- **Shop:** Gavin's Forge (1.15x markup)
- **Personality:**
  - Gruff, honest, proud of his craft
  - Deep gravelly voice, rhythmic like hammer strikes
  - Secretly served as a soldier decades ago
- **Key Dialogue:**
  - "*wipes hands on apron* Welcome to me forge! Looking for steel?"
  - "Good armor's like good ale - worth every coin."
  - "Help rescue Lily, and I'll give you a discount."

**🛒 GAVIN'S FORGE - SHOP INVENTORY:**

| Item | Base Price | Stock | Description |
|------|-----------|-------|-------------|
| **WEAPONS** |
| Dagger | 2g | ∞ | 1d4 damage, finesse |
| Club | 1g | ∞ | 1d4 damage |
| Shortsword | 10g | 3 | 1d6 damage, finesse |
| Longsword | 15g | 2 | 1d8 damage |
| Handaxe | 5g | 3 | 1d6 damage, thrown |
| **ARMOR** |
| Leather Armor | 10g | 2 | +1 AC |
| Chain Shirt | 50g | 1 | +3 AC |
| Shield | 10g | 3 | +2 AC |

> **Note:** Prices shown are base values. Gavin applies 1.15x markup, so actual prices are slightly higher.

#### **Marcus** (Recruitable) - `tavern_main`
A weathered mercenary looking for work.
- **Role:** RECRUITABLE
- **Class:** Fighter
- **Recruitment:** Pay 25 gold
- **Stats:** +2 STR, +1 CON
- **Abilities:** Heavy Strike, Shield Block
- **Key Dialogue:**
  - "Looking for muscle? I'm between jobs. Name's Marcus."
  - "Twenty-five gold and we have a deal."

---

### 🌲 FOREST NPCs

#### **Elira** (Recruitable) - `forest_clearing`
An elven ranger seeking vengeance for her brother's death.
- **Role:** RECRUITABLE
- **Class:** Ranger
- **Recruitment:** Charisma DC 12 skill check
- **Stats:** +2 DEX, +1 WIS
- **Abilities:** Precise Shot, Hunter's Mark
- **Key Dialogue:**
  - "You're heading to Darkhollow? So am I. Those goblins killed my brother."
  - "There's about a dozen in the main cave. But I've seen signs of more..."

---

### ⛏️ CAVE NPCs

#### **Shade** (Recruitable) - `goblin_camp_shadows`
A mysterious rogue hiding in the cave shadows.
- **Role:** RECRUITABLE
- **Class:** Rogue
- **Recruitment:** Charisma DC 14 skill check
- **Stats:** +2 DEX, +1 INT
- **Abilities:** Sneak Attack, Lockpicking
- **Key Dialogue:**
  - "You're not a goblin. Interesting."
  - "I can get you past the guards... for a price."

#### **Lily** (Objective) - `goblin_camp_cages` → `cave_exit`
Bram's kidnapped daughter, held prisoner by goblins.
- **Role:** INFO (rescued becomes ally)
- **Key Dialogue:**
  - "Please, get me out of here!"
  - "The key... the big goblin has it..."

#### **Chief Grotnak** (Boss) - `boss_chamber`
The goblin chieftain who orchestrated the kidnapping.
- **Role:** ENEMY (negotiable)
- **Combat:** goblin_boss + 2 goblin bodyguards
- **Alternative:** Can be negotiated with or intimidated


============================================================
## 📦 ITEMS BY LOCATION
============================================================
  `boss_chamber`: healing_potion, gold_pouch, longsword
  `cave_entrance`: torch
  `chief_tunnel`: antidote
  `darkhollow_approach`: goblin_ear
  `forest_clearing`: rations
  `goblin_camp_cages`: lockpicks
  `goblin_camp_main`: shortsword, rations, healing_potion, gold_pouch_small
  `goblin_camp_shadows`: poison_vial, dagger, storage_key
  `goblin_storage`: healing_potion, healing_potion, gold_pouch, shortsword, leather_armor, silver_locket, family_ring
  `secret_cave`: ancient_amulet, healing_potion, gold_coins
  `tavern_main`: torch
  `treasure_nook`: enchanted_dagger, ruby_ring, gold_pile, rare_scroll


============================================================
## 📜 QUESTS
============================================================
  From **Bram**: rescue_lily


============================================================
## 🎯 XP REWARDS (System-Controlled)
============================================================

**XP is automatically awarded by the system, NOT the AI DM.**

### Scene Objective XP (Fixed)

| Scene | Objective | XP |
|-------|-----------|-----|
| Tavern | meet_bram | 10 |
| Tavern | accept_quest | 15 |
| Journey | examine_entrance | 15 |
| Cave | deal_with_goblins | 25 |
| Cave | find_lily | 50 |
| Boss | defeat_chief | 50 |

### Combat XP (Fixed per enemy)

| Enemy | XP |
|-------|-----|
| Goblin | 25 |
| Goblin Boss | 100 |
| Wolf | 25 |

### Quest Completion XP

| Quest | XP | Gold |
|-------|-----|------|
| Rescue Lily (MAIN) | 100 | 50g |
| Recover Heirlooms | 50 | 25g |
| Clear the Path | 75 | 30g |
| Chief's Treasure | 50 | - |

### AI Discretionary XP (Rare - Exceptional Only)

The AI only awards 25 XP for **truly exceptional** roleplay:

**✅ AWARD XP FOR:**
1. **Creative Puzzle Solving** - Thinking outside the box
   - Using environment unexpectedly (rope + oil = trap)
   - Connecting clues from earlier conversations
2. **Brilliant Negotiation** - Exceptional diplomacy
   - Convincing hostile enemies to switch sides
   - Finding non-obvious win-win solutions
3. **Unexpected Ingenuity** - Surprising clever actions
   - Combining items creatively (mirror + sunlight = weapon)
   - Using environment in unexpected ways

**❌ NEVER AWARD XP FOR:**
- Accepting/completing quests (system handles it)
- Entering locations or meeting NPCs
- Combat victories
- Using items as intended
- Normal dialogue or investigation

============================================================
## ⚔️ COMBAT ENCOUNTERS
============================================================

| Location | Enemies | Difficulty |
|----------|---------|------------|
| `forest_path` | 1 wolf (random 20% chance) | Easy |
| `goblin_camp_main` | 4 goblins | Medium |
| `boss_chamber` | 1 goblin_boss + 2 goblins | Hard |


============================================================
## 🔒 HIDDEN LOCATIONS
============================================================

| Location | Discovery Requirement | Notable Loot |
|----------|----------------------|--------------|
| `secret_cave` | Perception DC 14 (from forest_clearing) | ancient_amulet, healing_potion, gold |
| `treasure_nook` | Investigation DC 12 (from boss_chamber) | enchanted_dagger, ruby_ring, gold_pile, rare_scroll |


============================================================
## 🗺️ MAP CONNECTIONS (Text)
============================================================

```
╔══════════════════════════════════════════════════════════════╗
║                       VILLAGE REGION                          ║
╠══════════════════════════════════════════════════════════════╣
║                                                               ║
║        [tavern_bar] ←──┐                                      ║
║        🍻 Greth        │                                      ║
║                        │                                      ║
║   [blacksmith] ←── [village_square] ←── [tavern_main]        ║
║   ⚒️ Gavin                │                 🍺 Bram, Marcus    ║
║                           │                                   ║
╠═══════════════════════════│═══════════════════════════════════╣
║                      FOREST REGION                            ║
╠═══════════════════════════│═══════════════════════════════════╣
║                           │                                   ║
║                      [forest_path]                            ║
║                      🐺 Random Wolf                           ║
║                           │                                   ║
║   [secret_cave] ←── [forest_clearing]                        ║
║   🔮 Hidden Loot    🌳 Elira (Ranger)                         ║
║                           │                                   ║
║                   [darkhollow_approach]                       ║
║                                                               ║
╠═══════════════════════════│═══════════════════════════════════╣
║                       CAVE REGION                             ║
╠═══════════════════════════│═══════════════════════════════════╣
║                           │                                   ║
║                    [cave_entrance]                            ║
║                           │                                   ║
║                     [cave_tunnel]                             ║
║                           │                                   ║
║               [goblin_camp_entrance]                          ║
║                    /      │      \                            ║
║                   /       │       \                           ║
║    [shadows] ←── [main_camp] ──→ [cages]                     ║
║    👤 Shade      ⚔️ 4 Goblins     🔒 Lily                     ║
║                       │                                       ║
║                  [storage]                                    ║
║                  📦 Loot                                      ║
║                       │                                       ║
║               [chief_tunnel]                                  ║
║                       │                                       ║
║                [boss_chamber]                                 ║
║                ⚔️ Chief Grotnak                               ║
║                       │                                       ║
║               [treasure_nook]                                 ║
║               🔮 Hidden Treasure                              ║
║                                                               ║
╚══════════════════════════════════════════════════════════════╝
```

---
**Legend:**
- 🍺 Tavern  | 🍻 Bar  | ⚒️ Shop  | 🌳 Forest
- 🐺 Random Encounter  | ⚔️ Combat  | 🔒 Objective
- 👤 NPC  | 📦 Loot  | 🔮 Hidden/Secret

---
*Document auto-generated from scenario.py*
