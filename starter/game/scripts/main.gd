extends Node2D
## Placeholder main scene. Replace it with your tiny game.


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("restart"):
		get_tree().reload_current_scene()
