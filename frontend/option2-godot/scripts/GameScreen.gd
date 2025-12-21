extends Control

## Main Game Screen
## Shows chat, character stats, and handles player input

@onready var chat_container: VBoxContainer = $HSplitContainer/ChatPanel/ScrollContainer/ChatContainer
@onready var scroll_container: ScrollContainer = $HSplitContainer/ChatPanel/ScrollContainer
@onready var input_field: LineEdit = $HSplitContainer/ChatPanel/InputContainer/InputField
@onready var send_button: Button = $HSplitContainer/ChatPanel/InputContainer/SendButton
@onready var quick_actions: HBoxContainer = $HSplitContainer/ChatPanel/QuickActions

@onready var character_panel: PanelContainer = $HSplitContainer/SidePanel/CharacterPanel
@onready var name_label: Label = $HSplitContainer/SidePanel/CharacterPanel/VBox/NameLabel
@onready var class_label: Label = $HSplitContainer/SidePanel/CharacterPanel/VBox/ClassLabel
@onready var hp_bar: ProgressBar = $HSplitContainer/SidePanel/CharacterPanel/VBox/HPBar
@onready var xp_bar: ProgressBar = $HSplitContainer/SidePanel/CharacterPanel/VBox/XPBar
@onready var gold_label: Label = $HSplitContainer/SidePanel/CharacterPanel/VBox/GoldLabel

@onready var dice_roller: Control = $HSplitContainer/SidePanel/DiceRoller
@onready var quit_button: Button = $HSplitContainer/SidePanel/QuitButton

const QUICK_ACTIONS = [
	{"label": "Look around", "action": "look around"},
	{"label": "Check inventory", "action": "check inventory"},
	{"label": "Rest", "action": "rest"},
]

var is_loading: bool = false


func _ready():
	# Connect signals
	ApiClient.action_completed.connect(_on_action_completed)
	ApiClient.request_failed.connect(_on_request_failed)
	GameState.message_added.connect(_on_message_added)
	GameState.character_updated.connect(_update_character_display)
	
	# Setup quick actions
	_setup_quick_actions()
	
	# Initial display
	_update_character_display(GameState.character)
	_load_existing_messages()
	
	# Entrance animation
	modulate.a = 0
	var tween = create_tween()
	tween.tween_property(self, "modulate:a", 1.0, 0.5)


func _setup_quick_actions():
	"""Create quick action buttons"""
	for qa in QUICK_ACTIONS:
		var button = Button.new()
		button.text = qa.label
		button.pressed.connect(_on_quick_action.bind(qa.action))
		quick_actions.add_child(button)


func _load_existing_messages():
	"""Load any existing messages from state"""
	for msg in GameState.messages:
		_add_message_bubble(msg)


func _update_character_display(character: Dictionary):
	"""Update the character info panel"""
	if character.is_empty():
		return
	
	name_label.text = character.get("name", "Unknown")
	
	var race = character.get("race", "")
	var char_class = character.get("class", "")
	var level = character.get("level", 1)
	class_label.text = "%s %s - Level %d" % [race, char_class, level]
	
	# HP bar
	var hp = character.get("hp", character.get("health", 20))
	var max_hp = character.get("max_hp", 20)
	hp_bar.max_value = max_hp
	hp_bar.value = hp
	
	# XP bar
	var xp = character.get("xp", 0)
	var xp_needed = level * 100
	xp_bar.max_value = xp_needed
	xp_bar.value = xp
	
	# Gold
	var gold = character.get("gold", 0)
	gold_label.text = "💰 %d Gold" % gold


func _on_message_added(msg: Dictionary):
	"""Handle new message"""
	_add_message_bubble(msg)
	
	# Auto-scroll to bottom
	await get_tree().process_frame
	scroll_container.scroll_vertical = scroll_container.get_v_scroll_bar().max_value


func _add_message_bubble(msg: Dictionary):
	"""Create a message bubble in chat"""
	var bubble = PanelContainer.new()
	bubble.size_flags_horizontal = Control.SIZE_SHRINK_END if msg.role == "user" else Control.SIZE_SHRINK_BEGIN
	
	# Style based on role
	var style = StyleBoxFlat.new()
	if msg.role == "user":
		style.bg_color = Color("#6366f140")
		style.border_color = Color("#6366f180")
	else:
		style.bg_color = Color("#1a1a2e")
		style.border_color = Color("#4a4a5a")
	
	style.set_border_width_all(1)
	style.set_corner_radius_all(8)
	style.set_content_margin_all(12)
	bubble.add_theme_stylebox_override("panel", style)
	
	var label = Label.new()
	label.text = msg.content
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	label.custom_minimum_size.x = 400
	bubble.add_child(label)
	
	chat_container.add_child(bubble)
	
	# Animate in
	bubble.modulate.a = 0
	bubble.position.y += 20
	var tween = create_tween()
	tween.set_parallel(true)
	tween.tween_property(bubble, "modulate:a", 1.0, 0.3)
	tween.tween_property(bubble, "position:y", bubble.position.y - 20, 0.3)


func _on_input_field_text_submitted(text: String):
	"""Handle enter key in input"""
	_send_action(text)


func _on_send_button_pressed():
	"""Handle send button click"""
	_send_action(input_field.text)


func _on_quick_action(action: String):
	"""Handle quick action button"""
	_send_action(action)


func _send_action(action: String):
	"""Send action to server"""
	action = action.strip_edges()
	if action.is_empty() or is_loading:
		return
	
	# Add user message
	GameState.add_message("user", action)
	
	# Clear and disable input
	input_field.text = ""
	is_loading = true
	input_field.editable = false
	send_button.disabled = true
	
	# Send to API
	ApiClient.send_action(action)


func _on_action_completed(data: Dictionary):
	"""Handle successful action response"""
	is_loading = false
	input_field.editable = true
	send_button.disabled = false
	input_field.grab_focus()
	
	# Update game state (this will trigger message_added)
	GameState.update_from_action(data)


func _on_request_failed(error: String):
	"""Handle API error"""
	is_loading = false
	input_field.editable = true
	send_button.disabled = false
	
	# Show error as system message
	GameState.add_message("system", "⚠️ " + error)


func _on_quit_button_pressed():
	"""Handle quit button"""
	GameState.reset()
	ApiClient.reset()
	get_tree().change_scene_to_file("res://scenes/CharacterCreation.tscn")
