# UI/UX Design Specification

## By Lamplight — AI Text RPG - Frontend Design Document

---

## Table of Contents

1. [Design Philosophy](#design-philosophy)
2. [Theme System](#theme-system)
3. [Screen Layouts](#screen-layouts)
4. [Component Library](#component-library)
5. [Navigation](#navigation)
6. [World Map Panel](#world-map-panel) ← **NEW**
7. [Animations](#animations)

---

## Design Philosophy

### Core Principles
- **Immersive** - Transport players into a fantasy world
- **Accessible** - Easy to use on any device
- **Customizable** - Multiple themes for personalization
- **Responsive** - Works on mobile, tablet, web, and desktop

### Visual Style
- Fantasy-inspired with modern usability
- Clear typography for readability
- Consistent iconography
- Smooth transitions and animations

---

## Theme System

### Available Themes

| Theme ID | Name | Primary | Background | Accent | Text |
|----------|------|---------|------------|--------|------|
| `dark_fantasy` | Dark Fantasy | `#D4AF37` (Gold) | `#1A1A1A` | `#8B4513` | `#F5F5DC` |
| `light_parchment` | Light Parchment | `#8B4513` (Brown) | `#F5F5DC` | `#D4AF37` | `#2C1810` |
| `forest_green` | Forest Green | `#228B22` (Forest) | `#1C2E1C` | `#90EE90` | `#E8F5E9` |
| `dungeon_stone` | Dungeon Stone | `#708090` (Slate) | `#2F2F2F` | `#FF6347` | `#D3D3D3` |
| `royal_purple` | Royal Purple | `#9932CC` (Orchid) | `#1A1A2E` | `#C0C0C0` | `#E6E6FA` |
| `blood_crimson` | Blood Crimson | `#DC143C` (Crimson) | `#1A0A0A` | `#B22222` | `#FFF5F5` |
| `system` | System Default | Auto | Auto | Auto | Auto |

### Theme Structure

```dart
class AppTheme {
  final String id;
  final String name;
  final Color primary;
  final Color background;
  final Color surface;
  final Color accent;
  final Color textPrimary;
  final Color textSecondary;
  final Color dmBubble;
  final Color playerBubble;
  final Color error;
  final Brightness brightness;
}
```

### Color Specifications

#### Dark Fantasy (Default)
```
Primary:        #D4AF37  (Gold)
Background:     #1A1A1A  (Near Black)
Surface:        #2D2D2D  (Dark Gray)
Accent:         #8B4513  (Saddle Brown)
Text Primary:   #F5F5DC  (Beige)
Text Secondary: #A0A0A0  (Gray)
DM Bubble:      #2D2D2D  (Dark surface)
Player Bubble:  #3D3D1A  (Olive tint)
Error:          #DC143C  (Crimson)
```

#### Light Parchment
```
Primary:        #8B4513  (Saddle Brown)
Background:     #F5F5DC  (Beige)
Surface:        #FAEBD7  (Antique White)
Accent:         #D4AF37  (Gold)
Text Primary:   #2C1810  (Dark Brown)
Text Secondary: #5C4033  (Medium Brown)
DM Bubble:      #FAEBD7  (Antique White)
Player Bubble:  #E6D5AC  (Wheat)
Error:          #B22222  (Firebrick)
```

### Theme Persistence

```dart
// Save theme preference
SharedPreferences.setString('theme_id', 'dark_fantasy');

// Load theme on startup
String themeId = SharedPreferences.getString('theme_id') ?? 'dark_fantasy';
```

### Theme Change Animation

- Duration: 300ms
- Curve: easeInOut
- Smooth color transition across all components

---

## Screen Layouts

### 1. Chat/Adventure Screen (Main)

```
┌─────────────────────────────────────────────────────┐
│  ⚔️ The Misty Forest                     ⚙️  📜  🎲 │ ← App Bar
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌─────────────────────────────────────────┐        │
│  │ 🎲 Game Master                       │        │
│  │                                          │        │
│  │ You stand at the edge of the ancient    │        │ ← DM Message
│  │ Misty Forest. The air is thick with     │        │
│  │ moisture and the scent of pine...       │        │
│  └─────────────────────────────────────────┘        │
│                                                     │
│              ┌──────────────────────────────────┐   │
│              │ I draw my sword and enter the   │   │ ← Player Message
│              │ forest cautiously               │   │
│              └──────────────────────────────────┘   │
│                                                     │
│  ┌─────────────────────────────────────────┐        │
│  │ 🎲 Game Master                       │        │
│  │                                          │        │
│  │ As you step into the forest, the        │        │
│  │ canopy closes above you. Roll a         │        │
│  │ perception check (d20 + WIS modifier)   │        │
│  └─────────────────────────────────────────┘        │
│                                                     │
├─────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────┐  ┌────┐ │
│  │ What do you do?                       │  │ ➤  │ │ ← Input Field
│  └───────────────────────────────────────┘  └────┘ │
├─────────────────────────────────────────────────────┤
│   💬        👤        🎒        ⚙️                  │ ← Bottom Nav
│  Chat    Character  Inventory  Settings             │
└─────────────────────────────────────────────────────┘
```

### 2. Character Sheet Screen

```
┌─────────────────────────────────────────────────────┐
│  ← Back    Character Sheet                    ✏️    │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │  ┌─────┐                                      │  │
│  │  │     │  ELARA                               │  │
│  │  │ 👤  │  Level 3 Wood Elf Ranger             │  │
│  │  │     │  HP: 28/28  ❤️❤️❤️❤️                │  │
│  │  └─────┘  AC: 15  |  Speed: 35ft              │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  ┌─────────────────────────────────────────────────┐│
│  │ ABILITIES                                       ││
│  │ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐││
│  │ │ STR │ │ DEX │ │ CON │ │ INT │ │ WIS │ │ CHA │││
│  │ │ 14  │ │ 18  │ │ 14  │ │ 10  │ │ 16  │ │ 12  │││
│  │ │ +2  │ │ +4  │ │ +2  │ │ +0  │ │ +3  │ │ +1  │││
│  │ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘││
│  └─────────────────────────────────────────────────┘│
│                                                     │
│  ┌─────────────────────────────────────────────────┐│
│  │ SKILLS & PROFICIENCIES                    [▼]  ││
│  └─────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────┐│
│  │ FEATURES & TRAITS                         [▼]  ││
│  └─────────────────────────────────────────────────┘│
│                                                     │
├─────────────────────────────────────────────────────┤
│   💬        👤        🎒        ⚙️                  │
└─────────────────────────────────────────────────────┘
```

### 3. Inventory Screen

```
┌─────────────────────────────────────────────────────┐
│  ← Back    Inventory                    🔍  Filter  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Gold: 47 gp                                        │
│                                                     │
│  ── EQUIPPED ────────────────────────────────────   │
│  ┌────────────────────────────────────────────────┐ │
│  │ 🗡️ Longbow +1          │ 🛡️ Studded Leather   │ │
│  │ Weapon (main)          │ Armor (body)          │ │
│  └────────────────────────────────────────────────┘ │
│                                                     │
│  ── BACKPACK ────────────────────────────────────   │
│  ┌────────────────────────────────────────────────┐ │
│  │ 🧪 Potion of Healing (x3)                      │ │
│  │ 📜 Oakhaven Token                              │ │
│  │ 🪢 Rope, hempen (50 ft)                        │ │
│  │ 🔥 Tinderbox                                   │ │
│  │ 🍞 Rations (3 days)                            │ │
│  │ 💧 Waterskin                                   │ │
│  │ 🏹 Arrows (20)                                 │ │
│  └────────────────────────────────────────────────┘ │
│                                                     │
├─────────────────────────────────────────────────────┤
│   💬        👤        🎒        ⚙️                  │
└─────────────────────────────────────────────────────┘
```

### 4. Settings Screen

```
┌─────────────────────────────────────────────────────┐
│  ← Back    Settings                                 │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ── APPEARANCE ──────────────────────────────────   │
│                                                     │
│  Theme                                              │
│  ┌─────────────────────────────────────────────────┐│
│  │ ┌─────────┐ ┌─────────┐ ┌─────────┐            ││
│  │ │  🌑     │ │  📜     │ │  🌲     │            ││
│  │ │  Dark   │ │ Light   │ │ Forest  │            ││
│  │ │ Fantasy │ │Parchment│ │ Green   │            ││
│  │ │   ✓     │ │         │ │         │            ││
│  │ └─────────┘ └─────────┘ └─────────┘            ││
│  │                                                 ││
│  │ ┌─────────┐ ┌─────────┐ ┌─────────┐            ││
│  │ │  🏰     │ │  👑     │ │  🩸     │            ││
│  │ │ Dungeon │ │ Royal   │ │ Blood   │            ││
│  │ │ Stone   │ │ Purple  │ │ Crimson │            ││
│  │ └─────────┘ └─────────┘ └─────────┘            ││
│  │                                                 ││
│  │ ☐ Follow system theme                          ││
│  └─────────────────────────────────────────────────┘│
│                                                     │
│  ── GAME ────────────────────────────────────────   │
│                                                     │
│  [ Save Game ]                                      │
│  [ Load Game ]                                      │
│  [ New Character ]                                  │
│                                                     │
│  ── API ─────────────────────────────────────────   │
│                                                     │
│  API Key: ************ [Edit]                       │
│  Model: gemini-2.0-flash ▼                          │
│                                                     │
├─────────────────────────────────────────────────────┤
│   💬        👤        🎒        ⚙️                  │
└─────────────────────────────────────────────────────┘
```

### 5. Dice Roller (Modal/Overlay)

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│              ┌─────────────────────┐                │
│              │                     │                │
│              │     🎲              │                │
│              │                     │                │
│              │    [ 17 ]           │                │
│              │                     │                │
│              │   d20 + 3 = 20      │                │
│              │                     │                │
│              └─────────────────────┘                │
│                                                     │
│          [ d4 ] [ d6 ] [ d8 ]                       │
│          [ d10 ] [ d12 ] [ d20 ]                    │
│                                                     │
│          Modifier: [ +3 ]                           │
│                                                     │
│              [ ROLL ]                               │
│                                                     │
│              [ Close ]                              │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Component Library

### Chat Bubbles

```dart
// DM Message Bubble
Container(
  margin: EdgeInsets.only(right: 60),
  padding: EdgeInsets.all(12),
  decoration: BoxDecoration(
    color: theme.dmBubble,
    borderRadius: BorderRadius.only(
      topLeft: Radius.circular(4),
      topRight: Radius.circular(16),
      bottomLeft: Radius.circular(16),
      bottomRight: Radius.circular(16),
    ),
    border: Border.all(color: theme.accent, width: 1),
  ),
)

// Player Message Bubble
Container(
  margin: EdgeInsets.only(left: 60),
  padding: EdgeInsets.all(12),
  decoration: BoxDecoration(
    color: theme.playerBubble,
    borderRadius: BorderRadius.only(
      topLeft: Radius.circular(16),
      topRight: Radius.circular(4),
      bottomLeft: Radius.circular(16),
      bottomRight: Radius.circular(16),
    ),
  ),
)
```

### Stat Boxes

```dart
Container(
  width: 60,
  padding: EdgeInsets.all(8),
  decoration: BoxDecoration(
    color: theme.surface,
    border: Border.all(color: theme.primary, width: 2),
    borderRadius: BorderRadius.circular(8),
  ),
  child: Column(
    children: [
      Text('STR', style: TextStyle(fontSize: 10)),
      Text('14', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
      Text('+2', style: TextStyle(fontSize: 14, color: theme.accent)),
    ],
  ),
)
```

### Action Buttons

```dart
ElevatedButton(
  style: ElevatedButton.styleFrom(
    backgroundColor: theme.primary,
    foregroundColor: theme.background,
    padding: EdgeInsets.symmetric(horizontal: 24, vertical: 12),
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(8),
    ),
  ),
  onPressed: onPressed,
  child: Text('ROLL'),
)
```

---

## Navigation

### Bottom Navigation Bar

| Tab | Icon | Screen | Description |
|-----|------|--------|-------------|
| Chat | 💬 | ChatScreen | Main gameplay |
| Character | 👤 | CharacterScreen | Stats and abilities |
| Inventory | 🎒 | InventoryScreen | Items and equipment |
| Settings | ⚙️ | SettingsScreen | Theme, saves, API |

### App Bar Actions

| Icon | Action |
|------|--------|
| 🎲 | Open dice roller overlay |
| 📜 | View adventure log/history |
| 🗺️ | Toggle world map panel |
| ⚙️ | Quick settings |

---

## World Map Panel

### Overview

The Interactive World Map is a visual navigation panel that displays locations as clickable nodes on a stylized map. It replaces tedious "go" commands with intuitive one-click travel.

### Layout Options

**Side Panel (Desktop/Tablet):**
```
┌──────────────────────────────┬────────────────────┐
│                              │  🗺️ WORLD MAP      │
│  💬 Chat/Adventure           │  ┌──────────────┐  │
│                              │  │   [Forest]   │  │
│  DM: You stand at the        │  │      ⚠️↑     │  │
│  village square...           │  │              │  │
│                              │  │[Shop]←[●]→[Inn]│  │
│  > What do you do?           │  │  ✓   YOU  ✓  │  │
│                              │  │      ↓       │  │
│                              │  │   [Temple]   │  │
│  [________________] [Send]   │  └──────────────┘  │
└──────────────────────────────┴────────────────────┘
```

**Overlay (Mobile):**
```
┌─────────────────────────────────────────┐
│  ⚔️ Village Square          🗺️  ⚙️  🎲 │ ← Tap 🗺️ to open
├─────────────────────────────────────────┤
│                                         │
│        ┌─────────────────────────┐      │
│        │      🗺️ WORLD MAP       │      │
│        │                         │      │
│        │     [🌲 Forest ⚠️]       │      │
│        │          ↑              │      │
│        │  [🛠️]←──[●]──→[🍺]       │      │
│        │  Shop   YOU   Tavern    │      │
│        │          ↓              │      │
│        │     [⛪ Temple]         │      │
│        │                         │      │
│        │  [✕ Close]              │      │
│        └─────────────────────────┘      │
│                                         │
└─────────────────────────────────────────┘
```

### Map Node Styling

| State | Background | Border | Opacity | Effect |
|-------|------------|--------|---------|--------|
| Current | Theme primary | 3px gold | 100% | Pulsing glow |
| Visited | Theme surface | 1px gray | 100% | None |
| Visible (unvisited) | Gray 600 | 1px dark | 70% | None |
| Hidden (fog of war) | Black | None | 30% | Blur |
| Accessible (clickable) | Normal | Normal | 100% | Hover highlight |
| Locked | Normal | Dashed red | 80% | 🔒 overlay |

### Danger Level Colors

| Level | Node Color | Icon | Description |
|-------|------------|------|-------------|
| Safe | Green #228B22 | ✓ | No enemies expected |
| Uneasy | Yellow #DAA520 | ❓ | Something feels off |
| Threatening | Orange #FF8C00 | ⚠️ | Known enemy presence |
| Deadly | Red #DC143C | ☠️ | Boss or lethal area |

### Connection Lines

```css
/* Normal connection */
.connection {
  stroke: rgba(255, 255, 255, 0.3);
  stroke-width: 2px;
}

/* Locked connection */
.connection-locked {
  stroke: rgba(255, 100, 100, 0.5);
  stroke-width: 2px;
  stroke-dasharray: 5, 5;
}

/* Highlighted (hover path) */
.connection-highlight {
  stroke: rgba(212, 175, 55, 0.8);
  stroke-width: 3px;
}
```

### Map Regions

Regions provide visual grouping with tinted backgrounds:

| Region | Background Tint | Border Color | Icon |
|--------|----------------|--------------|------|
| Village | #4A7C59 (green) | #2D5A3D | 🏘️ |
| Forest | #2D5A3D (dark green) | #1A3D1A | 🌲 |
| Cave | #3D3D3D (gray) | #2A2A2A | ⛰️ |
| Dungeon | #4A3D5A (purple) | #3D2A4A | 🏰 |

### Gestures

| Gesture | Action |
|---------|--------|
| Tap node | Travel to location (if adjacent) |
| Long press node | Show location details tooltip |
| Pinch | Zoom in/out (0.5x to 3x) |
| Drag | Pan map |
| Double tap | Center on current location |

### Tooltip Content

When hovering/long-pressing a map node:

```
┌─────────────────────────────────┐
│ 🛠️ The Rusty Anvil             │
│ ──────────────────────────────  │
│ Gavin's blacksmith shop.        │
│                                 │
│ ✓ Visited  |  🛒 Shop  |  Safe  │
│                                 │
│ [TAP TO TRAVEL]                 │
└─────────────────────────────────┘
```

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| M | Toggle map panel |
| Escape | Close map panel |
| Arrow keys | Pan map |
| +/- | Zoom in/out |
| Home | Center on player |
| 1-9 | Quick travel to adjacent node |

### State Persistence

Map state is saved with game state:
- `visited_locations`: Set of location IDs
- `discovered_secrets`: Hidden areas revealed
- `unlocked_exits`: Doors opened with keys
- `current_location`: Player position

---

## Animations

### Theme Transition
- Type: Color interpolation
- Duration: 300ms
- Curve: easeInOut

### Dice Roll
- Type: 3D rotation + bounce
- Duration: 800ms
- Sound: Optional dice sound effect

### Message Appear
- Type: Slide in + fade
- Duration: 200ms
- Direction: From bottom

### Page Transition
- Type: Shared axis (horizontal)
- Duration: 300ms

---

## Typography

### Font Stack
1. **Primary**: 'Cinzel' - Fantasy headings
2. **Secondary**: 'Roboto' - Body text
3. **Monospace**: 'Fira Code' - Dice results, stats

### Font Sizes
| Element | Size | Weight |
|---------|------|--------|
| App Title | 24sp | Bold |
| Section Header | 18sp | SemiBold |
| Body Text | 16sp | Regular |
| Caption | 12sp | Regular |
| Stat Number | 24sp | Bold |
| Stat Label | 10sp | Regular |

---

## Responsive Breakpoints

| Device | Width | Layout |
|--------|-------|--------|
| Mobile | < 600px | Single column, bottom nav |
| Tablet | 600-1024px | Two column, side nav optional |
| Desktop | > 1024px | Three column, persistent sidebars |

---
