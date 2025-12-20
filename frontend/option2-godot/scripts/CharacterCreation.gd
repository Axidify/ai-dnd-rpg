extends Control

## Character Creation Screen
## Handles name input, class/race selection, and character creation

@onready var name_input: LineEdit = $VBoxContainer/NameSection/NameInput
@onready var class_container: GridContainer = $VBoxContainer/ClassSection/ClassGrid
@onready var race_container: HBoxContainer = $VBoxContainer/RaceSection/RaceButtons
@onready var start_button: Button = $VBoxContainer/StartButton
@onready var error_label: Label = $VBoxContainer/ErrorLabel
@onready var loading_panel: Panel = $LoadingPanel

const CLASSES = [
	{"name": "Fighter", "icon": "⚔️", "desc": "Master of martial combat", "color": Color("#e53935")},
	{"name": "Wizard", "icon": "🧙", "desc": "Wielder of arcane magic", "color": Color("#8e24aa")},
	{"name": "Rogue", "icon": "🗡️", "desc": "Stealthy and cunning", "color": Color("#43a047")},
	{"name": "Cleric", "icon": "✝️", "desc": "Divine healer and warrior", "color": Color("#ffd700")},
	{"name": "Ranger", "icon": "🏹", "desc": "Skilled hunter and tracker", "color": Color("#1e88e5")},
	{"name": "Barbarian", "icon": "🪓", "desc": "Fierce primal warrior", "color": Color("#ff5722")},
]

const RACES = ["Human", "Elf", "Dwarf", "Halfling", "Half-Orc", "Tiefling"]

var selected_class: String = ""
var selected_race: String = "Human"
var class_buttons: Array[Button] = []
var race_buttons: Array[Button] = []


func _ready():
	# Connect API signals
	ApiClient.character_created.connect(_on_character_created)
	ApiClient.request_failed.connect(_on_request_failed)
	
	# Setup UI
	_setup_class_buttons()
	_setup_race_buttons()
	
	# Initial state
	error_label.hide()
	loading_panel.hide()
	
	# Entrance animation
	modulate.a = 0
	var tween = create_tween()
	tween.tween_property(self, "modulate:a", 1.0, 0.5).set_ease(Tween.EASE_OUT)


func _setup_class_buttons():
	"""Create class selection buttons"""
	for class_data in CLASSES:
		var button = Button.new()
		button.text = class_data.icon + "\n" + class_data.name
		button.custom_minimum_size = Vector2(100, 80)
		button.toggle_mode = true
		button.pressed.connect(_on_class_pressed.bind(class_data.name, button))
		
		class_container.add_child(button)
		class_buttons.append(button)


func _setup_race_buttons():
	"""Create race selection buttons"""
	for race_name in RACES:
		var button = Button.new()
		button.text = race_name
		button.toggle_mode = true
		button.button_pressed = race_name == selected_race
		button.pressed.connect(_on_race_pressed.bind(race_name, button))
		
		race_container.add_child(button)
		race_buttons.append(button)


func _on_class_pressed(class_name: String, button: Button):
	selected_class = class_name
	
	# Update button states
	for btn in class_buttons:
		btn.button_pressed = btn == button
	
	# Animate selection
	var tween = create_tween()
	tween.tween_property(button, "scale", Vector2(1.1, 1.1), 0.1)
	tween.tween_property(button, "scale", Vector2.ONE, 0.1)


func _on_race_pressed(race_name: String, button: Button):
	selected_race = race_name
	
	# Update button states
	for btn in race_buttons:
		btn.button_pressed = btn == button


func _on_start_button_pressed():
	"""Handle start button click"""
	var char_name = name_input.text.strip_edges()
	
	# Validation
	if char_name.is_empty():
		_show_error("Please enter a name for your hero!")
		return
	
	if selected_class.is_empty():
		_show_error("Please choose a class!")
		return
	
	# Show loading
	error_label.hide()
	loading_panel.show()
	start_button.disabled = true
	
	# Create character
	ApiClient.create_character(char_name, selected_class, selected_race)


func _on_character_created(data: Dictionary):
	"""Handle successful character creation"""
	# Update game state
	GameState.set_initial_state(data)
	
	# Animate out
	var tween = create_tween()
	tween.tween_property(self, "modulate:a", 0.0, 0.3)
	await tween.finished
	
	# Change scene
	get_tree().change_scene_to_file("res://scenes/GameScreen.tscn")


func _on_request_failed(error: String):
	"""Handle API error"""
	loading_panel.hide()
	start_button.disabled = false
	_show_error(error)


func _show_error(message: String):
	"""Display error message with animation"""
	error_label.text = message
	error_label.show()
	
	# Shake animation
	var original_pos = error_label.position
	var tween = create_tween()
	for i in range(3):
		tween.tween_property(error_label, "position:x", original_pos.x + 10, 0.05)
		tween.tween_property(error_label, "position:x", original_pos.x - 10, 0.05)
	tween.tween_property(error_label, "position:x", original_pos.x, 0.05)
