extends Sprite2D

# Movement
var max_speed = 500
var current_speed = 500
var acceleration = 800
var deceleration = 800
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

# Sprites
var tobor_right = preload("res://Sprite Tobor/ToborRight.png")
var tobor_left = preload("res://Sprite Tobor/ToborLeft.png")
var tobor_open_right = preload("res://Sprite Tobor/ToborOpenRight.png")
var tobor_open_left = preload("res://Sprite Tobor/ToborOpenLeft.png")

func _ready():
	randomize()
	position.y = 2200
	texture = tobor_right

func _process(delta):

	var screen_width = get_viewport_rect().size.x

	# RANDOM EVENT TIMER
	random_timer += delta
	if random_timer >= random_interval and not slowing_down and not paused:
		random_timer = 0
		
		if randi() % 2 == 0:
			slowing_down = true

	# SLOW DOWN BEFORE STOPPING
	if slowing_down:
		current_speed -= deceleration * delta
		
		if current_speed <= 0:
			current_speed = 0
			slowing_down = false
			paused = true
			lid_open = true
			update_sprite()

	# PAUSE WITH LID OPEN
	elif paused:
		pause_timer += delta
		
		if pause_timer >= pause_time:
			paused = false
			lid_open = false
			pause_timer = 0
			update_sprite()

	# SPEED UP AGAIN
	elif current_speed < max_speed:
		current_speed += acceleration * delta
		
		if current_speed > max_speed:
			current_speed = max_speed

	# MOVE
	if not paused:
		position.x += current_speed * direction * delta

	# SCREEN EDGE TURN
	if position.x + 150 >= screen_width:
		direction = -1
		update_sprite()

	elif position.x - 150 <= 0:
		direction = 1
		update_sprite()


func update_sprite():

	if direction == 1:
		if lid_open:
			texture = tobor_open_right
		else:
			texture = tobor_right
	else:
		if lid_open:
			texture = tobor_open_left
		else:
			texture = tobor_left
