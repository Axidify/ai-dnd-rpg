# Option 2: Godot Game Engine

A full game engine approach for maximum graphics, animation, and cross-platform support.

## Why Godot?

✅ **True Game Engine** - Built for games, not adapted from web tech
✅ **2D/3D Graphics** - Powerful rendering with shaders, particles, animations
✅ **All Platforms** - Windows, Mac, Linux, Web, iOS, Android from one codebase
✅ **Visual Editor** - Scene editor, animation tools, particle systems
✅ **Lightweight** - ~40MB download, fast compile times
✅ **GDScript** - Python-like scripting, easy to learn
✅ **Open Source** - MIT license, no royalties

## Tech Stack

- **Godot 4.2** - Game engine
- **GDScript** - Primary scripting language
- **HTTPRequest** - Built-in node for API calls
- **Tween/AnimationPlayer** - Smooth animations
- **Export Templates** - Build for any platform

## Project Structure

```
option2-godot/
├── project.godot          # Godot project file
├── export_presets.cfg     # Export configurations
├── scenes/
│   ├── Main.tscn          # Entry point scene
│   ├── CharacterCreation.tscn
│   ├── GameScreen.tscn
│   └── components/
│       ├── DiceRoller.tscn
│       └── ChatPanel.tscn
├── scripts/
│   ├── Main.gd
│   ├── CharacterCreation.gd
│   ├── GameScreen.gd
│   ├── ApiClient.gd
│   └── GameState.gd
├── assets/
│   ├── fonts/
│   ├── sprites/
│   └── audio/
└── themes/
    └── rpg_theme.tres
```

## Sample Code

### ApiClient.gd (Autoload/Singleton)
```gdscript
extends Node

signal request_completed(response)
signal request_failed(error)

var base_url = "http://localhost:5000/api"
var session_id = ""

func create_character(name: String, char_class: String, race: String):
    var http = HTTPRequest.new()
    add_child(http)
    http.request_completed.connect(_on_create_completed.bind(http))
    
    var body = JSON.stringify({
        "character": {
            "name": name,
            "class": char_class,
            "race": race
        }
    })
    
    http.request(
        base_url + "/game/start",
        ["Content-Type: application/json"],
        HTTPClient.METHOD_POST,
        body
    )

func _on_create_completed(result, code, headers, body, http):
    http.queue_free()
    if result == HTTPRequest.RESULT_SUCCESS:
        var json = JSON.parse_string(body.get_string_from_utf8())
        session_id = json.session_id
        request_completed.emit(json)
    else:
        request_failed.emit("Connection failed")
```

### CharacterCreation.gd
```gdscript
extends Control

@onready var name_input = $VBox/NameInput
@onready var class_grid = $VBox/ClassGrid
@onready var start_button = $VBox/StartButton

var selected_class = ""
var selected_race = "Human"

func _ready():
    # Connect to ApiClient signals
    ApiClient.request_completed.connect(_on_character_created)
    ApiClient.request_failed.connect(_on_request_failed)
    
    # Animate entrance
    modulate.a = 0
    var tween = create_tween()
    tween.tween_property(self, "modulate:a", 1.0, 0.5)

func _on_class_selected(class_name: String):
    selected_class = class_name
    # Update UI to show selection
    for button in class_grid.get_children():
        button.button_pressed = button.name == class_name

func _on_start_pressed():
    if name_input.text.is_empty() or selected_class.is_empty():
        return
    
    start_button.disabled = true
    ApiClient.create_character(name_input.text, selected_class, selected_race)

func _on_character_created(response):
    # Animate out and switch scene
    var tween = create_tween()
    tween.tween_property(self, "modulate:a", 0.0, 0.3)
    await tween.finished
    get_tree().change_scene_to_file("res://scenes/GameScreen.tscn")

func _on_request_failed(error):
    start_button.disabled = false
    $ErrorLabel.text = error
```

## Getting Started

### Install Godot
1. Download Godot 4.2+ from https://godotengine.org
2. No installation needed - just run the executable

### Open Project
1. Launch Godot
2. Click "Import"
3. Navigate to `option2-godot/project.godot`
4. Click "Import & Edit"

### Run
- Press F5 or click the play button
- The game will connect to Flask backend at localhost:5000

### Export to Platforms
1. Download export templates: Editor → Export → Download Templates
2. Add export presets for each platform
3. Build with one click

## Platform Notes

| Platform | Build Process | Notes |
|----------|---------------|-------|
| Windows | Export → Windows Desktop | .exe + .pck |
| macOS | Export → macOS | .app bundle |
| Linux | Export → Linux | Binary + .pck |
| Web | Export → Web | HTML5, works anywhere |
| Android | Export → Android | Requires Android SDK |
| iOS | Export → iOS | Requires Mac + Xcode |

## Pros vs React

- **Better Performance**: Native rendering, not browser-based
- **Built-in Animation**: AnimationPlayer, Tweens, Particles
- **Visual Editing**: Design UI visually, not just code
- **Mobile Native**: Touch gestures, device features
- **Offline First**: Can work without constant API calls
- **Asset Pipeline**: Built-in image, audio, font handling

## Cons vs React

- **Learning Curve**: GDScript and Godot editor
- **Deployment**: Need to build for each platform
- **Web Size**: Larger download (~15-20MB for web export)
- **Ecosystem**: Fewer libraries than npm/React
