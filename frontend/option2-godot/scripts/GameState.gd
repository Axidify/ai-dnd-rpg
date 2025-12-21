extends Node

## GameState singleton for managing game data
## Autoloaded as "GameState"

signal state_changed()
signal character_updated(character: Dictionary)
signal message_added(message: Dictionary)

var character: Dictionary = {}
var messages: Array[Dictionary] = []
var location: String = ""
var inventory: Array = []
var quests: Array = []


func set_initial_state(data: Dictionary) -> void:
	"""Set state from character creation response"""
	var game_state = data.get("game_state", data)
	
	character = game_state.get("character", {})
	location = game_state.get("location", "Unknown")
	inventory = game_state.get("inventory", [])
	
	# Add initial DM message
	var intro = game_state.get("dm_response", game_state.get("narrative", "Your adventure begins..."))
	add_message("dm", intro)
	
	state_changed.emit()
	character_updated.emit(character)


func update_from_action(data: Dictionary) -> void:
	"""Update state from action response"""
	var game_state = data.get("game_state", data)
	
	if game_state.has("character"):
		character = game_state.character
		character_updated.emit(character)
	
	if game_state.has("location"):
		location = game_state.location
	
	if game_state.has("inventory"):
		inventory = game_state.inventory
	
	# Add DM response
	var response = game_state.get("dm_response", game_state.get("narrative", ""))
	if not response.is_empty():
		add_message("dm", response)
	
	state_changed.emit()


func add_message(role: String, content: String) -> void:
	"""Add a message to the chat history"""
	var msg = {
		"role": role,
		"content": content,
		"timestamp": Time.get_unix_time_from_system()
	}
	messages.append(msg)
	message_added.emit(msg)


func reset() -> void:
	"""Clear all state"""
	character = {}
	messages.clear()
	location = ""
	inventory.clear()
	quests.clear()
	state_changed.emit()
