extends Control

# === NODE REFERENCES (Will find nodes by name, not path) ===
var api_request: HTTPRequest
var input_box: LineEdit
var response_label: Label
var pet_sprite: Node
var send_button: Button
var bubble_container: Control
var event_bubble: Button
var classroom_bubble: Button

# === CONFIGURATION ===
const BACKEND_URL = "http://127.0.0.1:8000/ask"

const QUERY_PROMPTS = {
	"events": "What events are happening at UTD today or this week? Keep it brief and friendly.",
	"classrooms": "Which classrooms or study spaces at UTD are currently available or open? Be specific if possible."
}

# === UI CONTROLS ===
func show_initial_ui():
	if bubble_container:
		bubble_container.visible = true
	var chat_panel = _find_node_by_name("ChatPanel")
	if chat_panel:
		chat_panel.visible = true
	if input_box:
		input_box.visible = true
		input_box.text = ""
		input_box.editable = true
	if send_button:
		send_button.visible = true
		send_button.disabled = false
	if response_label:
		response_label.text = "👋 Hello! Click a bubble or type a question."

func hide_chat_ui():
	if bubble_container:
		bubble_container.visible = false
	var chat_panel = _find_node_by_name("ChatPanel")
	if chat_panel:
		chat_panel.visible = false
	if input_box:
		input_box.visible = false
	if send_button:
		send_button.visible = false

func _on_pet_interacted():
	show_initial_ui()

# === DRAG FUNCTIONALITY ===
var dragging = false
var drag_offset = Vector2.ZERO

# === INITIALIZATION ===
func _ready():
	_find_nodes()
	
	if send_button:
		send_button.pressed.connect(_on_send_pressed)
	if input_box:
		input_box.text_submitted.connect(_on_send_pressed)
		input_box.text_changed.connect(_on_typing_started)
	if api_request:
		api_request.request_completed.connect(_on_request_completed)
	
	if event_bubble:
		event_bubble.text = "Events Map"
		event_bubble.pressed.connect(_on_bubble_pressed.bind("events"))
	if classroom_bubble:
		classroom_bubble.text = "Classrooms Available"
		classroom_bubble.pressed.connect(_on_bubble_pressed.bind("classrooms"))
	
	set_pet_state("idle")
	if input_box:
		input_box.placeholder_text = "Type your question..."
		
	hide_chat_ui()
	
	if pet_sprite and pet_sprite.has_signal("pet_interacted"):
		pet_sprite.pet_interacted.connect(_on_pet_interacted)
	
	print("✅ All nodes initialized in original state.")

# === FIND NODES (Robust method) ===
func _find_nodes():
	api_request = _find_node_by_type(HTTPRequest)
	input_box = _find_node_by_type(LineEdit)
	
	var chat_panel = _find_node_by_name("ChatPanel")
	if chat_panel:
		response_label = _find_node_by_name_in_parent(chat_panel, "Response")
		if not response_label:
			response_label = _find_node_by_type_in_parent(chat_panel, Label)
	
	pet_sprite = _find_node_by_name("Tobor")
	
	bubble_container = _find_node_by_name("Bubble cont")
	if not bubble_container:
		bubble_container = _find_node_by_name("BubbleCont")
	if not bubble_container:
		bubble_container = _find_node_by_name("Bubble Control")
	
	if bubble_container:
		event_bubble = _find_node_by_name_in_parent(bubble_container, "EventBubb")
		if not event_bubble:
			event_bubble = _find_node_by_name_in_parent(bubble_container, "EventBubble")
		
		classroom_bubble = _find_node_by_name_in_parent(bubble_container, "Classroom")
		if not classroom_bubble:
			classroom_bubble = _find_node_by_name_in_parent(bubble_container, "ClassroomBubble")
	
	send_button = _find_node_by_type(Button)

# === HELPER FUNCTIONS ===
func _find_node_by_name(node_name: String) -> Node:
	for child in get_children():
		if child.name == node_name:
			return child
	return null

func _find_node_by_name_in_parent(parent: Node, node_name: String) -> Node:
	for child in parent.get_children():
		if child.name == node_name:
			return child
	return null

func _find_node_by_type(node_type) -> Node:
	for child in get_children():
		if is_instance_of(child, node_type):
			return child
	return null

func _find_node_by_type_in_parent(parent: Node, node_type) -> Node:
	for child in parent.get_children():
		if is_instance_of(child, node_type):
			return child
	return null

