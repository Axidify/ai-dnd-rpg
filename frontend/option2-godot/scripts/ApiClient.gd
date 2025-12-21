extends Node

## API Client singleton for communicating with Flask backend
## Autoloaded as "ApiClient"

signal character_created(data: Dictionary)
signal action_completed(data: Dictionary)
signal request_failed(error: String)

const BASE_URL = "http://localhost:5000/api"

var session_id: String = ""
var _http_request: HTTPRequest


func _ready():
	# Create reusable HTTP request node
	_http_request = HTTPRequest.new()
	add_child(_http_request)


func create_character(char_name: String, char_class: String, race: String) -> void:
	"""Create a new character and start game session"""
	var url = BASE_URL + "/game/start"
	var body = JSON.stringify({
		"character": {
			"name": char_name,
			"class": char_class,
			"race": race
		}
	})
	
	var headers = ["Content-Type: application/json"]
	
	# Create new HTTP request for this call
	var http = HTTPRequest.new()
	add_child(http)
	http.request_completed.connect(_on_create_character_completed.bind(http))
	
	var error = http.request(url, headers, HTTPClient.METHOD_POST, body)
	if error != OK:
		request_failed.emit("Failed to send request")
		http.queue_free()


func _on_create_character_completed(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray, http: HTTPRequest) -> void:
	http.queue_free()
	
	if result != HTTPRequest.RESULT_SUCCESS:
		request_failed.emit("Connection failed - is the server running?")
		return
	
	if response_code != 200:
		request_failed.emit("Server error: " + str(response_code))
		return
	
	var json = JSON.parse_string(body.get_string_from_utf8())
	if json == null:
		request_failed.emit("Invalid response from server")
		return
	
	session_id = json.get("session_id", "")
	character_created.emit(json)


func send_action(action: String) -> void:
	"""Send player action to the game"""
	if session_id.is_empty():
		request_failed.emit("No active session")
		return
	
	var url = BASE_URL + "/game/action"
	var body = JSON.stringify({
		"session_id": session_id,
		"action": action
	})
	
	var headers = ["Content-Type: application/json"]
	
	var http = HTTPRequest.new()
	add_child(http)
	http.request_completed.connect(_on_action_completed.bind(http))
	
	var error = http.request(url, headers, HTTPClient.METHOD_POST, body)
	if error != OK:
		request_failed.emit("Failed to send action")
		http.queue_free()


func _on_action_completed(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray, http: HTTPRequest) -> void:
	http.queue_free()
	
	if result != HTTPRequest.RESULT_SUCCESS:
		request_failed.emit("Connection lost")
		return
	
	if response_code != 200:
		request_failed.emit("Action failed: " + str(response_code))
		return
	
	var json = JSON.parse_string(body.get_string_from_utf8())
	if json == null:
		request_failed.emit("Invalid response")
		return
	
	action_completed.emit(json)


func reset() -> void:
	"""Reset the session"""
	session_id = ""
