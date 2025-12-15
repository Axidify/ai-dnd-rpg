# Theme System Specification

## AI D&D Text RPG - DLC-Ready Theme Architecture

---

## Table of Contents

1. [Overview](#overview)
2. [Theme Data Structure](#theme-data-structure)
3. [Theme Registry](#theme-registry)
4. [Unlock System](#unlock-system)
5. [Theme Packs (DLC)](#theme-packs-dlc)
6. [Implementation Guide](#implementation-guide)
7. [Monetization Strategy](#monetization-strategy)

---

## Overview

The theme system is designed to:
- Ship with free default themes
- Support premium DLC theme packs
- Track unlocked themes per user
- Load themes dynamically
- Sync unlock status with backend (future)
- Support theme previews before purchase

---

## Theme Data Structure

### Theme Model

```dart
class GameTheme {
  // Identification
  final String id;              // Unique identifier: "dark_fantasy"
  final String name;            // Display name: "Dark Fantasy"
  final String description;     // Short description
  final String packId;          // Which pack it belongs to: "core" | "dlc_gothic" etc.
  
  // Unlock Status
  final ThemeTier tier;         // FREE | PREMIUM | EXCLUSIVE
  final bool isDefault;         // Is this a default unlocked theme?
  
  // Visual Assets
  final String? previewImage;   // Asset path for theme preview
  final String? iconEmoji;      // Emoji for quick identification
  
  // Colors
  final ThemeColors colors;
  
  // Typography (optional override)
  final ThemeTypography? typography;
  
  // Special Effects (optional)
  final ThemeEffects? effects;
}

enum ThemeTier {
  FREE,       // Available to all users
  PREMIUM,    // Requires purchase or subscription
  EXCLUSIVE,  // Limited edition, special events
}
```

### Theme Colors

```dart
class ThemeColors {
  // Core Colors
  final Color primary;          // Main brand color
  final Color primaryVariant;   // Darker/lighter variant
  final Color secondary;        // Accent color
  final Color secondaryVariant; // Accent variant
  
  // Backgrounds
  final Color background;       // Main background
  final Color surface;          // Cards, dialogs
  final Color surfaceVariant;   // Alternate surface
  
  // Text
  final Color onPrimary;        // Text on primary color
  final Color onSecondary;      // Text on secondary
  final Color onBackground;     // Text on background
  final Color onSurface;        // Text on surface
  final Color textSecondary;    // Muted text
  
  // Chat Specific
  final Color dmBubble;         // DM message background
  final Color dmBubbleBorder;   // DM message border
  final Color playerBubble;     // Player message background
  final Color playerBubbleBorder; // Player message border
  
  // Game Elements
  final Color healthBar;        // HP bar color
  final Color manaBar;          // MP/spell slots
  final Color goldText;         // Currency display
  final Color diceHighlight;    // Dice roll result
  
  // Status
  final Color success;          // Positive outcomes
  final Color warning;          // Caution
  final Color error;            // Negative outcomes, damage
  final Color info;             // Information
  
  // Brightness
  final Brightness brightness;  // LIGHT | DARK
}
```

### Theme Typography (Optional Override)

```dart
class ThemeTypography {
  final String? headingFont;    // Custom heading font
  final String? bodyFont;       // Custom body font
  final String? monoFont;       // Custom monospace font
  final double? baseFontSize;   // Scale factor
}
```

### Theme Effects (Optional)

```dart
class ThemeEffects {
  final bool hasParticles;      // Background particles
  final String? particleType;   // "dust" | "embers" | "snow" etc.
  final bool hasVignette;       // Dark edges effect
  final double? vignetteOpacity;
  final bool hasTexture;        // Background texture overlay
  final String? textureAsset;   // Path to texture image
}
```

---

## Theme Registry

### Central Theme Management

```dart
class ThemeRegistry {
  // All registered themes (including locked ones)
  final Map<String, GameTheme> _themes = {};
  
  // User's unlocked theme IDs
  Set<String> _unlockedThemeIds = {};
  
  // Currently active theme
  String _activeThemeId = 'dark_fantasy';
  
  // Register a theme
  void registerTheme(GameTheme theme) {
    _themes[theme.id] = theme;
  }
  
  // Register a theme pack
  void registerPack(ThemePack pack) {
    for (var theme in pack.themes) {
      registerTheme(theme);
    }
  }
  
  // Get available themes (respects unlock status)
  List<GameTheme> getAvailableThemes() {
    return _themes.values
        .where((t) => t.tier == ThemeTier.FREE || _unlockedThemeIds.contains(t.id))
        .toList();
  }
  
  // Get all themes (for store display)
  List<GameTheme> getAllThemes() {
    return _themes.values.toList();
  }
  
  // Check if theme is unlocked
  bool isUnlocked(String themeId) {
    final theme = _themes[themeId];
    if (theme == null) return false;
    return theme.tier == ThemeTier.FREE || _unlockedThemeIds.contains(themeId);
  }
  
  // Unlock a theme (after purchase)
  void unlockTheme(String themeId) {
    _unlockedThemeIds.add(themeId);
    _persistUnlocks();
  }
  
  // Unlock entire pack
  void unlockPack(String packId) {
    _themes.values
        .where((t) => t.packId == packId)
        .forEach((t) => _unlockedThemeIds.add(t.id));
    _persistUnlocks();
  }
}
```

---

## Unlock System

### Local Persistence

```dart
// Save unlock status locally
Future<void> _persistUnlocks() async {
  final prefs = await SharedPreferences.getInstance();
  await prefs.setStringList('unlocked_themes', _unlockedThemeIds.toList());
}

// Load unlock status on startup
Future<void> loadUnlocks() async {
  final prefs = await SharedPreferences.getInstance();
  _unlockedThemeIds = prefs.getStringList('unlocked_themes')?.toSet() ?? {};
}
```

### Backend Sync (Future)

```dart
// Sync with backend for cross-device unlocks
Future<void> syncUnlocksWithBackend() async {
  // GET /api/user/unlocked-themes
  final response = await api.get('/user/unlocked-themes');
  final serverUnlocks = Set<String>.from(response.data);
  
  // Merge local and server
  _unlockedThemeIds.addAll(serverUnlocks);
  
  // Push local-only unlocks to server
  final localOnly = _unlockedThemeIds.difference(serverUnlocks);
  if (localOnly.isNotEmpty) {
    await api.post('/user/unlocked-themes', {'add': localOnly.toList()});
  }
  
  _persistUnlocks();
}
```

### Purchase Verification

```dart
// Verify purchase with store
Future<bool> verifyPurchase(String productId) async {
  // For Google Play / App Store
  final purchaseDetails = await InAppPurchase.instance.restorePurchases();
  return purchaseDetails.any((p) => p.productID == productId && p.status == PurchaseStatus.purchased);
}

// Complete purchase flow
Future<void> purchaseThemePack(String packId) async {
  // 1. Initiate purchase through store
  final product = await getProduct(packId);
  final result = await InAppPurchase.instance.buyNonConsumable(
    purchaseParam: PurchaseParam(productDetails: product),
  );
  
  // 2. Verify purchase
  if (await verifyPurchase(packId)) {
    // 3. Unlock locally
    unlockPack(packId);
    
    // 4. Sync with backend
    await api.post('/user/purchases', {'pack_id': packId});
  }
}
```

---

## Theme Packs (DLC)

### Pack Structure

```dart
class ThemePack {
  final String id;              // "dlc_gothic"
  final String name;            // "Gothic Horror Pack"
  final String description;     // Marketing description
  final String price;           // "$2.99" (display only)
  final String storeProductId;  // "com.app.theme.gothic"
  final String? previewImage;   // Pack artwork
  final List<GameTheme> themes; // Themes in this pack
  final DateTime? releaseDate;  // For upcoming packs
  final bool isAvailable;       // Can be purchased now?
}
```

### Planned Theme Packs

| Pack ID | Name | Themes | Tier | Price |
|---------|------|--------|------|-------|
| `core` | Core Themes | Dark Fantasy, Light Parchment | FREE | - |
| `dlc_nature` | Nature Pack | Forest Green, Ocean Blue, Desert Sand | PREMIUM | $1.99 |
| `dlc_dungeon` | Dungeon Pack | Dungeon Stone, Cavern Dark, Lava Glow | PREMIUM | $1.99 |
| `dlc_arcane` | Arcane Pack | Royal Purple, Mystic Blue, Void Black | PREMIUM | $1.99 |
| `dlc_gothic` | Gothic Horror | Blood Crimson, Midnight, Haunted | PREMIUM | $2.99 |
| `dlc_seasonal` | Seasonal | Winter Frost, Autumn Leaves, Spring Bloom | PREMIUM | $2.99 |
| `dlc_premium` | Premium Bundle | All themes | PREMIUM | $7.99 |

---

## Free Themes (Core Pack)

### 1. Dark Fantasy (Default)

```dart
GameTheme darkFantasy = GameTheme(
  id: 'dark_fantasy',
  name: 'Dark Fantasy',
  description: 'Classic dark theme with gold accents. Perfect for epic adventures.',
  packId: 'core',
  tier: ThemeTier.FREE,
  isDefault: true,
  iconEmoji: '🌑',
  colors: ThemeColors(
    // Core
    primary: Color(0xFFD4AF37),       // Gold
    primaryVariant: Color(0xFFB8860B), // Dark Gold
    secondary: Color(0xFF8B4513),      // Saddle Brown
    secondaryVariant: Color(0xFF654321),
    
    // Backgrounds
    background: Color(0xFF1A1A1A),     // Near Black
    surface: Color(0xFF2D2D2D),        // Dark Gray
    surfaceVariant: Color(0xFF3D3D3D),
    
    // Text
    onPrimary: Color(0xFF1A1A1A),
    onSecondary: Color(0xFFF5F5DC),
    onBackground: Color(0xFFF5F5DC),   // Beige
    onSurface: Color(0xFFF5F5DC),
    textSecondary: Color(0xFFA0A0A0),
    
    // Chat
    dmBubble: Color(0xFF2D2D2D),
    dmBubbleBorder: Color(0xFF8B4513),
    playerBubble: Color(0xFF3D3D1A),
    playerBubbleBorder: Color(0xFFD4AF37),
    
    // Game
    healthBar: Color(0xFFDC143C),      // Crimson
    manaBar: Color(0xFF4169E1),        // Royal Blue
    goldText: Color(0xFFD4AF37),
    diceHighlight: Color(0xFFFFD700),
    
    // Status
    success: Color(0xFF228B22),
    warning: Color(0xFFFF8C00),
    error: Color(0xFFDC143C),
    info: Color(0xFF4169E1),
    
    brightness: Brightness.dark,
  ),
);
```

### 2. Light Parchment

```dart
GameTheme lightParchment = GameTheme(
  id: 'light_parchment',
  name: 'Light Parchment',
  description: 'Aged paper aesthetic. Easy on the eyes for long sessions.',
  packId: 'core',
  tier: ThemeTier.FREE,
  isDefault: false,
  iconEmoji: '📜',
  colors: ThemeColors(
    // Core
    primary: Color(0xFF8B4513),       // Saddle Brown
    primaryVariant: Color(0xFF654321),
    secondary: Color(0xFFD4AF37),      // Gold
    secondaryVariant: Color(0xFFB8860B),
    
    // Backgrounds
    background: Color(0xFFF5F5DC),     // Beige
    surface: Color(0xFFFAEBD7),        // Antique White
    surfaceVariant: Color(0xFFFFEFD5),
    
    // Text
    onPrimary: Color(0xFFF5F5DC),
    onSecondary: Color(0xFF2C1810),
    onBackground: Color(0xFF2C1810),   // Dark Brown
    onSurface: Color(0xFF2C1810),
    textSecondary: Color(0xFF5C4033),
    
    // Chat
    dmBubble: Color(0xFFFAEBD7),
    dmBubbleBorder: Color(0xFF8B4513),
    playerBubble: Color(0xFFE6D5AC),
    playerBubbleBorder: Color(0xFFD4AF37),
    
    // Game
    healthBar: Color(0xFFB22222),
    manaBar: Color(0xFF4169E1),
    goldText: Color(0xFFB8860B),
    diceHighlight: Color(0xFFD4AF37),
    
    // Status
    success: Color(0xFF228B22),
    warning: Color(0xFFCC7000),
    error: Color(0xFFB22222),
    info: Color(0xFF4682B4),
    
    brightness: Brightness.light,
  ),
);
```

---

## Premium Themes (Examples)

### Forest Green (Nature Pack)

```dart
GameTheme forestGreen = GameTheme(
  id: 'forest_green',
  name: 'Forest Green',
  description: 'Deep woodland vibes. Ideal for rangers and druids.',
  packId: 'dlc_nature',
  tier: ThemeTier.PREMIUM,
  isDefault: false,
  iconEmoji: '🌲',
  colors: ThemeColors(
    primary: Color(0xFF228B22),       // Forest Green
    primaryVariant: Color(0xFF006400),
    secondary: Color(0xFF90EE90),      // Light Green
    secondaryVariant: Color(0xFF3CB371),
    
    background: Color(0xFF1C2E1C),
    surface: Color(0xFF2E4A2E),
    surfaceVariant: Color(0xFF3D5C3D),
    
    onPrimary: Color(0xFFFFFFFF),
    onSecondary: Color(0xFF1C2E1C),
    onBackground: Color(0xFFE8F5E9),
    onSurface: Color(0xFFE8F5E9),
    textSecondary: Color(0xFFA5D6A7),
    
    dmBubble: Color(0xFF2E4A2E),
    dmBubbleBorder: Color(0xFF228B22),
    playerBubble: Color(0xFF3D5C3D),
    playerBubbleBorder: Color(0xFF90EE90),
    
    healthBar: Color(0xFFDC143C),
    manaBar: Color(0xFF90EE90),
    goldText: Color(0xFFFFD700),
    diceHighlight: Color(0xFF90EE90),
    
    success: Color(0xFF90EE90),
    warning: Color(0xFFFFD700),
    error: Color(0xFFDC143C),
    info: Color(0xFF87CEEB),
    
    brightness: Brightness.dark,
  ),
);
```

### Blood Crimson (Gothic Horror Pack)

```dart
GameTheme bloodCrimson = GameTheme(
  id: 'blood_crimson',
  name: 'Blood Crimson',
  description: 'Dark and dangerous. For those who embrace the shadows.',
  packId: 'dlc_gothic',
  tier: ThemeTier.PREMIUM,
  isDefault: false,
  iconEmoji: '🩸',
  colors: ThemeColors(
    primary: Color(0xFFDC143C),       // Crimson
    primaryVariant: Color(0xFFB22222),
    secondary: Color(0xFFC0C0C0),      // Silver
    secondaryVariant: Color(0xFF808080),
    
    background: Color(0xFF1A0A0A),
    surface: Color(0xFF2D1515),
    surfaceVariant: Color(0xFF3D2020),
    
    onPrimary: Color(0xFFFFFFFF),
    onSecondary: Color(0xFF1A0A0A),
    onBackground: Color(0xFFFFF5F5),
    onSurface: Color(0xFFFFF5F5),
    textSecondary: Color(0xFFCD9999),
    
    dmBubble: Color(0xFF2D1515),
    dmBubbleBorder: Color(0xFFDC143C),
    playerBubble: Color(0xFF3D2020),
    playerBubbleBorder: Color(0xFFC0C0C0),
    
    healthBar: Color(0xFFDC143C),
    manaBar: Color(0xFF8B0000),
    goldText: Color(0xFFC0C0C0),
    diceHighlight: Color(0xFFDC143C),
    
    success: Color(0xFF228B22),
    warning: Color(0xFFFF4500),
    error: Color(0xFFFF0000),
    info: Color(0xFFC0C0C0),
    
    brightness: Brightness.dark,
  ),
  effects: ThemeEffects(
    hasVignette: true,
    vignetteOpacity: 0.3,
  ),
);
```

---

## Implementation Guide

### Folder Structure

```
lib/
├── themes/
│   ├── theme_model.dart         # GameTheme, ThemeColors classes
│   ├── theme_registry.dart      # ThemeRegistry singleton
│   ├── theme_provider.dart      # State management for current theme
│   │
│   ├── packs/
│   │   ├── core_pack.dart       # Free themes
│   │   ├── nature_pack.dart     # Nature DLC
│   │   ├── dungeon_pack.dart    # Dungeon DLC
│   │   ├── arcane_pack.dart     # Arcane DLC
│   │   └── gothic_pack.dart     # Gothic DLC
│   │
│   └── widgets/
│       ├── theme_selector.dart   # Theme picker UI
│       └── theme_preview.dart    # Preview card for store
│
├── store/
│   ├── store_screen.dart        # Theme store UI
│   ├── purchase_service.dart    # In-app purchase handling
│   └── purchase_verification.dart
```

### Initialization

```dart
// In main.dart
void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Register theme packs
  ThemeRegistry.instance
    ..registerPack(corePack)
    ..registerPack(naturePack)
    ..registerPack(dungeonPack)
    ..registerPack(arcanePack)
    ..registerPack(gothicPack);
  
  // Load user's unlocked themes
  await ThemeRegistry.instance.loadUnlocks();
  
  // Load saved theme preference
  final savedThemeId = await ThemeStorage.getActiveTheme();
  ThemeRegistry.instance.setActiveTheme(savedThemeId);
  
  runApp(MyApp());
}
```

### Theme Provider (State Management)

```dart
class ThemeProvider extends ChangeNotifier {
  GameTheme _currentTheme;
  
  ThemeProvider() : _currentTheme = ThemeRegistry.instance.getActiveTheme();
  
  GameTheme get currentTheme => _currentTheme;
  
  ThemeData get themeData => _buildThemeData(_currentTheme);
  
  void setTheme(String themeId) {
    if (!ThemeRegistry.instance.isUnlocked(themeId)) {
      throw ThemeNotUnlockedException(themeId);
    }
    
    _currentTheme = ThemeRegistry.instance.getTheme(themeId)!;
    ThemeStorage.saveActiveTheme(themeId);
    notifyListeners();
  }
  
  ThemeData _buildThemeData(GameTheme theme) {
    return ThemeData(
      brightness: theme.colors.brightness,
      primaryColor: theme.colors.primary,
      scaffoldBackgroundColor: theme.colors.background,
      // ... map all colors to Flutter ThemeData
    );
  }
}
```

---

## Monetization Strategy

### Pricing Tiers

| Tier | Price Range | Content |
|------|-------------|---------|
| FREE | $0 | 2 core themes |
| Small Pack | $0.99 - $1.99 | 3-4 themed colors |
| Large Pack | $2.99 - $3.99 | 4-5 themes + effects |
| Bundle | $7.99 - $9.99 | All current themes |
| Subscription | $2.99/mo | All themes + new releases |

### Store Product IDs

| Platform | Product ID Format |
|----------|-------------------|
| Google Play | `com.yourapp.theme.{pack_id}` |
| App Store | `com.yourapp.theme.{pack_id}` |
| Web (Stripe) | `price_{pack_id}` |

### A/B Testing Hooks

```dart
// For testing different pricing/packaging
class ThemeExperiment {
  static String getPriceForPack(String packId) {
    // Return price based on experiment group
    return RemoteConfig.getString('price_$packId');
  }
  
  static List<String> getPacksToShow() {
    // Control which packs appear in store
    return RemoteConfig.getStringList('visible_packs');
  }
}
```

---

## Future Considerations

1. **Theme Editor** - Let users create custom themes (premium feature)
2. **Theme Sharing** - Share custom themes with friends
3. **Seasonal Themes** - Auto-unlock during holidays
4. **Achievement Themes** - Unlock by completing game milestones
5. **Patron Exclusives** - Special themes for supporters

---