# === INPUT HANDLING ===
func _unhandled_input(event: InputEvent):
	if event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_RIGHT:
			if event.pressed:
				dragging = true
				drag_offset = get_global_mouse_position() - global_position
			else:
				dragging = false

func _process(_delta):
	if dragging:
		global_position = get_global_mouse_position() - drag_offset

# === INPUT EVENT LISTENER ===
func _on_typing_started(_new_text: String):
	if bubble_container and bubble_container.visible:
		bubble_container.visible = false

# === BUBBLE CLICK HANDLER ===
func _on_bubble_pressed(query_type: String):
	if input_box:
		input_box.text = QUERY_PROMPTS[query_type]
	if bubble_container:
		bubble_container.visible = false

# === BACKEND COMMUNICATION ===
func _send_query_to_backend(question: String, query_type: String = "general"):
	set_pet_state("thinking")
	
	if response_label:
		response_label.text = "🤔 Thinking..."
	if bubble_container:
		bubble_container.visible = false
	if input_box:
		input_box.release_focus()
		input_box.editable = false
		input_box.visible = false
	if send_button:
		send_button.disabled = true
		send_button.visible = false
	
	var body = { 
		"question": question,
		"query_type": query_type
	}
	var headers = ["Content-Type: application/json"]
	
	if api_request:
		var error = api_request.request(
			BACKEND_URL,
			headers,
			HTTPClient.METHOD_POST,
			JSON.stringify(body)
		)
		
		if error != OK:
			_on_error("Failed to connect to backend.")

func _on_send_pressed(_ignore_text: String = ""):
	if not input_box:
		return
		
	var question = input_box.text.strip_edges()
	if question.is_empty(): 
		return
	
	_send_query_to_backend(question, "custom")

# === API RESPONSE HANDLER ===
func _on_request_completed(_result, response_code, _headers, body):
	if input_box:
		input_box.editable = true
	if send_button:
		send_button.disabled = false
	set_pet_state("idle")
	
	if response_code == 200:
		var json = JSON.parse_string(body.get_string_from_utf8())
		
		if json and json.has("answer"):
			if response_label:
				response_label.text = json["answer"]
			
			var anim_sprite = _get_animation_sprite()
			if anim_sprite and anim_sprite.sprite_frames:
				if anim_sprite.sprite_frames.has_animation("happy"):
					anim_sprite.play("happy")
					await get_tree().create_timer(2.0).timeout
					set_pet_state("idle")
					if pet_sprite and pet_sprite.has_method("resume_movement"):
						pet_sprite.resume_movement()
					hide_chat_ui()
		else:
			_on_error("Invalid response format.")
	else:
		_on_error("Server error (Code: %d)" % response_code)
	
	if input_box:
		input_box.text = ""

# === ERROR HANDLING ===
func _on_error(message: String):
	if response_label:
		response_label.text = "⚠️ " + message
	set_pet_state("idle")
	printerr("Godot Error: " + message)
	
	await get_tree().create_timer(3.0).timeout
	if pet_sprite and pet_sprite.has_method("resume_movement"):
		pet_sprite.resume_movement()
	hide_chat_ui()

# === PET ANIMATIONS ===
func set_pet_state(state: String):
	var anim_sprite = _get_animation_sprite()
	if not anim_sprite:
		return
	if not anim_sprite.sprite_frames:
		return
	
	match state:
		"thinking":
			if anim_sprite.sprite_frames.has_animation("thinking"):
				anim_sprite.play("thinking")
			elif anim_sprite.sprite_frames.get_animation_names().size() > 0:
				anim_sprite.play(anim_sprite.sprite_frames.get_animation_names()[0])
		"happy":
			if anim_sprite.sprite_frames.has_animation("happy"):
				anim_sprite.play("happy")
			elif anim_sprite.sprite_frames.get_animation_names().size() > 0:
				anim_sprite.play(anim_sprite.sprite_frames.get_animation_names()[0])
		_:
			if anim_sprite.sprite_frames.has_animation("idle"):
				anim_sprite.play("idle")
			elif anim_sprite.sprite_frames.get_animation_names().size() > 0:
				anim_sprite.play(anim_sprite.sprite_frames.get_animation_names()[0])

func _get_animation_sprite() -> AnimatedSprite2D:
	if not pet_sprite:
		return null
	if pet_sprite is AnimatedSprite2D:
		return pet_sprite
	for child in pet_sprite.get_children():
		if child is AnimatedSprite2D:
			return child
	return null
