# Flutter Setup Guide

## AI D&D Text RPG - Flutter Development Environment

This guide walks you through setting up Flutter for developing the cross-platform app.

---

## Prerequisites

- Windows 10/11 (64-bit)
- 10GB+ free disk space
- VS Code (already installed ✅)

---

## Installation Steps

### Step 1: Install Flutter SDK

1. **Download Flutter SDK**
   - Go to: https://docs.flutter.dev/get-started/install/windows
   - Download the latest stable release zip file

2. **Extract to installation folder**
   ```
   Recommended: C:\flutter
   ```
   ⚠️ Do NOT install in `C:\Program Files` (permission issues)

3. **Add to PATH**
   - Open System Properties → Environment Variables
   - Under "User variables", find `Path`
   - Add: `C:\flutter\bin`

4. **Verify installation**
   ```powershell
   flutter --version
   ```

---

### Step 2: Install Android Studio

1. **Download Android Studio**
   - Go to: https://developer.android.com/studio
   - Download and run installer

2. **During installation, select:**
   - ✅ Android SDK
   - ✅ Android SDK Platform
   - ✅ Android Virtual Device (AVD)

3. **After installation, open Android Studio:**
   - Complete the setup wizard
   - Install recommended SDK components

4. **Accept licenses**
   ```powershell
   flutter doctor --android-licenses
   ```
   Type `y` to accept each license

---

### Step 3: Install VS Code Extensions

1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X)
3. Install:
   - **Flutter** (by Dart Code)
   - **Dart** (by Dart Code)

---

### Step 4: Create Android Emulator

1. Open Android Studio
2. Go to: Tools → Device Manager
3. Click "Create Device"
4. Select: Pixel 6 (or similar)
5. Select: Latest Android version (API 34+)
6. Complete setup

---

### Step 5: Verify Setup

Run Flutter Doctor:

```powershell
flutter doctor -v
```

You should see:
```
[✓] Flutter (Channel stable, 3.x.x)
[✓] Windows Version (Windows 10/11)
[✓] Android toolchain - develop for Android devices
[✓] Chrome - develop for the web
[✓] Visual Studio - develop Windows apps (optional)
[✓] Android Studio
[✓] VS Code
[✓] Connected device (Chrome, emulator)
```

---

## Quick Commands Reference

| Command | Description |
|---------|-------------|
| `flutter doctor` | Check installation status |
| `flutter create app_name` | Create new project |
| `flutter run` | Run app on connected device |
| `flutter run -d chrome` | Run in Chrome browser |
| `flutter run -d windows` | Run as Windows app |
| `flutter build apk` | Build Android APK |
| `flutter build web` | Build for web |
| `flutter pub get` | Install dependencies |

---

## Project Structure (After Creation)

```
ai_dnd_rpg_app/
├── android/          # Android-specific files
├── ios/              # iOS-specific files
├── web/              # Web-specific files
├── windows/          # Windows-specific files
├── linux/            # Linux-specific files
├── macos/            # macOS-specific files
├── lib/              # Main Dart code
│   └── main.dart     # App entry point
├── test/             # Test files
└── pubspec.yaml      # Dependencies & config
```

---

## Troubleshooting

### "Flutter not recognized"
- Ensure `C:\flutter\bin` is in PATH
- Restart terminal/VS Code

### "Android licenses not accepted"
```powershell
flutter doctor --android-licenses
```

### "No devices found"
- Start Android emulator from Android Studio
- Or use Chrome: `flutter run -d chrome`

### "Android SDK not found"
- Open Android Studio → Settings → Languages & Frameworks → Android SDK
- Note the SDK Location
- Set environment variable: `ANDROID_HOME=<SDK Location>`

---

## Next Steps

After setup is complete:

1. Create Flutter project for the RPG app
2. Set up project structure
3. Implement chat UI
4. Connect to backend API

See [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) for Phase 6 details.

---

## Resources

- [Flutter Documentation](https://docs.flutter.dev/)
- [Dart Language Tour](https://dart.dev/language)
- [Flutter Widget Catalog](https://docs.flutter.dev/ui/widgets)
- [Pub.dev (Package Repository)](https://pub.dev/)
