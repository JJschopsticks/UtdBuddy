extends Control

func _ready():
	self.visible = true
	if has_node("ClassroomBubble"):
		$ClassroomBubble.visible = true
		$ClassroomBubble.mouse_filter = Control.MOUSE_FILTER_STOP
	if has_node("EventBubble"):
		$EventBubble.visible = true
		$EventBubble.mouse_filter = Control.MOUSE_FILTER_STOP
