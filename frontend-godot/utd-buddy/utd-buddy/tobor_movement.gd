extends Sprite2D

# Movement
var max_speed = 250
var current_speed = 250
var acceleration = 600
var deceleration = 600
var direction = 1

# State control
var slowing_down = false
var paused = false

# Pause timing
var pause_timer = 0.0
var pause_time = 2.5

# Random behavior
var random_timer = 0.0
var random_interval = 4.0

# Lid state
var lid_open = false

# Window position
var window_position : Vector2

# Sprites
var tobor_right = preload("res://Sprite Tobor/ToborRight.png")
var tobor_left = preload("res://Sprite Tobor/ToborLeft.png")
var tobor_open_right = preload("res://Sprite Tobor/ToborOpenRight.png")
var tobor_open_left = preload("res://Sprite Tobor/ToborOpenLeft.png")

func _ready():
	randomize()

	texture = tobor_right
	var sprite_size = texture.get_size()
	DisplayServer.window_set_size(Vector2i(sprite_size))

	# Get full screen size
	var screen_size = DisplayServer.screen_get_size()
	window_position.x = (screen_size.x - sprite_size.x) / 2
	window_position.y = screen_size.y - sprite_size.y  # <- bottom aligned

	DisplayServer.window_set_position(window_position)

	DisplayServer.window_set_flag(DisplayServer.WINDOW_FLAG_BORDERLESS, true)
	DisplayServer.window_set_flag(DisplayServer.WINDOW_FLAG_ALWAYS_ON_TOP, true)

func _process(delta):
	var screen_width = DisplayServer.screen_get_size().x
	var sprite_width = texture.get_width()
	
	# Random event timer
	random_timer += delta
	if random_timer >= random_interval and not slowing_down and not paused:
		random_timer = 0
		if randf() < 0.5:
			slowing_down = true

	# Slow down
	if slowing_down:
		current_speed -= deceleration * delta
		if current_speed <= 0:
			current_speed = 0
			slowing_down = false
			paused = true
			lid_open = true
			update_sprite()
	
	# Pause with lid open
	elif paused:
		pause_timer += delta
		if pause_timer >= pause_time:
			paused = false
			lid_open = false
			pause_timer = 0
			update_sprite()
	
	# Speed up
	elif current_speed < max_speed:
		current_speed += acceleration * delta
		if current_speed > max_speed:
			current_speed = max_speed
	
	# Move window only in X axis; Y stays at bottom
	if not paused:
		window_position.x += current_speed * direction * delta
		
		# Keep Y locked to bottom
		window_position.y = DisplayServer.screen_get_size().y - texture.get_height()
		
		DisplayServer.window_set_position(window_position)
	
	# Screen edge turn
	if window_position.x + sprite_width >= screen_width:
		direction = -1
		update_sprite()
	elif window_position.x <= 0:
		direction = 1
		update_sprite()

func update_sprite():
	if direction == 1:
		texture = tobor_open_right if lid_open else tobor_right
	else:
		texture = tobor_open_left if lid_open else tobor_left
