extends Sprite2D

signal pet_interacted

# Movement
var max_speed = 250
var current_speed = 250
var acceleration = 600
var deceleration = 600
var direction = 1

# State control
var slowing_down = false
var paused = false
var is_interacting = false

# Pause timing
var pause_timer = 0.0
var pause_time = 2.5

# Random behavior
var random_timer = 0.0
var random_interval = 4.0

# Lid state
var lid_open = false

# Window position
var window_position: Vector2

# Click detection
var last_click_time = 0.0
var double_click_threshold = 0.35 # 350ms window

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

	# Center X and align to bottom of usable screen
	var usable_rect = DisplayServer.screen_get_usable_rect()
	window_position.x = usable_rect.position.x + (usable_rect.size.x - sprite_size.x) / 2.0
	snap_to_bottom_of_monitor()

	DisplayServer.window_set_position(Vector2i(window_position))

	DisplayServer.window_set_flag(DisplayServer.WINDOW_FLAG_BORDERLESS, true)
	DisplayServer.window_set_flag(DisplayServer.WINDOW_FLAG_ALWAYS_ON_TOP, true)
	
	update_passthrough()

func _process(delta):
	# Random event timer
	# random_timer += delta
	# if random_timer >= random_interval and not slowing_down and not paused:
	# 	random_timer = 0
	# 	if randf() < 0.5:
	# 		slowing_down = true

	# Slow down
	if slowing_down:
		current_speed -= deceleration * delta
		if current_speed <= 0:
			current_speed = 0
			slowing_down = false
			paused = true
			lid_open = true
			update_sprite()

	# Pause with lid open (only auto-resume if not interacting permanently)
	elif paused and not is_interacting:
		pause_timer += delta
		if pause_timer >= pause_time:
			paused = false
			lid_open = false
			pause_timer = 0
			update_sprite()
			
	# If interacting permanently with the UI, just keep it open and paused
	elif paused and is_interacting:
		lid_open = true
		
	# Speed up
	elif current_speed < max_speed and not paused and not slowing_down:
		current_speed += acceleration * delta
		if current_speed > max_speed:
			current_speed = max_speed

	# Move window only in X axis
	if not paused:
		window_position.x += current_speed * direction * delta

		snap_to_bottom_of_monitor()

		DisplayServer.window_set_position(Vector2i(window_position))

	# Screen edge turn
	var screen_width = DisplayServer.screen_get_usable_rect().position.x + DisplayServer.screen_get_usable_rect().size.x
	var sprite_width = texture.get_width()
	if window_position.x + sprite_width >= screen_width:
		direction = -1
		update_sprite()
	elif window_position.x <= 0:
		direction = 1
		update_sprite()

# Snap to bottom of screen
func snap_to_bottom_of_monitor():
	var usable_rect = DisplayServer.screen_get_usable_rect()
	var sprite_height = texture.get_height() if texture != null else 0
	window_position.y = usable_rect.position.y + usable_rect.size.y - sprite_height

func update_sprite():
	if direction == 1:
		texture = tobor_open_right if lid_open else tobor_right
	else:
		texture = tobor_open_left if lid_open else tobor_left

	# Update window size when texture size changes
	if texture != null:
		var sprite_size = texture.get_size()
		DisplayServer.window_set_size(Vector2i(sprite_size))
		update_passthrough()
		
func update_passthrough():
	if texture == null:
		return
	
	# The sprite is drawn at Vector2(0, 0) relative to the window since it's the root node,
	# but it might have an offset or custom positioning. Assuming default Sprite2D top-left:
	var sprite_size = texture.get_size()
	
	# Calculate where the sprite visually starts in the window.
	# The window size is `DisplayServer.window_get_size()`. If the window is taller than the sprite,
	# and the sprite is aligned to the bottom (as per `window_position.y` logic),
	# passthrough everything above the sprite.
	var window_size = DisplayServer.window_get_size()
	
	# Assuming the sprite is placed at the bottom of the window
	var sprite_y_start = window_size.y - sprite_size.y
	
	# Create a polygon that only covers the sprite itself
	var click_area = PackedVector2Array([
		Vector2(0, sprite_y_start),           # Top Left
		Vector2(sprite_size.x, sprite_y_start), # Top Right
		Vector2(sprite_size.x, window_size.y),  # Bottom Right
		Vector2(0, window_size.y)             # Bottom Left
	])
	
	DisplayServer.window_set_mouse_passthrough(click_area)
	
func _input(event):
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
		if get_rect().has_point(get_local_mouse_position()):
			var current_time = Time.get_ticks_msec() / 1000.0
			
			if current_time - last_click_time <= double_click_threshold:
				# Double click confirmed
				last_click_time = 0.0
				
				# Toggle Interaction: if it was already interacting, resume. Otherwise, pause permanently.
				if is_interacting:
					resume_movement()
				else:
					pause_permanently()
					
			else:
				# Register this as the first click
				last_click_time = current_time

func pause_permanently():
	current_speed = 0
	slowing_down = false
	paused = true
	lid_open = true
	is_interacting = true
	update_sprite()
	emit_signal("pet_interacted")

func resume_movement():
	paused = false
	lid_open = false
	is_interacting = false
	pause_timer = 0.0
	update_sprite()
